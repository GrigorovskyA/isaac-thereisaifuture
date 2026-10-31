"""OFFLINE tests for the pure continuous-training profile (config v2, retention, metrics,
fault cap, forever supervisor). The synthetic room proves plumbing only, never Isaac play."""

import csv
import dataclasses
import shutil
import types
from pathlib import Path
from typing import Any

import gymnasium as gym
import numpy as np
import pytest
import yaml

from isaac_threrisaifuture import checkpoints as cp
from isaac_threrisaifuture import live, training
from isaac_threrisaifuture import session_runner as runner
from isaac_threrisaifuture.checkpoints import CheckpointError, config_hash
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.entities import OBSERVATION_SCHEMA_VERSION
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import (
    FIELDS,
    EpisodeMetricsEnv,
    EpisodeMetricsWriter,
)
from isaac_threrisaifuture.episodes import EpisodeFault, Scenario
from isaac_threrisaifuture.sim import SyntheticRoomBackend
from isaac_threrisaifuture.training import (
    PURE_CONFIG,
    PureTrainingConfig,
    TrainingConfigError,
    apply_use_head_prior,
    load_training_config,
    train,
)
from isaac_threrisaifuture.training_metrics import TRAIN_FIELDS, TrainMetricsCallback

TOY = Scenario("toy", "validation", 1, 90, enemy_count=2, enemy_hp=7.0)
SHIPPED_PURE_CONFIG = PURE_CONFIG
ARCHIVED = Path(__file__).parents[1] / "archive" / "configs"
RAW: dict[str, Any] = yaml.safe_load(SHIPPED_PURE_CONFIG.read_text("utf-8"))


def synthetic_env(_: int = 0) -> IsaacCombatEnv:
    return IsaacCombatEnv(SyntheticRoomBackend(), [TOY])


def write_config(path: Path, **changes: dict[str, Any]) -> Path:
    """Tiny pure profile; `changes` update whole sections by key."""
    raw = yaml.safe_load(yaml.safe_dump(RAW))
    raw["contract"]["lstm_hidden_size"] = 16
    raw["contract"]["features_dim"] = 24
    raw["hyperparameters"].update(n_steps=32, batch_size=32, n_epochs=1)
    for section, values in changes.items():
        raw[section].update(values)
    path.write_text(yaml.safe_dump(raw), "utf-8")
    return path


def current_config(path: Path) -> Path:
    """Full-size pure config at the current observation schema."""
    out = path / "current.yaml"
    out.write_text(yaml.safe_dump(RAW), "utf-8")
    return out


# --- config v2 -------------------------------------------------------------------------------


def test_pure_config_loads_and_hashes_only_the_contract(tmp_path):
    config, digest = load_training_config(current_config(tmp_path))
    assert isinstance(config, PureTrainingConfig)
    assert digest == config_hash(RAW["contract"])
    tuned = write_config(
        tmp_path / "a.yaml", hyperparameters={"learning_rate": 1e-5, "ent_coef": 0.0}
    )
    assert (
        load_training_config(tuned)[1] == load_training_config(write_config(tmp_path / "b.yaml"))[1]
    )
    changed = write_config(tmp_path / "c.yaml", contract={"seed": 2})
    assert load_training_config(changed)[1] != load_training_config(tuned)[1]


@pytest.mark.parametrize(
    "section,change",
    [
        ("contract", {"extra": 1}),
        ("contract", {"reward_version": 1}),
        ("contract", {"seed": "1"}),
        ("hyperparameters", {"learning_rate": "0.1"}),
        ("hyperparameters", {"unknown": 1}),
        ("budget", {"max_consecutive_faults": 0}),
        ("retention", {"keep_latest": 1}),
        ("watchdog", {"stall_seconds": -1.0}),
    ],
)
def test_pure_config_is_strict(tmp_path, section, change):
    with pytest.raises(TrainingConfigError):
        load_training_config(write_config(tmp_path / "x.yaml", **{section: change}))


def test_pure_v4_config_pins_the_new_contract_and_refuses_older_lineages(tmp_path):
    config, digest = load_training_config(SHIPPED_PURE_CONFIG)
    assert SHIPPED_PURE_CONFIG.name == "training-pure-v4.yaml" and config.status == "pure_v4"
    contract = config.contract
    assert contract.observation_schema_version == OBSERVATION_SCHEMA_VERSION == 9
    assert contract.reward_version == 12 and contract.action_repeat_game_updates == 6
    assert contract.use_head_initial_none_probability == 0.85
    assert config.retention.keep_every == 100
    for name in ("training-pure-v1.yaml", "training-pure-v2.yaml", "training-pure-v3.yaml"):
        old = ARCHIVED / name  # older schemas and rewards are refused by this code
        with pytest.raises(
            TrainingConfigError, match="features_dim|use_head|reward version|schema"
        ):
            load_training_config(old)
        assert config_hash(yaml.safe_load(old.read_text("utf-8"))["contract"]) != digest
    stale_contracts = (
        {"reward_version": 11},
        {"reward_version": 10},
        {"reward_version": 9},
        {"reward_version": 8},
        {"reward_version": 7},
        {"reward_version": 6},
        {"reward_version": 5},
        {"reward_version": 4},
        {"observation_schema_version": 8},
        {"observation_schema_version": 7},
        {"observation_schema_version": 6},
        {"observation_schema_version": 5},
        {"observation_schema_version": 4},
    )
    for stale in stale_contracts:
        with pytest.raises(TrainingConfigError):
            load_training_config(write_config(tmp_path / "x.yaml", contract=stale))


