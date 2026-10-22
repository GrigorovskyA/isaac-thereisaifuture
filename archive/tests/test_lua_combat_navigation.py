"""Production Lua navigation negotiation/filtering with isolated Lua 5.3 stubs."""

import json

import pytest
from test_lua_live_loop import build_live, hello, live_snapshots, records
from test_lua_observer import tick

from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES

STUBS = """
RoomType={ROOM_DEFAULT=1}
DOORS={}
local base_game=Game
Game=function()
 local g=base_game()
 local base_room=g.GetRoom
 g.GetRoom=function(self)
  local r=base_room(self)
  r.GetDoor=function(self,i) return DOORS[i] end
  r.GetDoorSlotPosition=function(self,i) return {X=40+i*100,Y=280} end
  r.GetType=function() return 1 end
  r.GetRoomShape=function() return 1 end
  return r
 end
 g.GetLevel=function() return {
  GetCurrentRoomIndex=function() return 84 end,
  GetStage=function() return 1 end,
  GetStageType=function() return 0 end } end
 return g
end
function door(open,locked,kind)
 return {IsOpen=function() return open end,IsLocked=function() return locked end,
         TargetRoomType=kind}
end
"""

GRID_STUBS = """
Vector=function(x,y) return {X=x,Y=y} end
NAV_SHAPE, GRID_WIDTH, GRID_HEIGHT = 1,15,9
NAV_BLOCKED={}
GridEntityType.GRID_SPIKES=8
local nav_base=Game
Game=function()
 local g=nav_base(); local get_room=g.GetRoom
 g.GetRoom=function(self)
  local r=get_room(self)
  r.GetRoomShape=function() return NAV_SHAPE end
  r.GetGridSize=function() return GRID_WIDTH*GRID_HEIGHT end
  r.GetGridWidth=function() return GRID_WIDTH end
  r.GetGridPosition=function(self,i)
   return Vector(40+(i%GRID_WIDTH)*40,120+math.floor(i/GRID_WIDTH)*40)
  end
  r.GetGridPath=function(self,i) return NAV_BLOCKED[i] and 1000 or 0 end
  r.GetGridCollisionAtPos=function(self,p) return 0 end
  r.IsPositionInRoom=function(self,p,margin)
   local x,y=(p.X-40)/40,(p.Y-120)/40
   if x<1 or x>GRID_WIDTH-2 or y<1 or y>GRID_HEIGHT-2 then return false end
   if (NAV_SHAPE==2 or NAV_SHAPE==7) and (y<3 or y>5) then return false end
   if (NAV_SHAPE==3 or NAV_SHAPE==5) and (x<6 or x>8) then return false end
   if NAV_SHAPE>=9 then
    local left=NAV_SHAPE==9 or NAV_SHAPE==11
    local top=NAV_SHAPE==9 or NAV_SHAPE==10
    if (x<GRID_WIDTH/2)==left and (y<GRID_HEIGHT/2)==top then return false end
   end
   return true
  end
  return r
 end
 return g
end
"""


def test_lua_emits_only_open_unlocked_ordinary_doors_when_negotiated():
    lua = build_live()
    lua.execute(STUBS)
    lua.execute(
        "DOORS={[0]=door(true,false,1),[1]=door(false,false,1),"
        "[2]=door(true,true,1),[3]=door(true,false,5)}"
    )
    hello(lua, (*LIVE_LOOP_CAPABILITIES, "combat_navigation_v1"))
    sample = live_snapshots(lua)[-1]
    nav = sample.oracle.navigation
    assert nav.room_index == 84 and nav.shape == 1
    assert [door.slot for door in nav.doors] == [0]
    assert nav.doors[0].position.x == 40
    assert "navigation" not in sample.entity_frame.model_dump()


def test_lua_default_live_oracle_unchanged_and_navigation_requires_live():
    lua = build_live()
    hello(lua, LIVE_LOOP_CAPABILITIES)
    raw = json.loads(records(lua, "snapshot")[-1])
    assert "navigation" not in raw["oracle"]
    other = build_live()
    hello(other, ["combat_navigation_v1"])
    assert other.globals().CLOSED and not records(other, "hello_ack")


def test_lua_missing_navigation_api_fails_closed_without_partial_data():
    lua = build_live()
    hello(lua, (*LIVE_LOOP_CAPABILITIES, "combat_navigation_v1"))
    tick(lua, 10)
    raw = json.loads(records(lua, "snapshot")[-1])
    assert raw["status"] == "unavailable" and raw["oracle"] is None


@pytest.mark.parametrize("shape", range(1, 13))
def test_production_lua_measures_each_shape_with_v2_only(shape):
    lua = build_live()
    lua.execute(STUBS)
    lua.execute(GRID_STUBS)
    width = 15 if shape <= 5 else 28
    height = 9 if shape <= 3 or shape in (6, 7) else 16
    lua.execute(
        f"NAV_SHAPE={shape};GRID_WIDTH={width};GRID_HEIGHT={height};"
        f"GRID_SIZE={width * height};DOORS={{[2]=door(true,false,1)}}"
    )
    hello(lua, (*LIVE_LOOP_CAPABILITIES, "combat_navigation_v1", "combat_navigation_grid_v2"))
    nav = live_snapshots(lua)[-1].oracle.navigation
    assert nav.version == 2 and nav.shape == shape
    assert nav.grid.width == width and nav.grid.height == height
    assert len(nav.grid.walkable) == width * height and "1" in nav.grid.walkable
    assert nav.grid.walkable[0] == "0"
    if shape >= 9:
        x = 2 if shape in (9, 11) else width - 3
        y = 2 if shape in (9, 10) else height - 3
        assert nav.grid.walkable[y * width + x] == "0"


def test_grid_hazards_and_closed_cells_never_become_walkable():
    lua = build_live()
    lua.execute(STUBS)
    lua.execute(GRID_STUBS)
    lua.execute("GRID_SIZE=135;NAV_BLOCKED[40]=true;GRID_ENTITIES[41]=make_grid(8,0,0,0)")
    hello(lua, (*LIVE_LOOP_CAPABILITIES, "combat_navigation_v1", "combat_navigation_grid_v2"))
    grid = live_snapshots(lua)[-1].oracle.navigation.grid
    assert grid.walkable[40:42] == "00"


def test_grid_capability_requires_v1_and_missing_api_is_unavailable():
    lua = build_live()
    hello(lua, (*LIVE_LOOP_CAPABILITIES, "combat_navigation_grid_v2"))
    assert lua.globals().CLOSED and not records(lua, "hello_ack")
    lua = build_live()
    lua.execute(STUBS)
    hello(lua, (*LIVE_LOOP_CAPABILITIES, "combat_navigation_v1", "combat_navigation_grid_v2"))
    assert json.loads(records(lua, "snapshot")[-1])["status"] == "unavailable"
