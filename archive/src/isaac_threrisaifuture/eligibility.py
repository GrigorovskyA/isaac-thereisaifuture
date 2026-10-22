"""Fail-closed save-slot and achievement eligibility gate.

``EligibilityEvidence`` is the contract the bridge must fill. The real bridge does not yet
expose the slot or achievement fields (blocked), so this module is an offline contract only.
``None`` always means "unknown" and is denied.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

REQUIRED_SLOT = 2
SCHEMA_VERSION = 1


class EligibilityError(RuntimeError):
    """Raised when autonomous progression is attempted without eligibility."""

    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__("progression denied: " + ", ".join(reasons))
        self.reasons = reasons


@dataclass(frozen=True)
class EligibilityEvidence:
    """Facts observed through the bridge. ``None`` means unknown, never assumed good."""

    slot_id: int | None = None
    achievements_enabled: bool | None = None
    console_or_debug_used: bool | None = None
    save_edited_or_imported: bool | None = None
    # Ids of active mods known to disable achievements; None = mod list not observed.
    achievement_blocking_mods: tuple[str, ...] | None = None
    game_version: str | None = None


@dataclass(frozen=True)
class EligibilityDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate(evidence: EligibilityEvidence) -> EligibilityDecision:
    reasons: list[str] = []
    if evidence.slot_id is None:
        reasons.append("slot_unknown")
    elif evidence.slot_id != REQUIRED_SLOT:
        reasons.append("slot_wrong")
    if evidence.achievements_enabled is None:
        reasons.append("achievements_unknown")
    elif not evidence.achievements_enabled:
        reasons.append("achievements_disabled")
    if evidence.console_or_debug_used is None:
        reasons.append("console_debug_unknown")
    elif evidence.console_or_debug_used:
        reasons.append("console_debug_used")
    if evidence.save_edited_or_imported is None:
        reasons.append("save_integrity_unknown")
    elif evidence.save_edited_or_imported:
        reasons.append("save_edited_or_imported")
    if evidence.achievement_blocking_mods is None:
        reasons.append("mods_unknown")
    elif evidence.achievement_blocking_mods:
        reasons.append("mods_block_achievements")
    if not evidence.game_version:
        reasons.append("game_version_unknown")
    return EligibilityDecision(allowed=not reasons, reasons=tuple(reasons))


def require_eligible(evidence: EligibilityEvidence) -> EligibilityDecision:
    """Guard to call before any autonomous progression; raises when denied."""
    decision = evaluate(evidence)
    if not decision.allowed:
        raise EligibilityError(decision.reasons)
    return decision


def audit_record(evidence: EligibilityEvidence, decision: EligibilityDecision) -> dict[str, Any]:
    """JSON-serializable record; contains only bridge-observed values, no paths or user names."""
    return {
        "schema_version": SCHEMA_VERSION,
        "allowed": decision.allowed,
        "reasons": list(decision.reasons),
        "evidence": {
            "slot_id": evidence.slot_id,
            "achievements_enabled": evidence.achievements_enabled,
            "console_or_debug_used": evidence.console_or_debug_used,
            "save_edited_or_imported": evidence.save_edited_or_imported,
            "achievement_blocking_mods": (
                None
                if evidence.achievement_blocking_mods is None
                else list(evidence.achievement_blocking_mods)
            ),
            "game_version": evidence.game_version,
        },
    }