@pytest.mark.parametrize("value", [0.0, 1.0, 1, -0.1, "0.85"])
def test_use_head_prior_must_be_a_float_strictly_between_zero_and_one(tmp_path, value):
    path = write_config(tmp_path / "x.yaml", contract={"use_head_initial_none_probability": value})
    with pytest.raises(TrainingConfigError):
        load_training_config(path)


def _head_probabilities(model, obs):
    import torch

    tensor = torch.as_tensor(obs, dtype=torch.float32)
    zeros = torch.zeros(1, len(obs), model.policy.lstm_actor.hidden_size)
    starts = torch.zeros(len(obs))
    heads = model.policy.get_distribution(tensor, (zeros, zeros), starts)[0].distribution
    return [head.probs.detach().numpy() for head in heads]


def test_use_head_prior_sets_only_the_use_head_probabilities():
    import numpy as np
    import torch
    from sb3_contrib import RecurrentPPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    env = DummyVecEnv([synthetic_env])
    kwargs: dict[str, Any] = {"policy_kwargs": {"lstm_hidden_size": 16}, "seed": 3}
    fresh = RecurrentPPO("MlpLstmPolicy", env, **kwargs)
    reference = RecurrentPPO("MlpLstmPolicy", env, **kwargs)
    obs = np.random.default_rng(0).normal(size=(8, OBSERVATION_SIZE)).astype(np.float32)
    apply_use_head_prior(fresh, 0.85)
    move, shoot, use = _head_probabilities(fresh, obs)
    assert np.allclose(use, [0.85, 0.05, 0.05, 0.05], atol=1e-3)
    # SB3 initialises action_net with gain 0.01, so the other heads stay near uniform.
    assert np.allclose(move, 0.2, atol=0.02) and np.allclose(shoot, 0.2, atol=0.02)
    assert torch.equal(reference.policy.action_net.weight[:10], fresh.policy.action_net.weight[:10])
    assert torch.equal(reference.policy.action_net.bias[:10], fresh.policy.action_net.bias[:10])


def test_use_head_prior_holds_with_the_input_projection():
    import numpy as np
    from sb3_contrib import RecurrentPPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    from isaac_threrisaifuture.policy import policy_kwargs

    model = RecurrentPPO(
        "MlpLstmPolicy", DummyVecEnv([synthetic_env]), policy_kwargs=policy_kwargs(16, 24), seed=3
    )
    apply_use_head_prior(model, 0.85)
    obs = np.random.default_rng(0).normal(size=(8, OBSERVATION_SIZE)).astype(np.float32)
    assert np.allclose(_head_probabilities(model, obs)[2], [0.85, 0.05, 0.05, 0.05], atol=1e-3)


def test_fresh_model_has_the_shared_input_projection_and_resume_refuses_another_width(tmp_path):
    from isaac_threrisaifuture.policy import InputProjection

    out = tmp_path / "run"
    run(write_config(tmp_path / "one.yaml"), out, 32)
    model, _, _ = load_latest(out)
    policy = model.policy
    assert isinstance(policy.features_extractor, InputProjection)
    assert policy.features_extractor.features_dim == 24
    assert policy.features_extractor.net[0].in_features == OBSERVATION_SIZE
    assert policy.share_features_extractor and policy.lstm_actor.input_size == 24
    assert policy.lstm_critic is not None and policy.lstm_critic.input_size == 24
    assert policy.lstm_actor.hidden_size == 16
    wider = write_config(tmp_path / "wide.yaml", contract={"features_dim": 32})
    config, digest = load_training_config(wider)
    with pytest.raises(CheckpointError, match="different training configuration"):
        train(config, digest, seed=1, env_factory=synthetic_env, out_dir=out, resume=True,
              reward_contract="pure-v11")  # fmt: skip
    model_after, _, _ = load_latest(out)
    assert model_after.policy.features_extractor.features_dim == 24  # nothing was written


def test_features_dim_binds_the_lineage_but_the_live_section_does_not(tmp_path):
    base = load_training_config(write_config(tmp_path / "a.yaml"))[1]
    wider = load_training_config(write_config(tmp_path / "b.yaml", contract={"features_dim": 32}))[
        1
    ]
    quiet = write_config(tmp_path / "c.yaml", live={"pause_during_updates": False})
    assert wider != base and load_training_config(quiet)[1] == base
    with pytest.raises(TrainingConfigError):
        load_training_config(write_config(tmp_path / "d.yaml", contract={"features_dim": 0}))
    with pytest.raises(TrainingConfigError):
        load_training_config(write_config(tmp_path / "e.yaml", live={"pause_during_updates": 1}))


