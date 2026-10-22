"""Counterfactual reward tests. Synthetic geometry is not native clearance evidence."""

from dataclasses import replace

import numpy as np
import pytest
import yaml
from pydantic import ValidationError
from test_checkpoint_policy import RAW_CONFIG
from test_checkpoint_publication import Artifact
from test_combat_gate import World, snap

from isaac_threrisaifuture import checkpoints as cp
from isaac_threrisaifuture import firing_position as firing
from isaac_threrisaifuture import live
from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.firing_position import FiringGeometry, FiringProgress, potential
from isaac_threrisaifuture.live import LiveRunOptions, LiveSnapshot, make_live_env
from isaac_threrisaifuture.observation import ProtocolError
from isaac_threrisaifuture.observer_client import ObserverConfig


def sample(frame=1, *, x=40.0, visit=1, room=4, firing_changes=None, grid_changes=None, target=1):
    raw = snap(frame, visit=visit, enemies={target: 10}).model_dump(mode="json")
    pos = {"x": x, "y": 80.0}
    raw["player"]["position"] = pos
    raw["entity_frame"]["player_position"] = pos
    raw["entity_frame"]["entities"] = [
        {
            "kind": "enemy",
            "entity_id": target,
            "spawn_generation": 0,
            "position": {"x": 280.0 - x, "y": 0.0},
            "velocity": None,
            "hp": None,
            "max_hp": None,
        }
    ]
    raw["oracle"]["navigation"] = {
        "version": 2,
        "room_index": room,
        "stage": 1,
        "stage_type": 0,
        "room_type": 1,
        "shape": 1,
        "doors": [],
        "grid": {
            "origin": {"x": 0.0, "y": 0.0},
            "spacing": 40,
            "width": 7,
            "height": 5,
            "walkable": "1" * 35,
            **(grid_changes or {}),
        },
    }
    raw["oracle"]["firing"] = {
        "version": 1,
        "status": "plain_tears",
        "tear_range": 260.0,
        "target_id": target,
        "target_position": {"x": 280.0, "y": 80.0},
        "target_vulnerable": True,
        "clear_cells": [18],
        "candidate_overflow": 0,
        **(firing_changes or {}),
    }
    return LiveSnapshot.model_validate(raw)


def score(snapshot):
    return potential(
        snapshot.oracle.navigation.grid,
        snapshot.oracle.firing,
        snapshot.entity_frame.player_position,
    )


def test_measured_clear_reachable_cell_gives_graph_distance_potential():
    assert score(sample(x=40.0)) == pytest.approx(1 / (1 + 120 / 260))
    assert score(sample(x=80.0)) > score(sample(x=40.0))
    assert score(sample(x=160.0)) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"clear_cells": []},
        {"tear_range": 100.0},
        {"clear_cells": [20]},
        {"target_vulnerable": False, "clear_cells": []},
        {
            "status": "unsupported",
            "target_id": None,
            "target_position": None,
            "target_vulnerable": False,
            "clear_cells": [],
        },
    ],
)
def test_blocked_out_of_range_too_close_and_unsupported_have_no_potential(changes):
    assert score(sample(firing_changes=changes)) is None


def test_walking_wall_and_non_axis_lane_do_not_count_as_firing_position():
    wall = "".join("0" if i % 7 == 3 else "1" for i in range(35))
    assert score(sample(grid_changes={"walkable": wall})) is None
    assert score(sample(firing_changes={"clear_cells": [11]})) is None


def test_monotone_progress_is_small_and_room_bounded():
    ledger = FiringProgress()
    previous = sample()
    ledger.begin(previous)
    rewards = []
    for i, x in enumerate([80.0, 120.0, 160.0, 120.0, 80.0, 40.0, 160.0], 1):
        current = sample(1 + i * 3, x=x)
        rewards.append(ledger.transition(previous, current))
        previous = current
    assert all(r > 0 for r in rewards[:3])
    assert rewards[3:] == [0] * 4
    assert sum(rewards) == pytest.approx(0.25 * (1 - score(sample())))
    assert sum(rewards) < 0.25


def test_standing_empty_shooting_wall_pressure_and_tiny_drift_do_not_pay():
    for x in (40.0, 40.1, 40.5):
        ledger = FiringProgress()
        before, after = sample(), sample(4, x=x)
        ledger.begin(before)
        assert ledger.transition(before, after) == 0


def test_software_reset_and_room_reentry_do_not_renew_credit():
    ledger = FiringProgress()
    before, best = sample(), sample(4, x=160.0)
    ledger.begin(before)
    assert ledger.transition(before, best) > 0
    for frame, room, visit in [(100, 4, 1), (200, 5, 2), (300, 4, 3)]:
        before = sample(frame, room=room, visit=visit)
        ledger.begin(before)
        reward = ledger.transition(before, sample(frame + 3, room=room, visit=visit, x=160.0))
        assert reward == 0 if room == 4 else reward > 0


def test_moving_target_alone_or_target_switch_does_not_pay():
    ledger = FiringProgress()
    before = sample()
    ledger.begin(before)
    raw = sample(4).model_dump(mode="json")
    raw["oracle"]["firing"]["target_position"]["x"] = 240.0
    raw["entity_frame"]["entities"][0]["position"]["x"] = 200.0
    after = LiveSnapshot.model_validate(raw)
    assert ledger.transition(before, after) == 0
    assert ledger.transition(after, sample(7, x=80.0, target=2)) == 0


