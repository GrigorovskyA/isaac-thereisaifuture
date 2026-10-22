"""OFFLINE cooldown trace tests against production Lua; no Isaac firing acceptance."""

import pytest
import test_lua_observer
from test_lua_actions import input_value, send
from test_lua_callback_trace import events, field, lines, traced
from test_lua_observer import ROOT, build_lua, handshake


def sparse_traced():
    lua = build_lua(
        approved=True,
        source_changes={"firing_diagnostics = false,": "firing_diagnostics = true,"},
    )
    lua.execute("callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=4096")
    handshake(lua, actions=True)
    return lua


def tear(lua, source="TEST_PLAYER"):
    lua.execute(f"callbacks.tear(mod, {{SpawnerEntity={source}, Velocity={{X=0,Y=-10}}}})")


def test_default_off_does_not_read_cooldown_even_for_shooting_or_tears():
    lua = traced(trace=False)
    lua.execute(
        "READS=0; setmetatable(TEST_PLAYER,{__index=function(_,k) "
        "if k=='FireDelay' or k=='MaxFireDelay' then READS=READS+1; error('read') end end})"
    )
    send(lua)
    assert input_value(lua, 6) == 1
    tear(lua)
    assert lua.globals().READS == 0
    assert lines(lua) == []
    lua.execute("NOW=NOW+250")
    assert input_value(lua, 6) is None


@pytest.mark.parametrize("value", ['"true"', "1", "{}", '"yes"'])
def test_firing_only_mode_requires_literal_true(tmp_path, monkeypatch, value):
    source = (ROOT / "mod/observer/main.lua").read_text(encoding="utf-8")
    patched = source.replace("firing_diagnostics = false,", f"firing_diagnostics = {value},", 1)
    assert patched != source
    target = tmp_path / "mod/observer"
    target.mkdir(parents=True)
    (target / "main.lua").write_text(patched, encoding="utf-8")
    monkeypatch.setattr(test_lua_observer, "ROOT", tmp_path)
    lua = traced(trace=False)
    send(lua)
    assert input_value(lua, 6) == 1
    assert lines(lua) == []


def test_shoot_input_records_fractional_values_without_mutation_or_wire_fields():
    lua = traced()
    lua.execute("TEST_PLAYER.FireDelay=2.5; TEST_PLAYER.MaxFireDelay=10.25")
    send(lua)
    wire = lua.globals().OUTGOING
    assert input_value(lua, 6) == 1
    record = lines(lua)[-1]
    assert field(record, "event") == "input"
    assert field(record, "returned") == "1.0"
    assert field(record, "fire_delay") == "2.5"
    assert field(record, "max_fire_delay") == "10.25"
    assert field(record, "hook") == "GET_ACTION_VALUE"
    assert field(record, "seq") == "1"
    assert lua.globals().TEST_PLAYER.FireDelay == 2.5
    assert lua.globals().TEST_PLAYER.MaxFireDelay == 10.25
    assert lua.globals().OUTGOING == wire
    assert "fire_delay" not in wire
    input_value(lua, 1)
    assert field(lines(lua)[-1], "fire_delay") is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("nil", "na"),
        ('"3"', "na"),
        ("true", "na"),
        ("{}", "na"),
        ("0/0", "na"),
        ("math.huge", "na"),
        ("-math.huge", "na"),
        ("1000001", "na"),
        ("-1000001", "na"),
        ("0", "0"),
        ("-1", "-1"),
    ],
)
def test_missing_invalid_and_boundary_cooldowns(value, expected):
    lua = traced()
    lua.execute(f"TEST_PLAYER.FireDelay={value}; TEST_PLAYER.MaxFireDelay={value}")
    send(lua)
    assert input_value(lua, 6, 0) is True
    assert field(lines(lua)[-1], "fire_delay") == expected
    assert field(lines(lua)[-1], "max_fire_delay") == expected


@pytest.mark.parametrize("hook", [0, 1, 2])
def test_cooldown_read_failure_disables_trace_without_changing_input_or_cleanup(hook):
    lua = traced()
    lua.execute(
        "setmetatable(TEST_PLAYER,{__index=function(_,k) "
        "if k=='FireDelay' then error('cooldown failure') end end})"
    )
    send(lua)
    before = len(lines(lua))
    assert input_value(lua, 6, hook) == {0: True, 1: False, 2: 1}[hook]
    input_value(lua, 6)
    assert len(lines(lua)) == before
    lua.execute("NOW=NOW+250")
    assert input_value(lua, 6) is None
    lua.execute("PEER_CLOSED=true; callbacks.render()")
    assert lua.globals().CLOSED


def test_recursive_cooldown_getter_disables_trace_only():
    lua = traced()
    lua.execute(
        "setmetatable(TEST_PLAYER,{__index=function(_,k) "
        "if k=='FireDelay' then callbacks.input(mod,TEST_PLAYER,2,6); return 2 end end})"
    )
    send(lua)
    before = len(lines(lua))
    assert input_value(lua, 6) == 1
    assert len(lines(lua)) == before
    lua.execute("callbacks.room()")
    assert input_value(lua, 6) is None


