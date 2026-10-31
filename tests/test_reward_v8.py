"""Reward v8 = reward v7 with a shorter stall limit (openspec change short-stall-reward-v8).

Reward v9 replaced v8 as the shipped config; these tests pin the archived v8 file.
"""

from pathlib import Path

import numpy as np
import pytest
import yaml
from test_reward_v4 import LIVE_SCENARIO, Script
from test_reward_v7 import IdleScript

from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.rewards import RewardLedgerV4, RewardV4Coefficients
from isaac_threrisaifuture.training import load_training_config

ROOT = Path(__file__).parents[1]
ARCHIVED_V8 = ROOT / "archive" / "configs" / "reward-v8.yaml"
ARCHIVED_V7 = ROOT / "archive" / "configs" / "reward-v7.yaml"
TRAINING = ROOT / "configs" / "training-pure-v4.yaml"
STALL_SECONDS = 40.0  # the stall limit v8 to v11 were sized for
COEF = RewardV4Coefficients.load(ARCHIVED_V8)


def ledger() -> RewardLedgerV4:
    return RewardLedgerV4(COEF, stall_seconds=STALL_SECONDS)


def test_v8_differs_from_v7_only_in_the_stagnation_rate_and_grace():
    v8 = yaml.safe_load(ARCHIVED_V8.read_text("utf-8"))
    v7 = yaml.safe_load(ARCHIVED_V7.read_text("utf-8"))
    assert v8.pop("reward_version") == 8 and v7.pop("reward_version") == 7
    assert v8.pop("stagnation") == {"per_second": -0.25, "grace_seconds": 12}
    assert v7.pop("stagnation") == {"per_second": -0.1, "grace_seconds": 20}
    assert v8 == v7  # stall_restart -5, damage -0.5, death -10 and the rest are unchanged


def test_the_training_config_keeps_a_stall_limit_not_longer_than_v8_under_the_current_contract():
    config, digest = load_training_config(TRAINING)
    assert config.watchdog.stall_seconds == 30.0 <= STALL_SECONDS  # reward v12 shortens it again
    assert config.contract.reward_version == 12
    assert digest != "d62dc21baf19941b0484e857f2124e8fbffb3d564ab9763a2e13619230c63bc4"


def test_the_stagnation_section_is_required_for_v8(tmp_path):
    raw = yaml.safe_load(ARCHIVED_V8.read_text("utf-8"))
    path = tmp_path / "missing.yaml"
    path.write_text(yaml.safe_dump({k: v for k, v in raw.items() if k != "stagnation"}), "utf-8")
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(path)
    assert RewardV4Coefficients.load(ARCHIVED_V7).stagnation_per_second == -0.1  # v7 stays loadable


def test_the_stagnation_cap_is_seven_at_the_configured_limit():
    assert COEF.stagnation_per_second * (STALL_SECONDS - COEF.stagnation_grace_seconds) == -7.0


@pytest.mark.parametrize(
    ("before", "after", "expected"),
    [(0, 12, 0.0), (5, 12, 0.0), (10, 14, -0.5), (12, 16, -1.0), (30, 2, 0.0), (0, 40, -7.0)],
)
def test_charging_starts_after_twelve_seconds(before, after, expected):
    assert ledger().stagnation(before, after) == pytest.approx(expected)


def test_snapshot_overshoot_past_the_limit_stays_at_seven():
    assert ledger().stagnation(0.0, 40.4) == pytest.approx(-7.0)


def test_a_full_stall_at_forty_seconds_pays_seven_stagnation_and_the_stall_restart():
    idle = [float(t) for t in range(4, 41, 4)]
    steps = [(2 + i, [], 1) for i in range(len(idle))]
    env = IsaacCombatEnv(IdleScript(steps, idle), [LIVE_SCENARIO], accountant=ledger())
    env.reset()
    results = []
    for index in range(len(idle)):
        if index == len(idle) - 1:
            env.request_truncation("stall")
        results.append(env.step(np.array([0, 0, 0])))
    paid = [r[4]["reward_components"]["stagnation"] for r in results]
    assert paid[:3] == [0.0, 0.0, 0.0]  # 4, 8 and 12 s are inside the grace
    assert paid[3] == pytest.approx(-1.0)  # 12 -> 16 s
    assert sum(paid) == pytest.approx(-7.0)
    info = results[-1][4]
    assert info["reward_components"]["stall"] == COEF.stall_restart == -5.0
    assert info["episode_summary"]["columns"]["stagnation"] == pytest.approx(-7.0)


def test_a_full_stall_is_never_cheaper_than_the_death_bound_in_the_shipped_configs():
    full_stall = COEF.stall_restart + COEF.stagnation_per_second * (
        STALL_SECONDS - COEF.stagnation_grace_seconds
    )
    assert full_stall == -12.0
    assert full_stall >= COEF.death + 6 * COEF.player_damage_half_heart


def test_a_grace_period_not_shorter_than_the_stall_limit_is_refused():
    for stall in (12.0, 10.0):
        with pytest.raises(ValueError, match="grace"):
            RewardLedgerV4(COEF, stall_seconds=stall)
    with pytest.raises(ValueError, match="positive"):
        RewardLedgerV4(COEF, stall_seconds=0.0)
    # Without a stagnation term the grace is irrelevant.
    v6 = RewardV4Coefficients.load(ROOT / "archive" / "configs" / "reward-v6.yaml")
    assert RewardLedgerV4(v6, stall_seconds=10.0)


def test_a_backend_without_an_idle_clock_pays_nothing():
    steps = [(2 + i, [], 1) for i in range(3)]
    env = IsaacCombatEnv(Script(steps), [LIVE_SCENARIO], accountant=ledger())
    env.reset()
    paid = [env.step(np.array([0, 0, 0]))[4]["reward_components"]["stagnation"] for _ in steps]
    assert paid == [0.0, 0.0, 0.0]
