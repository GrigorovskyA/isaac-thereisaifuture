"""Offline behavioral tests of the opt-in combat-experience gate (combat-experience-gate-v1).

A scripted fake client drives the real LiveBackend -> IsaacCombatEnv -> FaultTolerantEnv stack;
no game, socket or real training is involved. Synthetic results prove mechanics only.
"""

import json
import sys
import time
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from test_checkpoint_policy import RAW_CONFIG, synthetic_env
from test_entity_transport import entity_snapshot

from isaac_threrisaifuture import combat_gate, live
from isaac_threrisaifuture.checkpoints import config_hash, latest_checkpoint_dir, load_checkpoint
from isaac_threrisaifuture.combat_gate import (
    READY_NAME,
    REQUEST_NAME,
    CombatGateEnv,
    CombatGateExpired,
    GateConfig,
    GateError,
    ReadinessAck,
    ReadinessRequest,
    classify,
    write_readiness,
)
from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.live import (
    LiveBudgetExpired,
    LiveRunOptions,
    LiveSnapshot,
    _train_run,
    make_live_env,
)
from isaac_threrisaifuture.observation import BridgeTimeout, PeerDisconnected, ProtocolError
from isaac_threrisaifuture.observer_client import ObserverConfig
from isaac_threrisaifuture.training import TrainingConfig, train

SESSION = "a" * 32
NEW_SESSION = "b" * 32


def snap(frame, *, session=SESSION, epoch=1, visit=1, enemies=None, clear=False, dead=False,
         overflow=0, status="active"):  # fmt: skip
    raw = entity_snapshot(session, frame, frame_id=frame, game_epoch=epoch, room_visit=visit)
    raw.update(frame_id=frame, game_epoch=epoch, status=status)
    raw["room"]["visit_id"] = visit
    raw["oracle"] = (
        None
        if status == "unavailable"
        else {
            "room_clear": clear,
            "player_dead": dead,
            "enemies": [
                {"entity_id": i, "hp": hp, "max_hp": 10.0} for i, hp in (enemies or {}).items()
            ],
            "enemy_overflow": overflow,
        }
    )
    if status == "unavailable":
        raw.update(frame_id=None, room=None, player=None, reason="not_in_game")
        raw["entity_frame"] = None
    return LiveSnapshot.model_validate_json(json.dumps(raw))


class World:
    """Scripted live client: one snapshot per take(); records every command."""

    def __init__(self, *, fight_len=None, operator=None, die_at=None):
        self.session, self.epoch, self.visit = SESSION, 1, 1
        self.enemies: dict[int, float] = {}
        self.clear = self.dead = self.dead_shown = False
        self.status = "active"
        self.frame = 0
        self.fight_len, self.die_at, self.actions_in_room = fight_len, die_at, 0
        self.operator = operator
        self.commands: list[tuple[str, int]] = []
        self.connected, self.failure, self.connects, self.closed = True, None, 0, False
        self.config = ObserverConfig()
        self.take_errors: list[Exception] = []
        self.hooks: dict[int, object] = {}  # action count -> callable(world)
        self.actions = 0
        self.overflow = 0
        self.queue: list[LiveSnapshot] = []  # delivered by the next drain()
        self.stall = 0  # takes that time out while staying connected
        self.clock: FakeClock | None = None
        self.on_connect = None
        self.on_stall = None

    def snapshot(self):
        return snap(self.frame, session=self.session, epoch=self.epoch, visit=self.visit,
                    enemies=self.enemies, clear=self.clear, dead=self.dead,
                    overflow=self.overflow, status=self.status)  # fmt: skip

    def enqueue(self, **changes):
        """Queue one newer snapshot (changes apply to it only) before the next action."""
        saved = {name: getattr(self, name) for name in changes}
        for name, value in changes.items():
            setattr(self, name, value)
        self.frame += 1
        self.queue.append(self.snapshot())
        for name, value in saved.items():
            setattr(self, name, value)

    def enter_room(self, enemies):
        self.visit += 1
        self.enemies, self.clear, self.actions_in_room = dict(enemies), not enemies, 0

    def take(self, timeout):
        if self.clock is not None:
            self.clock.now += self.clock.tick
        if self.take_errors:
            error = self.take_errors.pop(0)
            self.connected = False
            raise error
        self.frame += 1
        if self.dead and self.dead_shown:  # natural autonomous restart into an empty room
            self.session, self.epoch, self.visit = NEW_SESSION, self.epoch + 1, 1
            self.enemies, self.clear, self.dead, self.actions_in_room = {}, False, False, 0
        self.dead_shown = self.dead
        if self.stall:
            self.stall -= 1
            if self.on_stall is not None:
                self.on_stall(self)
            raise BridgeTimeout("No live snapshot before the deadline")
        if self.operator is not None:
            self.operator(self)
        if self.fight_len is not None and self.actions_in_room >= self.fight_len:
            if self.enemies:
                self.enemies = {}
            elif not self.clear:
                self.clear = True
        return self.snapshot()

    def drain(self):
        queued, self.queue = self.queue, []
        return queued

    def command(self, kind, reference, **kwargs):
        self.commands.append((kind, self.frame))
        if kind == "action":
            self.actions += 1
            self.actions_in_room += 1
            if self.die_at == self.actions:
                self.dead = True
            hook = self.hooks.pop(self.actions, None)
            if hook is not None:
                hook(self)
        return SimpleNamespace(status="accepted", frame_id=self.frame)

    def connect(self):
        self.connected = True
        self.connects += 1
        if self.on_connect is not None:
            self.on_connect(self)

    def close_peer(self):
        self.connected = False

    def close(self):
        self.closed = True

    def action_count(self):
        return sum(kind == "action" for kind, _ in self.commands)


