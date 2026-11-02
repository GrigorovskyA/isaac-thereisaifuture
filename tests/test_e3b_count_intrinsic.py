"""OFFLINE tests for the E3B x count intrinsic bonus (contract `intrinsic: e3b_count_v1`): the
Sherman-Morrison bonus, its decay and episode reset, the masked embedding, the multiplicative count
factor and its floor, the `e3b` ledger column, the checkpoint round trip, evaluation without pay,
the unchanged shipped contract hash and the inverse-dynamics loss. Synthetic runs prove plumbing
only, never Isaac play."""

import csv
import dataclasses
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
from synthetic import frame
from test_pure_training import RAW, TOY, synthetic_env, write_config
from test_reward_v4 import LIVE_SCENARIO

from isaac_threrisaifuture import e3b
from isaac_threrisaifuture.auxiliary import Replay, RolloutRecord
from isaac_threrisaifuture.checkpoint_policy import CheckpointPolicy
from isaac_threrisaifuture.checkpoints import (
    E3B_FILE,
    MANIFEST_NAME,
    CheckpointError,
    latest_checkpoint_dir,
    read_manifest,
)
from isaac_threrisaifuture.e3b import (
    E3BLearner,
    EllipticalBonus,
    RunningStd,
    count_factor,
    keep_mask,
)
from isaac_threrisaifuture.encoding import FEATURE_BLOCKS, OBSERVATION_SIZE, continuous_mask
from isaac_threrisaifuture.entities import Vec
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import FIELDS, EpisodeMetricsEnv, EpisodeMetricsWriter
from isaac_threrisaifuture.episodes import ACTION_NVEC, StepResult
from isaac_threrisaifuture.learner import PureRecurrentPPO
from isaac_threrisaifuture.normalization import ContinuousVecNormalize
from isaac_threrisaifuture.novelty_counts import NoveltyCounts
from isaac_threrisaifuture.policy import policy_kwargs
from isaac_threrisaifuture.rewards import DEFAULT_CONFIG_V12, RewardLedgerV4, RewardV4Coefficients
from isaac_threrisaifuture.sim import SyntheticRoomBackend
from isaac_threrisaifuture.training import (
    PURE_CONFIG,
    TrainingConfigError,
    contract_hash,
    load_training_config,
    train,
)
from isaac_threrisaifuture.training_metrics import E3B, TRAIN_FIELDS

# The behaviour-cloning lineage (pretraining demo_bc_v1).
SHIPPED_HASH = "c8a7486b9806f2cd76e3aab5324163659dfb4b3ae41a619ed61a362be8936121"
# The reward v13 lineage before behaviour cloning.
V13_HASH = "54be12af1dcec7f0ade2dc109cbcb2f90b71d6e58cb7d51d17b3b704fa4859cc"
# The E3B lineage with reward v12 (runs/pure-v4-e3b).
E3B_HASH = "db85924fdb4f26190d287bf67336aabaa77aca941602016fcebfc5054a64cf21"
WITHOUT_E3B_HASH = "0399c37db311f00df37cea79a66385ff6cd7150dfcfa0c9e3e46415f577da79a"
V12 = RewardV4Coefficients.load(DEFAULT_CONFIG_V12)
GAMMA = 0.998
NVEC = list(ACTION_NVEC)
STEP = np.array([0, 0, 0])
ON = {"intrinsic": "e3b_count_v1"}
SHORT = {"e3b_idm_steps": 2, "e3b_idm_batch": 16, "e3b_embed_dim": 8}


def block(name: str) -> slice:
    found = next(b for b in FEATURE_BLOCKS if b.name == name)
    return slice(found.offset, found.offset + found.size)


def learner(*, beta: float = 0.05, ridge: float = 0.1, floor: float = 0.1, dim: int = 16):
    torch.manual_seed(0)
    return E3BLearner(NVEC, embed_dim=dim, ridge=ridge, beta=beta, floor=floor,
                      replay=Replay(2), device="cpu")  # fmt: skip


def observation(seed: int) -> np.ndarray:
    obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    obs[block("player.position")] = np.random.default_rng(seed).uniform(-1, 1, 2)
    return obs


def ledger(counts: NoveltyCounts) -> RewardLedgerV4:
    return RewardLedgerV4(V12, stall_seconds=30, gamma=GAMMA, novelty_counts=counts)