def test_shipped_config_projects_to_512_and_pauses_updates_with_longer_rollouts():
    config, _ = load_training_config(SHIPPED_PURE_CONFIG)
    assert config.features_dim == 512 and config.lstm_hidden_size == 256
    assert config.hyperparameters.n_steps == 1024 and config.hyperparameters.batch_size == 128
    assert config.hyperparameters.n_epochs == 10 and config.hyperparameters.target_kl == 0.03
    assert config.hyperparameters.ent_coef == 0.005
    assert config.live.pause_during_updates is True


def test_use_head_prior_applies_to_a_fresh_model_and_never_on_resume(tmp_path, monkeypatch):
    calls: list[float] = []
    original = training.apply_use_head_prior
    monkeypatch.setattr(
        training, "apply_use_head_prior", lambda m, p: (calls.append(p), original(m, p))
    )
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml")
    run(path, out, 32)
    assert calls == [0.85]
    run(path, out, 64, resume=True)
    assert calls == [0.85]  # the resumed session did not apply it again


def test_pure_v1_and_v2_checkpoints_are_refused_by_the_pure_v4_lineage(tmp_path):
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml")
    run(path, out, 32)
    config, digest = load_training_config(path)
    old_digest = config_hash({**config.contract.model_dump(), "reward_version": 2})
    assert old_digest != digest
    with pytest.raises(CheckpointError):  # a checkpoint of the old contract hash
        train(config, old_digest, seed=1, env_factory=synthetic_env, out_dir=out, resume=True,
              reward_contract="pure-v11")  # fmt: skip


def test_pure_v3_checkpoint_is_refused_by_the_pure_v4_lineage(tmp_path):
    import json

    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml")
    run(path, out, 32)
    # Make the checkpoint look like pure-v3: its contract hash and its reward contract name.
    v3 = yaml.safe_load((ARCHIVED / "training-pure-v3.yaml").read_text("utf-8"))
    manifest_path = cp.latest_checkpoint_dir(out / "checkpoints") / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest.update(config_hash=config_hash(v3["contract"]), reward_contract="pure-v4")
    manifest_path.write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(CheckpointError):
        run(path, out, 64, resume=True)


def test_pure_v2_checkpoint_is_refused_by_the_pure_v4_lineage(tmp_path):
    import json

    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml")
    run(path, out, 32)
    # Make the checkpoint look like pure-v2: its contract hash and its reward contract name.
    v2 = yaml.safe_load((ARCHIVED / "training-pure-v2.yaml").read_text("utf-8"))
    manifest_path = cp.latest_checkpoint_dir(out / "checkpoints") / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest.update(config_hash=config_hash(v2["contract"]), reward_contract="pure-v3")
    manifest_path.write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(CheckpointError):
        run(path, out, 64, resume=True)


def test_train_csv_has_one_aligned_row_per_update_with_action_shares(tmp_path):
    out = tmp_path / "run"
    metrics = out / "metrics" / "train.csv"
    config, digest = load_training_config(write_config(tmp_path / "c.yaml"))
    for steps in (64, 128):  # two sessions append to the same file
        train(config, digest, seed=1, env_factory=synthetic_env, out_dir=out / "seed-1",
              max_timesteps=steps, resume=steps > 64, reward_contract="pure-v11",
              train_metrics_path=metrics)  # fmt: skip
    rows = list(csv.DictReader(metrics.open(encoding="utf-8")))
    assert [r["timesteps"] for r in rows] == ["32", "64", "96", "128"]
    assert [r["rollout_index"] for r in rows] == ["0", "1", "2", "3"]
    assert list(rows[0]) == list(TRAIN_FIELDS)
    assert all(float(r["rollout_seconds"]) >= 0 for r in rows)
    assert rows[0]["update_seconds"] == "" and rows[1]["update_seconds"] != ""
    assert [float(r["n_updates"]) for r in rows[:2]] == [1.0, 2.0]  # this update, not the last
    for row in rows:
        for head in ("move", "shoot", "use"):
            assert sum(float(v) for k, v in row.items() if k.startswith(head + "_")) == (
                pytest.approx(1.0)
            )
        assert row["entropy_loss"] != "" and row["value_loss"] != "" and row["wall_time"]


