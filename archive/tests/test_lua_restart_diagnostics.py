"""OFFLINE production-Lua lifecycle diagnostics: ordering, authority facts, bounds, faults.

Every callback order below is a SIMULATED candidate sequence driven by the test
harness. None of them is evidence of the actual engine ordering in Isaac.
"""

import json
import re
import time

import pytest
from test_lua_live_loop import build_live, hello, records, send
from test_lua_observer import build_lua, tick

from isaac_threrisaifuture.observation import HelloAck, decode
from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES

PREFIX = "[Isaac Future Lifecycle] "
TOKEN = re.compile(r"^[a-z_]+=-?[A-Za-z0-9_]+$")


def life(lua):
    out = []
    for line in lua.globals().LOGS.values():
        if line.startswith(PREFIX):
            out.append(dict(token.split("=", 1) for token in line[len(PREFIX) :].split(" ")))
    return out


def life_lines(lua):
    return [x for x in lua.globals().LOGS.values() if x.startswith(PREFIX)]


def other_logs(lua):
    return [x for x in lua.globals().LOGS.values() if not x.startswith(PREFIX)]


def events(lua):
    return [r["event"] for r in life(lua)]


def first(lua, event):
    """First record of event after the first dispatch, or from the start without one."""
    names = events(lua)
    start = names.index("dispatch_before") if "dispatch_before" in names else 0
    return next(r for r in life(lua)[start:] if r["event"] == event)


def commands(lua):
    return list(lua.globals().COMMANDS.values())


def set_dispatch(lua, sequence):
    lua.globals().DISPATCH_EVENTS = lua.table_from(sequence)


def die(lua, ticks=100):
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, ticks, delta=20)


def observe(lua, session):
    """Reconnect read-only and return the advertised capabilities."""
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    hello(lua, [], session=session)
    return decode(records(lua, "hello_ack")[0].encode(), HelloAck).capabilities


# One frozen wall second for approval creation and Lua os.time in parity runs.
WALL = int(time.time())


def freeze_wall(lua):
    lua.execute(f"os.time = function() return {WALL} end")


def typed(value):
    """Type-tagged JSON value: object key order ignored; arrays, types and values kept."""
    if isinstance(value, dict):
        return ("object", tuple(sorted((key, typed(item)) for key, item in value.items())))
    if isinstance(value, list):
        return ("array", tuple(typed(item) for item in value))
    return (type(value).__name__, value)


def wire(text):
    """Decoded wire messages in order, plus any undelimited tail kept verbatim."""
    *lines, tail = text.split("\n")
    return [typed(json.loads(line)) for line in lines], tail


def portable(transcript):
    return {
        key: wire(value) if key in ("first_outgoing", "outgoing") else value
        for key, value in transcript.items()
    }


# Simulated candidate orders executed inside the single bridge dispatch.
SEQUENCES = {
    "single_exit_start": ["exit", "start"],
    "second_exit_start_without_dispatch": ["exit", "start", "exit", "start"],
    "duplicate_exit_before_confirmation": ["exit", "exit", "start"],
    "start_before_exit": ["start", "exit"],
    "disconnect_before_exit": ["disconnect", "exit", "start"],
    "disconnect_after_start": ["exit", "start", "disconnect"],
}


def run(name, *, diagnostics, prepare=""):
    lua = build_live(lifecycle_diagnostics=diagnostics, expires_at=WALL + 3600)
    freeze_wall(lua)
    lua.globals().BEFORE_FAULT = len(life_lines(lua))
    lua.execute(prepare)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    tick(lua, 3)
    transcript = {"acks": [send(lua, sequence=1).status]}
    transcript["held"] = lua.eval("callbacks.input(mod,TEST_PLAYER,2,1)")
    set_dispatch(lua, SEQUENCES[name])
    die(lua)
    transcript["first_outgoing"] = lua.globals().OUTGOING
    transcript["capabilities"] = observe(lua, "b" * 32)
    tick(lua, 10)
    transcript.update(
        outgoing=lua.globals().OUTGOING,
        commands=commands(lua),
        closed=lua.globals().CLOSED,
        logs=other_logs(lua),
    )
    return lua, transcript


def test_default_disabled_emits_no_lifecycle_records():
    lua, _ = run("second_exit_start_without_dispatch", diagnostics=False)
    assert life_lines(lua) == []


