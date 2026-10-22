"""Simulated production Lua acquisition; native engine qualification is separate."""

import pytest
from test_lua_combat_navigation import GRID_STUBS, STUBS
from test_lua_firing_geometry import CAPS, FIRING_STUBS
from test_lua_live_loop import build_live, hello, live_snapshots, records

from isaac_threrisaifuture.firing_progress_v5 import nearest_patch


def world(extra="", *, opted=True):
    lua = build_live()
    lua.execute(
        STUBS
        + GRID_STUBS
        + FIRING_STUBS.replace("assert(mode==3 and", "assert((mode==3 or mode==0) and")
        + """
X,Y=70,410
BOUNDARY_QUERIES=0
local boundary_game=Game
Game=function()
 local g=boundary_game(); local room=g.GetRoom
 g.GetRoom=function(self)
  local r=room(self); local check=r.CheckLine
  r.CheckLine=function(self,a,b,mode,...)
   if mode==0 then
    BOUNDARY_QUERIES=BOUNDARY_QUERIES+1
    if BOUNDARY_ERROR then error('missing API') end
    if BOUNDARY_BLOCKED then return false,b end
   end
   return check(self,a,b,mode,...)
  end
  return r
 end
 return g
end
"""
        + extra
    )
    caps = (*CAPS, "firing_geometry_v1")
    hello(lua, (*caps, "firing_boundary_support_v1") if opted else caps)
    return lua


def test_one_extra_query_exact_patch_and_oracle_separation():
    lua = world()
    assert not lua.globals().CLOSED
    snap = live_snapshots(lua)[-1]
    support = snap.oracle.firing.boundary_support
    assert support.clear is True
    assert (support.patch, support.position) == nearest_patch(
        snap.oracle.navigation.grid, snap.entity_frame.player_position
    )
    assert support.source == snap.entity_frame.player_position
    assert lua.globals().BOUNDARY_QUERIES == len(live_snapshots(lua))
    assert lua.globals().QUERY_PEAK <= 33
    assert "boundary_support" not in snap.entity_frame.model_dump()


@pytest.mark.parametrize(
    "extra,expected", [("BOUNDARY_ERROR=true", None), ("BOUNDARY_BLOCKED=true", False)]
)
def test_failed_and_blocked_queries_are_explicit(extra, expected):
    lua = world(extra)
    assert live_snapshots(lua)[-1].oracle.firing.boundary_support.clear is expected


def test_off_and_unsupported_weapon_have_no_extra_query():
    for lua in (world(opted=False), world("WEAPON=2")):
        assert lua.globals().BOUNDARY_QUERIES == 0
        assert live_snapshots(lua)[-1].oracle.firing.boundary_support is None


def test_missing_firing_capability_refused():
    lua = build_live()
    hello(lua, (*CAPS, "firing_boundary_support_v1"))
    assert lua.globals().CLOSED and not records(lua, "hello_ack")


def test_fractional_source_matches_raw_snapshot_without_rounding():
    lua = world("X,Y=70.123456,410.987654")
    snap = live_snapshots(lua)[-1]
    assert snap.oracle.firing.boundary_support.source.x == snap.player.position.x == 70.123456
    assert snap.oracle.firing.boundary_support.source.y == snap.player.position.y == 410.987654
    assert snap.oracle.firing.boundary_support.source == snap.entity_frame.player_position
