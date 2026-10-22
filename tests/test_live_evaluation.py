"""OFFLINE tests for the frozen live pilot runner. Fakes and a synthetic Lua room only; nothing
here connects to Isaac or verifies gameplay."""

import json
import shutil
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from test_checkpoint_policy import CFG_HASH, RAW_CONFIG, SEED, synthetic_env
from test_live_e2e import SOCKET_SHIM, Game, Shim, free_port
from test_lua_live_loop import build_live

from isaac_threrisaifuture import cli
from isaac_threrisaifuture import live_evaluation as le
from isaac_threrisaifuture.baselines import RandomPolicy
from isaac_threrisaifuture.checkpoint_policy import CheckpointPolicy, InvalidPolicyOutput
from isaac_threrisaifuture.checkpoints import CheckpointError
from isaac_threrisaifuture.encoding import OBSERVATION_SIZE
from isaac_threrisaifuture.episodes import EpisodeFault
from isaac_threrisaifuture.live import LiveBudgetExpired
from isaac_threrisaifuture.observation import BridgeTimeout, ProtocolError
from isaac_threrisaifuture.training import TrainingConfig, train

OBS = np.zeros(OBSERVATION_SIZE, dtype=np.float32)


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class FakeHello:
    def model_dump(self, mode: str) -> dict[str, Any]:
        return {"type": "hello_ack", "session_id": "s" * 32, "game": {"provenance": "unavailable"}}


class FakeClient:
    instances: list["FakeClient"] = []

    def __init__(self, config: Any, on_hello: Any) -> None:
        self.config = config
        self.on_hello = on_hello
        self.latest: tuple[str, int] | None = None
        self.closed = False
        self.fail_connect: BaseException | None = None
        FakeClient.instances.append(self)

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.closed = True

    @property
    def address(self) -> tuple[str, int]:
        return ("127.0.0.1", 1)

    def connect(self) -> FakeHello:
        if self.fail_connect is not None:
            raise self.fail_connect
        self.latest = ("s" * 32, 1)
        self.on_hello(FakeHello())
        return FakeHello()


class FakeEnv:
    """Scripted live env: each step entry is 'ok', an outcome, 'fault' or an exception."""

    def __init__(self, script: list[Any], clock: Clock, step_seconds: float = 0.1) -> None:
        self.script = list(script)
        self.clock = clock
        self.step_seconds = step_seconds
        self.actions: list[list[int]] = []
        self.resets = 0
        self.faults = 0
        self.closed = False
        self.reset_error: BaseException | None = None
        self.frame = 0

    def reset(self) -> tuple[Any, dict[str, Any]]:
        if self.reset_error is not None:
            raise self.reset_error
        self.resets += 1
        return OBS, {"episode_id": self.resets, "frame_id": self.frame}

    def step(self, action: Any) -> tuple[Any, float, bool, bool, dict[str, Any]]:
        self.actions.append([int(a) for a in action])
        self.clock.now += self.step_seconds
        entry = self.script.pop(0) if self.script else "ok"
        if isinstance(entry, BaseException):
            raise entry
        if entry == "fault":
            self.faults += 1
            return OBS, 0.0, False, True, {"fault": "boom", "outcome": None}
        self.frame += 3
        info = {"episode_id": self.resets, "frame_id": self.frame, "outcome": None}
        if entry in ("death", "cleared", "timeout"):
            info["outcome"] = entry
            return OBS, 1.0, entry != "timeout", entry == "timeout", info
        return OBS, 0.5, False, False, info

    def close(self) -> None:
        self.closed = True


class TrackingPolicy(RandomPolicy):
    def __init__(self, clock: Clock | None = None, act_seconds: float = 0.0) -> None:
        super().__init__()
        self.events: list[Any] = []
        self.clock = clock
        self.act_seconds = act_seconds

    def reset(self, seed: int) -> None:
        self.events.append(("reset", seed))
        super().reset(seed)

    def act(self, observation: Any) -> Any:
        self.events.append("act")
        if self.clock is not None:
            self.clock.now += self.act_seconds
        return super().act(observation)


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch) -> Any:
    clock = Clock()
    FakeClient.instances = []
    env_box: dict[str, Any] = {}

    def factory(client: Any, **kwargs: Any) -> FakeEnv:
        env_box["kwargs"] = kwargs
        return env_box["env"]

    monkeypatch.setattr(le, "monotonic", clock)
    monkeypatch.setattr(le, "_RecordingClient", FakeClient)
    monkeypatch.setattr(le, "make_live_env", factory)

    class H:
        def __init__(self) -> None:
            self.clock = clock
            self.env_box = env_box

        def env(self, script: list[Any], **kwargs: Any) -> FakeEnv:
            env_box["env"] = FakeEnv(script, clock, **kwargs)
            return env_box["env"]

    return H()