def test_single_restart_preserves_authority_and_correlates_dispatch():
    lua, out = run("single_exit_start", diagnostics=True)
    order = events(lua)
    expected = [
        "game_end_enter",
        "game_end_exit",
        "dispatch_before",
        "exit_enter",
        "approval_preserve",
        "close",
        "exit_exit",
        "start_enter",
        "start_exit",
        "dispatch_after",
    ]
    start = order.index("game_end_enter", order.index("restart_arm"))
    assert order[start : start + len(expected)] == expected
    exit_enter, start_enter = first(lua, "exit_enter"), first(lua, "start_enter")
    assert exit_enter["corr"] == "awaiting" and exit_enter["live"] == "1"
    assert start_enter["corr"] == "awaiting" and start_enter["continued"] == "0"
    assert first(lua, "dispatch_before")["restart_id"] == "1"
    assert first(lua, "dispatch_after")["ok"] == "1"
    assert first(lua, "start_exit")["epoch"] == "2"
    assert first(lua, "start_exit")["rs_disabled"] == "0"
    assert first(lua, "close")["reason"] == "game_exit"
    hellos = [r for r in life(lua) if r["event"] == "hello"]
    assert hellos[-1]["auth"] == "ok" and hellos[-1]["live_adv"] == "1"
    assert hellos[-1]["epoch"] == "2" and hellos[-1]["approval"] == "1"
    assert "live_loop_v1" in out["capabilities"] and out["commands"] == ["restart"]
    assert "approval_drop" not in order


@pytest.mark.parametrize(
    "name",
    [
        "second_exit_start_without_dispatch",
        "duplicate_exit_before_confirmation",
        "start_before_exit",
        "disconnect_before_exit",
    ],
)
def test_candidate_orders_show_actual_drop_branch_and_keep_refusal(name):
    lua, out = run(name, diagnostics=True)
    drop = first(lua, "approval_drop")
    assert drop["approval"] == "1"  # pre-mutation facts at the actual branch
    # Existing semantics: the refusal is preserved; only one dispatch is ever issued.
    assert out["commands"] == ["restart"]
    assert "safe_actions_v1" not in out["capabilities"]
    hello_record = [r for r in life(lua) if r["event"] == "hello"][-1]
    assert hello_record["auth"] == "none" and hello_record["approval"] == "0"
    if name == "second_exit_start_without_dispatch":
        rows = life(lua)
        entry = [r for r in rows[: rows.index(drop)] if r["event"] == "exit_enter"][-1]
        assert entry["corr"] == "uncorrelated"
        assert drop["live"] == "0" and drop["awaiting"] == "na"
        assert any(r["event"] == "start_enter" and r["corr"] == "uncorrelated" for r in life(lua))
        assert "restart_invalidate" in events(lua)
    elif name == "duplicate_exit_before_confirmation":
        assert drop["live"] == "0" and drop["awaiting"] == "1"
        assert first(lua, "start_exit")["rs_disabled"] == "0"  # start still confirms
    elif name == "start_before_exit":
        assert drop["live"] == "1" and drop["awaiting"] == "na"
        assert first(lua, "start_enter")["corr"] == "awaiting"
        assert first(lua, "restart_invalidate")["rs_disabled"] == "0"
        assert first(lua, "exit_exit")["rs_disabled"] == "1"
    else:
        assert first(lua, "close")["reason"] == "peer"
        assert drop["live"] == "0" and drop["awaiting"] == "1"


def test_wire_comparison_ignores_key_order_only():
    base = '{"type":"a","n":1,"list":[1,2],"o":{"x":true,"y":null}}\n{"type":"b","v":1.5}\n'
    permuted = '{"o":{"y":null,"x":true},"list":[1,2],"n":1,"type":"a"}\n{"v":1.5,"type":"b"}\n'
    assert wire(permuted) == wire(base)
    changed = [
        base.replace('"n":1', '"n":2'),  # value
        base.replace('"n":1', '"n":true'),  # type (1 == True in Python)
        base.replace('"n":1', '"n":1.0'),  # number type
        base.replace("[1,2]", "[2,1]"),  # array order
        base.replace(',"n":1', ""),  # missing key
        '{"type":"b","v":1.5}\n{"type":"a","n":1,"list":[1,2],"o":{"x":true,"y":null}}\n',
        base + "{",  # partial tail
    ]
    for text in changed:
        assert wire(text) != wire(base), text