def test_native_tear_records_owner_and_active_sequence_without_spawning():
    lua = traced()
    lua.execute("TEST_PLAYER.FireDelay=7; TEST_PLAYER.MaxFireDelay=10")
    send(lua, sequence=1)
    tear(lua, "{ToPlayer=function() return nil end}")
    assert "fire_tear" not in events(lua)
    tear(lua)
    record = lines(lua)[-1]
    assert field(record, "event") == "fire_tear"
    assert field(record, "seq") == "1"
    assert field(record, "fire_delay") == "7"
    assert field(record, "max_fire_delay") == "10"
    assert field(record, "session") and field(record, "epoch") == "1"
    lua.execute("NOW=NOW+250")
    assert input_value(lua, 6) is None
    before = events(lua).count("fire_tear")
    tear(lua)
    assert events(lua).count("fire_tear") == before


def test_shooting_records_share_original_trace_limits_and_stop_at_close():
    lua = traced()
    lua.execute("TEST_PLAYER.FireDelay=999999.5; TEST_PLAYER.MaxFireDelay=-999999.5")
    send(lua)
    for _ in range(600):
        input_value(lua, 6)
    assert len(lines(lua)) == 512
    assert all(len(line) <= 300 for line in lines(lua))
    assert events(lua)[-1] == "stop"
    lua.execute("PEER_CLOSED=true; callbacks.render()")
    assert input_value(lua, 6) is None
    assert lua.globals().CLOSED


def test_sparse_firing_mode_logs_only_commanded_value_hook_once_per_frame():
    lua = sparse_traced()
    send(lua)
    assert field(lines(lua)[0], "event") == "action_accepted"
    before = len(lines(lua))
    assert input_value(lua, 6, 0) is True  # pressed hook is omitted
    assert input_value(lua, 6, 1) is False  # triggered hook is omitted
    assert input_value(lua, 7, 2) == 0  # uncommanded direction is omitted
    assert input_value(lua, 6, 2) == 1
    assert input_value(lua, 6, 2) == 1
    assert len(lines(lua)) == before + 1
    record = lines(lua)[-1]
    assert field(record, "event") == "input"
    assert field(record, "hook") == "GET_ACTION_VALUE"
    assert field(record, "button") == "6" and field(record, "returned") == "1.0"
    assert field(record, "fire_delay") is not None
    lua.execute("FRAME=FRAME+1")
    assert input_value(lua, 6, 2) == 1
    assert len(lines(lua)) == before + 2
    send(lua, sequence=2, kind="release", move="none", shoot="none", frames=0)
    assert "release" in events(lua)
    assert "release_input" not in events(lua)


def test_sparse_mode_does_not_spend_budget_on_render_or_update_callbacks():
    lua = sparse_traced()
    send(lua)
    for index in range(600):
        lua.execute("FRAME=FRAME+1; NOW=NOW+20; callbacks.render(); callbacks.update()")
        if index % 20 == 19:
            send(
                lua,
                sequence=2 + index // 20,
                kind="heartbeat",
                move="none",
                shoot="none",
                frames=0,
            )
    assert "render_enter" not in events(lua)
    assert "render_exit" not in events(lua)
    assert "update_enter" not in events(lua)
    assert "update_exit" not in events(lua)
    assert len(lines(lua)) < 20
    lua.execute("PEER_CLOSED=true; callbacks.render()")
    assert events(lua)[-1] == "stop"
    assert field(lines(lua)[-1], "reason") == "deadline"


def test_sparse_cooldown_read_failure_disables_only_diagnostics_and_keeps_release():
    lua = sparse_traced()
    lua.execute(
        "setmetatable(TEST_PLAYER,{__index=function(_,k) "
        "if k=='FireDelay' then error('cooldown failure') end end})"
    )
    send(lua)
    before = len(lines(lua))
    assert input_value(lua, 6, 2) == 1
    assert input_value(lua, 6, 2) == 1
    assert len(lines(lua)) == before
    lua.execute("NOW=NOW+250")
    assert input_value(lua, 6, 2) is None
    lua.execute("PEER_CLOSED=true; callbacks.render()")
    assert lua.globals().CLOSED


def test_exhaustive_callback_trace_wins_when_both_modes_are_enabled():
    lua = build_lua(
        approved=True,
        callback_trace=True,
        source_changes={"firing_diagnostics = false,": "firing_diagnostics = true,"},
    )
    lua.execute("callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=4096")
    handshake(lua, actions=True)
    send(lua)
    before = len(lines(lua))
    input_value(lua, 6, 0)
    input_value(lua, 6, 1)
    input_value(lua, 6, 2)
    assert len(lines(lua)) == before + 3
    assert [field(line, "hook") for line in lines(lua)[-3:]] == [
        "IS_ACTION_PRESSED",
        "IS_ACTION_TRIGGERED",
        "GET_ACTION_VALUE",
    ]