def test_train_timing_columns_split_rollout_from_update_pause(tmp_path):
    ticks = iter([10.0, 14.0, 20.0, 23.0])  # rollout 1: 10-14, pause 6 s, rollout 2: 20-23
    callback = TrainMetricsCallback(tmp_path / "train.csv", clock=lambda: next(ticks))
    model = types.SimpleNamespace(
        num_timesteps=32,
        rollout_buffer=types.SimpleNamespace(actions=np.zeros((4, 1, 3))),
        logger=types.SimpleNamespace(name_to_value={}),
    )
    callback.model = model  # type: ignore[assignment]
    for _ in range(2):
        callback._on_rollout_start()
        callback._on_rollout_end()
    callback._on_training_end()
    rows = list(csv.DictReader((tmp_path / "train.csv").open(encoding="utf-8")))
    assert [r["rollout_seconds"] for r in rows] == ["4.0", "3.0"]
    assert [r["update_seconds"] for r in rows] == ["", "6.0"]


def test_train_csv_write_failure_is_logged_once_and_training_continues(tmp_path, caplog):
    out = tmp_path / "run"
    blocked = tmp_path / "blocked"
    blocked.write_text("a file, not a directory", "utf-8")
    config, digest = load_training_config(write_config(tmp_path / "c.yaml"))
    result = train(config, digest, seed=1, env_factory=synthetic_env, out_dir=out,
                   max_timesteps=64, reward_contract="pure-v11",
                   train_metrics_path=blocked / "train.csv")  # fmt: skip
    assert result.timesteps == 64
    assert len([r for r in caplog.records if "Training metrics disabled" in r.message]) == 1


def test_pure_config_rejects_missing_section_and_stale_schema(tmp_path):
    raw = yaml.safe_load(yaml.safe_dump(RAW))
    del raw["watchdog"]
    path = tmp_path / "x.yaml"
    path.write_text(yaml.safe_dump(raw), "utf-8")
    with pytest.raises(TrainingConfigError):
        load_training_config(path)
    with pytest.raises(TrainingConfigError, match="schema versions"):
        load_training_config(
            write_config(tmp_path / "y.yaml", contract={"observation_schema_version": 2})
        )


# --- retention -------------------------------------------------------------------------------


class Artifact:
    def __init__(self, value: bytes) -> None:
        self.value = value

    def save(self, path: Any) -> None:
        Path(path).write_bytes(self.value)


def save_many(root: Path, count: int, **kwargs: Any) -> list[cp.CheckpointManifest]:
    manifests: list[cp.CheckpointManifest] = []
    parent = None
    for step in range(1, count + 1):
        manifest = cp.save_checkpoint(
            root,
            model=Artifact(b"m%d" % step),
            vec_normalize=Artifact(b"n%d" % step),
            algorithm="RecurrentPPO",
            cfg_hash="a" * 64,
            seed=1,
            timesteps=step * 10,
            parent_checkpoint_id=parent,
            rng_state={},
            **kwargs,
        )
        parent = manifest.checkpoint_id
        manifests.append(manifest)
    return manifests


def rollouts(root: Path) -> list[int]:
    found = []
    for path in root.iterdir():
        if path.is_dir():
            found.append(cp.read_manifest(path).rollout_index)
    return sorted(i for i in found if i is not None)


def test_retention_keeps_newest_and_every_fiftieth(tmp_path):
    root = tmp_path / "checkpoints"
    manifests = save_many(root, 120, retention=(5, 50))
    assert rollouts(root) == [50, 100, 116, 117, 118, 119, 120]
    latest = cp.latest_checkpoint_dir(root)
    assert latest.name == manifests[-1].checkpoint_id
    assert (root / manifests[-2].checkpoint_id).is_dir()  # the parent survives


def test_retention_never_deletes_latest_or_parent(tmp_path):
    root = tmp_path / "checkpoints"
    save_many(root, 10, retention=(2, 1000))
    assert rollouts(root) == [9, 10]


def test_retention_keeps_the_checkpoint_before_a_hyperparameter_change(tmp_path):
    root = tmp_path / "checkpoints"
    old = save_many(root, 5, retention=(2, 1000), hyperparameters={"gamma": 0.995})
    for step in range(6, 12):
        manifest = cp.save_checkpoint(
            root,
            model=Artifact(b"m%d" % step),
            vec_normalize=Artifact(b"n%d" % step),
            algorithm="RecurrentPPO",
            cfg_hash="a" * 64,
            seed=1,
            timesteps=step * 10,
            parent_checkpoint_id=cp.latest_checkpoint_dir(root).name,
            rng_state={},
            hyperparameters={"gamma": 0.998},
            retention=(2, 1000),
        )
    assert cp.pinned_checkpoints(root) == {old[-1].checkpoint_id}
    assert rollouts(root) == [5, 10, 11]
    assert manifest.checkpoint_id == cp.latest_checkpoint_dir(root).name


def test_retention_leaves_unindexed_and_pending_directories(tmp_path):
    root = tmp_path / "checkpoints"
    save_many(root, 3)
    legacy = root / "legacy"
    legacy.mkdir()
    (legacy / "manifest.json").write_text('{"checkpoint_id": "legacy"}')
    (root / ".pending-x").mkdir()
    assert len(cp.prune_checkpoints(root, keep_latest=2, keep_every=50)) == 1
    assert legacy.is_dir() and (root / ".pending-x").is_dir()