def delayed_run(*, diagnostics):
    """SIMULATED: confirmed restart, live reconnect/rearm, then exit/start without dispatch."""
    lua = build_live(lifecycle_diagnostics=diagnostics, expires_at=WALL + 3600)
    freeze_wall(lua)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    set_dispatch(lua, ["exit", "start"])
    die(lua)
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    hello(lua, LIVE_LOOP_CAPABILITIES, session="b" * 32)
    ack = decode(records(lua, "hello_ack")[0].encode(), HelloAck)
    tick(lua, 3)
    transcript = {"rearmed": "live_loop_v1" in ack.capabilities}
    transcript["acks"] = [send(lua, sequence=1).status]
    transcript["held_before"] = lua.eval("callbacks.input(mod,TEST_PLAYER,2,1)")
    transcript["first_outgoing"] = lua.globals().OUTGOING
    lua.execute("callbacks.exit(); callbacks.start(mod,false)")
    transcript["held_after"] = lua.eval("callbacks.input(mod,TEST_PLAYER,2,1)")
    transcript["capabilities"] = observe(lua, "c" * 32)
    tick(lua, 10)
    transcript.update(
        outgoing=lua.globals().OUTGOING,
        commands=commands(lua),
        closed=lua.globals().CLOSED,
        logs=other_logs(lua),
    )
    return lua, transcript


def test_delayed_second_exit_after_live_rearm_drops_approval():
    lua, out = delayed_run(diagnostics=True)
    assert out["rearmed"] and out["acks"] == ["accepted"] and out["held_before"] == 1.0
    assert out["held_after"] is None and out["commands"] == ["restart"]
    assert "safe_actions_v1" not in out["capabilities"]
    rows = life(lua)
    assert [r["event"] for r in rows].count("approval_preserve") == 1
    drops = [r for r in rows if r["event"] == "approval_drop"]
    assert len(drops) == 1
    drop = drops[0]
    assert drop["live"] == "1" and drop["awaiting"] == "na" and drop["approval"] == "1"
    assert drop["session"] == "b" * 32 and drop["epoch"] == "2"
    entry = [r for r in rows[: rows.index(drop)] if r["event"] == "exit_enter"][-1]
    assert entry["corr"] == "uncorrelated"
    assert rows[rows.index(drop) - 1]["event"] == "restart_invalidate"
    assert [r for r in rows if r["event"] == "start_enter"][-1]["corr"] == "uncorrelated"
    final = [r for r in rows if r["event"] == "hello"][-1]
    assert final["auth"] == "none" and final["approval"] == "0" and final["live_adv"] == "0"


def test_delayed_second_exit_parity():
    _, off = delayed_run(diagnostics=False)
    _, on = delayed_run(diagnostics=True)
    assert portable(on) == portable(off)


def test_disconnect_after_confirmed_start_keeps_authority():
    lua, out = run("disconnect_after_start", diagnostics=True)
    assert "approval_preserve" in events(lua) and "approval_drop" not in events(lua)
    assert "live_loop_v1" in out["capabilities"]


@pytest.mark.parametrize("name", list(SEQUENCES))
def test_enabled_and_disabled_runs_are_observably_identical(name):
    _, off = run(name, diagnostics=False)
    _, on = run(name, diagnostics=True)
    assert portable(on) == portable(off)


def test_confirmation_timeout_is_recorded_and_disables_restart():
    lua = build_live(lifecycle_diagnostics=True)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    set_dispatch(lua, [])
    die(lua, ticks=80)
    tick(lua, 1, delta=5001)
    timeout = first(lua, "restart_timeout")
    assert timeout["rs_disabled"] == "1" and timeout["awaiting"] == "na"
    assert commands(lua) == ["restart"]


def test_exhausted_attempts_are_visible_and_not_renewed():
    lua = build_live(lifecycle_diagnostics=True, max_restarts=1)
    lua.execute("AUTO_START=true")
    hello(lua, LIVE_LOOP_CAPABILITIES)
    die(lua)
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    hello(lua, LIVE_LOOP_CAPABILITIES, session="b" * 32)
    arms = [r for r in life(lua) if r["event"] == "restart_arm"]
    assert arms[-1]["rs_armed"] == "0" and arms[-1]["attempts"] == "1"
    assert arms[-1]["limit"] == "1"
    die(lua)
    assert commands(lua) == ["restart"]


def test_legacy_restart_lease_expiry_stops_with_record():
    lua = build_lua(lifecycle_diagnostics=True)
    lua.execute("callbacks.start(mod,false)")
    tick(lua)
    request = {
        "type": "hello",
        "protocol_version": 1,
        "schema_version": 1,
        "session_id": "a" * 32,
        "required_capabilities": ["snapshot_v1", "availability", "death_restart_v1"],
    }
    lua.globals().INCOMING = json.dumps(request, separators=(",", ":")) + "\n"
    tick(lua, 15)
    tick(lua, 1, delta=600001)
    stop = first(lua, "restart_stop")
    assert stop["rs_armed"] == "0" and stop["limit"] == "3"
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, 100)
    assert commands(lua) == []


