"""Opt-in endpoint evidence and conservative combat stagnation detection.

Oracle records are diagnostic-only. Neither this module's state nor its records
are policy inputs, rewards, terminal outcomes or proof of zero actual damage.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from .encoding import encode
from .live import EventDeriver, LiveBudgetExpired, LiveSnapshot
from .observation import ProtocolError

MAX_TRACE_BYTES = 256 * 1024 * 1024
MAX_PROGRESS_UPDATES = 108_000


class CombatDiagnosticStop(LiveBudgetExpired):
    """An explicit diagnostic limit stopped collection before the next action."""


def validate_limits(trace_bytes: int, progress_updates: int | None) -> None:
    if type(trace_bytes) is not int or not 0 <= trace_bytes <= MAX_TRACE_BYTES:
        raise ValueError("Combat trace bytes must be an integer in 0..268435456 (0 disables)")
    if progress_updates is not None and (
        type(progress_updates) is not int or not 1 <= progress_updates <= MAX_PROGRESS_UPDATES
    ):
        raise ValueError("Combat progress window must be an integer in 1..108000 game updates")


def identity(snap: LiveSnapshot) -> tuple[str, int, int]:
    frame = snap.entity_frame
    if frame is None:
        raise ProtocolError("Combat diagnostics need an available entity frame")
    return frame.session_id, frame.game_epoch, frame.room_visit


def policy_state(snap: LiveSnapshot, observation: Any) -> dict[str, Any]:
    frame = snap.entity_frame
    if frame is None:
        raise ProtocolError("Combat diagnostics cannot bind an unavailable policy frame")
    encoded = encode(frame)
    from .policy_geometry import encode_geometry

    vector = (
        encode_geometry(frame, snap.combat_geometry)
        if snap.combat_geometry is not None
        else encoded.vector
    )
    if not np.array_equal(vector, observation):
        raise ProtocolError("Combat diagnostic vector does not match its raw entity frame")
    return {
        "session_id": frame.session_id,
        "game_epoch": frame.game_epoch,
        "room_visit": frame.room_visit,
        "frame_id": frame.frame_id,
        "observation_schema": 2 if snap.combat_geometry is not None else 1,
        "observation_stage": "encoder_before_vecnormalize",
        "observation": vector.tolist(),
        "overflow": encoded.overflow,
        "clipped_values": encoded.clipped_values,
    }


class CombatTrace:
    """Two append-only files with a shared byte budget; no held file handles."""

    def __init__(self, directory: Path, byte_limit: int) -> None:
        validate_limits(byte_limit, None)
        if byte_limit == 0:
            raise ValueError("A combat trace requires a positive byte limit")
        directory.mkdir(parents=True, exist_ok=True)
        self.policy_path = directory / "policy.jsonl"
        self.oracle_path = directory / "oracle.jsonl"
        # Refuse reusing either existing stream before creating anything.
        if self.policy_path.exists() or self.oracle_path.exists():
            raise FileExistsError("Combat diagnostic streams already exist")
        self.policy_path.touch(exist_ok=False)
        self.oracle_path.touch(exist_ok=False)
        self.byte_limit, self.bytes_written, self.records = byte_limit, 0, 0

    def transition(
        self,
        before: LiveSnapshot,
        before_observation: Any,
        after: LiveSnapshot,
        after_observation: Any,
        action: Any,
        *,
        terminated: bool,
        truncated: bool,
        action_withheld: str | None,
        fault: str | None = None,
    ) -> bool:
        record_id = self.records + 1
        policy = {
            "version": 1,
            "record_id": record_id,
            "before": policy_state(before, before_observation),
            "after": policy_state(after, after_observation),
            "selected_action": np.asarray(action).tolist(),
            "action_withheld": action_withheld,
            "terminated": terminated,
            "truncated": truncated,
            "fault": fault,
        }
        oracle = {
            "version": 1,
            "record_id": record_id,
            "before": before.model_dump(mode="json"),
            "after": after.model_dump(mode="json"),
            "weapon_range": None,
            "weapon_range_status": "not_exported",
            "coverage": "combat_endpoints_only_not_command_acknowledgements",
        }
        blocks = [
            (json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
            for row in (policy, oracle)
        ]
        size = sum(map(len, blocks))
        if self.bytes_written + size > self.byte_limit:
            return False
        for path, block in zip((self.policy_path, self.oracle_path), blocks, strict=True):
            with path.open("ab") as stream:
                stream.write(block)
        self.bytes_written += size
        self.records = record_id
        return True


@dataclass
class CombatProgressMonitor:
    """Count observed action spans, retaining conservative floors across resets."""

    window_updates: int
    updates_without_progress: int = 0
    _visit: tuple[str, int, int] | None = None
    _deriver: EventDeriver = field(default_factory=EventDeriver)

    def __post_init__(self) -> None:
        validate_limits(0, self.window_updates)

    def begin(self, snap: LiveSnapshot) -> None:
        visit = identity(snap)
        if visit != self._visit:
            self.updates_without_progress = 0
            self._visit = visit
        self._deriver.begin(snap)

    def transition(self, before: LiveSnapshot, after: LiveSnapshot, *, eligible: bool) -> bool:
        visit = identity(after)
        if visit != self._visit or identity(before) != visit:
            self.begin(after)
            return False
        assert before.frame_id is not None and after.frame_id is not None
        if after.frame_id < before.frame_id:
            raise ProtocolError("Combat diagnostic frames regressed within one visit")
        events = self._deriver.update(after)
        if any(event.kind in ("enemy_damaged", "room_cleared") for event in events):
            self.updates_without_progress = 0
        elif eligible:
            self.updates_without_progress += after.frame_id - before.frame_id
        return self.updates_without_progress >= self.window_updates
