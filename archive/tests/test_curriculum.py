import dataclasses

import numpy as np
import pytest

from isaac_threrisaifuture.baselines import RandomPolicy
from isaac_threrisaifuture.curriculum import (
    DEFAULT_CURRICULUM,
    LeakageCheckedPolicy,
    OracleLeakageError,
    RegressionTolerance,
    ResultsLog,
    Stage,
    compare_to_baselines,
    regression_gate,
    should_advance,
)
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.evaluation import EpisodeRecord, Metrics, summarize


def metrics(cleared: int, n: int, damage: float = 2.0) -> Metrics:
    records = [
        EpisodeRecord("s", i, "cleared" if i < cleared else "death", damage) for i in range(n)
    ]
    return summarize(records)


def test_advancement_uses_ci_lower_bound_and_validation_only() -> None:
    stage = Stage("s", (1,), 0.6)
    assert should_advance(stage, metrics(190, 200))
    assert not should_advance(stage, metrics(13, 20))  # small sample
    assert not should_advance(stage, metrics(130, 200))  # CI lower bound below threshold
    with pytest.raises(ValueError):
        should_advance(stage, metrics(190, 200), split="test")


def test_curriculum_hash_is_stable_and_stages_never_expose_test() -> None:
    assert DEFAULT_CURRICULUM.hash == DEFAULT_CURRICULUM.hash
    for stage in DEFAULT_CURRICULUM.stages:
        assert all(
            s.split != "test" for s in stage.scenarios("train") + stage.scenarios("validation")
        )
        with pytest.raises(ValueError):
            stage.scenarios("test")
    assert DEFAULT_CURRICULUM.old_task_difficulties(2) == (1, 2)


def test_tolerance_is_immutable_and_hashed() -> None:
    tol = RegressionTolerance()
    with pytest.raises(dataclasses.FrozenInstanceError):
        tol.max_clear_rate_drop = 0.5  # type: ignore[misc]
    assert tol.hash != RegressionTolerance(max_clear_rate_drop=0.2).hash


def test_regression_gate() -> None:
    tol = RegressionTolerance()
    snap = metrics(160, 200)
    assert regression_gate(snap, metrics(158, 200), tol).passed
    bad = regression_gate(snap, metrics(100, 200), tol)
    assert not bad.passed and bad.tolerance_hash == tol.hash
    assert not regression_gate(snap, metrics(160, 200, damage=5.0), tol).passed
    assert not regression_gate(snap, metrics(8, 10), tol).passed  # too few episodes


def test_baseline_comparison_reports_scripted_loss() -> None:
    cmp = compare_to_baselines(metrics(120, 200), metrics(20, 200), metrics(170, 200))
    assert cmp.beats_random and not cmp.beats_scripted
    assert cmp.clear_rate_vs_scripted < 0


def test_results_log_retains_failures_and_detects_tampering(tmp_path) -> None:
    log = ResultsLog(tmp_path / "log.jsonl")
    log.append({"stage": "a", "passed": False})
    log.append({"stage": "a", "passed": True})
    assert [r["entry"]["passed"] for r in log.read()] == [False, True]
    assert not hasattr(log, "delete") and not hasattr(log, "clear")
    lines = (tmp_path / "log.jsonl").read_text().splitlines()
    (tmp_path / "log.jsonl").write_text(lines[1] + "\n")  # dropped the failure
    with pytest.raises(ValueError):
        log.read()


def test_leakage_check_rejects_wrong_size() -> None:
    policy = LeakageCheckedPolicy(RandomPolicy())
    policy.reset(1)
    policy.act(np.zeros(OBSERVATION_SIZE, dtype=np.float32))
    with pytest.raises(OracleLeakageError):
        policy.act(np.zeros(OBSERVATION_SIZE + 3, dtype=np.float32))
