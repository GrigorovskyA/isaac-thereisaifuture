"""OFFLINE production Lua: the restart command, shared budget and pacing, 5 s confirmation."""

import json

import pytest
from test_lua_actions import send as plain_send
from test_lua_live_loop import acks, build_live, hello, live_snapshots, send
from test_lua_observer import build_lua, handshake, tick

from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES

DEFAULT_ROOM = "ROOM_ENTITIES={ make_enemy(1,140,200,10,20) }"


def started(*, max_restarts=3, auto_start=True, interval=None):
    changes = {"live_restart_interval_ms = 4000": f"live_restart_interval_ms = {interval}"}
    lua = build_live(max_restarts=max_restarts, source_changes=changes if interval else None)
    lua.execute(f"AUTO_START={'true' if auto_start else 'false'}; {DEFAULT_ROOM}")
    hello(lua, LIVE_LOOP_CAPABILITIES)
    tick(lua, 5)
    return lua


def dispatches(lua):
    return list(lua.globals().COMMANDS.values())


def logged(lua, text):
    return any(text in line for line in lua.globals().LOGS.values())


def restart_by_command(lua, sequence=1):
    """Send one restart command and let the game thread dispatch it."""
    ack = send(lua, sequence=sequence, kind="restart")
    tick(lua, 30)
    return ack


def reconnected(lua, session):
    """Answer the next fresh observer connection as soon as the mod opens it."""
    lua.execute('PEER_CLOSED=false; OUTGOING=""; INCOMING=""')
    calls = lua.eval("CONNECT_CALLS")
    for _ in range(400):
        if lua.eval("CONNECT_CALLS") > calls:
            break
        tick(lua, delta=17)
    hello(lua, LIVE_LOOP_CAPABILITIES, session=session)
    tick(lua, 5)


def die(lua):
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, 100, delta=20)


def test_authorized_paced_restart_is_acked_then_dispatched_once():
    lua = started()
    assert send(lua, sequence=1, kind="restart").status == "accepted"
    tick(lua, 30)
    assert dispatches(lua) == ["restart"]
    assert logged(lua, "Death restart dispatch") and logged(lua, "source=command")
    assert lua.globals().CLOSED  # the engine exit closes the session, as for a death restart
    reconnected(lua, "b" * 32)
    assert live_snapshots(lua)[-1].game_epoch == 2


def test_restart_is_rejected_while_the_player_is_dead_or_paused():
    for state in ("IS_DEAD=true", "PAUSED=true"):
        lua = started()
        lua.execute(state)
        assert send(lua, sequence=1, kind="restart").status == "rejected"
        tick(lua, 30)
        assert dispatches(lua) == [] and not lua.globals().CLOSED


def test_restart_without_live_authority_is_refused_and_never_dispatched():
    lua = build_lua(approved=True)  # isolated approval: safe actions only, no live loop
    lua.execute("callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=4096")
    handshake(lua, actions=True)
    plain_send(lua, kind="restart", move="none", shoot="none", frames=0)
    tick(lua, 30)
    assert lua.globals().CLOSED and dispatches(lua) == []


def raw_command(lua, **fields):
    """Canonical command text that bypasses the Python model, to probe the Lua validator."""
    snap = live_snapshots(lua)[-1]
    values = dict(
        type="command", protocol_version=1, session_id=snap.session_id, sequence=1,
        game_epoch=snap.game_epoch, room_visit=snap.room.visit_id, frame_id=snap.frame_id,
        kind="restart", move="none", shoot="none", use="none", frames=0,
    )  # fmt: skip
    values.update(fields)
    return json.dumps(values, separators=(",", ":")) + "\n"


def test_restart_after_the_approval_expired_is_refused():
    lua = started()
    lua.execute("os.time = function() return 4102444800 end")
    lua.globals().INCOMING = raw_command(lua)
    tick(lua, 30)
    assert dispatches(lua) == [] and lua.globals().CLOSED


@pytest.mark.parametrize(
    "changes", [dict(move="left"), dict(shoot="up"), dict(use="bomb"), dict(frames=3)]
)
def test_restart_with_an_action_payload_is_refused_as_incompatible(changes):
    lua = started()
    lua.globals().INCOMING = raw_command(lua, **changes)
    tick(lua, 30)
    assert dispatches(lua) == [] and lua.globals().CLOSED


def test_unlimited_budget_survives_many_death_and_command_restarts():
    lua = started(max_restarts=0, interval=100)  # pacing itself is tested separately
    assert logged(lua, "limit unlimited attempts")
    sessions = iter("bcdef0123456789")
    for cycle in range(10):
        if cycle % 2:
            die(lua)
        else:
            assert restart_by_command(lua).status == "accepted"
        reconnected(lua, next(sessions) * 32)
    assert dispatches(lua) == ["restart"] * 10


def test_finite_budget_is_shared_by_death_and_command_restarts():
    lua = started(max_restarts=2)
    die(lua)
    reconnected(lua, "b" * 32)
    tick(lua, 200)
    assert restart_by_command(lua).status == "accepted"
    reconnected(lua, "c" * 32)
    tick(lua, 200)
    assert send(lua, sequence=1, kind="restart").status == "rejected"
    tick(lua, 30)
    assert dispatches(lua) == ["restart", "restart"] and not lua.globals().CLOSED


def test_command_restart_shares_pacing_with_the_death_restart():
    lua = started(max_restarts=5)
    die(lua)
    reconnected(lua, "b" * 32)  # about 2.5 s after the dispatch, inside the 4 s interval
    assert send(lua, sequence=1, kind="restart").status == "rejected"
    tick(lua, 150)  # now past the interval
    assert send(lua, sequence=2, kind="restart").status == "accepted"
    tick(lua, 30)
    assert dispatches(lua) == ["restart", "restart"]


def test_duplicate_restart_while_one_is_pending_is_rejected():
    lua = started(max_restarts=5, auto_start=False)
    assert send(lua, sequence=1, kind="restart").status == "accepted"
    assert send(lua, sequence=2, kind="restart").status == "rejected"
    tick(lua, 30)
    assert dispatches(lua) == ["restart"]


def dispatch_time(lua):
    """Tick in small steps until the single dispatch has happened; return its fake time."""
    for _ in range(400):
        if dispatches(lua):
            return lua.eval("NOW")
        tick(lua, delta=10)
    raise AssertionError("No dispatch")


def at(lua, now):
    lua.execute(f"NOW={now}; callbacks.render()")


@pytest.mark.parametrize("source", ["death", "command"])
def test_confirmation_times_out_exactly_five_seconds_after_dispatch(source):
    lua = started(max_restarts=5, auto_start=False)  # the game never starts again
    if source == "death":
        lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    else:
        assert send(lua, sequence=1, kind="restart").status == "accepted"
    start = dispatch_time(lua)
    timeout = "Death restart fault: fresh game-start confirmation timed out; disabled"
    at(lua, start + 4999)
    assert not logged(lua, timeout)
    at(lua, start + 5000)
    assert logged(lua, timeout)
    # No retry, and a new command is refused without closing the session.
    lua.execute("IS_DEAD=false")
    tick(lua, 400)
    assert send(lua, sequence=2, kind="restart").status == "rejected"
    assert dispatches(lua) == ["restart"] and not lua.globals().CLOSED
    assert acks(lua)[-1].kind == "restart"