# --- fault cap -------------------------------------------------------------------------------


class Flaky(gym.Env):  # type: ignore[type-arg]
    observation_space = gym.spaces.Discrete(2)
    action_space = gym.spaces.Discrete(2)

    def __init__(self, pattern: str) -> None:
        self.pattern = list(pattern)

    def reset(self, *, seed: Any = None, options: Any = None) -> tuple[int, dict[str, Any]]:
        return 0, {}

    def step(self, action: Any) -> tuple[int, float, bool, bool, dict[str, Any]]:
        if self.pattern.pop(0) == "f":
            raise EpisodeFault("stalled transport")
        return 0, 0.0, False, False, {}


def test_consecutive_fault_cap_stops_and_success_resets():
    env = live.FaultTolerantEnv(Flaky("ffoffo"), max_faults=100, max_consecutive_faults=3)
    env.reset()
    for _ in range(6):  # never three faults in a row
        env.step(0)
    assert env.faults == 4 and env.consecutive_faults == 0
    capped = live.FaultTolerantEnv(Flaky("fff"), max_faults=100, max_consecutive_faults=3)
    capped.reset()
    capped.step(0)
    capped.step(0)
    with pytest.raises(EpisodeFault):
        capped.step(0)


# --- episode metrics -------------------------------------------------------------------------


def test_metrics_wrapper_appends_one_row_per_episode(tmp_path):
    path = tmp_path / "metrics" / "episodes.csv"
    env = EpisodeMetricsEnv(synthetic_env(), EpisodeMetricsWriter(path))
    env.reset(seed=1)
    done = False
    while not done:
        _, _, terminated, truncated, info = env.step(env.action_space.sample())
        done = terminated or truncated
    assert "episode_summary" in info
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len(rows) == 1 and tuple(rows[0]) == FIELDS
    assert rows[0]["outcome"] in ("terminated", "truncated")


def test_metrics_survive_monitor_and_vecnormalize(tmp_path):
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    path = tmp_path / "episodes.csv"
    writer = EpisodeMetricsWriter(path)
    venv = VecNormalize(DummyVecEnv([lambda: Monitor(EpisodeMetricsEnv(synthetic_env(), writer))]))
    venv.reset()
    for _ in range(40):
        venv.step([venv.action_space.sample()])
    assert len(list(csv.DictReader(path.open(encoding="utf-8")))) >= 1


# --- train: hyperparameters, lineage, live wiring ---------------------------------------------


def adam_steps(model: Any) -> float:
    state = model.policy.optimizer.state_dict()["state"]
    return min(float(entry["step"]) for entry in state.values())


def load_latest(out: Path) -> tuple[Any, cp.CheckpointManifest, Any]:
    from sb3_contrib import RecurrentPPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    directory = cp.latest_checkpoint_dir(out / "checkpoints")
    manifest = cp.read_manifest(directory)
    venv = VecNormalize.load(
        str(directory / manifest.normalizer_file), DummyVecEnv([lambda: synthetic_env()])
    )
    return (
        RecurrentPPO.load(directory / manifest.model_file, env=venv, device="cpu"),
        manifest,
        venv,
    )


def run(path: Path, out: Path, steps: int, **kwargs: Any) -> Any:
    config, digest = load_training_config(path)
    return train(
        config,
        digest,
        seed=1,
        env_factory=synthetic_env,
        out_dir=out,
        max_timesteps=steps,
        reward_contract="pure-v11",
        **kwargs,
    )


def test_two_sessions_change_hyperparameters_and_keep_state(tmp_path):
    out = tmp_path / "run"
    first = write_config(tmp_path / "one.yaml")
    run(first, out, 64)
    model1, manifest1, venv1 = load_latest(out)
    assert manifest1.hyperparameters is not None
    assert manifest1.hyperparameters["learning_rate"] == 0.0003
    assert manifest1.rollout_index == 2 and manifest1.timesteps == 64
    steps1, count1 = adam_steps(model1), float(venv1.obs_rms.count)
    assert steps1 > 0

    # Without --resume, existing checkpoints are refused.
    with pytest.raises(CheckpointError, match="explicit resume"):
        run(first, out, 128)

    second = write_config(
        tmp_path / "two.yaml",
        hyperparameters={"learning_rate": 1e-4, "ent_coef": 0.02, "n_steps": 64, "batch_size": 64},
    )
    run(second, out, 64 + 128, resume=True)
    model2, manifest2, venv2 = load_latest(out)
    assert manifest2.parent_checkpoint_id is not None
    assert manifest2.timesteps == 192 and manifest2.rollout_index == 4
    assert manifest2.config_hash == manifest1.config_hash  # same lineage
    assert manifest2.hyperparameters is not None
    assert manifest2.hyperparameters["learning_rate"] == 1e-4
    assert manifest2.hyperparameters["n_steps"] == 64
    assert model2.learning_rate == 1e-4 and model2.lr_schedule(1.0) == 1e-4
    assert model2.ent_coef == 0.02 and model2.n_steps == 64 and model2.batch_size == 64
    assert model2.rollout_buffer.buffer_size == 64
    # The optimizer and normalizer carry on; neither restarted from zero.
    assert adam_steps(model2) > steps1
    assert float(venv2.obs_rms.count) > count1