class Walk:
    """Scripted backend: the player stands at the given x per step, in room 1 of one run."""

    supports_seed = False

    def __init__(self, xs: list[float]) -> None:
        self.xs = list(xs)
        self.count = 0

    def _result(self, x: float) -> StepResult:
        self.count += 1
        return StepResult(frame(frame_id=self.count, player_position=Vec(x=x, y=200.0)), (),
                          room_index=1)  # fmt: skip

    def start_episode(self, scenario, seed):
        return self._result(100.0)

    def step(self, action, repeat):
        return self._result(self.xs.pop(0) if self.xs else 100.0)

    def release(self):
        pass

    def close(self):
        pass


class RoomBackend(SyntheticRoomBackend):
    """Synthetic room with an oracle room index, so the ledger has novelty keys."""

    def start_episode(self, scenario, seed):
        return dataclasses.replace(super().start_episode(scenario, seed), room_index=1)

    def step(self, action, repeat):
        return dataclasses.replace(super().step(action, repeat), room_index=1)


COUNTS: dict[int, NoveltyCounts] = {}


def counted_env(_: int = 0) -> IsaacCombatEnv:
    """Synthetic env whose v12 ledger fills the table `run(..., novelty_counts=...)` passes."""
    return IsaacCombatEnv(RoomBackend(), [TOY], accountant=ledger(COUNTS[0]))


def run(path: Path, out: Path, steps: int, **kwargs: Any) -> Any:
    config, digest = load_training_config(path)
    options: dict[str, Any] = {"env_factory": synthetic_env, **kwargs}
    return train(config, digest, seed=1, out_dir=out, max_timesteps=steps,
                 reward_contract="pure-v11", **options)  # fmt: skip


def train_e3b(path: Path, out: Path, steps: int, **kwargs: Any) -> Any:
    """Train on `counted_env`; a fresh table with `counts`, else the previous session's."""
    COUNTS[0] = kwargs.pop("counts", None) or COUNTS.get(0) or NoveltyCounts()
    return run(path, out, steps, novelty_counts=COUNTS[0], env_factory=counted_env, **kwargs)


# --- the elliptical bonus ----------------------------------------------------------------------


def test_sherman_morrison_matches_the_direct_inverse():
    rng = np.random.default_rng(1)
    bonus = EllipticalBonus(6, ridge=0.1)
    covariance = 0.1 * np.eye(6)
    for _ in range(40):
        phi = rng.normal(size=6)
        expected = float(phi @ np.linalg.inv(covariance) @ phi)
        assert bonus.observe(phi) == pytest.approx(expected, rel=1e-9)
        covariance += np.outer(phi, phi)
        np.testing.assert_allclose(bonus.inverse, np.linalg.inv(covariance), rtol=1e-7, atol=1e-9)


def test_the_bonus_decays_for_a_repeated_state_and_resets_on_a_new_episode():
    agent = learner()
    obs = observation(0)
    agent.start_episode(obs)
    raws = [agent.bonus.observe(agent.embed(obs)) for _ in range(5)]
    assert all(later < earlier for earlier, later in zip(raws, raws[1:], strict=False))
    agent.start_episode(obs)
    assert agent.bonus.observe(agent.embed(obs)) == pytest.approx(raws[0], rel=1e-12)


def test_the_env_pays_less_for_repeats_and_a_new_episode_starts_over():
    counts = NoveltyCounts()
    env = IsaacCombatEnv(Walk([100.0] * 6), [LIVE_SCENARIO], accountant=ledger(counts))
    env.intrinsic = agent = learner(beta=1.0)
    agent.std.load({"count": 1e6, "mean": 0.0, "m2": 1e6})  # std 1: raw bonuses are paid
    env.reset()
    paid = [env.step(STEP)[4]["reward_components"]["e3b"] for _ in range(3)]
    assert paid[0] > paid[1] > paid[2] > 0
    env.reset()
    assert env.step(STEP)[4]["reward_components"]["e3b"] > paid[2]


# --- embedding input -------------------------------------------------------------------------


def test_the_stall_clock_and_the_visited_grid_never_reach_phi():
    mask = keep_mask()
    assert mask[block("stall")].sum() == 0 and mask[block("visited_cells")].sum() == 0
    visited = block("visited_cells")
    assert mask.sum() == OBSERVATION_SIZE - 1 - (visited.stop - visited.start)
    agent = learner()
    obs = observation(3)
    changed = obs.copy()
    changed[block("stall")] = 0.9
    changed[block("visited_cells")] = 1.0
    np.testing.assert_array_equal(agent.embed(obs), agent.embed(changed))
    moved = obs.copy()
    moved[block("player.position")] += 0.5
    assert not np.allclose(agent.embed(obs), agent.embed(moved))


