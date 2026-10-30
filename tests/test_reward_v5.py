"""Reward v5 = reward v4 with the stall restart charged like a death (-10)."""

from pathlib import Path

import pytest
import yaml
from test_reward_v4 import ARCHIVED_V8, COEF, REWARD_V4_COLUMNS, run_env

from isaac_threrisaifuture.rewards import RewardV4Coefficients

ARCHIVE = Path(__file__).parents[1] / "archive" / "configs"
ARCHIVED_V4 = ARCHIVE / "reward-v4.yaml"
ARCHIVED_V5 = ARCHIVE / "reward-v5.yaml"
ARCHIVED_V6 = ARCHIVE / "reward-v6.yaml"


def test_v5_differs_from_v4_only_in_the_stall_restart():
    v5 = yaml.safe_load(ARCHIVED_V5.read_text("utf-8"))
    v4 = yaml.safe_load(ARCHIVED_V4.read_text("utf-8"))
    assert v5["reward_version"] == 5 and v4["reward_version"] == 4
    assert v5["outcome"].pop("stall_restart") == -10.0
    assert v4["outcome"].pop("stall_restart") == -5.0
    v5.pop("reward_version"), v4.pop("reward_version"), v5.pop("status"), v4.pop("status")
    assert v5 == v4
    assert RewardV4Coefficients.load(ARCHIVED_V5).stall_restart == -10.0


def test_v6_keeps_the_v5_coefficients():
    v6 = yaml.safe_load(ARCHIVED_V6.read_text("utf-8"))
    v5 = yaml.safe_load(ARCHIVED_V5.read_text("utf-8"))
    assert v6.pop("reward_version") == 6 and v5.pop("reward_version") == 5
    assert v6 == v5


def test_the_ledger_loads_versions_4_to_11_only(tmp_path):
    assert RewardV4Coefficients.load(ARCHIVED_V4).stall_restart == -5.0
    assert RewardV4Coefficients.load(ARCHIVED_V5) == RewardV4Coefficients.load(ARCHIVED_V6)
    assert RewardV4Coefficients.load(ARCHIVED_V8).stagnation_per_second == -0.25
    raw = yaml.safe_load(ARCHIVED_V8.read_text("utf-8"))
    raw["reward_version"] = 12
    path = tmp_path / "v12.yaml"
    path.write_text(yaml.safe_dump(raw), "utf-8")
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(path)


def test_stall_truncation_pays_the_stall_restart_once_and_never_with_death():
    _, results = run_env([(2, [], 1), (3, [], 1), (4, [], 1)], truncate_at=1)
    stalls = [r[4]["reward_components"].get("stall", 0.0) for r in results]
    assert stalls == [0.0, COEF.stall_restart]
    assert results[-1][4]["episode_summary"]["columns"]["stall"] == COEF.stall_restart
    _, died = run_env([(2, [("player_died", {})], 1), (3, [], 1)], truncate_at=0)
    columns = died[-1][4]["episode_summary"]["columns"]
    assert columns["death"] == COEF.death and columns.get("stall", 0.0) == 0.0


def test_v5_has_the_same_reward_columns_as_v4():
    assert "stall" in REWARD_V4_COLUMNS and len(REWARD_V4_COLUMNS) == 16
