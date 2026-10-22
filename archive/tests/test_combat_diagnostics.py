import numpy as np
import pytest

from isaac_threrisaifuture.combat_diagnostics import aim_proxy
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE, PLAYER_FEATURES


def observation(dx=0.2, dy=0.0):
    obs = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    obs[PLAYER_FEATURES : PLAYER_FEATURES + 3] = [1, dx, dy]
    return obs


@pytest.mark.parametrize(
    "dx,dy,shoot,expected",
    [
        (0.2, 0, 2, 1),
        (0.2, 0, 1, -1),
        (0, -0.2, 3, 1),
        (0, 0.2, 4, 1),
        (0.2, 0, 3, 0),
    ],
)
def test_screen_direction_cosine(dx, dy, shoot, expected):
    score = aim_proxy(observation(dx, dy), np.array([0, shoot]))
    assert score.cosine == pytest.approx(expected)
    assert score.coarse_aligned == (expected == 1)


def test_no_shoot_is_available_geometry_but_not_alignment():
    score = aim_proxy(observation(), np.array([0, 0]))
    assert score.geometry_available and not score.shooting
    assert score.cosine is None and score.coarse_aligned is False


@pytest.mark.parametrize("kind", ["missing", "zero", "clipped"])
def test_unavailable_geometry_is_excluded(kind):
    obs = observation(1 if kind == "clipped" else 0, 0)
    if kind == "missing":
        obs[PLAYER_FEATURES] = 0
    score = aim_proxy(obs, np.array([0, 2]))
    assert not score.geometry_available and score.coarse_aligned is None


def test_hp_invariance_and_input_immutability():
    obs = observation()
    action = np.array([0, 2])
    before = obs.copy()
    original = aim_proxy(obs, action)
    np.testing.assert_array_equal(obs, before)
    obs[PLAYER_FEATURES + 6 : PLAYER_FEATURES + 8] = [1, 0.01]
    assert aim_proxy(obs, action) == original


@pytest.mark.parametrize("action", [[0, 5], [0, -1], [0], [0.0, 2.0], [True, False]])
def test_invalid_actions_refused(action):
    with pytest.raises(ValueError):
        aim_proxy(observation(), np.asarray(action))


def test_invalid_observations_refused():
    for obs in (np.zeros(2), np.full(OBSERVATION_SIZE, np.nan)):
        with pytest.raises(ValueError):
            aim_proxy(obs, np.array([0, 2]))
