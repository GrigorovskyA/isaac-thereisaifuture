"""Synthetic contract tests; no Isaac or learned-play acceptance."""

import copy
import hashlib
import json
import subprocess
import sys

import pytest

from isaac_threrisaifuture.gameplay_comparison import Manifest, Trace, compare, raw_metrics

DIGEST = "a" * 64
POLICY = {
    "id": "original-t6912",
    "kind": "checkpoint",
    "artifact_sha256": DIGEST,
    "normalizer_sha256": DIGEST,
    "config_sha256": DIGEST,
    "checkpoint_id": "original-t6912",
    "training_seed": 20,
    "inference": "deterministic",
    "normalization": "frozen",
}
CONTROL = {
    "id": "random",
    "kind": "random",
    "artifact_sha256": "b" * 64,
    "inference": "seeded_random",
    "normalization": "none",
}
CASE = {
    "id": "ordinary-a",
    "split": "validation",
    "native_seed": "DECLARED-SEED",
    "room_shape": "small-square",
    "enemies": ["ordinary:one"],
    "character": 0,
    "build": ["starting-build"],
    "entry_history": "fresh-room-from-left",
    "decision_cap": 4,
    "wall_seconds": 10.0,
    "max_frame_gap": 3,
}


def sample(index, hp=10.0, **kwargs):
    return {
        "elapsed": float(index),
        "decisions": index,
        "session": "a" * 32,
        "epoch": 1,
        "room_visit": 1,
        "frame": index * 3,
        "phase": "combat",
        "player_half_hearts": 6,
        "player_position": {"x": 100.0, "y": 100.0},
        "enemies": [
            {
                "id": 1,
                "generation": 0,
                "hp": hp,
                "phase": "active",
                "kind": "ordinary:one",
                "position": {"x": 150.0, "y": 100.0},
            }
        ],
        "enemy_overflow": 0,
        "room_clear": False,
        "player_dead": False,
        **kwargs,
    }


def trace(**kwargs):
    return {
        "source": "native",
        "raw_log_sha256": DIGEST,
        "policy": copy.deepcopy(POLICY),
        "policy_seed": 7,
        "case": copy.deepcopy(CASE),
        "runtime_fingerprint": DIGEST,
        "code_revision": "c" * 40,
        "native_start_verified": True,
        "assistance": "unassisted",
        "control": "single",
        "policy_unchanged": True,
        "stop": "clear",
        "samples": [
            sample(0),
            sample(1, 8.0, player_half_hearts=5),
            sample(2, 0.0, room_clear=True),
        ],
        **kwargs,
    }