def test_resume_refuses_contract_change_and_missing_state(tmp_path):
    out = tmp_path / "run"
    run(write_config(tmp_path / "one.yaml"), out, 32)
    created: list[int] = []

    def factory(seed: int) -> Any:
        created.append(seed)
        return synthetic_env()

    changed = write_config(tmp_path / "two.yaml", contract={"lstm_hidden_size": 32})
    config, digest = load_training_config(changed)
    with pytest.raises(CheckpointError, match="different training configuration"):
        train(config, digest, seed=1, env_factory=factory, out_dir=out, resume=True,
              reward_contract="pure-v11")  # fmt: skip
    with pytest.raises(CheckpointError, match="No checkpoint to resume"):
        train(config, digest, seed=1, env_factory=factory, out_dir=tmp_path / "empty",
              resume=True, reward_contract="pure-v11")  # fmt: skip
    assert not created


def test_live_train_wires_watchdog_fault_cap_and_metrics(tmp_path, monkeypatch):
    seen: dict[str, Any] = {}

    def fake_env(_client: Any, **kwargs: Any) -> Any:
        seen.update(kwargs)
        return synthetic_env()

    monkeypatch.setattr(live, "make_live_env", fake_env)
    config = write_config(
        tmp_path / "pure.yaml",
        watchdog={"stall_seconds": 30.0},
        budget={"max_consecutive_faults": 4},
    )
    options = live.LiveRunOptions(
        mode="train", out_dir=tmp_path / "out", steps=64, minutes=5, config_path=config
    )
    live._train_run(None, options, lambda *_: None, lambda _: None)  # type: ignore[arg-type]
    assert seen["stall_seconds"] == 30.0 and seen["max_consecutive_faults"] == 4
    assert seen["max_faults"] > 1000  # no total budget in the pure profile
    assert seen["action_repeat"] == 6  # taken from the contract
    rows = list(csv.DictReader((tmp_path / "out/metrics/episodes.csv").open(encoding="utf-8")))
    assert rows
    manifest = cp.read_manifest(cp.latest_checkpoint_dir(tmp_path / "out/seed-1/checkpoints"))
    assert manifest.hyperparameters is not None and manifest.reward_contract == "pure-v11"


@pytest.mark.parametrize("enabled", [True, False])
def test_live_train_builds_the_update_pause_only_when_configured(tmp_path, monkeypatch, enabled):
    from isaac_threrisaifuture.update_pause import UpdatePause

    seen: dict[str, Any] = {}
    original = training.train

    def spy(*args: Any, **kwargs: Any) -> Any:
        seen["pause"] = kwargs["update_pause"]
        return original(*args, **kwargs)

    monkeypatch.setattr(live, "make_live_env", lambda _c, **kwargs: synthetic_env())
    monkeypatch.setattr(training, "train", spy)
    keyboard = types.SimpleNamespace(ready=lambda: True, press=lambda key, stop: None)
    config = write_config(tmp_path / "pure.yaml", live={"pause_during_updates": enabled})
    options = live.LiveRunOptions(
        mode="train", out_dir=tmp_path / "out", steps=32, minutes=5, config_path=config,
        keyboard=keyboard,  # type: ignore[arg-type]
    )  # fmt: skip
    live._train_run(None, options, lambda *_: None, lambda _: None)  # type: ignore[arg-type]
    if enabled:
        assert isinstance(seen["pause"], UpdatePause) and seen["pause"].keyboard is keyboard
    else:
        assert seen["pause"] is None
    rows = list(csv.DictReader((tmp_path / "out/metrics/train.csv").open(encoding="utf-8")))
    assert rows and (rows[0]["pause_ok"] == "") is True  # the synthetic backend cannot pause


# --- forever supervisor ----------------------------------------------------------------------


@pytest.fixture
def forever(tmp_path):
    config = write_config(tmp_path / "pure.yaml", budget={"max_consecutive_faults": 5})
    _, digest = load_training_config(config)
    run_root = tmp_path / "runs"
    options = runner.ForeverOptions(
        tmp_path / "game", tmp_path / "game.log", config, run_root, run_root / "supervisor",
        initialize=True,
    )  # fmt: skip
    return options, digest, run_root / "seed-1" / "checkpoints"


