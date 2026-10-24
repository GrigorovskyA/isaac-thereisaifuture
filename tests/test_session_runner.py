"""Offline runner contracts. No game, Steam, desktop input or real training."""

import json
from contextlib import nullcontext
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from isaac_threrisaifuture import live
from isaac_threrisaifuture import session_runner as runner


@pytest.fixture
def plan(tmp_path):
    return runner.SessionPlan(
        tmp_path / "game",
        tmp_path / "game.log",
        tmp_path / "config.yaml",
        tmp_path / "runs",
        tmp_path / "session",
        "parent",
        20,
        120,
        1000,
        2,
        10**7,
    )


@pytest.mark.parametrize("seconds", [0, -1, float("nan"), float("inf"), 28800])
def test_invalid_session_budget(plan, seconds):
    with pytest.raises(ValueError):
        replace(plan, seconds=seconds)


@pytest.mark.parametrize("winerror", [5, 32, 33])
@pytest.mark.parametrize("persistent", [False, True])
def test_atomic_status_retry_keeps_old_complete_snapshot(
    tmp_path, monkeypatch, winerror, persistent
):
    from pathlib import Path

    path = tmp_path / "status.json"
    path.write_text('{"generation":0}')
    original = Path.replace
    clock = [0.0]
    attempts = []

    def sleep(seconds):
        clock[0] += seconds

    def replace_file(source, target):
        attempts.append(clock[0])
        if persistent or len(attempts) < 4:
            assert json.loads(path.read_text()) == {"generation": 0}
            error = PermissionError("Transient Windows sharing refusal")
            error.winerror = winerror
            raise error
        return original(source, target)

    monkeypatch.setattr(runner, "time", SimpleNamespace(monotonic=lambda: clock[0], sleep=sleep))
    monkeypatch.setattr(Path, "replace", replace_file)
    if persistent:
        with pytest.raises(PermissionError):
            runner.atomic_json(path, {"generation": 1})
        assert json.loads(path.read_text()) == {"generation": 0}
        assert 1 <= clock[0] < 1.02
    else:
        runner.atomic_json(path, {"generation": 1})
        assert json.loads(path.read_text()) == {"generation": 1}
        assert len(attempts) == 4
        assert not path.with_suffix(".tmp").exists()


def test_atomic_status_unrelated_permission_refusal_is_not_retried(tmp_path, monkeypatch):
    from pathlib import Path

    fail = Mock(side_effect=PermissionError("Not a Windows sharing failure"))
    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(PermissionError):
        runner.atomic_json(tmp_path / "status.json", {"value": 1})
    assert fail.call_count == 1


def test_atomic_status_survives_actual_windows_open_reader(tmp_path):
    import sys
    import threading

    if sys.platform != "win32":
        pytest.skip("Native Windows sharing regression")
    path = tmp_path / "status.json"
    path.write_text('{"generation":0}')
    held = path.open("rb")
    release = threading.Timer(0.15, held.close)
    release.start()
    try:
        runner.atomic_json(path, {"generation": 1})
    finally:
        release.join()
        held.close()
    assert json.loads(path.read_text()) == {"generation": 1}


def time_only(plan, **kwargs):
    return replace(
        plan,
        **{
            "time_budget_only": True,
            "steps": runner.TIME_ONLY_STEPS,
            "max_restarts": runner.TIME_ONLY_RESTARTS,
            **kwargs,
        },
    )


@pytest.mark.parametrize("seconds", [300, 1800, 3600, 14400])
def test_time_only_count_sentinels_cannot_bind_supported_windows(plan, tmp_path, seconds):
    selected = time_only(plan, seconds=seconds)
    # Native restart dispatch is paced at least four seconds apart. Even one
    # decision each 30Hz game update cannot approach the cumulative step ceiling.
    assert selected.max_restarts > seconds // 4 + 1
    assert selected.steps - 7680 > seconds * 30
    (tmp_path / runner.MOD_DIRECTORY).mkdir(parents=True)
    path = live.write_training_approval(
        tmp_path, hours=seconds / 3600, now=1000, max_restarts=selected.max_restarts
    )
    approval = json.loads(path.read_text())
    assert approval["max_restarts"] == selected.max_restarts
    assert approval["expires_at"] == 1000 + seconds


