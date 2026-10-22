"""OFFLINE Lua stub tests for the bounded callback trace. Nothing here runs Isaac."""

import re

import pytest
import test_lua_observer
from test_lua_actions import input_value, send
from test_lua_observer import ROOT, build_lua, handshake, snapshots, tick

PREFIX = "[Isaac Future Trace]"


def traced(*, approved=True, trace=True):
    lua = build_lua(approved=approved, callback_trace=trace)
    lua.execute("callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=4096")
    handshake(lua, actions=approved)
    return lua


def lines(lua):
    return [x for x in lua.globals().LOGS.values() if x.startswith(PREFIX)]


def field(line, name):
    match = re.search(rf"\b{name}=(\S+)", line)
    return match.group(1) if match else None


def events(lua):
    return [field(x, "event") for x in lines(lua)]


def test_default_build_produces_no_trace_lines():
    lua = traced(trace=False)
    send(lua)
    input_value(lua)
    tick(lua, 5)
    lua.execute("callbacks.update(); callbacks.room(); callbacks.level()")
    assert lines(lua) == []


def test_opt_in_without_action_authority_never_starts():
    lua = traced(approved=False)
    tick(lua, 50)
    lua.execute("callbacks.update(); callbacks.room(); callbacks.exit()")
    assert lines(lua) == []


def test_heartbeat_and_invalid_commands_do_not_start_the_trace():
    lua = traced()
    send(lua, kind="heartbeat", move="none", shoot="none", frames=0)
    input_value(lua)
    assert lines(lua) == []
    send(lua, sequence=2, frame_id=19)  # stale action is rejected and closes the peer
    assert lua.globals().CLOSED
    assert lines(lua) == []


@pytest.mark.parametrize("value", ['"true"', "1", "{}", '"yes"'])
def test_only_the_literal_true_opts_in(tmp_path, monkeypatch, value):
    source = (ROOT / "mod/observer/main.lua").read_text(encoding="utf-8")
    patched = source.replace("callback_trace = false,", f"callback_trace = {value},", 1)
    assert patched != source
    target = tmp_path / "mod/observer"
    target.mkdir(parents=True)
    (target / "main.lua").write_text(patched, encoding="utf-8")
    monkeypatch.setattr(test_lua_observer, "ROOT", tmp_path)
    lua = traced(trace=False)
    send(lua)
    input_value(lua)
    assert lines(lua) == []


def test_authorized_acceptance_starts_correlated_records():
    lua = traced()
    session = snapshots(lua)[-1].session_id
    send(lua)
    first = lines(lua)[0]
    assert (field(first, "id"), field(first, "event")) == ("1", "action_accepted")
    assert field(first, "move") == "right" and field(first, "shoot") == "up"
    assert field(first, "frame") == "20" and field(first, "epoch") == "1"
    assert field(first, "session") == session and field(first, "seq") == "1"
    assert events(lua)[1] == "render_exit"
    assert input_value(lua, 1, 2) == 1
    assert input_value(lua, 8) is None  # unrecognized buttons produce no record
    record = lines(lua)[-1]
    assert field(record, "event") == "input" and field(record, "hook") == "GET_ACTION_VALUE"
    assert field(record, "button") == "1" and field(record, "returned") == "1.0"
    assert field(record, "seq") == "1" and field(record, "frame") == "20"
    assert input_value(lua, 1, 0) is True
    assert field(lines(lua)[-1], "hook") == "IS_ACTION_PRESSED"
    assert field(lines(lua)[-1], "returned") == "true"
    lua.execute("callbacks.update()")
    assert events(lua)[-3:] == ["update_enter", "hold_update", "update_exit"]
    assert field(lines(lua)[-3], "update") == "1"


def test_record_budget_includes_the_final_stop_record():
    lua = traced()
    send(lua)
    for _ in range(600):
        input_value(lua)
    seen = lines(lua)
    assert len(seen) == 512
    assert [int(field(x, "id")) for x in seen] == list(range(1, 513))
    assert all(len(x) <= 300 for x in seen)
    assert events(lua).count("stop") == 1 and field(seen[-1], "reason") == "count"
    lua.execute("callbacks.update(); callbacks.room()")
    assert len(lines(lua)) == 512


