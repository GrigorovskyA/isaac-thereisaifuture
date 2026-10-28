"""OFFLINE regression: asynchronous restart order, fault matrix and the plain training pipeline.

The deferred order (dispatch returns first; exit +15 ms; start +111 ms, continued=false;
hello ~1 s later) is SHAPED after the 2026-10-19 runtime trace
(reports/2026-10-19-restart-authority-runtime.md) but is still a SIMULATED schedule in
lupa. It is not engine evidence and does not explain the 2026-10-18 two-start failure.
"""

import contextlib
import time

import gymnasium as gym
import numpy as np
import pytest
from test_checkpoint_policy import RAW_CONFIG
from test_live_e2e import SOCKET_SHIM, Game, Shim
from test_lua_live_loop import build_live, hello, live_snapshots, records, send
from test_lua_observer import tick

from isaac_threrisaifuture.actions import Command
from isaac_threrisaifuture.checkpoints import config_hash, latest_checkpoint_dir, load_checkpoint
from isaac_threrisaifuture.encoding import VisitedCells, encode
from isaac_threrisaifuture.live import LiveClient, make_live_env
from isaac_threrisaifuture.observation import HelloAck, decode
from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES, ObserverConfig
from isaac_threrisaifuture.training import TrainingConfig, train

WALL = int(time.time())

OLD, NEW, THIRD = "a" * 32, "b" * 32, "c" * 32
# Offsets from the real trace: dispatch 60797235, exit 60797250, start 60797346.
REAL_ORDER = [{"after": 15, "event": "exit"}, {"after": 111, "event": "start"}]


def logs(lua):
    return list(lua.globals().LOGS.values())


def logged(lua, text):
    return any(text in line for line in logs(lua))


def freeze_wall(lua):
    lua.execute(f"os.time = function() return {WALL} end")


# --- deferred-order driver -------------------------------------------------------------


def now(lua):
    return lua.eval("NOW")


def advance(lua, ms, *, step=17, render=True):
    """Advance the fake clock by `ms`; due deferred callbacks run at their exact time."""
    end = now(lua) + ms
    while now(lua) < end:
        due = lua.eval("SCHEDULE[1] and SCHEDULE[1].at")
        target = min(now(lua) + step, end, due if due is not None else end)
        lua.execute(f"NOW={target}; run_due()")
        if render:
            lua.execute("callbacks.render()")


def defer(lua, order):
    lua.globals().DEFERRED_EVENTS = lua.table_from([lua.table_from(e) for e in order])


def commands(lua):
    return list(lua.globals().COMMANDS.values())


def held(lua):
    return lua.eval("callbacks.input(mod,TEST_PLAYER,2,1)")


def die_until_dispatch(lua, limit=400):
    """Natural death, then 17 ms renders until the single dispatch has returned."""
    before = len(commands(lua))
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    for _ in range(limit):
        if len(commands(lua)) > before:
            return now(lua)
        advance(lua, 17)
    raise AssertionError("No dispatch")


def reconnect(lua, session, capabilities=LIVE_LOOP_CAPABILITIES):
    """Answer the next fresh observer connection at once (as LiveClient does).

    Returns the advertised capabilities, or None when the live hello was refused/closed.
    """
    lua.execute('PEER_CLOSED=false; OUTGOING=""; INCOMING=""')
    calls = lua.eval("CONNECT_CALLS")
    for _ in range(400):
        if lua.eval("CONNECT_CALLS") > calls:
            break
        advance(lua, 17)
    hello(lua, capabilities, session=session)
    acks = records(lua, "hello_ack")
    return decode(acks[0].encode(), HelloAck).capabilities if acks else None


def started(*, max_restarts=1, expires=3600):
    lua = build_live(max_restarts=max_restarts, expires_at=WALL + expires)
    freeze_wall(lua)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    tick(lua, 3)
    defer(lua, REAL_ORDER)
    return lua


# --- stage 1: the real asynchronous order ----------------------------------------------


