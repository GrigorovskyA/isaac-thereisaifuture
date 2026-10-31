"""Continue2 training sessions: one finite session, or `--forever` back-to-back sessions.

Explicit invocation only. Each session owns its worker and game and cleans up on exit.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from .checkpoints import CheckpointError, latest_checkpoint_dir, load_checkpoint
from .launcher import MOD_DIRECTORY, PROJECT_ROOT, game_running, preflight, request_steam_launch
from .live import (
    APPROVAL_NAME,
    LIVE_REWARD_CONTRACT,
    LiveRunOptions,
    run_live,
    write_training_approval,
)
from .menu_entry import FreshGameLog, continue_or_new_run_file2
from .training import (
    PURE_CONFIG,
    TEMPLATE_STATUS,
    PureTrainingConfig,
    TrainingConfig,
    load_training_config,
)
from .windows_menu import WindowsMenu

TIME_ONLY_STEPS = 1_000_000_000
IDLE_SECONDS = 180
TIME_ONLY_RESTARTS = 5000
TIME_ONLY_MAX_SECONDS = 4 * 3600
MAX_SESSION_SECONDS = 28740  # the 8 h Lua lease minus a minute of margin
# The learner stops this long before the approval expires. Lua checks the lease every
# frame and closes the connection as soon as it lapses, so a learner that stops exactly
# at the deadline loses the race and the planned rollover is recorded as a fault.
STOP_MARGIN_SECONDS = 15.0


def atomic_json(path: Path, data: Any) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False), encoding="utf-8")
    deadline = time.monotonic() + 1.0
    while True:
        try:
            temporary.replace(path)
            return
        except PermissionError as error:
            # Windows readers may briefly omit FILE_SHARE_DELETE. Keep the
            # previous complete snapshot visible while retrying the same bytes.
            if getattr(error, "winerror", None) not in (5, 32, 33):
                raise
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)


def status_json(path: Path, data: Any) -> bool:
    """Write a live status view; a reader that keeps the file open skips this write only."""
    try:
        atomic_json(path, data)
        return True
    except PermissionError as error:
        if getattr(error, "winerror", None) not in (5, 32, 33):
            raise
        return False


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class EvaluationSpec:
    """Frozen evaluation instead of training: one exact checkpoint, or a random policy."""

    policy: Literal["checkpoint", "random", "random-prior"]
    checkpoint: Path | None = None

    def __post_init__(self) -> None:
        if self.policy == "checkpoint":
            if self.checkpoint is None:
                raise ValueError("Checkpoint evaluation needs an exact checkpoint directory")
        elif self.policy in ("random", "random-prior"):
            if self.checkpoint is not None:
                raise ValueError(f"The {self.policy} policy takes no checkpoint")
        else:
            raise ValueError("Evaluation policy must be 'checkpoint', 'random' or 'random-prior'")

    def to_json(self) -> dict[str, Any]:
        return {
            "policy": self.policy,
            "checkpoint": None if self.checkpoint is None else str(self.checkpoint),
        }


def validate_evaluation_root(run_root: Path, spec: EvaluationSpec) -> None:
    """An evaluation root is fresh output only: never a training root, never a lineage."""
    root = run_root.resolve()
    if root.exists() and (any(root.rglob("checkpoints")) or any(root.rglob("latest.txt"))):
        raise ValueError("Evaluation root contains checkpoints; use a separate folder")
    if spec.checkpoint is not None:
        checkpoint = spec.checkpoint.resolve()
        training_root = (
            checkpoint.parent.parent.parent if checkpoint.parent.name == "checkpoints" else None
        )
        if checkpoint.is_relative_to(root) or root.is_relative_to(checkpoint):
            raise ValueError("Evaluation root overlaps the checkpoint directory")
        if training_root is not None and root.is_relative_to(training_root):
            raise ValueError("Evaluation root is inside the training run root")
    episodes = root / "metrics" / "episodes.csv"
    if episodes.exists() and episodes.stat().st_size > 0:
        raise ValueError("Evaluation root already has episodes; use a new folder per evaluation")


@dataclass(frozen=True)
class SessionPlan:
    game: Path
    game_log: Path
    config: Path
    run_root: Path
    output: Path
    parent_id: str
    seed: int
    seconds: float
    steps: int
    max_restarts: int
    disk_bytes: int
    time_budget_only: bool = False
    # Forever sessions: unlimited restarts (0), nonbinding step count, resume or first start.
    forever: bool = False
    resume: bool = True
    stop_file: Path | None = None  # extra stop request, checked with the session's own
    # Evaluation sessions: no parent, no progress, unlimited restarts like pure training.
    evaluation: EvaluationSpec | None = None

    def __post_init__(self) -> None:
        if not math.isfinite(self.seconds) or not 60 <= self.seconds <= MAX_SESSION_SECONDS:
            raise ValueError("Session seconds must be finite and within 60..28740")
        if self.evaluation is not None:
            if (
                self.forever
                or self.time_budget_only
                or self.resume
                or self.parent_id
                or self.steps != TIME_ONLY_STEPS
                or self.max_restarts != 0
                or self.disk_bytes < 1
                or self.seconds > TIME_ONLY_MAX_SECONDS
            ):
                raise ValueError(
                    "Evaluation sessions are <=4h, fresh, with nonbinding steps and 0 restarts"
                )
        elif self.forever:
            if self.steps != TIME_ONLY_STEPS or self.max_restarts != 0 or self.disk_bytes < 1:
                raise ValueError(
                    "Forever sessions need nonbinding steps, 0 restarts and a disk cap"
                )
            if self.time_budget_only:
                raise ValueError("Forever and time-only modes are exclusive")
        elif self.steps < 1 or not 1 <= self.max_restarts <= 5000 or self.disk_bytes < 1:
            raise ValueError("Explicit positive step/disk and 1..5000 restart limits required")
        if not self.resume and self.parent_id:
            raise ValueError("A fresh start has no parent")
        if type(self.time_budget_only) is not bool:
            raise ValueError("Time budget mode must be boolean")
        if self.time_budget_only and (
            self.seconds > TIME_ONLY_MAX_SECONDS
            or self.steps != TIME_ONLY_STEPS
            or self.max_restarts != TIME_ONLY_RESTARTS
        ):
            raise ValueError(
                "Time-only sessions require <=4h and nonbinding step/restart sentinels"
            )


@dataclass(frozen=True)
class SessionClock:
    started: float
    wall_started: float
    deadline: float

    @classmethod
    def start(cls, seconds: float) -> SessionClock:
        now = time.monotonic()
        wall = time.time()
        # Lua approvals use integral Unix seconds. Align once so the lease can
        # cover the complete action window without rounding beyond its deadline.
        return cls(now, wall, now + (math.floor(wall + seconds) - wall))

    def lease(self, now: float, wall_now: float) -> tuple[int, float]:
        """Use this explicit paired sample for both the writer and expiry assertion."""
        expiry_limit = min(
            self.wall_started + self.deadline - self.started,
            wall_now + self.deadline - now,
        )
        seconds = math.floor(expiry_limit) - math.floor(wall_now)
        if seconds < 60:
            raise ValueError("Insufficient remaining time for a nonrenewed approval")
        return seconds, expiry_limit


@dataclass
class Progress:
    clock: SessionClock
    phase: str = "startup"
    phase_since: float = 0.0
    last_activity: float | None = None
    latest: dict[str, Any] | None = None
    last_update_at: float | None = None
    checkpoint_note: str | None = None
    reason: str | None = None
    stop_observed_at: float | None = None
    fault: str | None = None
    listening: bool = False
    durations: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.phase_since = self.clock.started

    def transition(self, phase: str, now: float) -> None:
        now = max(now, self.phase_since)
        self.durations[self.phase] = self.durations.get(self.phase, 0) + now - self.phase_since
        self.phase, self.phase_since = phase, now

    def tick(self, now: float) -> None:
        # Pure training collects all the time; it is only "waiting" when no episode or
        # checkpoint event arrived for longer than a rollout plus a stall restart.
        if self.phase in ("training", "checkpointing", "evaluating"):
            if self.last_activity is not None and now - self.last_activity > IDLE_SECONDS:
                self.transition("waiting", max(self.phase_since, self.last_activity + IDLE_SECONDS))

    def event(self, item: dict[str, Any]) -> None:
        now = float(item["monotonic"])
        event, data = item["event"], item.get("data")
        self.tick(now)
        self.last_activity = now
        if event == "listening":
            self.listening = True
        elif event == "fault":
            self.fault = str(data)
        elif event == "budget":
            self.reason = str(data)
            self.stop_observed_at = now
        elif event == "training_result" and isinstance(data, dict):
            self.reason = str(data["stop_reason"])
            self.stop_observed_at = now
            if self.reason == "completed":
                self.reason = f"Training timestep target reached at {data.get('timesteps')}"
        elif event == "training":
            self.transition("training", now)
        elif event == "evaluation":
            self.transition("evaluating", now)
        elif event == "checkpointing":
            self.transition("checkpointing", now)
        elif event == "checkpoint_completed":
            self.transition("training", now)  # the learner resumes collecting right away

    def snapshot(self, now: float) -> dict[str, Any]:
        self.tick(now)
        durations = dict(self.durations)
        durations[self.phase] = durations.get(self.phase, 0) + max(0, now - self.phase_since)
        return {
            "state": self.phase,
            "updated_at": time.time(),
            "observed_monotonic": now,
            "started_at": self.clock.wall_started,
            "deadline_monotonic": self.clock.deadline,
            "elapsed_seconds": now - self.clock.started,
            "last_activity_monotonic": self.last_activity,
            "phase_seconds": durations,
            "latest_checkpoint": self.latest,
            "last_checkpoint_update_at": self.last_update_at,
            "checkpoint_note": self.checkpoint_note,
            "reason": self.reason,
            "stop_observed_monotonic": self.stop_observed_at,
            "fault": self.fault,
        }


class EventTail:
    """Incremental bounded reads; never scan historical sessions or oracle data."""

    def __init__(self, path: Path) -> None:
        self.path, self.offset, self.pending = path, 0, b""

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("rb") as stream:
            stream.seek(self.offset)
            block = stream.read(256 * 1024)
            self.offset += len(block)
        lines = (self.pending + block).split(b"\n")
        self.pending = lines.pop()
        if len(self.pending) > 64 * 1024:
            raise ValueError("Oversized session event")
        return [json.loads(line) for line in lines if line]


class NativeRuntime:
    """Own exactly the worker and game window created by this invocation."""

    def __init__(self, plan: SessionPlan) -> None:
        self.plan = plan
        self.process: subprocess.Popen[bytes] | None = None
        self.menu: WindowsMenu | None = None
        self.console: Any = None
        self.kernel: Any = None
        self.frozen: dict[str, str] = {}
        self.config_hash = ""

    @property
    def approval(self) -> Path:
        return self.plan.game / MOD_DIRECTORY / APPROVAL_NAME

    def identity(self) -> dict[str, Any]:
        if self.plan.evaluation is not None:
            raise ValueError("An evaluation session has no checkpoint progress")
        directory = latest_checkpoint_dir(
            self.plan.run_root / f"seed-{self.plan.seed}" / "checkpoints"
        )
        manifest = load_checkpoint(
            directory,
            expected_config_hash=self.config_hash,
            expected_seed=self.plan.seed,
            expected_reward_contract=LIVE_REWARD_CONTRACT,
        )
        return {
            "id": manifest.checkpoint_id,
            "steps": manifest.timesteps,
            "path": str(directory),
            "completed_at": (directory / "manifest.json").stat().st_mtime,
        }

    def preflight(self) -> dict[str, Any] | None:
        preflight(self.plan.game)
        if self.approval.exists() or self.approval.with_suffix(".tmp").exists():
            raise ValueError("Foreign approval; no takeover")
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 9528))
        config, self.config_hash = load_training_config(self.plan.config)
        if config.status == TEMPLATE_STATUS:
            raise ValueError("Template configuration cannot train")
        if self.plan.time_budget_only and (
            not isinstance(config, TrainingConfig)
            or config.budget.total_timesteps < TIME_ONLY_STEPS
            or config.budget.wall_time_minutes * 60 < self.plan.seconds
        ):
            raise ValueError("Configuration would impose a hidden count or shorter time stop")
        if self.plan.forever and not isinstance(config, PureTrainingConfig):
            raise ValueError("Forever sessions need a config version 2 (pure) profile")
        parent: dict[str, Any] | None = None
        evaluated: list[Path] = []
        if self.plan.evaluation is not None:
            evaluated = self.check_evaluation(config)
        elif self.plan.resume:
            parent = self.identity()
            if parent["id"] != self.plan.parent_id:
                raise ValueError("Unexpected parent checkpoint; no fresh-model fallback")
        elif (self.plan.run_root / f"seed-{self.plan.seed}" / "checkpoints/latest.txt").exists():
            raise ValueError("Checkpoints exist; a fresh start would fork the lineage")
        paths = [
            *PROJECT_ROOT.joinpath("src").rglob("*.py"),
            self.plan.config,
            self.plan.game / MOD_DIRECTORY / "main.lua",
            self.plan.game / MOD_DIRECTORY / "metadata.xml",
        ]
        # Retention may delete the parent while a forever session runs; freeze it otherwise.
        if parent is not None and not self.plan.forever:
            paths.extend(Path(parent["path"]).iterdir())
        paths.extend(evaluated)  # the evaluated checkpoint must stay byte-identical
        self.frozen = {str(p): digest(p) for p in paths if p.is_file()}
        return parent

    def check_evaluation(self, config: Any) -> list[Path]:
        """Validate the evaluation target; returns the checkpoint files to freeze."""
        spec = self.plan.evaluation
        assert spec is not None
        if not isinstance(config, PureTrainingConfig):
            raise ValueError("Evaluation needs a config version 2 (pure) profile")
        validate_evaluation_root(self.plan.run_root, spec)
        if spec.checkpoint is None:
            return []
        load_checkpoint(
            spec.checkpoint,
            expected_config_hash=self.config_hash,
            expected_seed=config.seed,
            expected_reward_contract=LIVE_REWARD_CONTRACT,
        )
        return [p for p in spec.checkpoint.iterdir() if p.is_file()]

    def hold_sleep(self) -> None:
        self.kernel = ctypes.windll.kernel32
        self.kernel.SetThreadExecutionState.argtypes = [ctypes.c_uint]
        self.kernel.SetThreadExecutionState.restype = ctypes.c_uint
        if not self.kernel.SetThreadExecutionState(0x80000001):
            raise OSError("Cannot prevent system sleep")

    def release_sleep(self) -> None:
        if self.kernel is not None and not self.kernel.SetThreadExecutionState(0x80000000):
            raise OSError("Cannot release system sleep prevention")

    def grant(self, seconds: int, wall_now: float) -> str:
        if self.approval.exists() or self.approval.with_suffix(".tmp").exists():
            raise ValueError("Foreign approval appeared before grant")
        write_training_approval(
            self.plan.game,
            hours=(seconds + 0.5) / 3600,
            now=wall_now,
            max_restarts=self.plan.max_restarts,
            evidence="explicit finite session runner; Continue file2 or New Run on no game",
        )
        return digest(self.approval)

    def start(self) -> None:
        self.console = (self.plan.output / "console.txt").open("xb")
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "-m",
                "isaac_threrisaifuture.session_runner",
                "--worker",
                str(self.plan.output / "plan.json"),
            ],
            cwd=PROJECT_ROOT,
            stdout=self.console,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def poll(self) -> int | None:
        return self.process.poll() if self.process is not None else None

    def enter(self, deadline: float) -> None:
        if game_running():
            raise ValueError("Foreign game appeared before Steam launch")
        journal = StopAwareGameLog(
            self.plan.game_log, self.plan.output / "stop.request", self.plan.stop_file
        )
        self.menu = WindowsMenu(self.plan.game, time.time())
        request_steam_launch()
        with (self.plan.output / "menu.jsonl").open("x", encoding="utf-8") as stream:

            def record(event: str, data: Any) -> None:
                stream.write(json.dumps({"event": event, "data": data}) + "\n")
                stream.flush()

            continue_or_new_run_file2(
                journal, self.menu, min(deadline, time.monotonic() + 60), record
            )

    def size(self) -> int:
        roots = {self.plan.output.resolve(), self.plan.run_root.resolve()}
        return sum(p.stat().st_size for r in roots for p in r.rglob("*") if p.is_file())

    def stop_worker(self) -> None:
        if self.process is None:
            return
        (self.plan.output / "stop.request").touch()
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            self.process.wait(timeout=5)
            raise RuntimeError(
                "Owned worker required termination; cooperative release unverified"
            ) from None
        finally:
            if self.console is not None:
                self.console.close()

    def close_game(self) -> None:
        if self.menu is None:
            return
        if not game_running():
            return
        if not self.menu.ready() or self.menu.window is None:
            raise RuntimeError("Cannot identify owned game for normal close")
        user = self.menu.user
        user.PostMessageW.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_size_t,
            ctypes.c_ssize_t,
        ]
        user.PostMessageW.restype = ctypes.c_int
        if not user.PostMessageW(self.menu.window[0], 0x10, 0, 0):
            raise OSError("Normal owned-game close refused")
        limit = time.monotonic() + 12
        while game_running() and time.monotonic() < limit:
            time.sleep(0.2)
        if game_running():
            raise RuntimeError("Game did not close normally; no game force-kill")

    def remove_approval(self, expected: str) -> None:
        if self.approval.exists():
            if digest(self.approval) != expected:
                raise RuntimeError("Approval changed; deletion refused")
            self.approval.unlink()

    def verify_frozen(self) -> None:
        for path, expected in self.frozen.items():
            if digest(Path(path)) != expected:
                raise RuntimeError(f"Frozen source or parent changed: {path}")


class StopAwareGameLog(FreshGameLog):
    """The menu adapter polls this reader, including while a key is held."""

    def __init__(self, path: Path, stop: Path, extra_stop: Path | None = None) -> None:
        super().__init__(path)
        self.stop, self.extra_stop = stop, extra_stop

    def read(self) -> str:
        if self.stop.exists() or (self.extra_stop is not None and self.extra_stop.exists()):
            raise KeyboardInterrupt
        return super().read()


def supervise(plan: SessionPlan, runtime: NativeRuntime | None = None) -> dict[str, Any]:
    """Always publish the terminal result before attempting optional metrics."""
    runtime = runtime or NativeRuntime(plan)
    plan.output.mkdir(parents=True, exist_ok=False)
    clock = SessionClock.start(plan.seconds)
    progress = Progress(clock)
    tail = EventTail(plan.output / "events.jsonl")
    approval_hash: str | None = None
    cancelled, deadline_stop = False, False
    cleanup_errors: list[str] = []
    status_skipped = 0
    peak = 0

    def stop_requested() -> bool:
        return (plan.output / "stop.request").exists() or (
            plan.stop_file is not None and plan.stop_file.exists()
        )

    def publish() -> None:
        # status.json is only a view for readers such as a dashboard; result.json is the record.
        nonlocal status_skipped
        if not status_json(plan.output / "status.json", progress.snapshot(time.monotonic())):
            status_skipped += 1

    def drain() -> None:
        for item in tail.read():
            progress.event(item)
            if item["event"] == "checkpoint_completed":
                try:
                    latest = runtime.identity()
                    if latest["id"] != item["data"]["id"]:
                        raise ValueError("Checkpoint event/pointer mismatch")
                    progress.latest = latest
                    progress.last_update_at = float(item["time"])
                    progress.checkpoint_note = None
                except Exception as exc:
                    progress.checkpoint_note = str(exc)

    try:
        publish()
        progress.latest = runtime.preflight()
        atomic_json(
            plan.output / "plan.json",
            {
                "options": {
                    **{k: str(v) if isinstance(v, Path) else v for k, v in asdict(plan).items()},
                    "evaluation": None if plan.evaluation is None else plan.evaluation.to_json(),
                },
                "clock": asdict(clock),
                "config_hash": runtime.config_hash,
                "parent": progress.latest,
                "frozen": runtime.frozen,
                "max_faults": 0,
                "entry_mode": "continue",
                "retries": 0,
                "count_limit_mode": (
                    "nonbinding_schema_sentinels"
                    if plan.time_budget_only or plan.forever or plan.evaluation is not None
                    else "explicit_diagnostic"
                ),
            },
        )
        peak = runtime.size()
        if peak > plan.disk_bytes:
            raise ValueError("Emergency disk budget exceeded before launch")
        runtime.hold_sleep()
        runtime.verify_frozen()
        now = time.monotonic()
        wall_now = clock.wall_started + (now - clock.started)
        lease_seconds, wall_deadline = clock.lease(now, wall_now)
        approval_hash = runtime.grant(lease_seconds, wall_now)
        approval = json.loads(runtime.approval.read_text("utf-8"))
        if approval["expires_at"] > wall_deadline:
            raise ValueError("Approval expiry exceeds fixed deadline")
        atomic_json(
            plan.output / "approval-identity.json",
            {
                "sha256": approval_hash,
                "expires_at": approval["expires_at"],
                "mapped_deadline": wall_deadline,
            },
        )
        runtime.start()
        listener_deadline = min(clock.deadline, time.monotonic() + 20)
        while not progress.listening:
            drain()
            if progress.listening:
                break
            if stop_requested():
                raise KeyboardInterrupt
            if runtime.poll() is not None:
                raise RuntimeError("Worker exited before listener readiness")
            if time.monotonic() >= listener_deadline:
                raise TimeoutError("Listener readiness deadline exhausted")
            time.sleep(0.1)
        runtime.enter(clock.deadline)
        progress.transition("waiting", time.monotonic())
        next_disk = 0.0
        while True:
            drain()
            now = time.monotonic()
            publish()
            if stop_requested():
                raise KeyboardInterrupt
            if runtime.poll() is not None:
                break
            if now >= clock.deadline:
                deadline_stop = True
                break
            if now >= next_disk:
                peak = max(peak, runtime.size())
                next_disk = now + 5
                if peak > plan.disk_bytes:
                    raise RuntimeError("Emergency disk budget exhausted")
            time.sleep(0.25)
    except KeyboardInterrupt:
        cancelled = True
        progress.reason = "User cancellation requested"
    except Exception as exc:
        progress.fault = f"{type(exc).__name__}: {exc}"
    finally:
        # Every cleanup action is isolated; parser/identity errors cannot skip it.
        operations = [("worker", runtime.stop_worker), ("game", runtime.close_game)]
        if approval_hash is not None:
            operations.append(("approval", lambda: runtime.remove_approval(approval_hash)))
        operations.extend([("sleep", runtime.release_sleep), ("frozen", runtime.verify_frozen)])
        for name, operation in operations:
            try:
                operation()
            except Exception as exc:
                cleanup_errors.append(f"{name}: {type(exc).__name__}: {exc}")
        try:
            drain()
        except Exception as exc:
            progress.fault = progress.fault or f"Final telemetry read failed: {exc}"
        if progress.latest is not None:
            try:
                latest = runtime.identity()
                if latest["id"] != progress.latest["id"]:
                    if latest["steps"] <= progress.latest["steps"]:
                        raise ValueError("Final checkpoint regressed or changed lineage")
                    progress.latest = latest
                    progress.last_update_at = latest.get("completed_at", time.time())
                    progress.checkpoint_note = "Completed publication recovered by final readback"
            except Exception as exc:
                progress.checkpoint_note = str(exc)
                cleanup_errors.append(f"checkpoint: {type(exc).__name__}: {exc}")
        code = runtime.poll()
        now = time.monotonic()
        if cancelled:
            progress.reason = "User cancellation requested"
        state = "early_stop"
        if progress.fault or cleanup_errors or (code not in (None, 0) and not cancelled):
            state = "fault"
        elif cancelled:
            state = "user_cancelled"
        elif (
            progress.stop_observed_at is not None
            and progress.stop_observed_at >= clock.deadline - STOP_MARGIN_SECONDS
            and progress.reason is not None
            and (
                "wall time" in progress.reason.lower()
                or "wall-time" in progress.reason.lower()
                or progress.reason == "wall_time"
            )
        ):
            state = "completed"
        elif deadline_stop:
            state = "fault"
            progress.fault = "Deadline reached without cooperative wall-time stop evidence"
        progress.reason = progress.reason or "Worker exited without a completion reason"
        result = {
            **progress.snapshot(now),
            "state": state,
            "learner_exit": code,
            "cleanup_errors": cleanup_errors,
            "status_writes_skipped": status_skipped,
            "sampled_peak_bytes": peak,
            "ended_at": time.time(),
        }
        atomic_json(plan.output / "result.json", result)
        status_json(plan.output / "status.json", result)
    try:
        atomic_json(
            plan.output / "metrics.json",
            {
                "phase_seconds": result["phase_seconds"],
                "note": "Observed activity only; checkpoint changes do not prove improved gameplay",
            },
        )
    except Exception:
        pass  # Optional export must not replace the durable terminal state.
    return result


@dataclass(frozen=True)
class ForeverOptions:
    game: Path
    game_log: Path
    config: Path
    run_root: Path
    output: Path  # supervisor folder: one subfolder per session, plus forever.json
    initialize: bool = False  # allow the very first session to start a fresh model
    disk_bytes: int | None = None  # default: budget.disk_limit_mb of the config
    keep_sessions: int = 20  # newest session log folders kept; older raw logs are removed

    @property
    def stop_file(self) -> Path:
        return self.output / "stop.forever"


def _tree_bytes(*roots: Path) -> int:
    return sum(p.stat().st_size for r in roots if r.exists() for p in r.rglob("*") if p.is_file())


def _prune_session_logs(output: Path, keep: int) -> None:
    # Session folders only hold raw logs and status; checkpoints live in the run root.
    folders = sorted(p for p in output.glob("session-*") if p.is_dir())
    for old in folders[: max(0, len(folders) - keep)]:
        shutil.rmtree(old)


def run_forever(
    options: ForeverOptions,
    session: Callable[[SessionPlan], dict[str, Any]] = supervise,
) -> dict[str, Any]:
    """Run bounded sessions back to back until a stop condition; every session resumes latest.

    The config is read again before each session, so edited hyperparameters apply to the
    next session. Stops on: stop file, Ctrl+C, disk cap, a refused lineage, or
    `max_consecutive_faults` consecutive sessions that end in infrastructure faults.
    """
    options.output.mkdir(parents=True, exist_ok=True)
    sessions: list[dict[str, Any]] = []
    faulted = 0
    reason = "unknown"

    def finish() -> dict[str, Any]:
        summary = {"stop_reason": reason, "consecutive_faults": faulted, "sessions": sessions}
        atomic_json(options.output / "forever.json", summary)
        return summary

    try:
        while True:
            if options.stop_file.exists():
                reason = "stop file"
                return finish()
            try:
                config, cfg_hash = load_training_config(options.config)
            except ValueError as error:
                reason = f"config refused: {error}"
                return finish()
            if not isinstance(config, PureTrainingConfig):
                reason = "config refused: forever mode needs a config version 2 profile"
                return finish()
            cap = options.disk_bytes or config.budget.disk_limit_mb * 1_000_000
            _prune_session_logs(options.output, options.keep_sessions)
            if _tree_bytes(options.run_root, options.output) > cap:
                reason = "disk cap"
                return finish()
            checkpoints = options.run_root / f"seed-{config.seed}" / "checkpoints"
            parent_id = ""
            if (checkpoints / "latest.txt").exists():
                try:
                    manifest = load_checkpoint(
                        latest_checkpoint_dir(checkpoints),
                        expected_config_hash=cfg_hash,
                        expected_seed=config.seed,
                        expected_reward_contract=LIVE_REWARD_CONTRACT,
                    )
                except CheckpointError as error:
                    reason = f"lineage refused: {error}"
                    return finish()
                parent_id = manifest.checkpoint_id
            elif not options.initialize:
                reason = "no checkpoint to resume; pass --initialize for the first session"
                return finish()
            stamp = time.strftime("%Y%m%d-%H%M%S")
            plan = SessionPlan(
                options.game,
                options.game_log,
                options.config,
                options.run_root,
                options.output / f"session-{stamp}-{len(sessions) + 1:04d}",
                parent_id,
                config.seed,
                min(config.budget.wall_time_minutes * 60, MAX_SESSION_SECONDS),
                TIME_ONLY_STEPS,
                0,
                cap,
                forever=True,
                resume=bool(parent_id),
                stop_file=options.stop_file,
            )
            result = session(plan)
            latest = (result.get("latest_checkpoint") or {}).get("id", "")
            state = str(result.get("state"))
            sessions.append(
                {
                    "output": str(plan.output),
                    "resumed": plan.resume,
                    "parent": parent_id,
                    "latest": latest,
                    "state": state,
                    "reason": result.get("reason"),
                }
            )
            fault_text = str(result.get("fault") or "").lower()
            if state == "user_cancelled":
                reason = "user cancelled"
                return finish()
            if "disk budget" in fault_text:
                reason = "disk cap"
                return finish()
            # An early stop that saved nothing new is as bad as a fault.
            if state == "fault" or (state == "early_stop" and latest == parent_id):
                faulted += 1
                if faulted >= config.budget.max_consecutive_faults:
                    reason = f"fault cap: {faulted} consecutive sessions ended in faults"
                    return finish()
            else:
                faulted = 0
    except KeyboardInterrupt:
        reason = "Ctrl+C"
        return finish()


class LazyWindowsMenu:
    """Guarded game keyboard for the worker, built on first use.

    The worker starts before the supervisor launches the game, so any game process it finds is
    newer than `launched_at`. Errors surface at the first key press, where pausing records and
    skips them.
    """

    def __init__(self, directory: Path, launched_at: float) -> None:
        self._directory, self._launched_at = directory, launched_at
        self._menu: WindowsMenu | None = None

    def _get(self) -> WindowsMenu:
        if self._menu is None:
            self._menu = WindowsMenu(self._directory, self._launched_at)
        return self._menu

    def ready(self) -> bool:
        return self._get().ready()

    def press(self, key: str, stop: Callable[[], bool]) -> None:
        self._get().press(key, stop)


def worker(path: Path) -> None:
    launched_at = time.time()
    payload = json.loads(path.read_text("utf-8"))
    raw = payload["options"]
    output = Path(raw["output"])
    if time.monotonic() >= payload["clock"]["deadline"]:
        raise ValueError("Session deadline expired before worker startup")
    with (output / "events.jsonl").open("x", encoding="utf-8") as stream:

        def record(event: str, data: Any) -> None:
            stream.write(
                json.dumps(
                    {
                        "event": event,
                        "data": data,
                        "monotonic": time.monotonic(),
                        "time": time.time(),
                    }
                )
                + "\n"
            )
            stream.flush()

        evaluation = raw.get("evaluation")
        extra: dict[str, Any] = {}
        if evaluation is not None:
            checkpoint = evaluation["checkpoint"]
            extra = {
                "eval_policy": evaluation["policy"],
                "eval_checkpoint": None if checkpoint is None else Path(checkpoint),
            }
        try:
            run_live(
                LiveRunOptions(
                    mode="train" if evaluation is None else "evaluate",
                    out_dir=Path(raw["run_root"]),
                    config_path=Path(raw["config"]),
                    seed=raw["seed"],
                    steps=raw["steps"],
                    minutes=raw["seconds"] / 60,
                    resume=raw.get("resume", True) and evaluation is None,
                    max_faults=0,
                    connection_timeout=min(90, raw["seconds"]),
                    session_deadline=payload["clock"]["deadline"] - STOP_MARGIN_SECONDS,
                    stop_file=output / "stop.request",
                    require_initial_isaac=True,
                    keyboard=LazyWindowsMenu(Path(raw["game"]), launched_at),
                    **extra,
                ),
                on_record=record,
            )
        except Exception as exc:
            record("fault", f"{type(exc).__name__}: {exc}")
            raise


def _evaluate_main(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """One frozen evaluation session; limits are derived like the time-only mode does."""
    for name in ("config", "run_root", "output", "seconds"):
        if getattr(args, name) is None:
            parser.error(f"--{name.replace('_', '-')} is required with --evaluate")
    if any(getattr(args, n) is not None for n in ("parent_id", "steps", "max_restarts")):
        parser.error("--evaluate derives its limits; omit --parent-id, --steps and --max-restarts")
    if args.time_budget_only:
        parser.error("--evaluate is already time-bounded; omit --time-budget-only")
    try:
        spec = EvaluationSpec(args.evaluate, args.checkpoint and args.checkpoint.resolve())
        validate_evaluation_root(args.run_root, spec)
        config, _ = load_training_config(args.config.resolve())
        if not isinstance(config, PureTrainingConfig):
            raise ValueError("Evaluation needs a config version 2 (pure) profile")
        plan = SessionPlan(
            args.game.resolve(),
            args.game_log.resolve(),
            args.config.resolve(),
            args.run_root.resolve(),
            args.output.resolve(),
            "",
            config.seed if args.seed is None else args.seed,
            args.seconds,
            TIME_ONLY_STEPS,
            0,  # unlimited New Run after death or stall, as in training
            args.disk_bytes or config.budget.disk_limit_mb * 1_000_000,
            resume=False,
            evaluation=spec,
        )
    except ValueError as error:
        parser.error(str(error))
    result = supervise(plan)
    print(json.dumps(result, indent=2))
    return 1 if result["state"] == "fault" else 0


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(Path(sys.argv[2]))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forever", action="store_true", help="Run sessions back to back")
    parser.add_argument("--initialize", action="store_true", help="Forever: allow a fresh start")
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--game-log", required=True, type=Path)
    for name in ("config", "run-root", "output"):
        parser.add_argument(f"--{name}", type=Path)
    parser.add_argument("--parent-id")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--seconds", type=float)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--max-restarts", type=int)
    parser.add_argument("--time-budget-only", action="store_true")
    parser.add_argument("--disk-bytes", type=int)
    parser.add_argument(
        "--evaluate",
        choices=("checkpoint", "random", "random-prior"),
        help="Frozen evaluation session; --run-root is the new evaluation output root",
    )
    parser.add_argument("--checkpoint", type=Path, help="Exact checkpoint directory to evaluate")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("Native Windows is required")
    if args.forever and (args.evaluate is not None or args.checkpoint is not None):
        parser.error("--evaluate runs one session; it cannot be combined with --forever")
    if args.forever:
        derived = ("parent_id", "seed", "seconds", "steps", "max_restarts", "output")
        if any(getattr(args, name) is not None for name in derived) or args.time_budget_only:
            parser.error("--forever derives its limits from the config; pass only the paths")
        run_root = (args.run_root or Path("runs/pure-v4")).resolve()
        outcome = run_forever(
            ForeverOptions(
                args.game.resolve(),
                args.game_log.resolve(),
                (args.config or PURE_CONFIG).resolve(),
                run_root,
                run_root / "supervisor",
                args.initialize,
                args.disk_bytes,
            )
        )
        print(json.dumps(outcome, indent=2))
        failed = outcome["stop_reason"].startswith(("fault", "lineage", "config", "disk", "no "))
        raise SystemExit(1 if failed else 0)
    if args.initialize:
        parser.error("--initialize applies to --forever only")
    if args.evaluate is not None:
        raise SystemExit(_evaluate_main(parser, args))
    if args.checkpoint is not None:
        parser.error("--checkpoint applies to --evaluate checkpoint only")
    for name in ("config", "run_root", "output", "parent_id", "seed", "seconds", "disk_bytes"):
        if getattr(args, name) is None:
            parser.error(f"--{name.replace('_', '-')} is required without --forever")
    if args.time_budget_only:
        if args.steps is not None or args.max_restarts is not None:
            parser.error("Time-only mode derives count sentinels; omit --steps and --max-restarts")
        args.steps, args.max_restarts = TIME_ONLY_STEPS, TIME_ONLY_RESTARTS
    elif args.steps is None or args.max_restarts is None:
        parser.error("Diagnostic mode requires --steps and --max-restarts")
    values = vars(args)
    values.pop("forever"), values.pop("initialize")
    values.pop("evaluate"), values.pop("checkpoint")
    for key in ("game", "game_log", "config", "run_root", "output"):
        values[key] = values[key].resolve()
    result = supervise(SessionPlan(**values))
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["state"] == "fault" else 0)


if __name__ == "__main__":
    main()