def refused_hello(lua, *, session="a" * 32):
    hello(lua, LIVE_LOOP_CAPABILITIES, session=session)
    return [r for r in life(lua) if r["event"] == "hello"][-1]


def test_hello_refusal_missing_approval():
    lua = build_lua(lifecycle_diagnostics=True)
    lua.execute("callbacks.start(mod,false)")
    record = refused_hello(lua)
    assert record["auth"] == "none" and record["loaded"] == "0"
    assert record["live_req"] == "1" and record["live_adv"] == "0"
    assert lua.globals().CLOSED
    assert first(lua, "close")["reason"] == "other"


def test_hello_refusal_inactive_game():
    lua = build_lua(
        lifecycle_diagnostics=True,
        approved=True,
        approval_changes=dict(
            profile_mode="training",
            game_epoch=None,
            max_restarts=3,
            expires_at=int(time.time()) + 3600,
        ),
    )
    record = refused_hello(lua)  # approval present, no game started yet
    assert record["auth"] == "inactive" and record["active"] == "0"
    assert record["approval"] == "1" and record["eligible"] == "0"


def test_hello_refusal_expired_approval():
    lua = build_live(lifecycle_diagnostics=True, expires_at=int(time.time()) - 1)
    record = refused_hello(lua)
    assert record["auth"] == "expired" and int(record["expires_s"]) < 0


def test_hello_refusal_elapsed_action_lease():
    # A 10-minute approval keeps the lease shorter than the 20-minute diagnostic window.
    lua = build_live(lifecycle_diagnostics=True, expires_at=int(time.time()) + 600)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    lua.execute("PEER_CLOSED=true")
    tick(lua)
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=600 * 1000 + 5000)
    record = refused_hello(lua, session="b" * 32)
    assert record["auth"] == "lease" and int(record["lease_ms"]) <= 0
    assert int(record["expires_s"]) > 0  # not wall-clock expiry


def test_hello_refusal_other_validation():
    lua = build_live(lifecycle_diagnostics=True, slot=3)
    record = refused_hello(lua)
    assert record["auth"] == "other_validation" and record["eligible"] == "0"


def test_count_limit_includes_stop_and_survives_reconnect_and_epochs():
    lua = build_live(lifecycle_diagnostics=True)
    for index in range(150):
        lua.execute("callbacks.start(mod,false)")
        if index % 25 == 0:
            lua.execute('PEER_CLOSED=false; OUTGOING=""')
            tick(lua, delta=1001)
            hello(lua, [], session=f"{index:032x}")
    rows = life(lua)
    assert len(rows) == 256
    assert [int(r["id"]) for r in rows] == list(range(1, 257))
    assert rows[-1]["event"] == "stop" and rows[-1]["reason"] == "count"
    lua.execute("callbacks.exit(); callbacks.start(mod,false)")
    assert len(life(lua)) == 256


def test_time_window_is_nonrenewable():
    lua = build_live(lifecycle_diagnostics=True)
    lua.execute("callbacks.start(mod,false)")
    count = len(life(lua))
    lua.execute("NOW=NOW+1200000; callbacks.start(mod,false)")
    rows = life(lua)
    assert len(rows) == count + 1
    assert rows[-1]["event"] == "stop" and rows[-1]["reason"] == "deadline"
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    hello(lua, LIVE_LOOP_CAPABILITIES, session="c" * 32)
    lua.execute("callbacks.exit(); callbacks.start(mod,false)")
    assert len(life(lua)) == count + 1


def test_close_and_reconnect_before_expiry_do_not_extend_window():
    lua = build_live(lifecycle_diagnostics=True)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    lua.execute("NOW=NOW+1000000; PEER_CLOSED=true")
    tick(lua)  # close well inside the window
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    hello(lua, LIVE_LOOP_CAPABILITIES, session="b" * 32)
    lua.execute("NOW=NOW+200000; callbacks.start(mod,false)")
    rows = life(lua)
    assert rows[-1]["event"] == "stop" and rows[-1]["reason"] == "deadline"
    assert int(rows[-1]["time_ms"]) - int(rows[0]["time_ms"]) >= 1200000


