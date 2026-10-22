"""Full-run integration contract (offline): composes combat, floor, resource and secret layers.

``RunController`` is a plain loop, not an orchestrator: it runs injected policies over a
``RunBackend`` under per-level budgets and reports every episode, including failures. Death,
truncation, infrastructure fault and ineligible-abort are separate outcomes. Held actions are
released on every exit path.
"""

from __future__ import annotations

import time
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from .eligibility import EligibilityDecision
from .floors import (
    CombatFn,
    CombatOutcome,
    FloorBackend,
    FloorExecutor,
    FloorOutcome,
    FloorPolicy,
)
from .resources import BuildChooser, Offer, ResourceState
from .secrets import AttemptOutcome, Cell, SearchBudget, run_search

REPORT_SCHEMA_VERSION = 1


class RunOutcome(StrEnum):
    WON = "won"
    DEATH = "death"
    TRUNCATED = "truncated"
    FAULT = "fault"
    INELIGIBLE = "ineligible"


class RunBackend(Protocol):
    """Seam to the real bridge or an offline simulator. Exposes no hidden/oracle data."""

    def start_run(self, seed: int) -> None: ...

    def depth(self) -> int:
        """Number of floors completed so far."""
        ...

    def won(self) -> bool: ...

    def floor_backend(self) -> FloorBackend: ...

    def resource_state(self) -> ResourceState: ...

    def offers(self) -> Sequence[Offer]: ...

    def take_offer(self, index: int) -> None: ...

    def known_rooms(self) -> Iterable[Cell]: ...

    def try_secret(self, cell: Cell) -> AttemptOutcome: ...

    def release(self) -> None:
        """Neutral input; idempotent and safe after faults."""
        ...


class KnowledgeSource(Protocol):
    @property
    def synthetic(self) -> bool: ...

    @property
    def empty(self) -> bool: ...


EligibilityGate = Callable[[], EligibilityDecision]


@dataclass(frozen=True)
class LevelBudget:
    max_decisions: int = 50
    max_wall_seconds: float = 600.0

    def __post_init__(self) -> None:
        if self.max_decisions < 1 or self.max_wall_seconds <= 0:
            raise ValueError("level budgets must be positive")


@dataclass(frozen=True)
class RunConfig:
    max_levels: int = 8
    level: LevelBudget = field(default_factory=LevelBudget)
    secret_budget: SearchBudget = field(default_factory=lambda: SearchBudget(2, 20))

    def __post_init__(self) -> None:
        if self.max_levels < 1:
            raise ValueError("max_levels must be positive")


@dataclass
class RunRecord:
    run_index: int
    seed: int
    outcome: RunOutcome
    depth: int = 0
    damage_taken: float = 0.0
    rooms_cleared: int = 0
    secrets_found: int = 0
    levels: list[str] = field(default_factory=list)
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_index": self.run_index,
            "seed": self.seed,
            "outcome": self.outcome.value,
            "depth": self.depth,
            "damage_taken": self.damage_taken,
            "rooms_cleared": self.rooms_cleared,
            "secrets_found": self.secrets_found,
            "levels": list(self.levels),
            "detail": self.detail,
        }


def build_report(
    records: Sequence[RunRecord], knowledge: KnowledgeSource | None = None
) -> dict[str, Any]:
    """JSON-serializable; lists every episode. Rates exclude faults and ineligible aborts."""
    counts = Counter(r.outcome.value for r in records)
    valid = [r for r in records if r.outcome not in (RunOutcome.FAULT, RunOutcome.INELIGIBLE)]
    n = len(valid)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "episodes": len(records),
        "outcome_counts": {o.value: counts.get(o.value, 0) for o in RunOutcome},
        "valid_episodes": n,
        "win_rate": sum(r.outcome is RunOutcome.WON for r in valid) / n if n else 0.0,
        "mean_depth": sum(r.depth for r in valid) / n if n else 0.0,
        "mean_damage_taken": sum(r.damage_taken for r in valid) / n if n else 0.0,
        "knowledge": (
            None
            if knowledge is None
            else {"empty": knowledge.empty, "synthetic": knowledge.synthetic}
        ),
        "runs": [r.to_dict() for r in records],
    }


