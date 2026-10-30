"""Reward v11 additions: a stall ends the episode for the learner; novelty counts cross runs."""

import math
from pathlib import Path

import numpy as np
import pytest
import yaml
from synthetic import frame, room_facts
from test_reward_v4 import LIVE_SCENARIO
from test_reward_v10 import GAMMA, STALL_SECONDS, B, K, Rooms

from isaac_threrisaifuture.checkpoints import CheckpointError, read_manifest
from isaac_threrisaifuture.entities import Vec
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episodes import Scenario, StepResult
from isaac_threrisaifuture.novelty_counts import MAX_KEYS, NoveltyCounts, NoveltyCountsError
from isaac_threrisaifuture.rewards import (
    DEFAULT_CONFIG_V10,
    DEFAULT_CONFIG_V11,
    RewardLedgerV4,
    RewardV4Coefficients,
)

V10 = RewardV4Coefficients.load(DEFAULT_CONFIG_V10)
V11 = RewardV4Coefficients.load(DEFAULT_CONFIG_V11)
STEP = np.array([0, 0, 0])


class DeadEnd(Rooms):
    """Cleared room B with no door to a goal: graph cost 1 + max_hops = 6, Phi = -12."""

    def _result(self):
        self.count += 1
        return StepResult(
            frame(player_position=Vec(x=300.0, y=280.0), room=room_facts(clear=True),
                  frame_id=self.count),
            (), room_index=1, doors=(), enemies_present=False, room_grid=B,
        )  # fmt: skip


def ledger(coef=V11, counts=None):
    return RewardLedgerV4(coef, stall_seconds=STALL_SECONDS, gamma=GAMMA, novelty_counts=counts)


# --- 1. a stall ends the episode for learning -------------------------------------------


def test_a_stall_is_terminated_for_the_learner_but_truncated_in_reports():
    env = IsaacCombatEnv(DeadEnd(), [LIVE_SCENARIO], accountant=ledger())
    env.reset()
    env.request_truncation("stall")
    _, reward, terminated, truncated, info = env.step(STEP)
    assert terminated and not truncated
    assert info["outcome"] == "truncated" and info["truncation_reason"] == "stall"
    summary = info["episode_summary"]
    assert summary["outcome"] == "truncated" and summary["truncation_reason"] == "stall"
    assert summary["end_reason"] == "truncated"
    # Phi(s) = -12 at the dead end; the terminal zero now counts as a real termination.
    assert info["reward_components"]["door_shaping"] == pytest.approx(0.0 * GAMMA + 12.0)
    assert K * 6 == 12.0


def test_a_non_stall_truncation_keeps_the_potential_and_stays_truncated():
    capped = Scenario("capped", "train", 1, 2, 0, 1.0, True, False)
    env = IsaacCombatEnv(DeadEnd(), [capped], accountant=ledger())
    env.reset()
    for _ in range(5):
        _, _, terminated, truncated, info = env.step(STEP)
        if terminated or truncated:
            break
    assert truncated and not terminated and info["truncation_reason"] != "stall"
    # No zeroing: gamma * Phi(s') - Phi(s) with Phi(s') = Phi(s) = -12.
    assert info["reward_components"]["door_shaping"] == pytest.approx(12.0 * (1 - GAMMA))


def test_death_is_still_terminated_with_the_terminal_zero():
    class Dying(DeadEnd):
        def _result(self):
            result = super()._result()
            from synthetic import event

            died = (event("player_died", result.frame.frame_id),) if self.count > 1 else ()
            return StepResult(result.frame, died, room_index=1, doors=(), room_grid=B)

    env = IsaacCombatEnv(Dying(), [LIVE_SCENARIO], accountant=ledger())
    env.reset()
    _, _, terminated, truncated, info = env.step(STEP)
    assert terminated and not truncated and info["outcome"] == "death"
    assert info["reward_components"]["door_shaping"] == pytest.approx(12.0)


# --- 2. novelty across runs -------------------------------------------------------------


def run(value, run_index, x=100.0, room=1):
    """Start run `run_index` (a new game epoch) and take one step at (x, 280)."""
    first = frame(game_epoch=run_index, player_position=Vec(x=x, y=280.0))
    value.reset(run_index)
    value.begin(first, room, [], False, B)
    _, parts = value.consume([], 0, first, room, [], False, False, B)
    return parts["novelty"]


