"""Offline, reward-independent analysis of declared normalized raw gameplay traces.

No game access, checkpoint deserialization, policy selection or learning claims.
Hashes establish file identity, not the truth of submitted native provenance.
"""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import Field, model_validator

from .evaluation import wilson_interval
from .observation import Counter, Label, Position, SessionId, WireModel

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Positive = Annotated[float, Field(gt=0, le=14400)]
Amount = Annotated[float, Field(ge=0, le=1e6)]
Phase = Literal["combat", "navigation", "waiting"]


class PolicySpec(WireModel):
    id: Label
    kind: Literal["checkpoint", "random", "scripted"]
    artifact_sha256: Digest  # model bytes, or versioned control source
    normalizer_sha256: Digest | None = None
    config_sha256: Digest | None = None
    checkpoint_id: Label | None = None
    training_seed: int | None = None
    inference: Literal["deterministic", "seeded_random"]
    normalization: Literal["frozen", "none"]
    recurrent_reset: Literal["episode_start"] = "episode_start"

    @model_validator(mode="after")
    def complete_identity(self) -> Self:
        if self.kind == "checkpoint" and (
            self.normalizer_sha256 is None
            or self.config_sha256 is None
            or self.checkpoint_id is None
            or self.training_seed is None
            or self.normalization != "frozen"
            or self.inference != "deterministic"
        ):
            raise ValueError("Checkpoint needs complete frozen identity")
        if self.kind == "random" and self.inference != "seeded_random":
            raise ValueError("Random control needs seeded inference")
        return self


class Case(WireModel):
    id: Label
    split: Literal["train", "validation", "test"]
    native_seed: Label
    room_shape: Label
    enemies: Annotated[list[Label], Field(min_length=1, max_length=64)]
    character: Counter
    build: Annotated[list[Label], Field(max_length=128)]
    entry_history: Label
    decision_cap: Annotated[int, Field(ge=1, le=100000)]
    wall_seconds: Positive
    max_frame_gap: Annotated[int, Field(ge=1, le=120)]


class Attempt(WireModel):
    policy_id: Label
    case_id: Label
    repeat: Counter
    policy_seed: int
    trace: Annotated[str, Field(min_length=1, max_length=240)]
    sha256: Digest


class Manifest(WireModel):
    version: Literal[1] = 1
    suite_id: Label
    code_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    runtime_fingerprint: Digest  # game/mod/observation/action versions in frozen plan
    reference: Label
    repeats: Annotated[int, Field(ge=1, le=20)]
    policies: Annotated[list[PolicySpec], Field(min_length=2, max_length=16)]
    cases: Annotated[list[Case], Field(min_length=1, max_length=32)]
    attempts: Annotated[list[Attempt], Field(max_length=256)]

    @model_validator(mode="after")
    def matrix(self) -> Self:
        policies, cases = [p.id for p in self.policies], [c.id for c in self.cases]
        if len(set(policies)) != len(policies) or len(set(cases)) != len(cases):
            raise ValueError("Duplicate policy or case")
        if self.reference not in policies or len({c.split for c in self.cases}) != 1:
            raise ValueError("Reference must exist and splits must not mix")
        if len(policies) * len(cases) * self.repeats > 256:
            raise ValueError("Comparison matrix exceeds attempt limit")
        keys = [(a.policy_id, a.case_id, a.repeat) for a in self.attempts]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate attempt cell")
        if any(p not in policies or c not in cases or r >= self.repeats for p, c, r in keys):
            raise ValueError("Attempt outside declared matrix")
        seeds: dict[tuple[str, int], int] = {}
        for attempt in self.attempts:
            cell = attempt.case_id, attempt.repeat
            if seeds.setdefault(cell, attempt.policy_seed) != attempt.policy_seed:
                raise ValueError("Policies must share predeclared per-cell policy seeds")
        return self


class Enemy(WireModel):
    id: Counter
    generation: Counter
    kind: Label
    position: Position
    hp: Amount
    phase: Literal["active", "inactive", "unknown"]


