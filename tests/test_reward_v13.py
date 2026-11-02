"""Reward v13: a 15 s stall limit in a calm room and a 3 s stagnation grace period."""

from dataclasses import replace

import pytest
import yaml
from test_pure_training import write_config
from test_reward_v10 import GAMMA

from isaac_threrisaifuture.live import make_live_env
from isaac_threrisaifuture.rewards import (
    DEFAULT_CONFIG_V12,
    DEFAULT_CONFIG_V13,
    RewardLedgerV4,
    RewardV4Coefficients,
)
from isaac_threrisaifuture.training import TrainingConfigError, load_training_config

V12 = RewardV4Coefficients.load(DEFAULT_CONFIG_V12)
V13 = RewardV4Coefficients.load(DEFAULT_CONFIG_V13)


def write(tmp_path, mutate, name="v13.yaml"):
    raw = yaml.safe_load(DEFAULT_CONFIG_V13.read_text("utf-8"))
    mutate(raw)
    path = tmp_path / name
    path.write_text(yaml.safe_dump(raw), "utf-8")
    return path


def full_stall_cost(coefficients: RewardV4Coefficients, idle: float) -> float:
    ledger = RewardLedgerV4(coefficients, stall_seconds=30.0, gamma=GAMMA)
    return coefficients.stall_restart + ledger.stagnation(0.0, idle)


def test_v13_differs_from_v12_only_in_the_documented_values():
    v13 = yaml.safe_load(DEFAULT_CONFIG_V13.read_text("utf-8"))
    v12 = yaml.safe_load(DEFAULT_CONFIG_V12.read_text("utf-8"))
    assert v13.pop("reward_version") == 13 and v12.pop("reward_version") == 12
    assert v13["stall"].pop("calm_seconds") == 15
    assert v13["stagnation"].pop("grace_seconds") == 3
    assert v12["stagnation"].pop("grace_seconds") == 12
    assert v13 == v12


def test_v13_loads_with_the_exact_values_and_v12_has_no_calm_limit():
    assert V13 == replace(V12, stagnation_grace_seconds=3.0, stall_calm_seconds=15.0)
    assert V12.stall_calm_seconds is None and V13.stall_seconds == 30.0


@pytest.mark.parametrize("bad", [0, -15, True, "15", None, 3, 2, 31])
def test_the_calm_limit_must_be_a_number_between_the_grace_and_the_limit(tmp_path, bad):
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(write(tmp_path, lambda r: r["stall"].update(calm_seconds=bad)))


def test_the_calm_limit_is_required_for_v13_and_rejected_for_v12(tmp_path):
    with pytest.raises(ValueError, match="stall section"):
        RewardV4Coefficients.load(write(tmp_path, lambda r: r["stall"].pop("calm_seconds")))
    raw = yaml.safe_load(DEFAULT_CONFIG_V12.read_text("utf-8"))
    raw["stall"]["calm_seconds"] = 15
    path = tmp_path / "v12_calm.yaml"
    path.write_text(yaml.safe_dump(raw), "utf-8")
    with pytest.raises(ValueError, match="stall section"):
        RewardV4Coefficients.load(path)


def test_any_stall_costs_the_calm_floor_and_a_death_never_pays_better():
    calm = full_stall_cost(V13, 15.0)
    assert calm == pytest.approx(-4.0 - 0.39 * (15 - 3))
    # One run-wide floor sized for the calm limit: 30 s with enemies costs the same.
    assert full_stall_cost(V13, 30.0) == pytest.approx(calm)
    for lost in (1, 6):
        assert V13.death + lost * V13.player_damage_half_heart < calm
    # v12 paid nothing before 12 idle seconds; v13 charges from 3 s on.
    assert full_stall_cost(V12, 10.0) == pytest.approx(V12.stall_restart)
    assert full_stall_cost(V13, 10.0) == pytest.approx(-4.0 - 0.39 * 7)


def test_make_live_env_accepts_v13_and_rejects_v14():
    with pytest.raises(ValueError, match="must match the reward contract"):
        make_live_env(object(), reward_version=13, stall_seconds=15)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Unsupported"):
        make_live_env(object(), reward_version=14)  # type: ignore[arg-type]


def test_the_shipped_training_config_pays_reward_v13(tmp_path):
    config, _ = load_training_config(write_config(tmp_path / "ok.yaml"))
    assert config.contract.reward_version == 13
    assert config.watchdog.stall_seconds == V13.stall_seconds
    path = write_config(tmp_path / "v12.yaml", contract={"reward_version": 12})
    with pytest.raises(TrainingConfigError, match="reward version"):
        load_training_config(path)