def test_forever_resumes_latest_after_each_lease_end_until_stop_file(forever):
    options, digest, root = forever
    plans: list[runner.SessionPlan] = []

    def session(plan: runner.SessionPlan) -> dict[str, Any]:
        plans.append(plan)
        parent = (
            cp.read_manifest(cp.latest_checkpoint_dir(root)).checkpoint_id if plans[1:] else None
        )
        manifest = cp.save_checkpoint(
            root,
            model=Artifact(b"m"),
            vec_normalize=Artifact(b"n"),
            algorithm="RecurrentPPO",
            cfg_hash=digest,
            seed=1,
            timesteps=len(plans) * 10,
            parent_checkpoint_id=parent,
            rng_state={},
            reward_contract="pure-v11",
        )
        if len(plans) == 3:
            options.stop_file.touch()
        return {"state": "completed", "latest_checkpoint": {"id": manifest.checkpoint_id}}

    outcome = runner.run_forever(options, session)
    assert outcome["stop_reason"] == "stop file" and len(plans) == 3
    assert [p.resume for p in plans] == [False, True, True]
    assert plans[0].parent_id == ""
    assert plans[1].parent_id == outcome["sessions"][0]["latest"]
    assert plans[2].parent_id == outcome["sessions"][1]["latest"]
    assert all(p.forever and p.max_restarts == 0 and p.seconds <= 28740 for p in plans)
    assert all(p.stop_file == options.stop_file for p in plans)
    assert len({p.output for p in plans}) == 3


def test_forever_keeps_only_the_newest_session_log_folders(forever):
    options, _, _ = forever
    options = dataclasses.replace(options, keep_sessions=2)
    options.output.mkdir(parents=True)
    for stamp in ("20261001-000000-0001", "20261002-000000-0001", "20261003-000000-0007"):
        (options.output / f"session-{stamp}").mkdir()
        (options.output / f"session-{stamp}" / "oracle.jsonl").write_text("x", encoding="utf-8")
    (options.output / "forever.json").write_text("{}", encoding="utf-8")
    options.stop_file.touch()  # stops before pruning and before any session
    runner.run_forever(options, lambda plan: {})
    assert len(list(options.output.glob("session-*"))) == 3
    options.stop_file.unlink()
    runner.run_forever(dataclasses.replace(options, initialize=False), lambda plan: {})
    kept = sorted(p.name for p in options.output.glob("session-*"))
    assert kept == ["session-20261002-000000-0001", "session-20261003-000000-0007"]
    assert (options.output / "forever.json").exists()


def test_forever_needs_initialize_for_a_fresh_start(forever):
    options, _, _ = forever
    calls: list[int] = []
    outcome = runner.run_forever(
        runner.ForeverOptions(**{**options.__dict__, "initialize": False}),
        lambda plan: calls.append(1) or {},
    )
    assert outcome["stop_reason"].startswith("no checkpoint") and not calls


def test_forever_stops_after_five_consecutive_faulted_sessions(forever):
    options, _, _ = forever
    states = iter(["fault"] * 4 + ["completed"] + ["fault"] * 5 + ["completed"])
    calls: list[int] = []

    def session(plan: runner.SessionPlan) -> dict[str, Any]:
        calls.append(1)
        return {"state": next(states), "fault": "bridge down"}

    outcome = runner.run_forever(options, session)
    assert len(calls) == 10  # the success in the middle reset the streak
    assert outcome["stop_reason"].startswith("fault cap: 5 consecutive")


def test_forever_stops_on_disk_cap(forever):
    options, _, _ = forever
    options.run_root.mkdir(parents=True)
    (options.run_root / "big.bin").write_bytes(b"x" * 5000)
    capped = runner.ForeverOptions(**{**options.__dict__, "disk_bytes": 1000})
    calls: list[int] = []
    outcome = runner.run_forever(capped, lambda plan: calls.append(1) or {})
    assert outcome["stop_reason"] == "disk cap" and not calls
    fresh = runner.ForeverOptions(
        **{**options.__dict__, "run_root": options.run_root / "x", "output": options.output / "y"}
    )
    result = runner.run_forever(
        fresh, lambda plan: {"state": "fault", "fault": "RuntimeError: Emergency disk budget"}
    )
    assert result["stop_reason"] == "disk cap" and len(result["sessions"]) == 1


def test_forever_refuses_a_changed_contract_and_stops_on_ctrl_c(forever, tmp_path):
    options, digest, root = forever
    cp.save_checkpoint(
        root, model=Artifact(b"m"), vec_normalize=Artifact(b"n"), algorithm="RecurrentPPO",
        cfg_hash=digest, seed=1, timesteps=10, parent_checkpoint_id=None, rng_state={},
        reward_contract="pure-v11",
    )  # fmt: skip

    def interrupt(plan: runner.SessionPlan) -> dict[str, Any]:
        raise KeyboardInterrupt

    assert runner.run_forever(options, interrupt)["stop_reason"] == "Ctrl+C"
    other = write_config(tmp_path / "other.yaml", contract={"lstm_hidden_size": 32})
    refused = runner.run_forever(
        runner.ForeverOptions(**{**options.__dict__, "config": other}), interrupt
    )
    assert refused["stop_reason"].startswith("lineage refused")


