"""Compare frozen evaluation runs: one row per eval root with a metrics/episodes.csv.

Usage: python scripts/compare_eval.py runs/pure-v4-eval/t102400 runs/pure-v4-eval/random ...
       [--baseline random-prior]
Offline and read-only. Shares are fractions of all episodes; means skip empty cells.

Per-1000-step rates (`*_1k`) divide totals by all steps, so they do not depend on how
episodes end: a policy that dies early has short episodes and few stalls, but no more
progress per step. With `--baseline`, a second table gives each run's rate difference
to that run with a 95% bootstrap interval over episodes (fixed seed, unpaired runs).
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
    "damage_1k", "kills_1k", "clears_1k",
)  # fmt: skip
# Rate name -> episodes.csv column; each rate is 1000 * sum(column) / sum(timesteps).
RATES = {
    "damage_1k": "damage_dealt_fraction",
    "kills_1k": "enemies_killed",
    "clears_1k": "rooms_cleared",
}
BOOTSTRAP_SAMPLES = 2000


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


def read_rows(root: Path) -> list[dict[str, str]]:
    with (root / "metrics" / "episodes.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def rate(values: np.ndarray[Any, Any], steps: np.ndarray[Any, Any]) -> float:
    """1000 * total / steps over episodes with both cells; NaN without steps."""
    valid = ~np.isnan(values) & ~np.isnan(steps)
    total = float(steps[valid].sum())
    return 1000.0 * float(values[valid].sum()) / total if total > 0 else float("nan")


def rate_difference(
    rows: list[dict[str, str]], base: list[dict[str, str]], name: str, seed: int = 0
) -> tuple[float, float, float]:
    """Rate of `rows` minus rate of `base`, with a 95% bootstrap interval over episodes."""
    column_name = RATES[name]
    a = column(rows, column_name), column(rows, "timesteps")
    b = column(base, column_name), column(base, "timesteps")
    point = rate(*a) - rate(*b)
    if not len(a[0]) or not len(b[0]):
        return point, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(BOOTSTRAP_SAMPLES):
        i = rng.integers(0, len(a[0]), len(a[0]))
        j = rng.integers(0, len(b[0]), len(b[0]))
        draws.append(rate(a[0][i], a[1][i]) - rate(b[0][j], b[1][j]))
    low, high = np.nanpercentile(draws, [2.5, 97.5])
    return point, float(low), float(high)


def summarize(root: Path) -> dict[str, Any]:
    rows = read_rows(root)
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
        **{
            name: rate(column(rows, source), column(rows, "timesteps"))
            for name, source in RATES.items()
        },
    }


def format_rows(header: list[str], rows: list[list[str]]) -> str:
    table = [header, *rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    return "\n".join(
        "  ".join(c.ljust(w) for c, w in zip(row, widths, strict=True)) for row in table
    )


def format_differences(roots: list[Path], baseline: Path) -> str:
    """Rate differences of every other run to the baseline, `point [low, high]`."""
    base = read_rows(baseline)
    body = []
    for root in roots:
        if root == baseline:
            continue
        rows = read_rows(root)
        cells = [f"{p:+.2f} [{lo:+.2f}, {hi:+.2f}]" for p, lo, hi in (
            rate_difference(rows, base, name) for name in RATES
        )]  # fmt: skip
        body.append([root.name, *cells])
    return format_rows([f"minus {baseline.name}", *RATES], body)


def format_table(results: list[dict[str, Any]]) -> str:
    def cell(value: Any) -> str:
        if isinstance(value, float):
            return "nan" if np.isnan(value) else f"{value:.3f}"
        return str(value)

    return format_rows(list(COLUMNS), [[cell(r[name]) for name in COLUMNS] for r in results])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path, help="eval run roots")
    parser.add_argument("--baseline", help="label (root name) to compare every other run to")
    args = parser.parse_args()
    results = []
    for root in args.roots:
        if not (root / "metrics" / "episodes.csv").is_file():
            parser.error(f"No metrics/episodes.csv under {root}")
        results.append(summarize(root))
    print(format_table(results))
    if args.baseline is not None:
        matches = [root for root in args.roots if root.name == args.baseline]
        if len(matches) != 1:
            parser.error(f"--baseline must name exactly one of the roots: {args.baseline}")
        print()
        print(format_differences(args.roots, matches[0]))


if __name__ == "__main__":
    main()
