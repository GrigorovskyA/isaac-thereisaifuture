"""OFFLINE tests for rollout-level advantage normalization, the epoch-mean KL stop and the cuda
device contract. The Mac has no GPU: cuda is only ever monkeypatched. Synthetic rooms prove
plumbing only, never Isaac play."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml
from sb3_contrib import RecurrentPPO
from sb3_contrib.common.recurrent.buffers import RecurrentRolloutBuffer
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from test_pure_training import RAW, load_latest, run, synthetic_env, write_config

from isaac_threrisaifuture import learner
from isaac_threrisaifuture import session_runner as runner
from isaac_threrisaifuture.checkpoints import config_hash
from isaac_threrisaifuture.learner import PureRecurrentPPO, normalize_rollout_advantages
from isaac_threrisaifuture.normalization import ContinuousVecNormalize
from isaac_threrisaifuture.policy import policy_kwargs
from isaac_threrisaifuture.training import (
    PURE_CONFIG,
    TrainingConfigError,
    load_training_config,
    require_device,
    train,
)

# Contract hash of the full-batch structured run (runs/pure-v4-full-batch-structured).
FULL_BATCH_STRUCTURED_HASH = "ee4f65999d3a8cf0c85dabd5d887e360fd0823a164814bd20753d6dca91ac703"


def model(**kwargs: Any) -> PureRecurrentPPO:
    venv = ContinuousVecNormalize(DummyVecEnv([lambda: Monitor(synthetic_env())]), gamma=0.998)
    options: dict[str, Any] = {"n_steps": 64, "batch_size": 16, "n_epochs": 2, "seed": 3}
    return PureRecurrentPPO("MlpLstmPolicy", venv, policy_kwargs=policy_kwargs(16, 24),
                            device="cpu", **{**options, **kwargs})  # fmt: skip


# --- rollout-level advantage normalization -----------------------------------------------------


def test_advantages_are_normalized_once_over_the_rollout_and_never_per_minibatch(monkeypatch):
    raw: list[np.ndarray] = []
    seen: list[torch.Tensor] = []
    original_normalize = learner.normalize_rollout_advantages
    original_samples = RecurrentRolloutBuffer._get_samples

    def normalize(buffer: RecurrentRolloutBuffer) -> None:
        raw.append(buffer.advantages.copy())
        original_normalize(buffer)

    def samples(self: Any, batch_inds: np.ndarray, *args: Any, **kwargs: Any) -> Any:
        data = original_samples(self, batch_inds, *args, **kwargs)
        seen.append(data.advantages[data.mask > 1e-8])
        return data

    monkeypatch.setattr(learner, "normalize_rollout_advantages", normalize)
    monkeypatch.setattr(RecurrentRolloutBuffer, "_get_samples", samples)
    ppo = model()
    assert ppo.advantage_normalization == "rollout" and ppo.normalize_advantage is False
    ppo.learn(64)
    assert len(raw) == 1 and len(seen) == 8  # one normalization; 4 minibatches x 2 epochs
    expected = (raw[0] - raw[0].mean()) / (raw[0].std() + 1e-8)
    epoch = torch.cat(seen[:4]).numpy()
    assert epoch.size == 64
    assert np.allclose(np.sort(epoch), np.sort(expected.ravel()), atol=1e-5)
    assert abs(epoch.mean()) < 1e-5 and abs(epoch.std() - 1) < 1e-3
    # Minibatches keep their offsets: upstream would have centred each one on 0.
    assert max(abs(float(batch.mean())) for batch in seen[:4]) > 1e-2


def test_rollout_normalization_leaves_the_value_targets_alone():
    ppo = model()
    ppo.learn(64)
    buffer = ppo.rollout_buffer
    assert isinstance(buffer, RecurrentRolloutBuffer)
    returns = buffer.returns.copy()
    buffer.advantages = np.arange(64, dtype=np.float32).reshape(buffer.advantages.shape)
    normalize_rollout_advantages(buffer)
    assert buffer.advantages.dtype == np.float32 and abs(float(buffer.advantages.mean())) < 1e-5
    assert np.array_equal(buffer.returns, returns)


# --- target_kl over the mean of an epoch -------------------------------------------------------


def optimizer_steps(ppo: PureRecurrentPPO, monkeypatch: Any) -> list[int]:
    steps: list[int] = []
    original = ppo.policy.optimizer.step

    def step(*args: Any, **kwargs: Any) -> Any:
        steps.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(ppo.policy.optimizer, "step", step)
    return steps


@pytest.mark.parametrize("target_kl,epochs", [(None, 3), (1e3, 3), (1e-12, 1)])
def test_target_kl_stops_after_a_whole_epoch_on_its_mean_kl(monkeypatch, target_kl, epochs):
    ppo = model(n_epochs=3, target_kl=target_kl)
    steps = optimizer_steps(ppo, monkeypatch)
    ppo.learn(64)
    # A tiny limit ends the update after the first epoch, but all its 4 minibatches step;
    # upstream would stop inside the first epoch at the first minibatch over the limit.
    assert ppo._n_updates == epochs and len(steps) == 4 * epochs
    assert ppo.logger.name_to_value["train/n_updates"] == epochs


# --- persistence and the training path ---------------------------------------------------------


def test_saved_model_reloads_as_either_class_with_the_same_policy(tmp_path):
    ppo = model()
    ppo.learn(64)
    ppo.save(tmp_path / "model.zip")
    pure = PureRecurrentPPO.load(tmp_path / "model.zip", device="cpu")
    plain = RecurrentPPO.load(tmp_path / "model.zip", device="cpu")  # frozen evaluation
    assert pure.advantage_normalization == "rollout" and pure.normalize_advantage is False
    obs = np.zeros((1, *ppo.observation_space.shape), dtype=np.float32)
    start = np.ones((1,), dtype=bool)
    for other in (pure, plain):
        for name, tensor in ppo.policy.state_dict().items():
            assert torch.equal(other.policy.state_dict()[name], tensor)
        action, _ = other.predict(obs, episode_start=start, deterministic=True)
        assert np.array_equal(action, ppo.predict(obs, episode_start=start, deterministic=True)[0])


def test_training_and_resume_use_the_rollout_normalizing_learner(tmp_path, monkeypatch):
    calls: list[int] = []
    original = learner.normalize_rollout_advantages
    monkeypatch.setattr(
        learner, "normalize_rollout_advantages", lambda b: (calls.append(1), original(b))
    )
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml", hyperparameters={"batch_size": 16})
    run(path, out, 32)
    run(path, out, 64, resume=True)
    assert calls == [1, 1]  # one rollout per session, both through PureRecurrentPPO.train
    saved, manifest, _ = load_latest(out)
    assert saved.advantage_normalization == "rollout" and manifest.timesteps == 64


# --- device ----------------------------------------------------------------------------------


def test_cuda_without_a_gpu_is_refused_before_any_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    config, digest = load_training_config(
        write_config(tmp_path / "c.yaml", contract={"device": "cuda"})
    )
    built: list[int] = []

    def factory(seed: int) -> Any:
        built.append(seed)
        return synthetic_env()

    with pytest.raises(TrainingConfigError, match="device is cuda but CUDA is not available"):
        train(config, digest, seed=1, env_factory=factory, out_dir=tmp_path / "run",
              max_timesteps=32, reward_contract="pure-v11")  # fmt: skip
    assert not built and not (tmp_path / "run" / "checkpoints").exists()
    assert require_device("cpu") == "cpu"
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    assert require_device("cuda") == "cuda"  # never a silent fallback either way


def test_forever_refuses_a_cuda_contract_without_a_gpu_before_any_session(tmp_path, monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)
    config = write_config(tmp_path / "pure.yaml", contract={"device": "cuda"})
    root = tmp_path / "runs"
    options = runner.ForeverOptions(tmp_path / "game", tmp_path / "game.log", config, root,
                                    root / "supervisor", initialize=True)  # fmt: skip
    sessions: list[int] = []
    outcome = runner.run_forever(options, lambda plan: sessions.append(1) or {})
    assert outcome["stop_reason"].startswith("config refused: contract.device is cuda")
    assert not sessions


# --- contract ----------------------------------------------------------------------------------


def write(path: Path, **contract: Any) -> Path:
    raw = yaml.safe_load(yaml.safe_dump(RAW))
    raw["contract"].update(contract)
    for name in [key for key, value in contract.items() if value is None]:
        del raw["contract"][name]
    path.write_text(yaml.safe_dump(raw), "utf-8")
    return path


def test_the_contract_binds_the_device_and_the_advantage_normalization(tmp_path):
    config, digest = load_training_config(PURE_CONFIG)
    assert config.device == "cuda" and config.contract.advantage_normalization == "rollout"
    assert digest != FULL_BATCH_STRUCTURED_HASH
    old = {**RAW["contract"], "device": "cpu", "reward_version": 12}
    del old["advantage_normalization"], old["auxiliary"]  # auxiliary came after this change
    old.pop("intrinsic", None)  # and E3B after that
    assert config_hash(old) == FULL_BATCH_STRUCTURED_HASH  # the earlier lineage, refused now
    assert load_training_config(write(tmp_path / "cpu.yaml", device="cpu"))[1] != digest
    for change in (
        {"advantage_normalization": None},
        {"advantage_normalization": "minibatch"},
        {"device": "mps"},
        {"device": "auto"},
    ):
        with pytest.raises(TrainingConfigError):
            load_training_config(write(tmp_path / "x.yaml", **change))
