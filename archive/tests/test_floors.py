"""Floor policy contract tests. The floor simulator below is SYNTHETIC, not Isaac."""

from __future__ import annotations

import pytest

from isaac_threrisaifuture.floors import (
    CombatFn,
    CombatOutcome,
    DecisionSource,
    FloorDecision,
    FloorExecutor,
    FloorFault,
    FloorOption,
    FloorOutcome,
    FloorView,
    IllegalDecisionError,
    KnownRoom,
    OptionResult,
    RandomFloorPolicy,
    RoomKind,
    ScriptedFloorPolicy,
    aggregate,
    legal_decisions,
    validate_decision,
)

# SYNTHETIC layout: start (0,0); normal rooms in a row; boss revealed by clearing (2,0).
_LAYOUT = {
    (0, 0): RoomKind.OTHER,
    (1, 0): RoomKind.NORMAL,
    (2, 0): RoomKind.NORMAL,
    (1, 1): RoomKind.ITEM,
    (3, 0): RoomKind.BOSS,
}
_REVEALS = {(0, 0): [(1, 0)], (1, 0): [(2, 0), (1, 1)], (2, 0): [(3, 0)]}


class SyntheticFloor:
    def __init__(self, fault_at: int | None = None) -> None:
        self.known = {
            (0, 0): KnownRoom(RoomKind.OTHER, cleared=True),
            (1, 0): KnownRoom(RoomKind.NORMAL),
        }
        self.current = (0, 0)
        self.exit = False
        self.calls = 0
        self.fault_at = fault_at

    def view(self) -> FloorView:
        return FloorView(self.current, dict(self.known), self.exit)

    def run_option(self, decision: FloorDecision, combat: CombatFn) -> OptionResult:
        self.calls += 1
        if self.fault_at == self.calls:
            raise FloorFault("synthetic transport failure")
        if decision.option is FloorOption.DESCEND:
            return OptionResult(floor_completed=True)
        room = decision.target
        assert room is not None
        self.current = room
        kind = self.known[room].kind
        if kind is RoomKind.ITEM:
            self.known[room] = KnownRoom(kind, cleared=True)
            return OptionResult()
        out = combat(room)
        if out.died:
            return OptionResult(damage_taken=out.damage_taken, died=True)
        if out.timed_out:
            return OptionResult(damage_taken=out.damage_taken, timed_out=True)
        self.known[room] = KnownRoom(kind, cleared=True)
        for nxt in _REVEALS.get(room, []):
            self.known[nxt] = KnownRoom(_LAYOUT[nxt])
        if kind is RoomKind.BOSS:
            self.exit = True
        return OptionResult(rooms_cleared=1, damage_taken=out.damage_taken)


def _ok(_room: tuple[int, int]) -> CombatOutcome:
    return CombatOutcome(damage_taken=1.0)


def test_only_known_rooms_are_targets() -> None:
    floor = SyntheticFloor()
    targets = {d.target for d in legal_decisions(floor.view(), DecisionSource.RANDOM)}
    assert targets == {(1, 0)}
    assert (3, 0) not in targets
    with pytest.raises(IllegalDecisionError):
        validate_decision(
            floor.view(), FloorDecision(FloorOption.CLEAR_ROOM, (2, 0), DecisionSource.RANDOM)
        )


def test_boss_routing_requires_known_boss_and_descend_requires_exit() -> None:
    floor = SyntheticFloor()
    options = {d.option for d in legal_decisions(floor.view(), DecisionSource.SCRIPTED)}
    assert FloorOption.GO_BOSS not in options and FloorOption.DESCEND not in options
    floor.known[(3, 0)] = KnownRoom(RoomKind.BOSS)
    options = {d.option for d in legal_decisions(floor.view(), DecisionSource.SCRIPTED)}
    assert FloorOption.GO_BOSS in options and FloorOption.DESCEND not in options


def test_scripted_baseline_completes_floor_and_is_labelled() -> None:
    summary = FloorExecutor(ScriptedFloorPolicy(), _ok).run(SyntheticFloor())
    assert summary.outcome is FloorOutcome.COMPLETED
    assert summary.metrics.floor_completed and summary.metrics.rooms_cleared == 3
    assert dict(summary.metrics.decisions_by_source) == {"scripted": summary.metrics.decisions}


def test_truncation_is_not_termination_and_fault_is_neither() -> None:
    timeout = FloorExecutor(
        ScriptedFloorPolicy(), lambda r: CombatOutcome(cleared=False, timed_out=True)
    ).run(SyntheticFloor())
    assert timeout.truncated and not timeout.terminated
    death = FloorExecutor(
        ScriptedFloorPolicy(), lambda r: CombatOutcome(damage_taken=3.0, died=True)
    ).run(SyntheticFloor())
    assert death.terminated and not death.truncated and death.metrics.damage_taken == 3.0
    fault = FloorExecutor(ScriptedFloorPolicy(), _ok).run(SyntheticFloor(fault_at=2))
    assert fault.outcome is FloorOutcome.FAULT
    assert not fault.terminated and not fault.truncated and fault.metrics.faults == 1
    stats = aggregate([timeout, death, fault])
    assert stats["faults"] == 1 and stats["truncation_rate"] == 0.5 and stats["death_rate"] == 0.5


def test_decision_budget_bounds_loops() -> None:
    summary = FloorExecutor(RandomFloorPolicy(0), _ok, max_decisions=1).run(SyntheticFloor())
    assert summary.outcome is FloorOutcome.TIMEOUT and summary.metrics.decisions == 1


def test_random_baseline_is_deterministic_per_seed() -> None:
    def run(seed: int) -> tuple[FloorOutcome, int, float]:
        s = FloorExecutor(RandomFloorPolicy(seed), _ok).run(SyntheticFloor())
        return s.outcome, s.metrics.rooms_cleared, s.metrics.damage_taken

    assert run(7) == run(7)
    assert all(run(s)[0] in FloorOutcome for s in range(5))


def test_stuck_when_no_legal_option() -> None:
    class Dead:
        def view(self) -> FloorView:
            return FloorView((0, 0), {(0, 0): KnownRoom(RoomKind.OTHER, cleared=True)})

        def run_option(self, decision: FloorDecision, combat: CombatFn) -> OptionResult:
            raise AssertionError("must not run")

    summary = FloorExecutor(ScriptedFloorPolicy(), _ok).run(Dead())
    assert summary.outcome is FloorOutcome.STUCK and summary.truncated
