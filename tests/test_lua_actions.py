"""OFFLINE production Lua callbacks with simulated game/socket and local approval."""

import json

import pytest
from test_lua_observer import build_lua, handshake, snapshots, tick

from isaac_threrisaifuture.actions import Command, CommandAck
from isaac_threrisaifuture.observation import CAPABILITIES, decode


@pytest.fixture
def controlled():
    lua = build_lua(approved=True)
    lua.execute("callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=4096")
    handshake(lua, actions=True)
    return lua


def send(lua, *, sequence=1, **changes):
    snap = snapshots(lua)[-1]
    values = dict(
        session_id=snap.session_id,
        sequence=sequence,
        game_epoch=snap.game_epoch,
        room_visit=snap.room.visit_id,
        frame_id=snap.frame_id,
        kind="action",
        move="right",
        shoot="up",
        frames=15,
    )
    values.update(changes)
    raw = Command(**values).wire_bytes().decode()
    lua.globals().INCOMING = raw
    tick(lua, delta=1)
    return raw


def input_value(lua, button=1, hook=2):
    return lua.eval(f"callbacks.input(mod,TEST_PLAYER,{hook},{button})")


def test_independent_native_inputs_and_explicit_neutral_release(controlled):
    lua = controlled
    send(lua)
    assert [input_value(lua, i) for i in range(8)] == [0, 1, 0, 0, 0, 0, 1, 0]
    assert input_value(lua, 1, 0) is True
    assert input_value(lua, 1, 1) is False
    assert input_value(lua, 8) is None
    assert lua.eval("callbacks.input(mod,nil,2,1)") is None
    assert lua.eval("callbacks.input(mod,{ToPlayer=function() return nil end},2,1)") is None
    assert lua.eval("callbacks.input(mod,{ToPlayer=function(self) return self end},2,1)") is None
    records = lua.globals().OUTGOING.splitlines()
    ack = decode(records[-1].encode(), CommandAck)
    assert ack.sequence == 1 and ack.frame_id == 20
    send(lua, sequence=2, move="none", shoot="none")
    assert all(input_value(lua, i) == 0 for i in range(8))
    send(lua, sequence=3, kind="release", move="none", shoot="none", frames=0)
    assert all(input_value(lua, i) is None for i in range(8))


@pytest.mark.parametrize("boundary", ["NOW=NOW+250", "FRAME=35", "FRAME=19"])
def test_expiry_at_input_without_render_or_update(controlled, boundary):
    send(controlled)
    controlled.execute(boundary)
    assert input_value(controlled) is None


def test_heartbeat_does_not_extend_hold_and_missing_heartbeat_disarms(controlled):
    lua = controlled
    send(lua)
    lua.execute("NOW=NOW+150")
    send(lua, sequence=2, kind="heartbeat", move="none", shoot="none", frames=0)
    assert input_value(lua) == 1
    lua.execute("NOW=NOW+100")
    assert input_value(lua) is None
    lua.execute("NOW=NOW+501")
    send(lua, sequence=3)
    assert lua.globals().CLOSED
    assert input_value(lua) is None


@pytest.mark.parametrize(
    "event",
    [
        "PEER_CLOSED=true; callbacks.render()",
        "PAUSED=true",
        "IS_DEAD=true",
        "NO_PLAYER=true",
        "PLAYER_COUNT=2",
        "callbacks.room()",
        "callbacks.level()",
        "callbacks.start()",
        "callbacks.game_end(mod,true)",
        "callbacks.game_end(mod,false)",
        "callbacks.exit()",
        "callbacks.unload(mod,mod)",
        "FAIL_STATE=true",
    ],
)
def test_cleanup_cannot_resume_old_hold(controlled, event):
    lua = controlled
    send(lua)
    lua.execute(event)
    assert input_value(lua) is None
    lua.execute("PAUSED=false; IS_DEAD=false; NO_PLAYER=false; PLAYER_COUNT=1; FAIL_STATE=false")
    assert input_value(lua) is None


