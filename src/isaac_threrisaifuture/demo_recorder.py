"""Record human play for behaviour cloning: every snapshot plus the human's input, read-only.

Run `python -m isaac_threrisaifuture.demo_recorder [--out runs/demos] [--port 9528]` (or
Record-Demo.cmd) while no training holds the observer port, then play the game normally. Each mod
session becomes one gzip JSON Lines file: a manifest line, then one `{"t", "snapshot"}` line per
snapshot, where `t` is the recorder's monotonic receipt time in seconds.
"""

import argparse
import gzip
import json
import sys
import time
import zlib
from collections.abc import Callable, Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .entities import OBSERVATION_SCHEMA_VERSION
from .live_wire import DemoSnapshot
from .observation import BridgeError, BridgeTimeout, HelloAck
from .observer_client import ObservationClient, ObserverConfig

MANIFEST_TYPE = "demo_manifest"
RECORDING_FORMAT = 1
# The game runs 30 updates per second; every recorded input mask is one update of active play.
UPDATES_PER_SECOND = 30
FLUSH_SECONDS = 1.0
STATUS_SECONDS = 30.0
ACCEPT_TIMEOUT = 5.0
_READ_CHUNK = 1 << 16


class DemoWriter:
    """One recording file per mod session; flushed about once per second so a crash keeps data."""

    def __init__(
        self,
        out: Path,
        ack: HelloAck,
        *,
        created: datetime | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        created = created or datetime.now(UTC)
        out.mkdir(parents=True, exist_ok=True)
        self.path = out / f"{created:%Y%m%d-%H%M%S}-{ack.session_id[:8]}.jsonl.gz"
        self.snapshots = 0
        self.active_snapshots = 0
        self.input_updates = 0
        self._clock = clock
        self._file = gzip.open(self.path, "wb", compresslevel=6)
        self._flushed = clock()
        manifest = {
            "type": MANIFEST_TYPE,
            "format": RECORDING_FORMAT,
            "session_id": ack.session_id,
            "mod_version": ack.mod_version,
            "capabilities": list(ack.capabilities),
            "created_at": created.isoformat(),
            "observation_schema_version": OBSERVATION_SCHEMA_VERSION,
        }
        self._line(manifest)
        self._file.flush()

    @property
    def play_minutes(self) -> float:
        """Active play time from the recorded input updates (masks and dropped ones)."""
        return self.input_updates / UPDATES_PER_SECOND / 60

    def _line(self, value: object) -> None:
        self._file.write(json.dumps(value, separators=(",", ":")).encode() + b"\n")

    def write(self, received: float, snapshot: DemoSnapshot) -> None:
        self._line({"t": received, "snapshot": snapshot.model_dump(mode="json")})
        self.snapshots += 1
        self.active_snapshots += snapshot.status == "active"
        self.input_updates += len(snapshot.human_input.masks) + snapshot.human_input.dropped
        now = self._clock()
        if now - self._flushed >= FLUSH_SECONDS:
            self._file.flush()
            self._flushed = now

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    def status(self) -> str:
        return (
            f"{self.path.name}: {self.snapshots} snapshots, "
            f"{self.active_snapshots} active, {self.play_minutes:.1f} play minutes"
        )


class _Inflater:
    """Gzip decompression over chunks; a file can hold several gzip members."""

    def __init__(self, state: "zlib._Decompress | None" = None) -> None:
        self._zlib = state or zlib.decompressobj(wbits=31)

    def copy(self) -> "_Inflater":
        return _Inflater(self._zlib.copy())

    def feed(self, chunk: bytes) -> bytes:
        data = self._zlib.decompress(chunk)
        while self._zlib.eof and self._zlib.unused_data:
            rest = self._zlib.unused_data
            self._zlib = zlib.decompressobj(wbits=31)
            data += self._zlib.decompress(rest)
        return data

    def salvage(self, chunk: bytes) -> bytes:
        """Output of a chunk with corrupt bytes up to the first bad byte, fed byte by byte."""
        parts = []
        for start in range(len(chunk)):
            try:
                parts.append(self.feed(chunk[start : start + 1]))
            except zlib.error:
                break
        return b"".join(parts)


def _lines(path: Path) -> Iterator[bytes]:
    """Complete lines of a gzip file; a truncated or corrupt tail ends the stream quietly."""
    with path.open("rb") as raw:
        inflater, pending, corrupt = _Inflater(), b"", False
        while not corrupt and (chunk := raw.read(_READ_CHUNK)):
            backup = inflater.copy()
            try:
                data = inflater.feed(chunk)
            except zlib.error:
                inflater, corrupt = backup, True
                data = inflater.salvage(chunk)
            pending += data
            *complete, pending = pending.split(b"\n")
            yield from complete
        # A last line without its newline was cut off by a crash; it is dropped.


def read_recording(path: Path) -> tuple[dict[str, Any], Iterator[tuple[float, DemoSnapshot]]]:
    """Manifest and `(receipt time, snapshot)` pairs of a recording, tolerating a cut-off tail.

    Raises ValueError when the manifest is missing or of another format, and when a complete
    snapshot line is invalid.
    """
    lines = _lines(path)
    first = next(lines, None)
    manifest = json.loads(first) if first else None
    if (
        not isinstance(manifest, dict)
        or manifest.get("type") != MANIFEST_TYPE
        or manifest.get("format") != RECORDING_FORMAT
    ):
        raise ValueError(f"{path}: not a demo recording of format {RECORDING_FORMAT}")

    def snapshots() -> Iterator[tuple[float, DemoSnapshot]]:
        for number, line in enumerate(lines, start=2):
            try:
                record = json.loads(line)
                received = record["t"]
                if type(received) not in (int, float):
                    raise ValueError("Receipt time must be a number")
                yield float(received), DemoSnapshot.model_validate(record["snapshot"])
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"{path}:{number}: invalid demo record") from exc

    return manifest, snapshots()


