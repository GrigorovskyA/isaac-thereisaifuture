"""OFFLINE tests of the stall context columns in episodes.csv (metrics only)."""

import csv
from pathlib import Path

import numpy as np
import pytest
from synthetic import door, room_facts

from isaac_threrisaifuture.entities import Entity, OracleDoor, Vec
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import (
    FIELDS,
    LEGACY_HEADERS,
    STALL_FIELDS,
    EpisodeMetricsWriter,
)
from isaac_threrisaifuture.episodes import Scenario, StepResult
from isaac_threrisaifuture.sim import SyntheticRoomBackend

TOY = Scenario("toy", "train", 1, 900, enemy_count=1, enemy_hp=7.0)
CONTRACT_HASH = "ee4f65999d3a8cf0c85dabd5d887e360fd0823a164814bd20753d6dca91ac703"


def npc(entity_id, x, y, kind, variant, *, flying=False, invulnerable=False, boss=False):
    return Entity(
        kind="enemy", entity_id=entity_id, spawn_generation=0, position=Vec(x=x, y=y),
        hp=10.0, max_hp=10.0, npc_type=kind, npc_variant=variant, npc_max_hp=10.0,
        boss=boss, champion=False, flying=flying, invulnerable=invulnerable,
    )  # fmt: skip


class RoomBackend(SyntheticRoomBackend):
    """The toy backend with a fixed room around the player."""

    def __init__(self, *, clear: bool, entities: list[Entity]) -> None:
        super().__init__()
        self.clear, self.entities = clear, entities

    def oracle_enemy_count(self) -> int:
        return 5

    def _frame_model(self):
        base = super()._frame_model()
        doors = [door(open=True), None, door(open=False), *[None] * 5]
        room = room_facts(type=2, shape=4, clear=self.clear, doors=doors)
        return base.model_copy(update={"entities": self.entities, "room": room})

    def step(self, action, repeat):
        result = super().step(action, repeat)
        doors = (
            OracleDoor(slot=0, x=0.0, y=0.0, open=True, unexplored=True, target=85, usable=True),
            OracleDoor(slot=2, x=1.0, y=1.0, open=False, unexplored=True, target=83, usable=True),
        )
        return StepResult(result.frame, result.events, result.terminal_coverage, doors=doors)


def run_to_end(backend, *, stall: bool):
    env = IsaacCombatEnv(backend, [TOY], action_repeat=3)
    env.reset(seed=1)
    if stall:
        env.request_truncation("stall")
    for _ in range(2):
        *_, info = env.step(np.array([0, 0, 0]))
        if "episode_summary" in info:
            return info["episode_summary"]
    raise AssertionError("episode did not end")


def test_stall_episode_fills_the_context_columns(tmp_path):
    enemies = [
        npc(1, 30.0, 40.0, 18, 0, invulnerable=True, flying=True),
        npc(2, 300.0, 0.0, 10, 1, boss=True),
        npc(3, 0.0, 90.0, 18, 0),
    ]
    summary = run_to_end(RoomBackend(clear=False, entities=enemies), stall=True)
    assert summary["truncation_reason"] == "stall" and summary["last_room_clear"] == 0
    path = tmp_path / "episodes.csv"
    EpisodeMetricsWriter(path).write(summary)
    row = next(csv.DictReader(path.open(encoding="utf-8")))
    assert row["stall_room_clear"] == "0" and row["stall_room_type"] == "2"
    assert row["stall_room_shape"] == "4"
    assert row["stall_enemies"] == "3" and row["stall_oracle_enemies"] == "5"
    assert row["stall_enemies_invulnerable"] == "1" and row["stall_enemies_flying"] == "1"
    assert row["stall_enemies_boss"] == "1" and row["stall_enemy_kinds"] == "10.1;18.0"
    assert row["stall_nearest_enemy"] == "50.0"
    assert row["stall_open_unexplored_doors"] == "1" and row["stall_open_doors"] == "1"
    assert row["stall_half_hearts"] == "6" and float(row["stall_seconds_in_room"]) > 0


def test_death_episode_leaves_the_stall_columns_empty_and_sets_last_room_clear(tmp_path):
    class Dying(RoomBackend):
        def step(self, action, repeat):
            result = super().step(action, repeat)
            events = (*result.events, self._event("player_died"))
            return StepResult(result.frame, events, result.terminal_coverage, doors=result.doors)

    backend = Dying(clear=True, entities=[])
    env = IsaacCombatEnv(backend, [TOY], action_repeat=3)
    env.reset(seed=1)
    summary = None
    for _ in range(400):
        *_, info = env.step(np.array([0, 0, 0]))
        if "episode_summary" in info:
            summary = info["episode_summary"]
            break
    assert summary is not None and summary["end_reason"] == "death"
    path = tmp_path / "episodes.csv"
    EpisodeMetricsWriter(path).write(summary)
    row = next(csv.DictReader(path.open(encoding="utf-8")))
    assert row["last_room_clear"] == "1"
    assert all(row[name] == "" for name in STALL_FIELDS)


@pytest.mark.parametrize("generation", range(len(LEGACY_HEADERS)))
def test_old_header_is_upgraded_once_and_keeps_rows(tmp_path, generation):
    path = tmp_path / "episodes.csv"
    old = LEGACY_HEADERS[generation]  # 0: before the stall columns, 1: before stall_goal_hops
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(old)
        writer.writerow(["7" if name == "episode_id" else "x" for name in old])
    EpisodeMetricsWriter(path)
    EpisodeMetricsWriter(path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert tuple(rows[0]) == FIELDS and len(rows) == 1
    assert rows[0]["episode_id"] == "7" and rows[0]["return"] == "x"
    kept = "x" if generation == 1 else ""  # columns the old file already had keep their cells
    assert rows[0]["stall_goal_hops"] == "" and rows[0]["stall_enemies"] == kept
    assert rows[0]["last_room_clear"] == kept
    assert not path.with_name(path.name + ".upgrade").exists()


def test_contract_hash_is_unchanged():
    from isaac_threrisaifuture.training import load_training_config

    config = Path(__file__).parents[1] / "configs" / "training-pure-v4.yaml"
    _, digest = load_training_config(config)
    assert digest == CONTRACT_HASH