def options(tmp_path: Path, **changes: Any) -> le.FrozenLiveOptions:
    values: dict[str, Any] = dict(policy="random", out_dir=tmp_path, steps=5, minutes=1.0)
    values.update(changes)
    return le.FrozenLiveOptions(**values)


def log_of(result: le.FrozenLiveResult) -> list[dict[str, Any]]:
    lines = (result.logs / "live.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines]


def events(result: le.FrozenLiveResult, kind: str) -> list[Any]:
    return [r["data"] for r in log_of(result) if r["event"] == kind]


# --- options -------------------------------------------------------------------------------


def test_defaults_are_the_pilot_caps(tmp_path: Path) -> None:
    opts = le.FrozenLiveOptions(policy="random", out_dir=tmp_path)
    assert (opts.steps, opts.minutes, opts.max_faults) == (2000, 6.0, 0)
    assert opts.operator_assistance == "unknown"


@pytest.mark.parametrize(
    "changes",
    [
        {"minutes": float("nan")},
        {"minutes": float("inf")},
        {"minutes": 0.0},
        {"minutes": -1.0},
        {"minutes": 481.0},
        {"minutes": True},
        {"steps": 0},
        {"steps": True},
        {"steps": 2.5},
        {"steps": le.MAX_STEPS + 1},
        {"accept_timeout": float("nan")},
        {"accept_timeout": 0.0},
        {"max_faults": -1},
        {"operator_assistance": "autonomous"},
        {"policy": "latest"},
        {"policy": "checkpoint"},
        {"policy": "checkpoint", "checkpoint": Path("x")},
        {"checkpoint": Path("x")},
        {"expected_config_hash": "abc"},
        {"expected_training_seed": 3},
    ],
)
def test_invalid_options_rejected(tmp_path: Path, changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        options(tmp_path, **changes)


# --- lifecycle with fakes ------------------------------------------------------------------


def test_step_cap_stops_without_extra_action_and_logs_partial_segment(
    harness: Any, tmp_path: Path
) -> None:
    env = harness.env([])
    result = le.run_frozen_live(options(tmp_path, steps=5))
    assert (result.status, result.stop_reason, result.exit_code) == ("completed", "step_cap", 0)
    assert len(env.actions) == result.attempted == result.completed == 5
    assert env.closed and FakeClient.instances[0].closed
    (segment,) = events(result, "segment")
    assert segment["end"] == "stopped" and segment["steps"] == 5
    assert segment["reward_return"] == pytest.approx(2.5)
    summary = events(result, "summary")[-1]
    assert summary["attempted_decisions"] == summary["completed_decisions"] == 5
    assert summary["operator_assistance"] == "unknown"
    config = events(result, "configuration")[0]
    assert config["initial_room"] == config["character_build"] == "unknown"
    assert config["action_repeat"] == harness.env_box["kwargs"]["action_repeat"] == 3
    assert harness.env_box["kwargs"]["max_faults"] == 0
    assert events(result, "hello")


def test_single_absolute_deadline_reaches_env_and_accept(harness: Any, tmp_path: Path) -> None:
    harness.env([])
    le.run_frozen_live(options(tmp_path, minutes=2.0, accept_timeout=600.0))
    deadline = harness.env_box["kwargs"]["run_deadline"]
    assert deadline == pytest.approx(1000.0 + 120.0)
    assert FakeClient.instances[0].config.accept_timeout == pytest.approx(120.0)


def test_deadline_during_act_sends_no_action(harness: Any, tmp_path: Path) -> None:
    env = harness.env([])
    policy = TrackingPolicy(harness.clock, act_seconds=61.0)
    result = le.run_frozen_live(options(tmp_path, steps=50), policy)
    assert result.stop_reason == "deadline" and result.status == "completed"
    assert env.actions == [] and result.attempted == 0
    assert env.closed


def test_deadline_between_steps(harness: Any, tmp_path: Path) -> None:
    env = harness.env([], step_seconds=25.0)
    result = le.run_frozen_live(options(tmp_path, steps=50))
    assert result.stop_reason == "deadline" and len(env.actions) == 3


def test_backend_budget_expiry_is_deadline_not_failure(harness: Any, tmp_path: Path) -> None:
    env = harness.env(["ok", LiveBudgetExpired("Live wall-time budget exhausted")])
    result = le.run_frozen_live(options(tmp_path, steps=50))
    assert (result.stop_reason, result.status, result.exit_code) == ("deadline", "completed", 0)
    assert (result.attempted, result.completed) == (2, 1)
    assert env.closed and not events(result, "failure")


def test_policy_reset_at_every_segment_including_death_and_fault(
    harness: Any, tmp_path: Path
) -> None:
    env = harness.env(["ok", "death", "ok", "fault", "timeout", "ok"])
    policy = TrackingPolicy()
    result = le.run_frozen_live(options(tmp_path, steps=6, policy_seed=40, max_faults=1), policy)
    resets = [e for e in policy.events if e != "act"]
    assert resets == [("reset", 40), ("reset", 41), ("reset", 42), ("reset", 43)]
    # every reset happens before the first act of its segment
    assert policy.events[:2] == [("reset", 40), "act"]
    assert env.resets == 4
    ends = [s["end"] for s in events(result, "segment")]
    assert ends == ["death", "fault", "timeout", "stopped"]
    assert (result.attempted, result.completed) == (6, 5)


def test_no_reset_after_cap_on_terminal_step(harness: Any, tmp_path: Path) -> None:
    env = harness.env(["ok", "death"])
    result = le.run_frozen_live(options(tmp_path, steps=2))
    assert env.resets == 1 and result.stop_reason == "step_cap"


def test_tolerated_fault_is_not_success(harness: Any, tmp_path: Path) -> None:
    harness.env(["fault"])
    result = le.run_frozen_live(options(tmp_path, steps=3, max_faults=1))
    assert result.stop_reason == "step_cap"
    assert (result.status, result.exit_code, result.faults) == ("failed", 1, 1)


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (EpisodeFault("fault budget exceeded"), "fault"),
        (ProtocolError("bad json"), "protocol_error"),
        (KeyboardInterrupt(), "operator_interrupt"),
    ],
)
def test_step_failures_close_and_summarize(
    harness: Any, tmp_path: Path, error: BaseException, reason: str
) -> None:
    env = harness.env(["ok", error])
    result = le.run_frozen_live(options(tmp_path, steps=10))
    assert result.stop_reason == reason
    assert env.closed and FakeClient.instances[0].closed
    summary = events(result, "summary")[-1]
    assert summary["stop_reason"] == reason and summary["completed_decisions"] == 1
    (segment,) = events(result, "segment")
    assert segment["steps"] == 1
    if reason == "operator_interrupt":
        assert (result.status, result.exit_code) == ("interrupted", 0)
        assert segment["end"] == "stopped"
    else:
        assert (result.status, result.exit_code) == ("failed", 1)
        assert segment["end"] == reason


