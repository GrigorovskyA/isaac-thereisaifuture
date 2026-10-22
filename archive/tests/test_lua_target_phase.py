"""OFFLINE read-only phase diagnostics over production Lua; not native phase proof."""

import json

import pytest
from test_lua_live_loop import build_live, hello, live_snapshots
from test_lua_observer import tick

from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES

STUBS = """
AUDIT_READS=0
EntityType.ENTITY_EFFECT=1000
function phase_enemy(id,x)
 local e=make_enemy(id,x or 140,200,10,20)
 e.Variant,e.SubType,e.State=0,0,4
 e.dead,e.active,e.vulnerable=false,true,true
 e.ToNPC=function(self) AUDIT_READS=AUDIT_READS+1; return self end
 e.IsEnemy=function() AUDIT_READS=AUDIT_READS+1; return true end
 e.IsVulnerableEnemy=function(self) AUDIT_READS=AUDIT_READS+1; return self.vulnerable end
 e.IsDead=function(self) return self.dead end
 e.IsActiveEnemy=function(self,include_dead) return self.active or include_dead end
 e.champion=-1
 e.GetChampionColorIdx=function(self) AUDIT_READS=AUDIT_READS+1; return self.champion end
 return e
end
ROOM_ENTITIES={phase_enemy(1)}
"""


def build(flag="true", passive_effects="false"):
    effects_config = f"target_phase_passive_effects = {passive_effects},"
    lua = build_live(
        source_changes={
            "target_phase_diagnostics = false,": f"target_phase_diagnostics = {flag},",
            "target_phase_passive_effects = false,": effects_config,
        }
    )
    lua.execute(STUBS)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    return lua


def lines(lua):
    return [s for s in lua.globals().LOGS.values() if "[Isaac Future TargetPhase]" in s]


@pytest.mark.parametrize("flag", ["false", "1", '"true"', "{}"])
def test_disabled_has_no_extra_api_reads_or_local_lines(flag):
    lua = build(flag)
    assert lua.globals().AUDIT_READS == 0 and lines(lua) == []
    assert live_snapshots(lua)[-1].oracle.enemies


def test_vulnerable_dead_phase_is_logged_but_never_inserted_in_exports():
    lua = build()
    initial = live_snapshots(lua)[-1]
    assert initial.entity_frame.entities and initial.oracle.enemies
    assert "policy=true oracle=true" in lines(lua)[0]
    lua.execute(
        "ROOM_ENTITIES[1].dead=true; ROOM_ENTITIES[1].active=false; ROOM_ENTITIES[1].State=12"
    )
    tick(lua, 7)
    phase = live_snapshots(lua)[-1]
    assert phase.entity_frame.entities == [] and phase.oracle.enemies == []
    record = lines(lua)[-1]
    assert "label=1" in record and "dead=true" in record and "vulnerable=true" in record
    assert "policy=false oracle=false" in record and "npc_state=12" in record
    assert "session=" in record and "epoch=1" in record and "visit=0" in record
    assert "InitSeed" not in record and "e:" not in record
    assert "TargetPhase" not in lua.globals().OUTGOING


def test_membership_is_measured_after_policy_capacity_selection():
    lua = build()
    lua.execute("ROOM_ENTITIES={}; for i=1,13 do ROOM_ENTITIES[i]=phase_enemy(i,100+i) end")
    tick(lua, 7)
    state = live_snapshots(lua)[-1]
    assert len(state.entity_frame.entities) == 12 and len(state.oracle.enemies) == 13
    assert any("policy=false oracle=true" in s for s in lines(lua))


def test_position_changes_do_not_generate_semantic_change_lines():
    lua = build()
    count = len(lines(lua))
    lua.execute("ROOM_ENTITIES[1].Position.X=250")
    tick(lua, 20)
    assert len(lines(lua)) == count
    lua.execute("ROOM_ENTITIES={}")
    tick(lua, 7)
    assert "event=gone" in lines(lua)[-1] and "death" not in lines(lua)[-1]


def test_enabling_audit_preserves_wire_payloads():
    disabled, enabled = build("false"), build()

    def parse(lua):
        return [json.loads(s) for s in lua.globals().OUTGOING.splitlines()]

    assert parse(disabled) == parse(enabled)


def test_logging_failure_does_not_break_capture():
    lua = build()
    lua.execute(
        "Isaac.DebugString=function() error('audit log unavailable') end; ROOM_ENTITIES[1].State=12"
    )
    tick(lua, 7)
    assert live_snapshots(lua)[-1].status == "active" and not lua.globals().CLOSED