def record_session(
    client: ObservationClient,
    ack: HelloAck,
    out: Path,
    *,
    log: Callable[[str], None] = print,
    clock: Callable[[], float] = time.monotonic,
) -> DemoWriter:
    """Write snapshots until the session ends (BridgeError) or Ctrl+C; the file is closed.

    A file without any active snapshot is removed.
    """
    writer = DemoWriter(out, ack, clock=clock)
    log(f"Recording {writer.path}")
    status_at = clock() + STATUS_SECONDS
    try:
        while True:
            snapshot = client.receive()
            assert isinstance(snapshot, DemoSnapshot)
            writer.write(clock(), snapshot)
            if clock() >= status_at:
                log(writer.status())
                status_at = clock() + STATUS_SECONDS
    except BridgeError as exc:
        log(f"Session ended: {exc}")
    finally:
        writer.close()
        log(f"Closed {writer.status()}")
        if writer.active_snapshots == 0:
            # Menu-only sessions (the mod connects before a run starts) hold no play.
            writer.path.unlink(missing_ok=True)
            log(f"Removed {writer.path.name}: no active play")
    return writer


def run(out: Path, port: int, *, log: Callable[[str], None] = print) -> int:
    config = ObserverConfig(
        port=port, entity_observations=True, demo_record=True, accept_timeout=ACCEPT_TIMEOUT
    )
    try:
        with ObservationClient(config) as client:
            log(f"Listening on 127.0.0.1:{port}; start the game and play. Ctrl+C stops.")
            while True:
                try:
                    ack = client.accept()
                except BridgeTimeout:
                    continue  # the game is not running yet; the mod retries every second
                except BridgeError as exc:
                    log(f"Handshake failed: {exc}")
                    continue
                record_session(client, ack, out, log=log)
    except KeyboardInterrupt:
        log("Stopped.")
        return 0
    except BridgeError as exc:
        print(f"{exc}. Is training running? Stop it first with Train-Stop.cmd.", file=sys.stderr)
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--out", type=Path, default=Path("runs/demos"))
    parser.add_argument("--port", type=int, default=9528)
    args = parser.parse_args(argv)
    return run(args.out, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
