"""Offline producer delivery bookkeeping; no engine callbacks, transport or authority."""

from dataclasses import dataclass
from typing import NoReturn

from .entities import EntityFrame, OracleEvent
from .native_events import NativeOracleEvent
from .observation import MAX_MESSAGE_BYTES, ProtocolError

MAX_PENDING_EVENTS = 32
MAX_PENDING_BYTES = 32768
_MAX_COUNTER = 2**53 - 1


def _integer(value: object, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ProtocolError(f"{name} must be an integer in {minimum}..{maximum}")
    return value


@dataclass(frozen=True)
class NativeEventBatch:
    """Staged interval; sealing asserts callback completeness, it does not prove it."""

    start_frame: int
    end_frame: int
    last_event_id: int
    events: tuple[NativeOracleEvent, ...]
    records: tuple[bytes, ...]


class NativeEventOutbox:
    """Retain events until delivery commit; any protocol fault closes permanently.

    Single caller only. A future sender must close on send failure and acknowledge
    only after flushing completion. This class cannot release any game inputs.
    """

    def __init__(
        self,
        baseline: EntityFrame,
        *,
        max_events: int = MAX_PENDING_EVENTS,
        max_bytes: int = MAX_PENDING_BYTES,
    ) -> None:
        if not isinstance(baseline, EntityFrame):
            raise ProtocolError("A native baseline is required")
        baseline = EntityFrame.model_validate(baseline.model_dump())
        if baseline.provenance != "game_api":
            raise ProtocolError("Baseline must come from the game API")
        self._limit = _integer(max_events, "max_events", 1, MAX_PENDING_EVENTS)
        self._byte_limit = _integer(max_bytes, "max_bytes", 1, MAX_PENDING_BYTES)
        self._identity = (baseline.session_id, baseline.game_epoch, baseline.room_visit)
        self._frame = self._last_frame = baseline.frame_id
        self._assigned = self._committed = 0
        self._pending: list[tuple[NativeOracleEvent, bytes]] = []
        self._bytes = 0
        self._batch: NativeEventBatch | None = None
        self._closed = False

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def pending_bytes(self) -> int:
        return self._bytes

    def close(self) -> None:
        """Discard undelivered events; a new session needs a new explicit baseline."""
        self._closed = True
        self._pending.clear()
        self._bytes = 0
        self._batch = None

    def _fault(self, message: str) -> NoReturn:
        self.close()
        raise ProtocolError(message)

    def _require_open(self) -> None:
        if self._closed:
            raise ProtocolError("Event outbox is closed")

    def append(self, event: OracleEvent) -> NativeOracleEvent:
        """Assign one event ID, retaining the serialized record until commit."""
        self._require_open()
        try:
            return self._append(event)
        except BaseException:
            self.close()
            raise

    def _append(self, event: OracleEvent) -> NativeOracleEvent:
        if not isinstance(event, OracleEvent):
            self._fault("Expected a validated oracle event")
        event = OracleEvent.model_validate(event.model_dump())
        if (
            event.provenance != "game_api"
            or (
                event.session_id,
                event.game_epoch,
                event.room_visit,
            )
            != self._identity
        ):
            self._fault("Event differs from the native baseline identity")
        boundary = self._batch.end_frame if self._batch is not None else self._frame
        if event.frame_id <= boundary or event.frame_id < self._last_frame:
            self._fault("Late or regressing oracle event frame")
        if self._assigned == _MAX_COUNTER:
            self._fault("Native event ID exhausted")
        envelope = NativeOracleEvent(
            session_id=event.session_id,
            game_epoch=event.game_epoch,
            room_visit=event.room_visit,
            frame_id=event.frame_id,
            event_id=self._assigned + 1,
            event=event,
        )
        raw = envelope.model_dump_json().encode("utf-8")
        if (
            len(raw) > MAX_MESSAGE_BYTES
            or len(self._pending) >= self._limit
            or self._bytes + len(raw) > self._byte_limit
        ):
            self._fault("Pending oracle event budget exceeded")
        self._pending.append((envelope, raw))
        self._bytes += len(raw)
        self._assigned = envelope.event_id
        self._last_frame = event.frame_id
        return envelope

    def seal(self, end_frame: int) -> NativeEventBatch:
        """Stage the prefix in (committed frame, end]; do not dequeue on staging."""
        self._require_open()
        try:
            end = _integer(end_frame, "end_frame", 0, _MAX_COUNTER)
            if self._batch is not None or end <= self._frame:
                self._fault("Only one increasing interval may be staged")
            prefix = tuple(pair for pair in self._pending if pair[0].frame_id <= end)
            events = tuple(pair[0] for pair in prefix)
            self._batch = NativeEventBatch(
                self._frame,
                end,
                events[-1].event_id if events else self._committed,
                events,
                tuple(pair[1] for pair in prefix),
            )
            return self._batch
        except BaseException:
            self.close()
            raise

    def acknowledge(self, batch: NativeEventBatch) -> None:
        """Commit exactly the staged object after its completion has been flushed."""
        self._require_open()
        if self._batch is None or batch is not self._batch:
            self._fault("Acknowledgement must match the staged batch object")
        self._pending = self._pending[len(batch.events) :]
        self._bytes -= sum(map(len, batch.records))
        self._frame = batch.end_frame
        self._committed = batch.last_event_id
        self._batch = None
