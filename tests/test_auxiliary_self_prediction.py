"""OFFLINE tests for the auxiliary self-prediction losses (latent next-state, reward, termination)
with their replay, the auxiliary phase of PureRecurrentPPO, its checkpoint state and contract.
Synthetic rooms and toy tensors prove plumbing only, never Isaac play."""

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from test_pure_training import RAW, load_latest, run, synthetic_env, write_config
from torch import nn

from isaac_threrisaifuture import auxiliary
from isaac_threrisaifuture.auxiliary import (
    PROJECTION_DIM,
    AuxiliaryLearner,
    Replay,
    RolloutRecord,
    RolloutRecorder,
    ema_update,
    one_hot_actions,
)
from isaac_threrisaifuture.checkpoint_policy import CheckpointPolicy
from isaac_threrisaifuture.checkpoints import (
    AUXILIARY_FILE,
    MANIFEST_NAME,
    CheckpointError,
    config_hash,
    latest_checkpoint_dir,
)
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE, continuous_mask
from isaac_threrisaifuture.episodes import ACTION_NVEC
from isaac_threrisaifuture.learner import PureRecurrentPPO
from isaac_threrisaifuture.normalization import ContinuousVecNormalize
from isaac_threrisaifuture.policy import StructuredFeatures, policy_kwargs
from isaac_threrisaifuture.training import PURE_CONFIG, TrainingConfigError, load_training_config
from isaac_threrisaifuture.training_metrics import AUXILIARY

# Contract of the rollout-advantage lineage (never trained natively), refused by this one.
ROLLOUT_ADVANTAGE_HASH = "5eb6f93af48955b55130c410fff59d109bea133d81688a023bbd6c59687c4f14"
AUXILIARY_HASH = "0399c37db311f00df37cea79a66385ff6cd7150dfcfa0c9e3e46415f577da79a"
NVEC = list(ACTION_NVEC)


def model(**kwargs: Any) -> PureRecurrentPPO:
    venv = ContinuousVecNormalize(DummyVecEnv([lambda: Monitor(synthetic_env())]), gamma=0.998)
    options: dict[str, Any] = {
        "n_steps": 64, "batch_size": 32, "n_epochs": 1, "seed": 3,
        "auxiliary": "spr_reward_done_v1", "aux_steps": 4, "aux_batch": 32,
    }  # fmt: skip
    return PureRecurrentPPO("MlpLstmPolicy", venv, policy_kwargs=policy_kwargs(16, 24),
                            device="cpu", **{**options, **kwargs})  # fmt: skip


class Identity:
    """Normalizer stand-in for toy observations: nothing is scaled."""

    def normalize_obs(self, obs: np.ndarray) -> np.ndarray:
        return obs

    def normalize_reward(self, reward: np.ndarray) -> np.ndarray:
        return reward


def record(steps: int, size: int, mask: np.ndarray, *, start: int = 0, done_every: int = 0):
    """Binary observations with a running index in feature 0, so rows can be identified."""
    rng = np.random.default_rng(start)
    obs = (rng.random((steps + 1, size)) > 0.5).astype(np.float32)
    obs[:, 0] = np.arange(start, start + steps + 1)
    dones = np.zeros(steps, dtype=bool)
    if done_every:
        dones[done_every - 1 :: done_every] = True
    return RolloutRecord(
        continuous=obs[:, mask], discrete=obs[:, ~mask].astype(np.float16),
        actions=rng.integers(0, 4, size=(steps, 3)), rewards=rng.random(steps).astype(np.float32),
        dones=dones, terminated=dones.copy(),
    )  # fmt: skip


# --- heads and EMA -----------------------------------------------------------------------------


def test_heads_have_the_documented_shapes_and_the_target_starts_as_a_frozen_copy():
    extractor = StructuredFeatures(synthetic_env().observation_space, features_dim=24)
    learner = AuxiliaryLearner(extractor, 24, NVEC, replay_rollouts=2, target_ema=0.99,
                               device="cpu")  # fmt: skip
    actions = torch.tensor([[0, 4, 3], [2, 1, 0]])
    onehot = one_hot_actions(actions, NVEC)
    assert onehot.shape == (2, 14) and onehot.sum(dim=1).tolist() == [3.0, 3.0]
    assert onehot[0, 0] == onehot[0, 5 + 4] == onehot[0, 10 + 3] == 1.0
    heads = learner.model.heads
    joint = torch.zeros(5, 24 + 14)
    assert heads.transition(joint).shape == (5, 24)
    assert heads.projection(heads.transition(joint)).shape == (5, PROJECTION_DIM)
    assert heads.reward(joint).shape == heads.done(joint).shape == (5, 1)
    online, target = extractor.state_dict(), learner.model.target_extractor.state_dict()
    assert all(torch.equal(online[name], target[name]) for name in online)
    assert not any(p.requires_grad for p in learner.model.target_parameters())
    trained = {id(p) for group in learner.optimizer.param_groups for p in group["params"]}
    assert {id(p) for p in extractor.parameters()} <= trained
    assert not trained & {id(p) for p in learner.model.target_parameters()}


