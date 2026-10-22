"""Native oracle envelopes and an O(1) deduplicating cursor. No transport, inference or Lua."""

import re
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .entities import OracleEvent
from .observation import Counter, ProtocolError, SessionId, WireModel

EventId = Annotated[int, Field(ge=1, le=2**53 - 1)]
_SESSION = re.compile(r"[0-9a-f]{32}")
_MAX = 2**53 - 1


class NativeOracleEvent(WireModel):
    """Identity-carrying wrapper; the wrapped OracleEvent stays out of every policy path."""

    type: Literal["native_oracle_event"] = "native_oracle_event"
    protocol_version: Literal[1] = 1
    session_id: SessionId
    game_epoch: Counter
    room_visit: Counter
    frame_id: Counter
    event_id: EventId
    event: OracleEvent

    @property
    def provenance(self) -> Literal["synthetic", "game_api"]:
        return self.event.provenance

    @model_validator(mode="after")
    def agrees_with_event(self) -> Self:
        e = self.event
        if e.provenance != "game_api":
            raise ProtocolError("Native oracle events must come from the game API")
        if (e.session_id, e.game_epoch, e.room_visit, e.frame_id) != (
            self.session_id,
            self.game_epoch,
            self.room_visit,
            self.frame_id,
        ):
            raise ProtocolError("Oracle event identity differs from its envelope")
        return self


def _bounded(value: object, name: str) -> int:
    if type(value) is not int or not 0 <= value <= _MAX:
        raise ProtocolError(f"{name} must be a bounded integer")
    return value


class NativeEventCursor:
    """One session and epoch; keeps only the last contiguous event ID."""

    __slots__ = ("_epoch", "_last_id", "_session")

    def __init__(self, session_id: str, game_epoch: int) -> None:
        if not isinstance(session_id, str) or not _SESSION.fullmatch(session_id):
            raise ProtocolError("Invalid session identity")
        self._session = session_id
        self._epoch = _bounded(game_epoch, "game_epoch")
        self._last_id = 0

    @property
    def session_id(self) -> str:
        return self._session

    @property
    def game_epoch(self) -> int:
        return self._epoch

    @property
    def last_id(self) -> int:
        return self._last_id

    def take(
        self, envelope: NativeOracleEvent, start_frame: int, end_frame: int
    ) -> NativeOracleEvent | None:
        """Return the envelope for a new in-order event, None for an already consumed ID.

        Any fault leaves the cursor unchanged. This deduplicates; it never infers an outcome.
        """
        if not isinstance(envelope, NativeOracleEvent):
            raise ProtocolError("Expected a native oracle envelope")
        if envelope.session_id != self._session or envelope.game_epoch != self._epoch:
            raise ProtocolError("Event session or epoch differs from the cursor")
        start = _bounded(start_frame, "start_frame")
        end = _bounded(end_frame, "end_frame")
        if start >= end:
            raise ProtocolError("Step interval must satisfy start_frame < end_frame")
        if envelope.event_id <= self._last_id:
            return None
        if envelope.event_id != self._last_id + 1:
            raise ProtocolError("Native event ID gap")
        if not start < envelope.frame_id <= end:
            raise ProtocolError("Event frame outside the step interval")
        self._last_id = envelope.event_id
        return envelope
