"""Compare frozen evaluation runs: one row per eval root with a metrics/episodes.csv.

Usage: python scripts/compare_eval.py runs/pure-v4-eval/t102400 runs/pure-v4-eval/random ...
Offline and read-only. Shares are fractions of all episodes; means skip empty cells.
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from isaac_threrisaifuture.training import wilson_interval  # noqa: E402

COLUMNS = (
    "label", "episodes", "death", "stall", "left_room", "damage", "damage_se", "kills",
    "rooms_cleared", "any_clear", "hp_lost", "return", "max_stage", "stall_lo", "stall_hi",
)  # fmt: skip


def column(rows: list[dict[str, str]], name: str) -> np.ndarray[Any, np.dtype[np.float64]]:
    """Numeric column; empty or missing cells become NaN."""
    values = []
    for row in rows:
        try:
            values.append(float(row.get(name) or "nan"))
        except ValueError:
            values.append(float("nan"))
    return np.asarray(values, dtype=np.float64)


def mean(values: np.ndarray[Any, Any]) -> float:
    valid = values[~np.isnan(values)]
    return float(valid.mean()) if valid.size else float("nan")


def standard_error(values: np.ndarray[Any, Any]) -> float:
    valid = values[~np.isnan(values)]
    return float(valid.std(ddof=1) / np.sqrt(valid.size)) if valid.size > 1 else float("nan")


def summarize(root: Path) -> dict[str, Any]:
    path = root / "metrics" / "episodes.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    n = len(rows)
    stalls = sum(row.get("truncation_reason") == "stall" for row in rows)
    deaths = sum(row.get("end_reason") == "death" for row in rows)
    visited, cleared = column(rows, "rooms_visited"), column(rows, "rooms_cleared")
    low, high = wilson_interval(stalls, n)
    damage = column(rows, "damage_dealt_fraction")
    stages = column(rows, "max_stage")
    return {
        "label": root.name,
        "episodes": n,
        "death": deaths / n if n else float("nan"),
        "stall": stalls / n if n else float("nan"),
        "left_room": float(np.sum(visited > 1)) / n if n else float("nan"),
        "damage": mean(damage),
        "damage_se": standard_error(damage),
        "kills": mean(column(rows, "enemies_killed")),
        "rooms_cleared": mean(cleared),
        "any_clear": float(np.sum(cleared > 0)) / n if n else float("nan"),
        "hp_lost": mean(column(rows, "half_hearts_lost")),
        "return": mean(column(rows, "return")),
        "max_stage": float(np.nanmax(stages)) if n and not np.isnan(stages).all() else float("nan"),
        "stall_lo": low,
        "stall_hi": high,
    }


def format_table(results: list[dict[str, Any]]) -> str:
    def cell(value: Any) -> str:
        if isinstance(value, float):
            return "nan" if np.isnan(value) else f"{value:.3f}"
        return str(value)

    table = [list(COLUMNS)] + [[cell(r[name]) for name in COLUMNS] for r in results]
    widths = [max(len(row[i]) for row in table) for i in range(len(COLUMNS))]
    return "\n".join(
        "  ".join(c.ljust(w) for c, w in zip(row, widths, strict=True)) for row in table
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path, help="eval run roots")
    args = parser.parse_args()
    results = []
    for root in args.roots:
        if not (root / "metrics" / "episodes.csv").is_file():
            parser.error(f"No metrics/episodes.csv under {root}")
        results.append(summarize(root))
    print(format_table(results))


if __name__ == "__main__":
    main()
