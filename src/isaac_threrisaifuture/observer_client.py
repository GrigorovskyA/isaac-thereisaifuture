"""Loopback observation consumer: Python listens, the audited Lua peer connects."""

import math
import socket
import time
import uuid
from dataclasses import dataclass
from types import TracebackType
from typing import Self, get_args

from .entities import EntitySnapshot, NativeOracleKind
from .live_wire import LiveSnapshot
from .observation import (
    CAPABILITIES,
    MAX_MESSAGE_BYTES,
    BridgeError,
    BridgeTimeout,
    Hello,
    HelloAck,
    PeerDisconnected,
    ProtocolError,
    Snapshot,
    decode,
)

DEATH_RESTART_CAPABILITY = "death_restart_v1"
NATIVE_EPISODE_CAPABILITY = "entity_action_v1"
ORACLE_KINDS: tuple[NativeOracleKind, ...] = get_args(NativeOracleKind)


def oracle_kind_capability(kind: str) -> str:
    """Exact per-kind OracleEvent capability name; negotiation only, no producer coverage claim."""
    return f"oracle_{kind}_v1"


LIVE_LOOP_CAPABILITIES = (
    "entity_observation_v1",
    "safe_actions_v1",
    DEATH_RESTART_CAPABILITY,
    "live_loop_v1",
)


@dataclass(frozen=True)
class ObserverConfig:
    host: str = "127.0.0.1"
    port: int = 9528
    accept_timeout: float = 10.0
    handshake_timeout: float = 3.0
    message_timeout: float = 3.0
    restart_after_death: bool = False
    safe_actions: bool = False
    entity_observations: bool = False
    native_episode_steps: bool = False
    live_loop: bool = False
    native_oracle_kinds: tuple[NativeOracleKind, ...] | None = None

    def __post_init__(self) -> None:
        if type(self.live_loop) is not bool:
            raise ValueError("Live loop opt-in must be boolean")
        if self.live_loop and (
            self.safe_actions
            or self.restart_after_death
            or self.entity_observations
            or self.native_episode_steps
        ):
            raise ValueError("Live loop implies its own modes and combines with no other opt-in")
        if type(self.entity_observations) is not bool:
            raise ValueError("Entity observation opt-in must be boolean")
        if self.entity_observations and (self.safe_actions or self.restart_after_death):
            raise ValueError("Entity observation currently requires read-only mode")
        if type(self.safe_actions) is not bool:
            raise ValueError("Action opt-in must be boolean")
        if self.safe_actions and self.restart_after_death:
            raise ValueError("Action and restart modes are mutually exclusive")
        if type(self.restart_after_death) is not bool:
            raise ValueError("Restart opt-in must be boolean")
        if type(self.native_episode_steps) is not bool:
            raise ValueError("Native episode opt-in must be boolean")
        if self.native_episode_steps and (
            self.safe_actions or self.entity_observations or self.restart_after_death
        ):
            raise ValueError("Native episode mode cannot combine with other opt-in modes")
        kinds = self.native_oracle_kinds
        if kinds is not None:
            if type(kinds) is not tuple or not kinds:
                raise ValueError("Native oracle kinds must be a nonempty tuple")
            if any(type(kind) is not str or kind not in ORACLE_KINDS for kind in kinds):
                raise ValueError("Unknown native oracle kind")
            if len(set(kinds)) != len(kinds):
                raise ValueError("Duplicate native oracle kind")
            if not self.native_episode_steps:
                raise ValueError("Native oracle kinds require native episode mode")
        if self.host != "127.0.0.1":
            raise ValueError("Only IPv4 loopback 127.0.0.1 is permitted")
        if type(self.port) is not int or not 0 <= self.port <= 65535:
            raise ValueError("Port must be 0..65535 (0 selects an ephemeral test port)")
        for value in (self.accept_timeout, self.handshake_timeout, self.message_timeout):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Timeouts must be finite positive seconds")


