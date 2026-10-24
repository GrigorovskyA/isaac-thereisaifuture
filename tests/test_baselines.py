"""OFFLINE tests for scenario splits and reference policies. No Isaac behavior is verified."""

import dataclasses

import numpy as np
import pytest

from isaac_threrisaifuture.baselines import (
    ENEMY_SLOT,
    RandomPolicy,
    RandomPriorPolicy,
    ScriptedPolicy,
)
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.episodes import ACTION_NVEC
from isaac_threrisaifuture.scenarios import SCENARIO_SET_VERSION, SCENARIOS, SPLITS, scenarios_for


def test_splits_are_disjoint_nonempty_and_cover_the_pool():
    ids = [s.id for s in SCENARIOS]
    assert len(ids) == len(set(ids))
    parts = [{s.id for s in scenarios_for(split)} for split in SPLITS]
    assert all(parts)
    assert set().union(*parts) == set(ids)
    assert sum(len(p) for p in parts) == len(ids)
    for split in SPLITS:
        assert {s.difficulty for s in scenarios_for(split)} == {1, 2, 3}
    assert SCENARIO_SET_VERSION


def test_scenario_pool_is_immutable():
    assert isinstance(SCENARIOS, tuple)
    with pytest.raises(dataclasses.FrozenInstanceError):
        SCENARIOS[0].split = "test"  # type: ignore[misc]
    with pytest.raises(ValueError):
        scenarios_for("holdout")  # type: ignore[arg-type]


def test_random_policy_is_reproducible_and_valid():
    obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    a, b = RandomPolicy(), RandomPolicy()
    a.reset(3)
    b.reset(3)
    first = [a.act(obs) for _ in range(20)]
    assert all(np.array_equal(x, b.act(obs)) for x in first)
    assert all(((0 <= x) & (x < ACTION_NVEC)).all() and x.shape == (3,) for x in first)


def test_random_prior_policy_samples_the_configured_use_prior():
    obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    policy = RandomPriorPolicy(0.85)
    policy.reset(11)
    draws = np.array([policy.act(obs) for _ in range(20000)])
    assert ((0 <= draws) & (draws < ACTION_NVEC)).all() and draws.shape == (20000, 3)
    use = np.bincount(draws[:, 2], minlength=4) / len(draws)
    assert abs(use[0] - 0.85) < 0.01
    assert all(abs(share - 0.05) < 0.01 for share in use[1:])
    for head in (0, 1):  # move and shoot stay uniform
        share = np.bincount(draws[:, head], minlength=5) / len(draws)
        assert all(abs(s - 0.2) < 0.015 for s in share)


def test_random_prior_policy_is_reproducible_per_seed():
    obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    a, b, c = RandomPriorPolicy(0.85), RandomPriorPolicy(0.85), RandomPriorPolicy(0.85)
    a.reset(3)
    b.reset(3)
    c.reset(4)
    first = [a.act(obs) for _ in range(50)]
    assert all(np.array_equal(x, b.act(obs)) for x in first)
    assert not all(np.array_equal(x, c.act(obs)) for x in first)
    assert a.name == "random-prior"


@pytest.mark.parametrize("probability", [0.0, 1.0, -0.1, 1.5])
def test_random_prior_policy_rejects_invalid_probability(probability):
    with pytest.raises(ValueError):
        RandomPriorPolicy(probability)


def _obs(dx: float, dy: float) -> np.ndarray:
    obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    obs[ENEMY_SLOT : ENEMY_SLOT + 3] = (1.0, dx, dy)
    return obs


def test_scripted_policy_is_labelled_and_shoots_toward_the_nearest_enemy():
    policy = ScriptedPolicy()
    assert policy.label == "scripted-baseline"
    assert policy.act(np.zeros(OBSERVATION_SIZE, dtype=np.float32)).tolist() == [0, 0, 0]
    assert policy.act(_obs(0.4, 0.1)).tolist() == [0, 2, 0]  # far: shoot right, stand still
    assert policy.act(_obs(-0.4, 0.1)).tolist() == [0, 1, 0]
    assert policy.act(_obs(0.05, 0.3)).tolist() == [0, 4, 0]  # down
    assert policy.act(_obs(0.05, -0.3)).tolist() == [0, 3, 0]
    close = policy.act(_obs(0.1, 0.02))
    assert close[1] == 2 and close[0] in (3, 4)  # strafe perpendicular when close
