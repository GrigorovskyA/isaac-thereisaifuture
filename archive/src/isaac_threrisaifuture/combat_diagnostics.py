"""Policy-only geometric shooting proxy; never a hit metric or action controller."""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from .encoding import OBSERVATION_SIZE, PLAYER_FEATURES, POSITION_SCALE

SHOOT_VECTORS = ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))


@dataclass(frozen=True)
class AimProxy:
    enemy_present: bool
    shooting: bool
    geometry_available: bool
    position_clipped: bool
    nearest_distance: float | None
    cosine: float | None
    coarse_aligned: bool | None


def aim_proxy(observation: NDArray[np.float32], action: NDArray[np.int64]) -> AimProxy:
    """Describe direction to the nearest encoded enemy, without consulting HP/oracles."""
    obs = np.asarray(observation)
    act = np.asarray(action)
    if obs.shape != (OBSERVATION_SIZE,) or not np.isfinite(obs).all():
        raise ValueError("Expected one finite encoded observation")
    if (
        act.shape != (2,)
        or not np.issubdtype(act.dtype, np.integer)
        or np.any(act < 0)
        or np.any(act > 4)
    ):
        raise ValueError("Expected integer MultiDiscrete([5, 5]) action")
    shooting = int(act[1]) != 0
    present = bool(obs[PLAYER_FEATURES] >= 0.5)
    dx, dy = (float(obs[PLAYER_FEATURES + i]) for i in (1, 2))
    clipped = present and (abs(dx) >= 1 or abs(dy) >= 1)
    distance = math.hypot(dx, dy) if present else 0.0
    if not present or clipped or distance == 0:
        return AimProxy(present, shooting, False, clipped, None, None, None)
    sx, sy = SHOOT_VECTORS[int(act[1])]
    cosine = (dx * sx + dy * sy) / distance if shooting else None
    aligned = cosine >= math.sqrt(0.5) - 1e-12 if cosine is not None else False
    return AimProxy(True, shooting, True, False, distance * POSITION_SCALE, cosine, aligned)