def test_the_start_room_decays_with_the_number_of_runs():
    counts = NoveltyCounts()
    value = ledger(counts=counts)
    paid = [run(value, index) for index in range(1, 5)]
    expected = [0.1 / math.sqrt(n) for n in (1, 2, 3, 4)]
    assert paid == pytest.approx(expected)
    assert paid[:3] == pytest.approx([0.1, 0.0707, 0.0577], abs=1e-4)
    assert counts.get((1, 1, 1, 3)) == 4  # (stage, room, cell x, cell y)


def test_re_entering_a_cell_in_one_run_pays_nothing_and_counts_once():
    counts = NoveltyCounts()
    value = ledger(counts=counts)
    assert run(value, 1) > 0
    first = frame(game_epoch=1, player_position=Vec(x=100.0, y=280.0))
    _, parts = value.consume([], 0, first, 1, [], False, False, B)
    assert parts["novelty"] == 0.0 and counts.get((1, 1, 1, 3)) == 1


def test_a_resume_continues_the_decay_and_v10_ignores_counts(tmp_path):
    counts = NoveltyCounts()
    value = ledger(counts=counts)
    run(value, 1)
    run(value, 2)
    path = tmp_path / "counts.npz"
    counts.save(path)
    restored = NoveltyCounts()
    restored.load(path)
    assert run(ledger(counts=restored), 7) == pytest.approx(0.1 / math.sqrt(3))
    old_counts = NoveltyCounts()
    old = ledger(V10, old_counts)
    assert [run(old, index) for index in (1, 2, 3)] == [0.1, 0.1, 0.1]
    assert len(old_counts) == 0


def test_a_frozen_table_never_stores_a_count():
    counts = NoveltyCounts()
    run(ledger(counts=counts), 1)
    frozen = NoveltyCounts(frozen=True)
    frozen._counts = dict(counts._counts)
    assert run(ledger(counts=frozen), 2) == pytest.approx(0.1 / math.sqrt(2))
    assert frozen._counts == counts._counts


def test_a_large_table_round_trips_and_a_full_table_refuses_new_keys(tmp_path, monkeypatch):
    counts = NoveltyCounts()
    for stage in range(1, 14):
        for room in range(0, 40):
            for cell in range(0, 364):
                counts.visit((stage, room, cell % 26, cell // 26))
    path = tmp_path / "big.npz"
    counts.save(path)
    again = NoveltyCounts()
    again.load(path)
    assert len(again) == len(counts) == 13 * 40 * 364 and again._counts == counts._counts
    monkeypatch.setattr("isaac_threrisaifuture.novelty_counts.MAX_KEYS", len(counts))
    assert counts.visit((99, 0, 0, 0)) == 0 and counts.visit((1, 0, 0, 0)) == 2
    assert MAX_KEYS >= 13 * 169 * 364


def test_a_corrupt_counts_file_is_an_error(tmp_path):
    path = tmp_path / "bad.npz"
    path.write_bytes(b"not an npz")
    with pytest.raises(NoveltyCountsError):
        NoveltyCounts().load(path)


def test_cross_run_is_required_for_v11_and_forbidden_before(tmp_path):
    raw = yaml.safe_load(DEFAULT_CONFIG_V11.read_text("utf-8"))
    del raw["novelty"]["cross_run"]
    path = tmp_path / "missing.yaml"
    path.write_text(yaml.safe_dump(raw), "utf-8")
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(path)
    raw10 = yaml.safe_load(DEFAULT_CONFIG_V10.read_text("utf-8"))
    raw10["novelty"]["cross_run"] = True
    path = tmp_path / "v10.yaml"
    path.write_text(yaml.safe_dump(raw10), "utf-8")
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(path)
    assert V10.novelty_cross_run is False and V11.novelty_cross_run is True


# --- checkpoint ------------------------------------------------------------------------


def test_checkpoints_carry_the_counts_file_in_the_manifest_and_hash(tmp_path):
    from isaac_threrisaifuture.checkpoints import save_checkpoint

    class Saver:
        def save(self, path):
            Path(path).write_bytes(b"x")

    counts = NoveltyCounts()
    counts.visit((1, 1, 1, 1))
    root = tmp_path / "ckpt"
    manifest = save_checkpoint(
        root, model=Saver(), vec_normalize=Saver(), algorithm="RecurrentPPO", cfg_hash="a" * 64,
        seed=1, timesteps=10, parent_checkpoint_id=None, rng_state={}, novelty_counts=counts,
    )  # fmt: skip
    directory = root / manifest.checkpoint_id
    assert manifest.novelty_counts_file == "novelty_counts.npz"
    assert (directory / "novelty_counts.npz").is_file()
    (directory / "novelty_counts.npz").write_bytes(b"tampered")
    with pytest.raises(CheckpointError):
        read_manifest(directory)