@pytest.mark.parametrize(
    "change",
    [
        {"seconds": 14401},
        {"steps": 12288},
        {"max_restarts": 2},
    ],
)
def test_time_only_rejects_binding_counts_or_unsupported_windows(plan, change):
    with pytest.raises(ValueError, match="Time-only"):
        time_only(plan, **change)


@pytest.mark.parametrize("steps,minutes", [(12288, 240), (10**9, 10)])
def test_time_only_preflight_refuses_hidden_config_limits(plan, monkeypatch, steps, minutes):
    runtime = runner.NativeRuntime(time_only(plan, seconds=1800))
    monkeypatch.setattr(runner, "preflight", Mock())
    monkeypatch.setattr(
        runner,
        "socket",
        SimpleNamespace(socket=lambda: nullcontext(SimpleNamespace(bind=lambda _: None))),
    )
    monkeypatch.setattr(
        runner,
        "load_training_config",
        lambda _: (
            SimpleNamespace(
                status="test",
                budget=SimpleNamespace(total_timesteps=steps, wall_time_minutes=minutes),
            ),
            "config",
        ),
    )
    identity = Mock()
    monkeypatch.setattr(runtime, "identity", identity)
    with pytest.raises(ValueError, match="hidden count or shorter time"):
        runtime.preflight()
    identity.assert_not_called()
    assert runtime.process is None and not runtime.approval.exists()


def test_time_only_cli_derives_limits_without_game_access(plan, monkeypatch):
    import sys

    args = ["runner"]
    for name in ("game", "game_log", "config", "run_root", "output"):
        args += ["--" + name.replace("_", "-"), str(getattr(plan, name))]
    args += [
        "--parent-id",
        "parent",
        "--seed",
        "20",
        "--seconds",
        "1800",
        "--disk-bytes",
        "10000000",
        "--time-budget-only",
    ]
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setattr(runner, "os", SimpleNamespace(name="nt"))
    run = Mock(return_value={"state": "completed"})
    monkeypatch.setattr(runner, "supervise", run)
    with pytest.raises(SystemExit) as result:
        runner.main()
    assert result.value.code == 0
    chosen = run.call_args.args[0]
    assert chosen.time_budget_only
    assert chosen.max_restarts > 1800 // 4


@pytest.mark.parametrize("fraction,delay", [(0.01, 0), (0.999, 0.7), (0.5, 35.95), (0.99, 58)])
def test_actual_approval_writer_never_exceeds_deadline(tmp_path, fraction, delay):
    game = tmp_path / "game"
    (game / runner.MOD_DIRECTORY).mkdir(parents=True)
    clock = runner.SessionClock(100, 1000 + fraction, 220)
    now, wall = 100 + delay, 1000 + fraction + delay
    seconds, expiry_limit = clock.lease(now, wall)
    path = live.write_training_approval(game, hours=seconds / 3600, now=wall, max_restarts=2)
    assert json.loads(path.read_text())["expires_at"] <= expiry_limit
    assert expiry_limit == pytest.approx(clock.wall_started + 120)


def test_startup_delay_cannot_renew_lease():
    with pytest.raises(ValueError, match="Insufficient"):
        runner.SessionClock(0, 1000, 120).lease(61, 1061)


def test_fixed_deadline_aligns_with_full_lease_window(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner, "time", SimpleNamespace(monotonic=lambda: 100.25, time=lambda: 1000.999)
    )
    clock = runner.SessionClock.start(120)
    assert 119 < clock.deadline - clock.started <= 120
    seconds, limit = clock.lease(120.25, clock.wall_started + 20)
    game = tmp_path / "game"
    (game / runner.MOD_DIRECTORY).mkdir(parents=True)
    path = live.write_training_approval(
        game, hours=(seconds + 0.5) / 3600, now=clock.wall_started + 20, max_restarts=2
    )
    assert json.loads(path.read_text())["expires_at"] == limit == 1120