class FakeClock:
    """Monotonic clock for live/gate deadlines; every take() advances it (no sleeping)."""

    def __init__(self, tick=0.05):
        self.now, self.tick = 1000.0, tick

    def monotonic(self):
        return self.now

    def __getattr__(self, name):
        return getattr(time, name)


@pytest.fixture
def clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(live, "time", fake)
    monkeypatch.setattr(combat_gate, "time", fake)
    return fake


class Operator:
    """Human stand-in: on each new request, walk into a fight, then confirm readiness."""

    def __init__(self, session_dir, *, navigate=True, respond=None, enemies=None):
        self.session_dir, self.navigate = session_dir, navigate
        self.respond = respond  # max handoffs answered; None = always
        self.enemies = enemies or {1: 10.0, 2: 10.0}
        self.moved: set[str] = set()
        self.acked: set[str] = set()

    def request(self):
        path = self.session_dir / "combat_gate" / REQUEST_NAME
        return ReadinessRequest.model_validate_json(path.read_bytes()) if path.exists() else None

    def __call__(self, world):
        request = self.request()
        if request is None or request.state != "waiting_for_operator":
            return
        if self.respond is not None and request.handoff > self.respond:
            return
        if self.navigate and request.request_id not in self.moved:
            self.moved.add(request.request_id)
            world.enter_room(self.enemies)
            return
        if (request.request_id not in self.acked and request.eligibility == "combat"
                and request.room_visit == world.visit):  # fmt: skip
            self.acked.add(request.request_id)
            write_readiness(self.session_dir)


def gated(world, tmp_path, *, cap=5.0, deadline=None, records=None, stale=1.0):
    rows = records if records is not None else []
    env = make_live_env(world, max_faults=5, record=lambda *r: rows.append(r),
                        run_deadline=deadline)  # fmt: skip
    return CombatGateEnv(
        env,
        GateConfig(
            tmp_path / "combat_gate", wait_cap_seconds=cap, poll_seconds=0.05, stale_seconds=stale
        ),  # fmt: skip
        run_deadline=deadline,
        record=lambda *r: rows.append(r),
    )


def gate_events(records, name=None):
    rows = [row[1] for row in records if row[0] == "combat_gate"]
    return [row for row in rows if name is None or row["event"] == name]


# --- eligibility -------------------------------------------------------------------------


def test_classify_is_conservative():
    combat = snap(2, enemies={1: 5.0})
    assert classify(None) == "unavailable"
    assert classify(combat) == "combat"
    assert classify(snap(2, enemies={1: 5.0}, status="paused")) == "paused"
    assert classify(snap(2, enemies={1: 5.0}, dead=True)) == "dead"
    assert classify(snap(2, enemies={1: 5.0}, overflow=1)) == "ambiguous"
    assert classify(snap(2, enemies={1: 5.0}, clear=True)) == "cleared"
    assert classify(snap(2)) == "empty"
    assert classify(snap(2, enemies={1: 0.0})) == "empty"
    assert classify(combat, snap(1, visit=2)) == "transition"
    assert classify(combat, snap(1, epoch=2)) == "transition"
    assert classify(combat, snap(1, enemies={1: 5.0})) == "combat"


# --- handoff behavior --------------------------------------------------------------------


