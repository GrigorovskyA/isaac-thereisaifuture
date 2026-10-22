"""One fixed, attach-only, stationary firing-cadence comparison."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from pathlib import Path
from time import monotonic, time
from typing import TextIO

from .actions import ActionApproval, ActionClient, CommandAck, CommandKind, Direction
from .entities import EntitySnapshot
from .observation import BridgeError, BridgeTimeout, Health, ProtocolError, Snapshot
from .observer_client import ObserverConfig

MAX_RUNTIME_SECONDS = 30.0
MAX_COMMANDS = 16
COMMAND_RESERVE_SECONDS = 0.75
TRACE_PHASES = (("short", 3, 7), ("long", 6, 7))


@dataclass(frozen=True)
class _RoomEvidence:
    game_epoch: int
    room_visit: int
    health: Health
    x: float
    y: float


def _preflight_room(
    client: ActionClient, approval: ActionApproval, deadline: float
) -> _RoomEvidence:
    """Verify an empty room read-only, then reuse the same listener for actions."""
    remaining = deadline - monotonic()
    if remaining <= 4:
        raise BridgeTimeout("Firing probe deadline reached before room preflight")
    accept_timeout = min(8.0, remaining - 4.0)
    handshake_timeout = min(2.0, remaining - accept_timeout - 2.0)
    message_timeout = min(2.0, remaining - accept_timeout - handshake_timeout - 1.0)
    if min(accept_timeout, handshake_timeout, message_timeout) <= 0:
        raise BridgeTimeout("Firing probe deadline reached before room preflight")
    readonly_config = replace(
        client.config,
        accept_timeout=accept_timeout,
        handshake_timeout=handshake_timeout,
        message_timeout=message_timeout,
        safe_actions=False,
        entity_observations=True,
    )
    action_config = client.config
    client.config = readonly_config
    try:
        client.accept()
        snapshot = client.receive()
    finally:
        client.close_peer()
        client.config = action_config
    if not isinstance(snapshot, EntitySnapshot):
        raise ProtocolError("Read-only preflight did not provide entity observations")
    if (
        snapshot.status != "active"
        or snapshot.frame_id is None
        or snapshot.room is None
        or snapshot.player is None
        or snapshot.entity_frame is None
        or snapshot.game_epoch != approval.game_epoch
        or snapshot.player.character_type != 0
    ):
        raise ProtocolError("Read-only preflight needs the approved active file-2 instance")
    entities = snapshot.entity_frame
    if any(entity.kind in ("enemy", "projectile") for entity in entities.entities):
        raise ProtocolError("Firing cadence preflight requires an empty room")
    if entities.source_overflow.get("enemy", 0) or entities.source_overflow.get("projectile", 0):
        raise ProtocolError("Entity feed overflow prevents proving the room is empty")
    x, y = snapshot.player.position.x, snapshot.player.position.y
    if not (120 <= x <= 520 and 100 <= y <= 420):
        raise ProtocolError("Firing probe requires the player inside the centered-room bounds")
    return _RoomEvidence(
        game_epoch=snapshot.game_epoch,
        room_visit=snapshot.room.visit_id,
        health=snapshot.player.health,
        x=x,
        y=y,
    )


def _write(stream: TextIO, event: str, data: object) -> None:
    stream.write(json.dumps({"event": event, "data": data}, separators=(",", ":")) + "\n")
    stream.flush()


def _identity(snapshot: Snapshot) -> dict[str, object]:
    assert snapshot.player is not None
    position = snapshot.player.position
    return {
        "session_id": snapshot.session_id,
        "game_epoch": snapshot.game_epoch,
        "room_visit": snapshot.room.visit_id if snapshot.room is not None else None,
        "frame_id": snapshot.frame_id,
        "status": snapshot.status,
        "character_type": snapshot.player.character_type,
        "position": {"x": position.x, "y": position.y},
    }


def _active(
    client: ActionClient,
    session_id: str,
    approval: ActionApproval,
    deadline: float,
    evidence: _RoomEvidence,
) -> Snapshot:
    if monotonic() + COMMAND_RESERVE_SECONDS >= deadline:
        raise BridgeTimeout("Firing probe deadline reached")
    snapshot = client.receive()
    if (
        snapshot.status != "active"
        or snapshot.frame_id is None
        or snapshot.player is None
        or snapshot.room is None
        or snapshot.player.character_type != 0
        or snapshot.session_id != session_id
        or snapshot.game_epoch != approval.game_epoch
    ):
        raise ProtocolError(
            "Firing probe requires active character type 0 and approved game identity"
        )
    if (
        snapshot.game_epoch != evidence.game_epoch
        or snapshot.room.visit_id != evidence.room_visit
        or snapshot.player.health != evidence.health
    ):
        raise ProtocolError("Room, epoch, session, health or position changed during firing probe")
    x, y = snapshot.player.position.x, snapshot.player.position.y
    if not (120 <= x <= 520 and 100 <= y <= 420):
        raise ProtocolError("Firing probe requires the player inside the centered-room bounds")
    if (
        abs(snapshot.player.position.x - evidence.x) > 2
        or abs(snapshot.player.position.y - evidence.y) > 2
    ):
        raise ProtocolError("Room, epoch, session, health or position changed during firing probe")
    return snapshot


def _wait_until_frame(
    client: ActionClient,
    session_id: str,
    approval: ActionApproval,
    target_frame: int,
    deadline: float,
    evidence: _RoomEvidence,
) -> Snapshot:
    while True:
        snapshot = _active(client, session_id, approval, deadline, evidence)
        if snapshot.frame_id is not None and snapshot.frame_id >= target_frame:
            return snapshot


def _command(
    client: ActionClient,
    command_count: list[int],
    stream: TextIO,
    deadline: float,
    kind: CommandKind,
    *,
    shoot: Direction = "none",
    frames: int = 0,
) -> CommandAck:
    if command_count[0] >= MAX_COMMANDS:
        raise ProtocolError("Firing probe command limit reached")
    if monotonic() + COMMAND_RESERVE_SECONDS >= deadline:
        raise BridgeTimeout("Firing probe deadline reached")
    command_count[0] += 1
    ack = client.command(kind, move="none", shoot=shoot, frames=frames)
    _write(stream, "command_ack", ack.model_dump(mode="json"))
    return ack


def run_firing_cadence_probe(approval: ActionApproval, stream: TextIO) -> None:
    """Run 7 three-frame then 7 six-frame stationary shots, with bounded cleanup."""
    now = time()
    if approval.profile_mode != "ordinary_profile_exception" or approval.slot != 2:
        raise ValueError("This probe requires an explicit ordinary-profile file-2 approval")
    if approval.expires_at <= now or approval.expires_at > now + 1800:
        raise ValueError("Approval must be live and expire within 30 minutes")

    started = monotonic()
    deadline = started + MAX_RUNTIME_SECONDS
    command_count = [0]
    action_sent = False
    session_id: str | None = None
    primary_error: BaseException | None = None

    config = ObserverConfig(
        accept_timeout=8.0,
        handshake_timeout=2.0,
        message_timeout=0.5,
    )
    with ActionClient(config, approval) as client:
        try:
            evidence = _preflight_room(client, approval, deadline)
            remaining = deadline - monotonic()
            if remaining <= COMMAND_RESERVE_SECONDS + 1.0:
                raise BridgeTimeout("Firing probe deadline reached after room preflight")
            accept_timeout = min(8.0, remaining - 3.0)
            handshake_timeout = min(2.0, remaining - accept_timeout - COMMAND_RESERVE_SECONDS - 1.0)
            if min(accept_timeout, handshake_timeout) <= 0:
                raise BridgeTimeout("Firing probe deadline reached before action connection")
            client.config = replace(
                client.config,
                accept_timeout=accept_timeout,
                handshake_timeout=handshake_timeout,
            )
            hello = client.accept()
            session_id = hello.session_id
            initial = _active(client, session_id, approval, deadline, evidence)
            _write(
                stream,
                "started",
                {
                    "identity": _identity(initial),
                    "approval_slot": approval.slot,
                    "preflight": "empty_active_room",
                },
            )

            for phase, frames, repeats in TRACE_PHASES:
                for repetition in range(1, repeats + 1):
                    ack = _command(
                        client,
                        command_count,
                        stream,
                        deadline,
                        "action",
                        shoot="right",
                        frames=frames,
                    )
                    action_sent = True
                    target_frame = ack.frame_id + frames
                    current = _wait_until_frame(
                        client,
                        session_id,
                        approval,
                        target_frame,
                        deadline,
                        evidence,
                    )
                    _write(
                        stream,
                        "sample_window",
                        {
                            "phase": phase,
                            "repetition": repetition,
                            "requested_frames": frames,
                            "identity": _identity(current),
                        },
                    )
                if phase == "short":
                    neutral = _command(
                        client,
                        command_count,
                        stream,
                        deadline,
                        "action",
                        frames=1,
                    )
                    action_sent = True
                    current = _wait_until_frame(
                        client,
                        session_id,
                        approval,
                        neutral.frame_id + 1,
                        deadline,
                        evidence,
                    )
                    _write(stream, "neutral_between_phases", {"identity": _identity(current)})

            _command(client, command_count, stream, deadline, "release")
            action_sent = False
            _write(
                stream,
                "completed",
                {
                    "commands": command_count[0],
                    "elapsed_seconds": round(monotonic() - started, 3),
                    "release": "explicit",
                },
            )
        except BaseException as exc:
            primary_error = exc
            try:
                _write(
                    stream,
                    "stopped",
                    {"commands": command_count[0], "error_type": type(exc).__name__},
                )
            except OSError:
                pass
            raise
        finally:
            if action_sent and getattr(client, "_peer", None) is not None:
                try:
                    _command(client, command_count, stream, deadline, "release")
                    _write(stream, "cleanup_release", {"commands": command_count[0]})
                except BaseException as cleanup_error:
                    if primary_error is None:
                        raise
                    if hasattr(primary_error, "add_note"):
                        primary_error.add_note(
                            f"Release cleanup failed: {type(cleanup_error).__name__}"
                        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--confirmed-save-slot", type=int, choices=[2], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.approval.stat().st_size > 2048:
            raise ValueError("Local action approval exceeds 2048 bytes")
        approval = ActionApproval.model_validate_json(args.approval.read_bytes())
        if approval.slot != args.confirmed_save_slot:
            raise ValueError("Approval and manually confirmed slot do not match")
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            run_firing_cadence_probe(approval, stream)
    except (BridgeError, ValueError, OSError) as exc:
        print(f"Firing cadence probe stopped: {type(exc).__name__}", flush=True)
        raise SystemExit(2) from exc
    except KeyboardInterrupt:
        print("Firing cadence probe interrupted; disconnect cleanup was attempted.", flush=True)
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