def test_grid_change_and_unknown_geometry_do_not_pay():
    before = sample()
    for after in [
        sample(4, x=80.0, grid_changes={"walkable": "0" + "1" * 34}),
        sample(4, x=80.0, firing_changes={"clear_cells": []}),
    ]:
        ledger = FiringProgress()
        ledger.begin(before)
        # A removed positive clearance witness must not pay for stale geometry.
        assert ledger.transition(before, after) == 0


def test_replay_regression_and_history_exhaustion_fail_explicitly(monkeypatch):
    ledger = FiringProgress()
    before, after = sample(), sample(4, x=80.0)
    ledger.begin(before)
    ledger.transition(before, after)
    with pytest.raises(ProtocolError):
        ledger.transition(before, after)
    with pytest.raises(ProtocolError):
        ledger.begin(before)
    monkeypatch.setattr(firing, "MAX_ROOMS", 1)
    with pytest.raises(ProtocolError, match="history exhausted"):
        ledger.begin(sample(7, room=5))


@pytest.mark.parametrize(
    "changes",
    [
        {"version": True},
        {"clear_cells": [18, 18]},
        {"clear_cells": list(range(33))},
        {"tear_range": 0.0},
        {"tear_range": float("nan")},
        {"status": "unsupported"},
        {"target_id": None},
    ],
)
def test_invalid_geometry_refused(changes):
    with pytest.raises(ValidationError):
        FiringGeometry.model_validate({**sample().oracle.firing.model_dump(), **changes})


def test_hidden_or_displaced_target_refused_at_snapshot_boundary():
    for key, value in [("target_id", 20), ("target_position", {"x": 300.0, "y": 80.0})]:
        with pytest.raises(ValidationError, match="Firing target"):
            sample(firing_changes={key: value})


def test_oracle_range_does_not_change_policy_encoding():
    a, b = sample(), sample(firing_changes={"tear_range": 520.0})
    np.testing.assert_array_equal(encode(a.entity_frame).vector, encode(b.entity_frame).vector)


class FiringWorld(World):
    def __init__(self):
        super().__init__()
        self.x = 40.0

    def snapshot(self):
        return sample(self.frame, x=self.x)


def test_live_wrapper_adds_named_reward_without_oracle_input_or_episode_miscount():
    world = FiringWorld()
    world.hooks[1] = lambda w: setattr(w, "x", 80.0)
    records = []
    env = make_live_env(
        world, max_faults=0, firing_position_reward=True, record=lambda *r: records.append(r)
    )
    env.unwrapped.scenarios = (replace(env.unwrapped.scenarios[0], max_game_updates=3),)
    try:
        env.reset()
        observation, reward, _, truncated, info = env.step([2, 0])
        assert info["reward_components"]["firing_position"] > 0
        assert truncated and info["outcome"] == "unknown"
        assert info["episode"]["return"] == pytest.approx(reward)
        assert "firing" not in info and "oracle" not in info
        np.testing.assert_array_equal(observation, encode(world.snapshot().entity_frame).vector)
        assert any(r[0] == "firing_position_reward" for r in records)
    finally:
        env.close()


def test_missing_requested_telemetry_refuses_environment():
    world = World()
    world.enemies = {1: 10}
    env = make_live_env(world, firing_position_reward=True)
    try:
        with pytest.raises(ProtocolError, match="telemetry is missing"):
            env.reset()
    finally:
        env.close()


def test_opt_in_requires_gate_and_grid_navigation(tmp_path):
    with pytest.raises(ValueError):
        ObserverConfig(firing_geometry=True)
    with pytest.raises(ValueError):
        LiveRunOptions("random", tmp_path, firing_position_reward=True)
    assert not LiveRunOptions("random", tmp_path).firing_position_reward


def test_old_contract_refused_before_environment_creation(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(RAW_CONFIG), encoding="utf-8")
    cfg = cp.config_hash(RAW_CONFIG)
    cp.save_checkpoint(
        tmp_path / "out/seed-7/checkpoints",
        model=Artifact(),
        vec_normalize=Artifact(),
        algorithm="RecurrentPPO",
        cfg_hash=cfg,
        seed=7,
        timesteps=32,
        parent_checkpoint_id=None,
        rng_state={},
        reward_contract="live-conservative-v2",
    )
    called = []
    monkeypatch.setattr(live, "make_live_env", lambda *a, **kw: called.append(True))
    options = LiveRunOptions(
        "train",
        tmp_path / "out",
        config_path=path,
        seed=7,
        resume=True,
        minutes=0.2,
        combat_gate=True,
        auto_navigate=True,
        navigation_time_dominant=True,
        firing_position_reward=True,
    )
    with pytest.raises(cp.CheckpointError, match="reward contract"):
        live._train_run(None, options, lambda *a: None, lambda *a: None, tmp_path)
    assert not called


def test_new_contract_is_readable_only_when_explicitly_expected(tmp_path):
    manifest = cp.save_checkpoint(
        tmp_path,
        model=Artifact(),
        vec_normalize=Artifact(),
        algorithm="RecurrentPPO",
        cfg_hash="a" * 64,
        seed=7,
        timesteps=32,
        parent_checkpoint_id=None,
        rng_state={},
        reward_contract="live-firing-v3",
    )
    directory = tmp_path / manifest.checkpoint_id
    cp.load_checkpoint(
        directory,
        expected_config_hash="a" * 64,
        expected_seed=7,
        expected_reward_contract="live-firing-v3",
    )
    with pytest.raises(cp.CheckpointError):
        cp.load_checkpoint(
            directory,
            expected_config_hash="a" * 64,
            expected_seed=7,
            expected_reward_contract="live-conservative-v2",
        )
