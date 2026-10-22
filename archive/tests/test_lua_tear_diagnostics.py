"""Production Lua offline tear audit tests; mocks do not establish engine physics."""

import json

import pytest
from test_lua_live_loop import build_live, hello, live_snapshots
from test_lua_observer import tick

from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES

STUBS = """
AUDIT_READS=0
EntityType.ENTITY_TEAR=2
Vector=function(x,y) return {X=x,Y=y} end
TEST_PLAYER.TearRange=260
function make_tear(id,owner)
 local t=make_entity(id,110,200,2)
 t.SpawnerEntity=owner or TEST_PLAYER
 t.ToTear=function(self) AUDIT_READS=AUDIT_READS+1; return self end
 t.Height,t.FallingSpeed,t.FallingAcceleration=-20,-1,.5
 t.TearFlags,t.GridCollisionClass=0,1
 return t
end
ROOM_ENTITIES={make_enemy(1,400,200,10,10),make_tear(2)}
local previous_game=Game
Game=function()
 local game=previous_game(); local previous_room=game.GetRoom
 game.GetRoom=function(self)
  local room=previous_room(self)
  room.CheckLine=function(self,a,b,mode,threshold,walls,crush)
   AUDIT_READS=AUDIT_READS+1
   assert(mode==3 and threshold==0 and walls==false and crush==false)
   return false,Vector(200,200)
  end
  return room
 end
 return game
end
"""


def build(flag="true"):
    lua = build_live(source_changes={"tear_diagnostics = false,": f"tear_diagnostics = {flag},"})
    lua.execute(STUBS)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    return lua


def lines(lua):
    return [s for s in lua.globals().LOGS.values() if "[Isaac Future TearAudit]" in s]


@pytest.mark.parametrize("flag", ["false", "1", '"true"', "{}"])
def test_disabled_has_no_additional_reads(flag):
    lua = build(flag)
    assert lua.globals().AUDIT_READS == 0 and not lines(lua)


def test_wire_payload_and_game_entities_unchanged():
    off, on = build("false"), build()
    assert [json.loads(s) for s in off.globals().OUTGOING.splitlines()] == [
        json.loads(s) for s in on.globals().OUTGOING.splitlines()
    ]
    assert on.eval("ROOM_ENTITIES[2].Position.X") == 110
    assert "TearAudit" not in on.globals().OUTGOING
    assert "range=260" in lines(on)[0] and "clear3=false" in lines(on)[0]
    assert "hit_x=200" in lines(on)[0] and "dx=300" in lines(on)[0]


def test_owned_trajectory_and_absence_are_sampled_facts():
    lua = build()
    lua.execute("ROOM_ENTITIES[2].Position.X=140; ROOM_ENTITIES[2].Position.Y=240")
    tick(lua, 7)
    assert any("distance=50" in s and "path=50" in s for s in lines(lua))
    lua.execute("ROOM_ENTITIES={ROOM_ENTITIES[1]}")
    tick(lua, 7)
    record = [s for s in lines(lua) if "event=absent" in s][-1]
    assert "label=1" in record and "path=50" in record
    assert "collision" not in record and "death" not in record
    assert "InitSeed" not in record


def test_other_owners_are_not_tracked():
    # Enable through a fresh source instance; no dynamic Config mutation.
    other = build_live(source_changes={"tear_diagnostics = false,": "tear_diagnostics = true,"})
    other.execute(STUBS + "ROOM_ENTITIES[2].SpawnerEntity={ToPlayer=function() return nil end}")
    hello(other, LIVE_LOOP_CAPABILITIES)
    assert not any("event=sample" in s for s in lines(other))


def test_missing_optional_line_api_and_stat_are_unavailable():
    lua = build_live(source_changes={"tear_diagnostics = false,": "tear_diagnostics = true,"})
    lua.execute(
        STUBS + "TEST_PLAYER.TearRange=nil; local base=Game; Game=function() local g=base(); "
        "local r=g.GetRoom(g); r.CheckLine=nil; g.GetRoom=function() return r end; return g end"
    )
    hello(lua, LIVE_LOOP_CAPABILITIES)
    assert "range=na" in lines(lua)[0] and "clear3=na" in lines(lua)[0]
    assert any("event=sample" in s for s in lines(lua))


def test_failure_stops_only_diagnostics():
    lua = build()
    lua.execute("ROOM_ENTITIES[2].ToTear=function() error('test fault') end")
    tick(lua, 7)
    assert "reason=error" in lines(lua)[-1]
    n = len(lines(lua))
    tick(lua, 10)
    assert len(lines(lua)) == n and live_snapshots(lua)[-1].status == "active"
    assert not lua.globals().CLOSED


def test_deadline_context_and_scan_stop_without_bridge_fault():
    lua = build()
    lua.execute("NOW=NOW+120001")
    tick(lua)
    assert "reason=deadline" in lines(lua)[-1]
    lua = build()
    lua.execute("callbacks.room()")
    tick(lua, 7)
    assert "reason=context" in lines(lua)[-1]
    lua = build()
    lua.execute("ROOM_ENTITIES={}; for i=1,65 do ROOM_ENTITIES[i]=make_entity(i,110,200,2) end")
    tick(lua, 7)
    assert "reason=scan" in lines(lua)[-1]
    assert not lua.globals().CLOSED


def test_lifetime_and_line_caps_are_nonrenewable():
    lua = build()
    for i in range(3, 68):
        lua.execute(f"ROOM_ENTITIES={{make_tear({i})}}")
        tick(lua, 1, delta=100)
    assert "reason=labels" in lines(lua)[-1]
    lua = build()
    tick(lua, 1100, delta=100)
    assert len(lines(lua)) == 1024 and "reason=lines" in lines(lua)[-1]
    assert max(map(len, lines(lua))) <= 900
    assert not lua.globals().CLOSED


def test_logging_failure_does_not_change_capture():
    lua = build()
    lua.execute("Isaac.DebugString=function() error('no journal') end")
    tick(lua, 7)
    n = len(lines(lua))
    tick(lua, 10)
    assert len(lines(lua)) == n and live_snapshots(lua)[-1].status == "active"


@pytest.mark.parametrize("flag", ["io.stdout", "{}", "math.huge", "2^60"])
def test_non_scalar_or_unsafe_flags_are_unavailable_without_losing_trajectory(flag):
    lua = build_live(source_changes={"tear_diagnostics = false,": "tear_diagnostics = true,"})
    lua.execute(
        STUBS + f"ROOM_ENTITIES[2].TearFlags={flag}; "
        "TearFlags={TEAR_SPECTRAL={},TEAR_PIERCING={}}; "
        "ROOM_ENTITIES[2].HasTearFlags=function(self,flag) "
        "return flag==TearFlags.TEAR_SPECTRAL end"
    )
    hello(lua, LIVE_LOOP_CAPABILITIES)
    samples = [s for s in lines(lua) if "event=sample" in s]
    assert samples and "flags=na" in samples[0]
    assert "spectral=true piercing=false" in samples[0]
    assert not any("reason=error" in s for s in lines(lua))