def test_wrapped_protocol_error_stops_as_protocol_error(harness: Any, tmp_path: Path) -> None:
    fault = EpisodeFault("Episode 1 fault: bad")
    fault.__cause__ = ProtocolError("bad")
    harness.env([fault])
    assert le.run_frozen_live(options(tmp_path)).stop_reason == "protocol_error"


class BadPolicy(RandomPolicy):
    def act(self, observation: Any) -> Any:
        raise InvalidPolicyOutput("out of range")


def test_bad_model_output_stops_and_closes(harness: Any, tmp_path: Path) -> None:
    env = harness.env([])
    result = le.run_frozen_live(options(tmp_path), BadPolicy())
    assert (result.stop_reason, result.exit_code) == ("policy_error", 1)
    assert env.actions == [] and env.closed and FakeClient.instances[0].closed


def test_reset_failure_closes_everything(harness: Any, tmp_path: Path) -> None:
    env = harness.env([])
    env.reset_error = EpisodeFault("no playable state")
    result = le.run_frozen_live(options(tmp_path))
    assert (result.stop_reason, result.exit_code) == ("fault", 1)
    assert env.closed and FakeClient.instances[0].closed
    assert events(result, "summary")[-1]["status"] == "failed"


def test_env_creation_failure_closes_client_and_reraises(
    harness: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("cannot build env")

    monkeypatch.setattr(le, "make_live_env", broken)
    with pytest.raises(RuntimeError):
        le.run_frozen_live(options(tmp_path))
    assert FakeClient.instances[0].closed
    (session,) = (tmp_path / "sessions").iterdir()
    summary = [json.loads(x) for x in (session / "live.jsonl").read_text().splitlines()][-1]
    assert summary["event"] == "summary" and summary["data"]["status"] == "failed"


def test_accept_timeout_is_a_failure(harness: Any, tmp_path: Path, monkeypatch: Any) -> None:
    class Silent(FakeClient):
        def connect(self) -> FakeHello:
            raise BridgeTimeout("No observer connected")

    monkeypatch.setattr(le, "_RecordingClient", Silent)
    harness.env([])
    result = le.run_frozen_live(options(tmp_path))
    assert (result.stop_reason, result.exit_code) == ("connection_timeout", 1)
    assert FakeClient.instances[0].closed and result.attempted == 0


# --- frozen checkpoint ---------------------------------------------------------------------


@pytest.fixture(scope="module")
def trained(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("synthetic-live-eval")
    result = train(
        TrainingConfig.model_validate(RAW_CONFIG),
        CFG_HASH,
        seed=SEED,
        env_factory=synthetic_env,
        out_dir=out,
    )
    assert result.checkpoint_id is not None
    return out / "checkpoints" / result.checkpoint_id


@pytest.fixture
def checkpoint(trained: Path, tmp_path: Path) -> Path:
    copy = tmp_path / "ckpt" / trained.name
    shutil.copytree(trained, copy)
    return copy


def checkpoint_options(tmp_path: Path, path: Path, **changes: Any) -> le.FrozenLiveOptions:
    return options(
        tmp_path / "out",
        policy="checkpoint",
        checkpoint=path,
        expected_config_hash=CFG_HASH,
        **changes,
    )


def test_incompatible_checkpoint_rejected_before_listening(
    harness: Any, tmp_path: Path, checkpoint: Path
) -> None:
    opts = options(
        tmp_path / "out", policy="checkpoint", checkpoint=checkpoint, expected_config_hash="0" * 64
    )
    with pytest.raises(CheckpointError):
        le.run_frozen_live(opts)
    assert FakeClient.instances == [] and not (tmp_path / "out").exists()


def test_frozen_checkpoint_never_learns_saves_or_updates_normalizer(
    harness: Any, tmp_path: Path, checkpoint: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sb3_contrib import RecurrentPPO
    from stable_baselines3.common.vec_env import VecNormalize

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("learn/save called during frozen evaluation")

    for owner, name in ((RecurrentPPO, "learn"), (RecurrentPPO, "save"), (VecNormalize, "save")):
        monkeypatch.setattr(owner, name, forbidden)
    harness.env(["ok", "death", "ok"])
    policy = le.load_policy(checkpoint_options(tmp_path, checkpoint, steps=6))
    assert isinstance(policy, CheckpointPolicy)
    stats = policy._normalizer.obs_rms
    mean, var, count = stats.mean.copy(), stats.var.copy(), stats.count
    result = le.run_frozen_live(checkpoint_options(tmp_path, checkpoint, steps=6), policy)
    assert (result.status, result.attempted) == ("completed", 6)
    assert np.array_equal(stats.mean, mean) and np.array_equal(stats.var, var)
    assert stats.count == count
    config = events(result, "configuration")[0]
    assert config["policy"]["model_sha256"] == policy.identity.model_sha256
    assert config["policy_kind"] == "checkpoint"


def test_recurrent_state_cleared_on_new_segment(
    harness: Any, tmp_path: Path, checkpoint: Path
) -> None:
    harness.env(["ok", "death"])
    policy = le.load_policy(checkpoint_options(tmp_path, checkpoint, steps=3))
    assert isinstance(policy, CheckpointPolicy)
    starts: list[bool] = []
    original = policy.act

    def spy(observation: Any) -> Any:
        starts.append(bool(policy._episode_start[0]))
        return original(observation)

    policy.act = spy  # type: ignore[method-assign]
    le.run_frozen_live(checkpoint_options(tmp_path, checkpoint, steps=3), policy)
    assert starts == [True, False, True]


def test_artifact_change_during_run_invalidates_result(
    harness: Any, tmp_path: Path, checkpoint: Path
) -> None:
    policy = le.load_policy(checkpoint_options(tmp_path, checkpoint, steps=3))
    assert isinstance(policy, CheckpointPolicy)
    model = policy._paths["model"]

    class Tamper(FakeEnv):
        def step(self, action: Any) -> Any:
            model.write_bytes(model.read_bytes() + b"x")
            return super().step(action)

    harness.env_box["env"] = Tamper([], harness.clock)
    result = le.run_frozen_live(checkpoint_options(tmp_path, checkpoint, steps=3), policy)
    assert (result.status, result.exit_code, result.identity_valid) == ("invalid", 3, False)
    assert result.completed == 3  # gameplay happened, but the result is invalid
    assert events(result, "identity_changed")


# --- CLI -----------------------------------------------------------------------------------


def run_cli(monkeypatch: pytest.MonkeyPatch, *argv: str) -> int:
    monkeypatch.setattr(sys, "argv", ["isaac", "eval-live", *argv])
    try:
        cli.main()
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


@pytest.mark.parametrize(
    "argv",
    [
        ["--policy", "random"],
        ["--policy", "random", "--confirmed-save-slot", "1"],
        ["--policy", "checkpoint", "--confirmed-save-slot", "2"],
        ["--policy", "random", "--checkpoint", "x", "--confirmed-save-slot", "2"],
        ["--policy", "random", "--minutes", "nan", "--confirmed-save-slot", "2"],
        ["--policy", "random", "--steps", "0", "--confirmed-save-slot", "2"],
        ["--policy", "random", "--launch", "--confirmed-save-slot", "2"],
        ["--policy", "random", "--resume", "--confirmed-save-slot", "2"],
        ["--policy", "random", "--operator-assistance", "auto", "--confirmed-save-slot", "2"],
    ],
)
def test_cli_rejects_before_listening(
    harness: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, argv: list[str]
) -> None:
    assert run_cli(monkeypatch, *argv, "--out-dir", str(tmp_path)) == 2
    assert FakeClient.instances == []


def test_cli_wrong_checkpoint_hash_exit_2(
    harness: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, checkpoint: Path
) -> None:
    code = run_cli(
        monkeypatch,
        *("--policy", "checkpoint", "--checkpoint", str(checkpoint)),
        *("--expected-config-hash", "0" * 64, "--confirmed-save-slot", "2"),
        *("--out-dir", str(tmp_path / "out")),
    )
    assert code == 2 and FakeClient.instances == []


def test_cli_exit_code_follows_result(
    harness: Any, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: Any
) -> None:
    harness.env(["fault"])
    common = ("--policy", "random", "--confirmed-save-slot", "2", "--out-dir", str(tmp_path))
    assert run_cli(monkeypatch, *common, "--steps", "3", "--max-faults", "1") == 1
    assert '"status": "failed"' in capsys.readouterr().out
    harness.env([])
    assert run_cli(monkeypatch, *common, "--steps", "3") == 0


# --- synthetic Lua + socket end-to-end (not Isaac evidence) -------------------------------


@pytest.fixture
def lua_room() -> Any:
    port = free_port()
    lua = build_live(max_restarts=5)
    shim = Shim(port)
    lua.globals().PY = shim
    lua.execute(SOCKET_SHIM)
    lua.execute("AUTO_START=true; SEND_LIMIT=1e9; ROOM_ENTITIES={ make_enemy(1,160,200,10,10) }")
    game = Game(lua)
    game.every = "local e=ROOM_ENTITIES[1]; e.HitPoints=math.max(1,e.HitPoints-0.01)"
    game.start()
    yield port
    game.stop.set()
    game.join(timeout=5)
    shim.close()
    assert game.error is None


def test_synthetic_lua_frozen_checkpoint_run(
    lua_room: int, tmp_path: Path, checkpoint: Path
) -> None:
    opts = checkpoint_options(tmp_path, checkpoint, steps=30, port=lua_room, accept_timeout=10.0)
    result = le.run_frozen_live(opts)
    assert (result.status, result.stop_reason) == ("completed", "step_cap")
    assert result.attempted == result.completed == 30
    kinds = [r["event"] for r in log_of(result)]
    assert kinds[:3] == ["configuration", "listening", "hello"]
    assert kinds[-1] == "summary" and "fault" not in kinds
    text = (result.logs / "live.jsonl").read_text(encoding="utf-8")
    oracle = (result.logs / "oracle.jsonl").read_text(encoding="utf-8")
    assert "enemy_damaged" in oracle and "enemy_damaged" not in text
    start = events(result, "segment_start")[0]
    assert len(start["session_id"]) == 32 and "game_epoch" in start
