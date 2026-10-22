"""Optional native action contract; no game launch, reset or background sender."""

import json
import socket
import time
from dataclasses import replace
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .live_wire import CommandKind
from .observation import (
    BridgeError,
    BridgeTimeout,
    Counter,
    HelloAck,
    PeerDisconnected,
    ProtocolError,
    SessionId,
    Snapshot,
    WireModel,
    decode,
)
from .observer_client import ObservationClient, ObserverConfig

Direction = Literal["none", "left", "right", "up", "down"]
Use = Literal["none", "bomb", "active", "pillcard"]


class ActionApproval(WireModel):
    """References to reviewed evidence, never automatic slot/isolation detection."""

    profile_id: Annotated[str, Field(min_length=1, max_length=128, pattern=r"\S")]
    profile_mode: Literal["isolated", "ordinary_profile_exception"]
    expires_at: Annotated[int, Field(ge=1)]
    profile_evidence: Annotated[str, Field(min_length=1, max_length=128, pattern=r"\S")]
    slot_evidence: Annotated[str, Field(min_length=1, max_length=128, pattern=r"\S")]
    runtime_authorization: Annotated[str, Field(min_length=1, max_length=128, pattern=r"\S")]
    slot: Annotated[int, Field(ge=2, le=2)]
    game_epoch: Counter


class Command(WireModel):
    type: Literal["command"] = "command"
    protocol_version: Literal[1] = 1
    session_id: SessionId
    sequence: Counter
    game_epoch: Counter
    room_visit: Counter
    frame_id: Counter
    kind: CommandKind
    move: Direction = "none"
    shoot: Direction = "none"
    use: Use = "none"
    frames: Annotated[int, Field(ge=0, le=15)] = 0

    @model_validator(mode="after")
    def valid_payload(self) -> Self:
        """Reject semantic inconsistencies at both encode and decode boundaries."""
        if self.sequence < 1:
            raise ProtocolError("Command sequence must start at one")
        if self.kind == "action":
            if self.frames < 1:
                raise ProtocolError("Action needs 1..15 frames")
        elif self.frames != 0 or self.move != "none" or self.shoot != "none" or self.use != "none":
            raise ProtocolError("Heartbeat/release/restart must carry no action")
        return self

    def wire_bytes(self) -> bytes:
        """Lua admits this exact canonical field order, with optional whitespace."""
        return self.model_dump_json().encode() + b"\n"


class CommandAck(WireModel):
    type: Literal["command_ack"]
    protocol_version: Literal[1]
    session_id: SessionId
    sequence: Counter
    game_epoch: Counter
    room_visit: Counter
    frame_id: Counter
    kind: CommandKind
    status: Literal["accepted"]


class ActionClient(ObservationClient):
    """Attach only, one transaction at a time. Explicit caller-driven heartbeat.

    Closing relies on Lua's disconnect/deadline cleanup. Acknowledgements prove
    command acceptance only. Actual position/projectile effects need game evidence.
    """

    def __init__(self, config: ObserverConfig, approval: ActionApproval) -> None:
        if config.restart_after_death:
            raise ValueError("Action and restart modes are mutually exclusive")
        super().__init__(replace(config, safe_actions=True))
        self.approval = approval
        self._command_sequence = 0
        self._latest: Snapshot | None = None

    def close_peer(self) -> None:
        super().close_peer()
        self._command_sequence = 0
        self._latest = None

    def accept(self) -> HelloAck:
        if self.approval.expires_at <= time.time():
            self.close_peer()
            raise ProtocolError("Local action approval expired")
        ack = super().accept()
        self._command_sequence = 0
        return ack

    def _validate_snapshot(self, snap: Snapshot) -> None:
        super()._validate_snapshot(snap)
        if snap.game_epoch != self.approval.game_epoch:
            raise ProtocolError("Action approval does not cover this game epoch")
        self._latest = snap

    def command(
        self,
        kind: CommandKind,
        *,
        move: Direction = "none",
        shoot: Direction = "none",
        use: Use = "none",
        frames: int = 0,
    ) -> CommandAck:
        """Send once and await a matching ack; errors always invalidate the peer."""
        try:
            if self.approval.expires_at <= time.time():
                raise ProtocolError("Local action approval expired")
            snap = self._latest
            if self._peer is None or self._session is None or snap is None:
                raise BridgeError("Negotiate and receive a fresh action snapshot first")
            if snap.status != "active" or snap.frame_id is None or snap.room is None:
                raise ProtocolError("Actions need an active current snapshot")
            self._command_sequence += 1
            command = Command(
                session_id=self._session,
                sequence=self._command_sequence,
                game_epoch=snap.game_epoch,
                room_visit=snap.room.visit_id,
                frame_id=snap.frame_id,
                kind=kind,
                move=move,
                shoot=shoot,
                use=use,
                frames=frames,
            )
            deadline = time.monotonic() + min(self.config.message_timeout, 0.5)
            self._peer.settimeout(max(0.001, deadline - time.monotonic()))
            self._peer.sendall(command.wire_bytes())
            while True:
                raw = self._read_line(deadline)
                try:
                    is_snapshot = json.loads(raw).get("type") == "snapshot"
                except (ValueError, AttributeError, UnicodeError, RecursionError) as exc:
                    raise ProtocolError("Invalid action response") from exc
                if is_snapshot:
                    self._validate_snapshot(decode(raw, Snapshot))
                    continue
                ack = decode(raw, CommandAck)
                if (
                    ack.session_id != command.session_id
                    or ack.sequence != command.sequence
                    or ack.game_epoch != command.game_epoch
                    or ack.room_visit != command.room_visit
                    or ack.kind != command.kind
                    or not command.frame_id <= ack.frame_id <= command.frame_id + 15
                ):
                    raise ProtocolError("Command acknowledgement identity mismatch")
                return ack
        except BaseException as exc:
            self.close_peer()
            if isinstance(exc, (TimeoutError, socket.timeout)):
                raise BridgeTimeout("Command deadline expired") from exc
            if isinstance(exc, OSError):
                raise PeerDisconnected("Command socket failed") from exc
            raise
