"""Reward v12: door pull 4, death -11, stall restart -4, stagnation -0.39 and a 30 s stall limit."""

import random
from dataclasses import replace

import pytest
import yaml
from test_pure_training import write_config
from test_reward_v10 import GAMMA, make, start, trajectory, visit

from isaac_threrisaifuture.live import make_live_env
from isaac_threrisaifuture.rewards import (
    DEFAULT_CONFIG_V11,
    DEFAULT_CONFIG_V12,
    RewardLedgerV4,
    RewardV4Coefficients,
)
from isaac_threrisaifuture.training import TrainingConfigError, load_training_config

V11 = RewardV4Coefficients.load(DEFAULT_CONFIG_V11)
V12 = RewardV4Coefficients.load(DEFAULT_CONFIG_V12)
STALL = 30.0


def write(tmp_path, mutate, name="v12.yaml"):
    raw = yaml.safe_load(DEFAULT_CONFIG_V12.read_text("utf-8"))
    mutate(raw)
    path = tmp_path / name
    path.write_text(yaml.safe_dump(raw), "utf-8")
    return path


def full_stall_cost() -> float:
    ledger = RewardLedgerV4(V12, stall_seconds=STALL, gamma=GAMMA)
    return V12.stall_restart + ledger.stagnation(0.0, STALL)


def death_cost(half_hearts_lost: int) -> float:
    return V12.death + half_hearts_lost * V12.player_damage_half_heart


def test_v12_differs_from_v11_only_in_the_documented_values():
    v12 = yaml.safe_load(DEFAULT_CONFIG_V12.read_text("utf-8"))
    v11 = yaml.safe_load(DEFAULT_CONFIG_V11.read_text("utf-8"))
    assert v12.pop("reward_version") == 12 and v11.pop("reward_version") == 11
    assert v12.pop("stall") == {"seconds": 30}
    assert v12["door_shaping"].pop("coefficient") == 4.0
    assert v11["door_shaping"].pop("coefficient") == 2.0
    assert v12["outcome"].pop("death") == -11.0 and v11["outcome"].pop("death") == -10.0
    assert v12["outcome"].pop("stall_restart") == -4.0
    assert v11["outcome"].pop("stall_restart") == -5.0
    assert v12["stagnation"].pop("per_second") == -0.39
    assert v11["stagnation"].pop("per_second") == -0.25
    assert v12 == v11  # grace 12, blocked_cost 0, max_hops 5, novelty and pickups are unchanged


def test_v12_loads_with_the_exact_values_and_v11_has_no_stall_limit():
    assert V12.door_shaping_coefficient == 4.0 and V12.door_shaping_max_hops == 5
    assert V12.door_shaping_blocked_cost == 0.0 and V12.novelty_cross_run is True
    assert V12.death == -11.0 and V12.stall_restart == -4.0
    assert V12.stagnation_per_second == -0.39 and V12.stagnation_grace_seconds == 12.0
    assert V12.stall_seconds == 30.0 and V11.stall_seconds is None
    assert V12 == replace(
        V11,
        door_shaping_coefficient=4.0,
        death=-11.0,
        stall_restart=-4.0,
        stagnation_per_second=-0.39,
        stall_seconds=30.0,
    )


def test_the_stall_section_is_required_for_v12_and_rejected_for_v11(tmp_path):
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(write(tmp_path, lambda r: r.pop("stall")))
    raw = yaml.safe_load(DEFAULT_CONFIG_V11.read_text("utf-8"))
    raw["stall"] = {"seconds": 30}
    path = tmp_path / "v11_stall.yaml"
    path.write_text(yaml.safe_dump(raw), "utf-8")
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(path)


@pytest.mark.parametrize(
    "bad",
    [12, 10, 0, -30, True, "30", None, {"seconds": 30, "extra": 1}, {}],
)
def test_the_stall_section_must_hold_a_number_above_the_grace_period(tmp_path, bad):
    section = bad if isinstance(bad, dict) else {"seconds": bad}
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(write(tmp_path, lambda r: r.update(stall=section)))
    with pytest.raises(ValueError, match="exceed"):
        replace(V12, stall_seconds=12.0)


def test_a_stall_costs_about_eleven_and_a_death_never_pays_better():
    assert full_stall_cost() == pytest.approx(-4.0 - 0.39 * (30 - 12))
    assert full_stall_cost() == pytest.approx(-11.02)
    assert death_cost(1) == pytest.approx(-11.5)
    assert death_cost(6) == pytest.approx(-14.0)
    for lost in (1, 6):
        assert death_cost(lost) <= full_stall_cost()
    # v11 let a death at one half heart pay more than a stall; v12 does not.
    v11_stall = V11.stall_restart + V11.stagnation_per_second * (40 - V11.stagnation_grace_seconds)
    assert V11.death + V11.player_damage_half_heart > v11_stall
    assert full_stall_cost() < V12.stall_restart  # the stagnation floor still bites


@pytest.mark.parametrize("seed", range(4))
def test_door_coefficient_four_doubles_the_v11_step_shaping(seed):
    first, doors, position, _ = next(trajectory(random.Random(seed), 1))
    steps = list(trajectory(random.Random(seed), 40))
    paid: dict[str, list[float]] = {}
    for name, coef in (("v11", V11), ("v12", V12)):
        value = make(coef)
        start(value, first, doors, frame=position)
        paid[name] = [
            visit(value, room, doors, position, enemies=enemies, terminal=t == len(steps) - 1)
            for t, (room, doors, position, enemies) in enumerate(steps)
        ]
    assert paid["v12"] == pytest.approx([2 * x for x in paid["v11"]])
    assert any(abs(x) > 0 for x in paid["v11"])


def test_make_live_env_rejects_a_stall_limit_that_differs_from_the_contract():
    for seconds in (40, 90, 29.5):
        with pytest.raises(ValueError, match="must match the reward contract"):
            make_live_env(object(), reward_version=12, stall_seconds=seconds)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Unsupported"):
        make_live_env(object(), reward_version=13)  # type: ignore[arg-type]


def test_the_training_config_must_use_the_reward_stall_limit(tmp_path):
    config, _ = load_training_config(write_config(tmp_path / "ok.yaml"))
    assert config.watchdog.stall_seconds == V12.stall_seconds
    for seconds in (40.0, 45.0, 29.0):
        path = write_config(tmp_path / "bad.yaml", watchdog={"stall_seconds": seconds})
        with pytest.raises(TrainingConfigError, match="stall"):
            load_training_config(path)
