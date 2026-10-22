"""Floor-level policy contract, option executor and baselines (offline contract).

The strategic layer chooses an option and a target among KNOWN rooms only; low-level combat is
delegated to an injected callable. Rooms are plain ``(x, y)`` grid tuples. Nothing here reads
hidden/oracle data: the policy sees only a ``FloorView`` of rooms the player legitimately knows.
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

Room = tuple[int, int]

FLOOR_SCHEMA_VERSION = 1


class FloorOption(StrEnum):
    CLEAR_ROOM = "clear_room"
    TAKE_ITEM = "take_item"
    GO_BOSS = "go_boss"
    DESCEND = "descend"


class RoomKind(StrEnum):
    NORMAL = "normal"
    ITEM = "item"
    BOSS = "boss"
    OTHER = "other"


class DecisionSource(StrEnum):
    LEARNED = "learned"
    RANDOM = "random"
    SCRIPTED = "scripted"


class FloorOutcome(StrEnum):
    COMPLETED = "completed"
    DEATH = "death"
    TIMEOUT = "timeout"
    STUCK = "stuck"
    FAULT = "fault"


class FloorFault(Exception):
    """Infrastructure failure; never a death, timeout or completed floor."""


class IllegalDecisionError(ValueError):
    """The policy chose an option or room that is not legal for the current view."""


@dataclass(frozen=True)
class KnownRoom:
    kind: RoomKind
    cleared: bool = False


@dataclass(frozen=True)
class FloorView:
    """Strategic observation: known rooms only. ``exit_available`` means the floor can be left."""

    current: Room
    known_rooms: Mapping[Room, KnownRoom]
    exit_available: bool = False

    @property
    def boss_room(self) -> Room | None:
        for room in sorted(self.known_rooms):
            if self.known_rooms[room].kind is RoomKind.BOSS:
                return room
        return None


@dataclass(frozen=True)
class FloorDecision:
    option: FloorOption
    target: Room | None
    source: DecisionSource


@dataclass(frozen=True)
class CombatOutcome:
    damage_taken: float = 0.0
    cleared: bool = True
    died: bool = False
    timed_out: bool = False


CombatFn = Callable[[Room], CombatOutcome]


@dataclass(frozen=True)
class OptionResult:
    rooms_cleared: int = 0
    damage_taken: float = 0.0
    died: bool = False
    timed_out: bool = False
    floor_completed: bool = False


class FloorBackend(Protocol):
    def view(self) -> FloorView: ...

    def run_option(self, decision: FloorDecision, combat: CombatFn) -> OptionResult:
        """Travel to the target and run the option, calling ``combat`` for fights.

        Raises ``FloorFault`` on infrastructure failure.
        """


class FloorPolicy(Protocol):
    source: DecisionSource

    def choose(self, view: FloorView) -> FloorDecision | None:
        """Return a legal decision, or ``None`` when no legal option exists."""


def legal_decisions(view: FloorView, source: DecisionSource) -> list[FloorDecision]:
    """Enumerate legal decisions in deterministic order; unknown rooms are never targets."""
    out: list[FloorDecision] = []
    for room in sorted(view.known_rooms):
        info = view.known_rooms[room]
        if info.cleared:
            continue
        if info.kind is RoomKind.NORMAL:
            out.append(FloorDecision(FloorOption.CLEAR_ROOM, room, source))
        elif info.kind is RoomKind.ITEM:
            out.append(FloorDecision(FloorOption.TAKE_ITEM, room, source))
    boss = view.boss_room
    if boss is not None and not view.known_rooms[boss].cleared:
        out.append(FloorDecision(FloorOption.GO_BOSS, boss, source))
    if view.exit_available:
        out.append(FloorDecision(FloorOption.DESCEND, None, source))
    return out


def validate_decision(view: FloorView, decision: FloorDecision) -> None:
    if decision not in legal_decisions(view, decision.source):
        raise IllegalDecisionError(f"illegal floor decision: {decision}")


class RandomFloorPolicy:
    """Seeded uniform choice among legal decisions."""

    source = DecisionSource.RANDOM

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)

    def choose(self, view: FloorView) -> FloorDecision | None:
        legal = legal_decisions(view, self.source)
        return self._rng.choice(legal) if legal else None


class ScriptedFloorPolicy:
    """SCRIPTED heuristic baseline (not learning): descend, items, normal rooms, then boss."""

    source = DecisionSource.SCRIPTED
    _priority = (
        FloorOption.DESCEND,
        FloorOption.TAKE_ITEM,
        FloorOption.CLEAR_ROOM,
        FloorOption.GO_BOSS,
    )

    def choose(self, view: FloorView) -> FloorDecision | None:
        legal = legal_decisions(view, self.source)
        for option in self._priority:
            for decision in legal:
                if decision.option is option:
                    return decision
        return None


@dataclass
class FloorMetrics:
    rooms_cleared: int = 0
    floor_completed: bool = False
    damage_taken: float = 0.0
    decisions: int = 0
    deaths: int = 0
    timeouts: int = 0
    faults: int = 0
    decisions_by_source: Counter[str] = field(default_factory=Counter)


@dataclass(frozen=True)
class FloorSummary:
    outcome: FloorOutcome
    metrics: FloorMetrics

    @property
    def terminated(self) -> bool:
        return self.outcome is FloorOutcome.DEATH

    @property
    def truncated(self) -> bool:
        return self.outcome in (FloorOutcome.TIMEOUT, FloorOutcome.STUCK)


class FloorExecutor:
    """Hierarchical option loop: the policy picks options, ``combat`` handles fights."""

    def __init__(
        self,
        policy: FloorPolicy,
        combat: CombatFn,
        max_decisions: int = 50,
    ) -> None:
        if max_decisions < 1:
            raise ValueError("max_decisions must be positive")
        self._policy = policy
        self._combat = combat
        self._max_decisions = max_decisions

    def run(self, backend: FloorBackend) -> FloorSummary:
        m = FloorMetrics()
        while m.decisions < self._max_decisions:
            try:
                decision = self._policy.choose(backend.view())
                if decision is None:
                    return FloorSummary(FloorOutcome.STUCK, m)
                validate_decision(backend.view(), decision)
                m.decisions += 1
                m.decisions_by_source[decision.source.value] += 1
                result = backend.run_option(decision, self._combat)
            except FloorFault:
                m.faults += 1
                return FloorSummary(FloorOutcome.FAULT, m)
            m.rooms_cleared += result.rooms_cleared
            m.damage_taken += result.damage_taken
            if result.died:
                m.deaths += 1
                return FloorSummary(FloorOutcome.DEATH, m)
            if result.timed_out:
                m.timeouts += 1
                return FloorSummary(FloorOutcome.TIMEOUT, m)
            if result.floor_completed:
                m.floor_completed = True
                return FloorSummary(FloorOutcome.COMPLETED, m)
        # Decision budget exhausted without completion: truncation, bounds endless loops.
        m.timeouts += 1
        return FloorSummary(FloorOutcome.TIMEOUT, m)


def aggregate(summaries: Sequence[FloorSummary]) -> dict[str, float]:
    """Per-floor rates; faults are reported separately and excluded from the rate denominators."""
    valid = [s for s in summaries if s.outcome is not FloorOutcome.FAULT]
    n = len(valid)
    return {
        "floors": float(len(summaries)),
        "faults": float(len(summaries) - n),
        "completion_rate": sum(s.metrics.floor_completed for s in valid) / n if n else 0.0,
        "death_rate": sum(s.terminated for s in valid) / n if n else 0.0,
        "truncation_rate": sum(s.truncated for s in valid) / n if n else 0.0,
        "mean_rooms_cleared": sum(s.metrics.rooms_cleared for s in valid) / n if n else 0.0,
    }
