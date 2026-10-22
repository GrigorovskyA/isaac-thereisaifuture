"""OFFLINE benchmark tests with a fake clock. Synthetic throughput says nothing about Isaac."""

import json
from typing import Any

import pytest

from isaac_threrisaifuture.benchmark import (
    BenchmarkConfig,
    compare_action_repeat,
    propose_config_changes,
    run_benchmark,
    write_report,
)

TICK = 0.01


class FakeClock:
    def __init__(self, tick: float = TICK) -> None:
        self.now = 0.0
        self.tick = tick

    def __call__(self) -> float:
        self.now += self.tick
        return self.now


def test_fake_clock_gives_exact_timing_and_report_sections():
    report = run_benchmark(BenchmarkConfig(max_steps=20, seed=1), clock=FakeClock())
    det, timing = report["deterministic"], report["timing"]
    assert report["backend"] == "synthetic"
    assert report["real_game_throughput"] == "blocked"
    assert det["steps"] == 20
    assert timing["backend_step_latency_seconds"]["mean"] == pytest.approx(TICK)
    assert timing["observation_encode_seconds"]["mean"] == pytest.approx(TICK)
    assert timing["env_steps_per_second"] == pytest.approx(1 / (3 * TICK))
    assert timing["game_updates_per_second"] == pytest.approx(det["game_updates"] / (20 * 3 * TICK))
    assert report["host"]["cuda_required"] is False
    assert "platform" not in det and "elapsed_seconds" not in det


def test_deterministic_section_is_reproducible_across_clocks():
    cfg = BenchmarkConfig(max_steps=150, max_seconds=600.0, seed=7)
    a = run_benchmark(cfg, clock=FakeClock(0.01))
    b = run_benchmark(cfg, clock=FakeClock(0.1))
    assert a["deterministic"] == b["deterministic"]
    assert a["timing"] != b["timing"]


def test_duration_bound_stops_before_step_bound():
    report = run_benchmark(BenchmarkConfig(max_steps=10_000, max_seconds=1.0), clock=FakeClock())
    assert 0 < report["deterministic"]["steps"] < 100


@pytest.mark.parametrize(
    "kwargs",
    [
        {"action_repeat": 0},
        {"action_repeat": 16},
        {"max_steps": 0},
        {"max_seconds": 0.0},
        {"max_steps": 10**9},
    ],
)
def test_config_bounds_are_enforced(kwargs: dict[str, Any]):
    with pytest.raises(ValueError):
        BenchmarkConfig(**kwargs)


def test_action_repeat_changes_game_updates_per_step():
    comparison = compare_action_repeat(
        [1, 4], BenchmarkConfig(max_steps=10, seed=3), clock=FakeClock()
    )
    assert comparison["backend"] == "synthetic"
    assert "Synthetic" in comparison["note"]
    one, four = (r["deterministic"] for r in comparison["runs"])
    assert one["game_updates"] <= one["steps"]
    assert four["game_updates"] > one["game_updates"]
    with pytest.raises(ValueError):
        compare_action_repeat([2, 2])


def _run(repeat: int, ups: float, clear: float = 0.5, fault: float = 0.0, episodes: int = 10):
    return {
        "deterministic": {
            "config": {"action_repeat": repeat},
            "episodes": episodes,
            "clear_rate": clear,
            "fault_rate": fault,
        },
        "timing": {"game_updates_per_second": ups},
    }


def _comparison(*runs: dict[str, Any]) -> dict[str, Any]:
    return {"backend": "synthetic", "runs": list(runs)}


def test_proposal_has_evidence_and_is_not_applied():
    (proposal,) = propose_config_changes(_comparison(_run(1, 100), _run(4, 300), _run(8, 200)))
    assert proposal["applied"] is False
    assert (proposal["from"], proposal["to"]) == (1, 4)
    assert proposal["evidence"]["game_updates_per_second"] == [100, 300]
    assert "Synthetic" in proposal["caveat"]


@pytest.mark.parametrize(
    "candidate",
    [
        _run(4, 110),  # gain too small
        _run(4, 300, clear=0.2),  # quality dropped
        _run(4, 300, fault=0.1),  # more failures
        _run(4, 300, episodes=2),  # too little evidence
    ],
)
def test_no_proposal_without_clear_win(candidate: dict[str, Any]):
    assert propose_config_changes(_comparison(_run(1, 100), candidate)) == []


def test_no_proposal_for_non_synthetic_or_single_run():
    assert propose_config_changes({"backend": "real", "runs": [_run(1, 1), _run(4, 9)]}) == []
    assert propose_config_changes(_comparison(_run(1, 100))) == []


def test_report_round_trips_as_json(tmp_path):
    report = run_benchmark(BenchmarkConfig(max_steps=5), clock=FakeClock())
    path = tmp_path / "bench.json"
    write_report(report, path)
    assert json.loads(path.read_text(encoding="utf-8")) == report
