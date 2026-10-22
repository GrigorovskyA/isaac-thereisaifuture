"""Attach-only, inference-only live runner for one frozen checkpoint or the random baseline.

Reuses the live transport (`LiveClient`, `make_live_env`); it never launches the game, learns,
saves, resumes, follows the latest pointer, writes approvals or forces restarts. The Lua
`live_loop_v1` approval is still required. One absolute monotonic deadline bounds listening,
reset, paused waits, steps and reconnects; in-flight I/O may overrun it by the bounds documented
in `LiveBackend` (ack 1 s, step wait 5 s). Results are descriptive pilot data, never a ranking.
"""

import json
import math
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import monotonic
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from .baselines import RandomPolicy
from .checkpoint_policy import CheckpointPolicy, InvalidPolicyOutput
from .checkpoints import ACTION_SCHEMA_VERSION, REWARD_SCHEMA_VERSION, CheckpointError
from .entities import OBSERVATION_SCHEMA_VERSION, OracleEvent
from .episodes import EpisodeFault
from .launcher import EventLog
from .live import (
    TRAINING_MAX_SECONDS,
    LiveBudgetExpired,
    LiveClient,
    LiveSnapshot,
    make_live_env,
)
from .observation import BridgeTimeout, HelloAck, ProtocolError
from .observer_client import ObserverConfig

PolicyKind = Literal["checkpoint", "random"]
Assistance = Literal["assisted", "unassisted", "unknown"]
Record = Callable[[str, Any], None]
Status = Literal["completed", "interrupted", "failed", "invalid"]
ACTION_REPEAT = 3  # live default; equals configs/training-live-v1.yaml; manifests omit it
MAX_STEPS = 100_000
MAX_ACCEPT_SECONDS = 3600.0
ORDINARY_STOPS = ("step_cap", "deadline", "operator_interrupt")
EXIT_CODES: dict[Status, int] = {"completed": 0, "interrupted": 0, "failed": 1, "invalid": 3}


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _seconds(value: object, name: str, limit: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    if not math.isfinite(value) or not 0 < value <= limit:
        raise ValueError(f"{name} must be finite and within (0, {limit:g}]")
    return float(value)


@dataclass(frozen=True)
class FrozenLiveOptions:
    policy: PolicyKind
    out_dir: Path
    checkpoint: Path | None = None
    expected_config_hash: str | None = None
    expected_training_seed: int | None = None
    policy_seed: int = 0
    steps: int = 2000
    minutes: float = 6.0
    accept_timeout: float = 300.0
    max_faults: int = 0
    operator_assistance: Assistance = "unknown"
    port: int = 9528

    def __post_init__(self) -> None:
        if self.policy not in ("checkpoint", "random"):
            raise ValueError("Policy must be 'checkpoint' or 'random'")
        if self.operator_assistance not in ("assisted", "unassisted", "unknown"):
            raise ValueError("Operator assistance must be assisted, unassisted or unknown")
        if self.policy == "checkpoint":
            if self.checkpoint is None or not self.expected_config_hash:
                raise ValueError("Checkpoint policy needs --checkpoint and --expected-config-hash")
        elif self.checkpoint is not None or self.expected_config_hash is not None:
            raise ValueError("Checkpoint arguments are only valid with --policy checkpoint")
        elif self.expected_training_seed is not None:
            raise ValueError("Expected training seed is only valid with --policy checkpoint")
        if self.expected_training_seed is not None:
            _integer(self.expected_training_seed, "Expected training seed")
        _integer(self.policy_seed, "Policy seed")
        if not 1 <= _integer(self.steps, "Steps") <= MAX_STEPS:
            raise ValueError(f"Steps must be within 1..{MAX_STEPS}")
        _seconds(self.minutes, "Minutes", TRAINING_MAX_SECONDS / 60)
        _seconds(self.accept_timeout, "Accept timeout", MAX_ACCEPT_SECONDS)
        if _integer(self.max_faults, "Fault budget") < 0:
            raise ValueError("Fault budget must be nonnegative")


@dataclass
class Segment:
    """One episode segment; a live run is a sequence of them within one game run."""

    index: int
    episode_id: int
    session_id: str | None
    game_epoch: int | None
    start_frame: int | None
    end_frame: int | None = None
    steps: int = 0
    reward_return: float = 0.0
    end: str | None = None


@dataclass
class FrozenLiveResult:
    logs: Path
    status: Status = "failed"
    stop_reason: str = "error"
    attempted: int = 0
    completed: int = 0
    faults: int = 0
    segments: list[Segment] = field(default_factory=list)
    identity_valid: bool = True

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.status]