@pytest.mark.parametrize(
    "changes",
    [
        {"sequence": 1},
        {"session_id": "b" * 32},
        {"game_epoch": 0},
        {"game_epoch": 2},
        {"room_visit": 1},
        {"frame_id": 19},
        {"frame_id": 21},
    ],
)
def test_stale_replayed_wrong_identity_closes_and_clears(controlled, changes):
    send(controlled)
    send(controlled, **changes)
    assert controlled.globals().CLOSED
    assert input_value(controlled) is None


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s.replace('"protocol_version":1', '"protocol_version":2'),
        lambda s: s.replace('"right"', '"diagonal"'),
        lambda s: s.replace('"frames":15', '"frames":16'),
        lambda s: s.replace('"frames":15', '"frames":true'),
        lambda s: s.replace('"frames":15', '"frames":1.5'),
        lambda s: s.replace('"frames":15', '"frames":0'),
        lambda s: s.replace('"frames":15', '"frames":15,"extra":1'),
        lambda s: s.replace('"frames":15', '"frames":15,"frames":15'),
        lambda s: s.replace('"kind":"action"', '"kind":"restart"'),
        lambda s: s.replace('"kind":"action"', '"kind":"heartbeat"'),
        lambda s: s.replace('"kind":"action"', '"kind":"release"'),
        lambda s: s.replace('"frames":15', '"frames":NaN'),
        lambda s: s.replace('"frames":15', '"frames":0xf'),
        lambda s: s.replace("}\n", "} trailing\n"),
        lambda s: s.replace("}\n", "}\r\n"),
        lambda s: "x" * 1026,
    ],
)
def test_invalid_commands_fail_closed_while_holding(controlled, mutate):
    raw = send(controlled)
    controlled.globals().INCOMING = mutate(raw.replace('"sequence":1', '"sequence":2'))
    tick(controlled, delta=1)
    assert controlled.globals().CLOSED
    assert input_value(controlled) is None


