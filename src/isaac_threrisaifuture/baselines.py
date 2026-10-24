"""Reference policies for comparison. Neither one learns, and neither sees oracle data."""

from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .encoding import ENEMY_OFFSET, POSITION_SCALE
from .episodes import ACTION_NVEC

ENEMY_SLOT = ENEMY_OFFSET  # the encoder orders enemies first and nearest-first
KITE_DISTANCE = 150.0 / POSITION_SCALE  # toy value: strafe when the nearest enemy is closer


class Policy(Protocol):
    name: str
    label: str

    def reset(self, seed: int) -> None: ...

    def act(self, observation: NDArray[np.float32]) -> NDArray[np.int64]: ...


class RandomPolicy:
    name = "random"
    label = "random-baseline"

    def __init__(self) -> None:
        self._rng = np.random.default_rng(0)

    def reset(self, seed: int) -> None:
        self._rng = np.random.default_rng(seed)

    def act(self, observation: NDArray[np.float32]) -> NDArray[np.int64]:
        return self._rng.integers(0, ACTION_NVEC, dtype=np.int64)


class RandomPriorPolicy:
    """Random baseline with the use head of a fresh model.

    Move and shoot are uniform. The use head presses nothing with the configured initial
    probability and splits the rest evenly over the other uses, like a model before learning.
    """

    name = "random-prior"
    label = "random-prior-baseline"

    def __init__(self, none_probability: float) -> None:
        if not 0.0 < none_probability < 1.0:
            raise ValueError("The use head none probability must be between 0 and 1")
        uses = ACTION_NVEC[2]
        rest = (1.0 - none_probability) / (uses - 1)
        self._use_probabilities = [none_probability] + [rest] * (uses - 1)
        self._rng = np.random.default_rng(0)

    def reset(self, seed: int) -> None:
        self._rng = np.random.default_rng(seed)

    def act(self, observation: NDArray[np.float32]) -> NDArray[np.int64]:
        move, shoot = self._rng.integers(0, ACTION_NVEC[:2], dtype=np.int64)
        use = self._rng.choice(len(self._use_probabilities), p=self._use_probabilities)
        return np.array([move, shoot, use], dtype=np.int64)


class ScriptedPolicy:
    """Hand-written heuristic, NOT learned: shoot the nearest enemy and strafe when it is close.

    It reads only the policy observation vector and exists to give learned agents a bar to beat.
    """

    name = "scripted"
    label = "scripted-baseline"

    def reset(self, seed: int) -> None:
        pass

    def act(self, observation: NDArray[np.float32]) -> NDArray[np.int64]:
        if observation[ENEMY_SLOT] < 0.5:  # presence bit: no visible enemy
            return np.zeros(len(ACTION_NVEC), dtype=np.int64)
        dx, dy = float(observation[ENEMY_SLOT + 1]), float(observation[ENEMY_SLOT + 2])
        horizontal = abs(dx) >= abs(dy)
        if horizontal:
            shoot = 2 if dx > 0 else 1
        else:
            shoot = 4 if dy > 0 else 3  # screen y grows downward
        move = 0
        if (dx * dx + dy * dy) ** 0.5 < KITE_DISTANCE:
            # perpendicular strafe, away from the enemy's side
            if horizontal:
                move = 3 if dy > 0 else 4
            else:
                move = 1 if dx > 0 else 2
        return np.array([move, shoot, 0], dtype=np.int64)  # never uses items
