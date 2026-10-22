"""OFFLINE tests for the frozen checkpoint policy. The checkpoint is trained on the synthetic
room only; nothing here touches or verifies Isaac."""

import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from isaac_threrisaifuture import checkpoint_policy
from isaac_threrisaifuture.checkpoint_policy import (
    CheckpointPolicy,
    InvalidPolicyOutput,
    _sha256,
)
from isaac_threrisaifuture.checkpoints import CheckpointError, config_hash
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episodes import Scenario
from isaac_threrisaifuture.evaluation import evaluate
from isaac_threrisaifuture.sim import SyntheticRoomBackend
from isaac_threrisaifuture.training import TrainingConfig, train

TOY = Scenario("toy", "validation", 1, 90, enemy_count=2, enemy_hp=7.0)
SEED = 7
RAW_CONFIG: dict[str, Any] = {
    "config_version": 1,
    "status": "synthetic_test_fixture",
    "algorithm": "RecurrentPPO",
    "device": "cpu",
    "num_envs": 1,
    "seed": SEED,
    "learning_rate": 0.0003,
    "gamma": 0.99,
    "gae_lambda": 0.95,
    "clip_range": 0.2,
    "ent_coef": 0.01,
    "n_steps": 32,
    "batch_size": 32,
    "n_epochs": 1,
    "lstm_hidden_size": 16,
    "action_repeat_game_updates": 3,
    "budget": {
        "total_timesteps": 32,
        "wall_time_minutes": 5.0,
        "stop_on_infrastructure_fault": True,
        "disk_limit_mb": 64,
    },
    "evaluation": {"episodes": 1, "split": "validation", "update_normalizer": False},
}
CFG_HASH = config_hash(RAW_CONFIG)


def synthetic_env(_: int = 0) -> IsaacCombatEnv:
    return IsaacCombatEnv(SyntheticRoomBackend(), [TOY])


