"""Production Lua opt-in geometry with simulated APIs; not engine acceptance."""

import pytest
from test_lua_combat_navigation import GRID_STUBS, STUBS
from test_lua_live_loop import build_live, hello, live_snapshots, records

from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES

CAPS = (*LIVE_LOOP_CAPABILITIES, "combat_navigation_v1", "combat_navigation_grid_v2")
FIRING_STUBS = """
WeaponType={WEAPON_TEARS=1,NUM_WEAPON_TYPES=16}
TearFlags={TEAR_NORMAL=0}
WEAPON, LINE_CLEAR, VULNERABLE = 1,true,true
LINE_QUERIES, QUERY_PEAK, CURRENT_QUERIES=0,0,0
TEST_PLAYER.TearRange,TEST_PLAYER.TearFlags=260,0
TEST_PLAYER.HasWeaponType=function(self,kind) return kind==WEAPON end
ROOM_ENTITIES={make_enemy(1,400,280,10,10)}
ROOM_ENTITIES[1].IsVulnerableEnemy=function() return VULNERABLE end
local firing_game=Game
Game=function()
 local g=firing_game(); local get_room=g.GetRoom
 g.GetRoom=function(self)
  local r=get_room(self)
  local grid_size=r.GetGridSize
  r.GetGridSize=function(self) CURRENT_QUERIES=0; return grid_size(self) end
  r.CheckLine=function(self,a,b,mode,threshold,walls,crushable)
   assert(mode==3 and threshold==0 and walls==false and crushable==false)
   LINE_QUERIES=LINE_QUERIES+1
   CURRENT_QUERIES=CURRENT_QUERIES+1
   QUERY_PEAK=math.max(QUERY_PEAK,CURRENT_QUERIES)
   return LINE_CLEAR,b
  end
  return r
 end
 return g
end
"""


def world(extra="", *, opted=True):
    lua = build_live()
    lua.execute(STUBS + GRID_STUBS + FIRING_STUBS + extra)
    hello(lua, (*CAPS, "firing_geometry_v1") if opted else CAPS)
    return lua


def test_negotiated_projectile_queries_export_reward_only_geometry():
    lua = world()
    assert not lua.globals().CLOSED
    snapshot = live_snapshots(lua)[-1]
    firing = snapshot.oracle.firing
    assert firing.status == "plain_tears" and firing.tear_range == 260
    assert firing.target_vulnerable and firing.target_id is not None
    assert firing.clear_cells and len(firing.clear_cells) <= 32
    assert lua.globals().LINE_QUERIES > 0 and lua.globals().QUERY_PEAK <= 32
    assert "firing" not in snapshot.entity_frame.model_dump()
    assert "firing_geometry_v1" in records(lua, "hello_ack")[0]


def test_feature_off_preserves_capture_and_makes_no_line_queries():
    lua = world(opted=False)
    assert live_snapshots(lua)[-1].oracle.firing is None
    assert lua.globals().LINE_QUERIES == 0


@pytest.mark.parametrize(
    "extra,status",
    [
        ("WEAPON=2", "unsupported"),
        ("TEST_PLAYER.TearFlags=1", "unsupported"),
        ("TEST_PLAYER.HasWeaponType=nil", "unavailable"),
        ("TEST_PLAYER.HasWeaponType=function() error('API failed') end", "unavailable"),
        ("TEST_PLAYER.TearRange=0", "unavailable"),
    ],
)
def test_unknown_or_special_weapons_do_not_invent_firing_positions(extra, status):
    lua = world(extra)
    geometry = live_snapshots(lua)[-1].oracle.firing
    assert geometry.status == status and geometry.clear_cells == []
    assert lua.globals().LINE_QUERIES == 0


def test_blocked_line_and_invulnerable_enemy_offer_no_positive_candidates():
    for extra in ("LINE_CLEAR=false", "VULNERABLE=false"):
        lua = world(extra)
        assert live_snapshots(lua)[-1].oracle.firing.clear_cells == []


def test_query_cap_truncates_candidates_without_unbounded_work():
    lua = world("GRID_WIDTH,GRID_HEIGHT=32,32; TEST_PLAYER.TearRange=4000")
    geometry = live_snapshots(lua)[-1].oracle.firing
    assert lua.globals().QUERY_PEAK == 32
    assert geometry.candidate_overflow > 0 and len(geometry.clear_cells) == 32


def test_firing_request_without_measured_grid_is_rejected():
    lua = build_live()
    hello(lua, (*LIVE_LOOP_CAPABILITIES, "firing_geometry_v1"))
    assert lua.globals().CLOSED and not records(lua, "hello_ack")