def test_the_embedding_has_its_own_weights():
    model = pure_model(auxiliary="spr_reward_done_v1")
    assert model.e3b_learner is not None
    policy_params = {id(p) for p in model.policy.parameters()}
    assert not policy_params & {id(p) for p in model.e3b_learner.embedding.parameters()}
    assert model.e3b_learner.replay is model.auxiliary_learner.replay  # one shared replay


# --- multiplicative count combination --------------------------------------------------------


def test_the_count_factor_is_one_over_sqrt_n_with_a_floor():
    assert count_factor(1, 0.1) == 1.0 and count_factor(4, 0.1) == 0.5
    assert count_factor(400, 0.1) == 0.1 and count_factor(None, 0.1) == 0.1
    assert count_factor(0, 0.1) == 1.0  # a full table never counted it: treated as new


def paid(count: int | None, *, ridge: float, beta: float = 1.0) -> tuple[float, float]:
    """Paid r_int of one step and the raw bonus it was made from (std 1 on the first value)."""
    agent = learner(ridge=ridge, beta=beta)
    agent.start_episode(observation(0))
    inverse = agent.bonus.inverse.copy()
    phi = agent.embed(observation(1))
    return agent.reward(observation(1), count), float(phi @ inverse @ phi)


def test_the_bonus_multiplies_the_episodic_term_by_the_count_factor_and_clips():
    ridge = 1e6  # raw bonuses far below the clip
    base, raw = paid(1, ridge=ridge)
    assert base == pytest.approx(raw) and 0 < raw < 1e-3
    assert paid(4, ridge=ridge)[0] == pytest.approx(0.5 * base)
    assert paid(400, ridge=ridge)[0] == pytest.approx(0.1 * base)  # the floor
    assert paid(None, ridge=ridge)[0] == pytest.approx(0.1 * base)
    clipped, raw = paid(1, ridge=1e-8, beta=0.05)
    assert raw > 1 and clipped == pytest.approx(0.05)  # clip to [0, 1] before beta


def test_running_std_is_the_sample_std_and_round_trips():
    std = RunningStd()
    values = [3.0, 1.0, 4.0, 1.0, 5.0]
    for value in values:
        std.update(value)
    assert std.std == pytest.approx(np.std(values, ddof=1))
    copy = RunningStd()
    copy.load(std.state())
    assert copy.std == std.std


# --- ledger column ---------------------------------------------------------------------------


def test_the_e3b_column_sums_per_episode_and_the_columns_sum_to_the_return(tmp_path):
    counts = NoveltyCounts()
    walk = Walk([100.0, 140.0, 180.0, 180.0])
    env = IsaacCombatEnv(walk, [LIVE_SCENARIO], accountant=ledger(counts))
    env.intrinsic = learner()
    writer = EpisodeMetricsWriter(tmp_path / "episodes.csv")
    wrapped = EpisodeMetricsEnv(env, writer)
    wrapped.reset()
    rewards, bonuses = [], []
    for _ in range(4):
        _, reward, _, _, info = wrapped.step(STEP)
        parts = info["reward_components"]
        assert sum(parts.values()) == pytest.approx(reward)
        rewards.append(reward)
        bonuses.append(parts["e3b"])
    assert all(0.0 <= value <= 0.05 for value in bonuses) and sum(bonuses) > 0
    env.request_truncation("stall")
    _, reward, _, _, info = wrapped.step(STEP)
    rewards.append(reward)
    bonuses.append(info["reward_components"]["e3b"])
    summary = info["episode_summary"]
    assert summary["columns"]["e3b"] == pytest.approx(sum(bonuses))
    assert sum(summary["columns"].values()) == pytest.approx(summary["return"])
    assert summary["return"] == pytest.approx(sum(rewards))
    assert "col_e3b" in FIELDS
    row = next(csv.DictReader((tmp_path / "episodes.csv").open(encoding="utf-8")))
    assert float(row["col_e3b"]) == pytest.approx(sum(bonuses))