@pytest.mark.parametrize("menu_renders", [True, False])
def test_async_real_order_keeps_one_dispatch_identity_and_authority(menu_renders):
    lua = started()
    assert send(lua, sequence=1).status == "accepted" and held(lua) == 1.0
    t = die_until_dispatch(lua)
    assert t and held(lua) is None  # game_end released the hold

    # Boundary 1: ExecuteCommand returned; exit/start not delivered yet.
    assert not lua.globals().CLOSED and commands(lua) == ["restart"]
    # A racing old-session action is refused (dead player) without a hold or closure.
    assert send(lua, sequence=2).status == "rejected" and held(lua) is None
    assert not lua.globals().CLOSED

    # Boundary 2: exit delivered at +15; the peer is closed, approval retained.
    advance(lua, 15, render=menu_renders)
    # The racing command's render already stopped the spent restart (attempts 1/1).
    assert logged(lua, "Death restart stopped: lease or attempt budget exhausted")
    assert lua.globals().CLOSED and held(lua) is None

    # Boundary 3: start at +111 (continued=false) confirms and consumes the await.
    advance(lua, 96, render=menu_renders)
    assert logged(lua, "Death restart confirmed old_epoch=1 new_epoch=2")
    assert not logged(lua, "Death restart fault") and held(lua) is None

    # Boundary 4: live reconnect; approval still loaded, attempts/lease not renewed.
    capabilities = reconnect(lua, NEW)
    assert "live_loop_v1" in capabilities and commands(lua) == ["restart"]
    tick(lua, 3)
    assert live_snapshots(lua)[-1].game_epoch == 2
    assert send(lua, sequence=1).status == "accepted"  # new session, new epoch only


# --- stage 2: Lua fault matrix at the four async boundaries ---------------------------
#
# Outcome classes: accepted (live authority continues), refused (approval dropped or a
# command rejected/closed), infrastructure fault (restart disabled, bounded), budget stop
# (lease, wall expiry or spent attempts). None of them is a game outcome.

BOUNDARIES = ["after_return", "after_exit", "after_start", "after_reconnect"]


def to_boundary(lua, boundary):
    """Drive the real async order up to `boundary`; returns the dispatch time."""
    t = die_until_dispatch(lua)
    if boundary != "after_return":
        advance(lua, 15)
    if boundary in ("after_start", "after_reconnect"):
        advance(lua, 96)
    if boundary == "after_reconnect":
        reconnect(lua, NEW)
    return t


def finish(lua, boundary, session=THIRD):
    """Deliver whatever remains of the order, then reconnect; returns the capabilities."""
    advance(lua, 200)
    return reconnect(lua, session)


@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_peer_loss_at_each_boundary(boundary):
    lua = started()
    to_boundary(lua, boundary)
    lua.execute("PEER_CLOSED=true; NOW=NOW+1; callbacks.render()")  # before any due callback
    advance(lua, 34)
    capabilities = finish(lua, boundary)
    assert commands(lua) == ["restart"] and held(lua) is None
    if boundary == "after_return":
        # refused: the peer closed before the exit, so the exit is a normal-exit drop.
        assert capabilities is None
    else:
        # accepted: approval was already preserved; the spent attempt is not renewed.
        assert "live_loop_v1" in capabilities
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    advance(lua, 6000)
    assert commands(lua) == ["restart"]


@pytest.mark.parametrize("start_after", [4990, 5010, 5100, None])
def test_delayed_or_missing_confirmation_is_bounded_by_five_seconds(start_after):
    lua = started()
    order = [{"after": 15, "event": "exit"}]
    if start_after is not None:
        order.append({"after": start_after, "event": "start"})
    defer(lua, order)
    die_until_dispatch(lua)
    advance(lua, 7000)
    timed_out = logged(lua, "confirmation timed out")
    if start_after == 4990:  # accepted: confirmed inside the window
        assert logged(lua, "Death restart confirmed") and not timed_out
    elif start_after == 5010:  # fault: the late start arrives before the next render
        assert not timed_out and logged(lua, "unexpected game-start; disabled")
    else:  # fault: the render-time timeout disables the restart first
        assert timed_out
    capabilities = reconnect(lua, NEW)
    if start_after is None:  # refused: no game started, so actions stay unauthorized
        assert capabilities is None
    else:
        assert "live_loop_v1" in capabilities  # approval was preserved at the exit
        lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
        advance(lua, 6000)
    assert commands(lua) == ["restart"]


def test_wall_approval_expiry_during_the_transition_refuses_the_reconnect():
    lua = started()
    to_boundary(lua, "after_exit")
    lua.execute(f"os.time = function() return {WALL + 3601} end")
    capabilities = finish(lua, "after_exit")
    assert capabilities is None and commands(lua) == ["restart"]  # budget stop, never renewed


