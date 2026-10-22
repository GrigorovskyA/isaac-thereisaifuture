"""Campaign loop and verification tests (synthetic goals; not real Isaac evidence)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from isaac_threrisaifuture.campaign import (
    CampaignController,
    CampaignLimits,
    CampaignStateError,
    RunReport,
    verify_campaign,
)
from isaac_threrisaifuture.eligibility import EligibilityEvidence
from isaac_threrisaifuture.progression import Ledger, UnlockGraph

GRAPH = UnlockGraph("final", {"final": ("base",), "base": ()})
GOOD = EligibilityEvidence(
    slot_id=2,
    achievements_enabled=True,
    console_or_debug_used=False,
    save_edited_or_imported=False,
    achievement_blocking_mods=(),
    game_version="synthetic",
)


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


DEFAULT_LIMITS = CampaignLimits(10, 100.0)


def make(
    tmp_path: Path,
    reports: list[RunReport],
    evidence: Callable[[], EligibilityEvidence] = lambda: GOOD,
    limits: CampaignLimits = DEFAULT_LIMITS,
    clock: Clock | None = None,
    on_run: Callable[[], None] = lambda: None,
) -> CampaignController:
    it = iter(reports)

    def run_once(goal: str) -> RunReport:
        on_run()
        return next(it)

    return CampaignController(
        GRAPH,
        Ledger(tmp_path / "ledger.jsonl"),
        tmp_path / "state.json",
        evidence,
        run_once,
        limits,
        clock or Clock(),
        lambda: "2026-01-01T00:00:00Z",
    )


def rep(run_id: str, goals: tuple[str, ...], source: str = "observed_in_game", **kw) -> RunReport:
    return RunReport(run_id, "s1", source, goals, **kw)


def test_full_campaign_verifies(tmp_path: Path) -> None:
    c = make(tmp_path, [rep("r1", ("base",)), rep("r2", ("final",), user_assisted=True)])
    result = c.run()
    assert result.stop_reason == "target_observed"
    report = verify_campaign(GRAPH, c.ledger, tmp_path / "state.json")
    assert report.status == "verified"
    assert (report.autonomous_runs, report.user_assisted_runs) == (1, 1)


def test_ineligible_before_run_stops_without_running(tmp_path: Path) -> None:
    ran: list[int] = []
    bad = EligibilityEvidence()
    c = make(tmp_path, [], evidence=lambda: bad, on_run=lambda: ran.append(1))
    assert c.run().stop_reason == "ineligible"
    assert not ran
    assert c.state["denials"]
    assert verify_campaign(GRAPH, c.ledger, tmp_path / "state.json").status == "unverified"


def test_eligibility_lost_during_run_discards_evidence(tmp_path: Path) -> None:
    calls = {"n": 0}

    def evidence() -> EligibilityEvidence:
        calls["n"] += 1
        return GOOD if calls["n"] == 1 else EligibilityEvidence(slot_id=2)

    c = make(tmp_path, [rep("r1", ("base",))], evidence=evidence)
    assert c.run().stop_reason == "ineligible"
    assert c.ledger.events == []


@pytest.mark.parametrize("source", ["manual_note", "inferred"])
def test_non_observed_evidence_is_not_ledgered(tmp_path: Path, source: str) -> None:
    c = make(tmp_path, [rep("r1", ("base",), source=source)] * 10, limits=CampaignLimits(2, 100))
    assert c.run().stop_reason == "max_runs"
    assert c.ledger.events == []


def test_unknown_goal_in_report_stops(tmp_path: Path) -> None:
    c = make(tmp_path, [rep("r1", ("nope",))])
    assert c.run().stop_reason == "invalid_report"
    assert c.ledger.events == []


def test_run_fault_and_exception_stop(tmp_path: Path) -> None:
    c = make(tmp_path, [rep("r1", (), fault="bridge_timeout")])
    assert c.run().stop_reason == "run_fault"


def test_run_once_exception_stops(tmp_path: Path) -> None:
    assert make(tmp_path, []).run().stop_reason == "run_fault"  # StopIteration from run_once


def test_max_runs_budget_persists_across_resume(tmp_path: Path) -> None:
    limits = CampaignLimits(1, 100.0)
    c = make(tmp_path, [rep("r1", ())], limits=limits)
    assert c.run().stop_reason == "max_runs"
    again = make(tmp_path, [rep("r2", ())], limits=limits)
    result = again.run()
    assert (result.stop_reason, result.runs_this_call, result.runs_total) == ("max_runs", 0, 1)


def test_wall_budget(tmp_path: Path) -> None:
    clock = Clock()
    c = make(
        tmp_path,
        [rep("r1", ())],
        limits=CampaignLimits(10, 5.0),
        clock=clock,
        on_run=lambda: setattr(clock, "t", 6.0),
    )
    assert c.run().stop_reason == "max_wall_seconds"


def test_interrupted_run_is_counted_not_replayed(tmp_path: Path) -> None:
    (tmp_path / "state.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "running",
                "stop_reason": None,
                "runs": [],
                "denials": [],
            }  # fmt: skip
        )
    )
    c = make(tmp_path, [], limits=CampaignLimits(1, 100.0))
    assert c.run().stop_reason == "max_runs"


def test_corrupt_state_refuses_to_resume(tmp_path: Path) -> None:
    (tmp_path / "state.json").write_text("{not json")
    with pytest.raises(CampaignStateError):
        make(tmp_path, [])


def test_tampered_ledger_blocks(tmp_path: Path) -> None:
    c = make(tmp_path, [rep("r1", ("base",))], limits=CampaignLimits(1, 100.0))
    c.run()
    path = tmp_path / "ledger.jsonl"
    path.write_text(path.read_text().replace("base", "final"))
    bad = Ledger(path)
    assert verify_campaign(GRAPH, bad, tmp_path / "state.json").status == "blocked"
    blocked = CampaignController(
        GRAPH, bad, tmp_path / "state.json", lambda: GOOD, lambda g: rep("r", ()),
        CampaignLimits(5, 5), Clock(), lambda: "t",
    )  # fmt: skip
    assert blocked.run().stop_reason == "ledger_invalid"


def test_target_without_allowed_audit_is_unverified(tmp_path: Path) -> None:
    c = make(tmp_path, [rep("r1", ("base", "final"))])
    c.run()
    state = json.loads((tmp_path / "state.json").read_text())
    state["runs"][0]["audits"][1]["allowed"] = False
    (tmp_path / "state.json").write_text(json.dumps(state))
    report = verify_campaign(GRAPH, c.ledger, tmp_path / "state.json")
    assert report.status == "unverified"


def test_target_evidence_not_from_ledgered_run_is_unverified(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.append("final", "observed_in_game", "s", "ghost", "t")
    assert verify_campaign(GRAPH, ledger, tmp_path / "state.json").status == "unverified"


def test_manual_target_note_never_verifies(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.append("final", "manual_note", "s", "r", "t")
    assert verify_campaign(GRAPH, ledger, tmp_path / "state.json").status == "unverified"