def test_status_requires_recent_training_evidence():
    progress = runner.Progress(runner.SessionClock(100, 1000, 220))
    progress.event({"monotonic": 101, "event": "listening"})
    assert progress.snapshot(102)["state"] == "startup"
    progress.event(
        {
            "monotonic": 103,
            "event": "training",
            "data": {"seed": 7},
        }
    )
    assert progress.snapshot(104)["state"] == "training"
    assert progress.snapshot(103 + runner.IDLE_SECONDS)["state"] == "training"
    status = progress.snapshot(115 + runner.IDLE_SECONDS)
    assert status["state"] == "waiting"
    assert status["last_checkpoint_update_at"] is None
    assert status["phase_seconds"]["training"] == runner.IDLE_SECONDS
    assert status["phase_seconds"]["waiting"] == 12


def test_training_and_checkpointing_are_distinct():
    progress = runner.Progress(runner.SessionClock(0, 1000, 120))
    for now, event, data, phase in [
        (1, "training", {"seed": 7}, "training"),
        (2, "checkpointing", {"timesteps": 256}, "checkpointing"),
        (3, "checkpoint_completed", {"id": "new"}, "training"),
    ]:
        progress.event({"monotonic": now, "event": event, "data": data})
        assert progress.snapshot(now)["state"] == phase
    assert progress.latest is None  # event alone cannot verify a complete checkpoint


def test_tail_retains_partial_line_and_rejects_malformed(tmp_path):
    path = tmp_path / "events"
    tail = runner.EventTail(path)
    path.write_bytes(b'{"event": "a"}\n{"event":')
    assert tail.read() == [{"event": "a"}]
    with path.open("ab") as stream:
        stream.write(b' "b"}\n')
    assert tail.read() == [{"event": "b"}]
    assert tail.read() == []
    with path.open("ab") as stream:
        stream.write(b"bad\n")
    with pytest.raises(ValueError):
        tail.read()


class FakeRuntime(runner.NativeRuntime):
    def __init__(self, plan, clock, mode="early"):
        super().__init__(plan)
        self.clock, self.mode = clock, mode
        self.calls = []
        self.config_hash = "hash"
        self.started = False
        self.code = None
        self.updated = False

    def event(self, event, data=None):
        with (self.plan.output / "events.jsonl").open("a") as stream:
            stream.write(
                json.dumps(
                    {
                        "event": event,
                        "data": data,
                        "monotonic": self.clock.now,
                        "time": self.clock.now + 1000,
                    }
                )
                + "\n"
            )

    def identity(self):
        if self.mode == "bad-checkpoint" and self.updated:
            raise ValueError("partial checkpoint")
        return {"id": "new" if self.updated else "parent", "steps": 512 if self.updated else 256}

    def preflight(self):
        self.calls.append("preflight")
        if self.mode == "refused":
            raise ValueError("Foreign game or invalid parent")
        return self.identity()

    def hold_sleep(self):
        self.calls.append("hold")

    def grant(self, seconds, wall_now):
        self.calls.append("grant")
        self.approval.parent.mkdir(parents=True)
        self.approval.write_text(json.dumps({"expires_at": int(wall_now) + seconds}))
        return runner.digest(self.approval)

    def start(self):
        self.started = True
        self.calls.append("start")
        self.event("listening")
        if self.mode == "malformed":
            with (self.plan.output / "events.jsonl").open("a") as stream:
                stream.write("bad-json\n")

    def enter(self, deadline):
        self.calls.append("enter")
        assert deadline == 220
        if self.mode == "focus":
            raise ValueError("Menu focus refused")
        self.event("training", {"seed": 7})

    def poll(self):
        if self.code is not None or not self.started:
            return self.code
        if self.mode == "silent-checkpoint":
            self.updated = True
            self.event("budget", "Navigation budget exhausted after 20 transitions")
            self.code = 0
        elif self.mode in (
            "early",
            "cleanup",
            "changed",
            "checkpoint",
            "bad-checkpoint",
            "cleanup-delay",
        ):
            if self.mode in ("checkpoint", "bad-checkpoint"):
                self.updated = True
                self.event("checkpoint_completed", {"id": "new"})
            if self.mode == "changed":
                self.approval.write_text("changed foreign approval")
            self.event(
                "budget",
                "Live wall-time budget exhausted"
                if self.mode == "cleanup-delay"
                else "Navigation budget exhausted after 20 transitions",
            )
            self.code = 0
        elif self.mode == "cancel":
            (self.plan.output / "stop.request").touch()
        elif self.mode == "timer-margin" and self.clock.now >= 220 - runner.STOP_MARGIN_SECONDS:
            self.event("budget", "Live wall-time budget exhausted")
            self.code = 0
        elif self.mode == "timer" and self.clock.now >= 220:
            self.event("budget", "Live wall-time budget exhausted")
            self.code = 0
        return self.code

    def size(self):
        return 100

    def stop_worker(self):
        self.calls.append("stop_worker")
        self.code = 0 if self.started else None

    def close_game(self):
        self.calls.append("close_game")
        if self.mode == "cleanup-delay":
            self.clock.now += 130
        if self.mode == "cleanup":
            raise OSError("Normal close refused")

    def release_sleep(self):
        self.calls.append("release")

    def verify_frozen(self):
        self.calls.append("verify")