def test_monotonic_lease_expiry_during_the_transition_refuses_the_reconnect():
    lua = started(expires=3, max_restarts=5)
    defer(lua, [{"after": 15, "event": "exit"}, {"after": 1500, "event": "start"}])
    die_until_dispatch(lua)
    advance(lua, 1600)
    assert logged(lua, "Death restart confirmed")  # the start still confirms
    assert reconnect(lua, NEW) is None  # the 3 s lease ended between exit and start
    assert commands(lua) == ["restart"]


def test_spent_attempts_survive_repeated_reconnects():
    lua = started()
    to_boundary(lua, "after_reconnect")
    for session in (THIRD, "d" * 32):
        lua.execute("PEER_CLOSED=true")
        advance(lua, 34)
        assert "live_loop_v1" in reconnect(lua, session)
        assert commands(lua) == ["restart"]
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    advance(lua, 6000)
    assert commands(lua) == ["restart"]  # budget stop: no counter reset


def test_duplicate_async_exit_drops_approval():
    lua = started(max_restarts=5)
    defer(lua, [{"after": 15, "event": "exit"}, {"after": 40, "event": "exit"},
                {"after": 111, "event": "start"}])  # fmt: skip
    die_until_dispatch(lua)
    advance(lua, 200)
    assert reconnect(lua, NEW) is None and commands(lua) == ["restart"]


def test_second_async_start_without_dispatch_after_rearm_drops_approval():
    lua = started(max_restarts=5)
    to_boundary(lua, "after_reconnect")
    tick(lua, 3)
    assert send(lua, sequence=1).status == "accepted" and held(lua) == 1.0
    # A later exit/start that no dispatch requested (the 2026-10-18 shape, simulated).
    lua.execute("SCHEDULE={{at=NOW+15, event='exit'}, {at=NOW+111, event='start'}}")
    advance(lua, 200)
    assert held(lua) is None
    assert reconnect(lua, THIRD) is None and commands(lua) == ["restart"]


def test_command_pending_in_the_buffer_at_exit_is_never_applied():
    lua = started()
    to_boundary(lua, "after_return")
    snap = live_snapshots(lua)[-1]
    lua.globals().INCOMING = Command(
        session_id=OLD, sequence=5, game_epoch=snap.game_epoch, room_visit=snap.room.visit_id,
        frame_id=snap.frame_id, kind="action", move="left", shoot="none", frames=5,
    ).wire_bytes().decode()  # fmt: skip
    lua.execute("IS_DEAD=false")  # even if the player looked alive again
    lua.execute("NOW=NOW+15; run_due()")  # the exit runs before the next render reads it
    advance(lua, 200)
    assert held(lua) is None and records(lua, "command_ack") == []


@pytest.mark.parametrize(
    "changes, closes",
    [
        (dict(session_id=OLD), True),  # old session after reconnect: closed
        (dict(sequence=1), True),  # replayed sequence: closed
        (dict(game_epoch=1), False),  # old epoch: refused without closing
    ],
)
def test_stale_identity_after_async_reconnect_never_holds_input(changes, closes):
    lua = started(max_restarts=5)
    to_boundary(lua, "after_reconnect")
    tick(lua, 3)
    assert send(lua, sequence=1).status == "accepted"
    lua.execute("NOW=NOW+300")
    tick(lua, 3)
    if "sequence" in changes:
        changes = dict(changes, kind="heartbeat")
    else:
        changes = dict(changes, sequence=2)
    snap = live_snapshots(lua)[-1]
    values = dict(session_id=NEW, sequence=2, game_epoch=snap.game_epoch,
                  room_visit=snap.room.visit_id, frame_id=snap.frame_id, kind="action",
                  move="left", shoot="none", frames=5)  # fmt: skip
    values.update(changes)
    if values["kind"] != "action":
        values.update(move="none", frames=0)
    before = len(records(lua, "command_ack"))
    lua.globals().INCOMING = Command(**values).wire_bytes().decode()
    tick(lua, delta=1)
    assert bool(lua.globals().CLOSED) is closes
    acks = records(lua, "command_ack")[before:]
    if not closes:
        assert len(acks) == 1 and '"rejected"' in acks[0]
    lua.execute("NOW=NOW+300")
    tick(lua)
    assert held(lua) is None


def test_peer_loss_after_the_async_reconnect_releases_an_accepted_hold():
    lua = started(max_restarts=5)
    to_boundary(lua, "after_reconnect")
    tick(lua, 3)
    assert send(lua, sequence=1).status == "accepted"
    assert held(lua) is not None  # the new session really holds input
    lua.execute("PEER_CLOSED=true; NOW=NOW+1; callbacks.render()")
    assert bool(lua.globals().CLOSED) and held(lua) is None  # released at once, no expiry


