"""Append-only CSV of episode summaries (`info["episode_summary"]`), one row per episode."""

import csv
import os
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, SupportsFloat

import gymnasium as gym

from .entities import ENTITY_KINDS
from .episodes import HIT_FIELDS
from .rewards import REWARD_V4_COLUMNS

PICKUPS = ("coin", "bomb", "key", "collectible")
BASE_FIELDS = (
    "episode_id",
    "scenario_id",
    "timesteps",
    "game_updates",
    "return",
    "outcome",
    "end_reason",
    "truncation_reason",
    "damage_dealt_fraction",
    "rooms_visited",
    "rooms_cleared",
    "max_stage",
)
# Cap tuning, metrics only: per kind the most entities in one snapshot (cut ones included) and
# the share of observed steps in which the observer or the encoder dropped some.
CAP_FIELDS = (
    *(f"max_{kind}" for kind in ENTITY_KINDS),
    *(f"overflow_{kind}" for kind in ENTITY_KINDS),
    "enemy_kinds",  # distinct enemy (type, variant) pairs seen in the episode
)
# Stall context, metrics only: filled for stall truncations from the last snapshot, else empty.
STALL_FIELDS = (
    "stall_room_clear",
    "stall_room_type",
    "stall_room_shape",
    "stall_enemies",
    "stall_oracle_enemies",
    "stall_enemies_invulnerable",
    "stall_enemies_flying",
    "stall_enemies_boss",
    "stall_enemy_kinds",  # "type.variant" pairs, sorted, joined by ";"
    "stall_nearest_enemy",  # px from the player
    "stall_open_unexplored_doors",
    "stall_goal_hops",  # reward v10: best door term (rooms to cross plus in-room share), 2 digits
    "stall_open_doors",
    "stall_half_hearts",
    "stall_seconds_in_room",  # game updates since the room change (or episode start) / 30
)
EXTRA_FIELDS = (
    "use_bomb",
    "use_active",
    "use_pillcard",
    "half_hearts_lost",
    "steps_to_first_exit",
    "steps_to_first_damage",
    "enemies_killed",
    *HIT_FIELDS,
    *CAP_FIELDS,
    "last_room_clear",  # clear flag of the room the episode ended in
    *STALL_FIELDS,
)
FIELDS = (
    *BASE_FIELDS,
    *(f"pickups_{name}" for name in PICKUPS),
    *(f"col_{name}" for name in REWARD_V4_COLUMNS),
    *EXTRA_FIELDS,
    "wall_time",  # UTC ISO-8601, seconds precision, stamped when the row is written
)

NEW_FIELDS = frozenset(("last_room_clear", *STALL_FIELDS))
LEGACY_HEADERS = (
    tuple(name for name in FIELDS if name not in NEW_FIELDS),  # before the stall columns
    tuple(name for name in FIELDS if name != "stall_goal_hops"),  # before reward v10
)


def summary_row(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Flatten a summary; facts the summary does not have stay empty."""
    row: dict[str, Any] = {name: summary.get(name) for name in BASE_FIELDS}
    for name in PICKUPS:
        row[f"pickups_{name}"] = summary.get("pickups", {}).get(name)
    for name in REWARD_V4_COLUMNS:
        row[f"col_{name}"] = summary.get("columns", {}).get(name)
    for name in EXTRA_FIELDS:
        row[name] = summary.get(name)
    return row


class EpisodeMetricsWriter:
    """Writes the header once; every row is flushed so a crash keeps completed episodes."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > 0:
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
            header = tuple(rows[0]) if rows else ()
            if header in LEGACY_HEADERS:
                self._upgrade(rows)
            elif header != FIELDS:
                raise ValueError(f"Existing metrics file has a different header: {path}")
        else:
            self._append([dict(zip(FIELDS, FIELDS, strict=True))])

    def _upgrade(self, rows: list[list[str]]) -> None:
        """Rewrite an old-header file with the full header; old rows get empty new cells."""
        temporary = self.path.with_name(self.path.name + ".upgrade")
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, restval="", lineterminator="\n")
            writer.writeheader()
            writer.writerows(dict(zip(rows[0], row, strict=False)) for row in rows[1:])
        os.replace(temporary, self.path)

    def write(self, summary: Mapping[str, Any]) -> None:
        row = summary_row(summary)
        row["wall_time"] = datetime.now(UTC).isoformat(timespec="seconds")
        self._append([row])

    def _append(self, rows: list[dict[str, Any]]) -> None:
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, restval="", lineterminator="\n")
            writer.writerows(rows)
            handle.flush()


class EpisodeMetricsEnv(gym.Wrapper[Any, Any, Any, Any]):
    """Appends each `info["episode_summary"]` to the CSV; the step result is untouched."""

    def __init__(self, env: gym.Env[Any, Any], writer: EpisodeMetricsWriter) -> None:
        super().__init__(env)
        self.writer = writer

    def step(self, action: Any) -> tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]:
        result = self.env.step(action)
        summary = result[4].get("episode_summary")
        if summary is not None:
            self.writer.write(summary)
        return result