@pytest.fixture
def clock(monkeypatch):
    clock = SimpleNamespace(now=100.0)

    def sleep(_):
        clock.now += 10

    monkeypatch.setattr(
        runner,
        "time",
        SimpleNamespace(
            monotonic=lambda: clock.now,
            time=lambda: clock.now + 1000,
            sleep=sleep,
        ),
    )
    return clock


@pytest.mark.parametrize(
    "mode,state",
    [
        ("early", "early_stop"),
        ("timer", "completed"),
        ("timer-margin", "completed"),
        ("cancel", "user_cancelled"),
        ("focus", "fault"),
        ("refused", "fault"),
        ("cleanup", "fault"),
        ("stuck", "fault"),
        ("changed", "fault"),
        ("malformed", "fault"),
        ("cleanup-delay", "early_stop"),
    ],
)
def test_terminal_status_and_isolated_owned_cleanup(plan, clock, mode, state):
    runtime = FakeRuntime(plan, clock, mode)
    result = runner.supervise(plan, runtime)
    assert result["state"] == state
    assert json.loads((plan.output / "status.json").read_text()) == result
    assert json.loads((plan.output / "result.json").read_text()) == result
    assert runtime.calls.count("start") <= 1
    assert all(call in runtime.calls for call in ("stop_worker", "close_game", "release", "verify"))
    if mode == "early":
        assert result["reason"] == "Navigation budget exhausted after 20 transitions"
    if mode == "refused":
        assert "grant" not in runtime.calls and "enter" not in runtime.calls
    elif mode == "changed":
        assert runtime.approval.read_text() == "changed foreign approval"
        assert any("Approval changed" in error for error in result["cleanup_errors"])
    else:
        assert not runtime.approval.exists()


@pytest.mark.parametrize("mode,latest", [("checkpoint", "new"), ("bad-checkpoint", "parent")])
def test_completed_checkpoint_readback_and_concurrent_read_failure(plan, clock, mode, latest):
    result = runner.supervise(plan, FakeRuntime(plan, clock, mode))
    assert result["latest_checkpoint"]["id"] == latest
    if latest == "parent":
        assert "partial checkpoint" in result["checkpoint_note"]
        assert result["last_checkpoint_update_at"] is None
    else:
        assert result["last_checkpoint_update_at"] is not None


def test_final_readback_finds_committed_checkpoint_without_worker_event(plan, clock):
    result = runner.supervise(plan, FakeRuntime(plan, clock, "silent-checkpoint"))
    assert result["latest_checkpoint"]["id"] == "new"
    assert result["last_checkpoint_update_at"] is not None
    assert "final readback" in result["checkpoint_note"]
    assert result["state"] == "early_stop"


def test_optional_metrics_failure_cannot_erase_final_status(plan, clock, monkeypatch):
    original = runner.atomic_json

    def write(path, data):
        if path.name == "metrics.json":
            raise ValueError("optional metrics unavailable")
        original(path, data)

    monkeypatch.setattr(runner, "atomic_json", write)
    result = runner.supervise(plan, FakeRuntime(plan, clock))
    assert json.loads((plan.output / "status.json").read_text()) == result
    assert result["state"] == "early_stop"


