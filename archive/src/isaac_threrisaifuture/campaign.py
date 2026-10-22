"""Bounded, resumable, fail-closed Dead God campaign loop (offline contract).

The controller never plays: it gates each run on eligibility, picks a goal, calls an injected
``run_once`` and records only ``observed_in_game`` evidence. Real-game wiring is blocked.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Literal

from isaac_threrisaifuture.eligibility import (
    EligibilityEvidence,
    audit_record,
    evaluate,
)
from isaac_threrisaifuture.progression import (
    COUNTED_SOURCE,
    GoalSelection,
    Ledger,
    LedgerError,
    UnlockGraph,
    select_next_goal,
)

STATE_SCHEMA_VERSION: Final = 1
TARGET_FINAL: Final = "target_observed"

VerificationStatus = Literal["verified", "unverified", "blocked"]


class CampaignStateError(Exception):
    """State file is malformed or unsafe to resume from."""


@dataclass(frozen=True)
class RunReport:
    """What one run claims. Only ``evidence_source == "observed_in_game"`` is ledgered."""

    run_id: str
    session_id: str
    evidence_source: str
    observed_goals: tuple[str, ...] = ()
    user_assisted: bool = False
    fault: str | None = None


@dataclass(frozen=True)
class CampaignLimits:
    max_runs: int
    max_wall_seconds: float


@dataclass(frozen=True)
class CampaignResult:
    stop_reason: str
    runs_total: int
    runs_this_call: int


@dataclass(frozen=True)
class VerificationReport:
    status: VerificationStatus
    reasons: tuple[str, ...]
    autonomous_runs: int
    user_assisted_runs: int
    remaining: tuple[str, ...]


RunOnce = Callable[[str], RunReport]


def _empty_state() -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "status": "idle",
        "stop_reason": None,
        "runs": [],
        "denials": [],
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return _empty_state()
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["schema_version"] != STATE_SCHEMA_VERSION:
            raise CampaignStateError("unsupported campaign state schema_version")
        if not isinstance(state["runs"], list) or not isinstance(state["denials"], list):
            raise CampaignStateError("runs and denials must be lists")
        if state["status"] not in ("idle", "running", "stopped"):
            raise CampaignStateError("unknown status")
    except (ValueError, KeyError, TypeError) as exc:
        raise CampaignStateError(f"malformed campaign state: {exc!r}") from exc
    return dict(state)


class CampaignController:
    def __init__(
        self,
        graph: UnlockGraph,
        ledger: Ledger,
        state_path: Path,
        get_evidence: Callable[[], EligibilityEvidence],
        run_once: RunOnce,
        limits: CampaignLimits,
        clock: Callable[[], float],
        timestamp: Callable[[], str],
    ) -> None:
        self.graph = graph
        self.ledger = ledger
        self.state_path = state_path
        self.get_evidence = get_evidence
        self.run_once = run_once
        self.limits = limits
        self.clock = clock
        self.timestamp = timestamp
        self.state = load_state(state_path)
        # A crash mid-run leaves status "running": count it as an unaccounted run, never replay it.
        if self.state["status"] == "running":
            self.state["runs"].append({"run_id": None, "interrupted": True, "audits": []})

    def _save(self) -> None:
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".part")
        tmp.write_text(json.dumps(self.state, sort_keys=True, indent=1), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def _stop(self, reason: str, calls: int) -> CampaignResult:
        self.state["status"] = "stopped"
        self.state["stop_reason"] = reason
        self._save()
        return CampaignResult(reason, len(self.state["runs"]), calls)

    def _gate(self) -> dict[str, Any] | None:
        """Return an allowed audit record or None (denial is recorded)."""
        evidence = self.get_evidence()
        decision = evaluate(evidence)
        record = audit_record(evidence, decision)
        if decision.allowed:
            return record
        self.state["denials"].append({"timestamp": self.timestamp(), "audit": record})
        return None

    def run(self) -> CampaignResult:
        start = self.clock()
        calls = 0
        if not self.ledger.verified:
            return self._stop("ledger_invalid", calls)
        while True:
            if len(self.state["runs"]) >= self.limits.max_runs:
                return self._stop("max_runs", calls)
            if self.clock() - start >= self.limits.max_wall_seconds:
                return self._stop("max_wall_seconds", calls)
            selection: GoalSelection = select_next_goal(self.graph, self.ledger)
            if selection.goal is None:
                return self._stop(TARGET_FINAL, calls)
            pre = self._gate()
            if pre is None:
                return self._stop("ineligible", calls)
            run: dict[str, Any] = {"run_id": None, "goal": selection.goal, "audits": [pre]}
            self.state["runs"].append(run)
            self.state["status"] = "running"
            self._save()
            try:
                report = self.run_once(selection.goal)
            except Exception:
                run["fault"] = "run_once_raised"
                return self._stop("run_fault", calls + 1)
            calls += 1
            run.update(
                run_id=report.run_id,
                session_id=report.session_id,
                user_assisted=report.user_assisted,
                evidence_source=report.evidence_source,
                fault=report.fault,
            )
            if report.fault is not None:
                return self._stop("run_fault", calls)
            post = self._gate()
            if post is None:
                run["audits"].append({"allowed": False})
                return self._stop("ineligible", calls)
            run["audits"].append(post)
            if report.evidence_source == COUNTED_SOURCE:
                unknown = [g for g in report.observed_goals if g not in self.graph.requires]
                if unknown:
                    return self._stop("invalid_report", calls)
                try:
                    for goal in report.observed_goals:
                        stamp = self.timestamp()
                        self.ledger.append(
                            goal, COUNTED_SOURCE, report.session_id, report.run_id, stamp
                        )
                except LedgerError:
                    return self._stop("ledger_invalid", calls)
            self._save()


def verify_campaign(graph: UnlockGraph, ledger: Ledger, state_path: Path) -> VerificationReport:
    """Dead God counts only with a verified ledger, observed evidence and allowed audits."""
    try:
        state = load_state(state_path)
        done = ledger.completed_goals()
    except (CampaignStateError, LedgerError) as exc:
        return VerificationReport("blocked", (f"cannot verify: {exc}",), 0, 0, ())
    runs = [r for r in state["runs"] if not r.get("interrupted")]
    assisted = sum(1 for r in runs if r.get("user_assisted"))
    remaining = tuple(sorted(select_next_goal(graph, ledger).remaining))

    def counts(reasons: tuple[str, ...], status: VerificationStatus) -> VerificationReport:
        return VerificationReport(status, reasons, len(runs) - assisted, assisted, remaining)

    if graph.target not in done:
        return counts(("no observed_in_game evidence of the target",), "unverified")
    bad: list[str] = []
    by_id = {r["run_id"]: r for r in runs if r.get("run_id")}
    for event in (e for e in ledger.events if e.source == COUNTED_SOURCE):
        run = by_id.get(event.run_id)
        audits = run["audits"] if run else []
        if len(audits) != 2 or not all(a.get("allowed") is True for a in audits):
            bad.append(f"run {event.run_id!r} lacks allowed eligibility audits")
    if bad:
        return counts(tuple(sorted(set(bad))), "unverified")
    if any(r.get("interrupted") for r in state["runs"]):
        return counts(("an interrupted run has no audit trail",), "unverified")
    return counts((), "verified")