class RunController:
    def __init__(
        self,
        backend: RunBackend,
        combat: CombatFn,
        floor_policy: FloorPolicy,
        chooser: BuildChooser,
        gate: EligibilityGate,
        config: RunConfig | None = None,
        *,
        secret_search: bool = False,
        knowledge: KnowledgeSource | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._backend = backend
        self._combat = combat
        self._policy = floor_policy
        self._chooser = chooser
        self._gate = gate
        self._config = config or RunConfig()
        self._secrets = secret_search
        self._knowledge = knowledge
        self._clock = clock

    def run_series(self, seeds: Sequence[int]) -> dict[str, Any]:
        """Run one episode per seed; an ineligible gate aborts the series (fail-closed)."""
        records: list[RunRecord] = []
        for i, seed in enumerate(seeds):
            record = self.run_one(i, seed)
            records.append(record)
            if record.outcome is RunOutcome.INELIGIBLE:
                break
        return build_report(records, self._knowledge)

    def _allowed(self) -> tuple[bool, str]:
        try:
            decision = self._gate()
        except Exception as exc:  # noqa: BLE001 - gate failure must deny, never crash or allow
            return False, f"gate_error:{type(exc).__name__}"
        if decision.allowed is not True:
            return False, ",".join(decision.reasons) or "denied"
        return True, ""

    def run_one(self, index: int, seed: int) -> RunRecord:
        allowed, why = self._allowed()
        if not allowed:
            return RunRecord(index, seed, RunOutcome.INELIGIBLE, detail=why)
        rec = RunRecord(index, seed, RunOutcome.TRUNCATED)
        try:
            self._play(rec, seed)
        except Exception as exc:  # noqa: BLE001 - any failure here is a fault, not a death
            rec.outcome = RunOutcome.FAULT
            rec.detail = f"{type(exc).__name__}: {exc}"
        finally:
            self._release(rec)
        return rec

    def _release(self, rec: RunRecord) -> None:
        try:
            self._backend.release()
        except Exception as exc:  # noqa: BLE001 - failed release is itself a fault
            rec.outcome = RunOutcome.FAULT
            rec.detail = (rec.detail + "; " if rec.detail else "") + f"release_failed:{exc}"

    def _play(self, rec: RunRecord, seed: int) -> None:
        b, cfg = self._backend, self._config
        b.start_run(seed)
        for _ in range(cfg.max_levels):
            self._prepare_level(rec)
            deadline = self._clock() + cfg.level.max_wall_seconds
            summary = FloorExecutor(
                self._policy, self._bounded(deadline), cfg.level.max_decisions
            ).run(b.floor_backend())
            m = summary.metrics
            rec.levels.append(summary.outcome.value)
            rec.damage_taken += m.damage_taken
            rec.rooms_cleared += m.rooms_cleared
            rec.depth = b.depth()
            if summary.outcome is FloorOutcome.DEATH:
                rec.outcome = RunOutcome.DEATH
                return
            if summary.outcome is FloorOutcome.FAULT:
                rec.outcome = RunOutcome.FAULT
                rec.detail = "floor_fault"
                return
            if summary.outcome is not FloorOutcome.COMPLETED:
                rec.outcome = RunOutcome.TRUNCATED
                rec.detail = summary.outcome.value
                return
            if b.won():
                rec.outcome = RunOutcome.WON
                return
        rec.detail = "max_levels"

    def _bounded(self, deadline: float) -> CombatFn:
        def fight(room: tuple[int, int]) -> CombatOutcome:
            if self._clock() >= deadline:
                return CombatOutcome(cleared=False, timed_out=True)
            return self._combat(room)

        return fight

    def _prepare_level(self, rec: RunRecord) -> None:
        b = self._backend
        offers = b.offers()
        if offers:
            pick = self._chooser.choose(b.resource_state(), offers)
            if not -1 <= pick < len(offers):
                raise ValueError(f"chooser returned invalid index {pick}")
            if pick >= 0:
                b.take_offer(pick)
        if self._secrets:
            result = run_search(b.known_rooms(), self._config.secret_budget, b.try_secret)
            rec.secrets_found += int(result.found)
