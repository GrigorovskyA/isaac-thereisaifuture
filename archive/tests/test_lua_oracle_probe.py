"""Production Lua probe with simulated callbacks, entities and I/O; no Isaac proof."""

import pytest
import test_lua_observer
from test_lua_actions import input_value, send
from test_lua_callback_trace import field
from test_lua_observer import build_lua, handshake, snapshots, tick

PREFIX = "[Isaac Future OracleProbe]"


def logs(lua):
    return [line for line in lua.globals().LOGS.values() if line.startswith(PREFIX)]


def events(lua):
    return [field(line, "event") for line in logs(lua)]


def prepared(*, enabled=True, actions=False, restart=False):
    lua = build_lua(approved=actions)
    lua.execute(
        "callbacks.start(); callbacks.room(); SEND_LIMIT=4096;"
        "TEST_PLAYER=Isaac.GetPlayer(0);"
        "NPC={Type=10,Variant=0,HitPoints=12};"
        "NPC.ToNPC=function(self) return self end; NPC.ToPlayer=function() return nil end;"
        "NPC.Exists=function() return true end;"
        "SOURCE={Entity={Type=2}}"
    )
    handshake(
        lua, actions=actions, restart=restart, oracle_probe=enabled and not (actions or restart)
    )
    return lua


def test_default_callbacks_are_inert_without_diagnostic_request():
    lua = prepared(enabled=False)
    lua.execute("GetPtrHash=function() error('must not read') end")
    assert lua.eval("callbacks.damage(mod,NPC,1,0,nil,0)") is None
    assert lua.eval("callbacks.award()") is None
    lua.execute(
        "callbacks.npc_init(mod,NPC); callbacks.npc_update(mod,NPC);"
        " callbacks.update(); callbacks.game_end(mod,true)"
    )
    assert logs(lua) == []


def test_readonly_attach_starts_without_action_approval_and_stays_outside_wire():
    lua = prepared()
    assert events(lua) == ["attach"]
    lua.execute("callbacks.update()")
    assert events(lua) == ["attach", "post_update"]
    sample = logs(lua)[-1]
    assert field(sample, "red") == "5" and field(sample, "soul") == "2"
    assert field(sample, "dead") == field(sample, "clear") == "false"
    tick(lua, 15)
    assert snapshots(lua) and PREFIX not in lua.globals().OUTGOING
    assert "native_oracle_event" not in lua.globals().OUTGOING
    assert input_value(lua) is None and len(lua.globals().COMMANDS) == 0


@pytest.mark.parametrize("mode", ["actions", "restart"])
def test_control_modes_never_start_passive_probe(mode):
    lua = prepared(**{mode: True})
    lua.execute("callbacks.damage(mod,NPC,5,0,SOURCE,0); callbacks.award(); callbacks.update()")
    assert logs(lua) == []
    if mode == "actions":
        send(lua)
        assert input_value(lua) == 1
        lua.execute("callbacks.room()")
        assert input_value(lua) is None


def test_invalid_hello_and_callbacks_before_attach_do_not_start():
    lua = build_lua()
    lua.execute("callbacks.award(); callbacks.update(); callbacks.start(); SEND_LIMIT=4096")
    assert logs(lua) == []
    tick(lua)
    lua.execute('INCOMING="{}\\n"')
    tick(lua)
    assert logs(lua) == [] and lua.globals().CLOSED
    lua.execute('OUTGOING=""')
    tick(lua, delta=1001)
    handshake(lua, "d" * 32, oracle_probe=True)
    assert events(lua) == ["attach"]


