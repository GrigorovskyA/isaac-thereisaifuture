"""Offline sign, target budgeting and observable geometry compatibility regressions."""

from dataclasses import replace

import gymnasium as gym
import numpy as np
import pytest
from pydantic import ValidationError
from test_checkpoint_policy import RAW_CONFIG
from test_checkpoint_publication import Artifact
from test_firing_position import FiringWorld, sample

from isaac_threrisaifuture import checkpoints as cp
from isaac_threrisaifuture import firing_progress_v4 as v4
from isaac_threrisaifuture import live
from isaac_threrisaifuture.checkpoint_policy import CheckpointPolicy
from isaac_threrisaifuture.combat_progress import policy_state
from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.firing_position import FiringProgress as LegacyProgress
from isaac_threrisaifuture.live import LiveRunOptions, LiveSnapshot, make_live_env
from isaac_threrisaifuture.observation import ProtocolError
from isaac_threrisaifuture.policy_geometry import CombatGeometry, encode_geometry
from isaac_threrisaifuture.training import TrainingConfig, train


def value(snap):
    return v4.potential(
        snap.oracle.navigation.grid, snap.oracle.firing, snap.entity_frame.player_position
    )


def test_retreat_counterexample_corrected_and_legacy_replay_retained():
    before, after = sample(x=10.0), sample(4, x=1.0)
    old, new = LegacyProgress(), v4.FiringProgressV4()
    old.begin(before)
    new.begin(before)
    assert old.transition(before, after) > 0
    assert new.transition(before, after) == 0
    assert value(after) < value(before)
    toward = v4.FiringProgressV4()
    toward.begin(sample(x=1.0))
    assert toward.transition(sample(x=1.0), sample(4, x=10.0)) > 0


def test_continuous_open_path_across_cell_boundaries():
    scores = [value(sample(x=float(x))) for x in range(1, 161)]
    assert all(a < b for a, b in zip(scores, scores[1:], strict=False))
    assert scores[-1] == 1


def test_missing_interpolation_support_is_not_center_detour_fallback():
    raw = sample(x=10.0).model_dump(mode="json")
    mask = list(raw["oracle"]["navigation"]["grid"]["walkable"])
    mask[14] = "0"
    raw["oracle"]["navigation"]["grid"]["walkable"] = "".join(mask)
    assert value(LiveSnapshot.model_validate(raw)) is None
    assert value(sample(x=-1.0)) is None


def test_targets_have_separate_records_without_renewing_old_credit():
    ledger = v4.FiringProgressV4()
    a = sample(x=1.0)
    ledger.begin(a)
    b = sample(4, x=80.0)
    assert ledger.transition(a, b) > 0
    c = sample(7, x=1.0, target=2)
    assert ledger.transition(b, c) == 0
    d = sample(10, x=80.0, target=2)
    assert ledger.transition(c, d) > 0
    e = sample(13, x=1.0)
    assert ledger.transition(d, e) == 0
    assert ledger.transition(e, sample(16, x=80.0)) == 0
    ledger.begin(sample(19, x=1.0, visit=2))
    assert ledger.transition(sample(19, x=1.0, visit=2), sample(22, x=80.0, visit=2)) == 0


def test_many_targets_share_one_room_cap_and_target_limit_fails(monkeypatch):
    ledger = v4.FiringProgressV4()
    total = 0.0
    for target in range(1, 12):
        before = sample(target * 10, x=1.0, target=target)
        ledger.begin(before)
        total += ledger.transition(before, sample(target * 10 + 3, x=160.0, target=target))
    assert total == pytest.approx(0.25)
    monkeypatch.setattr(v4, "MAX_TARGETS", 1)
    limited = v4.FiringProgressV4()
    limited.begin(sample())
    with pytest.raises(ProtocolError, match="history exhausted"):
        limited.begin(sample(4, target=2))


def geometry_snapshot(*, clear=False):
    raw = sample().model_dump(mode="json")
    raw["combat_geometry"] = {
        "version": 2,
        "frame_id": raw["frame_id"],
        "weapon": "plain_tears",
        "tear_range": 260.0,
        "movement": [True, False, None, True],
        "enemies": [{"entity_id": 1, "clear": clear}],
    }
    return LiveSnapshot.model_validate(raw)


def test_blocked_in_range_target_has_explicit_features_and_unchanged_legacy_prefix():
    snap = geometry_snapshot()
    vector = encode_geometry(snap.entity_frame, snap.combat_geometry)
    assert vector.shape == (723,)
    np.testing.assert_array_equal(vector[:649], encode(snap.entity_frame).vector)
    np.testing.assert_allclose(vector[649:659], [1, 0.065, 1, 0, 1, 1, 0, 0, 1, 0])
    np.testing.assert_array_equal(vector[659:663], [1, 0, 1, 1])
    assert policy_state(snap, vector)["observation_schema"] == 2
    raw = snap.model_dump(mode="json")
    raw["oracle"]["enemies"][0]["hp"] = 1.0
    raw["oracle"]["firing"]["clear_cells"] = []
    changed = LiveSnapshot.model_validate(raw)
    np.testing.assert_array_equal(
        vector, encode_geometry(changed.entity_frame, changed.combat_geometry)
    )


