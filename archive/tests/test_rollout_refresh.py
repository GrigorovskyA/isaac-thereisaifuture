"""Actual SB3 accounting and simulated native gaps; no installed-game evidence."""

import json
from copy import deepcopy
from types import SimpleNamespace

import gymnasium as gym
import numpy as np
import pytest
from test_checkpoint_policy import RAW_CONFIG
from test_combat_gate import Operator, World, gate_events

from isaac_threrisaifuture import checkpoints as cp
from isaac_threrisaifuture.combat_gate import CombatGateEnv, GateConfig, GateError
from isaac_threrisaifuture.live import LiveBudgetExpired, make_live_env
from isaac_threrisaifuture.training import TrainingConfig, train


def gated(tmp_path):
    world = World(operator=Operator(tmp_path, navigate=False))
    world.enemies = {1: 10.0}
    records = []
    env = CombatGateEnv(
        make_live_env(world),
        GateConfig(
            tmp_path / "combat_gate", combat_trace_bytes=1024**2, combat_progress_updates=900
        ),
        record=lambda *row: records.append(row),
    )
    return world, env, records


def test_live_gap_rebases_hp_and_trace_without_a_transition(tmp_path):
    world, env, records = gated(tmp_path)
    try:
        env.reset()
        env.step([1, 0])
        steps = env.stats.combat_steps
        outcomes = dict(env.stats.outcomes)
        progress = env._combat_progress.updates_without_progress
        before = env.end_collection_segment()
        assert world.commands[-1][0] == "release"
        with pytest.raises(RuntimeError, match="call reset"):
            env.step([1, 0])
        world.frame += 21
        world.enemies = {1: 3.0}  # idle damage must not be rewarded
        env.reset()
        assert env.stats.combat_steps == steps
        assert dict(env.stats.outcomes) == outcomes
        assert env._combat_progress.updates_without_progress == progress
        fresh = env.backend.latest.frame_id
        assert fresh > before["frame_id"] + 21
        _, _, _, _, info = env.step([1, 0])
        assert info["reward_components"]["enemy_damage"] == 0
        gap = gate_events(records, "collection_refreshed")[0]
        assert gap["previous"]["frame_id"] == before["frame_id"]
        assert gap["frame_id"] == fresh
        trace = tmp_path / "combat_gate/diagnostics/policy.jsonl"
        rows = [json.loads(x) for x in trace.read_text().splitlines()]
        assert len(rows) == 2 and rows[1]["before"]["frame_id"] == fresh
        assert rows[0]["after"]["frame_id"] < fresh
    finally:
        env.close()


def test_release_rejection_or_deadline_prevents_another_action(tmp_path, monkeypatch):
    world, env, _ = gated(tmp_path)
    try:
        env.reset()
        monkeypatch.setattr(world, "command", lambda *a, **k: SimpleNamespace(status="rejected"))
        with pytest.raises(GateError, match="rejected"):
            env.end_collection_segment()
        with pytest.raises(RuntimeError, match="call reset"):
            env.step([1, 0])
        env.run_deadline = 0.0001
        with pytest.raises(LiveBudgetExpired):
            env.reset()
        assert world.action_count() == 0
    finally:
        env.close()


class MovingClockWorld(gym.Env):
    observation_space = gym.spaces.Box(-1.0, 1.0, (649,), np.float32)
    action_space = gym.spaces.MultiDiscrete([5, 5])

    def __init__(self):
        self.frame = self.resets = self.steps = self.ends = 0
        self.suspended = False
        self.reset_vectors = []

    def vector(self):
        obs = np.zeros(649, np.float32)
        obs[0] = self.frame / 1000
        return obs

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.frame += 1
        self.resets += 1
        self.suspended = False
        obs = self.vector()
        self.reset_vectors.append(obs.copy())
        return obs, {}

    def step(self, action):
        assert not self.suspended, "Action used before fresh reset"
        self.frame += 3
        self.steps += 1
        return self.vector(), 0.0, False, False, {}

    def end_collection_segment(self):
        self.suspended = True
        self.ends += 1
        return {"frame_id": self.frame}

    def close(self):
        self.closed = True