def test_the_bonus_reads_the_count_of_the_next_cell_and_never_counts():
    counts = NoveltyCounts()
    stage = frame().room.stage
    for _ in range(3):  # three earlier runs first visited the cell at x = 140
        counts.visit((stage, 1, 2, 1))
    env = IsaacCombatEnv(Walk([140.0]), [LIVE_SCENARIO], accountant=ledger(counts))
    seen: list[int | None] = []

    class Spy:
        def start_episode(self, observation):
            pass

        def reward(self, observation, count):
            seen.append(count)
            return 0.0

    env.intrinsic = Spy()
    env.reset()
    env.step(STEP)
    assert env.accountant.novelty_key() == (stage, 1, 2, 1)
    assert seen == [4]  # this run's first visit included, by the ledger alone
    assert counts.get((stage, 1, 2, 1)) == 4 and len(counts) == 1


def test_without_the_bonus_the_column_stays_empty(tmp_path):
    env = IsaacCombatEnv(Walk([100.0]), [LIVE_SCENARIO], accountant=ledger(NoveltyCounts()))
    assert env.intrinsic is None
    writer = EpisodeMetricsWriter(tmp_path / "episodes.csv")
    wrapped = EpisodeMetricsEnv(env, writer)
    wrapped.reset()
    env.request_truncation("stall")
    _, _, _, _, info = wrapped.step(STEP)
    assert "e3b" not in info["reward_components"]
    assert "e3b" not in info["episode_summary"]["columns"]
    row = next(csv.DictReader((tmp_path / "episodes.csv").open(encoding="utf-8")))
    assert row["col_e3b"] == ""


# --- evaluation ------------------------------------------------------------------------------


def test_frozen_evaluation_never_pays_the_bonus_even_when_set():
    env = IsaacCombatEnv(Walk([140.0, 180.0]), [LIVE_SCENARIO],
                         accountant=ledger(NoveltyCounts(frozen=True)))  # fmt: skip
    calls: list[str] = []

    class Spy:
        def start_episode(self, observation):
            calls.append("start")

        def reward(self, observation, count):
            calls.append("reward")
            return 1.0

    env.intrinsic = Spy()
    env.reset()
    for _ in range(2):
        _, reward, _, _, info = env.step(STEP)
        assert "e3b" not in info["reward_components"]
        assert reward == pytest.approx(sum(info["reward_components"].values()))
    assert calls == []


def test_frozen_evaluation_loads_the_policy_and_ignores_the_e3b_state(tmp_path):
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml", contract=ON, hyperparameters=SHORT)
    train_e3b(path, out, 32, counts=NoveltyCounts())
    directory = latest_checkpoint_dir(out / "checkpoints")
    policy = CheckpointPolicy(directory, expected_config_hash=load_training_config(path)[1],
                              observation_normalization="continuous_only")  # fmt: skip
    policy.reset(0)
    action = policy.act(np.zeros(OBSERVATION_SIZE, dtype=np.float32))
    assert action.shape == (3,) and (action < np.array(ACTION_NVEC)).all()
    (directory / E3B_FILE).unlink()  # never read by inference
    policy.verify_unchanged()


# --- learner, checkpoints and contract -------------------------------------------------------


def pure_model(**kwargs: Any) -> PureRecurrentPPO:
    venv = ContinuousVecNormalize(DummyVecEnv([lambda: Monitor(synthetic_env())]), gamma=0.998)
    options: dict[str, Any] = {
        "n_steps": 32, "batch_size": 32, "n_epochs": 1, "seed": 3, "intrinsic": "e3b_count_v1",
        "e3b_embed_dim": 8, "e3b_idm_steps": 3, "e3b_idm_batch": 16, "aux_steps": 1,
        "aux_batch": 8,
    }  # fmt: skip
    return PureRecurrentPPO("MlpLstmPolicy", venv, policy_kwargs=policy_kwargs(16, 24),
                            device="cpu", **{**options, **kwargs})  # fmt: skip


def test_the_learner_keeps_its_own_replay_and_logs_the_idm_loss():
    model = pure_model()
    assert model.auxiliary_learner is None and model.e3b_learner is not None
    model.learn(total_timesteps=32)
    assert len(model.e3b_learner.replay) == 32
    logged = model.logger.name_to_value
    assert np.isfinite(logged["train/e3b_idm_loss"]) and logged["train/e3b_seconds"] >= 0
    assert "train/e3b_bonus_mean" not in logged  # the synthetic env never paid a bonus
    assert "e3b_learner" in model._excluded_save_params()