def write_suite(tmp_path, traces=None):
    traces = traces or [trace(), trace(policy=CONTROL)]
    attempts = []
    for index, raw in enumerate(traces):
        data = json.dumps(raw).encode()
        path = tmp_path / f"trace-{index}.json"
        path.write_bytes(data)
        attempts.append(
            {
                "policy_id": raw["policy"]["id"],
                "case_id": CASE["id"],
                "repeat": 0,
                "policy_seed": 7,
                "trace": path.name,
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    manifest = {
        "suite_id": "readiness-validation-v1",
        "code_revision": "c" * 40,
        "runtime_fingerprint": DIGEST,
        "reference": POLICY["id"],
        "repeats": 1,
        "policies": copy.deepcopy([POLICY, CONTROL]),
        "cases": copy.deepcopy([CASE]),
        "attempts": attempts,
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path, manifest


def test_complete_native_contract_reports_raw_pairs_and_no_learning_claim(tmp_path):
    path, _ = write_suite(
        tmp_path,
        [
            trace(),
            trace(
                policy=CONTROL,
                samples=[sample(0), sample(1, 9.0), sample(2, 7.0, player_dead=True)],
                stop="death",
            ),
        ],
    )
    result = compare(path)
    assert result["status"] == "matched_descriptive"
    assert result["learning_claim"] is False
    row = result["paired_deltas"][0]
    assert row["damage_dealt_delta_hp"] == -7
    assert row["damage_taken_delta_half_hearts"] == -1
    assert row["clear_delta"] == -1
    original = result["policies"][POLICY["id"]]
    assert original["verified_clears"] == original["known_outcomes"] == 1
    assert original["clear_rate_ci95"][0] < 1
    assert result["attempts"][0]["phase_seconds"] == {
        "combat": 2.0,
        "navigation": 0.0,
        "waiting": 0.0,
    }


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("source", "synthetic", "native_start_unverified"),
        ("native_start_verified", False, "native_start_unverified"),
        ("assistance", "assisted", "control_attribution"),
        ("assistance", "unknown", "control_attribution"),
        ("control", "mixed", "control_attribution"),
        ("control", "shadow", "control_attribution"),
        ("policy_unchanged", False, "policy_identity"),
        ("runtime_fingerprint", "f" * 64, "runtime"),
        ("policy_seed", 88, "case_or_seed"),
    ],
)
def test_unattributable_evidence_retained_but_not_paired(tmp_path, field, value, reason):
    path, manifest = write_suite(tmp_path, [trace(), trace(policy=CONTROL, **{field: value})])
    # The predeclared attempt seed remains 7, independently of submitted trace metadata.
    assert manifest["attempts"][1]["policy_seed"] == 7
    result = compare(path)
    assert result["status"] == "not_comparable"
    assert reason in result["attempts"][1]["issues"]
    assert len(result["attempts"]) == 2
    assert not result["paired_deltas"]


def test_case_mismatch_and_missing_cells_are_visible(tmp_path):
    different = copy.deepcopy(CASE)
    different["build"] = ["different-build"]
    path, _ = write_suite(tmp_path, [trace(case=different)])
    result = compare(path)
    assert len(result["missing"]) == 1
    assert result["policies"]["random"]["missing"] == 1
    assert result["policies"]["random"]["clear_rate_known"] is None
    assert "case_or_seed" in result["attempts"][0]["issues"]
    assert not result["paired_deltas"]


@pytest.mark.parametrize("change", ["health", "player_position", "enemy_position", "enemy_hp"])
def test_actual_start_must_match_even_when_declared_metadata_matches(tmp_path, change):
    other = trace(policy=CONTROL)
    first = other["samples"][0]
    if change == "health":
        first["player_half_hearts"] = 4
    elif change == "player_position":
        first["player_position"]["x"] = 120.0
    elif change == "enemy_position":
        first["enemies"][0]["position"]["y"] = 130.0
    else:
        first["enemies"][0]["hp"] = 20.0
    path, _ = write_suite(tmp_path, [trace(), other])
    result = compare(path)
    assert result["status"] == "not_comparable"
    assert "observed_start_mismatch" in result["attempts"][1]["issues"]
    assert not result["paired_deltas"]


def test_transient_clear_flag_does_not_verify_final_clear():
    rows = [sample(0), sample(1, room_clear=True), sample(2)]
    assert raw_metrics(Trace.model_validate(trace(samples=rows)))["outcome"] == "unknown"


def test_fault_and_censored_attempts_are_not_negative_clear_outcomes(tmp_path):
    path, _ = write_suite(
        tmp_path,
        [
            trace(stop="fault", fault="connection failed", samples=[]),
            trace(policy=CONTROL, stop="budget", samples=[sample(0), sample(4, 6.0)]),
        ],
    )
    result = compare(path)
    assert len(result["attempts"]) == 2
    assert result["policies"][POLICY["id"]]["faults"] == 1
    assert result["policies"]["random"]["unknown"] == 1
    assert result["policies"]["random"]["known_outcomes"] == 0
    assert result["policies"]["random"]["clear_fraction_all_attempts"] == 0


def test_damage_never_credits_disappearance_healing_or_new_generation():
    rows = [sample(0), sample(1, 5.0), sample(2, 9.0), sample(3, 5.0), sample(4, enemies=[])]
    metrics = raw_metrics(Trace.model_validate(trace(samples=rows, stop="budget")))
    assert metrics["damage_dealt_hp_lower_bound"] == 5
    assert metrics["outcome"] == "unknown"
    rows[2]["enemies"][0]["generation"] = 1
    rows[3]["enemies"][0]["generation"] = 2
    assert (
        raw_metrics(Trace.model_validate(trace(samples=rows, stop="budget")))[
            "damage_dealt_hp_lower_bound"
        ]
        == 5
    )


@pytest.mark.parametrize(
    "change",
    [
        {"frame": 20},
        {"session": "b" * 32},
        {"epoch": 2},
        {"room_visit": 2},
    ],
)
def test_gaps_or_identity_changes_cannot_credit_hp_loss_or_clear(change):
    raw = trace(
        samples=[sample(0), sample(1, 0.0, room_clear=True, player_half_hearts=0, **change)]
    )
    metrics = raw_metrics(Trace.model_validate(raw))
    assert metrics["damage_dealt_hp_lower_bound"] == 0
    assert metrics["damage_taken_half_hearts_lower_bound"] == 0
    assert metrics["coverage_gaps"] == 1
    assert metrics["outcome"] == "unknown"


@pytest.mark.parametrize("phase", ["inactive", "unknown"])
def test_phase_changes_do_not_invent_damage(phase):
    row = sample(1, 2.0)
    row["enemies"][0]["phase"] = phase
    assert (
        raw_metrics(Trace.model_validate(trace(samples=[sample(0), row])))[
            "damage_dealt_hp_lower_bound"
        ]
        == 0
    )


def test_empty_start_clear_overflow_and_software_stop_remain_unknown():
    for rows, stop in [
        ([sample(0, enemies=[]), sample(1, room_clear=True)], "clear"),
        ([sample(0), sample(1, room_clear=True, enemy_overflow=1)], "clear"),
        ([sample(0), sample(1, room_clear=True)], "user_stop"),
    ]:
        result = raw_metrics(Trace.model_validate(trace(samples=rows, stop=stop)))
        assert result["outcome"] == "unknown"
        assert not result["verified_clear"]


def test_player_damage_counts_raw_decreases_not_rewards_or_net_health():
    rows = [
        sample(0),
        sample(1, player_half_hearts=4),
        sample(2, player_half_hearts=6),
        sample(3, player_half_hearts=5),
    ]
    result = raw_metrics(Trace.model_validate(trace(samples=rows, stop="budget")))
    assert result["damage_taken_half_hearts_lower_bound"] == 3
    assert "reward" not in result


@pytest.mark.parametrize(
    "mutator",
    [
        lambda m: m["attempts"].append(m["attempts"][0]),
        lambda m: m["policies"].append(m["policies"][0]),
        lambda m: m["cases"].append({**m["cases"][0], "id": "other", "split": "test"}),
        lambda m: m["attempts"][0].update(repeat=3),
        lambda m: m["policies"][0].update(normalizer_sha256=None),
    ],
)
def test_invalid_manifest_refuses_before_analysis(tmp_path, mutator):
    _, manifest = write_suite(tmp_path)
    mutator(manifest)
    with pytest.raises(ValueError):
        Manifest.model_validate(manifest)


@pytest.mark.parametrize("mutation", ["hash", "escape", "oversize"])
def test_changed_escaped_and_oversize_files_refused(tmp_path, mutation):
    path, manifest = write_suite(tmp_path)
    if mutation == "hash":
        (tmp_path / "trace-0.json").write_text("{}")
    elif mutation == "escape":
        manifest["attempts"][0]["trace"] = "../outside.json"
        path.write_text(json.dumps(manifest))
    else:
        path.write_bytes(b" " * (1024 * 1024 + 1))
    with pytest.raises(ValueError):
        compare(path)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda t: t["samples"][1].update(elapsed=-1.0),
        lambda t: t["samples"][1].update(elapsed=float("nan")),
        lambda t: t["samples"][1].update(decisions=True),
        lambda t: t["samples"][1].update(decisions=100),
        lambda t: t["samples"][1].update(elapsed=11.0),
        lambda t: t["samples"][0].update(decisions=1),
        lambda t: t["samples"][1].update(reward=10000),
        lambda t: t["samples"][1]["enemies"].append(t["samples"][1]["enemies"][0]),
    ],
)
def test_invalid_raw_trace_is_not_sanitized(mutation):
    raw = trace()
    mutation(raw)
    with pytest.raises(ValueError):
        Trace.model_validate(raw)


def test_cli_is_offline_and_preserves_existing_output(tmp_path):
    path, _ = write_suite(
        tmp_path, [trace(source="synthetic"), trace(policy=CONTROL, source="synthetic")]
    )
    out = tmp_path / "report.json"
    cmd = [sys.executable, "-m", "isaac_threrisaifuture.gameplay_comparison", str(path), str(out)]
    run = subprocess.run(cmd, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    assert json.loads(out.read_text())["status"] == "not_comparable"
    before = out.read_bytes()
    assert subprocess.run(cmd, capture_output=True).returncode != 0
    assert out.read_bytes() == before
