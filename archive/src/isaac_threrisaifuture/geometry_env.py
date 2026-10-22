"""Explicit opt-in observation2 wrapper; no access to oracle data."""

from typing import Any

import gymnasium as gym
import numpy as np

from .observation import ProtocolError
from .policy_geometry import GEOMETRY_OBSERVATION_SIZE, encode_geometry


class GeometryObservationEnv(gym.ObservationWrapper[Any, Any, Any]):
    def __init__(self, env: gym.Env[Any, Any]) -> None:
        super().__init__(env)
        self.observation_space = gym.spaces.Box(-1.0, 1.0, (GEOMETRY_OBSERVATION_SIZE,), np.float32)

    def observation(self, observation: Any) -> Any:
        base: Any = self.env.unwrapped
        snap = base.controller.backend.latest
        if snap is None or snap.entity_frame is None or snap.combat_geometry is None:
            raise ProtocolError("Requested observable combat geometry is missing")
        return encode_geometry(snap.entity_frame, snap.combat_geometry)