def test_empty_start_without_operator_acts_never_and_stops_at_cap(tmp_path):
    world, records = World(), []
    env = gated(world, tmp_path, cap=0.3, records=records)
    with pytest.raises(RuntimeError, match="reset"):
        env.step(np.array([1, 1]))
    with pytest.raises(CombatGateExpired):
        env.reset()
    assert world.action_count() == 0
    assert env.state == "stopped" and env.env.faults == 0
    request = ReadinessRequest.model_validate_json(
        (tmp_path / "combat_gate" / REQUEST_NAME).read_bytes()
    )
    assert request.state == "stopped" and request.eligibility == "empty"
    summary = gate_events(records, "summary")[0]
    assert summary["combat_decisions"] == 0 and summary["wait_snapshots"] > 0
    with pytest.raises(GateError, match="stopped"):
        write_readiness(tmp_path)
    env.close()
    assert world.closed


def test_enemy_spawn_does_not_steal_control_without_readiness(tmp_path):
    world, records = World(), []
    env = gated(world, tmp_path, cap=0.3, records=records)

    def spawn(w):
        if w.frame == 3:
            w.enemies = {1: 10.0}

    world.operator = spawn
    with pytest.raises(CombatGateExpired):
        env.reset()
    assert world.action_count() == 0
    assert any(e["eligibility"] == "combat" for e in gate_events(records, "observed"))
    assert not gate_events(records, "combat_resumed")


def test_readiness_resumes_combat_clear_hands_off_and_releases(tmp_path):
    operator = Operator(tmp_path)
    world, records = World(fight_len=4, operator=operator), []
    env = gated(world, tmp_path, records=records)
    obs, info = env.reset()
    assert env.state == "combat_active"
    assert "eligibility" not in info and "combat_gate" not in info
    np.testing.assert_array_equal(obs, encode(env.backend.latest.entity_frame).vector)
    rewards, done = [], False
    while not done:
        _, reward, terminated, truncated, info = env.step(np.array([1, 2]))
        rewards.append(reward)
        done = terminated or truncated
    # LiveBackend derives events from frame deltas and declares no terminal coverage, so a
    # derived clear cannot rule out an unreported death: unknown, truncated, never "cleared".
    assert truncated and not terminated and info["outcome"] == "unknown"
    assert info["episode"]["room_cleared"] is True and info["episode"]["died"] is None
    parts = info["reward_components"]
    assert parts["room_clear"] == 8
    assert parts["enemy_damage"] == parts["enemy_kill"] == 0
    assert parts["time"] < 0 and rewards[-1] == pytest.approx(sum(parts.values()))
    assert all(r < 0 for r in rewards[:-1])
    assert world.commands[-1][0] == "release"
    with pytest.raises(RuntimeError, match="reset"):
        env.step(np.array([1, 2]))  # the ended episode is never stepped again
    actions_before = world.action_count()
    env.reset()  # second handoff: the operator walks into another fight and confirms
    assert world.action_count() == actions_before
    assert env.stats.handoffs == 2 and env.stats.accepted == 2
    assert env.stats.outcomes == {"unknown": 1}
    assert [e["state"] for e in gate_events(records, "combat_resumed")] == ["combat_active"] * 2


def test_natural_restart_waits_and_rejects_prior_epoch_readiness(tmp_path):
    world, records = World(die_at=2), []
    world.enemies = {1: 10.0}
    env = gated(world, tmp_path, records=records)
    world.operator = Operator(tmp_path, navigate=False)
    env.reset()
    old = (world.session, world.epoch, world.visit)
    world.operator = None
    _, reward, terminated, _, info = env.step(np.array([0, 0]))
    if not terminated:
        _, reward, terminated, _, info = env.step(np.array([0, 0]))
    assert terminated and info["outcome"] == "death" and reward < -20
    actions = world.action_count()
    gate_dir = tmp_path / "combat_gate"
    stage = {"n": 0}

    def operator(w):
        request = ReadinessRequest.model_validate_json((gate_dir / REQUEST_NAME).read_bytes())
        if stage["n"] == 0 and request.game_epoch == 2:
            stale = ReadinessAck(
                request_id=request.request_id,
                session_id=old[0],
                game_epoch=old[1],
                room_visit=old[2],
                acked_at=request.issued_at,
            )
            (gate_dir / READY_NAME).write_text(stale.model_dump_json())
            stage["n"] = 1
        elif stage["n"] == 1:
            w.enter_room({3: 10.0})
            stage["n"] = 2
        elif stage["n"] == 2 and request.eligibility == "combat" and request.room_visit == w.visit:
            write_readiness(tmp_path)
            stage["n"] = 3

    world.operator = operator
    env.reset()
    assert world.action_count() == actions
    assert env.stats.rejected["cross_session"] == 1
    assert env.backend.latest.game_epoch == 2 and env.state == "combat_active"


