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

from .encoding import OBSERVATION_SIZE, VisitedCells, encode
from .entities import ENTITY_KINDS, EntityFrame, EntityKind, OracleDoor, OracleEvent
from .episodes import (
    ACTION_NVEC,
    HIT_FIELDS,
    Action,
    EpisodeController,
    GameBackend,
    Scenario,
    Transition,
)

UPDATES_PER_SECOND = 30  # game logic updates per second; rendering is 60 FPS and not used here


_USE_NAMES = {1: "use_bomb", 2: "use_active", 3: "use_pillcard"}


def _new_facts() -> dict[str, Any]:
    """Per-episode facts for the summary; None means it did not happen."""
    return {
        "use_bomb": 0,
        "use_active": 0,
        "use_pillcard": 0,
        "half_hearts_lost": 0.0,
        "steps_to_first_exit": None,
        "steps_to_first_damage": None,
    }


class RewardAccountant(Protocol):
    """Turns oracle events into reward. Implemented by the reward ledger (item 07)."""

    def reset(self, episode_id: int) -> None: ...

    def consume(
        self, events: Sequence[OracleEvent], elapsed_updates: int
    ) -> tuple[float, dict[str, float]]: ...


@runtime_checkable
class StateAwareAccountant(RewardAccountant, Protocol):
    """An accountant that also sees the frame and the oracle room index (reward v4)."""

    def begin(
        self,
        frame: EntityFrame,
        room_index: int | None,
        doors: Sequence[OracleDoor] | None = None,
        enemies_present: bool = False,
    ) -> None: ...

    def consume(
        self,
        events: Sequence[OracleEvent],
        elapsed_updates: int,
        frame: EntityFrame | None = None,
        room_index: int | None = None,
        doors: Sequence[OracleDoor] | None = None,
        enemies_present: bool = False,
        terminal: bool = False,
    ) -> tuple[float, dict[str, float]]: ...

    def run_stats(self) -> dict[str, Any]: ...

    def stall_restart(self) -> float: ...

    def stagnation(self, before: float, after: float) -> float: ...


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
        self._facts = _new_facts()
        self._start_room: int | None = None
        self._idle_seconds = 0.0  # stall watchdog idle clock at the previous step
        self._visited = VisitedCells()  # run-long; a new session or game epoch clears it
        self._reset_cap_stats()

    def _backend_idle_seconds(self) -> float:
        """Idle clock of the stall watchdog; backends without one report 0.0."""
        return float(getattr(self.controller.backend, "stall_idle_seconds", 0.0))

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
        self._facts = _new_facts()
        self._reset_cap_stats()
        self._start_room = transition.room_index
        self._idle_seconds = self._backend_idle_seconds()
        if self.accountant is not None:
            self.accountant.reset(transition.episode_id)
            if isinstance(self.accountant, StateAwareAccountant):
                self.accountant.begin(
                    transition.frame,
                    transition.room_index,
                    transition.doors,
                    transition.enemies_present,
                )
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
                    transition.events,
                    elapsed,
                    transition.frame,
                    transition.room_index,
                    transition.doors,
                    transition.enemies_present,
                    transition.terminated or transition.truncated,
                )
            else:
                reward, components = self.accountant.consume(transition.events, elapsed)
            idle = self._backend_idle_seconds()
            if isinstance(self.accountant, StateAwareAccountant):
                stagnation = self.accountant.stagnation(self._idle_seconds, idle)
                reward += stagnation
                components = {**components, "stagnation": stagnation}
            self._idle_seconds = idle
            if (
                transition.truncated
                and transition.truncation_reason == "stall"
                and isinstance(self.accountant, StateAwareAccountant)
            ):
                stall = self.accountant.stall_restart()  # once: the episode ends here
                reward += stall
                components = {**components, "stall": stall}
        self._note_facts(transition, int(action[2]), components)
        self._return += reward
        for name, value in components.items():
            self._columns[name] = self._columns.get(name, 0.0) + value
        info = self._info(transition)
        info["reward_components"] = components
        obs = self._observe(transition.frame, info)  # before the summary: it counts this frame
        if transition.outcome is not None:
            info["episode"] = {**asdict(transition.summary), "return": self._return}
            info["episode_summary"] = self._summary(transition)
        return obs, reward, transition.terminated, transition.truncated, info

    def _note_facts(self, transition: Transition, use: int, components: dict[str, float]) -> None:
        facts = self._facts
        if use in _USE_NAMES:
            facts[_USE_NAMES[use]] += 1
        for event in transition.events:
            if event.kind == "player_damaged":
                facts["half_hearts_lost"] += event.amount or 0.0
        if facts["steps_to_first_damage"] is None and components.get("enemy_damage", 0.0) > 0:
            facts["steps_to_first_damage"] = transition.step_index
        room = transition.room_index
        if self._start_room is None:
            self._start_room = room
        elif facts["steps_to_first_exit"] is None and room is not None and room != self._start_room:
            facts["steps_to_first_exit"] = transition.step_index

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
            "enemies_killed": transition.summary.enemies_killed,
            **self._hits(),
            **stats,
            **self._facts,
            **self._cap_facts(),
        }

    def _reset_cap_stats(self) -> None:
        self._cap_max: dict[EntityKind, int] = dict.fromkeys(ENTITY_KINDS, 0)
        self._cap_over: dict[EntityKind, int] = dict.fromkeys(ENTITY_KINDS, 0)
        self._cap_steps = 0
        self._enemy_kinds: set[tuple[int, int]] = set()

    def _cap_facts(self) -> dict[str, float]:
        """Per kind: max count in one snapshot (cut ones included), share of steps with overflow."""
        steps = max(self._cap_steps, 1)
        return {
            **{f"max_{kind}": self._cap_max[kind] for kind in ENTITY_KINDS},
            **{f"overflow_{kind}": self._cap_over[kind] / steps for kind in ENTITY_KINDS},
            "enemy_kinds": len(self._enemy_kinds),
        }

    def _hits(self) -> dict[str, int]:
        """Player hits by source from the observer; zeros for backends without oracle metrics."""
        stats = getattr(self.controller.backend, "episode_oracle_stats", None)
        raw = stats() if stats is not None else {}
        return {name: int(raw.get(name, 0)) for name in HIT_FIELDS}

    def _emit(self, transition: Transition) -> None:
        if self.oracle_sink is not None:
            for event in transition.events:
                self.oracle_sink(event)

    def _observe(self, frame: EntityFrame, info: dict[str, Any]) -> NDArray[np.float32]:
        stall = float(getattr(self.controller.backend, "stall_fraction", 0.0))
        encoded = encode(frame, stall_fraction=stall, visited_cells=self._visited.update(frame))
        info["overflow"] = dict(encoded.overflow)
        self._cap_steps += 1
        self._enemy_kinds |= encoded.enemy_kinds
        for kind in ENTITY_KINDS:
            self._cap_max[kind] = max(self._cap_max[kind], encoded.counts.get(kind, 0))
            self._cap_over[kind] += encoded.overflow.get(kind, 0) > 0
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