class Sample(WireModel):
    elapsed: Annotated[float, Field(ge=0, le=14400)]
    decisions: Counter
    session: SessionId
    epoch: Counter
    room_visit: Counter
    frame: Counter
    phase: Phase
    player_half_hearts: Counter
    player_position: Position
    enemies: Annotated[list[Enemy], Field(max_length=64)]
    enemy_overflow: Counter
    room_clear: bool
    player_dead: bool

    @model_validator(mode="after")
    def unique_enemies(self) -> Self:
        keys = [(e.id, e.generation) for e in self.enemies]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate raw enemy identity")
        return self


class Trace(WireModel):
    version: Literal[1] = 1
    source: Literal["native", "synthetic"]
    raw_log_sha256: Digest
    policy: PolicySpec
    policy_seed: int
    case: Case
    runtime_fingerprint: Digest
    code_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    native_start_verified: bool
    assistance: Literal["unassisted", "assisted", "unknown"]
    control: Literal["single", "mixed", "shadow"]
    policy_unchanged: bool
    stop: Literal["clear", "death", "budget", "user_stop", "fault"]
    fault: Label | None = None
    samples: Annotated[list[Sample], Field(max_length=10000)]

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if (self.stop == "fault") != (self.fault is not None):
            raise ValueError("Fault stop needs exactly one fault reason")
        if not self.samples and self.stop != "fault":
            raise ValueError("Non-fault attempt needs samples")
        for old, new in zip(self.samples, self.samples[1:], strict=False):
            if new.elapsed <= old.elapsed or new.decisions < old.decisions:
                raise ValueError("Raw time/decision order regressed")
        if self.samples and (
            self.samples[0].elapsed != 0
            or self.samples[0].decisions != 0
            or self.samples[-1].elapsed > self.case.wall_seconds
            or self.samples[-1].decisions > self.case.decision_cap
        ):
            raise ValueError("Trace exceeds budget or lacks initial baseline")
        return self


def raw_metrics(trace: Trace) -> dict[str, Any]:
    """Conservative sampled HP loss, never a missing-enemy kill or causal hit count."""
    dealt = taken = 0.0
    gaps = uncertain = comparisons = 0
    phases = dict.fromkeys(("combat", "navigation", "waiting"), 0.0)
    floors: dict[tuple[int, int], float] = {}
    occupied = bool(trace.samples and trace.samples[0].enemies)
    clear = dead = False
    for index, sample in enumerate(trace.samples):
        uncertain += int(
            sample.enemy_overflow > 0 or any(e.phase == "unknown" for e in sample.enemies)
        )
        current = {(e.id, e.generation): e for e in sample.enemies}
        if index:
            old = trace.samples[index - 1]
            phases[old.phase] += sample.elapsed - old.elapsed
            continuous = (old.session, old.epoch, old.room_visit) == (
                sample.session,
                sample.epoch,
                sample.room_visit,
            ) and 0 < sample.frame - old.frame <= trace.case.max_frame_gap
            if continuous:
                taken += max(0, old.player_half_hearts - sample.player_half_hearts)
                previous = {(e.id, e.generation): e for e in old.enemies}
                for key, enemy in current.items():
                    before = previous.get(key)
                    if before and before.phase == enemy.phase == "active":
                        comparisons += 1
                        dealt += max(0.0, min(floors.get(key, before.hp), before.hp) - enemy.hp)
                clear |= occupied and not old.room_clear and sample.room_clear
                dead |= not old.player_dead and sample.player_dead
            else:
                gaps += 1
                # Identity discontinuity never transfers HP credit to another encounter.
                if (old.session, old.epoch, old.room_visit) != (
                    sample.session,
                    sample.epoch,
                    sample.room_visit,
                ):
                    floors.clear()
        for key, enemy in current.items():
            floors[key] = min(floors.get(key, enemy.hp), enemy.hp)
    # A known negative outcome needs continuous occupied evidence through observed death.
    covered = occupied and not gaps and not uncertain
    last = trace.samples[-1] if trace.samples else None
    outcome = (
        "fault"
        if trace.stop == "fault"
        else "cleared"
        if clear and covered and trace.stop == "clear" and last and last.room_clear
        else "death"
        if dead and covered and trace.stop == "death" and last and last.player_dead
        else "unknown"
    )
    return {
        "outcome": outcome,
        "stop": trace.stop,
        "fault": trace.fault,
        "damage_dealt_hp_lower_bound": dealt,
        "damage_taken_half_hearts_lower_bound": taken,
        "verified_clear": outcome == "cleared",
        "observed_death": dead,
        "initially_occupied": occupied,
        "coverage_gaps": gaps,
        "uncertain_samples": uncertain,
        "enemy_hp_comparisons": comparisons,
        "decisions": last.decisions if last else 0,
        "seconds": last.elapsed if last else 0.0,
        "phase_seconds": phases,
        "near_wall_stationary": None,
    }