class ObservationClient:
    """One listener, one peer; reconnection is explicit via accept()."""

    def __init__(self, config: ObserverConfig) -> None:
        self.config = config
        self._listener: socket.socket | None = None
        self._peer: socket.socket | None = None
        self._buffer = bytearray()
        self._session: str | None = None
        self._sequence = -1
        self._epoch = -1
        self._frame = -1
        self._update = -1
        self._room_visit = -1

    @property
    def address(self) -> tuple[str, int]:
        if self._listener is None:
            raise BridgeError("Listener is closed")
        host, port = self._listener.getsockname()
        return str(host), int(port)

    def __enter__(self) -> Self:
        if self._listener is not None:
            raise BridgeError("Listener already open")
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.bind((self.config.host, self.config.port))
            listener.listen(1)
        except OSError as exc:
            listener.close()
            raise BridgeError(f"Cannot bind loopback listener: {exc}") from exc
        self._listener = listener
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close_peer(self) -> None:
        if self._peer is not None:
            self._peer.close()
            self._peer = None
        self._buffer.clear()
        self._session = None
        self._sequence = self._epoch = self._frame = self._update = self._room_visit = -1

    def close(self) -> None:
        self.close_peer()
        if self._listener is not None:
            self._listener.close()
            self._listener = None

    def _read_line(self, deadline: float) -> bytes:
        assert self._peer is not None
        while True:
            newline = self._buffer.find(b"\n")
            if newline >= 0:
                if newline > MAX_MESSAGE_BYTES:
                    raise ProtocolError("Message exceeds 16384 bytes")
                raw = bytes(self._buffer[:newline])
                del self._buffer[: newline + 1]
                return raw
            if len(self._buffer) > MAX_MESSAGE_BYTES:
                raise ProtocolError("Message exceeds 16384 bytes")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeTimeout("Message deadline expired")
            self._peer.settimeout(remaining)
            try:
                chunk = self._peer.recv(min(4096, MAX_MESSAGE_BYTES + 1 - len(self._buffer)))
            except TimeoutError as exc:
                raise BridgeTimeout("Message deadline expired") from exc
            except OSError as exc:
                raise PeerDisconnected("Socket read failed") from exc
            if not chunk:
                raise PeerDisconnected("Peer closed before a complete record")
            self._buffer.extend(chunk)

    def accept(self) -> HelloAck:
        """Accept and negotiate one fresh session; close an earlier peer first."""
        self.close_peer()
        if self._listener is None:
            raise BridgeError("Use the client as a context manager")
        try:
            self._listener.settimeout(self.config.accept_timeout)
            try:
                self._peer, _ = self._listener.accept()
            except TimeoutError as exc:
                raise BridgeTimeout("No Lua peer connected before accept deadline") from exc
            self._session = uuid.uuid4().hex
            required = list(CAPABILITIES)
            if self.config.restart_after_death:
                required.append(DEATH_RESTART_CAPABILITY)
            if self.config.safe_actions:
                required.append("safe_actions_v1")
            if self.config.entity_observations:
                required.append("entity_observation_v1")
            if self.config.native_episode_steps:
                required.append(NATIVE_EPISODE_CAPABILITY)
                required.extend(map(oracle_kind_capability, self.config.native_oracle_kinds or ()))
            if self.config.live_loop:
                required.extend(LIVE_LOOP_CAPABILITIES)
            hello = Hello(session_id=self._session, required_capabilities=required)
            deadline = time.monotonic() + self.config.handshake_timeout
            self._peer.settimeout(self.config.handshake_timeout)
            self._peer.sendall(hello.model_dump_json().encode() + b"\n")
            ack = decode(self._read_line(deadline), HelloAck)
            if ack.session_id != self._session or not set(required) <= set(ack.capabilities):
                raise ProtocolError("Handshake session or capabilities do not match")
            return ack
        except BaseException as exc:
            self.close_peer()
            if isinstance(exc, TimeoutError):
                raise BridgeTimeout("Handshake send deadline expired") from exc
            if isinstance(exc, OSError):
                raise BridgeError("Accept/handshake socket failed") from exc
            raise

    def receive(self) -> Snapshot:
        """Read one validated state; failures invalidate this connection."""
        if self._peer is None or self._session is None:
            raise BridgeError("No negotiated peer")
        try:
            raw = self._read_line(time.monotonic() + self.config.message_timeout)
            if self.config.live_loop:
                snap: Snapshot = decode(raw, LiveSnapshot)
            elif self.config.entity_observations or self.config.native_episode_steps:
                snap = decode(raw, EntitySnapshot)
            else:
                snap = decode(raw, Snapshot)
            self._validate_snapshot(snap)
            return snap
        except BaseException:
            self.close_peer()
            raise

    def _validate_snapshot(self, snap: Snapshot) -> None:
        """Share ordering validation with the optional command consumer."""
        if snap.session_id != self._session or snap.sequence <= self._sequence:
            raise ProtocolError("Wrong session or duplicate/out-of-order sequence")
        if snap.game_epoch < self._epoch or snap.update_id < self._update:
            raise ProtocolError("Game epoch/update counter regressed")
        same_epoch = snap.game_epoch == self._epoch
        if same_epoch and snap.frame_id is not None and snap.frame_id < self._frame:
            raise ProtocolError("Engine frame regressed within game epoch")
        if same_epoch and snap.room is not None and snap.room.visit_id < self._room_visit:
            raise ProtocolError("Room visit regressed within game epoch")
        if not same_epoch:
            self._frame = self._room_visit = -1
        self._session = snap.session_id
        self._sequence, self._epoch, self._update = (
            snap.sequence,
            snap.game_epoch,
            snap.update_id,
        )
        if snap.frame_id is not None:
            self._frame = snap.frame_id
        if snap.room is not None:
            self._room_visit = snap.room.visit_id