def test_contract_log_failure_closes_environment_without_an_action(tmp_path):
    world = MovingClockWorld()

    def failed_record(event, data):
        raise OSError("Journal unavailable")

    with pytest.raises(OSError, match="Journal unavailable"):
        train(
            TrainingConfig.model_validate(RAW_CONFIG),
            cp.config_hash(RAW_CONFIG),
            seed=7,
            env_factory=lambda _: world,
            out_dir=tmp_path,
            refresh_between_rollouts=True,
            on_progress=failed_record,
        )
    assert world.closed and world.steps == world.resets == 0


@pytest.mark.parametrize("algorithm", ["PPO", "RecurrentPPO"])
@pytest.mark.parametrize("refresh", [False, True])
def test_real_sb3_actor_buffer_rms_and_recurrent_boundary(
    tmp_path, monkeypatch, algorithm, refresh
):
    import torch
    from sb3_contrib import RecurrentPPO
    from sb3_contrib.common.recurrent.policies import RecurrentActorCriticPolicy
    from stable_baselines3 import PPO
    from stable_baselines3.common.policies import ActorCriticPolicy

    cls = RecurrentPPO if algorithm == "RecurrentPPO" else PPO
    policy_cls = RecurrentActorCriticPolicy if algorithm == "RecurrentPPO" else ActorCriticPolicy
    world = MovingClockWorld()
    calls, rollouts, events, models = [], [], [], []
    forward = policy_cls.forward

    def observed_forward(self, obs, *args, **kwargs):
        calls.append(obs.detach().cpu().numpy().copy())
        if len(calls) == 33 and refresh:
            normalizer = models[0].get_vec_normalize_env()
            raw_obs = normalizer.get_original_obs()
            assert raw_obs[0, 0] == pytest.approx(0.119)
            np.testing.assert_array_equal(
                obs.detach().cpu().numpy(), normalizer.normalize_obs(raw_obs)
            )
            np.testing.assert_array_equal(models[0]._last_original_obs, raw_obs)
        if algorithm == "RecurrentPPO" and len(calls) == 33 and refresh:
            states, starts = args
            assert starts.tolist() == [1.0]
            zeros = type(states)(*(tuple(torch.zeros_like(x) for x in pair) for pair in states))
            actual = forward(self, obs, states, starts, deterministic=True)
            reset = forward(self, obs, zeros, starts, deterministic=True)
            for a, b in zip(actual[:3], reset[:3], strict=True):
                torch.testing.assert_close(a, b)
        return forward(self, obs, *args, **kwargs)

    monkeypatch.setattr(policy_cls, "forward", observed_forward)
    optimize = cls.train

    def observed_train(self):
        models.append(self)
        if refresh:
            assert world.suspended  # input released before optimization
        rollouts.append(
            {
                "obs": self.rollout_buffer.observations.copy(),
                "starts": self.rollout_buffer.episode_starts.copy(),
                "raw": self.get_vec_normalize_env().get_original_obs().copy(),
                "count": self.get_vec_normalize_env().obs_rms.count,
            }
        )
        optimize(self)
        world.frame += 21  # game advances during optimization/checkpoint gap

    monkeypatch.setattr(cls, "train", observed_train)
    raw = deepcopy(RAW_CONFIG)
    raw["algorithm"] = algorithm
    raw["budget"]["total_timesteps"] = 64
    result = train(
        TrainingConfig.model_validate(raw),
        cp.config_hash(raw),
        seed=7,
        env_factory=lambda _: world,
        out_dir=tmp_path,
        refresh_between_rollouts=refresh,
        on_progress=lambda *row: events.append(row),
    )
    assert result.timesteps == world.steps == 64 and len(calls) == 64
    assert world.resets == (2 if refresh else 1)
    assert world.ends == (2 if refresh else 0)
    assert rollouts[1]["count"] == pytest.approx(64 + world.resets + 0.0001)
    for index, data in enumerate(rollouts):
        np.testing.assert_array_equal(
            data["obs"][:, 0], np.concatenate(calls[index * 32 : (index + 1) * 32])
        )
    assert bool(rollouts[1]["starts"][0, 0]) == refresh
    if refresh:
        assert world.reset_vectors[1][0] == pytest.approx(0.119)
        assert len([e for e in events if e[0] == "collection_refresh_scheduled"]) == 1
    else:
        assert not any(e[0].startswith("collection_") for e in events)