def test_invalid_stale_replayed_and_mismatched_readiness_is_rejected(tmp_path):
    world, records = World(), []
    world.enemies = {1: 10.0}
    env = gated(world, tmp_path, records=records)
    gate_dir = tmp_path / "combat_gate"
    first = {}

    def bad_acks(w):
        request = ReadinessRequest.model_validate_json((gate_dir / REQUEST_NAME).read_bytes())
        if request.eligibility != "combat":
            return
        base = dict(request_id=request.request_id, session_id=SESSION, game_epoch=1,
                    room_visit=w.visit, acked_at=request.issued_at + 0.001)  # fmt: skip
        attempts = [
            "not json",
            "x" * 5000,
            {**base, "request_id": "0" * 32},
            {**base, "acked_at": request.issued_at - 10},
            {**base, "acked_at": request.issued_at + 3600},
            {**base, "session_id": NEW_SESSION},
            {**base, "game_epoch": 9},
            {**base, "room_visit": w.visit + 5},
            base,
        ]
        step = first.setdefault("i", 0)
        if step < len(attempts):
            item = attempts[step]
            text = item if isinstance(item, str) else ReadinessAck(**item).model_dump_json()
            (gate_dir / READY_NAME).write_text(text)
            first["i"] = step + 1
            first["accepted"] = base

    world.operator = bad_acks
    env.reset()
    assert dict(env.stats.rejected) == {
        "invalid": 2, "stale_request": 1, "predates_wait": 1, "future_timestamp": 1,
        "cross_session": 1, "cross_epoch": 1, "cross_room": 1,
    }  # fmt: skip
    assert env.state == "combat_active" and world.action_count() == 0
    replay = first["accepted"]
    env.step(np.array([0, 0]))
    world.enemies = {}
    world.clear = True
    env.step(np.array([0, 0]))  # room clears: terminal, then a fresh handoff

    def replay_then_quit(w):
        (gate_dir / READY_NAME).write_text(ReadinessAck(**replay).model_dump_json())
        w.operator = None

    world.operator = replay_then_quit
    env.config = GateConfig(gate_dir, wait_cap_seconds=0.3, poll_seconds=0.05)
    with pytest.raises(CombatGateExpired):
        env.reset()
    assert env.stats.rejected["replayed"] == 1


def test_readiness_outside_combat_is_rejected(tmp_path):
    world = World()
    env = gated(world, tmp_path, cap=0.3)
    acked = []

    def operator(w):
        request = (tmp_path / "combat_gate" / REQUEST_NAME).read_bytes()
        if not acked and ReadinessRequest.model_validate_json(request).session_id:
            write_readiness(tmp_path)
            acked.append(1)

    world.operator = operator
    with pytest.raises(CombatGateExpired):
        env.reset()
    assert env.stats.rejected["not_eligible"] == 1 and world.action_count() == 0


def test_global_deadline_stops_wait_without_renewal(tmp_path):
    import time

    world, records = World(), []
    env = gated(world, tmp_path, cap=60.0, deadline=time.monotonic() + 0.3, records=records)
    with pytest.raises(LiveBudgetExpired) as caught:
        env.reset()
    assert not isinstance(caught.value, CombatGateExpired)
    assert env.state == "stopped" and env.env.faults == 0 and world.action_count() == 0
    assert "LiveBudgetExpired" in gate_events(records, "stopped")[0]["reason"]


def test_manual_wait_damage_is_not_credited(tmp_path):
    world = World()
    gate_dir = tmp_path / "combat_gate"
    done = []

    def operator(w):
        if not done:
            w.enter_room({1: 10.0})
            done.append("entered")
        elif len(done) == 1:
            w.enemies = {1: 2.0}  # operator damages the enemy by hand while waiting
            done.append("hit")
        elif len(done) == 2:
            request = ReadinessRequest.model_validate_json((gate_dir / REQUEST_NAME).read_bytes())
            if request.eligibility == "combat" and request.room_visit == w.visit:
                write_readiness(tmp_path)
                done.append("ack")

    world.operator = operator
    env = gated(world, tmp_path)
    env.reset()
    _, reward, _, _, info = env.step(np.array([0, 0]))
    assert info["reward_components"]["enemy_damage"] == 0.0
    assert reward == pytest.approx(info["reward_components"]["time"]) and reward < 0