class _RecordingClient(LiveClient):
    """Observes every hello and the latest snapshot identity; the protocol is untouched."""

    def __init__(self, config: ObserverConfig, on_hello: Callable[[HelloAck], None]) -> None:
        super().__init__(config)
        self.on_hello = on_hello
        self.latest: tuple[str, int] | None = None

    def connect(self) -> HelloAck:
        ack = super().connect()
        self.on_hello(ack)
        return ack

    def take(self, timeout: float) -> LiveSnapshot:
        snap = super().take(timeout)
        self.latest = (snap.session_id, snap.game_epoch)
        return snap

    def drain(self) -> list[LiveSnapshot]:
        items = super().drain()
        if items:
            self.latest = (items[-1].session_id, items[-1].game_epoch)
        return items


class _PolicyFailure(Exception):
    """The policy refused an observation or produced an invalid action."""


def load_policy(options: FrozenLiveOptions) -> CheckpointPolicy | RandomPolicy:
    """Load and verify the selected policy; raises before any socket is opened."""
    if options.policy == "random":
        return RandomPolicy()
    assert options.checkpoint is not None and options.expected_config_hash is not None
    policy = CheckpointPolicy(
        options.checkpoint,
        expected_config_hash=options.expected_config_hash,
        expected_seed=options.expected_training_seed,
    )
    policy.verify_unchanged()
    return policy


def _identity(policy: CheckpointPolicy | RandomPolicy) -> dict[str, Any]:
    if isinstance(policy, CheckpointPolicy):
        return {"name": policy.name, "label": policy.label, **policy.identity.to_dict()}
    return {"name": policy.name, "label": policy.label, "deterministic": False}


def _stop_reason(exc: BaseException) -> str:
    if isinstance(exc, KeyboardInterrupt):
        return "operator_interrupt"
    if isinstance(exc, LiveBudgetExpired):
        return "deadline"
    if isinstance(exc, ProtocolError) or isinstance(exc.__cause__, ProtocolError):
        return "protocol_error"
    if isinstance(exc, _PolicyFailure):
        return "policy_error"
    if isinstance(exc, EpisodeFault):
        return "fault"
    if isinstance(exc, BridgeTimeout):
        return "connection_timeout"
    return "error"


def run_frozen_live(
    options: FrozenLiveOptions,
    policy: CheckpointPolicy | RandomPolicy | None = None,
) -> FrozenLiveResult:
    """Validate, load the policy, then listen and act until cap, deadline, stop or failure."""
    if policy is None:
        policy = load_policy(options)
    identity = _identity(policy)
    deadline = monotonic() + options.minutes * 60
    stamp = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    logs = options.out_dir / "sessions" / stamp
    logs.mkdir(parents=True)
    print(f"Local logs: {logs}", flush=True)
    result = FrozenLiveResult(logs)
    with (
        EventLog(logs / "live.jsonl") as log,
        (logs / "oracle.jsonl").open("x", encoding="utf-8") as oracle,
    ):

        def sink(event: OracleEvent) -> None:
            oracle.write(event.model_dump_json() + "\n")

        def record(event: str, data: Any) -> None:
            log.record(event, data)

        log.record(
            "configuration",
            {
                "runner": "frozen-live-pilot-v1",
                "policy_kind": options.policy,
                "policy": identity,
                "policy_seed": options.policy_seed,
                "steps": options.steps,
                "minutes": options.minutes,
                "accept_timeout": options.accept_timeout,
                "max_faults": options.max_faults,
                "operator_assistance": options.operator_assistance,
                "assistance_detection": "none; declared by the operator for the whole session",
                "action_repeat": ACTION_REPEAT,
                "observation_schema_version": OBSERVATION_SCHEMA_VERSION,
                "action_schema_version": ACTION_SCHEMA_VERSION,
                "reward_schema_version": REWARD_SCHEMA_VERSION,
                "initial_room": "unknown",
                "character_build": "unknown",
                "comparability": "descriptive pilot; unmatched rooms; no ranking",
            },
        )
        failure: BaseException | None = None
        try:
            _drive(options, policy, deadline, result, record, sink)
        except KeyboardInterrupt as exc:
            result.stop_reason = _stop_reason(exc)
        except Exception as exc:  # classified below; unexpected ones are re-raised
            result.stop_reason = _stop_reason(exc)
            if result.stop_reason != "deadline":
                log.record("failure", {"reason": result.stop_reason, "error": str(exc)})
            if result.stop_reason == "error":
                failure = exc
        finally:
            if isinstance(policy, CheckpointPolicy):
                try:
                    policy.verify_unchanged()
                except CheckpointError as exc:
                    result.identity_valid = False
                    log.record("identity_changed", str(exc))
            result.status = _status(result)
            ordinary = result.stop_reason in ORDINARY_STOPS
            for segment in result.segments:
                if segment.end is None:  # final partial segment, steps preserved
                    segment.end = "stopped" if ordinary else result.stop_reason
                    log.record("segment", asdict(segment))
            log.record(
                "summary",
                {
                    "status": result.status,
                    "stop_reason": result.stop_reason,
                    "exit_code": result.exit_code,
                    "attempted_decisions": result.attempted,
                    "completed_decisions": result.completed,
                    "faults": result.faults,
                    "segments": len(result.segments),
                    "identity_valid": result.identity_valid,
                    "operator_assistance": options.operator_assistance,
                },
            )
    if failure is not None:
        raise failure
    return result


