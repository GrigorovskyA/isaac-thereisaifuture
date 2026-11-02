"""Behaviour cloning from human demos (contract `pretraining: demo_bc_v1`, demo_learning.py)."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml
from stable_baselines3.common.logger import Logger
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from test_pure_training import RAW, run, synthetic_env, write_config

from isaac_threrisaifuture import checkpoints as cp
from isaac_threrisaifuture import demo_dataset, demo_learning
from isaac_threrisaifuture.demo_dataset import DemoSequence
from isaac_threrisaifuture.demo_learning import (
    DemoBatch,
    DemoLearner,
    action_distribution,
    holdout_split,
    linear_coef,
    normalize_on_device,
    zero_lstm_states,
)
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.learner import PureRecurrentPPO
from isaac_threrisaifuture.normalization import ContinuousVecNormalize
from isaac_threrisaifuture.policy import policy_kwargs
from isaac_threrisaifuture.training import (
    PURE_CONFIG,
    TrainingConfigError,
    contract_hash,
    load_training_config,
)

SIGNAL = 0  # player.position x: a continuous scalar feature


def sequence(length: int, rng: np.random.Generator, source: str = "demo") -> DemoSequence:
    """Move right (index 4 is not used) when the signal is positive, else left; shoot/use none."""
    observations = np.zeros((length, OBSERVATION_SIZE), dtype=np.float16)
    signs = rng.choice([-1.0, 1.0], size=length)
    observations[:, SIGNAL] = 0.5 * signs
    actions = np.zeros((length, 3), dtype=np.int64)
    actions[:, 0] = np.where(signs > 0, 1, 2)
    return DemoSequence(observations, actions, source)


def sequences(count: int, length: int, seed: int = 0) -> list[DemoSequence]:
    rng = np.random.default_rng(seed)
    return [sequence(length, rng, f"demo-{i}") for i in range(count)]


def small_model() -> PureRecurrentPPO:
    venv = ContinuousVecNormalize(DummyVecEnv([lambda: Monitor(synthetic_env())]), gamma=0.998)
    return PureRecurrentPPO(
        "MlpLstmPolicy",
        venv,
        n_steps=32,
        batch_size=32,
        n_epochs=1,
        policy_kwargs=policy_kwargs(16, 24),
        device="cpu",
        seed=0,
    )


# --- data layout ---------------------------------------------------------------------------------


def test_windows_pad_the_last_chunk_and_split_whole_sequences():
    learner = DemoLearner(sequences(4, 10), seq_len=4, holdout_fraction=0.25, seed=3)
    assert len(learner.train_indices) == 3 and len(learner.holdout_indices) == 1
    assert len(learner.train_windows) == 9 and len(learner.holdout_windows) == 3  # 0, 4, 8
    batch = DemoBatch(learner.sequences, learner.train_windows[[2, 0]], 4)
    assert batch.observations.shape == (8, OBSERVATION_SIZE)
    assert batch.mask.tolist() == [True, True, False, False, True, True, True, True]
    assert batch.episode_starts.tolist() == [1, 0, 0, 0, 1, 0, 0, 0]
    index = int(learner.train_windows[0][0])
    assert np.array_equal(batch.actions[4:], learner.sequences[index].actions[:4])
    assert holdout_split(10, 0.1, 5) == holdout_split(10, 0.1, 5)  # seeded
    assert holdout_split(1, 0.5, 0) == ([0], [])  # one sequence always stays for training
    assert len(holdout_split(2, 0.01, 0)[1]) == 1


def test_batch_layout_matches_stepping_the_lstm_one_step_at_a_time():
    model = small_model()
    policy: Any = model.policy
    learner = DemoLearner(sequences(2, 10), seq_len=4, holdout_fraction=0.0)
    batch = DemoBatch(learner.sequences, learner.train_windows[[0, 2, 4]], 4)
    obs = torch.as_tensor(model.get_vec_normalize_env().normalize_obs(batch.observations))
    obs = obs.float()
    starts = torch.as_tensor(batch.episode_starts)
    actions = torch.as_tensor(batch.actions)
    states = zero_lstm_states(policy, 3, torch.device("cpu"))
    with torch.no_grad():
        batched = action_distribution(policy, obs, states, starts).log_prob(actions)
        upstream = policy.evaluate_actions(obs, actions, states, starts)[1]
        stepped = []
        for window in range(3):
            pi = zero_lstm_states(policy, 1, torch.device("cpu")).pi
            for step in range(4):
                row = window * 4 + step
                latent, pi = policy._process_sequence(
                    policy.extract_features(obs[row : row + 1]), pi, starts[row : row + 1],
                    policy.lstm_actor,
                )  # fmt: skip
                latent = policy.mlp_extractor.forward_actor(latent)
                dist = policy._get_action_dist_from_latent(latent)
                stepped.append(dist.log_prob(actions[row : row + 1]))
    assert torch.allclose(batched, torch.cat(stepped), atol=1e-5)
    assert torch.allclose(batched, upstream, atol=1e-6)


def test_fit_normalizer_adds_every_demo_observation_in_chunks(monkeypatch):
    monkeypatch.setattr(demo_learning, "FIT_CHUNK", 7)
    demos = sequences(3, 20)
    venv = ContinuousVecNormalize(DummyVecEnv([synthetic_env]), gamma=0.998)
    count = float(venv.obs_rms.count)
    DemoLearner(demos).fit_normalizer(venv)
    assert float(venv.obs_rms.count) == pytest.approx(count + 60)
    raw = np.concatenate([d.observations for d in demos]).astype(np.float64)
    assert venv.obs_rms.mean[SIGNAL] == pytest.approx(raw[:, SIGNAL].mean(), abs=1e-3)
    assert venv.obs_rms.var[SIGNAL] == pytest.approx(raw[:, SIGNAL].var(), rel=1e-3)


def test_device_normalization_equals_the_normalizer():
    demos = sequences(2, 30)
    venv = ContinuousVecNormalize(DummyVecEnv([synthetic_env]), gamma=0.998)
    DemoLearner(demos).fit_normalizer(venv)
    raw = demos[0].observations
    expected = venv.normalize_obs(raw.astype(np.float32))
    got = normalize_on_device(venv, raw, torch.device("cpu")).numpy()
    assert got.dtype == np.float32
    np.testing.assert_allclose(got, expected, atol=1e-5)


# --- learning ------------------------------------------------------------------------------------


def test_behaviour_cloning_learns_the_demo_rule_on_the_holdout():
    model = small_model()
    learner = DemoLearner(sequences(10, 24), seq_len=8, batch_sequences=8, holdout_fraction=0.2)
    learner.fit_normalizer(model.get_vec_normalize_env())
    logged: list[dict[str, Any]] = []
    summary = learner.pretrain(
        model, steps=80, learning_rate=1e-2, max_grad_norm=0.5, log_every=30, log=logged.append
    )
    assert [row["step"] for row in logged] == [30, 60, 80]
    before, after = summary["holdout_before"], summary["holdout_after"]
    assert summary["steps"] == 80 and summary["holdout_sequences"] == 2
    assert summary["majority_accuracy"]["shoot"] == 1.0
    assert 0.3 < summary["majority_accuracy"]["move"] < 0.7
    assert after["accuracy"]["move"] > 0.95 > before["accuracy"]["move"]
    assert after["nll"] < before["nll"] and summary["train_nll"] < before["nll"]
    json.dumps(summary)  # pretraining.json takes it as is


def test_the_regulariser_weight_decays_linearly_to_zero():
    learner = DemoLearner(sequences(1, 4), bc_coef=2.0, bc_decay_timesteps=1000)
    assert [learner.coef_at(t) for t in (0, 250, 1000, 5000)] == [2.0, 1.5, 0.0, 0.0]
    assert linear_coef(1.0, 0, 0) == 0.0


def capture_logs(model: PureRecurrentPPO) -> dict[str, Any]:
    logger = Logger(None, [])
    records: dict[str, Any] = {}
    logger.record = lambda key, value, exclude=None: records.__setitem__(key, value)  # type: ignore[method-assign]
    model.set_logger(logger)
    return records


def test_the_demo_phase_logs_while_its_weight_is_positive_and_is_skipped_at_zero(monkeypatch):
    model = small_model()
    learner = DemoLearner(sequences(2, 16), seq_len=8, batch_sequences=2, bc_steps=3)
    model.demo_learner = learner
    records = capture_logs(model)
    model.learn(total_timesteps=32)
    assert records["train/demo_bc_coef"] == pytest.approx(1.0 - 32 / 1_000_000)
    assert np.isfinite(records["train/demo_bc_loss"]) and records["train/demo_approx_kl"] >= 0
    assert "demo_learner" in model._excluded_save_params()

    calls: list[int] = []
    monkeypatch.setattr(DemoLearner, "regularize", lambda *a, **k: calls.append(1) or 0.0)
    learner.bc_decay_timesteps = 32  # the weight is 0 from timestep 32 on
    records.clear()
    model.learn(total_timesteps=32, reset_num_timesteps=False)
    assert not calls and not any(key.startswith("train/demo_") for key in records)


# --- config --------------------------------------------------------------------------------------


DEMO = {
    "recordings": ["demos"],
    "seq_len": 8,
    "batch_sequences": 2,
    "pretrain_steps": 3,
    "bc_steps": 2,
    "min_steps": 40,
}


def demo_config(path: Path, *, demo: dict[str, Any] | None = None, **contract: Any) -> Path:
    raw = yaml.safe_load(write_config(path).read_text("utf-8"))
    raw["contract"].update({"pretraining": "demo_bc_v1", **contract})
    if demo is not None:
        raw["demo"] = demo
    path.write_text(yaml.safe_dump(raw), "utf-8")
    return path


def test_the_shipped_config_starts_the_demo_lineage():
    config, digest = load_training_config(PURE_CONFIG)
    assert config.contract.pretraining == "demo_bc_v1"
    assert config.demo is not None and config.demo.recordings == ["runs/demos"]
    assert (config.demo.seq_len, config.demo.batch_sequences, config.demo.min_steps) == (
        64, 16, 20000,
    )  # fmt: skip
    assert digest == contract_hash(RAW["contract"])


def test_demo_section_is_required_with_demo_bc_and_only_then(tmp_path):
    with pytest.raises(TrainingConfigError, match="demo section"):
        load_training_config(demo_config(tmp_path / "a.yaml"))
    plain = write_config(tmp_path / "b.yaml")
    raw = yaml.safe_load(plain.read_text("utf-8"))
    raw["demo"] = DEMO
    (tmp_path / "c.yaml").write_text(yaml.safe_dump(raw), "utf-8")
    with pytest.raises(TrainingConfigError, match="demo section"):
        load_training_config(tmp_path / "c.yaml")
    with pytest.raises(TrainingConfigError):
        load_training_config(demo_config(tmp_path / "d.yaml", demo={**DEMO, "recordings": []}))
    with pytest.raises(TrainingConfigError):
        load_training_config(demo_config(tmp_path / "e.yaml", demo={**DEMO, "extra": 1}))


def test_pretraining_none_keeps_the_hash_and_the_demo_section_is_not_hashed(tmp_path):
    plain = load_training_config(write_config(tmp_path / "a.yaml"))[1]
    none = write_config(tmp_path / "b.yaml", contract={"pretraining": "none"})
    explicit = load_training_config(none)[1]
    assert explicit == plain
    one = load_training_config(demo_config(tmp_path / "c.yaml", demo=DEMO))[1]
    other = demo_config(tmp_path / "d.yaml", demo={**DEMO, "bc_coef": 0.5, "seq_len": 16})
    assert load_training_config(other)[1] == one != plain


# --- training ------------------------------------------------------------------------------------


@pytest.fixture
def demos(tmp_path, monkeypatch):
    """Fake recordings: load_demos returns synthetic sequences; the calls are recorded."""
    root = tmp_path / "demos"
    root.mkdir()
    (root / "a.jsonl.gz").write_bytes(b"one")
    (root / "b.jsonl.gz").write_bytes(b"two")
    monkeypatch.chdir(tmp_path)
    calls: list[dict[str, Any]] = []

    def load(paths: Any, **options: Any) -> list[DemoSequence]:
        calls.append({"paths": list(paths), **options})
        return sequences(4, 12)

    monkeypatch.setattr(demo_dataset, "load_demos", load)
    monkeypatch.setattr(demo_dataset, "watchdog_limits", lambda version: (30.0, 15.0))
    return calls


def test_fresh_training_pretrains_checkpoints_t0_and_resumes_with_the_regulariser(
    tmp_path, demos, monkeypatch
):
    path = demo_config(tmp_path / "c.yaml", demo=DEMO)
    out = tmp_path / "run"
    pretrains: list[int] = []
    original = DemoLearner.pretrain
    monkeypatch.setattr(
        DemoLearner,
        "pretrain",
        lambda self, *a, **k: pretrains.append(1) or original(self, *a, **k),
    )
    run(path, out, 0)  # pretraining and the t0 checkpoint only, as if the first rollout crashed
    assert demos[0]["repeat"] == 6 and demos[0]["stall_seconds"] == 30.0
    assert demos[0]["calm_seconds"] == 15.0 and demos[0]["paths"] == [Path("demos")]
    record = json.loads((out / "pretraining.json").read_text("utf-8"))
    assert record["summary"]["steps"] == 3 and record["demo"]["seq_len"] == 8
    assert [row["path"] for row in record["recordings"]] == ["demos/a.jsonl.gz", "demos/b.jsonl.gz"]
    assert len(record["recordings"][0]["sha256"]) == 64
    first = cp.read_manifest(cp.latest_checkpoint_dir(out / "checkpoints"))
    assert first.timesteps == 0 and first.parent_checkpoint_id is None
    assert first.hyperparameters is not None and first.hyperparameters["demo"]["bc_steps"] == 2
    assert pretrains == [1]

    regularized: list[float] = []
    real = DemoLearner.regularize
    monkeypatch.setattr(
        DemoLearner,
        "regularize",
        lambda self, model, **k: regularized.append(k["learning_rate"]) or real(self, model, **k),
    )
    run(path, out, 32, resume=True)
    assert pretrains == [1]  # never again on resume
    assert regularized and regularized[0] == pytest.approx(3e-4 * (1 - 32 / 1_000_000))
    second = cp.read_manifest(cp.latest_checkpoint_dir(out / "checkpoints"))
    assert second.timesteps == 32 and second.parent_checkpoint_id == first.checkpoint_id


def test_too_few_demo_steps_are_refused_before_any_environment(tmp_path, demos, monkeypatch):
    path = demo_config(tmp_path / "c.yaml", demo={**DEMO, "min_steps": 1000})
    created: list[int] = []
    monkeypatch.setattr(
        "test_pure_training.synthetic_env", lambda *_: created.append(1) or synthetic_env()
    )
    with pytest.raises(TrainingConfigError, match="48 usable steps"):
        run(path, tmp_path / "run", 32)
    assert not created
    with pytest.raises(TrainingConfigError, match="not found"):
        run(
            demo_config(tmp_path / "d.yaml", demo={**DEMO, "recordings": ["nope"]}),
            tmp_path / "x",
            0,
        )


def test_a_resume_after_the_decay_needs_no_demos(tmp_path, demos):
    path = demo_config(tmp_path / "c.yaml", demo=DEMO)
    out = tmp_path / "run"
    run(path, out, 0)
    decayed = demo_config(tmp_path / "d.yaml", demo={**DEMO, "bc_decay_timesteps": 0})
    demos.clear()
    run(decayed, out, 32, resume=True)
    assert not demos


def test_pretraining_stops_early_and_keeps_the_best_holdout_weights(monkeypatch):
    model = small_model()
    learner = DemoLearner(sequences(10, 24), seq_len=8, batch_sequences=8, holdout_fraction=0.2)
    learner.fit_normalizer(model.get_vec_normalize_env())
    # Holdout NLL improves twice, then never again: stop after 2 stale checks, keep check 2.
    scores = iter([5.0, 4.0, 3.0, 3.5, 3.6, 3.7, 3.8])
    original = learner.evaluate
    states: list[dict[str, torch.Tensor]] = []

    def evaluate(target: Any) -> dict[str, Any]:
        result = dict(original(target) or {})
        result["nll"] = next(scores)
        states.append({k: v.clone() for k, v in target.policy.state_dict().items()})
        return result

    monkeypatch.setattr(learner, "evaluate", evaluate)
    summary = learner.pretrain(
        model, steps=100, learning_rate=1e-2, max_grad_norm=0.5, log_every=10, patience=2
    )
    assert summary["steps"] == 40 and summary["best_step"] == 20
    best = states[2]  # before, then the checks at 10 and 20 steps
    for name, value in model.policy.state_dict().items():
        assert torch.equal(value, best[name]), name