def test_disconnect_during_wait_reconnects_and_protocol_error_stops(tmp_path):
    world = World(operator=Operator(tmp_path))
    world.take_errors = [PeerDisconnected("restart closed the session")]
    env = gated(world, tmp_path)
    env.reset()
    assert world.connects == 1 and env.state == "combat_active"

    other = World()
    other.take_errors = [PeerDisconnected("gone")]
    other.failure = ProtocolError("malformed record")
    other_env = gated(other, tmp_path / "second")
    with pytest.raises(ProtocolError):
        other_env.reset()
    assert other_env.state == "stopped" and other.connects == 0


def test_room_change_and_fault_in_combat_end_segment_and_release(tmp_path):
    operator = Operator(tmp_path)
    world, records = World(operator=operator), []
    env = gated(world, tmp_path, records=records)
    env.reset()
    world.hooks[1] = lambda w: w.enter_room({5: 10.0})  # e.g. leaving through an open door
    _, _, terminated, truncated, info = env.step(np.array([0, 0]))
    assert truncated and not terminated and info["gate_exit"] == "room_changed"
    assert world.commands[-1][0] == "release" and env.state == "waiting_for_operator"
    env.reset()

    def epoch_jump(w):
        w.epoch += 1  # epoch changes without an observed death: an infrastructure fault

    world.hooks[world.actions + 1] = epoch_jump
    _, reward, terminated, truncated, info = env.step(np.array([0, 0]))
    assert truncated and "fault" in info and reward == 0.0
    assert env.stats.outcomes == {"room_changed": 1, "fault": 1}
    ended = gate_events(records, "combat_ended")
    assert [e["outcome"] for e in ended] == ["room_changed", "fault"]
    assert world.commands[-1][0] == "release"


# --- training integration ----------------------------------------------------------------


def test_short_fights_over_handoffs_make_a_real_update_and_checkpoint(tmp_path, monkeypatch):
    import isaac_threrisaifuture.training as training

    captured = {}
    original = training.save_checkpoint

    def capture(*args, **kwargs):
        captured["model"], captured["venv"] = kwargs["model"], kwargs["vec_normalize"]
        return original(*args, **kwargs)

    monkeypatch.setattr(training, "save_checkpoint", capture)
    config = TrainingConfig.model_validate(RAW_CONFIG)
    cfg_hash = config_hash(RAW_CONFIG)
    gates = []

    def factory(_):
        world = World(fight_len=5, operator=Operator(tmp_path))
        gates.append(gated(world, tmp_path))
        return gates[-1]

    result = train(config, cfg_hash, seed=7, env_factory=factory, out_dir=tmp_path / "run")
    assert result.stop_reason == "completed" and result.timesteps == 32
    manifest = load_checkpoint(
        latest_checkpoint_dir(tmp_path / "run" / "checkpoints"),
        expected_config_hash=cfg_hash, expected_seed=7,
    )  # fmt: skip
    assert manifest.timesteps == 32 and manifest.parent_checkpoint_id is None
    gate, model, venv = gates[0], captured["model"], captured["venv"]
    assert gate.stats.combat_steps == 32 and gate.stats.handoffs >= 5
    assert gate.stats.wait_snapshots > gate.stats.handoffs  # waits saw frames ...
    assert venv.obs_rms.count == pytest.approx(1 + 32, abs=1e-3)  # ... the normalizer did not
    buffer = model.rollout_buffer
    starts = np.flatnonzero(buffer.episode_starts[:, 0])
    lengths = venv.venv.envs[0].get_episode_lengths()
    assert len(lengths) == gate.stats.outcomes["unknown"] >= 4  # derived clears are unknown
    assert not gate.stats.outcomes["cleared"]
    assert list(starts) == [0, *np.cumsum(lengths)[: len(starts) - 1]]
    terminal = np.cumsum(lengths) - 1
    rewards = buffer.rewards[:, 0]
    assert (rewards[terminal] > 0).all()
    assert (np.delete(rewards, terminal) < 0).all()

    resumed = train(config.model_copy(update={"budget": config.budget.model_copy(
        update={"total_timesteps": 64})}), cfg_hash, seed=7, env_factory=factory,
        out_dir=tmp_path / "run", resume=True)  # fmt: skip
    assert resumed.timesteps == 64
    child = load_checkpoint(latest_checkpoint_dir(tmp_path / "run" / "checkpoints"),
                            expected_config_hash=cfg_hash, expected_seed=7)  # fmt: skip
    assert child.parent_checkpoint_id == manifest.checkpoint_id


