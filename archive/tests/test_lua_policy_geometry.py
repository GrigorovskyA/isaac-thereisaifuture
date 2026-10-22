"""Observable probes in production Lua with simulated APIs, not native acceptance."""

import pytest
from test_lua_combat_navigation import GRID_STUBS, STUBS
from test_lua_firing_geometry import FIRING_STUBS
from test_lua_live_loop import build_live, hello, live_snapshots

from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES


def world(extra="", opted=True):
    lua = build_live()
    stubs = FIRING_STUBS.replace("mode==3 and", "(mode==0 or mode==3) and")
    lua.execute(STUBS + GRID_STUBS + stubs + "\nTEST_PLAYER.CanFly=false\n" + extra)
    hello(lua, (*LIVE_LOOP_CAPABILITIES, "combat_geometry_v2") if opted else LIVE_LOOP_CAPABILITIES)
    return lua


def test_explicit_blocked_probes_and_known_range_without_reward_oracle_geometry():
    lua = world("LINE_CLEAR=false")
    snap = live_snapshots(lua)[-1]
    assert snap.combat_geometry.tear_range == 260
    assert snap.combat_geometry.movement == [False] * 4
    assert all(e.clear is False for e in snap.combat_geometry.enemies)
    assert snap.oracle.firing is None
    assert lua.globals().QUERY_PEAK <= 16


def test_default_mode_has_no_new_queries_and_unknown_weapon_does_not_guess():
    lua = world(opted=False)
    assert live_snapshots(lua)[-1].combat_geometry is None
    assert lua.globals().LINE_QUERIES == 0

    lua = world("WEAPON=2\nTEST_PLAYER.CanFly=true")
    data = live_snapshots(lua)[-1].combat_geometry
    assert data.weapon == "unsupported" and data.tear_range is None
    assert data.movement == [None] * 4
    assert all(e.clear is None for e in data.enemies)
    assert lua.globals().LINE_QUERIES == 0


@pytest.mark.parametrize(
    "api", ["nil", "function() error('missing API') end", "function() return 1 end"]
)
def test_absent_failed_or_nonboolean_line_api_is_unknown(api):
    lua = world(
        "local geometry_game=Game\n"
        "Game=function() local g=geometry_game(); local get_room=g.GetRoom\n"
        "g.GetRoom=function(self) local r=get_room(self); r.CheckLine="
        + api
        + "; return r end; return g end"
    )
    data = live_snapshots(lua)[-1].combat_geometry
    assert data.tear_range == 260
    assert data.movement == [None] * 4
    assert all(e.clear is None for e in data.enemies)