def test_native_preflight_refuses_foreign_approval_before_parent_read(plan, monkeypatch):
    runtime = runner.NativeRuntime(plan)
    runtime.approval.parent.mkdir(parents=True)
    runtime.approval.write_text("foreign")
    monkeypatch.setattr(runner, "preflight", Mock())
    identity = Mock()
    monkeypatch.setattr(runtime, "identity", identity)
    with pytest.raises(ValueError, match="Foreign approval"):
        runtime.preflight()
    identity.assert_not_called()
    assert runtime.approval.read_text() == "foreign"


@pytest.mark.parametrize("parent", [None, "wrong"])
def test_native_preflight_has_no_missing_or_different_parent_fallback(plan, monkeypatch, parent):
    runtime = runner.NativeRuntime(plan)
    monkeypatch.setattr(runner, "preflight", Mock())
    monkeypatch.setattr(
        runner,
        "socket",
        SimpleNamespace(
            socket=lambda: nullcontext(SimpleNamespace(bind=lambda _: None)),
        ),
    )
    monkeypatch.setattr(
        runner,
        "load_training_config",
        lambda _: (
            SimpleNamespace(status="test"),
            "expected-config-hash",
        ),
    )
    if parent is None:
        identity = Mock(side_effect=ValueError("Missing compatible parent"))
    else:
        identity = Mock(return_value={"id": parent})
    monkeypatch.setattr(runtime, "identity", identity)
    with pytest.raises(ValueError, match="parent"):
        runtime.preflight()
    assert runtime.config_hash == "expected-config-hash"
    assert not runtime.approval.exists()
    assert runtime.process is None and runtime.menu is None


def test_live_stop_signal_prevents_command(tmp_path):
    stop = tmp_path / "stop"
    stop.touch()
    client = Mock()
    backend = live.LiveBackend(client, stop_file=stop)
    with pytest.raises(live.LiveSessionCancelled, match="cancellation"):
        backend._check_budget()
    client.command.assert_not_called()


def test_deadline_stop_signal_is_not_mislabeled_as_user_cancel(tmp_path):
    stop = tmp_path / "stop"
    stop.touch()
    backend = live.LiveBackend(Mock(), run_deadline=0, stop_file=stop)
    with pytest.raises(live.LiveBudgetExpired) as caught:
        backend._check_budget()
    assert not isinstance(caught.value, live.LiveSessionCancelled)
    assert "wall-time" in str(caught.value)


def test_nonfinite_live_deadline_refused(tmp_path):
    with pytest.raises(ValueError, match="finite"):
        live.LiveRunOptions("train", tmp_path, session_deadline=float("nan"))


def test_menu_stop_signal_raises_before_more_native_log_or_keys(tmp_path):
    path = tmp_path / "game.log"
    path.write_text("old log")
    stop = tmp_path / "stop"
    journal = runner.StopAwareGameLog(path, stop)
    stop.touch()
    with pytest.raises(KeyboardInterrupt):
        journal.read()


def test_live_trainer_receives_fixed_deadline_and_cancel_does_not_save(tmp_path, monkeypatch):
    received = {}

    def train(*args, **kwargs):
        received.update(kwargs)
        raise live.LiveSessionCancelled("User cancellation requested")

    monkeypatch.setattr("isaac_threrisaifuture.training.train", train)
    records = []
    live._train_run(
        None,
        live.LiveRunOptions(
            "train",
            tmp_path,
            session_deadline=123.5,
            stop_file=tmp_path / "stop",
        ),
        lambda *row: records.append(row),
        lambda _: None,
    )
    assert received["run_deadline"] == 123.5
    assert callable(received["on_progress"])
    assert records[-1][0] == "budget"
    assert "cancellation" in records[-1][1] and "no new checkpoint" in records[-1][1]
    assert not list(tmp_path.rglob("latest.txt"))


def test_owned_worker_command_is_importable_module(plan, monkeypatch):
    runtime = runner.NativeRuntime(plan)
    plan.output.mkdir()
    popen = Mock()
    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    runtime.start()
    assert popen.call_args.args[0][2:4] == ["-m", "isaac_threrisaifuture.session_runner"]
    runtime.console.close()