# --- stage 2: the plain live env and a real tiny RecurrentPPO over the production Lua --

A = np.array([1, 2, 0])


@contextlib.contextmanager
def harness():
    """Listening LiveClient + production Lua game thread with the deferred restart order."""
    client = LiveClient(ObserverConfig(port=0, accept_timeout=10.0))
    with client:
        assert client.address[1] != 9528
        lua = build_live(max_restarts=1)
        shim = Shim(client.address[1])
        lua.globals().PY = shim
        lua.execute(SOCKET_SHIM)
        lua.execute("SEND_LIMIT=1e9; ROOM_ENTITIES={ make_enemy(1,160,200,10,10) }")
        defer(lua, REAL_ORDER)
        game = Game(lua)
        game.every = "run_due()"
        game.start()
        try:
            yield client, game
        finally:
            game.stop.set()
            game.join(timeout=5)
            shim.close()
            assert not game.is_alive(), "game thread still running after the bounded join"
            assert game.error is None


@pytest.fixture
def loop_game():
    with harness() as parts:
        yield parts


def spy(client, game, *, die_after):
    """Record every command kind; schedule the natural death once."""
    sent, original = [], client.command

    def command(kind, reference, **kwargs):
        sent.append(kind)
        if kind == "action" and sent.count("action") == die_after:
            game.tasks.append("IS_DEAD=true; callbacks.game_end(mod,true)")
        return original(kind, reference, **kwargs)

    client.command = command
    return sent


class EncodedOnly(gym.Wrapper):
    """Records every observation the policy receives next to the oracle-free encoding."""

    def __init__(self, env):
        super().__init__(env)
        self.pairs: list[tuple[np.ndarray, np.ndarray]] = []
        self.visited = VisitedCells()  # independent of the env's own visited-cell state

    def _check(self, obs):
        backend = self.env.env.controller.backend
        frame = backend.latest.entity_frame
        self.pairs.append((obs, encode(frame, visited_cells=self.visited.update(frame)).vector))
        return obs

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        return self._check(obs), info

    def step(self, action):
        obs, *rest = self.env.step(action)
        return (self._check(obs), *rest)


def test_live_env_sends_the_action_repeat_of_the_shipped_contract(loop_game):
    from isaac_threrisaifuture.training import PURE_CONFIG, load_training_config

    config, _ = load_training_config(PURE_CONFIG)
    assert config.action_repeat_game_updates == 6
    client, _ = loop_game
    frames: list[int] = []
    original = client.command

    def command(kind, reference, **kwargs):
        if kind == "action":
            frames.append(kwargs["frames"])
        return original(kind, reference, **kwargs)

    client.command = command
    env = make_live_env(
        client,
        action_repeat=config.action_repeat_game_updates,
        max_faults=0,
        run_deadline=time.monotonic() + 60,
    )
    client.connect()
    env.reset()
    for _ in range(3):
        env.step(A)
    env.close()
    assert frames == [6, 6, 6]


def test_loopback_async_restart_through_the_plain_live_env(loop_game):
    client, game = loop_game
    deadline = time.monotonic() + 60
    env = make_live_env(client, max_faults=0, run_deadline=deadline)
    client.connect()
    sent = spy(client, game, die_after=4)
    env.reset()
    first = client._session
    outcome = None
    for _ in range(200):
        _, reward, terminated, truncated, info = env.step(A)
        if terminated or truncated:
            outcome = info.get("outcome")
            break
    assert outcome == "death" and reward < 0 and "fault" not in info
    env.reset()  # async exit/start, then reconnect on the fresh session
    assert client._session != first and env.env.controller.backend.latest.game_epoch == 2
    _, _, terminated, truncated, info = env.step(A)
    assert not (terminated or truncated) and "fault" not in info
    env.close()
    assert sent.count("action") == 5 and env.faults == 0
    assert list(game.lua.globals().COMMANDS.values()) == ["restart"]
    assert env.env.controller.backend.run_deadline == env.run_deadline == deadline