@pytest.fixture(scope="module")
def trained(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One real RecurrentPPO + VecNormalize checkpoint saved by the project trainer."""
    out = tmp_path_factory.mktemp("synthetic-run")
    result = train(
        TrainingConfig.model_validate(RAW_CONFIG),
        CFG_HASH,
        seed=SEED,
        env_factory=synthetic_env,
        out_dir=out,
    )
    assert result.checkpoint_id is not None
    return out / "checkpoints" / result.checkpoint_id


@pytest.fixture
def checkpoint(trained: Path, tmp_path: Path) -> Path:
    """A private copy that a test may corrupt without affecting the others."""
    copy = tmp_path / trained.name
    shutil.copytree(trained, copy)
    return copy


def load(directory: Path, **kwargs: Any) -> CheckpointPolicy:
    kwargs.setdefault("expected_config_hash", CFG_HASH)
    return CheckpointPolicy(directory, **kwargs)


def observations(count: int, seed: int = 0) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.uniform(-1, 1, OBSERVATION_SIZE).astype(np.float32) for _ in range(count)]


class PredictSpy:
    def __init__(self, model: Any) -> None:
        self.model = model
        self.calls: list[dict[str, Any]] = []

    def predict(self, observation: Any, **kwargs: Any) -> Any:
        self.calls.append(
            {
                "observation": np.array(observation, copy=True),
                "state": None if kwargs["state"] is None else [s.copy() for s in kwargs["state"]],
                "episode_start": kwargs["episode_start"].copy(),
                "deterministic": kwargs["deterministic"],
            }
        )
        return self.model.predict(observation, **kwargs)


def test_identity_is_serializable_and_matches_artifact_hashes(checkpoint: Path) -> None:
    policy = load(checkpoint, expected_seed=SEED)
    identity = policy.identity.to_dict()
    assert json.loads(json.dumps(identity)) == identity
    assert identity["model_sha256"] == _sha256(checkpoint / "model.zip")
    assert identity["normalizer_sha256"] == _sha256(checkpoint / "vecnormalize.pkl")
    assert identity["config_hash"] == CFG_HASH and identity["deterministic"] is True
    assert policy.name == f"checkpoint:{checkpoint.name}"
    with pytest.raises(AttributeError):
        policy.identity.model_sha256 = "x"  # type: ignore[misc]


def test_statistics_frozen_and_normalization_applied_exactly_once(checkpoint: Path) -> None:
    policy = load(checkpoint)
    stats = policy._normalizer.obs_rms
    before = (stats.mean.copy(), stats.var.copy(), stats.count)
    spy = PredictSpy(policy._model)
    policy._model = spy
    inputs = observations(40)
    for obs in inputs:
        policy.act(obs)
    assert np.array_equal(stats.mean, before[0]) and np.array_equal(stats.var, before[1])
    assert stats.count == before[2]
    assert policy._normalizer.training is False and policy._normalizer.norm_reward is False
    eps, clip = policy._normalizer.epsilon, policy._normalizer.clip_obs
    for obs, call in zip(inputs, spy.calls, strict=True):
        once = np.clip((obs - before[0]) / np.sqrt(before[1] + eps), -clip, clip)
        assert np.allclose(call["observation"][0], once, atol=1e-5)
        assert call["deterministic"] is True


def test_recurrent_state_is_carried_and_cleared_on_reset(checkpoint: Path) -> None:
    policy = load(checkpoint)
    spy = PredictSpy(policy._model)
    policy._model = spy
    inputs = observations(12, seed=3)
    policy.reset(1)
    first = [policy.act(obs).tolist() for obs in inputs]
    assert spy.calls[0]["state"] is None and spy.calls[0]["episode_start"].all()
    assert spy.calls[1]["state"] is not None and not spy.calls[1]["episode_start"].any()
    assert any(np.abs(s).sum() > 0 for s in spy.calls[-1]["state"])
    policy.reset(2)  # a different seed must not change deterministic inference
    second = [policy.act(obs).tolist() for obs in inputs]
    restarted = spy.calls[len(inputs)]
    assert restarted["state"] is None and restarted["episode_start"].all()
    assert first == second


def test_hidden_state_influences_the_next_decision(checkpoint: Path) -> None:
    policy = load(checkpoint)
    probe = observations(1, seed=9)[0]
    policy.reset(0)
    fresh = policy._model.predict(
        policy._normalizer.normalize_obs(probe[None, :]),
        state=None,
        episode_start=np.ones((1,), dtype=bool),
        deterministic=True,
    )[1]
    for obs in observations(10, seed=4):
        policy.act(obs)
    carried = policy._state
    assert carried is not None
    assert not all(np.array_equal(a, b) for a, b in zip(fresh, carried, strict=True))


def test_inference_leaves_artifacts_unchanged_and_detects_tampering(checkpoint: Path) -> None:
    before = {p.name: _sha256(p) for p in checkpoint.iterdir()}
    policy = load(checkpoint)
    for obs in observations(30):
        policy.act(obs)
    policy.reset(0)
    policy.verify_unchanged()
    assert {p.name: _sha256(p) for p in checkpoint.iterdir()} == before
    with (checkpoint / "model.zip").open("ab") as handle:
        handle.write(b"tamper")
    with pytest.raises(CheckpointError, match="model changed"):
        policy.verify_unchanged()


def edit_manifest(directory: Path, **changes: Any) -> None:
    path = directory / "manifest.json"
    data = json.loads(path.read_text("utf-8"))
    data.update(changes)
    path.write_text(json.dumps(data), "utf-8")


@pytest.mark.parametrize(
    ("changes", "kwargs", "message"),
    [
        ({}, {"expected_config_hash": "0" * 64}, "different training configuration"),
        ({}, {"expected_seed": SEED + 1}, "seed"),
        ({"observation_schema_version": 99}, {}, "observation_schema_version"),
        ({"action_schema_version": 99}, {}, "action_schema_version"),
        ({"observation_schema_version": 1}, {}, "observation_schema_version"),
        ({"observation_schema_version": 2}, {}, "observation_schema_version"),
        ({"action_schema_version": 1}, {}, "action_schema_version"),
        ({"algorithm": "PPO"}, {}, "Unsupported algorithm"),
        ({"checkpoint_id": "other-id"}, {}, "directory"),
    ],
)
def test_incompatible_checkpoints_are_rejected(
    checkpoint: Path, changes: dict[str, Any], kwargs: dict[str, Any], message: str
) -> None:
    edit_manifest(checkpoint, **changes)
    with pytest.raises(CheckpointError, match=message):
        load(checkpoint, **kwargs)


def test_model_with_a_different_action_space_is_refused(
    checkpoint: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Pretend the project still used the two-head action space; the saved model has three.
    monkeypatch.setattr(checkpoint_policy, "ACTION_NVEC", (5, 5))
    with pytest.raises(CheckpointError, match="action space"):
        load(checkpoint)


def test_model_with_a_different_observation_space_is_refused(
    checkpoint: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(checkpoint_policy, "OBSERVATION_SIZE", 649)
    with pytest.raises(CheckpointError):
        load(checkpoint)


def test_moving_latest_pointer_root_is_refused(trained: Path) -> None:
    with pytest.raises(CheckpointError, match="latest pointer"):
        load(trained.parent)
    with pytest.raises(CheckpointError, match="latest pointer"):
        load(trained.parent / "latest.txt")


@pytest.mark.parametrize(
    ("name", "damage"),
    [
        ("vecnormalize.pkl", "delete"),
        ("model.zip", "delete"),
        ("manifest.json", "delete"),
        ("model.zip", "truncate"),
        ("vecnormalize.pkl", "garbage"),
        ("manifest.json", "garbage"),
    ],
)
def test_missing_or_corrupt_artifacts_are_checkpoint_errors(
    checkpoint: Path, name: str, damage: str
) -> None:
    path = checkpoint / name
    if damage == "delete":
        path.unlink()
    elif damage == "truncate":
        path.write_bytes(path.read_bytes()[:100])
    else:
        path.write_bytes(b"\x80\x04not a valid artifact")
    with pytest.raises(CheckpointError):
        load(checkpoint)


@pytest.mark.parametrize(
    "bad",
    [
        np.zeros(OBSERVATION_SIZE - 1, dtype=np.float32),
        np.zeros((1, OBSERVATION_SIZE), dtype=np.float32),
        np.full(OBSERVATION_SIZE, np.nan, dtype=np.float32),
        np.concatenate([np.zeros(OBSERVATION_SIZE - 1), [np.inf]]).astype(np.float32),
        ["not", "numbers"],
    ],
)
def test_malformed_observations_are_rejected_without_advancing_state(
    checkpoint: Path, bad: Any
) -> None:
    policy = load(checkpoint)
    policy.act(observations(1)[0])
    state = [s.copy() for s in policy._state or ()]
    with pytest.raises(ValueError):
        policy.act(bad)
    assert all(np.array_equal(a, b) for a, b in zip(state, policy._state or (), strict=True))
    assert not policy._episode_start.any()


class FakeModel:
    def __init__(self, action: Any) -> None:
        self.action = action

    def predict(self, observation: Any, **kwargs: Any) -> Any:
        return np.asarray(self.action), ("new-state",)


@pytest.mark.parametrize(
    "action",
    [
        [[0, 5, 0]],
        [[-1, 0, 0]],
        [[0, 0, 4]],
        [[0, 1]],
        [[0, 1, 2, 3]],
        [[0.5, 1.0, 0.0]],
        [0],
    ],
)
def test_invalid_model_outputs_are_rejected(checkpoint: Path, action: Any) -> None:
    policy = load(checkpoint)
    policy._model = FakeModel(action)
    with pytest.raises(InvalidPolicyOutput):
        policy.act(observations(1)[0])
    assert policy._state is None and policy._episode_start.all()


def test_frozen_policy_runs_in_the_existing_offline_evaluator(checkpoint: Path) -> None:
    policy = load(checkpoint)
    first = evaluate(policy, synthetic_env, [TOY], episodes=2, seeds=[1]).to_dict()
    second = evaluate(policy, synthetic_env, [TOY], episodes=2, seeds=[1]).to_dict()
    assert first["policy"] == policy.name and first["overall"]["attempted"] == 2
    assert first["episodes"] == second["episodes"]  # deterministic on a seeded synthetic room
    policy.verify_unchanged()


def resave_normalizer(directory: Path, corrupt: Any) -> None:
    """Corrupt the saved VecNormalize of a private copy through SB3's own save path."""
    policy = load(directory)
    corrupt(policy._normalizer)
    policy._normalizer.save(str(directory / "vecnormalize.pkl"))
    # This fixture changes semantic statistics intentionally. Keep storage hashes
    # valid so these tests still exercise normalizer validation after deserialization.
    edit_manifest(directory, normalizer_sha256=_sha256(directory / "vecnormalize.pkl"))


def set_item(name: str, index: int, value: Any) -> Any:
    return lambda n: getattr(n.obs_rms, name).__setitem__(index, value)


@pytest.mark.parametrize(
    "corrupt",
    [
        pytest.param(set_item("mean", 0, np.nan), id="mean-nan"),
        pytest.param(set_item("mean", 3, np.inf), id="mean-inf"),
        pytest.param(lambda n: setattr(n.obs_rms, "mean", n.obs_rms.mean[:-1]), id="mean-shape"),
        pytest.param(set_item("var", 0, np.nan), id="var-nan"),
        pytest.param(set_item("var", 5, -np.inf), id="var-inf"),
        pytest.param(set_item("var", 2, -1e-3), id="var-negative"),
        pytest.param(lambda n: setattr(n.obs_rms, "var", n.obs_rms.var[:-1]), id="var-shape"),
        pytest.param(lambda n: setattr(n.obs_rms, "count", np.nan), id="count-nan"),
        pytest.param(lambda n: setattr(n.obs_rms, "count", np.inf), id="count-inf"),
        pytest.param(lambda n: setattr(n.obs_rms, "count", 0.0), id="count-zero"),
        pytest.param(lambda n: setattr(n.obs_rms, "count", -4.0), id="count-negative"),
        pytest.param(lambda n: setattr(n.obs_rms, "count", "32"), id="count-string"),
        pytest.param(lambda n: setattr(n, "epsilon", 0.0), id="epsilon-zero"),
        pytest.param(lambda n: setattr(n, "epsilon", -1e-8), id="epsilon-negative"),
        pytest.param(lambda n: setattr(n, "epsilon", np.nan), id="epsilon-nan"),
        pytest.param(lambda n: setattr(n, "clip_obs", 0.0), id="clip-zero"),
        pytest.param(lambda n: setattr(n, "clip_obs", np.inf), id="clip-inf"),
        pytest.param(lambda n: setattr(n, "clip_obs", np.nan), id="clip-nan"),
        pytest.param(lambda n: setattr(n, "norm_obs", False), id="norm-obs-off"),
    ],
)
def test_corrupt_saved_normalizer_state_is_rejected_at_construction(
    checkpoint: Path, corrupt: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    resave_normalizer(checkpoint, corrupt)
    from sb3_contrib import RecurrentPPO

    def no_inference(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("predict must not run for a corrupt normalizer")

    monkeypatch.setattr(RecurrentPPO, "predict", no_inference)
    with pytest.raises(CheckpointError):
        load(checkpoint)


def test_zero_variance_statistics_remain_valid(checkpoint: Path) -> None:
    def zero(n: Any) -> None:
        n.obs_rms.var[:] = 0.0

    resave_normalizer(checkpoint, zero)
    policy = load(checkpoint)
    spy = PredictSpy(policy._model)
    policy._model = spy
    obs = observations(1)[0]
    policy.act(obs)
    stats, eps, clip = (
        policy._normalizer.obs_rms,
        policy._normalizer.epsilon,
        policy._normalizer.clip_obs,
    )
    expected = np.clip((obs - stats.mean) / np.sqrt(eps), -clip, clip)
    assert np.allclose(spy.calls[0]["observation"][0], expected, atol=1e-4)
    assert np.isfinite(spy.calls[0]["observation"]).all()


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_non_finite_normalized_input_never_reaches_predict(checkpoint: Path, bad: float) -> None:
    policy = load(checkpoint)
    policy.act(observations(1)[0])
    state = [s.copy() for s in policy._state or ()]
    spy = PredictSpy(policy._model)
    policy._model = spy
    policy._normalizer.normalize_obs = lambda obs: np.full_like(obs, bad)
    with pytest.raises(CheckpointError, match="non-finite"):
        policy.act(observations(1)[0])
    assert spy.calls == []
    assert all(np.array_equal(a, b) for a, b in zip(state, policy._state or (), strict=True))