def test_ordinary_attach_disconnect_does_not_consume_window():
    lua = prepared(enabled=False)
    lua.execute('PEER_CLOSED=true; callbacks.render(); PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    handshake(lua, "b" * 32, oracle_probe=True)
    assert events(lua) == ["attach"]


@pytest.mark.parametrize("mode", ["actions", "restart"])
def test_lua_rejects_probe_control_combination_without_starting(mode):
    lua = build_lua(approved=mode == "actions")
    lua.execute("callbacks.start(); SEND_LIMIT=4096")
    with pytest.raises(IndexError):
        handshake(lua, actions=mode == "actions", restart=mode == "restart", oracle_probe=True)
    assert lua.globals().CLOSED and logs(lua) == []


def test_exhausted_request_fails_but_ordinary_observation_still_works():
    lua = prepared()
    lua.execute('PEER_CLOSED=true; callbacks.render(); PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    # Negative handshakes have no ack, so the helper reports IndexError after Lua closes.
    with pytest.raises(IndexError):
        handshake(lua, "b" * 32, oracle_probe=True)
    assert lua.globals().CLOSED
    lua.execute('OUTGOING=""')
    tick(lua, delta=1001)
    ack = handshake(lua, "c" * 32)
    assert "oracle_probe_v1" not in ack.capabilities
    tick(lua, 15)
    assert snapshots(lua) and len(logs(lua)) == 2


def test_damage_is_attempt_only_nil_return_and_pending_update_coalesces():
    lua = prepared()
    assert lua.eval("callbacks.damage(mod,NPC,50,4,SOURCE,7)") is None
    assert lua.eval("callbacks.damage(mod,NPC,3,0,SOURCE,0)") is None
    attempts = logs(lua)[-2:]
    assert all(field(x, "event") == "damage_attempt" and field(x, "hp") == "12" for x in attempts)
    assert field(attempts[0], "requested") == "50" and field(attempts[0], "source_type") == "2"
    assert field(attempts[0], "flags") == "4" and field(attempts[0], "countdown") == "7"
    # A later callback's HP is a raw sample, not per-hit attribution or a producer outcome.
    lua.execute("NPC.HitPoints=9; FRAME=21; callbacks.npc_update(mod,NPC)")
    assert field(logs(lua)[-1], "hp") == "9" and events(lua)[-1] == "npc_update_hp"
    total = len(logs(lua))
    lua.execute("callbacks.npc_update(mod,NPC)")
    assert len(logs(lua)) == total
    assert lua.globals().NPC.HitPoints == 9


def test_cancelled_attempt_can_leave_health_unchanged_without_manufacturing_damage():
    lua = prepared()
    lua.execute("callbacks.damage(mod,NPC,12,0,nil,0); callbacks.npc_update(mod,NPC)")
    assert field(logs(lua)[-1], "hp") == "12"
    assert "enemy_damaged" not in "\n".join(logs(lua))


def test_callback_sequence_uses_local_labels_without_pointer_or_spawn_claims():
    lua = prepared()
    lua.execute(
        "callbacks.npc_init(mod,NPC); callbacks.npc_update(mod,NPC);"
        "callbacks.kill(mod,NPC); callbacks.npc_death(mod,NPC); callbacks.remove(mod,NPC)"
    )
    assert events(lua)[1:] == [
        "npc_init",
        "npc_update_hp",
        "entity_kill",
        "npc_death",
        "entity_remove",
    ]
    assert {field(x, "label") for x in logs(lua)[1:]} == {"1"}
    lua.execute("callbacks.npc_init(mod,NPC)")  # Possible morph: diagnostic relabel only.
    assert field(logs(lua)[-1], "label") == "2"
    assert not any(
        word in "\n".join(logs(lua)) for word in ("table:", "pointer", "reward", "generation")
    )


def test_award_death_transition_and_revival_samples_are_facts_only():
    lua = prepared()
    assert lua.eval("callbacks.award()") is None
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true); callbacks.update()")
    assert "game_end" in events(lua) and field(logs(lua)[-1], "dead") == "true"
    lua.execute(
        "NOW=NOW+201; IS_DEAD=false; callbacks.update(); callbacks.room(); callbacks.level()"
    )
    assert field(logs(lua)[-3], "dead") == "false"
    assert events(lua)[-2:] == ["new_room", "new_level"]
    assert len(lua.globals().COMMANDS) == 0


def test_projectile_removals_do_not_consume_entity_labels_or_log_budget():
    lua = prepared()
    lua.execute(
        "SHOT={ToNPC=function() return nil end,ToPlayer=function() return nil end};"
        "for i=1,1100 do callbacks.remove(mod,SHOT); callbacks.kill(mod,SHOT) end;"
        "callbacks.npc_init(mod,NPC)"
    )
    assert events(lua) == ["attach", "npc_init"]
    assert field(logs(lua)[-1], "label") == "1"


def test_room_transition_discards_pending_samples_without_reusing_labels():
    lua = prepared()
    lua.execute(
        "callbacks.damage(mod,NPC,1,0,nil,0); callbacks.room(); callbacks.npc_update(mod,NPC)"
    )
    assert "npc_update_hp" not in events(lua)
    lua.execute("callbacks.npc_init(mod,NPC)")
    assert field(logs(lua)[-1], "label") == "2"


def test_post_update_sampling_has_interval_and_one_callback_triggered_sample():
    lua = prepared()
    lua.execute("callbacks.update(); callbacks.update(); callbacks.update()")
    assert events(lua).count("post_update") == 1
    lua.execute("callbacks.award(); callbacks.update(); callbacks.update()")
    assert events(lua).count("post_update") == 2
    lua.execute("NOW=NOW+200; callbacks.update()")
    assert events(lua).count("post_update") == 3


def test_game_end_requests_immediate_next_update_sample_without_other_callbacks():
    lua = prepared()
    lua.execute(
        "callbacks.update(); IS_DEAD=true; callbacks.game_end(mod,true); callbacks.update()"
    )
    assert events(lua)[-2:] == ["game_end", "post_update"]
    assert field(logs(lua)[-1], "dead") == "true"


def test_record_budget_has_one_final_stop_and_bounded_lines():
    lua = prepared()
    lua.execute("for i=1,1100 do callbacks.award() end")
    seen = logs(lua)
    assert len(seen) == 1024 and all(len(x.encode()) <= 400 for x in seen)
    assert [int(field(x, "id")) for x in seen] == list(range(1, 1025))
    assert field(seen[-1], "event") == "stop" and field(seen[-1], "reason") == "count"
    lua.execute("callbacks.damage(mod,{},1,0,nil,0); callbacks.update(); callbacks.room()")
    assert len(logs(lua)) == 1024


def test_deadline_is_checked_during_paused_render_without_updates():
    lua = prepared()
    attached = int(field(logs(lua)[0], "time_ms"))
    lua.execute(f"PAUSED=true; NOW={attached + 120000}; callbacks.render()")
    assert events(lua)[-1] == "stop" and field(logs(lua)[-1], "reason") == "deadline"
    total = len(logs(lua))
    lua.execute("callbacks.award(); callbacks.update()")
    assert len(logs(lua)) == total


def test_label_budget_stops_without_retaining_unbounded_entities():
    lua = prepared()
    lua.execute(
        "for i=1,129 do callbacks.npc_init(mod,{Type=10,HitPoints=1,"
        "Exists=function() return true end}); callbacks.update() end"
    )
    assert events(lua).count("npc_init") == 128
    assert events(lua)[-1] == "stop" and field(logs(lua)[-1], "reason") == "labels"
    total = len(logs(lua))
    lua.execute("callbacks.npc_init(mod,NPC); callbacks.award()")
    assert len(logs(lua)) == total
    tick(lua, 15)
    assert snapshots(lua) and not lua.globals().CLOSED


@pytest.mark.parametrize("finish", ["disconnect", "exit", "unload"])
def test_stop_and_reconnect_cannot_renew_probe(finish):
    lua = prepared()
    if finish == "disconnect":
        lua.execute("PEER_CLOSED=true; callbacks.render()")
    elif finish == "unload":
        lua.execute("callbacks.unload(mod,mod)")
    else:
        lua.execute(f"callbacks.{finish}(mod)")
    assert lua.globals().CLOSED and events(lua)[-1] == "stop"
    total = len(logs(lua))
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    handshake(lua, "b" * 32)
    lua.execute("callbacks.award(); callbacks.update()")
    assert len(logs(lua)) == total


@pytest.mark.parametrize("failure", ["logger", "read", "invalid_scalar"])
def test_diagnostic_failure_never_changes_callback_return_or_observer(failure):
    lua = prepared()
    if failure == "logger":
        lua.execute(
            "print=function(m) if m:find('OracleProbe',1,true) then error('log fail') end end"
        )
    elif failure == "read":
        lua.execute("GetPtrHash=function() error('read fail') end")
    else:
        lua.execute("NPC.HitPoints=0/0")
    assert lua.eval("callbacks.damage(mod,NPC,1,0,SOURCE,0)") is None
    assert lua.eval("callbacks.award()") is None
    total = len(logs(lua))
    tick(lua, 15)
    assert snapshots(lua) and not lua.globals().CLOSED
    assert len(logs(lua)) == total


def test_missing_callback_disables_probe_without_breaking_observation(tmp_path, monkeypatch):
    monkeypatch.setattr(
        test_lua_observer, "STUBS", test_lua_observer.STUBS + "\nModCallbacks.MC_NPC_UPDATE=nil"
    )
    lua = prepared(enabled=False)
    assert lua.globals().callbacks.damage is None and logs(lua) == []
    tick(lua, 15)
    assert snapshots(lua)
