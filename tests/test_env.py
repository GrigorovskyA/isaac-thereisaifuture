"""OFFLINE Gymnasium tests on the toy simulator. No Isaac behavior is verified here."""

import gymnasium as gym
import numpy as np
import pytest
from stable_baselines3.common.env_checker import check_env

from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.entities import OracleEvent
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episodes import EpisodeFault, Scenario
from isaac_threrisaifuture.sim import SyntheticRoomBackend

TOY = Scenario("toy", "train", 1, 90, enemy_count=2, enemy_hp=7.0)


def make_env(**kwargs: object) -> IsaacCombatEnv:
    backend = kwargs.pop("backend", None) or SyntheticRoomBackend()
    return IsaacCombatEnv(backend, [TOY], **kwargs)  # type: ignore[arg-type]


def test_passes_the_sb3_environment_checker():
    env = make_env()
    check_env(env, warn=True)
    env.close()


def test_reset_is_reproducible_for_equal_seeds():
    env = make_env()
    first, info_a = env.reset(seed=5)
    second, info_b = env.reset(seed=5)
    assert first.shape == (OBSERVATION_SIZE,)
    assert np.array_equal(first, second) and info_a["game_seed"] == info_b["game_seed"]
    assert info_a["game_seed_supported"] is True
    assert info_b["episode_id"] == info_a["episode_id"] + 1


def test_invalid_actions_are_rejected_not_clamped():
    env = make_env()
    env.reset(seed=1)
    with pytest.raises(ValueError):
        env.step(np.array([5, 0, 0]))


@pytest.mark.parametrize("bad", [[0, 0, 4], [0, 0, -1], [0, 0], [0, 0, 0, 0]])
def test_use_head_is_bounded_and_arity_is_three(bad):
    env = make_env()
    env.reset(seed=1)
    with pytest.raises(ValueError):
        env.step(np.array(bad))


def test_action_space_has_a_use_head_that_reaches_the_backend():
    seen = []

    class Spy(SyntheticRoomBackend):
        def step(self, action, repeat):
            seen.append(action)
            return super().step(action, repeat)

    env = make_env(backend=Spy())
    assert isinstance(env.action_space, gym.spaces.MultiDiscrete)
    assert env.action_space.nvec.tolist() == [5, 5, 4]
    env.reset(seed=1)
    for use in range(4):
        env.step(np.array([1, 2, use]))
    assert [(a.move, a.shoot, a.use) for a in seen[:4]] == [(1, 2, u) for u in range(4)]


def test_oracle_events_use_the_sink_not_info_or_observation():
    seen: list[OracleEvent] = []
    env = make_env(oracle_sink=seen.append)
    env.reset(seed=3)
    _, _, _, _, info = env.step(np.array([0, 2, 0]))
    assert seen and seen[0].kind == "enemy_spawned"
    assert not any("event" in key for key in info)


def test_episode_summary_appears_only_at_the_end():
    env = make_env()
    env.reset(seed=2)
    last_info: dict = {}
    terminated = truncated = False
    steps = 0
    while not (terminated or truncated):
        _, _, terminated, truncated, last_info = env.step(np.array([0, 0, 0]))
        steps += 1
        assert ("episode" in last_info) == (terminated or truncated)
    assert last_info["episode"]["return"] == 0.0 and steps >= 1


def test_transport_fault_raises_and_never_returns_a_transition():
    env = make_env(backend=SyntheticRoomBackend(fail_after_updates=4))
    env.reset(seed=1)
    with pytest.raises(EpisodeFault):
        for _ in range(10):
            env.step(np.array([0, 0, 0]))
    with pytest.raises(RuntimeError):
        env.step(np.array([0, 0, 0]))


def test_scenario_override_and_validation():
    env = make_env()
    easy = Scenario("empty", "validation", 1, 30, enemy_count=0, enemy_hp=1.0)
    _, info = env.reset(seed=1, options={"scenario": easy})
    assert info["scenario_id"] == "empty" and info["split"] == "validation"
    with pytest.raises(ValueError):
        env.reset(options={"scenario": "empty"})


def test_ten_thousand_steps_never_accept_stale_state():
    env = make_env()
    env.reset(seed=0)
    env.action_space.seed(0)
    last_frame, last_episode = -1, 0
    for _ in range(10_000):
        _, _, terminated, truncated, info = env.step(env.action_space.sample())
        if info["episode_id"] == last_episode:
            assert info["frame_id"] > last_frame
        last_frame, last_episode = info["frame_id"], info["episode_id"]
        if terminated or truncated:
            env.reset(seed=int(env.action_space.np_random.integers(1000)))
            last_frame, last_episode = -1, 0
    env.close()
