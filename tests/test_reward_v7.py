"""Reward v7 = reward v6 + stagnation cost (openspec change stagnation-cost-reward-v7)."""

from pathlib import Path

import numpy as np
import pytest
import yaml
from test_reward_v4 import COEF, LIVE_SCENARIO, Script, event, ledger, live

from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.rewards import (
    DEFAULT_CONFIG_V7,
    REWARD_V4_COLUMNS,
    RewardLedgerV4,
    RewardV4Coefficients,
)

ROOT = Path(__file__).parents[1]
ARCHIVED_V6 = ROOT / "archive" / "configs" / "reward-v6.yaml"


def test_v7_differs_from_v6_only_in_stall_hit_and_stagnation():
    v7 = yaml.safe_load(DEFAULT_CONFIG_V7.read_text("utf-8"))
    v6 = yaml.safe_load(ARCHIVED_V6.read_text("utf-8"))
    assert v7.pop("reward_version") == 7 and v6.pop("reward_version") == 6
    assert v7.pop("stagnation") == {"per_second": -0.1, "grace_seconds": 20}
    assert v7["outcome"].pop("stall_restart") == -5.0
    assert v6["outcome"].pop("stall_restart") == -10.0
    assert v7["outcome"].pop("player_damage_half_heart") == -0.5
    assert v6["outcome"].pop("player_damage_half_heart") == -1.0
    assert v7 == v6


def test_the_stagnation_section_is_required_for_v7_and_forbidden_for_older(tmp_path):
    raw = yaml.safe_load(DEFAULT_CONFIG_V7.read_text("utf-8"))
    missing = {k: v for k, v in raw.items() if k != "stagnation"}
    forbidden = {**yaml.safe_load(ARCHIVED_V6.read_text("utf-8")), "stagnation": raw["stagnation"]}
    wrong_keys = {**raw, "stagnation": {"per_second": -0.1}}
    for name, bad in (("missing", missing), ("forbidden", forbidden), ("keys", wrong_keys)):
        path = tmp_path / f"{name}.yaml"
        path.write_text(yaml.safe_dump(bad), "utf-8")
        with pytest.raises(ValueError):
            RewardV4Coefficients.load(path)


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [(5, 15, 0.0), (18, 25, -0.5), (60, 2, 0.0), (20, 20, 0.0), (0, 90, -7.0)],
)
def test_stagnation_charges_only_idle_seconds_added_past_the_grace(before, after, expected):
    assert ledger().stagnation(before, after) == pytest.approx(expected)


def test_a_dead_player_and_a_config_without_the_term_pay_no_stagnation():
    dead = ledger()
    dead.consume([event("player_died")], 0)
    assert dead.stagnation(30.0, 40.0) == 0.0
    v6 = RewardLedgerV4(RewardV4Coefficients.load(ARCHIVED_V6))
    assert v6.coefficients.stagnation_per_second == 0.0
    assert v6.stagnation(0.0, 90.0) == 0.0


class IdleScript(Script):
    """Script backend that reports a prepared idle clock after every step."""

    def __init__(self, steps, idle):
        super().__init__(steps)
        self.clock = list(idle)
        self.stall_idle_seconds = self.clock[0]

    def start_episode(self, scenario, seed):
        self.stall_idle_seconds = 0.0
        return super().start_episode(scenario, seed)

    def step(self, action, repeat):
        self.stall_idle_seconds = self.clock.pop(0)
        return super().step(action, repeat)


def run_idle(idle, truncate_last=False):
    steps = [(2 + i, [], 1) for i in range(len(idle))]
    env = IsaacCombatEnv(IdleScript(steps, idle), [LIVE_SCENARIO], accountant=RewardLedgerV4(COEF))
    env.reset()
    results = []
    for index in range(len(idle)):
        if truncate_last and index == len(idle) - 1:
            env.request_truncation("stall")
        results.append(env.step(np.array([0, 0, 0])))
    return results


def stagnation_of(results):
    return [r[4]["reward_components"]["stagnation"] for r in results]


def test_env_charges_nothing_inside_the_grace_and_past_it_the_added_seconds():
    results = run_idle([10.0, 20.0, 25.0, 30.0])
    assert stagnation_of(results) == pytest.approx([0.0, 0.0, -0.5, -0.5])


def test_env_pays_nothing_when_progress_resets_the_clock():
    results = run_idle([60.0, 2.0, 5.0])
    assert stagnation_of(results) == pytest.approx([-4.0, 0.0, 0.0])


def test_a_full_stall_pays_seven_stagnation_and_the_stall_restart():
    results = run_idle([float(t) for t in range(10, 91, 10)], truncate_last=True)
    info = results[-1][4]
    assert sum(stagnation_of(results)) == pytest.approx(-7.0)  # the truncation step is charged
    assert info["reward_components"]["stall"] == COEF.stall_restart == -5.0
    columns = info["episode_summary"]["columns"]
    assert columns["stagnation"] == pytest.approx(-7.0) and columns["stall"] == -5.0
    assert set(REWARD_V4_COLUMNS) >= {"stagnation", "stall"}


def test_a_backend_without_an_idle_clock_pays_nothing():
    steps = [(2 + i, [], 1) for i in range(3)]
    env = IsaacCombatEnv(Script(steps), [LIVE_SCENARIO], accountant=RewardLedgerV4(COEF))
    env.reset()
    results = [env.step(np.array([0, 0, 0])) for _ in steps]
    assert stagnation_of(results) == [0.0, 0.0, 0.0]


def test_a_full_stall_is_never_cheaper_than_the_death_bound_in_the_shipped_configs():
    training = yaml.safe_load((ROOT / "configs" / "training-pure-v4.yaml").read_text("utf-8"))
    stall_seconds = training["watchdog"]["stall_seconds"]
    full_stall = COEF.stall_restart + COEF.stagnation_per_second * (
        stall_seconds - COEF.stagnation_grace_seconds
    )
    assert full_stall >= COEF.death + 6 * COEF.player_damage_half_heart


def test_stagnation_caps_snapshot_overshoot_at_seven():
    assert ledger().stagnation(0.0, 90.2) == pytest.approx(-7.0)


def test_repeated_idle_periods_share_one_episode_cap():
    results = run_idle([80.0, 2.0, 80.0, 2.0, 90.4], truncate_last=True)
    assert stagnation_of(results) == pytest.approx([-6.0, 0.0, -1.0, 0.0, 0.0])
    assert results[-1][4]["episode_summary"]["columns"]["stagnation"] == pytest.approx(-7.0)


def test_stagnation_allowance_survives_same_run_reset_and_renews_only_on_new_epoch():
    value = ledger()
    value.begin(live(1).entity_frame, 84)
    assert value.stagnation(0.0, 90.0) == pytest.approx(-7.0)
    value.reset(2)
    value.begin(live(2).entity_frame, 84)
    assert value.stagnation(0.0, 80.0) == 0.0
    value.begin(live(3, epoch=2).entity_frame, 84)
    assert value.stagnation(0.0, 80.0) == pytest.approx(-6.0)


def test_stagnation_cap_uses_the_configured_watchdog_limit():
    value = RewardLedgerV4(COEF, stall_seconds=60.0)
    assert value.stagnation(0.0, 90.0) == pytest.approx(-4.0)
