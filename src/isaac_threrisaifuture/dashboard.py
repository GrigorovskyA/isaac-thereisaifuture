"""Read-only live training dashboard: `python -m isaac_threrisaifuture.dashboard`.

Serves one HTML page and one JSON endpoint on 127.0.0.1 only. It reads the run root
(episode CSV, supervisor status, latest checkpoint manifest) and never writes to it.
"""

import argparse
import csv
import json
import math
import threading
import time
from array import array
from collections.abc import Sequence
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .checkpoints import CheckpointError, latest_checkpoint_dir, read_manifest

LOOPBACK = "127.0.0.1"
MAX_ROWS = 5000
EPISODES_CSV = Path("metrics") / "episodes.csv"
TRAIN_CSV = Path("metrics") / "train.csv"
TEXT_FIELDS = frozenset(
    {"episode_id", "scenario_id", "outcome", "end_reason", "truncation_reason", "wall_time"}
)
_CHUNK = 1 << 20


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, UTC).isoformat(timespec="seconds")


def _number(text: str) -> float | int | None:
    if text == "":
        return None
    value = float(text)  # ValueError marks the row malformed
    if not math.isfinite(value):
        return None
    return (
        int(value) if value.is_integer() and "." not in text and "e" not in text.lower() else value
    )


class EpisodeTail:
    """Incremental CSV reader (episodes.csv, train.csv).

    Keeps one byte offset per valid row, not the rows themselves.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._reset()

    def _reset(self) -> None:
        self._header: list[str] | None = None
        self._ident: int | None = None
        self._offset = 0  # end of the last fully consumed line
        self._starts = array("Q")  # start offset of each valid row

    def _parse(self, line: bytes) -> dict[str, Any] | None:
        header = self._header
        if header is None:
            return None
        try:
            cells = next(csv.reader([line.decode("utf-8")]))
            if len(cells) != len(header):
                return None
            return {
                name: (cell or None) if name in TEXT_FIELDS else _number(cell)
                for name, cell in zip(header, cells, strict=True)
            }
        except (ValueError, UnicodeError, csv.Error, StopIteration):
            return None

    def _refresh(self) -> int:
        try:
            info = self.path.stat()
        except OSError:
            self._reset()
            return 0
        if info.st_size < self._offset or (self._ident not in (None, info.st_ino)):
            self._reset()  # truncated or recreated
        self._ident = info.st_ino
        if info.st_size == self._offset:
            return len(self._starts)
        try:
            with self.path.open("rb") as stream:
                stream.seek(self._offset)
                buffer = b""
                while True:
                    chunk = stream.read(_CHUNK)
                    if not chunk:
                        break
                    buffer += chunk
                    end = buffer.rfind(b"\n") + 1  # a partial last line stays unconsumed
                    if end:
                        self._consume(buffer[:end])
                        buffer = buffer[end:]
        except OSError:
            pass
        return len(self._starts)

    def _consume(self, block: bytes) -> None:
        position = self._offset
        for line in block.splitlines(keepends=True):
            text = line.rstrip(b"\r\n")
            if self._header is None:
                try:
                    header = next(csv.reader([text.decode("utf-8")]))
                except (UnicodeError, csv.Error, StopIteration):
                    header = []
                if header:
                    self._header = header
            elif text and self._parse(text) is not None:
                self._starts.append(position)
            position += len(line)
        self._offset = position

    def read(self, since: int, limit: int | None = None) -> tuple[list[dict[str, Any]], int]:
        """Rows with index >= since (at most `limit`) and the total count of valid rows."""
        with self._lock:
            total = self._refresh()
            since = max(0, since)
            if since >= total:
                return [], total
            stop = since + (MAX_ROWS if limit is None else limit)
            begin = self._starts[since]
            end = self._starts[stop] if stop < total else self._offset
            try:
                with self.path.open("rb") as stream:
                    stream.seek(begin)
                    block = stream.read(end - begin)
            except OSError:
                return [], total
        rows: list[dict[str, Any]] = []
        for line in block.splitlines():
            row = self._parse(line) if line else None
            if row is not None:
                row["index"] = since + len(rows)
                rows.append(row)
        return rows, total


class CheckpointInfo:
    """Latest checkpoint across seeds; the manifest (and its hashes) is re-read only on change."""

    def __init__(self, run_root: Path) -> None:
        self.run_root = run_root
        self._cache: dict[Path, tuple[tuple[Any, ...], dict[str, Any] | None]] = {}
        self._lock = threading.Lock()

    def read(self) -> dict[str, Any] | None:
        best: dict[str, Any] | None = None
        with self._lock:
            for root in sorted(self.run_root.glob("seed-*/checkpoints")):
                item = self._one(root)
                if item is not None and (best is None or item["created_at"] > best["created_at"]):
                    best = item
        return best

    def _one(self, root: Path) -> dict[str, Any] | None:
        try:
            pointer = root / "latest.txt"
            name = pointer.read_text("utf-8").strip()
            key = (
                name,
                pointer.stat().st_mtime_ns,
                (root / name / "manifest.json").stat().st_mtime,
            )
        except (OSError, UnicodeError):
            return None
        cached = self._cache.get(root)
        if cached is not None and cached[0] == key:
            return cached[1]
        value: dict[str, Any] | None
        try:
            manifest = read_manifest(latest_checkpoint_dir(root))
            value = {
                "checkpoint_id": manifest.checkpoint_id,
                "timesteps": manifest.timesteps,
                "rollout_index": manifest.rollout_index,
                "hyperparameters": manifest.hyperparameters,
                "seed": manifest.seed,
                "created_at": _iso(key[2]),
            }
        except (CheckpointError, OSError):
            return None  # not cached: a half-published checkpoint is retried next poll
        self._cache[root] = (key, value)
        return value


def _read_json(path: Path) -> tuple[dict[str, Any], float] | None:
    try:
        stamp = path.stat().st_mtime
        data = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return None
    return (data, stamp) if isinstance(data, dict) else None


def read_supervisor(run_root: Path) -> dict[str, Any] | None:
    """Newest session status, or the final forever.json once it is newer than every session."""
    folder = run_root / "supervisor"
    sessions = sorted(p for p in folder.glob("session-*") if p.is_dir())
    live = _read_json(sessions[-1] / "status.json") if sessions else None
    forever = _read_json(folder / "forever.json")
    if forever is not None and (live is None or forever[1] >= live[1]):
        data, stamp = forever
        return {
            "state": "stopped",
            "session": sessions[-1].name if sessions else None,
            "updated_at": _iso(stamp),
            "stop_reason": str(data.get("stop_reason", "unknown")),
            "consecutive_faults": data.get("consecutive_faults"),
            "finished": True,
        }
    if live is None:
        return None
    data, stamp = live
    updated = data.get("updated_at")
    return {
        "state": str(data.get("state", "unknown")),
        "session": sessions[-1].name,
        "updated_at": _iso(float(updated) if isinstance(updated, int | float) else stamp),
        "stop_reason": None,
        "reason": data.get("reason"),
        "fault": data.get("fault"),
        "finished": False,
    }


class DashboardState:
    def __init__(self, run_root: Path) -> None:
        self.run_root = run_root
        self.tail = EpisodeTail(run_root / EPISODES_CSV)
        self.train_tail = EpisodeTail(run_root / TRAIN_CSV)
        self.checkpoints = CheckpointInfo(run_root)

    def snapshot(self, since: int, train_since: int = 0) -> dict[str, Any]:
        rows, total = self.tail.read(since)
        train, train_total = self.train_tail.read(train_since)
        return {
            "episodes": rows,
            "total_episodes": total,
            "train": train,
            "total_train_rows": train_total,
            "latest_checkpoint": self.checkpoints.read(),
            "supervisor": read_supervisor(self.run_root),
            "run_root": self.run_root.name,
            "expected_csv": EPISODES_CSV.as_posix(),
            "expected_train_csv": TRAIN_CSV.as_posix(),
            "server_time": _iso(time.time()),
        }


class DashboardServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, run_root: Path, host: str = LOOPBACK, port: int = 8765) -> None:
        if host != LOOPBACK:
            raise ValueError(f"The dashboard only binds to {LOOPBACK}, not {host!r}")
        super().__init__((host, port), _Handler)
        self.state = DashboardState(run_root)


def _int_param(query: dict[str, list[str]], name: str) -> int:
    try:
        return int(query.get(name, ["0"])[0])
    except ValueError:
        return 0


class _Handler(BaseHTTPRequestHandler):
    server: DashboardServer

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass

    def _send(self, status: int, body: bytes, content_type: str, extra: Sequence[str] = ()) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for header in extra:
            name, _, value = header.partition(": ")
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].lower()
        return host in (LOOPBACK, "localhost")  # blocks DNS-rebinding names

    def do_GET(self) -> None:
        if not self._host_ok():
            self._send(HTTPStatus.FORBIDDEN, b"forbidden", "text/plain; charset=utf-8")
            return
        url = urlsplit(self.path)
        if url.path == "/":
            page = resources.files(__package__).joinpath("dashboard.html").read_bytes()
            csp = (
                "Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; "
                "style-src 'unsafe-inline'; connect-src 'self'"
            )
            self._send(HTTPStatus.OK, page, "text/html; charset=utf-8", (csp,))
        elif url.path == "/api/state":
            query = parse_qs(url.query)
            since, train_since = (_int_param(query, "since"), _int_param(query, "train_since"))
            body = json.dumps(
                self.server.state.snapshot(since, train_since), allow_nan=False
            ).encode()
            self._send(HTTPStatus.OK, body, "application/json")
        else:
            self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain; charset=utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=Path("runs/pure-v4"))
    parser.add_argument("--host", default=LOOPBACK, help="loopback only; anything else is refused")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    try:
        server = DashboardServer(args.run_root, args.host, args.port)
    except (ValueError, OSError) as error:
        print(f"Dashboard cannot start: {error}")
        return 2
    url = f"http://{LOOPBACK}:{server.server_address[1]}"
    print(f"Dashboard for {args.run_root}: {url} (Ctrl+C stops)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
