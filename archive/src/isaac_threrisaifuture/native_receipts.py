"""Offline assembly of one native step receipt from ordered wire records.

No sockets, clock or sender. A matching receipt is not proof of physical input.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass

from .actions import CommandAck
from .entities import EntityFrame
from .native_events import NativeEventCursor, NativeOracleEvent
from .native_protocol import (
    StepCommand,
    StepCompletion,
    validate_completion,
    validate_event_barrier,
)
from .observation import MAX_MESSAGE_BYTES, ProtocolError, decode
from .observer_client import ORACLE_KINDS

MAX_EVENT_RECORDS = 32
MAX_RECORDS = 34
MAX_TOTAL_BYTES = 65536
_TYPES = ("command_ack", "native_oracle_event", "step_completion")


@dataclass(frozen=True)
class NativeStepReceipt:
    """A completed step: the acknowledgement, completion and new (deduplicated) events."""

    ack: CommandAck
    completion: StepCompletion
    events: tuple[NativeOracleEvent, ...]


def _record_type(raw: bytes) -> str:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ProtocolError("Record is not valid UTF-8 JSON") from exc
    kind = value.get("type") if isinstance(value, dict) else None
    if kind not in _TYPES:
        raise ProtocolError("Unexpected record type")
    return str(kind)


class NativeReceiptAssembler:
    """Consumes one record per feed(); any fault invalidates the assembler for good.

    oracle_kinds is the exact set of OracleEvent kinds requested for this connection. An
    event of any other kind faults the receipt; the default accepts no native oracle event.
    """

    def __init__(
        self,
        command: StepCommand,
        baseline: EntityFrame,
        cursor: NativeEventCursor,
        *,
        oracle_kinds: tuple[str, ...] | frozenset[str] = (),
        before_commit: Callable[[], None] | None = None,
    ) -> None:
        if not isinstance(command, StepCommand) or not isinstance(baseline, EntityFrame):
            raise ProtocolError("Command and baseline must be validated models")
        if not isinstance(cursor, NativeEventCursor):
            raise ProtocolError("A native event cursor is required")
        if not isinstance(oracle_kinds, (tuple, frozenset)) or any(
            type(kind) is not str or kind not in ORACLE_KINDS for kind in oracle_kinds
        ):
            raise ProtocolError("Oracle kinds must be a tuple or frozenset of known kind names")
        if baseline.provenance != "game_api" or (
            baseline.session_id,
            baseline.game_epoch,
            baseline.room_visit,
            baseline.frame_id,
        ) != (command.session_id, command.game_epoch, command.room_visit, command.frame_id):
            raise ProtocolError("Baseline does not match the command")
        if (cursor.session_id, cursor.game_epoch) != (command.session_id, command.game_epoch):
            raise ProtocolError("Cursor does not match the command session/epoch")
        self._command = command
        self._baseline = baseline.frame_id
        self._cursor = cursor
        self._captured = cursor.last_id
        self._kinds = frozenset(oracle_kinds)
        self._before_commit = before_commit
        self._ack: CommandAck | None = None
        self._pending: list[NativeOracleEvent] = []
        self._records = self._event_records = self._bytes = 0
        self._state = "open"

    def feed(self, raw: bytes) -> NativeStepReceipt | None:
        """Take one delimiter-free record; return the receipt only on a completed step."""
        if self._state != "open":
            raise ProtocolError("Assembler is finished or failed")
        try:
            return self._feed(raw)
        except BaseException:
            self._state = "failed"
            self._pending.clear()
            raise

    def _feed(self, raw: bytes) -> NativeStepReceipt | None:
        if not isinstance(raw, bytes):
            raise ProtocolError("Record must be bytes")
        if len(raw) > MAX_MESSAGE_BYTES:
            raise ProtocolError("Record exceeds the per-record limit")
        self._records += 1
        self._bytes += len(raw)
        if self._records > MAX_RECORDS or self._bytes > MAX_TOTAL_BYTES:
            raise ProtocolError("Receipt exceeds the record or byte budget")
        if b"\n" in raw or b"\r" in raw:
            raise ProtocolError("Record must not contain line delimiters")
        kind = _record_type(raw)
        if kind == "command_ack":
            self._take_ack(decode(raw, CommandAck))
        elif kind == "native_oracle_event":
            self._take_event(raw)
        else:
            return self._finish(decode(raw, StepCompletion))
        return None

    def _take_ack(self, ack: CommandAck) -> None:
        cmd = self._command
        if self._ack is not None:
            raise ProtocolError("Second acknowledgement")
        if ack.kind != "action" or (
            ack.session_id,
            ack.sequence,
            ack.game_epoch,
            ack.room_visit,
        ) != (cmd.session_id, cmd.sequence, cmd.game_epoch, cmd.room_visit):
            raise ProtocolError("Acknowledgement identity mismatch")
        if not cmd.frame_id <= ack.frame_id <= cmd.frame_id + 15:
            raise ProtocolError("Acknowledgement outside the freshness window")
        self._ack = ack

    def _take_event(self, raw: bytes) -> None:
        if self._ack is None:
            raise ProtocolError("Event before acknowledgement")
        self._event_records += 1  # duplicates count against the budget
        if self._event_records > MAX_EVENT_RECORDS:
            raise ProtocolError("Too many event records")
        event = decode(raw, NativeOracleEvent)
        self._check_context(event)
        if event.event.kind not in self._kinds:  # replays count: every record must be requested
            raise ProtocolError("Native oracle event kind was not requested")
        self._pending.append(event)

    def _check_context(self, event: NativeOracleEvent) -> None:
        cmd = self._command
        if (event.session_id, event.game_epoch, event.room_visit) != (
            cmd.session_id,
            cmd.game_epoch,
            cmd.room_visit,
        ):
            raise ProtocolError("Event context differs from the command")

    def _finish(self, result: StepCompletion) -> NativeStepReceipt:
        if self._ack is None:
            raise ProtocolError("Completion before acknowledgement")
        validate_completion(self._command, self._ack, result)
        if result.status != "completed":
            raise ProtocolError("Only a completed step can yield a receipt")
        if self._cursor.last_id != self._captured:
            raise ProtocolError("Event cursor changed during the transaction")
        start, end = self._baseline, result.frame.frame_id
        if start >= end:
            raise ProtocolError("Step interval must satisfy baseline < completion frame")
        last = self._captured
        fresh: list[NativeOracleEvent] = []
        for event in self._pending:  # validate everything before touching the shared cursor
            if event.event_id <= last:
                continue
            if event.event_id != last + 1:
                raise ProtocolError("Native event ID gap")
            if not start < event.frame_id <= end:
                raise ProtocolError("Event frame outside the step interval")
            last = event.event_id
            fresh.append(event)
        validate_event_barrier(result, last)
        if self._before_commit is not None:  # caller-owned guard (e.g. a deadline), no clock here
            self._before_commit()
            if self._cursor.last_id != self._captured:
                raise ProtocolError("Event cursor changed during the transaction")
        for event in fresh:
            if self._cursor.take(event, start, end) is None:
                raise ProtocolError("Event unexpectedly deduplicated")
        receipt = NativeStepReceipt(self._ack, result, tuple(fresh))
        self._state = "done"
        self._pending.clear()
        return receipt


__all__ = ["NativeReceiptAssembler", "NativeStepReceipt"]