def test_missing_diagnostic_api_stops_only_audit_and_normal_capture_continues():
    lua = build()
    lua.execute("ROOM_ENTITIES[1].ToNPC=function() error('unavailable audit api') end")
    tick(lua, 7)
    assert "event=stop" in lines(lua)[-1] and "reason=error" in lines(lua)[-1]
    assert live_snapshots(lua)[-1].status == "active"
    count = len(lines(lua))
    tick(lua, 15)
    assert len(lines(lua)) == count and not lua.globals().CLOSED


def test_scan_budget_stops_without_changing_normal_membership():
    lua = build()
    lua.execute("ROOM_ENTITIES={}; for i=1,65 do ROOM_ENTITIES[i]=phase_enemy(i) end")
    tick(lua, 7)
    assert "reason=scan" in lines(lua)[-1]
    assert live_snapshots(lua)[-1].oracle.enemy_overflow == 1


def test_nonrenewable_deadline_and_line_bounds():
    lua = build()
    lua.execute("NOW=NOW+120001")
    tick(lua)
    assert "reason=deadline" in lines(lua)[-1]
    count = len(lines(lua))
    lua.execute("ROOM_ENTITIES[1].State=15")
    tick(lua, 10)
    assert len(lines(lua)) == count

    lua = build()
    for i in range(530):
        lua.execute(f"ROOM_ENTITIES[1].State={i}")
        tick(lua, 1, delta=100)
    assert len(lines(lua)) == 512 and "reason=lines" in lines(lua)[-1]
    assert max(map(len, lines(lua))) <= 800


def test_label_budget_stops_without_eviction():
    lua = build()
    for i in range(2, 130):
        lua.execute(f"ROOM_ENTITIES={{phase_enemy({i})}}")
        tick(lua, 1, delta=100)
    assert "reason=labels" in lines(lua)[-1]
    assert not lua.globals().CLOSED and live_snapshots(lua)[-1].status == "active"


EFFECT = """
function phase_effect(id,vulnerable)
 local e=phase_enemy(id)
 e.Type=1000; e.active=false; e.vulnerable=vulnerable
 e.ToNPC=function() return nil end
 e.IsEnemy=function() return false end
 e.IsActiveEnemy=function() return false end
 return e
end
"""


def test_passive_effect_churn_preserves_lifetime_budget_for_npc_phase():
    lua = build()
    lua.execute(EFFECT + "TARGET=ROOM_ENTITIES[1]")
    for i in range(2, 145):
        lua.execute(f"ROOM_ENTITIES={{TARGET,phase_effect({i},false)}}")
        tick(lua, 1, delta=100)
    lua.execute("TARGET.State=12; TARGET.dead=true; TARGET.active=false")
    tick(lua, 7)
    assert not any("event=stop" in s or "type=1000" in s for s in lines(lua))
    assert "label=1" in lines(lua)[-1] and "npc_state=12" in lines(lua)[-1]
    assert "vulnerable=true" in lines(lua)[-1]
    assert "policy=false oracle=false" in lines(lua)[-1]


def test_vulnerable_effect_is_a_candidate_even_without_passive_opt_in():
    lua = build()
    lua.execute(EFFECT + "ROOM_ENTITIES={phase_effect(2,true)}")
    tick(lua, 7)
    assert any(
        "type=1000" in s and "vulnerable=true" in s and "policy=false oracle=false" in s
        for s in lines(lua)
    )


@pytest.mark.parametrize("flag, included", [("true", True), ("false", False), ('"true"', False)])
def test_passive_effect_opt_in_is_literal_and_does_not_change_wire(flag, included):
    lua = build(passive_effects=flag)
    lua.execute(EFFECT + "ROOM_ENTITIES={phase_effect(2,false)}")
    tick(lua, 7)
    assert any("type=1000" in s for s in lines(lua)) is included
    state = live_snapshots(lua)[-1]
    assert not state.entity_frame.entities and not state.oracle.enemies


def test_champion_modifier_is_local_evidence_and_triggers_a_new_record():
    lua = build()
    assert "champion_color=-1" in lines(lua)[0]
    lua.execute("ROOM_ENTITIES[1].champion=12")
    tick(lua, 7)
    assert "label=1" in lines(lua)[-1] and "champion_color=12" in lines(lua)[-1]
    assert "champion_color" not in lua.globals().OUTGOING


def test_unavailable_champion_api_keeps_phase_diagnostics_running():
    lua = build()
    lua.execute("ROOM_ENTITIES[1].GetChampionColorIdx=nil; ROOM_ENTITIES[1].State=12")
    tick(lua, 7)
    assert "npc_state=12" in lines(lua)[-1] and "event=state" in lines(lua)[-1]
    assert live_snapshots(lua)[-1].status == "active"