def test_interrupted_gated_rollout_reports_unsaved_steps(tmp_path):
    path = tmp_path / "training.yaml"
    path.write_text(yaml.safe_dump(RAW_CONFIG), encoding="utf-8")
    world = World(fight_len=3, operator=Operator(tmp_path, respond=2))
    records = []
    options = LiveRunOptions(
        mode="train",
        out_dir=tmp_path / "out",
        minutes=0.2,
        steps=32,
        config_path=path,
        combat_gate=True,
        gate_wait_minutes=0.01,
    )
    _train_run(world, options, lambda *r: records.append(r), lambda e: None, tmp_path)
    assert records[-2][0] == "budget" and "no new checkpoint" in records[-2][1]
    accounting = records[-1][1]
    assert accounting["event"] == "rollout_accounting"
    assert accounting["reason"].startswith("Operator wait cap expired")
    assert accounting["checkpointed_timesteps"] == 0
    assert accounting["unsaved_steps"] == accounting["combat_decisions"] > 0
    assert not list((tmp_path / "out").rglob("latest.txt"))
    assert world.closed and world.commands[-1][0] == "release"


# --- options and operator command --------------------------------------------------------


def test_gate_is_opt_in_and_wait_cap_is_bounded(tmp_path):
    assert LiveRunOptions(mode="random", out_dir=tmp_path).combat_gate is False
    with pytest.raises(ValueError, match="wait cap"):
        LiveRunOptions(
            mode="random", out_dir=tmp_path, minutes=5, combat_gate=True, gate_wait_minutes=6
        )
    LiveRunOptions(mode="random", out_dir=tmp_path, minutes=0.01)  # default stays valid
    with pytest.raises(ValueError):
        GateConfig(tmp_path, wait_cap_seconds=0)
    with pytest.raises(TypeError, match="LiveBackend"):
        CombatGateEnv(synthetic_env(), GateConfig(tmp_path))


def test_combat_ready_command_writes_only_the_fixed_ack(tmp_path, monkeypatch, capsys):
    from isaac_threrisaifuture import cli

    gate_dir = tmp_path / "combat_gate"
    monkeypatch.setattr(sys, "argv", ["cli", "combat-ready", "--session-dir", str(tmp_path)])
    with pytest.raises(SystemExit):
        cli.main()
    assert "No combat-gate request" in capsys.readouterr().err
    gate_dir.mkdir()
    request = ReadinessRequest(request_id="1" * 32, handoff=1, state="waiting_for_operator",
                               issued_at=1.0, session_id=SESSION, game_epoch=1, room_visit=4,
                               eligibility="combat")  # fmt: skip
    (gate_dir / REQUEST_NAME).write_text(request.model_dump_json())
    cli.main()
    assert "Combat readiness written" in capsys.readouterr().out
    ack = ReadinessAck.model_validate_json((gate_dir / READY_NAME).read_bytes())
    assert (ack.request_id, ack.room_visit, ack.game_epoch) == ("1" * 32, 4, 1)
    assert sorted(p.name for p in gate_dir.iterdir()) == [READY_NAME, REQUEST_NAME]
    with pytest.raises(GateError, match="does not match"):
        write_readiness(tmp_path, "2" * 32)
    unobserved = request.model_copy(update={"session_id": None})
    (gate_dir / REQUEST_NAME).write_text(unobserved.model_dump_json())
    with pytest.raises(GateError, match="No observed"):
        write_readiness(tmp_path)


# --- feedback 1: eligibility is maintained during combat ---------------------------------

A = np.array([1, 2])


def in_fight(tmp_path, records=None):
    world = World()
    world.enemies = {1: 10.0, 2: 10.0}
    env = gated(world, tmp_path, records=records)
    world.operator = Operator(tmp_path, navigate=False)
    env.reset()
    world.operator = None
    assert env.state == "combat_active"
    return world, env


@pytest.mark.parametrize(
    ("change", "reason"), [({"enemies": {}}, "empty"), ({"overflow": 1}, "ambiguous")]
)
def test_eligibility_lost_within_a_step_ends_segment_before_any_next_action(
    tmp_path, change, reason
):
    records: list = []
    world, env = in_fight(tmp_path, records)
    env.step(A)
    for name, value in change.items():  # observed while the step's action plays out
        setattr(world, name, value)
    _, _, terminated, truncated, info = env.step(A)
    assert classify(env.backend.latest) == reason
    assert truncated and not terminated and info["gate_exit"] == reason
    assert info["outcome"] is None and info["reward_components"]["room_clear"] == 0.0
    assert "action_withheld" not in info  # this step's action was sent before the change
    assert env.state == "waiting_for_operator" and world.commands[-1][0] == "release"
    actions = world.action_count()
    with pytest.raises(RuntimeError, match="No gated combat"):
        env.step(A)
    assert world.action_count() == actions == 2
    assert env.stats.outcomes[reason] == 1
    assert gate_events(records, "combat_ended")[-1]["gate_exit"] == reason


