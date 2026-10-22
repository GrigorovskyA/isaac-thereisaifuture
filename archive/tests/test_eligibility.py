import json
from dataclasses import replace

import pytest

from isaac_threrisaifuture.eligibility import (
    EligibilityError,
    EligibilityEvidence,
    audit_record,
    evaluate,
    require_eligible,
)

GOOD = EligibilityEvidence(
    slot_id=2,
    achievements_enabled=True,
    console_or_debug_used=False,
    save_edited_or_imported=False,
    achievement_blocking_mods=(),
    game_version="synthetic-1",
)


def test_all_good_is_allowed() -> None:
    decision = require_eligible(GOOD)
    assert decision.allowed and decision.reasons == ()


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"slot_id": 1}, "slot_wrong"),
        ({"achievements_enabled": False}, "achievements_disabled"),
        ({"console_or_debug_used": True}, "console_debug_used"),
        ({"save_edited_or_imported": True}, "save_edited_or_imported"),
        ({"achievement_blocking_mods": ("some_mod",)}, "mods_block_achievements"),
        ({"game_version": ""}, "game_version_unknown"),
    ],
)
def test_each_denial_reason(change: dict[str, object], reason: str) -> None:
    decision = evaluate(replace(GOOD, **change))
    assert not decision.allowed and decision.reasons == (reason,)
    with pytest.raises(EligibilityError) as err:
        require_eligible(replace(GOOD, **change))
    assert err.value.reasons == (reason,)


@pytest.mark.parametrize(
    ("field", "reason"),
    [
        ("slot_id", "slot_unknown"),
        ("achievements_enabled", "achievements_unknown"),
        ("console_or_debug_used", "console_debug_unknown"),
        ("save_edited_or_imported", "save_integrity_unknown"),
        ("achievement_blocking_mods", "mods_unknown"),
        ("game_version", "game_version_unknown"),
    ],
)
def test_unknown_is_denied(field: str, reason: str) -> None:
    decision = evaluate(replace(GOOD, **{field: None}))
    assert decision.reasons == (reason,)


def test_empty_evidence_denied_with_all_reasons() -> None:
    assert len(evaluate(EligibilityEvidence()).reasons) == 6


def test_audit_record_is_json_serializable() -> None:
    record = audit_record(GOOD, evaluate(GOOD))
    assert json.loads(json.dumps(record))["evidence"]["slot_id"] == 2
    denied = audit_record(EligibilityEvidence(), evaluate(EligibilityEvidence()))
    assert json.loads(json.dumps(denied))["allowed"] is False