def test_reconnect_new_session_has_no_hold_or_old_authority(controlled):
    lua = controlled
    old = send(lua)
    lua.execute('PEER_CLOSED=true; callbacks.render(); PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    handshake(lua, "b" * 32, actions=True)
    assert input_value(lua) is None
    lua.globals().INCOMING = old
    tick(lua)
    assert lua.globals().CLOSED


def test_fragmented_command_and_stalled_python(controlled):
    lua = controlled
    raw = send(lua)
    raw = raw.replace('"sequence":1', '"sequence":2')
    lua.globals().INCOMING = raw[:25]
    tick(lua, delta=100)
    lua.globals().INCOMING = raw[25:]
    tick(lua, delta=1)
    assert input_value(lua) == 1
    lua.execute("NOW=NOW+501")
    assert input_value(lua) is None  # Python failure without FIN


def test_default_gate_and_unnegotiated_control():
    lua = build_lua()
    lua.execute("callbacks.start()")
    ack = handshake(lua)
    assert "safe_actions_v1" not in ack.capabilities
    lua.globals().INCOMING = '{"type":"command"}\n'
    tick(lua)
    assert lua.globals().CLOSED and input_value(lua) is None
    lua = build_lua()
    lua.execute("callbacks.start()")
    handshake_request(lua, ["safe_actions_v1"])
    assert lua.globals().CLOSED


def handshake_request(lua, extra):
    tick(lua)
    lua.globals().INCOMING = (
        json.dumps(
            dict(
                type="hello",
                protocol_version=1,
                schema_version=1,
                session_id="a" * 32,
                required_capabilities=list(CAPABILITIES) + extra,
            ),
            separators=(",", ":"),
        )
        + "\n"
    )
    tick(lua, 15)


def test_incompatible_modes_and_epoch_reapproval():
    lua = build_lua(approved=True)
    lua.execute("callbacks.start()")
    handshake_request(lua, ["safe_actions_v1", "death_restart_v1"])
    assert lua.globals().CLOSED
    lua = build_lua(approved=True)
    lua.execute("callbacks.start(); callbacks.start()")
    handshake_request(lua, ["safe_actions_v1"])
    assert lua.globals().CLOSED


@pytest.mark.parametrize("frame", [19, 36])
def test_current_frame_outside_freshness_window(controlled, frame):
    send(controlled)
    controlled.globals().FRAME = frame
    send(controlled, sequence=2)
    assert controlled.globals().CLOSED
    assert input_value(controlled) is None


def test_frame_limit_does_not_wait_for_wall_clock(controlled):
    send(controlled, frames=3)
    controlled.execute("FRAME=22")
    assert input_value(controlled) == 1
    controlled.execute("FRAME=23")
    assert input_value(controlled) is None


def test_ack_backpressure_never_extends_hold(controlled):
    lua = controlled
    lua.execute("BLOCK_OUTPUT=true")
    send(lua)
    assert input_value(lua) == 1
    tick(lua, delta=250)
    assert input_value(lua) is None
    tick(lua, delta=3001)
    assert lua.globals().CLOSED


def test_partial_ack_cannot_authorize_command():
    lua = build_lua(approved=True)
    lua.execute("callbacks.start(); SEND_LIMIT=1")
    tick(lua)
    lua.globals().INCOMING = (
        json.dumps(
            dict(
                type="hello",
                protocol_version=1,
                schema_version=1,
                session_id="a" * 32,
                required_capabilities=list(CAPABILITIES) + ["safe_actions_v1"],
            ),
            separators=(",", ":"),
        )
        + "\n"
    )
    tick(lua)
    lua.globals().INCOMING = '{"type":"command"}\n'
    tick(lua)
    assert lua.globals().CLOSED


def test_invalid_input_api_is_fail_closed(controlled):
    send(controlled)
    controlled.execute("GetPtrHash=nil")
    assert input_value(controlled) is None
    assert controlled.globals().CLOSED


@pytest.mark.parametrize(
    "move,shoot,buttons",
    [
        ("left", "down", (0, 7)),
        ("right", "up", (1, 6)),
        ("up", "right", (2, 5)),
        ("down", "left", (3, 4)),
        ("none", "left", (4,)),
        ("up", "none", (2,)),
    ],
)
def test_cardinal_mapping_and_independent_none(controlled, move, shoot, buttons):
    send(controlled, move=move, shoot=shoot)
    assert [input_value(controlled, i) for i in range(8)] == [int(i in buttons) for i in range(8)]


@pytest.mark.parametrize(
    "changes",
    [
        {"profile_id": ""},
        {"profile_evidence": ""},
        {"slot_evidence": ""},
        {"runtime_authorization": ""},
        {"slot": 1},
        {"slot": True},
        {"profile_id": " "},
        {"game_epoch": 2},
    ],
)
def test_incomplete_local_approval_never_advertises_control(changes):
    lua = build_lua(approved=True, approval_changes=changes)
    lua.execute("callbacks.start()")
    ack = handshake(lua)
    assert "safe_actions_v1" not in ack.capabilities
    assert input_value(lua) is None


@pytest.mark.parametrize("mode", ["isolated", "ordinary_profile_exception"])
def test_approved_profile_modes(mode):
    lua = build_lua(approved=True, approval_changes={"profile_mode": mode})
    lua.execute("callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=4096")
    handshake(lua, actions=True)
    send(lua)
    assert input_value(lua) == 1


@pytest.mark.parametrize(
    "changes",
    [
        {"profile_mode": "ordinary"},
        {"expires_at": 1},
        {"expires_at": 9999999999999},
        {"expires_at": True},
    ],
)
def test_expired_or_incompatible_local_authority(changes):
    lua = build_lua(approved=True, approval_changes=changes)
    lua.execute("callbacks.start()")
    assert "safe_actions_v1" not in handshake(lua).capabilities


def test_authority_lease_is_not_renewed_by_reconnect(controlled):
    lua = controlled
    send(lua)
    lua.execute('PEER_CLOSED=true; callbacks.render(); PEER_CLOSED=false; OUTGOING=""; NOW=100000')
    handshake(lua, "b" * 32, actions=True)
    send(lua)
    lua.execute("NOW=120500")
    assert input_value(lua) is None
    assert lua.globals().CLOSED
    lua.execute('OUTGOING=""; NOW=122000')
    assert "safe_actions_v1" not in handshake(lua, "c" * 32).capabilities


def test_hold_expiry_releases_input_and_logs_the_release(controlled):
    lua = controlled
    send(lua)
    lua.execute("NOW=NOW+250; callbacks.update()")
    logs = list(lua.globals().LOGS.values())
    assert any("Action release reason=expiry" in line and "sequence=1" in line for line in logs)
    assert input_value(lua) is None


def test_private_json_approval_loaded_once_without_save_writes():
    import time

    lua = build_lua()
    record = dict(
        profile_id="ordinary-user",
        profile_mode="ordinary_profile_exception",
        profile_evidence="direct-user-instruction",
        slot_evidence="operator-file-2",
        runtime_authorization="bounded-probe",
        slot=2,
        game_epoch=1,
        expires_at=int(time.time()) + 600,
    )
    lua.globals().APPROVAL_JSON = json.dumps(record)
    lua.execute("""
    FILE_READS=0
    io.open=function(path,mode)
        assert(path=="mods/isaac_threrisaifuture_observer/action_authorization.json")
        assert(mode=="rb")
        return {read=function(_,n)
            assert(n==2049); FILE_READS=FILE_READS+1; return APPROVAL_JSON end,
                close=function() end}
    end
    callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=4096
    """)
    handshake(lua, actions=True)
    send(lua)
    assert input_value(lua) == 1
    lua.execute('PEER_CLOSED=true; callbacks.render(); PEER_CLOSED=false; OUTGOING=""; NOW=2000')
    handshake(lua, "b" * 32, actions=True)
    assert lua.globals().FILE_READS == 1


def test_missing_approval_can_be_created_after_read_only_slot_confirmation():
    import time

    lua = build_lua()
    lua.execute("callbacks.start(); SEND_LIMIT=4096")
    first = handshake(lua)
    assert "safe_actions_v1" not in first.capabilities
    record = dict(
        profile_id="ordinary-user",
        profile_mode="ordinary_profile_exception",
        profile_evidence="direct-user-instruction",
        slot_evidence="operator-file-2",
        runtime_authorization="bounded-probe",
        slot=2,
        game_epoch=1,
        expires_at=int(time.time()) + 600,
    )
    lua.globals().APPROVAL_JSON = json.dumps(record)
    lua.execute("""
    io.open=function(path,mode)
        return {read=function() return APPROVAL_JSON end, close=function() end}
    end
    PEER_CLOSED=true; callbacks.render(); PEER_CLOSED=false; OUTGOING=""; NOW=2000
    """)
    assert "safe_actions_v1" in handshake(lua, "b" * 32, actions=True).capabilities


USE_BUTTONS = {"active": 8, "pillcard": 9, "bomb": 10}
PRESSED, TRIGGERED, VALUE = 0, 1, 2


@pytest.mark.parametrize("use", ["bomb", "active", "pillcard"])
def test_use_triggers_once_and_stays_pressed_while_the_hold_is_live(controlled, use):
    lua, button = controlled, USE_BUTTONS[use]
    send(lua, use=use)
    assert input_value(lua, button, PRESSED) is True
    assert input_value(lua, button, VALUE) == 1.0
    assert input_value(lua, button, TRIGGERED) is True  # exactly once
    assert input_value(lua, button, TRIGGERED) is False
    assert input_value(lua, button, PRESSED) is True  # still held
    for other in set(USE_BUTTONS.values()) - {button}:
        assert input_value(lua, other, PRESSED) is None  # other use buttons are untouched
        assert input_value(lua, other, TRIGGERED) is None
    assert input_value(lua, 1, VALUE) == 1  # movement keeps working beside the use
    assert lua.eval(f"callbacks.input(mod,nil,1,{button})") is None


def test_each_accepted_command_arms_a_new_single_trigger(controlled):
    lua = controlled
    send(lua, use="bomb", sequence=1)
    assert input_value(lua, 10, TRIGGERED) is True and input_value(lua, 10, TRIGGERED) is False
    send(lua, use="bomb", sequence=2)
    assert input_value(lua, 10, TRIGGERED) is True and input_value(lua, 10, TRIGGERED) is False


def test_use_none_presses_nothing_and_replacement_drops_the_old_use(controlled):
    lua = controlled
    send(lua, use="none", sequence=1)
    assert all(input_value(lua, b, h) is None for b in USE_BUTTONS.values() for h in (0, 1, 2))
    send(lua, use="bomb", sequence=2)
    assert input_value(lua, 10, PRESSED) is True
    send(lua, use="active", sequence=3)
    assert input_value(lua, 10, PRESSED) is None and input_value(lua, 10, TRIGGERED) is None
    assert input_value(lua, 8, PRESSED) is True and input_value(lua, 8, TRIGGERED) is True


@pytest.mark.parametrize("ending", ["release", "expiry", "room", "disconnect"])
def test_use_buttons_clear_when_the_hold_ends(controlled, ending):
    lua = controlled
    send(lua, use="bomb")
    assert input_value(lua, 10, PRESSED) is True
    if ending == "release":
        send(lua, sequence=2, kind="release", move="none", shoot="none", frames=0, use="none")
    elif ending == "expiry":
        lua.execute("FRAME=FRAME+15")
    elif ending == "room":
        lua.execute("callbacks.room()")
    else:
        lua.execute("PEER_CLOSED=true")
        tick(lua)
    assert input_value(lua, 10, PRESSED) is None
    assert input_value(lua, 10, TRIGGERED) is None
    assert input_value(lua, 10, VALUE) is None


@pytest.mark.parametrize("kind", ["heartbeat", "release"])
@pytest.mark.parametrize("use", ["bomb", "active", "pillcard"])
def test_use_on_a_non_action_command_is_refused_and_presses_nothing(controlled, kind, use):
    lua = controlled
    snap = snapshots(lua)[-1]
    raw = (
        Command(
            session_id=snap.session_id,
            sequence=1,
            game_epoch=snap.game_epoch,
            room_visit=snap.room.visit_id,
            frame_id=snap.frame_id,
            kind=kind,
        )
        .wire_bytes()
        .decode()
    )
    assert '"use":"none"' in raw
    lua.globals().INCOMING = raw.replace('"use":"none"', f'"use":"{use}"')
    tick(lua, delta=1)
    assert lua.globals().CLOSED
    assert all(input_value(lua, b, h) is None for b in USE_BUTTONS.values() for h in (0, 1, 2))


@pytest.mark.parametrize(
    "edit",
    [
        lambda raw: raw.replace('"use":"none",', ""),  # old command shape without use
        lambda raw: raw.replace('"use":"none"', '"use":"grenade"'),
        lambda raw: raw.replace('"use":"none"', '"use":1'),
        lambda raw: raw.replace('"use":"none","frames":15', '"frames":15,"use":"none"'),
    ],
)
def test_noncanonical_or_old_shape_commands_are_refused(controlled, edit):
    lua = controlled
    snap = snapshots(lua)[-1]
    raw = (
        Command(
            session_id=snap.session_id,
            sequence=1,
            game_epoch=snap.game_epoch,
            room_visit=snap.room.visit_id,
            frame_id=snap.frame_id,
            kind="action",
            move="right",
            shoot="up",
            frames=15,
        )
        .wire_bytes()
        .decode()
    )
    changed = edit(raw)
    assert changed != raw
    lua.globals().INCOMING = changed
    tick(lua, delta=1)
    assert lua.globals().CLOSED
    assert input_value(lua, 1, VALUE) is None
