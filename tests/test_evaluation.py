"""OFFLINE evaluation tests on the toy simulator. Rates here say nothing about Isaac."""

import json
from dataclasses import replace

import pytest

from isaac_threrisaifuture.baselines import RandomPolicy, ScriptedPolicy
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episodes import Scenario
from isaac_threrisaifuture.evaluation import (
    REPORT_VERSION,
    EpisodeRecord,
    evaluate,
    summarize,
    wilson_interval,
)
from isaac_threrisaifuture.rewards import CombatCoefficients, RewardLedger
from isaac_threrisaifuture.scenarios import scenarios_for
from isaac_threrisaifuture.sim import SyntheticRoomBackend

EASY = Scenario("easy", "validation", 1, 300, enemy_count=1, enemy_hp=3.5)


def factory(**backend_args: object):
    def make() -> IsaacCombatEnv:
        ledger = RewardLedger(CombatCoefficients.load())
        return IsaacCombatEnv(
            SyntheticRoomBackend(**backend_args),  # type: ignore[arg-type]
            [EASY],
            accountant=ledger,
        )

    return make


def test_wilson_interval_known_values_and_bounds():
    low, high = wilson_interval(5, 10)
    assert low == pytest.approx(0.2366, abs=1e-3) and high == pytest.approx(0.7634, abs=1e-3)
    assert wilson_interval(0, 0) == (0.0, 1.0)
    low, high = wilson_interval(10, 10)
    assert high == 1.0 and 0.0 < low < 1.0


def test_report_is_json_serializable_with_equal_budgets():
    report = evaluate(ScriptedPolicy(), factory(), [EASY], episodes=3, seeds=[1, 2])
    data = json.loads(json.dumps(report.to_dict()))
    assert data["label"] == "scripted-baseline" and data["split"] == "validation"
    assert data["overall"]["attempted"] == 6 == len(data["episodes"])
    assert data["per_scenario"]["easy"]["attempted"] == 6
    assert {e["seed"] for e in data["episodes"]} == {10000, 10001, 10002, 20000, 20001, 20002}
    low, high = data["overall"]["clear_rate_ci95"]
    assert 0.0 <= low <= data["overall"]["clear_rate"] <= high <= 1.0


def test_evaluation_is_reproducible():
    a = evaluate(RandomPolicy(), factory(), [EASY], episodes=2, seeds=[7])
    b = evaluate(RandomPolicy(), factory(), [EASY], episodes=2, seeds=[7])
    assert a.to_dict() == b.to_dict()


def test_infrastructure_faults_are_not_deaths_or_clears():
    report = evaluate(RandomPolicy(), factory(fail_after_updates=0), [EASY], 2, [1])
    overall = report.overall
    assert (overall.faults, overall.valid, overall.deaths, overall.cleared) == (2, 0, 0, 0)
    assert all(e.outcome == "fault" and e.fault for e in report.episodes)
    json.dumps(report.to_dict())


def test_summarize_excludes_faults_from_rates():
    records = [
        EpisodeRecord("s", 1, "cleared", 1.0, 10.0),
        EpisodeRecord("s", 2, "death", 3.0, -10.0),
        EpisodeRecord("s", 3, "timeout", 0.0, 0.0),
        EpisodeRecord("s", 4, "fault", fault="x"),
    ]
    m = summarize(records)
    assert (m.attempted, m.valid, m.unknown, m.faults) == (4, 3, 0, 1)
    assert m.clear_rate == pytest.approx(1 / 3)
    assert m.mean_damage_taken_half_hearts == pytest.approx(4 / 3)
    assert m.mean_return == 0.0


def test_summarize_keeps_unknown_out_of_categories_rates_and_faults():
    records = [
        EpisodeRecord("s", 1, "cleared", 1.0, 10.0),
        EpisodeRecord("s", 2, "death", 3.0, -10.0),
        EpisodeRecord("s", 3, "unknown", 5.0, 4.0),
        EpisodeRecord("s", 4, "unknown", 2.0, 4.0),
        EpisodeRecord("s", 5, "fault", fault="x"),
    ]
    m = summarize(records)
    assert (m.attempted, m.unknown, m.faults) == (5, 2, 1)
    assert (m.cleared, m.deaths, m.timeouts) == (1, 1, 0)
    assert m.attempted == m.valid + m.unknown + m.faults
    assert m.valid == m.cleared + m.deaths + m.timeouts == 2
    assert m.clear_rate == pytest.approx(1 / 2)
    assert m.clear_rate_ci95 == wilson_interval(1, 2)
    # Damage/return means keep covering every non-fault episode, unknown ones included.
    assert m.mean_damage_taken_half_hearts == pytest.approx((1 + 3 + 5 + 2) / 4)
    assert m.mean_return == pytest.approx((10 - 10 + 4 + 4) / 4)


def test_only_unknown_episodes_give_no_rate_evidence():
    m = summarize([EpisodeRecord("s", i, "unknown", 2.0, 1.0) for i in range(3)])
    assert (m.attempted, m.valid, m.unknown, m.faults, m.cleared) == (3, 0, 3, 0, 0)
    assert m.clear_rate == 0.0 and m.clear_rate_ci95 == (0.0, 1.0)
    assert m.mean_damage_taken_half_hearts == 2.0 and m.mean_return == 1.0


class UncoveredBackend(SyntheticRoomBackend):
    """Same toy room, but without the terminal-coverage claim (like the live frame-delta path)."""

    def start_episode(self, scenario, seed):
        return replace(super().start_episode(scenario, seed), terminal_coverage=frozenset())

    def step(self, action, repeat):
        return replace(super().step(action, repeat), terminal_coverage=frozenset())


def test_uncovered_backend_reports_unknown_not_clears_and_json_round_trips():
    def make() -> IsaacCombatEnv:
        return IsaacCombatEnv(UncoveredBackend(), [EASY], accountant=None)

    report = evaluate(ScriptedPolicy(), make, [EASY], episodes=2, seeds=[1])
    data = json.loads(json.dumps(report.to_dict()))
    outcomes = {e["outcome"] for e in data["episodes"]}
    assert data["report_version"] == 2 == REPORT_VERSION
    assert outcomes <= {"death", "unknown"} and "unknown" in outcomes
    overall = data["overall"]
    assert overall["unknown"] == sum(e["outcome"] == "unknown" for e in data["episodes"])
    assert overall["faults"] == 0 and overall["cleared"] == 0 and overall["timeouts"] == 0
    assert overall["attempted"] == overall["valid"] + overall["unknown"]
    assert data["per_scenario"]["easy"]["unknown"] == overall["unknown"]


def test_mixed_splits_and_empty_budgets_are_rejected():
    mixed = [*scenarios_for("validation")[:1], *scenarios_for("test")[:1]]
    with pytest.raises(ValueError):
        evaluate(RandomPolicy(), factory(), mixed, 1, [1])
    with pytest.raises(ValueError):
        evaluate(RandomPolicy(), factory(), [EASY], 0, [1])
    with pytest.raises(ValueError):
        evaluate(RandomPolicy(), factory(), [EASY], 1, [])
