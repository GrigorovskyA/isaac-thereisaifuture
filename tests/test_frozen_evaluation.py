"""OFFLINE tests for frozen evaluation (live mode `evaluate`). The synthetic room proves
plumbing only: no game, no learning, no checkpoint writes."""

import csv
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from test_pure_training import run, synthetic_env, write_config

from isaac_threrisaifuture import checkpoint_policy, live
from isaac_threrisaifuture import session_runner as runner
from isaac_threrisaifuture.checkpoint_policy import CheckpointPolicy
from isaac_threrisaifuture.checkpoints import CheckpointError, latest_checkpoint_dir


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}


@pytest.fixture(scope="module")
def trained(tmp_path_factory: pytest.TempPathFactory) -> SimpleNamespace:
    """A tiny real pure checkpoint (lstm 16) and the config that produced it."""
    base = tmp_path_factory.mktemp("frozen-eval")
    config = write_config(base / "pure.yaml", watchdog={"stall_seconds": 45.0})
    run(config, base / "train", 64)
    directory = latest_checkpoint_dir(base / "train/checkpoints")
    return SimpleNamespace(config=config, checkpoint=directory, root=base / "train")


@pytest.fixture
def seen(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}

    def fake_env(_client: Any, **options: Any) -> Any:
        kwargs.update(options)
        return synthetic_env()

    monkeypatch.setattr(live, "make_live_env", fake_env)
    return kwargs


def options(out: Path, config: Path, **changes: Any) -> live.LiveRunOptions:
    values: dict[str, Any] = {
        "mode": "evaluate", "out_dir": out, "config_path": config, "minutes": 5,
        "eval_policy": "random", "session_deadline": time.monotonic() + 0.4, "seed": 3,
    }  # fmt: skip
    return live.LiveRunOptions(**{**values, **changes})


@pytest.mark.parametrize(
    "changes",
    [
        {"eval_policy": None},
        {"eval_policy": "checkpoint"},  # no checkpoint named
        {"eval_policy": "random", "eval_checkpoint": Path("c")},
        {"eval_policy": "random-prior", "eval_checkpoint": Path("c")},
        {"resume": True},
    ],
)
def test_evaluate_options_validate_combinations(tmp_path, changes):
    with pytest.raises(ValueError):
        live.LiveRunOptions(mode="evaluate", out_dir=tmp_path, **changes)


def test_random_prior_evaluation_names_policy_and_uses_config_prior(
    tmp_path, seen, trained, monkeypatch
):
    from isaac_threrisaifuture import baselines
    from isaac_threrisaifuture.training import load_training_config

    records: list[tuple[str, Any]] = []
    created: list[float] = []

    class Spy(baselines.RandomPriorPolicy):
        def __init__(self, none_probability: float) -> None:
            created.append(none_probability)
            super().__init__(none_probability)

    monkeypatch.setattr(baselines, "RandomPriorPolicy", Spy)
    out = tmp_path / "eval"
    with pytest.raises(live.LiveBudgetExpired):
        live._evaluate_run(
            None,  # type: ignore[arg-type]
            options(out, trained.config, eval_policy="random-prior"),
            lambda *row: records.append(row),
            lambda _: None,
        )
    config, _ = load_training_config(trained.config)
    assert created == [config.use_head_initial_none_probability]
    assert records[0][1]["policy"] == "random-prior" and records[0][1]["checkpoint_id"] is None
    assert records[-1][0] == "evaluation_result" and records[-1][1]["episodes"] >= 1
    assert not list(out.rglob("checkpoints"))


def test_evaluate_options_accept_valid_and_train_refuses_eval_fields(tmp_path):
    live.LiveRunOptions("evaluate", tmp_path, eval_policy="random")
    live.LiveRunOptions("evaluate", tmp_path, eval_policy="random-prior")
    live.LiveRunOptions(
        "evaluate", tmp_path, eval_policy="checkpoint", eval_checkpoint=tmp_path / "t1"
    )
    for mode in ("train", "random"):
        with pytest.raises(ValueError):
            live.LiveRunOptions(mode, tmp_path, eval_policy="random")  # type: ignore[arg-type]


def test_random_evaluation_writes_episodes_only_and_stops_on_deadline(tmp_path, seen, trained):
    records: list[tuple[str, Any]] = []
    out = tmp_path / "eval"
    with pytest.raises(live.LiveBudgetExpired):
        live._evaluate_run(
            None,  # type: ignore[arg-type]
            options(out, trained.config),
            lambda *row: records.append(row),
            lambda _: None,
        )
    # Built like the pure training env.
    assert seen["action_repeat"] == 6 and seen["stall_seconds"] == 45.0
    assert seen["reward_version"] == 9 and seen["max_consecutive_faults"] >= 1
    assert seen["max_faults"] > 1000 and seen["run_deadline"] is not None
    names = [name for name, _ in records]
    assert names[0] == "evaluation" and names[-1] == "evaluation_result"
    assert records[0][1]["policy"] == "random" and records[0][1]["checkpoint_id"] is None
    result = records[-1][1]
    rows = list(csv.DictReader((out / "metrics/episodes.csv").open(encoding="utf-8")))
    assert result["episodes"] >= 1 and len(rows) >= result["episodes"]
    assert result["steps"] >= result["episodes"]
    assert not list(out.rglob("checkpoints")) and not list(out.rglob("latest.txt"))
    assert not list(out.glob("seed-*")) and not (out / "metrics/train.csv").exists()


