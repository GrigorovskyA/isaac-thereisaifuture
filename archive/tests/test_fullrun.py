"""Full-run contract tests. The backend below is SYNTHETIC, not Isaac."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from typing import Any

import pytest

from isaac_threrisaifuture.eligibility import EligibilityDecision
from isaac_threrisaifuture.floors import (
    CombatFn,
    CombatOutcome,
    FloorDecision,
    FloorFault,
    FloorView,
    KnownRoom,
    OptionResult,
    RoomKind,
    ScriptedFloorPolicy,
)
from isaac_threrisaifuture.fullrun import (
    LevelBudget,
    RunConfig,
    RunController,
    RunOutcome,
)
from isaac_threrisaifuture.resources import Offer, RandomChooser, ResourceState
from isaac_threrisaifuture.secrets import AttemptOutcome, Cell


class SyntheticFloor:
    """SYNTHETIC one-option floor: the exit is available, so DESCEND completes it."""

    def __init__(self, run: SyntheticRun) -> None:
        self._run = run

    def view(self) -> FloorView:
        return FloorView((0, 0), {(0, 0): KnownRoom(RoomKind.OTHER)}, exit_available=True)

    def run_option(self, decision: FloorDecision, combat: CombatFn) -> OptionResult:
        run = self._run
        if run.fault_on == run.floors_done:
            raise FloorFault("synthetic bridge drop")
        if run.die_on == run.floors_done:
            return OptionResult(damage_taken=1.0, died=True)
        if run.fight:
            out = combat((0, 0))
            if out.timed_out:
                return OptionResult(timed_out=True)
        run.floors_done += 1
        return OptionResult(rooms_cleared=1, damage_taken=0.5, floor_completed=True)


class SyntheticRun:
    def __init__(
        self,
        floors_to_win: int = 2,
        fault_on: int | None = None,
        die_on: int | None = None,
        fight: bool = False,
    ) -> None:
        self.floors_to_win, self.fault_on, self.die_on, self.fight = (
            floors_to_win,
            fault_on,
            die_on,
            fight,
        )
        self.floors_done = 0
        self.releases = 0
        self.starts = 0
        self.taken: list[int] = []

    def start_run(self, seed: int) -> None:
        self.starts += 1
        self.floors_done = 0

    def depth(self) -> int:
        return self.floors_done

    def won(self) -> bool:
        return self.floors_done >= self.floors_to_win

    def floor_backend(self) -> SyntheticFloor:
        return SyntheticFloor(self)

    def resource_state(self) -> ResourceState:
        return ResourceState(coins=5)

    def offers(self) -> Sequence[Offer]:
        return [Offer(1, "synthetic_item", 1)]

    def take_offer(self, index: int) -> None:
        self.taken.append(index)

    def known_rooms(self) -> Iterable[Cell]:
        return [(0, 0), (1, 0), (0, 1)]

    def try_secret(self, cell: Cell) -> AttemptOutcome:
        return AttemptOutcome(found=False)

    def release(self) -> None:
        self.releases += 1


def _combat(room: tuple[int, int]) -> CombatOutcome:
    return CombatOutcome()


def _allow() -> EligibilityDecision:
    return EligibilityDecision(True, ())


def _controller(
    backend: SyntheticRun, gate: Callable[[], EligibilityDecision] = _allow, **kw: Any
) -> RunController:
    return RunController(backend, _combat, ScriptedFloorPolicy(), RandomChooser(0), gate, **kw)


def test_gate_blocks_start_and_fails_closed() -> None:
    for gate in (
        lambda: EligibilityDecision(False, ("slot_wrong",)),
        lambda: (_ for _ in ()).throw(RuntimeError("probe broke")),
    ):
        backend = SyntheticRun()
        report = _controller(backend, gate).run_series([1, 2, 3])
        assert backend.starts == 0
        assert report["outcome_counts"]["ineligible"] == 1
        assert report["episodes"] == 1  # series aborted
        assert report["win_rate"] == 0.0 and report["valid_episodes"] == 0


def test_win_and_taxonomy_are_distinct() -> None:
    for kwargs, expected in (
        ({}, RunOutcome.WON),
        ({"die_on": 1}, RunOutcome.DEATH),
        ({"fault_on": 0}, RunOutcome.FAULT),
        ({"floors_to_win": 99}, RunOutcome.TRUNCATED),
    ):
        backend = SyntheticRun(**kwargs)
        rec = _controller(backend, config=RunConfig(max_levels=3)).run_one(0, 7)
        assert rec.outcome is expected, kwargs
    assert backend.taken == [0, 0, 0]


def test_wall_budget_truncates() -> None:
    ticks = iter(range(0, 1000, 10))
    backend = SyntheticRun(fight=True)
    cfg = RunConfig(level=LevelBudget(max_wall_seconds=5))
    rec = _controller(backend, config=cfg, clock=lambda: next(ticks)).run_one(0, 1)
    assert rec.outcome is RunOutcome.TRUNCATED


def test_release_on_every_exit_including_fault() -> None:
    for kwargs in ({}, {"die_on": 0}, {"fault_on": 1}):
        backend = SyntheticRun(**kwargs)
        _controller(backend).run_one(0, 1)
        assert backend.releases == 1

    class BadChooser:
        def choose(self, state: ResourceState, offers: Sequence[Offer]) -> int:
            raise RuntimeError("policy crash")

    backend = SyntheticRun()
    rec = RunController(backend, _combat, ScriptedFloorPolicy(), BadChooser(), _allow).run_one(0, 1)
    assert rec.outcome is RunOutcome.FAULT and backend.releases == 1


def test_report_includes_failures_and_is_json() -> None:
    backend = SyntheticRun(fault_on=1)
    report = _controller(backend, secret_search=True).run_series([1, 2])
    assert report["outcome_counts"]["fault"] == 2
    assert [r["outcome"] for r in report["runs"]] == ["fault", "fault"]
    assert report["valid_episodes"] == 0
    assert json.loads(json.dumps(report)) == report


def test_mixed_series_rates_exclude_faults() -> None:
    backend = SyntheticRun()
    controller = _controller(backend)
    records = [controller.run_one(0, 1)]
    backend.die_on = 0
    records.append(controller.run_one(1, 2))
    backend.die_on, backend.fault_on = None, 0
    records.append(controller.run_one(2, 3))
    from isaac_threrisaifuture.fullrun import build_report

    report = build_report(records)
    assert report["episodes"] == 3 and report["valid_episodes"] == 2
    assert report["win_rate"] == 0.5


def test_invalid_budgets_rejected() -> None:
    with pytest.raises(ValueError):
        LevelBudget(max_decisions=0)