def test_loopback_stall_truncates_and_restarts_through_the_production_lua(loop_game):
    client, game = loop_game
    clock = [1000.0]
    env = make_live_env(
        client,
        max_faults=0,
        run_deadline=time.monotonic() + 120,
        stall_seconds=90,
        clock=lambda: clock[0],
    )
    client.connect()
    sent, original = [], client.command

    def command(kind, reference, **kwargs):
        sent.append(kind)
        ack = original(kind, reference, **kwargs)
        if kind == "restart":
            assert ack.status == "accepted"
        return ack

    client.command = command
    env.reset()
    first = client._session
    idle = np.array([0, 0, 0])  # the policy does nothing; no progress event can occur
    info = {}
    for _ in range(200):
        clock[0] += 2.0  # the fake clock passes 90 s after about 45 steps
        _, _, terminated, truncated, info = env.step(idle)
        if terminated or truncated:
            break
    assert truncated and not terminated
    assert info["truncation_reason"] == "stall" and "fault" not in info
    assert sent.count("restart") == 1 and sent[-1] == "restart"
    env.reset()  # the accepted restart exits and starts a new epoch, then reconnects
    assert client._session != first and env.env.controller.backend.latest.game_epoch == 2
    _, _, terminated, truncated, info = env.step(idle)
    assert not (terminated or truncated) and "fault" not in info
    env.close()
    assert list(game.lua.globals().COMMANDS.values()) == ["restart"]
    assert env.faults == 0


def test_tiny_recurrent_ppo_over_production_lua_socket(loop_game, tmp_path, monkeypatch):
    """Real CPU RecurrentPPO + VecNormalize over production Lua, loopback LiveClient and
    LiveBackend: one rollout spans the natural death and the async exit/start/reconnect;
    then checkpoint, reload and resume."""
    import isaac_threrisaifuture.training as training

    client, game = loop_game
    captured: dict = {}
    original_save = training.save_checkpoint

    def capture(*args, **kwargs):
        captured["model"], captured["venv"] = kwargs["model"], kwargs["vec_normalize"]
        return original_save(*args, **kwargs)

    monkeypatch.setattr(training, "save_checkpoint", capture)
    config = TrainingConfig.model_validate(RAW_CONFIG)
    cfg_hash = config_hash(RAW_CONFIG)
    deadline = time.monotonic() + 120
    envs: list = []

    def factory(_):
        env = make_live_env(
            client,
            action_repeat=config.action_repeat_game_updates,
            max_faults=0,
            run_deadline=deadline,
        )
        envs.append(env)
        return EncodedOnly(env)

    client.connect()
    sent = spy(client, game, die_after=10)
    run = tmp_path / "run"
    result = train(config, cfg_hash, seed=7, env_factory=factory, out_dir=run)
    assert result.stop_reason == "completed" and result.timesteps == 32
    first = load_checkpoint(
        latest_checkpoint_dir(run / "checkpoints"), expected_config_hash=cfg_hash, expected_seed=7
    )
    assert first.timesteps == 32 and first.parent_checkpoint_id is None
    env, venv, model = envs[0], captured["venv"], captured["model"]
    assert (
        env.faults == 0 and env.env.controller.backend.latest.game_epoch == 2
    )  # continued after the death
    assert list(game.lua.globals().COMMANDS.values()) == ["restart"]
    assert sent.count("action") == 32  # one command per policy decision
    starts = np.flatnonzero(model.rollout_buffer.episode_starts[:, 0])
    assert list(starts) == [0, 10]  # recurrent state reset exactly at the post-death resume
    for obs, expected in venv.venv.envs[0].env.pairs:
        np.testing.assert_array_equal(obs, expected)  # oracle-free encoding only
    assert np.isfinite(model.rollout_buffer.rewards[:, 0]).all()

    # venv.close() closed the listener (LiveBackend.close owns it), so the resume runs a
    # fresh process-like harness: new production Lua, new LiveClient.
    with harness() as (client, game):
        client.connect()
        longer = config.budget.model_copy(update={"total_timesteps": 64})
        resumed = train(
            config.model_copy(update={"budget": longer}),
            cfg_hash,
            seed=7,
            env_factory=factory,
            out_dir=run,
            resume=True,
        )
        assert envs[1].env.controller.backend.latest.game_epoch == 1
    assert resumed.timesteps == 64 and resumed.stop_reason == "completed"
    child = load_checkpoint(
        latest_checkpoint_dir(run / "checkpoints"), expected_config_hash=cfg_hash, expected_seed=7
    )
    assert child.parent_checkpoint_id == first.checkpoint_id and child.timesteps == 64
    assert captured["venv"].obs_rms.count == pytest.approx(1 + 32 + 1 + 32, abs=1e-3)
    assert envs[1].faults == 0