@pytest.mark.parametrize(
    ("queued", "reason"),
    [
        ({"enemies": {}}, "empty"),
        ({"overflow": 1}, "ambiguous"),
        ({"status": "paused"}, "paused"),
        ({"status": "unavailable"}, "unavailable"),
        ({"visit": 9}, "room_changed"),
    ],
)
def test_ineligible_queued_snapshot_withholds_the_next_action_and_keeps_events(
    tmp_path, queued, reason
):
    world, env = in_fight(tmp_path)
    env.step(A)
    actions = world.action_count()
    world.enqueue(enemies={1: 4.0, 2: 10.0})  # damage observed before the ineligible state
    world.enqueue(**queued)
    obs, _, terminated, truncated, info = env.step(A)
    assert truncated and not terminated and info["gate_exit"] == reason
    assert info["action_withheld"] == reason
    assert info["reward_components"]["enemy_damage"] > 0  # queued events are kept
    assert info["outcome"] is None and info["reward_components"]["room_clear"] == 0.0
    assert world.action_count() == actions  # the policy's action never reached the game
    assert world.commands[-1][0] == "release" and env.state == "waiting_for_operator"
    assert np.isfinite(obs).all()


def test_queued_death_before_the_next_action_stays_a_terminal_death(tmp_path):
    world, env = in_fight(tmp_path)
    env.step(A)
    actions = world.action_count()
    world.enqueue(dead=True)
    _, reward, terminated, truncated, info = env.step(A)
    assert terminated and not truncated and info["outcome"] == "death" and reward < 0
    assert world.action_count() == actions and env.state == "waiting_for_operator"


def test_eligibility_losses_keep_honest_boundaries_and_normalizer_counts(tmp_path):
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    world = World(operator=Operator(tmp_path))
    world.hooks[3] = lambda w: setattr(w, "enemies", {})  # empty, clear flag still false
    world.hooks[5] = lambda w: w.enqueue(overflow=1)  # queued before action 6
    env = gated(world, tmp_path)
    vec = VecNormalize(DummyVecEnv([lambda: Monitor(env)]), norm_reward=False)
    vec.reset()
    dones, withheld = [], []
    for _ in range(8):
        _, _, done, info = vec.step(np.array([A]))
        dones.append(bool(done[0]))
        withheld.append("action_withheld" in info[0])
    assert vec.obs_rms.count == pytest.approx(1 + 8, abs=1e-3)  # waits never reach it
    assert (
        dones[2] and dones[5] and sum(dones) == 2 and withheld == [False] * 5 + [True] + [False] * 2
    )
    assert world.action_count() == 8 - 1
    assert env.stats.combat_steps == 8 and env.stats.withheld_actions == 1
    assert env.stats.outcomes == {"empty": 1, "ambiguous": 1}
    assert env.stats.handoffs == 3 and env.stats.wait_snapshots > env.stats.handoffs


# --- feedback 1: the handoff deadline bounds every reset, resume and reconnect ------------


def test_readiness_wait_expires_on_the_fake_clock(clock, tmp_path):
    world = World()
    world.clock = clock
    start, deadline = clock.now, clock.now + 100
    env = gated(world, tmp_path, cap=1.0, deadline=deadline)
    with pytest.raises(CombatGateExpired):
        env.reset()
    assert start + 1.0 <= clock.now <= start + 1.0 + clock.tick
    assert world.action_count() == 0 and env.state == "stopped"
    assert env.backend.run_deadline == env.env.run_deadline == deadline  # restored, not renewed
    request = ReadinessRequest.model_validate_json(
        (tmp_path / "combat_gate" / REQUEST_NAME).read_bytes()
    )
    assert request.state == "stopped"


