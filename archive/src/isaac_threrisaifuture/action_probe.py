"""Finite attach-only ordinary-profile probe. Never launches or resets Isaac."""

import argparse
import json
import time
from pathlib import Path
from typing import TextIO

from .actions import ActionApproval, ActionClient, Direction
from .observation import BridgeError, ProtocolError, Snapshot
from .observer_client import ObserverConfig


def sequence_plan(count: int) -> list[tuple[Direction, Direction]]:
    """At most five repetitions of the ten declared independent/combined cases."""
    if type(count) is not int or not 1 <= count <= 50:
        raise ValueError("Sequence count must be 1..50")
    cases: list[tuple[Direction, Direction]] = [
        ("left", "none"),
        ("right", "none"),
        ("up", "none"),
        ("down", "none"),
        ("none", "left"),
        ("none", "right"),
        ("none", "up"),
        ("none", "down"),
        ("right", "up"),
        ("left", "down"),
    ]
    return (cases * 5)[:count]


def _write(stream: TextIO, event: str, data: object) -> None:
    stream.write(json.dumps({"time": time.time(), "event": event, "data": data}) + "\n")
    stream.flush()


def _active(client: ActionClient, initial: Snapshot | None, deadline: float) -> Snapshot:
    if time.monotonic() >= deadline:
        raise BridgeError("Finite probe deadline expired")
    snap = client.receive()
    if snap.status != "active" or snap.player is None or snap.room is None:
        raise ProtocolError("Probe requires an active solo room; stop on pause/unavailability")
    if initial is not None and (
        initial.player is None
        or snap.game_epoch != initial.game_epoch
        or snap.room != initial.room
        or snap.player.health != initial.player.health  # stop on damage or health changes
    ):
        raise ProtocolError("Probe room/epoch/health changed; stop without reset")
    return snap


def run_probe(approval: ActionApproval, count: int, stream: TextIO) -> None:
    """Run once, <=50 cases / 120 seconds; socket cleanup is unconditional."""
    plan = sequence_plan(count)
    if approval.expires_at <= time.time():
        raise ValueError("Local action approval expired")
    deadline = time.monotonic() + 120
    with ActionClient(ObserverConfig(accept_timeout=30), approval) as client:
        print("Listening for manually launched Isaac; no automatic startup.", flush=True)
        _write(stream, "hello", client.accept().model_dump())
        initial = _active(client, None, deadline)
        before = initial
        for index, (move, shoot) in enumerate(plan, 1):
            if before.player is None:
                raise ProtocolError("Missing player")
            # No automatic repositioning; avoid intentionally approaching room edges.
            pos = before.player.position
            if move != "none" and not (120 <= pos.x <= 520 and 100 <= pos.y <= 420):
                raise ProtocolError("Player too close to room boundary for a movement probe")
            acks = []
            for repeat in range(1 if shoot == "none" else 3):
                if time.monotonic() >= deadline:
                    raise BridgeError("Finite probe deadline expired")
                # A single two-frame movement pulse bounds displacement even on
                # fast builds. Shooting refreshes afterward never repeat movement.
                pulse_move = move if repeat == 0 else "none"
                acks.append(
                    client.command(
                        "action",
                        move=pulse_move,
                        shoot=shoot,
                        frames=2 if pulse_move != "none" else 15,
                    ).model_dump()
                )
                _active(client, initial, deadline)
            client.command("action", frames=1)  # bounded explicit neutral
            client.command("release")
            after = _active(client, initial, deadline)
            _write(
                stream,
                "sequence",
                {
                    "index": index,
                    "move": move,
                    "shoot": shoot,
                    "acks": acks,
                    "before": before.model_dump(),
                    "after": after.model_dump(),
                    "shooting_evidence": "requires_matching_native_tear_diagnostics",
                },
            )
            before = after
            print(
                f"Sequence {index}/{count}: movement={move}, shooting={shoot}; released", flush=True
            )
        _write(
            stream,
            "completed",
            {"sequences": count, "runtime_acceptance": "pending_evidence_review"},
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval", type=Path, required=True)
    parser.add_argument("--confirmed-save-slot", type=int, choices=[2], required=True)
    parser.add_argument("--sequences", type=int, default=50)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.approval.stat().st_size > 2048:
            raise ValueError("Local action approval exceeds 2048 bytes")
        approval = ActionApproval.model_validate_json(args.approval.read_bytes())
        with args.output.open("x", encoding="utf-8") as stream:
            run_probe(approval, args.sequences, stream)
    except (BridgeError, ValueError, OSError) as exc:
        print(f"Probe stopped: {exc}", flush=True)
        raise SystemExit(2) from exc
    except KeyboardInterrupt:
        print(
            "Probe interrupted; connection closed and Lua action expiry remains active.", flush=True
        )
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
