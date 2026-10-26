"""Summarize the observer's frame-timing log lines from an Isaac log.txt.

Usage: python scripts/lua_perf.py /path/to/log.txt [--since TEXT]
Offline and read-only. The Lua mod writes one line per ~10 s window while streaming:
  Observer perf window_ms=10003 updates=321 renders=598 snapshots=290 update_ms=12
  render_ms=4100 capture_ms=3000 encode_ms=800   (one physical line, integers only)
`--since TEXT` keeps only windows after the last log line containing TEXT (for example a
session marker); without it all windows are used. Shares are fractions of window wall
time spent inside each callback, capture() or json.encode of snapshots.
"""

import argparse
import re
import sys
from pathlib import Path

KEYS = (
    "window_ms", "updates", "renders", "snapshots", "update_ms", "render_ms", "capture_ms",
    "encode_ms",
)  # fmt: skip
LINE = re.compile(r"Observer perf((?: [a-z_]+=\d+)+)\s*$")


def parse_line(line: str) -> dict[str, int] | None:
    """Return the counters of one perf line, or None if it is not a complete one."""
    match = LINE.search(line)
    if match is None:
        return None
    values = {k: int(v) for k, v in (pair.split("=") for pair in match.group(1).split())}
    return values if all(key in values for key in KEYS) else None


def read_windows(lines: list[str], since: str | None = None) -> list[dict[str, int]]:
    """All perf windows, after the last line containing `since` when it is given."""
    start = 0
    if since:
        marks = [i for i, line in enumerate(lines) if since in line]
        if not marks:
            raise ValueError(f"--since text not found: {since!r}")
        start = marks[-1] + 1
    parsed = (parse_line(line) for line in lines[start:])
    return [window for window in parsed if window is not None]


def summarize(windows: list[dict[str, int]]) -> dict[str, float]:
    """Totals, rates per second, wall-time shares and mean ms per snapshot."""
    total = {key: sum(w[key] for w in windows) for key in KEYS}
    wall_s = total["window_ms"] / 1000
    snapshots = total["snapshots"]
    return {
        "windows": float(len(windows)),
        "wall_s": wall_s,
        "updates_per_s": total["updates"] / wall_s if wall_s else float("nan"),
        "renders_per_s": total["renders"] / wall_s if wall_s else float("nan"),
        "snapshots_per_s": snapshots / wall_s if wall_s else float("nan"),
        "update_share": total["update_ms"] / total["window_ms"] if wall_s else float("nan"),
        "render_share": total["render_ms"] / total["window_ms"] if wall_s else float("nan"),
        "capture_share": total["capture_ms"] / total["window_ms"] if wall_s else float("nan"),
        "encode_share": total["encode_ms"] / total["window_ms"] if wall_s else float("nan"),
        "capture_ms_per_snapshot": total["capture_ms"] / snapshots if snapshots else float("nan"),
        "encode_ms_per_snapshot": total["encode_ms"] / snapshots if snapshots else float("nan"),
    }


def format_summary(stats: dict[str, float]) -> str:
    return "\n".join(
        (
            f"windows            {int(stats['windows'])}  ({stats['wall_s']:.1f} s of wall time)",
            f"updates/s          {stats['updates_per_s']:.1f}",
            f"renders/s          {stats['renders_per_s']:.1f}",
            f"snapshots/s        {stats['snapshots_per_s']:.1f}",
            f"update callback    {stats['update_share']:.1%} of wall time",
            f"render callback    {stats['render_share']:.1%} of wall time",
            f"capture()          {stats['capture_share']:.1%} of wall time, "
            f"{stats['capture_ms_per_snapshot']:.2f} ms/snapshot",
            f"json.encode        {stats['encode_share']:.1%} of wall time, "
            f"{stats['encode_ms_per_snapshot']:.2f} ms/snapshot",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("log", type=Path, help="Isaac log.txt")
    parser.add_argument(
        "--since", default=None, help="only windows after the last line with this text"
    )
    args = parser.parse_args()
    lines = args.log.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        windows = read_windows(lines, args.since)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    if not windows:
        print("No 'Observer perf' windows found", file=sys.stderr)
        return 1
    print(format_summary(summarize(windows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