def test_worker_stops_learner_before_the_lease_expires(tmp_path, monkeypatch):
    output = tmp_path / "session"
    output.mkdir()
    payload = {
        "options": {
            "output": str(output),
            "run_root": str(tmp_path),
            "config": "c.yaml",
            "seed": 1,
            "steps": 512,
            "seconds": 600,
        },
        "clock": {"deadline": 1000.0},
    }
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload))
    received = {}
    monkeypatch.setattr(runner, "time", SimpleNamespace(monotonic=lambda: 10.0, time=lambda: 0.0))
    monkeypatch.setattr(runner, "run_live", lambda options, on_record: received.update(o=options))
    runner.worker(path)
    assert received["o"].session_deadline == 1000.0 - runner.STOP_MARGIN_SECONDS


# --- frozen evaluation sessions ------------------------------------------------------------


@pytest.fixture
def eval_plan(plan, tmp_path):
    return replace(
        plan,
        run_root=tmp_path / "eval" / "t1",
        parent_id="",
        steps=runner.TIME_ONLY_STEPS,
        max_restarts=0,
        resume=False,
        evaluation=runner.EvaluationSpec("checkpoint", tmp_path / "train/checkpoints/t1"),
    )


class EvalRuntime(FakeRuntime):
    """An evaluation has no parent and no checkpoint progress."""

    def preflight(self):
        self.calls.append("preflight")

    def identity(self):
        raise AssertionError("evaluation must never read checkpoint progress")

    def enter(self, deadline):
        self.calls.append("enter")
        self.event("evaluation", {"policy": "checkpoint"})


@pytest.mark.parametrize(
    "mode,state",
    [("timer", "completed"), ("timer-margin", "completed"), ("early", "early_stop")],
)
def test_evaluation_deadline_stop_is_completed_without_checkpoint_progress(
    eval_plan, clock, mode, state
):
    result = runner.supervise(eval_plan, EvalRuntime(eval_plan, clock, mode))
    assert result["state"] == state
    assert result["latest_checkpoint"] is None and result["checkpoint_note"] is None
    assert result["fault"] is None and result["cleanup_errors"] == []
    saved = json.loads((eval_plan.output / "plan.json").read_text())
    assert saved["parent"] is None
    assert saved["options"]["evaluation"]["policy"] == "checkpoint"
    assert saved["count_limit_mode"] == "nonbinding_schema_sentinels"


@pytest.mark.parametrize(
    "change",
    [{"resume": True}, {"parent_id": "p"}, {"max_restarts": 5}, {"steps": 100}, {"forever": True}],
)
def test_evaluation_plan_refuses_training_semantics(eval_plan, change):
    with pytest.raises(ValueError, match="Evaluation sessions"):
        replace(eval_plan, **change)


def test_evaluation_spec_validates_checkpoint(tmp_path):
    with pytest.raises(ValueError):
        runner.EvaluationSpec("checkpoint")
    with pytest.raises(ValueError):
        runner.EvaluationSpec("random", tmp_path)


def test_evaluation_root_guard(tmp_path):
    train = tmp_path / "pure-v4"
    checkpoint = train / "seed-1" / "checkpoints" / "t1"
    checkpoint.mkdir(parents=True)
    spec = runner.EvaluationSpec("checkpoint", checkpoint)
    runner.validate_evaluation_root(tmp_path / "eval" / "t1", spec)
    for root in (train, train / "seed-1", train / "eval", checkpoint):
        with pytest.raises(ValueError):
            runner.validate_evaluation_root(root, spec)
    random = runner.EvaluationSpec("random")
    with pytest.raises(ValueError, match="contains checkpoints"):
        runner.validate_evaluation_root(train, random)
    used = tmp_path / "eval" / "used"
    (used / "metrics").mkdir(parents=True)
    (used / "metrics" / "episodes.csv").write_text("header\n")
    with pytest.raises(ValueError, match="already has episodes"):
        runner.validate_evaluation_root(used, random)


