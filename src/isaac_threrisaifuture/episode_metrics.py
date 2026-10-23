"""Append-only CSV of episode summaries (`info["episode_summary"]`), one row per episode."""

import csv
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, SupportsFloat

import gymnasium as gym

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
EXTRA_FIELDS = (
    "use_bomb",
    "use_active",
    "use_pillcard",
    "half_hearts_lost",
    "steps_to_first_exit",
    "steps_to_first_damage",
    "enemies_killed",
    *HIT_FIELDS,
)
FIELDS = (
    *BASE_FIELDS,
    *(f"pickups_{name}" for name in PICKUPS),
    *(f"col_{name}" for name in REWARD_V4_COLUMNS),
    *EXTRA_FIELDS,
    "wall_time",  # UTC ISO-8601, seconds precision, stamped when the row is written
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
                if next(csv.reader(handle), None) != list(FIELDS):
                    raise ValueError(f"Existing metrics file has a different header: {path}")
        else:
            self._append([dict(zip(FIELDS, FIELDS, strict=True))])

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
