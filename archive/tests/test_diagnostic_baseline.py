"""Behavior checks for an explicitly hand-written diagnostic comparator."""

import numpy as np
import pytest

from isaac_threrisaifuture.diagnostic_baseline import ApproachDiagnosticPolicy
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE


def obs(dx=180, dy=0, obstacles=()):
    result = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    result[9:12] = [1, dx / 1000, dy / 1000]
    for n, (x, y) in enumerate(obstacles):
        result[393 + n * 8 : 396 + n * 8] = [1, x / 1000, y / 1000]
    return result


def test_open_firing_opportunity_and_no_enemy():
    p = ApproachDiagnosticPolicy()
    assert p.act(obs()).tolist() == [0, 2]
    assert p.act(obs(0, -180)).tolist() == [0, 3]
    assert p.act(np.zeros(OBSERVATION_SIZE, dtype=np.float32)).tolist() == [0, 0]


def test_known_blocker_prevents_direct_shot_and_routes_around_it():
    action = ApproachDiagnosticPolicy().act(obs(obstacles=[(20, 0)]))
    assert action[1] == 0 and action[0] in (1, 3, 4)


def test_approach_requires_alignment_and_ignores_clipped_absolute_position():
    x = obs(300, 120)
    p = ApproachDiagnosticPolicy()
    first = p.act(x)
    x[0:9] = 1
    assert p.act(x).tolist() == first.tolist()
    assert first[0] != 0 and first[1] == 0


def test_unavailable_space_holds_and_invalid_input_fails():
    p = ApproachDiagnosticPolicy()
    assert p.act(obs(300, 0, [(-20, 0), (20, 0), (0, -20), (0, 20)])).tolist() == [0, 0]
    with pytest.raises(ValueError):
        p.act(np.zeros(3, dtype=np.float32))