@pytest.mark.parametrize("blocking", ["reconnect_loop", "slow_reset", "slow_return"])
def test_cap_expiry_inside_resume_never_activates_combat(clock, tmp_path, blocking):
    records: list = []
    world = World(fight_len=1, operator=Operator(tmp_path))
    world.clock = clock
    deadline = clock.now + 1000
    env = gated(world, tmp_path, cap=1.0, deadline=deadline, records=records)
    env.reset()
    done = False
    while not done:
        _, _, terminated, truncated, _ = env.step(A)
        done = terminated or truncated
    actions = world.action_count()
    inner, seen, accepts = env.backend.start_episode, [], []

    def blocked_start(scenario, seed):
        seen.append((clock.now, env.backend.run_deadline, env.env.run_deadline))
        if blocking == "slow_reset":
            clock.now += 5.0
        elif blocking == "slow_return":  # succeeds, but only after the cap
            result = inner(scenario, seed)
            clock.now += 5.0
            return result
        else:  # the shared reset keeps reconnecting, as after a long autonomous restart
            world.take_errors = [PeerDisconnected("restart")] * 10_000
            world.on_connect = lambda w: accepts.append((clock.now, w.config.accept_timeout))
        return inner(scenario, seed)

    env.backend.start_episode = blocked_start
    start = clock.now
    with pytest.raises(CombatGateExpired):
        env.reset()
    ((entered, backend_limit, wrapper_limit),) = seen
    assert backend_limit == wrapper_limit == start + 1.0 < deadline  # narrowed for the reset
    if blocking == "reconnect_loop":
        assert clock.now <= start + 1.0 + 2 * clock.tick  # bounded inside the blocking reset
        assert accepts and all(now + timeout <= start + 1.0 + 1e-9 for now, timeout in accepts)
    assert env.state == "stopped" and world.action_count() == actions
    assert "combat_resumed" not in [e["event"] for e in gate_events(records)[-4:]]
    assert env.backend.run_deadline == env.env.run_deadline == deadline


def test_reconnect_during_the_wait_is_bounded_by_the_cap(clock, tmp_path):
    world, accepts = World(), []
    world.clock = clock
    world.take_errors = [PeerDisconnected("restart")]

    def slow_accept(w):
        accepts.append((clock.now, w.config.accept_timeout))
        clock.now += 5.0  # the accept blocked for its whole timeout and longer

    world.on_connect = slow_accept
    start = clock.now
    env = gated(world, tmp_path, cap=1.0, deadline=clock.now + 1000)
    with pytest.raises(CombatGateExpired):
        env.reset()
    assert accepts and all(now + timeout <= start + 1.0 + 1e-9 for now, timeout in accepts)
    assert world.action_count() == 0 and env.state == "stopped"


def test_global_deadline_inside_resume_is_reported_as_the_run_budget(clock, tmp_path):
    world = World(operator=Operator(tmp_path))
    world.clock = clock
    env = gated(world, tmp_path, cap=60.0, deadline=clock.now + 0.5)
    inner = env.backend.start_episode

    def slow(scenario, seed):
        clock.now += 5.0
        return inner(scenario, seed)

    env.backend.start_episode = slow
    with pytest.raises(LiveBudgetExpired) as caught:
        env.reset()
    assert not isinstance(caught.value, CombatGateExpired)
    assert world.action_count() == 0 and env.state == "stopped"


# --- feedback 1: readiness freshness after gaps and disconnects ---------------------------


def _stale_ack(tmp_path, request):
    ack = ReadinessAck(request_id=request.request_id, session_id=request.session_id,
                       game_epoch=request.game_epoch, room_visit=request.room_visit,
                       acked_at=time.time())  # fmt: skip
    (tmp_path / "combat_gate" / READY_NAME).write_text(ack.model_dump_json())


@pytest.mark.parametrize("gap", ["silence", "disconnect"])
def test_retained_observation_cannot_authorize_resume_after_a_gap(clock, tmp_path, gap):
    records: list = []
    world = World()
    world.clock = clock
    world.enemies = {1: 10.0}
    operator = Operator(tmp_path, navigate=False)
    takes, saved = [0], []

    def script(w):
        takes[0] += 1
        if takes[0] == 2:  # combat observed; then the stream goes quiet or drops
            saved.append(operator.request())
            if gap == "silence":
                w.stall = 8  # 0.4 s without samples (> 0.2 s staleness window)
                w.on_stall = lambda w2: w2.stall == 0 and _stale_ack(tmp_path, saved[0])
            else:
                w.take_errors = [PeerDisconnected("dropped")]
                w.on_connect = lambda w2: (_stale_ack(tmp_path, saved[0]),
                                           setattr(w2, "stall", 1))  # fmt: skip
        elif takes[0] > 2:
            operator(w)

    world.operator = script
    env = gated(world, tmp_path, records=records, stale=0.2)
    env.reset()
    assert saved[0].eligibility == "combat"
    assert env.stats.rejected == {"no_observation": 1}
    assert env.stats.observation_gaps == 1 and env.stats.accepted == 1
    assert env.state == "combat_active"
    observed = [e["eligibility"] for e in gate_events(records, "observed")]
    assert "unavailable" in observed and observed[-1] == "combat"


def test_gate_config_rejects_staleness_outside_bounds(tmp_path):
    with pytest.raises(ValueError):
        GateConfig(tmp_path, poll_seconds=0.5, stale_seconds=0.25)
    with pytest.raises(ValueError):
        GateConfig(tmp_path, stale_seconds=31)