def test_checkpoints_save_and_resume_restores_the_e3b_state(tmp_path, monkeypatch):
    loads: list[Path] = []
    original = E3BLearner.load

    def load(self: E3BLearner, path: Path) -> None:
        original(self, path)
        saved = torch.load(path, weights_only=True)
        for name, module in (("embedding", self.embedding), ("idm", self.idm)):
            state = module.state_dict()
            assert saved[name].keys() == state.keys()
            assert all(torch.equal(saved[name][key], state[key]) for key in state)
        assert self.std.state() == saved["std"] and saved["std"]["count"] > 0
        loads.append(path)

    monkeypatch.setattr(E3BLearner, "load", load)
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml", contract=ON, hyperparameters=SHORT)
    metrics = tmp_path / "train.csv"
    train_e3b(path, out, 32, counts=NoveltyCounts(), train_metrics_path=metrics)
    directory = latest_checkpoint_dir(out / "checkpoints")
    manifest = read_manifest(directory)
    assert manifest.e3b_file == E3B_FILE and manifest.e3b_sha256
    assert manifest.hyperparameters is not None and manifest.hyperparameters["e3b_beta"] == 0.05
    state = torch.load(directory / E3B_FILE, weights_only=True)
    assert set(state) == {"format", "embedding", "idm", "optimizer", "std"}
    assert state["optimizer"]["state"]
    train_e3b(path, out, 64, resume=True, train_metrics_path=metrics)
    assert loads == [directory / E3B_FILE]
    rows = list(csv.DictReader(metrics.open(encoding="utf-8")))
    assert len(rows) == 2 and all(name in rows[0] for name in E3B)
    for row in rows:
        assert float(row["e3b_idm_loss"]) > 0 and 0 < float(row["e3b_bonus_mean"]) <= 0.05


def test_resume_without_e3b_state_is_refused(tmp_path):
    out = tmp_path / "run"
    path = write_config(tmp_path / "c.yaml", contract=ON, hyperparameters=SHORT)
    train_e3b(path, out, 32, counts=NoveltyCounts())
    manifest_path = latest_checkpoint_dir(out / "checkpoints") / MANIFEST_NAME
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest.update(e3b_file=None, e3b_sha256=None)
    manifest_path.write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(CheckpointError, match="no E3B state"):
        train_e3b(path, out, 64, resume=True)


def test_the_bonus_needs_the_saved_counts_and_a_novelty_ledger(tmp_path):
    path = write_config(tmp_path / "c.yaml", contract=ON, hyperparameters=SHORT)
    with pytest.raises(TrainingConfigError, match="novelty counts"):
        run(path, tmp_path / "a", 32)
    with pytest.raises(TrainingConfigError, match="novelty ledger"):
        run(path, tmp_path / "b", 32, novelty_counts=NoveltyCounts())  # env without a ledger
    COUNTS[0] = NoveltyCounts()
    with pytest.raises(TrainingConfigError, match="counts the checkpoints save"):
        run(path, tmp_path / "c", 32, novelty_counts=NoveltyCounts(), env_factory=counted_env)


def test_intrinsic_none_keeps_the_earlier_contract_hash_and_manifests(tmp_path):
    config, digest = load_training_config(PURE_CONFIG)
    assert digest == SHIPPED_HASH and config.contract.intrinsic == "e3b_count_v1"
    v13 = {name: value for name, value in RAW["contract"].items() if name != "pretraining"}
    assert contract_hash(v13) == V13_HASH  # the reward v13 lineage before behaviour cloning
    v12 = {**v13, "reward_version": 12}
    assert contract_hash(v12) == E3B_HASH  # the E3B lineage before reward v13, refused now
    without = {name: value for name, value in v12.items() if name != "intrinsic"}
    assert contract_hash(without) == WITHOUT_E3B_HASH  # the auxiliary lineage, refused now
    assert contract_hash({**without, "intrinsic": "none"}) == WITHOUT_E3B_HASH
    explicit = write_config(tmp_path / "none.yaml", contract={"intrinsic": "none"})
    implicit = write_config(tmp_path / "absent.yaml")
    assert load_training_config(explicit)[1] == load_training_config(implicit)[1]
    with pytest.raises(TrainingConfigError):
        load_training_config(write_config(tmp_path / "x.yaml", contract={"intrinsic": "e3b"}))
    out = tmp_path / "run"
    run(implicit, out, 32)
    manifest = read_manifest(latest_checkpoint_dir(out / "checkpoints"))
    assert manifest.e3b_file is None
    assert manifest.hyperparameters is not None
    assert not any(name.startswith("e3b_") for name in manifest.hyperparameters)
    # A checkpoint of the `none` contract is refused by an E3B contract.
    COUNTS[0] = NoveltyCounts()
    with pytest.raises(CheckpointError, match="different training configuration"):
        on = write_config(tmp_path / "on.yaml", contract=ON, hyperparameters=SHORT)
        train_e3b(on, out, 64, resume=True)