def test_worker_passes_evaluate_mode_and_checkpoint(tmp_path, monkeypatch):
    output = tmp_path / "session"
    output.mkdir()
    checkpoint = tmp_path / "train" / "checkpoints" / "t1"
    payload = {
        "options": {
            "output": str(output), "run_root": str(tmp_path / "eval"), "config": "c.yaml",
            "seed": 1, "steps": runner.TIME_ONLY_STEPS, "seconds": 600, "resume": False,
            "evaluation": {"policy": "checkpoint", "checkpoint": str(checkpoint)},
        },
        "clock": {"deadline": 1000.0},
    }  # fmt: skip
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload))
    received = {}
    monkeypatch.setattr(runner, "time", SimpleNamespace(monotonic=lambda: 10.0, time=lambda: 0.0))
    monkeypatch.setattr(runner, "run_live", lambda options, on_record: received.update(o=options))
    runner.worker(path)
    chosen = received["o"]
    assert chosen.mode == "evaluate" and chosen.eval_policy == "checkpoint"
    assert chosen.eval_checkpoint == checkpoint and not chosen.resume
    assert chosen.session_deadline == 1000.0 - runner.STOP_MARGIN_SECONDS
    assert chosen.out_dir == tmp_path / "eval"


@pytest.fixture
def cli(tmp_path, monkeypatch):
    """Run main() with fake Windows args; returns (plan, exit code, stderr)."""
    import sys

    monkeypatch.setattr(runner, "os", SimpleNamespace(name="nt"))
    run = Mock(return_value={"state": "completed"})
    monkeypatch.setattr(runner, "supervise", run)
    config = runner.PURE_CONFIG

    def call(*extra, drop=(), root=tmp_path / "eval" / "t1"):
        args = ["runner", "--game", str(tmp_path / "game"), "--game-log", str(tmp_path / "log")]
        named = {"config": config, "run-root": root, "output": tmp_path / "out",
                 "seconds": 1800}  # fmt: skip
        for name, value in named.items():
            if name not in drop:
                args += [f"--{name}", str(value)]
        monkeypatch.setattr(sys, "argv", [*args, *map(str, extra)])
        run.reset_mock()
        try:
            runner.main()
        except SystemExit as exit_:
            return run, exit_.code
        raise AssertionError("main did not exit")

    return call


def test_cli_evaluate_random_derives_everything(cli):
    run, code = cli("--evaluate", "random")
    chosen = run.call_args.args[0]
    assert code == 0 and chosen.evaluation == runner.EvaluationSpec("random")
    config, _ = runner.load_training_config(runner.PURE_CONFIG)
    assert chosen.seed == config.seed and chosen.parent_id == "" and not chosen.resume
    assert chosen.max_restarts == 0 and chosen.steps == runner.TIME_ONLY_STEPS
    assert chosen.disk_bytes == config.budget.disk_limit_mb * 1_000_000


def test_cli_evaluate_checkpoint_passes_exact_directory(cli, tmp_path):
    checkpoint = tmp_path / "train" / "seed-1" / "checkpoints" / "t102400"
    run, code = cli("--evaluate", "checkpoint", "--checkpoint", checkpoint)
    chosen = run.call_args.args[0]
    assert code == 0 and chosen.evaluation.checkpoint == checkpoint.resolve()


def test_cli_evaluate_refusals(cli, tmp_path):
    train = tmp_path / "train"
    checkpoint = train / "seed-1" / "checkpoints" / "t1"
    checkpoint.mkdir(parents=True)
    refused = [
        (["--evaluate", "random", "--forever"], {}),
        (["--forever", "--checkpoint", checkpoint], {}),
        (["--evaluate", "checkpoint"], {}),  # needs --checkpoint
        (["--evaluate", "random", "--checkpoint", checkpoint], {}),
        (["--checkpoint", checkpoint], {}),  # without --evaluate
        (["--evaluate", "checkpoint", "--checkpoint", checkpoint], {"root": train}),
        (["--evaluate", "checkpoint", "--checkpoint", checkpoint], {"root": train / "eval"}),
        (["--evaluate", "random"], {"root": train}),  # holds a checkpoints folder
        (["--evaluate", "random", "--parent-id", "x"], {}),
        (["--evaluate", "random", "--steps", "5"], {}),
        (["--evaluate", "random", "--time-budget-only"], {}),
        (["--evaluate", "random"], {"drop": ("seconds",)}),
    ]
    for extra, kwargs in refused:
        run, code = cli(*extra, **kwargs)
        assert code == 2, extra
        run.assert_not_called()
