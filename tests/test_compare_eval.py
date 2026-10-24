"""Offline check of scripts/compare_eval.py on a tiny synthetic episodes.csv."""

import csv
import importlib.util
import math
from pathlib import Path

from isaac_threrisaifuture.episode_metrics import FIELDS
from isaac_threrisaifuture.training import wilson_interval

SCRIPT = Path(__file__).parents[1] / "scripts" / "compare_eval.py"


def load_script():
    spec = importlib.util.spec_from_file_location("compare_eval", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_root(root: Path, rows: list[dict[str, object]]) -> Path:
    path = root / "metrics" / "episodes.csv"
    path.parent.mkdir(parents=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, restval="", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return root


def test_summarize_one_row_per_root(tmp_path):
    compare = load_script()
    root = write_root(
        tmp_path / "t100",
        [
            {"end_reason": "death", "rooms_visited": 3, "rooms_cleared": 2, "max_stage": 1,
             "damage_dealt_fraction": 0.5, "enemies_killed": 4, "half_hearts_lost": 6,
             "return": 2.0},
            {"end_reason": "timeout", "truncation_reason": "stall", "rooms_visited": 1,
             "rooms_cleared": 0, "max_stage": 2, "damage_dealt_fraction": 0.1,
             "enemies_killed": 0, "half_hearts_lost": 0, "return": -1.0},
            {"end_reason": "death", "rooms_visited": 1, "rooms_cleared": 0, "max_stage": 1,
             "damage_dealt_fraction": 0.3, "enemies_killed": 2, "half_hearts_lost": 4,
             "return": 0.0},
            {"end_reason": "death", "rooms_visited": 2, "rooms_cleared": 1, "max_stage": 1,
             "damage_dealt_fraction": "", "enemies_killed": 2, "half_hearts_lost": 2,
             "return": 1.0},
        ],
    )  # fmt: skip
    row = compare.summarize(root)
    assert row["label"] == "t100" and row["episodes"] == 4
    assert row["death"] == 0.75 and row["stall"] == 0.25
    assert row["left_room"] == 0.5 and row["any_clear"] == 0.5
    assert math.isclose(row["damage"], 0.3)  # the empty cell is skipped
    assert math.isclose(row["kills"], 2.0) and math.isclose(row["rooms_cleared"], 0.75)
    assert math.isclose(row["hp_lost"], 3.0) and math.isclose(row["return"], 0.5)
    assert row["max_stage"] == 2.0
    assert (row["stall_lo"], row["stall_hi"]) == wilson_interval(1, 4)
    table = compare.format_table([row])
    assert table.splitlines()[0].startswith("label") and "t100" in table.splitlines()[1]


def test_damage_standard_error_is_sample_sd_over_root_n(tmp_path):
    compare = load_script()
    root = write_root(
        tmp_path / "r",
        [{"damage_dealt_fraction": v} for v in (0.0, 0.2, 0.4, 0.6)],
    )
    expected = 0.2581988897 / 2  # sample sd of the four values over sqrt(4)
    assert math.isclose(compare.summarize(root)["damage_se"], expected, rel_tol=1e-6)