def test_forever_plan_rules(tmp_path):
    base = dict(
        game=tmp_path, game_log=tmp_path, config=tmp_path, run_root=tmp_path, output=tmp_path,
        parent_id="", seed=1, seconds=600, steps=runner.TIME_ONLY_STEPS, disk_bytes=10**6,
    )  # fmt: skip
    assert runner.SessionPlan(**base, max_restarts=0, forever=True, resume=False).forever
    with pytest.raises(ValueError):
        runner.SessionPlan(**base, max_restarts=0)  # 0 restarts only in forever mode
    with pytest.raises(ValueError):
        runner.SessionPlan(**base, max_restarts=5, forever=True)
    with pytest.raises(ValueError):
        runner.SessionPlan(**{**base, "seconds": 28800}, max_restarts=0, forever=True)


def test_extra_stop_file_cancels_a_session(tmp_path, monkeypatch):
    from test_session_runner import FakeRuntime, clock  # noqa: F401

    stop = tmp_path / "stop.forever"
    stop.touch()
    plan = runner.SessionPlan(
        tmp_path / "game", tmp_path / "game.log", tmp_path / "c.yaml", tmp_path / "runs",
        tmp_path / "session", "parent", 20, 120, 1000, 2, 10**7, stop_file=stop,
    )  # fmt: skip
    shutil.rmtree(tmp_path / "session", ignore_errors=True)
    from types import SimpleNamespace

    clk = SimpleNamespace(now=100.0)

    def sleep(_: float) -> None:
        clk.now += 10

    monkeypatch.setattr(
        runner, "time",
        SimpleNamespace(monotonic=lambda: clk.now, time=lambda: clk.now + 1000, sleep=sleep),
    )  # fmt: skip
    result = runner.supervise(plan, FakeRuntime(plan, clk, "timer"))
    assert result["state"] == "user_cancelled"


def test_train_csv_bridge_timing_columns_come_from_backend_counters_when_present(tmp_path):
    class Backend:
        def timing_counters(self):
            return {"wait_seconds": 3.0, "command_seconds": 0.5, "steps": 4.0, "snapshots": 10.0}

    def run(path, backend):
        ticks = iter([0.0, 4.0])
        callback = TrainMetricsCallback(path, clock=lambda: next(ticks))
        env = types.SimpleNamespace(controller=types.SimpleNamespace(backend=backend))
        callback.model = types.SimpleNamespace(  # type: ignore[assignment]
            num_timesteps=4,
            rollout_buffer=types.SimpleNamespace(actions=np.zeros((4, 1, 3))),
            logger=types.SimpleNamespace(name_to_value={}),
            get_env=lambda: types.SimpleNamespace(get_attr=lambda name: [env]),
        )
        callback._on_rollout_start()
        callback._on_rollout_end()
        callback._on_training_end()
        return list(csv.DictReader(path.open(encoding="utf-8")))

    (row,) = run(tmp_path / "live.csv", Backend())
    assert (row["game_wait_seconds"], row["command_seconds"]) == ("3.0", "0.5")
    assert row["snapshots_per_step"] == "2.5"
    (row,) = run(tmp_path / "sim.csv", object())
    assert row["rollout_seconds"] == "4.0"
    assert row["game_wait_seconds"] == row["command_seconds"] == row["snapshots_per_step"] == ""


@pytest.mark.parametrize("generation", [0, 1])
def test_train_csv_with_an_old_header_is_upgraded_to_the_new_columns(tmp_path, generation):
    from isaac_threrisaifuture.training_metrics import LEGACY_HEADERS

    fields = LEGACY_HEADERS[generation]  # 0: before bridge timing, 1: before pause columns
    path = tmp_path / "train.csv"
    old_row = ["2026-10-24T00:00:00+00:00", "512", "0", "100.0"] + [""] * (len(fields) - 4)
    path.write_text(",".join(fields) + "\n" + ",".join(old_row) + "\n", "utf-8")
    callback = TrainMetricsCallback(path, clock=iter([0.0, 1.0]).__next__)
    callback.model = types.SimpleNamespace(  # type: ignore[assignment]
        num_timesteps=4,
        rollout_buffer=types.SimpleNamespace(actions=np.zeros((4, 1, 3))),
        logger=types.SimpleNamespace(name_to_value={}),
    )
    callback._on_rollout_start()
    callback._on_rollout_end()
    callback._on_training_end()
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert list(rows[0]) == list(TRAIN_FIELDS) and len(rows) == 2
    assert rows[0]["rollout_seconds"] == "100.0" and rows[0]["game_wait_seconds"] == ""
    assert rows[0]["pause_seconds"] == rows[0]["pause_ok"] == ""
    assert rows[1]["rollout_seconds"] == "1.0" and rows[1]["rollout_index"] == "1"
    assert not (tmp_path / "train.csv.upgrade").exists()
