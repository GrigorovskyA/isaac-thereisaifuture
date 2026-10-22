"""Gymnasium adapter over an EpisodeController.

Faults raise EpisodeFault out of step()/reset(); they are never returned as transitions.
Oracle events leave through `oracle_sink`, never through the observation or `info`.
"""

from collections.abc import Callable, Sequence
from dataclasses import asdict
from typing import Any, Protocol, runtime_checkable

import gymnasium as gym
import numpy as np
from numpy.typing import NDArray

from .encoding import OBSERVATION_SIZE, encode
from .entities import EntityFrame, OracleEvent
from .episodes import ACTION_NVEC, Action, EpisodeController, GameBackend, Scenario, Transition

UPDATES_PER_SECOND = 30  # game logic updates per second; rendering is 60 FPS and not used here


class RewardAccountant(Protocol):
    """Turns oracle events into reward. Implemented by the reward ledger (item 07)."""

    def reset(self, episode_id: int) -> None: ...

    def consume(
        self, events: Sequence[OracleEvent], elapsed_updates: int
    ) -> tuple[float, dict[str, float]]: ...


@runtime_checkable
class StateAwareAccountant(RewardAccountant, Protocol):
    """An accountant that also sees the frame and the oracle room index (reward v2)."""

    def begin(self, frame: EntityFrame, room_index: int | None) -> None: ...

    def consume(
        self,
        events: Sequence[OracleEvent],
        elapsed_updates: int,
        frame: EntityFrame | None = None,
        room_index: int | None = None,
    ) -> tuple[float, dict[str, float]]: ...

    def run_stats(self) -> dict[str, Any]: ...


class IsaacCombatEnv(gym.Env[NDArray[np.float32], NDArray[np.int64]]):
    metadata: dict[str, Any] = {"render_modes": []}

    def __init__(
        self,
        backend: GameBackend,
        scenarios: Sequence[Scenario],
        *,
        action_repeat: int = 3,
        accountant: RewardAccountant | None = None,
        oracle_sink: Callable[[OracleEvent], None] | None = None,
    ) -> None:
        super().__init__()
        if not scenarios:
            raise ValueError("At least one scenario is required")
        self.scenarios = tuple(scenarios)
        self.controller = EpisodeController(backend, repeat=action_repeat)
        self.accountant = accountant
        self.oracle_sink = oracle_sink
        self.observation_space = gym.spaces.Box(-1.0, 1.0, (OBSERVATION_SIZE,), np.float32)
        self.action_space = gym.spaces.MultiDiscrete(list(ACTION_NVEC))
        self._return = 0.0
        self._columns: dict[str, float] = {}

    def request_truncation(self, reason: str) -> None:
        """Truncate the running episode after its next step; the reason reaches step info."""
        self.controller.request_truncation(reason)

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[NDArray[np.float32], dict[str, Any]]:
        super().reset(seed=seed)
        chosen = (options or {}).get("scenario")
        if chosen is None:
            chosen = self.scenarios[int(self.np_random.integers(len(self.scenarios)))]
        elif not isinstance(chosen, Scenario):
            raise ValueError("options['scenario'] must be a Scenario")
        game_seed = int(self.np_random.integers(2**31 - 1))
        transition = self.controller.start(chosen, game_seed)
        self._return = 0.0
        self._columns = {}
        if self.accountant is not None:
            self.accountant.reset(transition.episode_id)
            if isinstance(self.accountant, StateAwareAccountant):
                self.accountant.begin(transition.frame, transition.room_index)
            self.accountant.consume(transition.events, 0)  # spawn events; reward is zero
        self._emit(transition)
        info = self._info(transition)
        info["game_seed"] = game_seed
        backend = self.controller.backend
        info["game_seed_supported"] = bool(getattr(backend, "supports_seed", False))
        return self._observe(transition.frame, info), info

    def step(
        self, action: NDArray[np.int64]
    ) -> tuple[NDArray[np.float32], float, bool, bool, dict[str, Any]]:
        if not self.action_space.contains(np.asarray(action)):
            raise ValueError(f"Invalid action: {action!r}")
        before = self.controller.last_updates
        transition = self.controller.step(Action(int(action[0]), int(action[1]), int(action[2])))
        self._emit(transition)
        reward = 0.0
        components: dict[str, float] = {}
        if self.accountant is not None:
            elapsed = transition.summary.game_updates - before
            if isinstance(self.accountant, StateAwareAccountant):
                reward, components = self.accountant.consume(
                    transition.events, elapsed, transition.frame, transition.room_index
                )
            else:
                reward, components = self.accountant.consume(transition.events, elapsed)
        self._return += reward
        for name, value in components.items():
            self._columns[name] = self._columns.get(name, 0.0) + value
        info = self._info(transition)
        info["reward_components"] = components
        if transition.outcome is not None:
            info["episode"] = {**asdict(transition.summary), "return": self._return}
            info["episode_summary"] = self._summary(transition)
        obs = self._observe(transition.frame, info)
        return obs, reward, transition.terminated, transition.truncated, info

    def close(self) -> None:
        self.controller.close()

    def _summary(self, transition: Transition) -> dict[str, Any]:
        """Episode metrics for training logs; reward columns are per-episode sums."""
        stats: dict[str, Any] = {}
        if isinstance(self.accountant, StateAwareAccountant):
            stats = self.accountant.run_stats()
        return {
            "episode_id": transition.episode_id,
            "scenario_id": transition.summary.scenario_id,
            "timesteps": transition.summary.steps,
            "game_updates": transition.summary.game_updates,
            "return": self._return,
            "columns": dict(self._columns),
            "outcome": "terminated" if transition.terminated else "truncated",
            "end_reason": transition.outcome,
            "truncation_reason": transition.truncation_reason,
            **stats,
        }

    def _emit(self, transition: Transition) -> None:
        if self.oracle_sink is not None:
            for event in transition.events:
                self.oracle_sink(event)

    def _observe(self, frame: EntityFrame, info: dict[str, Any]) -> NDArray[np.float32]:
        encoded = encode(frame)
        info["overflow"] = dict(encoded.overflow)
        info["clipped_values"] = encoded.clipped_values
        return encoded.vector

    def _info(self, transition: Transition) -> dict[str, Any]:
        return {
            "episode_id": transition.episode_id,
            "step_index": transition.step_index,
            "frame_id": transition.frame.frame_id,
            "scenario_id": transition.summary.scenario_id,
            "split": transition.summary.split,
            "outcome": transition.outcome,
            "truncation_reason": transition.truncation_reason,
        }
