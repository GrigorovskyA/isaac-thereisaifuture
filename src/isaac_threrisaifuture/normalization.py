"""Observation normalizer of the pure profile: only continuous features are normalized.

SB3's VecNormalize centres, scales and clips every index. A binary flag or one-hot bit that is
almost always 0 then jumps to about +10 the first time it is set, which happens exactly in new
layouts (a new minimap cell, a rare room class, an item bucket). Here binary and one-hot features
pass through unchanged; the running statistics still cover every index, so the saved state has
the usual shape. Saved normalizers pickle this class by its module path, so keep the name and
module stable. Torch is not needed; stable-baselines3 is imported at module load.
"""

from typing import Any

import numpy as np
from numpy.typing import NDArray
from stable_baselines3.common.running_mean_std import RunningMeanStd
from stable_baselines3.common.vec_env import VecEnv, VecNormalize

from .checkpoints import CheckpointError
from .encoding import continuous_mask

CONTINUOUS_ONLY = "continuous_only"  # contract value `observation_normalization`
# Floor of the running variance of a continuous index. The encoder already scales continuous
# features to about [-1, 1]; a rarely used entity slot is almost always 0, so its variance is tiny
# and its first real value would hit the clip of 10. With the floor such a value stays within
# about 3 standard units, while features with a larger spread are scaled as before.
VARIANCE_FLOOR = 0.1


class ContinuousVecNormalize(VecNormalize):
    """VecNormalize that normalizes and clips the continuous indices only."""

    def __init__(self, venv: VecEnv, **kwargs: Any) -> None:
        super().__init__(venv, **kwargs)
        self.continuous = continuous_mask()
        if self.observation_space.shape != self.continuous.shape:
            raise ValueError("Continuous-only normalization needs the project observation size")

    def _normalize_obs(self, obs: np.ndarray, obs_rms: RunningMeanStd) -> np.ndarray:
        std = np.sqrt(np.maximum(obs_rms.var, VARIANCE_FLOOR) + self.epsilon)
        scaled = np.clip((obs - obs_rms.mean) / std, -self.clip_obs, self.clip_obs)
        return np.where(self.continuous, scaled, obs)

    def _unnormalize_obs(self, obs: np.ndarray, obs_rms: RunningMeanStd) -> np.ndarray:
        std = np.sqrt(np.maximum(obs_rms.var, VARIANCE_FLOOR) + self.epsilon)
        return np.where(self.continuous, obs * std + obs_rms.mean, obs)


def check_continuous_only(normalizer: Any) -> None:
    """Refuse a loaded normalizer that is not continuous-only over the current layout."""
    if not isinstance(normalizer, ContinuousVecNormalize):
        raise CheckpointError("Saved normalizer is not the continuous-only normalizer")
    mask: NDArray[np.bool_] | None = getattr(normalizer, "continuous", None)
    if not isinstance(mask, np.ndarray) or not np.array_equal(mask, continuous_mask()):
        raise CheckpointError("Saved continuous feature mask does not match the encoder layout")