def test_checkpoint_evaluation_is_frozen_stochastic_and_resets_per_episode(
    tmp_path, seen, trained, monkeypatch
):
    resets: list[int] = []
    sampling: list[bool] = []
    original_reset, original_act = CheckpointPolicy.reset, CheckpointPolicy.act

    def reset(self: CheckpointPolicy, seed: int) -> None:
        resets.append(seed)
        original_reset(self, seed)

    def act(self: CheckpointPolicy, observation: Any) -> Any:
        sampling.append(self.deterministic)
        return original_act(self, observation)

    monkeypatch.setattr(checkpoint_policy.CheckpointPolicy, "reset", reset)
    monkeypatch.setattr(checkpoint_policy.CheckpointPolicy, "act", act)
    before = snapshot(trained.root)
    records: list[tuple[str, Any]] = []
    out = tmp_path / "eval"
    with pytest.raises(live.LiveBudgetExpired):
        live._evaluate_run(
            None,  # type: ignore[arg-type]
            options(
                out, trained.config, eval_policy="checkpoint", eval_checkpoint=trained.checkpoint
            ),
            lambda *row: records.append(row),
            lambda _: None,
        )
    start, final = records[0][1], records[-1][1]
    assert start["policy"] == "checkpoint" and start["checkpoint_id"] == trained.checkpoint.name
    assert start["timesteps"] == 64 and start["config_hash"]
    assert sampling and not any(sampling)  # stochastic, as in training
    assert len(resets) == final["episodes"] + 1  # once at start, once per ended episode
    assert resets[:2] == [3, 4]  # fixed seed, advancing per episode
    assert snapshot(trained.root) == before  # lineage untouched
    assert not list(out.rglob("checkpoints"))


def test_checkpoint_of_another_config_is_refused_before_any_step(tmp_path, seen, trained):
    other = write_config(tmp_path / "other.yaml", contract={"lstm_hidden_size": 32})
    with pytest.raises(CheckpointError):
        live._evaluate_run(
            None,  # type: ignore[arg-type]
            options(
                tmp_path / "eval", other, eval_policy="checkpoint",
                eval_checkpoint=trained.checkpoint,
            ),
            lambda *_: None,
            lambda _: None,
        )  # fmt: skip
    assert not seen  # the env was never built
    assert not (tmp_path / "eval/metrics").exists()


def test_changed_checkpoint_is_a_fault_at_the_end(tmp_path, seen, trained, monkeypatch):
    copy = tmp_path / "copy" / trained.checkpoint.name
    import shutil

    shutil.copytree(trained.checkpoint, copy)
    original = CheckpointPolicy.act

    def tamper(self: CheckpointPolicy, observation: Any) -> Any:
        (copy / "manifest.json").write_text((copy / "manifest.json").read_text() + " ")
        return original(self, observation)

    monkeypatch.setattr(CheckpointPolicy, "act", tamper)
    with pytest.raises(CheckpointError, match="changed after loading"):
        live._evaluate_run(
            None,  # type: ignore[arg-type]
            options(
                tmp_path / "eval", trained.config, eval_policy="checkpoint", eval_checkpoint=copy
            ),
            lambda *_: None,
            lambda _: None,
        )


def test_evaluation_requires_pure_config(tmp_path, seen):
    from test_pure_training import ARCHIVED

    old = next(ARCHIVED.glob("training-*.yaml"), None)
    if old is None:
        pytest.skip("no archived v1 config")
    with pytest.raises(ValueError, match="pure"):
        live._evaluate_run(None, options(tmp_path, old), lambda *_: None, lambda _: None)  # type: ignore[arg-type]


def test_native_preflight_for_evaluation_freezes_checkpoint_without_parent(
    tmp_path, trained, monkeypatch
):
    plan = runner.SessionPlan(
        tmp_path / "game", tmp_path / "game.log", trained.config, tmp_path / "eval",
        tmp_path / "out", "", 1, 600, runner.TIME_ONLY_STEPS, 0, 10**9, resume=False,
        evaluation=runner.EvaluationSpec("checkpoint", trained.checkpoint),
    )  # fmt: skip
    runtime = runner.NativeRuntime(plan)
    monkeypatch.setattr(runner, "preflight", Mock())
    from contextlib import nullcontext

    monkeypatch.setattr(
        runner,
        "socket",
        SimpleNamespace(socket=lambda: nullcontext(SimpleNamespace(bind=lambda _: None))),
    )
    assert runtime.preflight() is None
    assert all(str(f) in runtime.frozen for f in trained.checkpoint.iterdir())
    with pytest.raises(ValueError, match="no checkpoint progress"):
        runtime.identity()
    # A checkpoint of a different lineage is refused.
    bad = write_config(tmp_path / "bad.yaml", contract={"lstm_hidden_size": 32})
    with pytest.raises(CheckpointError, match="different training configuration"):
        runner.NativeRuntime(runner.SessionPlan(**{**plan.__dict__, "config": bad})).preflight()
