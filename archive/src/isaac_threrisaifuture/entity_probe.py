"""Finite read-only entity recording. Attach only; never launch, reset or control Isaac."""

import argparse
import json
import time
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from .encoding import encode
from .entities import EntitySnapshot
from .observation import BridgeError, BridgeTimeout
from .observer_client import ObservationClient, ObserverConfig
from .recording import JsonlRecorder


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--samples", type=int, default=50)
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--port", type=int, default=9528)
    args = parser.parse_args(argv)
    if not 1 <= args.samples <= 500 or not 0 < args.seconds <= 300:
        parser.error("Budget must be 1..500 samples and >0..300 finite seconds")
    written = unavailable = 0
    deadline = time.monotonic() + args.seconds
    config = ObserverConfig(
        port=args.port,
        accept_timeout=args.seconds / 2,
        handshake_timeout=args.seconds / 2,
        entity_observations=True,
    )
    try:
        with JsonlRecorder(args.output, "policy_frames", "game_api") as recorder:
            with ObservationClient(config) as client:
                print(json.dumps({"event": "listening", "address": client.address}), flush=True)
                print(client.accept().model_dump_json(), flush=True)
                for _ in range(args.samples):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise BridgeTimeout("Entity recording wall-time budget expired")
                    client.config = replace(config, message_timeout=min(3.0, remaining))
                    snap = client.receive()
                    if not isinstance(snap, EntitySnapshot):
                        raise BridgeError("Entity capability did not produce entity snapshots")
                    if snap.entity_frame is None:
                        unavailable += 1
                        continue
                    encode(snap.entity_frame)  # Validate the actual encoder path before recording.
                    recorder.record(snap.entity_frame)
                    written += 1
    except (BridgeError, OSError, ValueError) as error:
        print(json.dumps({"status": "failed", "error": str(error), "frames": written}))
        return 2
    except KeyboardInterrupt:
        print(json.dumps({"status": "interrupted", "frames": written}))
        return 130
    print(json.dumps({"status": "recorded", "frames": written, "unavailable": unavailable}))
    return 0 if written else 2


if __name__ == "__main__":
    raise SystemExit(main())
