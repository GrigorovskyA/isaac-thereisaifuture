"""Opt-in real-combat reward wrapper; oracle state never leaves through policy info."""

from collections.abc import Callable
from typing import Any, SupportsFloat

import gymnasium as gym

from .firing_progress_v4 import FiringProgressV4
from .live import LiveBackend, LiveSnapshot
from .observation import ProtocolError


class FiringRewardEnv(gym.Wrapper[Any, Any, Any, Any]):
    def __init__(
        self,
        env: gym.Env[Any, Any],
        *,
        record: Callable[[str, Any], None] | None = None,
        boundary_progress: bool = False,
    ) -> None:
        super().__init__(env)
        backend = getattr(getattr(env.unwrapped, "controller", None), "backend", None)
        if not isinstance(backend, LiveBackend):
            raise TypeError("Firing reward requires a live combat environment")
        self.backend = backend
        from .firing_progress_v5 import FiringProgressV5

        self.progress = FiringProgressV5() if boundary_progress else FiringProgressV4()
        self.record = record
        self._before: LiveSnapshot | None = None
        self._bonus_return = 0.0

    def reset(self, **kwargs: Any) -> tuple[Any, dict[str, Any]]:
        result = self.env.reset(**kwargs)
        self._bonus_return = 0.0
        self._before = self.backend.latest
        if (
            self._before is None
            or self._before.oracle is None
            or self._before.oracle.firing is None
        ):
            raise ProtocolError("Requested firing reward telemetry is missing")
        self.progress.begin(self._before)
        if self.record is not None:
            self.record("firing_reward_status", {"status": self._before.oracle.firing.status})
        return result

    def step(self, action: Any) -> tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]:
        before = self._before
        observation, reward, terminated, truncated, info = self.env.step(action)
        after = self.backend.latest
        if before is None or after is None or after.oracle is None or after.oracle.firing is None:
            raise ProtocolError("Firing reward telemetry disappeared")
        if self.backend.blocked is not None:
            self.progress.begin(after)
            bonus = 0.0
        else:
            bonus = self.progress.transition(before, after)
        self._bonus_return += bonus
        self._before = after
        components = {**info.get("reward_components", {}), "firing_position": bonus}
        info = {**info, "reward_components": components}
        if "episode" in info:
            info["episode"] = {
                **info["episode"],
                "return": info["episode"]["return"] + self._bonus_return,
            }
        if self.record is not None:
            self.record(
                "firing_position_reward",
                {"frame_id": after.frame_id, "bonus": bonus, "status": after.oracle.firing.status},
            )
        return observation, float(reward) + bonus, terminated, truncated, info