def _start_signature(trace: Trace) -> str | None:
    if not trace.samples:
        return None
    first = trace.samples[0]
    # Entity IDs and epoch/frame counters differ between sessions; geometry/HP do not.
    state = {
        "health": first.player_half_hearts,
        "position": first.player_position.model_dump(),
        "enemies": sorted(
            (e.kind, e.hp, e.phase, e.position.x, e.position.y) for e in first.enemies
        ),
        "clear": first.room_clear,
        "dead": first.player_dead,
        "phase": first.phase,
    }
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def _read(path: Path, cap: int) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(cap + 1)
    if len(data) > cap:
        raise ValueError(f"Evidence file exceeds {cap} bytes: {path}")
    return data


def compare(manifest_path: Path) -> dict[str, Any]:
    """Read only named evidence; missing cells block matching without dropping attempts."""
    manifest_bytes = _read(manifest_path, 1024 * 1024)
    manifest = Manifest.model_validate_json(manifest_bytes)
    cases = {c.id: c for c in manifest.cases}
    policies = {p.id: p for p in manifest.policies}
    records: list[dict[str, Any]] = []
    reasons: list[str] = []
    starts: dict[tuple[str, int], str | None] = {}
    total_bytes = 0
    for attempt in manifest.attempts:
        path = (manifest_path.parent / attempt.trace).resolve()
        if not path.is_relative_to(manifest_path.parent.resolve()):
            raise ValueError("Trace escapes manifest directory")
        data = _read(path, 8 * 1024 * 1024)
        total_bytes += len(data)
        if total_bytes > 128 * 1024 * 1024:
            raise ValueError("Total trace bytes exceed analysis budget")
        if hashlib.sha256(data).hexdigest() != attempt.sha256:
            raise ValueError(f"Trace hash mismatch: {attempt.trace}")
        trace = Trace.model_validate_json(data)
        issues = []
        if trace.policy != policies[attempt.policy_id] or not trace.policy_unchanged:
            issues.append("policy_identity")
        if trace.case != cases[attempt.case_id] or trace.policy_seed != attempt.policy_seed:
            issues.append("case_or_seed")
        if (
            trace.runtime_fingerprint != manifest.runtime_fingerprint
            or trace.code_revision != manifest.code_revision
        ):
            issues.append("runtime")
        if trace.source != "native" or not trace.native_start_verified:
            issues.append("native_start_unverified")
        if trace.assistance != "unassisted" or trace.control != "single":
            issues.append("control_attribution")
        metrics = raw_metrics(trace)
        start_signature = _start_signature(trace)
        start_cell = attempt.case_id, attempt.repeat
        if starts.setdefault(start_cell, start_signature) != start_signature:
            issues.append("observed_start_mismatch")
        if trace.samples and (
            sorted(e.kind for e in trace.samples[0].enemies) != sorted(trace.case.enemies)
            or trace.samples[0].phase != "combat"
        ):
            issues.append("observed_start_composition")
        if metrics["coverage_gaps"] or metrics["uncertain_samples"]:
            issues.append("incomplete_raw_coverage")
        if not metrics["initially_occupied"] or trace.stop in ("fault", "user_stop"):
            issues.append("empty_fault_or_interrupted")
        if trace.stop in ("clear", "death") and metrics["outcome"] == "unknown":
            issues.append("unverified_terminal")
        if (
            trace.stop == "budget"
            and trace.samples
            and (
                trace.samples[-1].decisions != trace.case.decision_cap
                and trace.samples[-1].elapsed != trace.case.wall_seconds
            )
        ):
            issues.append("early_budget_stop")
        if issues:
            reasons.append(
                f"{attempt.policy_id}/{attempt.case_id}/{attempt.repeat}: {','.join(issues)}"
            )
        records.append(
            {
                **attempt.model_dump(),
                **metrics,
                "issues": issues,
                "start_signature": start_signature,
            }
        )
    expected = {(p, c, r) for p in policies for c in cases for r in range(manifest.repeats)}
    present = {(r["policy_id"], r["case_id"], r["repeat"]) for r in records}
    missing = sorted(expected - present)
    if missing:
        reasons.append("missing_attempts")
    aggregates = {}
    for policy in policies:
        rows = [r for r in records if r["policy_id"] == policy]
        known = [r for r in rows if r["outcome"] in ("cleared", "death")]
        clears = sum(r["verified_clear"] for r in rows)
        decisions = sum(r["decisions"] for r in rows)
        aggregates[policy] = {
            "metrics_scope": "all_observed_attempts_not_causal",
            "attempted": len(rows),
            "missing": sum(p == policy for p, _, _ in missing),
            "verified_clears": clears,
            "known_outcomes": len(known),
            "unknown": sum(r["outcome"] == "unknown" for r in rows),
            "faults": sum(r["outcome"] == "fault" for r in rows),
            "observed_deaths": sum(r["observed_death"] for r in rows),
            "clear_rate_known": clears / len(known) if known else None,
            "clear_rate_ci95": wilson_interval(clears, len(known)),
            "clear_fraction_all_attempts": clears / len(rows) if rows else None,
            "damage_dealt_hp_lower_bound": sum(r["damage_dealt_hp_lower_bound"] for r in rows),
            "damage_taken_half_hearts_lower_bound": sum(
                r["damage_taken_half_hearts_lower_bound"] for r in rows
            ),
            "decisions": decisions,
            "seconds": sum(r["seconds"] for r in rows),
            "attributable_attempts": sum(not r["issues"] for r in rows),
        }
    paired = []
    if not reasons:
        indexed = {(r["policy_id"], r["case_id"], r["repeat"]): r for r in records}
        for policy, case, repeat in sorted(expected):
            if policy == manifest.reference:
                continue
            row, ref = indexed[policy, case, repeat], indexed[manifest.reference, case, repeat]
            paired.append(
                {
                    "policy_id": policy,
                    "case_id": case,
                    "repeat": repeat,
                    "damage_dealt_delta_hp": row["damage_dealt_hp_lower_bound"]
                    - ref["damage_dealt_hp_lower_bound"],
                    "damage_taken_delta_half_hearts": row["damage_taken_half_hearts_lower_bound"]
                    - ref["damage_taken_half_hearts_lower_bound"],
                    "clear_delta": int(row["verified_clear"]) - int(ref["verified_clear"]),
                }
            )
    return {
        "report_version": 1,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "suite": manifest.model_dump(exclude={"attempts"}),
        "status": "not_comparable" if reasons else "matched_descriptive",
        "learning_claim": False,
        "limitations": [
            "Submitted provenance requires native acceptance; hashes only detect mutation",
            "Sampled HP-loss lower bounds do not prove projectile causation or missing kills",
            "Paired deltas are descriptive; no winner, reward or tensor-based selection",
        ],
        "reasons": reasons,
        "missing": missing,
        "policies": aggregates,
        "attempts": records,
        "paired_deltas": paired,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = compare(args.manifest)
    # Exclusive output preserves evidence, including an input accidentally named as output.
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"{report['status']}: {args.output}; learning claim: false")


if __name__ == "__main__":
    main()
