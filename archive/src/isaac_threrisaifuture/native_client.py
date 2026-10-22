"""Dedicated native transport slice: bounded active-snapshot waiting; sends no command."""

import time
from typing import NoReturn

from .entities import EntityFrame, EntitySnapshot
from .episodes import EpisodeFault
from .native_events import NativeEventCursor
from .native_protocol import StepCommand
from .native_receipts import NativeReceiptAssembler, NativeStepReceipt
from .observation import BridgeError, BridgeTimeout, decode
from .observer_client import ObservationClient, ObserverConfig


class UnsupportedNativeOperation(EpisodeFault):
    """Start/reset/step need real step transport and authority that do not exist yet."""


class NativeStepClient(ObservationClient):
    """Future native transaction transport; not a GameBackend and not physical step execution."""

    def __init__(self, config: ObserverConfig) -> None:
        if not config.native_episode_steps:
            raise ValueError("NativeStepClient requires native_episode_steps=True")
        super().__init__(config)
        self._active: tuple[int, int, int] | None = None  # epoch, room visit, frame
        self._receipts = 0  # last successful receipt sequence in this connection

    def close_peer(self) -> None:
        super().close_peer()
        self._active = None
        self._receipts = 0

    def release(self) -> None:
        """Close the peer idempotently; no neutral acknowledgement is synthesized."""
        self.close_peer()

    def receive_active(self) -> EntitySnapshot:
        """Return the next active snapshot within one total message_timeout deadline."""
        if self._peer is None or self._session is None:
            raise BridgeError("No negotiated peer")
        deadline = time.monotonic() + self.config.message_timeout
        try:
            while True:
                if time.monotonic() >= deadline:
                    raise BridgeTimeout("Active snapshot deadline expired")
                snap = decode(self._read_line(deadline), EntitySnapshot)
                self._validate_snapshot(snap)
                if snap.status != "active":
                    continue  # paused/unavailable traffic only consumes the same deadline
                self._check_active(snap)
                if time.monotonic() >= deadline:
                    raise BridgeTimeout("Active snapshot deadline expired")
                return snap
        except BaseException as exc:
            self.close_peer()
            if isinstance(exc, (BridgeError, ValueError)) and not isinstance(exc, EpisodeFault):
                raise EpisodeFault(f"Native snapshot wait failed: {exc}") from exc
            raise

    def receive_receipt(
        self, command: StepCommand, baseline: EntityFrame, cursor: NativeEventCursor
    ) -> NativeStepReceipt:
        """Read one step receipt within one total message_timeout deadline; sends nothing.

        A matching receipt is wire-level consistency, not proof of physical input. Only the
        kinds requested in config.native_oracle_kinds are accepted (none when unset); extra
        capabilities advertised by the peer never widen that set.
        """
        if self._peer is None or self._session is None:
            raise BridgeError("No negotiated peer")
        deadline = time.monotonic() + self.config.message_timeout

        def guard() -> None:
            if time.monotonic() >= deadline:
                raise BridgeTimeout("Receipt deadline expired")

        try:
            if self._active is None:
                raise EpisodeFault("A receipt needs a prior active snapshot or receipt")
            if command.session_id != self._session or command.sequence != self._receipts + 1:
                raise EpisodeFault("Command session or sequence does not follow the last receipt")
            if (baseline.game_epoch, baseline.room_visit, baseline.frame_id) != self._active:
                raise EpisodeFault("Baseline is not the latest active frame of this connection")
            assembler = NativeReceiptAssembler(
                command,
                baseline,
                cursor,
                oracle_kinds=self.config.native_oracle_kinds or (),
                before_commit=guard,
            )
            while True:
                guard()
                receipt = assembler.feed(self._read_line(deadline))
                if receipt is not None:
                    break
        except BaseException as exc:
            self.close_peer()
            if isinstance(exc, (BridgeError, ValueError)) and not isinstance(exc, EpisodeFault):
                raise EpisodeFault(f"Native receipt wait failed: {exc}") from exc
            raise
        done = receipt.completion
        self._active = (done.frame.game_epoch, done.frame.room_visit, done.frame.frame_id)
        self._frame = done.frame.frame_id
        self._receipts = command.sequence
        return receipt

    def _check_active(self, snap: EntitySnapshot) -> None:
        if snap.frame_id is None or snap.room is None:
            raise EpisodeFault("Active snapshot lacks frame or room identity")
        if self._active is not None:
            epoch, room, frame = self._active
            if snap.game_epoch != epoch or snap.room.visit_id != room:
                raise EpisodeFault("Game epoch or room changed between active snapshots")
            if snap.frame_id <= frame:
                raise EpisodeFault("Active snapshot frame did not advance")
        self._active = (snap.game_epoch, snap.room.visit_id, snap.frame_id)

    def _unsupported(self, name: str) -> NoReturn:
        self.close_peer()
        raise UnsupportedNativeOperation(f"{name} is not supported by this transport slice")

    def start_episode(self, *args: object, **kwargs: object) -> NoReturn:
        self._unsupported("start_episode")

    def reset(self, *args: object, **kwargs: object) -> NoReturn:
        self._unsupported("reset")

    def step(self, *args: object, **kwargs: object) -> NoReturn:
        self._unsupported("step")