def test_records_are_bounded_fixed_tokens_without_private_values():
    lua, _ = run("second_exit_start_without_dispatch", diagnostics=True)
    lines = life_lines(lua)
    assert lines and all(len(line) <= 768 for line in lines)
    for line in lines:
        assert all(TOKEN.match(token) for token in line[len(PREFIX) :].split(" ")), line
        assert "offline-only" not in line and "simulated" not in line and "/" not in line


def test_line_limit_stops_with_identity_only_record():
    lua = build_live(lifecycle_diagnostics=True, source_changes={"LINE_MAX = 768": "LINE_MAX = 80"})
    lua.execute("callbacks.start(mod,false); callbacks.start(mod,false)")
    rows = life(lua)
    assert len(rows) == 1 and rows[0]["event"] == "stop" and rows[0]["reason"] == "line_limit"
    assert all(len(line) <= 80 for line in life_lines(lua))


# One transient sink fault: diagnostics must stay disabled after it.
SINK_FAIL = """
SINK_FAILED = false
Isaac.DebugString = function(text)
 if text:find("Lifecycle", 1, true) and not SINK_FAILED then
  SINK_FAILED = true; error("Simulated sink fault")
 end
 LOGS[#LOGS+1] = text
end
"""
CLOCK_FAIL = "local base = Isaac.GetTime; Isaac.GetTime = function() return base() + 0.5 end"
FRAME_FAIL = """
local base_game = Game
Game = function()
 local game = base_game()
 game.GetFrameCount = function() error("Simulated frame fault") end
 return game
end
"""


@pytest.mark.parametrize("fault", [SINK_FAIL, CLOCK_FAIL])
@pytest.mark.parametrize("name", ["single_exit_start", "second_exit_start_without_dispatch"])
def test_sink_and_clock_faults_disable_only_diagnostics(fault, name):
    _, off = run(name, diagnostics=False, prepare=fault)
    lua, on = run(name, diagnostics=True, prepare=fault)
    assert portable(on) == portable(off)
    assert len(life_lines(lua)) == lua.globals().BEFORE_FAULT  # nothing after the fault


def test_frame_fault_during_exit_disables_only_diagnostics():
    lua = build_live(lifecycle_diagnostics=True)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    lua.execute(f"function fail_frames() {FRAME_FAIL} end")
    lua.execute(
        "local base_exit = callbacks.exit; callbacks.exit = function(...)"
        " fail_frames(); return base_exit(...) end"
    )
    set_dispatch(lua, ["exit", "start"])
    die(lua)
    assert events(lua)[-1] == "dispatch_before"  # exit_enter attempt failed; no more records
    count = len(life(lua))
    assert commands(lua) == ["restart"] and lua.globals().CLOSED
    assert "live_loop_v1" in observe(lua, "b" * 32)  # approval preserved, cleanup ran
    assert len(life(lua)) == count


def test_recursive_diagnostic_call_disables_without_escaping():
    lua = build_live(lifecycle_diagnostics=True)
    lua.execute(
        """
        REENTERED = false
        Isaac.DebugString = function(text)
         LOGS[#LOGS+1] = text
         if text:find("event=dispatch_before", 1, true) and not REENTERED then
          REENTERED = true; callbacks.game_end(mod,false)
         end
        end
        """
    )
    hello(lua, LIVE_LOOP_CAPABILITIES)
    set_dispatch(lua, ["exit", "start"])
    die(lua)
    assert lua.globals().REENTERED and events(lua)[-1] == "dispatch_before"
    assert commands(lua) == ["restart"]
    assert "live_loop_v1" in observe(lua, "b" * 32)
    assert events(lua)[-1] == "dispatch_before"


@pytest.mark.parametrize("approved", [False, True])
def test_diagnostics_never_read_or_reload_approval(approved):
    counts = []
    for diagnostics in (False, True):
        lua = (
            build_live(lifecycle_diagnostics=diagnostics)
            if approved
            else build_lua(lifecycle_diagnostics=diagnostics)
        )
        lua.execute(
            "OPENS = 0; local base = io.open; io.open = function(...)"
            " OPENS = OPENS + 1; return base(...) end"
        )
        lua.execute("callbacks.start(mod,false)")
        for session in ("a", "b"):
            lua.execute('PEER_CLOSED=false; OUTGOING=""')
            tick(lua, delta=1001)
            hello(lua, [], session=session * 32)
            lua.execute("PEER_CLOSED=true")
            tick(lua)
        lua.execute("callbacks.exit(); callbacks.start(mod,false)")
        counts.append(lua.globals().OPENS)
    assert counts[0] == counts[1]