def _status(result: FrozenLiveResult) -> Status:
    if not result.identity_valid:
        return "invalid"
    if result.faults or result.stop_reason not in ORDINARY_STOPS:
        return "failed"
    return "interrupted" if result.stop_reason == "operator_interrupt" else "completed"


def _drive(
    options: FrozenLiveOptions,
    policy: CheckpointPolicy | RandomPolicy,
    deadline: float,
    result: FrozenLiveResult,
    record: Record,
    sink: Callable[[OracleEvent], None],
) -> None:
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise LiveBudgetExpired("Live wall-time budget exhausted before listening")
    timeout = min(options.accept_timeout, remaining)
    config = ObserverConfig(port=options.port, accept_timeout=timeout)

    def hello(ack: HelloAck) -> None:
        record("hello", ack.model_dump(mode="json"))

    with _RecordingClient(config, hello) as client:
        record("listening", list(client.address))
        print("Waiting for the observer: file 2 must already be selected and running.", flush=True)
        client.connect()
        env = make_live_env(
            client,
            action_repeat=ACTION_REPEAT,
            max_faults=options.max_faults,
            record=record,
            oracle_sink=sink,
            run_deadline=deadline,
        )
        try:
            _loop(options, policy, deadline, result, record, env, client)
        finally:
            result.faults = env.faults
            env.close()


def _begin(
    result: FrozenLiveResult,
    policy: CheckpointPolicy | RandomPolicy,
    seed: int,
    info: dict[str, Any],
    client: _RecordingClient,
    record: Record,
) -> Segment:
    index = len(result.segments)
    policy.reset(seed + index)  # every segment starts with fresh recurrent state
    session, epoch = client.latest if client.latest is not None else (None, None)
    frame = info.get("frame_id")
    segment = Segment(index, int(info["episode_id"]), session, epoch, frame, frame)
    result.segments.append(segment)
    record("segment_start", {k: v for k, v in asdict(segment).items() if v is not None})
    return segment


def _loop(
    options: FrozenLiveOptions,
    policy: CheckpointPolicy | RandomPolicy,
    deadline: float,
    result: FrozenLiveResult,
    record: Record,
    env: Any,
    client: _RecordingClient,
) -> None:
    obs, info = env.reset()
    segment = _begin(result, policy, options.policy_seed, info, client, record)
    while True:
        if result.attempted >= options.steps:
            result.stop_reason = "step_cap"
            return
        if monotonic() >= deadline:
            result.stop_reason = "deadline"
            return
        try:
            action: NDArray[np.int64] = policy.act(obs)
        except (InvalidPolicyOutput, CheckpointError, ValueError) as exc:
            raise _PolicyFailure(str(exc)) from exc
        if monotonic() >= deadline:
            result.stop_reason = "deadline"
            return
        result.attempted += 1
        obs, reward, terminated, truncated, info = env.step(action)
        result.faults = env.faults
        if "fault" in info:
            segment.end = "fault"
        else:
            result.completed += 1
            segment.steps += 1
            segment.reward_return += float(reward)
            segment.end_frame = info.get("frame_id", segment.end_frame)
            if terminated or truncated:
                segment.end = str(info.get("outcome") or "truncated")
        if segment.end is None:
            continue
        record("segment", asdict(segment))
        if result.attempted >= options.steps:
            result.stop_reason = "step_cap"
            return
        obs, info = env.reset()  # bounded by the same deadline; reconnects after a death
        segment = _begin(result, policy, options.policy_seed, info, client, record)


def summary_line(result: FrozenLiveResult) -> str:
    return json.dumps(
        {
            "status": result.status,
            "stop_reason": result.stop_reason,
            "attempted": result.attempted,
            "completed": result.completed,
            "faults": result.faults,
            "segments": len(result.segments),
            "logs": str(result.logs),
        }
    )