def test_time_window_stops_exactly_once_at_the_deadline():
    lua = traced()
    send(lua)
    start = int(lua.globals().NOW)
    lua.execute(f"NOW={start + 9999}; callbacks.room()")
    assert events(lua)[-2:] == ["release", "new_room"]
    lua.execute(f"NOW={start + 10000}; callbacks.room()")
    assert events(lua)[-1] == "stop" and field(lines(lua)[-1], "reason") == "deadline"
    total = len(lines(lua))
    lua.execute("callbacks.room(); callbacks.update(); callbacks.level()")
    assert len(lines(lua)) == total and events(lua).count("stop") == 1


def test_reconnect_cannot_renew_the_window():
    lua = traced()
    send(lua)
    lua.execute("PEER_CLOSED=true; callbacks.render()")
    assert lua.globals().CLOSED and field(lines(lua)[-1], "event") == "close"
    total = len(lines(lua))
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    handshake(lua, "d" * 32, actions=True)
    send(lua)
    assert input_value(lua) == 1  # the action itself still works after reconnect
    lua.execute("callbacks.update(); callbacks.room()")
    assert len(lines(lua)) == total
    assert input_value(lua) is None  # room transition still releases held input


def test_release_and_disconnect_records_end_the_trace():
    lua = traced()
    send(lua)
    lua.execute("callbacks.room()")
    assert events(lua)[-2:] == ["release", "new_room"]
    assert "reason=transition" in lines(lua)[-2]
    lua.execute("PEER_CLOSED=true; callbacks.render()")
    assert field(lines(lua)[-1], "event") == "close"
    assert "Peer" in lines(lua)[-1]
    total = len(lines(lua))
    lua.execute("callbacks.update(); callbacks.level()")
    assert len(lines(lua)) == total


def test_game_exit_is_recorded_then_ends_the_trace():
    lua = traced()
    send(lua)
    lua.execute("callbacks.exit()")
    assert lua.globals().CLOSED
    assert events(lua)[-3:] == ["pre_game_exit", "release", "close"]
    total = len(lines(lua))
    lua.execute("callbacks.render(); callbacks.update()")
    assert len(lines(lua)) == total


def test_logger_failure_disables_trace_without_changing_inputs_or_cleanup():
    lua = traced()
    lua.execute(
        "print=function(m) if m:find('Future Trace',1,true) then error('log fail') end"
        " LOGS[#LOGS+1]=m end"
    )
    send(lua)
    assert lines(lua) == []
    assert input_value(lua, 1, 2) == 1 and input_value(lua, 1, 0) is True
    assert any("Action accepted" in x for x in lua.globals().LOGS.values())
    lua.execute("callbacks.room()")
    assert input_value(lua) is None
    lua.execute("callbacks.exit()")
    assert lua.globals().CLOSED
    assert lines(lua) == []


DEBUG_LOGGER = "Isaac.DebugString=function(m) LOGS[#LOGS+1]=m end"
FAILING_DEBUG_LOGGER = (
    "ATTEMPTS=0; Isaac.DebugString=function(m)"
    " if m:find('Future Trace',1,true) then ATTEMPTS=ATTEMPTS+1; error('log fail') end"
    " LOGS[#LOGS+1]=m end"
)


def test_debug_string_logger_receives_trace_lines_instead_of_print():
    lua = traced()
    lua.execute(DEBUG_LOGGER)
    send(lua)
    assert input_value(lua, 1, 2) == 1
    assert events(lua)[0] == "action_accepted" and events(lua)[-1] == "input"
    assert all(len(x) <= 300 for x in lines(lua))


def test_debug_string_failure_disables_trace_without_changing_behavior():
    lua = traced()
    lua.execute(FAILING_DEBUG_LOGGER)
    send(lua)
    assert lines(lua) == [] and lua.globals().ATTEMPTS == 1
    assert input_value(lua, 1, 2) == 1 and input_value(lua, 1, 0) is True
    lua.execute("callbacks.update(); callbacks.render()")
    assert lua.globals().ATTEMPTS == 1  # no further attempts after the failure
    assert any("Action accepted" in x for x in lua.globals().LOGS.values())
    lua.execute("callbacks.room()")
    assert input_value(lua) is None
    lua.execute("callbacks.exit()")
    assert lua.globals().CLOSED
    assert lua.globals().ATTEMPTS == 1


def test_trace_records_never_enter_wire_data():
    lua = traced()
    send(lua)
    input_value(lua)
    tick(lua, 20, delta=1)
    assert lines(lua)
    assert "trace" not in lua.globals().OUTGOING.lower()
    assert snapshots(lua)  # strict snapshot models still decode every record