def test_train_csv_has_the_e3b_columns_empty_when_off(tmp_path):
    assert set(E3B) <= set(TRAIN_FIELDS)
    path = write_config(tmp_path / "c.yaml")
    metrics = tmp_path / "train.csv"
    run(path, tmp_path / "run", 32, train_metrics_path=metrics)
    row = next(csv.DictReader(metrics.open(encoding="utf-8")))
    assert all(row[name] == "" for name in E3B)


# --- inverse dynamics ------------------------------------------------------------------------


def test_the_inverse_dynamics_loss_falls_on_a_tiny_task():
    """The action moves the player (move), its velocity (shoot) and a heart value (use)."""
    rng = np.random.default_rng(0)
    steps = 256
    directions = np.array([[0, 0], [0, -1], [0, 1], [-1, 0], [1, 0]], dtype=np.float32)
    actions = np.stack([rng.integers(0, n, steps + 1) for n in NVEC], axis=1)
    obs = np.zeros((steps + 1, OBSERVATION_SIZE), dtype=np.float32)
    position, velocity = block("player.position"), block("player.velocity")
    hearts = block("player.hearts")
    obs[:, position] = rng.uniform(-0.5, 0.5, (steps + 1, 2))
    for t in range(steps):
        move, shoot, use = actions[t]
        obs[t + 1, position] = obs[t, position] + 0.3 * directions[move]
        obs[t + 1, velocity] = 0.8 * directions[shoot]
        obs[t + 1, hearts.start] = use / 4.0
    mask = continuous_mask()
    replay = Replay(1, mask)
    replay.add(RolloutRecord(
        continuous=obs[:, mask], discrete=obs[:, ~mask].astype(np.float16),
        actions=actions[:steps].astype(np.int64), rewards=np.zeros(steps, dtype=np.float32),
        dones=np.zeros(steps, dtype=bool), terminated=np.zeros(steps, dtype=bool),
    ))  # fmt: skip
    agent = learner(dim=32)
    agent.replay = replay
    np.random.seed(0)
    first = agent.update(steps=1, batch=128, learning_rate=1e-3, max_grad_norm=0.5)
    agent.update(steps=150, batch=128, learning_rate=1e-3, max_grad_norm=0.5)
    last = agent.update(steps=5, batch=128, learning_rate=1e-3, max_grad_norm=0.5)
    assert first > 4.0  # about log 5 + log 5 + log 4 = 4.6 at the start
    assert last < 0.5 * first


def test_idm_pairs_across_an_episode_end_do_not_count():
    agent = learner()
    obs = np.stack([observation(0), observation(1)])
    actions = np.zeros((2, 3), dtype=np.int64)
    valid = np.array([True, False])
    both = agent.idm_loss(obs, obs[::-1].copy(), actions, valid)
    one = agent.idm_loss(obs[:1], obs[1:], actions[:1], valid[:1])
    assert float(both) == pytest.approx(float(one), rel=1e-5)


def test_unknown_intrinsic_and_two_envs_are_refused():
    with pytest.raises(ValueError, match="intrinsic"):
        pure_model(intrinsic="rnd")
    venv = ContinuousVecNormalize(DummyVecEnv([synthetic_env, synthetic_env]), gamma=0.998)
    with pytest.raises(ValueError, match="n_envs must be 1"):
        PureRecurrentPPO("MlpLstmPolicy", venv, n_steps=8, batch_size=8, intrinsic="e3b_count_v1",
                         policy_kwargs=policy_kwargs(16, 24), device="cpu")  # fmt: skip
    assert e3b.INTRINSICS == ("none", "e3b_count_v1")