def test_ema_update_moves_the_target_by_one_minus_tau():
    online, target = nn.Linear(3, 2), nn.Linear(3, 2)
    before = target.weight.detach().clone()
    ema_update(target, online, 0.9)
    expected = 0.9 * before + 0.1 * online.weight.detach()
    assert torch.allclose(target.weight, expected)
    ema_update(target, online, 0.0)
    assert torch.equal(target.weight, online.weight)


# --- replay ------------------------------------------------------------------------------------


def test_replay_keeps_the_last_rollouts_and_never_pairs_across_an_episode_end():
    size = 12
    mask = np.zeros(size, dtype=bool)
    mask[:3] = True  # feature 0 (the index) is continuous, the rest binary
    replay = Replay(2, mask)
    for start in (0, 100, 200):
        replay.add(record(10, size, mask, start=start, done_every=4))
    assert len(replay.records) == 2 and len(replay) == 20  # the first rollout dropped out
    assert replay.nbytes == sum(r.nbytes for r in replay.records)
    sample = replay.sample(500)
    index = sample.observations[:, 0]
    assert set(np.unique(index // 100).astype(int)) == {1, 2}
    step = (index % 100).astype(int)
    assert np.array_equal(sample.next_valid, ~np.isin(step, [3, 7]))  # dones at t = 3 and 7
    valid = sample.next_valid
    assert np.array_equal(sample.next_observations[valid, 0], index[valid] + 1)
    assert set(np.unique(sample.observations[:, 3:])) <= {0.0, 1.0}  # float16 holds 0/1 exactly
    with pytest.raises(ValueError):
        Replay(2, mask).sample(1)


def test_the_learner_records_raw_rollouts_that_match_its_rollout_buffer():
    ppo = model(n_epochs=1)
    ppo.learn(128)
    learner = ppo.auxiliary_learner
    assert learner is not None and len(learner.replay.records) == 2
    last = learner.replay.records[-1]
    buffer = ppo.rollout_buffer
    mask = continuous_mask()
    assert last.continuous.shape == (65, int(mask.sum())) and last.discrete.dtype == np.float16
    # Binary and one-hot features pass the normalizer unchanged, so they equal the buffer's.
    observations = buffer.observations.reshape(64, -1)
    assert np.array_equal(last.discrete[:64].astype(np.float32), observations[:, ~mask])
    assert np.array_equal(last.actions, buffer.actions.reshape(64, 3).astype(np.int64))
    starts = buffer.episode_starts.reshape(64)
    assert np.array_equal(last.dones[:-1], starts[1:].astype(bool))
    assert not (last.terminated & ~last.dones).any()


# --- auxiliary phase ---------------------------------------------------------------------------


def test_the_auxiliary_phase_lowers_its_losses_on_a_tiny_task():
    torch.manual_seed(0)
    np.random.seed(0)
    size = 16
    mask = np.zeros(size, dtype=bool)
    extractor = nn.Sequential(nn.Linear(size, 32), nn.ReLU())
    learner = AuxiliaryLearner(extractor, 32, NVEC, replay_rollouts=4, target_ema=0.9,
                               device="cpu")  # fmt: skip
    learner.replay = Replay(4, mask)
    rng = np.random.default_rng(1)
    for _ in range(2):
        steps = 128
        obs = (rng.random((steps + 1, size)) > 0.5).astype(np.float32)
        actions = rng.integers(0, 4, size=(steps, 3))
        obs[1:, :4] = np.eye(4, dtype=np.float32)[actions[:, 0]]  # next obs follows the move
        dones = obs[:-1, 5] > 0.5  # an ending is visible in the observation
        learner.replay.add(
            RolloutRecord(
                continuous=obs[:, mask], discrete=obs[:, ~mask].astype(np.float16),
                actions=actions, rewards=(actions[:, 1] == 2).astype(np.float32),
                dones=dones, terminated=dones,
            )
        )  # fmt: skip
    probe = learner.replay.sample(256)

    def losses() -> dict[str, float]:
        with torch.no_grad():
            return {k: float(v) for k, v in learner.losses(probe, Identity()).items()}

    before = losses()
    means = learner.update(Identity(), steps=300, batch=64, learning_rate=3e-3, max_grad_norm=0.5)
    after = losses()
    assert set(means) == {"latent", "reward", "done"}
    for name in ("reward", "done"):
        assert after[name] < 0.5 * before[name], (name, before, after)
    assert after["latent"] < before["latent"]


def test_the_phase_logs_losses_and_the_policy_kl_it_caused():
    ppo = model()
    ppo.learn(64)
    logged = ppo.logger.name_to_value
    for name in AUXILIARY:
        assert np.isfinite(logged[f"train/{name}"])
    assert logged["train/aux_approx_kl"] >= 0.0 and logged["train/aux_seconds"] > 0.0
    buffer = ppo.rollout_buffer
    first = ppo._rollout_log_probs(buffer)
    assert first.shape == (64,) and torch.equal(first, ppo._rollout_log_probs(buffer))


def kl_after_phase(aux_coef: float) -> tuple[float, float]:
    """Logged KL of one phase and the largest change of action probabilities on a fixed batch."""
    ppo = model(aux_coef=aux_coef, aux_steps=16)
    ppo.learn(64)  # one rollout, the PPO epoch and a first phase fill the replay
    obs = torch.as_tensor(ppo.rollout_buffer.observations[:32])
    with torch.no_grad():
        before = ppo.policy.get_distribution(obs, ppo._last_lstm_states.pi,
                                             torch.ones(32))[0]  # fmt: skip
        probs = [d.probs.clone() for d in before.distribution]
    ppo._auxiliary_phase(ppo.rollout_buffer)
    with torch.no_grad():
        after = ppo.policy.get_distribution(obs, ppo._last_lstm_states.pi, torch.ones(32))[0]
    change = max(
        float((d.probs - p).abs().max()) for d, p in zip(after.distribution, probs, strict=True)
    )
    return float(ppo.logger.name_to_value["train/aux_approx_kl"]), change


def test_a_tiny_coefficient_leaves_the_policy_unchanged_and_a_large_one_shows_in_the_kl():
    tiny_kl, tiny_change = kl_after_phase(1e-9)
    big_kl, big_change = kl_after_phase(100.0)
    assert tiny_kl < 1e-9 and tiny_change < 1e-6
    assert big_kl > 1e3 * max(tiny_kl, 1e-12) and big_change > 1e3 * tiny_change


def test_a_zero_coefficient_skips_the_phase():
    ppo = model(aux_coef=0.0)
    ppo.learn(64)
    assert "train/aux_approx_kl" not in ppo.logger.name_to_value
    assert ppo.auxiliary_learner is not None and len(ppo.auxiliary_learner.replay) == 64


# --- checkpoints, resume, frozen evaluation ----------------------------------------------------


def test_checkpoints_save_and_resume_restores_the_auxiliary_state(tmp_path, monkeypatch):
    loads: list[Path] = []
    original = AuxiliaryLearner.load

    def load(self: AuxiliaryLearner, path: Path) -> None:
        original(self, path)
        saved = torch.load(path, weights_only=True)["model"]
        state = self.model.state_dict()
        assert saved.keys() == state.keys()
        assert all(torch.equal(saved[name], state[name]) for name in saved)
        assert len(self.replay) == 0  # the replay is in memory only
        loads.append(path)

    monkeypatch.setattr(AuxiliaryLearner, "load", load)
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml")
    run(path, out, 32)
    directory = latest_checkpoint_dir(out / "checkpoints")
    manifest = json.loads((directory / MANIFEST_NAME).read_text("utf-8"))
    assert manifest["auxiliary_file"] == AUXILIARY_FILE and manifest["auxiliary_sha256"]
    state = torch.load(directory / AUXILIARY_FILE, weights_only=True)
    assert set(state) == {"format", "model", "optimizer"} and state["optimizer"]["state"]
    run(path, out, 64, resume=True)
    assert loads == [directory / AUXILIARY_FILE]
    saved, latest, _ = load_latest(out)  # plain RecurrentPPO, as frozen evaluation loads it
    assert latest.timesteps == 64 and latest.auxiliary_file == AUXILIARY_FILE
    assert saved.auxiliary == "spr_reward_done_v1" and not hasattr(saved, "auxiliary_learner")


def test_resume_without_auxiliary_state_is_refused(tmp_path):
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml")
    run(path, out, 32)
    manifest_path = latest_checkpoint_dir(out / "checkpoints") / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest.update(auxiliary_file=None, auxiliary_sha256=None)
    manifest_path.write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(CheckpointError, match="no auxiliary state"):
        run(path, out, 64, resume=True)


def test_frozen_evaluation_loads_the_policy_and_ignores_the_auxiliary_state(tmp_path):
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml")
    run(path, out, 32)
    directory = latest_checkpoint_dir(out / "checkpoints")
    policy = CheckpointPolicy(directory, expected_config_hash=load_training_config(path)[1],
                              observation_normalization="continuous_only")  # fmt: skip
    policy.reset(0)
    action = policy.act(np.zeros(OBSERVATION_SIZE, dtype=np.float32))
    assert action.shape == (3,) and (action < np.array(ACTION_NVEC)).all()
    (directory / AUXILIARY_FILE).unlink()  # never read by inference
    policy.verify_unchanged()


# --- metrics and contract ----------------------------------------------------------------------


def test_train_csv_gains_the_auxiliary_columns(tmp_path):
    rows: dict[str, list[dict[str, str]]] = {}
    for name in ("spr_reward_done_v1", "none"):
        path = write_config(tmp_path / f"{name}.yaml", contract={"auxiliary": name})
        metrics = tmp_path / name / "train.csv"
        run(path, tmp_path / name, 64, train_metrics_path=metrics)
        rows[name] = list(csv.DictReader(metrics.open(encoding="utf-8")))
    assert len(rows["spr_reward_done_v1"]) == 2
    for row in rows["spr_reward_done_v1"]:
        assert all(np.isfinite(float(row[name])) for name in AUXILIARY)
    for row in rows["none"]:
        assert all(row[name] == "" for name in AUXILIARY)


def test_the_contract_binds_the_auxiliary_losses_and_refuses_older_checkpoints(tmp_path):
    config, digest = load_training_config(PURE_CONFIG)
    assert config.contract.auxiliary == "spr_reward_done_v1" and config.device == "cuda"
    without_e3b = {name: value for name, value in RAW["contract"].items() if name != "intrinsic"}
    assert config_hash(without_e3b) == AUXILIARY_HASH  # the auxiliary lineage before E3B
    assert digest not in (AUXILIARY_HASH, ROLLOUT_ADVANTAGE_HASH)
    hyper = config.hyperparameters
    assert (hyper.aux_coef, hyper.aux_steps, hyper.aux_batch) == (1.0, 64, 256)
    assert (hyper.replay_rollouts, hyper.target_ema, hyper.batch_size) == (8, 0.99, 256)
    older = {name: value for name, value in without_e3b.items() if name != "auxiliary"}
    assert config_hash(older) == ROLLOUT_ADVANTAGE_HASH  # absent means `none`, hash kept
    with pytest.raises(TrainingConfigError):
        load_training_config(write_config(tmp_path / "x.yaml", contract={"auxiliary": "spr"}))
    # A checkpoint of a contract without auxiliary losses is refused by this one.
    out = tmp_path / "run"
    run(write_config(tmp_path / "none.yaml", contract={"auxiliary": "none"}), out, 32)
    with pytest.raises(CheckpointError, match="different training configuration"):
        run(write_config(tmp_path / "aux.yaml"), out, 64, resume=True)


def test_auxiliary_losses_need_a_single_env_and_a_known_name():
    venv = ContinuousVecNormalize(DummyVecEnv([synthetic_env, synthetic_env]), gamma=0.998)
    with pytest.raises(ValueError, match="n_envs must be 1"):
        PureRecurrentPPO("MlpLstmPolicy", venv, n_steps=8, auxiliary="spr_reward_done_v1",
                         policy_kwargs=policy_kwargs(16, 24), device="cpu")  # fmt: skip
    with pytest.raises(ValueError, match="Unsupported auxiliary"):
        model(auxiliary="spr")
    assert auxiliary.AUXILIARIES == ("none", "spr_reward_done_v1")


def test_recorder_marks_time_limits_as_ends_but_not_as_outcomes():
    recorder = RolloutRecorder(np.zeros((1, 4), dtype=np.float32))
    recorder.step(
        np.ones((1, 4)), np.array([1.5]), np.array([True]), [{"TimeLimit.truncated": True}]
    )
    recorder.step(np.ones((1, 4)), np.array([-2.0]), np.array([True]), [{}])
    recorder.step(np.ones((1, 4)), np.array([0.0]), np.array([False]), [{}])
    done = recorder.finish(np.zeros((3, 1, 3)), np.array([True, False, False, False]))
    assert done.dones.tolist() == [True, True, False]
    assert done.terminated.tolist() == [False, True, False]
    assert done.rewards.tolist() == [1.5, -2.0, 0.0] and done.continuous.shape == (4, 1)
