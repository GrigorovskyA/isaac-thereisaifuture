"""Offline wire models for a native step receipt. No sockets, threads or game calls."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .actions import Command, CommandAck, Direction
from .entities import EntityFrame
from .observation import Counter, ProtocolError, SessionId, WireModel

Status = Literal["completed", "expired", "cancelled"]
Reason = Literal[
    "interval_elapsed", "wall_deadline", "pause", "transition", "input_fault", "explicit_release"
]
_CANCEL_REASONS = {"pause", "transition", "input_fault", "explicit_release"}


class StepCommand(WireModel):
    """Same canonical field order as Command, but a distinct type so a legacy peer rejects it."""

    type: Literal["step_command"] = "step_command"
    protocol_version: Literal[1] = 1
    session_id: SessionId
    sequence: Counter
    game_epoch: Counter
    room_visit: Counter
    frame_id: Counter
    kind: Literal["action"] = "action"
    move: Direction = "none"
    shoot: Direction = "none"
    frames: Annotated[int, Field(ge=1, le=15)]

    @model_validator(mode="after")
    def legacy_payload(self) -> Self:
        """Delegate payload semantics to Command so the two cannot drift apart."""
        Command(**{**self.model_dump(), "type": "command"})
        return self

    def wire_bytes(self) -> bytes:
        return self.model_dump_json().encode() + b"\n"


class StepCompletion(WireModel):
    """A receipt for one step. Status and reason are not physical proof of input application."""

    type: Literal["step_completion"] = "step_completion"
    protocol_version: Literal[1] = 1
    session_id: SessionId
    sequence: Annotated[int, Field(ge=1, le=2**53 - 1)]
    game_epoch: Counter
    room_visit: Counter
    accepted_frame: Counter
    requested_updates: Annotated[int, Field(ge=1, le=15)]
    elapsed_updates: Counter
    status: Status
    reason: Reason
    frame: EntityFrame
    last_event_id: Counter

    @model_validator(mode="after")
    def coherent(self) -> Self:
        f = self.frame
        if f.provenance != "game_api":
            raise ProtocolError("Completion frame must come from the game API")
        if (f.session_id, f.game_epoch, f.room_visit) != (
            self.session_id,
            self.game_epoch,
            self.room_visit,
        ):
            raise ProtocolError("Completion frame identity mismatch")
        if f.frame_id < self.accepted_frame:
            raise ProtocolError("Completion frame precedes acceptance")
        if self.elapsed_updates != f.frame_id - self.accepted_frame:
            raise ProtocolError("Elapsed updates do not match the frame delta")
        if self.status == "completed":
            full = self.elapsed_updates == self.requested_updates
            ok = self.reason == "interval_elapsed" and full
        elif self.status == "expired":
            ok = self.reason == "wall_deadline"
        else:
            ok = self.reason in _CANCEL_REASONS
        if not ok:
            raise ProtocolError("Status, reason and elapsed updates are inconsistent")
        return self


def validate_completion(command: StepCommand, ack: CommandAck, result: StepCompletion) -> None:
    """Check that three messages describe one coherent step; never proves engine application."""
    if ack.kind != "action" or command.kind != "action":
        raise ProtocolError("Step receipts apply to action commands only")
    for message in (ack, result):
        if (message.session_id, message.sequence, message.game_epoch, message.room_visit) != (
            command.session_id,
            command.sequence,
            command.game_epoch,
            command.room_visit,
        ):
            raise ProtocolError("Step message identity mismatch")
    if result.accepted_frame != ack.frame_id:
        raise ProtocolError("Accepted frame does not match the acknowledgement")
    if result.requested_updates != command.frames:
        raise ProtocolError("Requested updates do not match the command")
    if not command.frame_id <= ack.frame_id <= command.frame_id + 15:
        raise ProtocolError("Acknowledgement outside the freshness window")


def validate_event_barrier(result: StepCompletion, last_event_id: int) -> None:
    """Compare a caller's cursor.last_id with the receipt; binds no session or cursor itself."""
    if type(last_event_id) is not int or not 0 <= last_event_id <= 2**53 - 1:
        raise ProtocolError("Observed event counter must be an integer in 0..2**53-1")
    if last_event_id != result.last_event_id:
        raise ProtocolError("Observed events do not match the completion watermark")


__all__ = ["StepCommand", "StepCompletion", "validate_completion", "validate_event_barrier"]