def test_unknown_geometry_and_mismatched_frame_are_not_guessed():
    snap = geometry_snapshot()
    raw = snap.model_dump(mode="json")
    raw["combat_geometry"].update(
        weapon="unavailable",
        tear_range=None,
        movement=[None] * 4,
        enemies=[{"entity_id": 1, "clear": None}],
    )
    unknown = LiveSnapshot.model_validate(raw)
    assert np.all(encode_geometry(unknown.entity_frame, unknown.combat_geometry)[649:] == 0)
    for changes in (
        {"frame_id": 99},
        {"enemies": [{"entity_id": 99, "clear": True}]},
        {"weapon": "unsupported"},
    ):
        invalid = snap.model_dump(mode="json")
        invalid["combat_geometry"].update(changes)
        with pytest.raises(ValidationError):
            LiveSnapshot.model_validate(invalid)


class GeometryWorld(FiringWorld):
    def snapshot(self):
        snap = super().snapshot()
        return snap.model_copy(
            update={
                "combat_geometry": CombatGeometry(
                    version=2,
                    frame_id=snap.frame_id,
                    weapon="plain_tears",
                    tear_range=260.0,
                    movement=[False] * 4,
                    enemies=[{"entity_id": 1, "clear": False}],
                )
            }
        )


def test_live_wrapper_and_diagnostics_use_same_observation2():
    world = GeometryWorld()
    env = make_live_env(world, combat_geometry=True)
    env.unwrapped.scenarios = (replace(env.unwrapped.scenarios[0], max_game_updates=3),)
    try:
        obs, _ = env.reset()
        assert obs.shape == (723,)
        obs, *_ = env.step([0, 0])
        assert obs.shape == (723,)
        assert policy_state(world.snapshot(), obs)["observation_schema"] == 2
    finally:
        env.close()


@pytest.mark.parametrize(
    "contract,schema,geometry",
    [("live-firing-v3", 1, False), ("live-firing-v4", 1, True), ("live-firing-v4", 2, True)],
)
def test_incompatible_contract_or_observation_refused_before_env(
    tmp_path, monkeypatch, contract, schema, geometry
):
    import yaml

    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(RAW_CONFIG), encoding="utf-8")
    cp.save_checkpoint(
        tmp_path / "seed-7/checkpoints",
        model=Artifact(),
        vec_normalize=Artifact(),
        algorithm="RecurrentPPO",
        cfg_hash=cp.config_hash(RAW_CONFIG),
        seed=7,
        timesteps=32,
        parent_checkpoint_id=None,
        rng_state={},
        reward_contract=contract,
        observation_schema=schema,
    )
    called = []
    monkeypatch.setattr(live, "make_live_env", lambda *a, **k: called.append(True))
    options = LiveRunOptions(
        "train",
        tmp_path,
        config_path=path,
        resume=True,
        seed=7,
        minutes=0.2,
        combat_gate=True,
        auto_navigate=True,
        navigation_time_dominant=True,
        firing_position_reward=True,
        combat_geometry=geometry,
        boundary_progress_reward=(schema == 2),
    )
    with pytest.raises(cp.CheckpointError):
        live._train_run(None, options, lambda *a: None, lambda *a: None, tmp_path)
    assert not called


class ShapeWorld(gym.Env):
    observation_space = gym.spaces.Box(-1.0, 1.0, (723,), np.float32)
    action_space = gym.spaces.MultiDiscrete([5, 5])

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        return np.zeros(723, np.float32), {}

    def step(self, action):
        return np.zeros(723, np.float32), 0.0, False, False, {}


def test_observation2_training_save_reload_and_legacy_refusal(tmp_path):
    raw = {**RAW_CONFIG, "budget": {**RAW_CONFIG["budget"], "total_timesteps": 64}}
    cfg = TrainingConfig.model_validate(raw)
    hashed = cp.config_hash(raw)
    first = train(
        cfg,
        hashed,
        seed=7,
        env_factory=lambda _: ShapeWorld(),
        out_dir=tmp_path,
        max_timesteps=32,
        reward_contract="live-firing-v4",
        observation_schema=2,
    )
    path = tmp_path / "checkpoints" / first.checkpoint_id
    with pytest.raises(cp.CheckpointError, match="observation_schema"):
        cp.load_checkpoint(path, expected_config_hash=hashed, expected_seed=7)
    frozen = CheckpointPolicy(path, expected_config_hash=hashed, expected_seed=7)
    assert frozen.act(np.zeros(723, np.float32)).shape == (2,)
    with pytest.raises(ValueError):
        frozen.act(np.zeros(649, np.float32))
    resumed = train(
        cfg,
        hashed,
        seed=7,
        env_factory=lambda _: ShapeWorld(),
        out_dir=tmp_path,
        resume=True,
        max_timesteps=64,
        reward_contract="live-firing-v4",
        observation_schema=2,
    )
    assert resumed.timesteps == 64
