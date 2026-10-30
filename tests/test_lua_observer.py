"""OFFLINE Lua 5.3 harness. Isaac, callbacks and sockets are simulated.

Run with test-only lupa.lua53 on PYTHONPATH and ISAAC_JSON_LUA pointing to the
installed game JSON source. This never loads the game or its socket DLL.
"""

import json
import os
import time
from pathlib import Path

import pytest

from isaac_threrisaifuture.observation import CAPABILITIES, HelloAck, Snapshot, decode

lupa = pytest.importorskip("lupa.lua53", reason="Optional isolated Lua 5.3 test runtime required")
JSON_PATH = os.environ.get("ISAAC_JSON_LUA")
if not JSON_PATH:
    pytest.skip(
        "Set ISAAC_JSON_LUA to test with the installed JSON decoder", allow_module_level=True
    )

ROOT = Path(__file__).resolve().parents[1]
STUBS = """
NOW, FRAME, X, Y = 0, 20, 100, 200
PAUSED, NO_PLAYER, FAIL_STATE = false, false, false
SOCKET_MISSING, CONNECT_MODE, BLOCK_OUTPUT = false, "ok", false
SEND_LIMIT, SEND_CALLS, READ_CALLS, CONNECT_CALLS = 64, 0, 0, 0
INCOMING, OUTGOING, CLOSED, LOGS = "", "", false, {}
PEER_CLOSED = false
IS_DEAD, AUTO_START, COMMAND_FAIL = false, false, false
PLAYER_COUNT = 1
COMMANDS = {}
-- Simulated inventory, held collectibles, room and level facts (not engine evidence).
COINS, BOMBS, KEYS, ACTIVE, CHARGE, MAX_CHARGES = 0, 0, 0, 0, 0, nil
CARD, PILL, TRINKET, HELD, HAS_CALLS, ITEM_SIZE = 0, 0, 0, {}, 0, 733
ROOM_TYPE, STAGE, STAGE_TYPE, ROOM_INDEX, DOORS = 1, 1, 0, 84, {}
CURSES = 0
-- DOORS[slot] is a bool (open) or { open, locked, type, target, lock_fault }; ROOM_DESCS maps a
-- room index to its descriptor (simulated, not engine evidence).
ROOM_DESCS = {}
-- Simulated room geometry and level map (not engine evidence). GetRooms is a RoomsList:
-- 0-based Get(i) and Size; each descriptor has GridIndex, VisitedCount, DisplayFlags, Data.
ROOM_SHAPE, GRID_W, GRID_H, MAP_ROOMS = 1, 15, 9, {}
function make_desc(grid, shape, rtype, visited, flags)
 return { GridIndex=grid, VisitedCount=visited, DisplayFlags=flags,
  Data=(rtype ~= nil) and { Type=rtype, Shape=shape } or nil }
end
ActiveSlot = { SLOT_PRIMARY = 0 }
-- Simulated stats, 128-bit tear flag sets and weapons (not engine evidence). A set is
-- {l, h} with & and ==, like Repentance BitSet128; TEAR_BOUNCE sits in the high word.
STAT_DAMAGE, STAT_FIRE_DELAY, STAT_RANGE, STAT_SHOT, STAT_MOVE, STAT_LUCK =
 3.5, 10, 260, 1, 1, 0
local bits_meta = {}
bits_meta.__band = function(a, b) return bit_set(a.l & b.l, a.h & b.h) end
bits_meta.__eq = function(a, b) return a.l == b.l and a.h == b.h end
function bit_set(l, h) return setmetatable({l=l, h=h}, bits_meta) end
TearFlags = { TEAR_NORMAL = bit_set(0, 0) }
for i, name in ipairs({ "SPECTRAL", "PIERCING", "HOMING", "SLOW", "POISON", "FREEZE",
 "SPLIT", "GROW", "BOOMERANG", "PERSISTENT", "WIGGLE", "EXPLOSIVE", "CHARM",
 "CONFUSION", "BURN" }) do TearFlags["TEAR_" .. name] = bit_set(1 << (i - 1), 0) end
TearFlags.TEAR_BOUNCE = bit_set(0, 1)
PLAYER_TEAR_FLAGS = bit_set(0, 0)
WeaponType = { WEAPON_TEARS=1, WEAPON_BRIMSTONE=2, WEAPON_LASER=3, WEAPON_KNIFE=4,
 WEAPON_BOMBS=5, WEAPON_ROCKETS=6, WEAPON_MONSTROS_LUNGS=7, WEAPON_LUDOVICO_TECHNIQUE=8,
 WEAPON_TECH_X=9, WEAPON_BONE=10, WEAPON_NOTCHED_AXE=11, WEAPON_URN_OF_SOULS=12,
 WEAPON_SPIRIT_SWORD=13, WEAPON_FETUS=14 }  -- UMBILICAL_WHIP missing: reads false
WEAPONS = { [1]=true }
-- Optional scripted callback order run inside a dispatch (simulated, not engine evidence).
DISPATCH_EVENTS = nil
-- Optional deferred order: {{after=ms, event=name}, ...} queued by a dispatch that returns
-- first; run_due() runs each later at its fake-clock time (simulated, not engine evidence).
DEFERRED_EVENTS, SCHEDULE = nil, {}
EntityType = { ENTITY_PLAYER=1 }
callbacks = {}
mod = { AddCallback = function(self, id, fn) callbacks[id] = fn end }
RegisterMod = function() return mod end
ModCallbacks = {
 MC_POST_RENDER="render", MC_POST_UPDATE="update", MC_POST_GAME_STARTED="start",
 MC_POST_GAME_END="game_end", MC_POST_NEW_ROOM="room",
 MC_PRE_GAME_EXIT="exit", MC_PRE_MOD_UNLOAD="unload",
 MC_INPUT_ACTION="input", MC_POST_NEW_LEVEL="level", MC_POST_FIRE_TEAR="tear",
 MC_ENTITY_TAKE_DMG="damage", MC_POST_NPC_INIT="npc_init", MC_NPC_UPDATE="npc_update",
 MC_POST_NPC_DEATH="npc_death", MC_POST_ENTITY_KILL="kill", MC_POST_ENTITY_REMOVE="remove",
 MC_PRE_SPAWN_CLEAN_AWARD="award"
}
print = function(message) LOGS[#LOGS+1] = message end
Isaac = { GetTime = function() return NOW end }
Isaac.GetItemConfig = function() return {
 GetCollectibles=function() return { Size=ITEM_SIZE } end,
 GetCollectible=function(self, id)
  -- ITEM_CONFIG(id) overrides the catalog entry (quality, type, charges, tags).
  if ITEM_CONFIG then return ITEM_CONFIG(id) end
  if MAX_CHARGES then return { MaxCharges=MAX_CHARGES } end
 end
} end
Isaac.ExecuteCommand = function(command)
 COMMANDS[#COMMANDS+1] = command
 if COMMAND_FAIL then error("Simulated dispatch fault") end
 if AUTO_START then callbacks.exit(); IS_DEAD=false; FRAME=0; callbacks.start(mod,false) end
 for _, event in ipairs(DISPATCH_EVENTS or {}) do run_event(event) end
 for _, e in ipairs(DEFERRED_EVENTS or {}) do
  SCHEDULE[#SCHEDULE+1] = {at=NOW+e.after, event=e.event}
 end
end
function run_due()
 while SCHEDULE[1] and SCHEDULE[1].at <= NOW do run_event(table.remove(SCHEDULE, 1).event) end
end
function run_event(event)
 if event=="exit" then callbacks.exit()
 elseif event=="start" then IS_DEAD=false; FRAME=0; callbacks.start(mod,false)
 elseif event=="continue" then callbacks.start(mod,true)
 elseif event=="disconnect" then PEER_CLOSED=true; NOW=NOW+1; callbacks.render()
 else error("Unknown scripted event") end
end
ButtonAction = { ACTION_LEFT=0, ACTION_RIGHT=1, ACTION_UP=2, ACTION_DOWN=3,
 ACTION_SHOOTLEFT=4, ACTION_SHOOTRIGHT=5, ACTION_SHOOTUP=6, ACTION_SHOOTDOWN=7,
 ACTION_ITEM=8, ACTION_PILLCARD=9, ACTION_BOMB=10 }
InputHook = { IS_ACTION_PRESSED=0, IS_ACTION_TRIGGERED=1, GET_ACTION_VALUE=2 }
GetPtrHash = function(entity) return entity end
local player = {
 HasWeaponType=function(self, kind) return WEAPONS[kind] == true end,
 GetPlayerType=function() return 0 end, GetHearts=function() return 5 end,
 GetMaxHearts=function() return 6 end, GetSoulHearts=function() return 2 end,
 IsDead=function() return IS_DEAD end,
 GetBoneHearts=function() return 1 end,
 GetNumCoins=function() return COINS end, GetNumBombs=function() return BOMBS end,
 GetNumKeys=function() return KEYS end, GetActiveItem=function() return ACTIVE end,
 GetActiveCharge=function() return CHARGE end, GetCard=function() return CARD end,
 GetPill=function() return PILL end, GetTrinket=function() return TRINKET end,
 HasCollectible=function(self, id, ignore) HAS_CALLS=HAS_CALLS+1; return HELD[id]==true end
}
player.ToPlayer = function(self) return self end
Isaac.GetPlayer = function()
 player.Damage, player.MaxFireDelay, player.TearRange = STAT_DAMAGE, STAT_FIRE_DELAY, STAT_RANGE
 player.ShotSpeed, player.MoveSpeed, player.Luck = STAT_SHOT, STAT_MOVE, STAT_LUCK
 player.TearFlags = PLAYER_TEAR_FLAGS
 if FAIL_STATE then error("Simulated game API fault") end
 if NO_PLAYER then return nil end
 player.Position = {X=X,Y=Y}
 return player
end
Game = function() return {
 GetNumPlayers=function() return NO_PLAYER and 0 or PLAYER_COUNT end,
 GetRoom=function() return {
  IsClear=function() return false end, GetType=function() return ROOM_TYPE end,
  GetRoomShape=function() return ROOM_SHAPE end,
  GetGridWidth=function() return GRID_W end, GetGridHeight=function() return GRID_H end,
  GetDoor=function(self, slot)
   local d = DOORS[slot]
   if d == nil then return nil end
   if type(d) ~= "table" then d = { open=d } end
   return { IsOpen=function() return d.open == true end,
    IsLocked=function() if d.lock_fault then error("lock fault") end return d.locked == true end,
    TargetRoomType=d.type, TargetRoomIndex=d.target }
  end
 } end,
 GetLevel=function() return {
  GetStage=function() return STAGE end, GetStageType=function() return STAGE_TYPE end,
  GetCurses=function() return CURSES end,
  GetCurrentRoomIndex=function() return ROOM_INDEX end,
  GetCurrentRoomDesc=function() return { GridIndex=ROOM_INDEX } end,
  GetRoomByIdx=function(self, index) return ROOM_DESCS[index] end,
  GetRooms=function() return {
   Size=#MAP_ROOMS, Get=function(self, i) return MAP_ROOMS[i+1] end } end
 } end,
 GetFrameCount=function() return FRAME end,
 IsPaused=function() return PAUSED end
} end
local tcp = {
 settimeout=function(self,t) assert(t==0); return 1 end,
 connect=function()
  CONNECT_CALLS=CONNECT_CALLS+1
  if CONNECT_MODE=="refused" then return nil,"refused" end
  if CONNECT_MODE=="pending" then return nil,"timeout" end
  return 1
 end,
 getpeername=function() if CONNECT_MODE=="ok" then return "127.0.0.1",9528 end end,
 receive=function(self,n)
  assert(n==4096); READ_CALLS=READ_CALLS+1
  if PEER_CLOSED then return nil,"closed","" end
  local chunk=INCOMING:sub(1,n)
  INCOMING=INCOMING:sub(n+1)
  return nil,"timeout",chunk
 end,
 send=function(self,data,first,last)
  SEND_CALLS=SEND_CALLS+1
  assert(last-first+1<=32768)
  if BLOCK_OUTPUT then return nil,"timeout",first-1 end
  local finish=math.min(last,first+SEND_LIMIT-1)
  OUTGOING=OUTGOING..data:sub(first,finish)
  if finish<last then return nil,"timeout",finish end
  return finish
 end,
 close=function() CLOSED=true end
}
package.preload["socket.core"] = function()
 if SOCKET_MISSING then error("No socket") end
 return { tcp=function() CLOSED=false; return tcp end }
end
"""


def build_lua(
    *,
    approved=False,
    approval_changes=None,
    source_changes=None,
):
    runtime = lupa.LuaRuntime(unpack_returned_tuples=True, max_memory=16 * 1024 * 1024)
    runtime.execute(STUBS)
    module = runtime.execute(Path(JSON_PATH).read_text(encoding="utf-8"))
    runtime.globals().json_module = module
    runtime.execute('package.preload["json"] = function() return json_module end')
    source = (ROOT / "mod/observer/main.lua").read_text(encoding="utf-8")
    if approved:
        approval = dict(
            profile_id="offline-only",
            profile_mode="isolated",
            expires_at=int(time.time()) + 600,
            profile_evidence="simulated",
            slot_evidence="simulated",
            runtime_authorization="offline-only",
            slot=2,
            game_epoch=1,
        )
        approval.update(approval_changes or {})
        fields = ",".join(f"{key}={json.dumps(value)}" for key, value in approval.items())
        source = source.replace(
            "action_authorization = nil,", "action_authorization = {" + fields + "},", 1
        )
    for old, new in (source_changes or {}).items():
        assert old in source, old
        source = source.replace(old, new, 1)
    runtime.execute(source)
    return runtime


@pytest.fixture
def lua():
    return build_lua()


def tick(lua, count=1, delta=20):
    for _ in range(count):
        lua.execute(f"NOW=NOW+{delta}; callbacks.render()")


def handshake(lua, session="a" * 32, *, restart=False, actions=False):
    tick(lua)
    request = {
        "type": "hello",
        "protocol_version": 1,
        "schema_version": 1,
        "session_id": session,
        "required_capabilities": list(CAPABILITIES)
        + (["death_restart_v1"] if restart else [])
        + (["safe_actions_v1"] if actions else []),
    }
    lua.globals().INCOMING = json.dumps(request, separators=(",", ":")) + "\n"
    tick(lua, 15)
    lines = lua.globals().OUTGOING.splitlines()
    return decode(lines[0].encode(), HelloAck)


def snapshots(lua):
    return [
        decode(line.encode(), Snapshot)
        for line in lua.globals().OUTGOING.split("\n")[:-1]
        if json.loads(line)["type"] == "snapshot"
    ]


def test_lua_partial_io_capture_pause_and_epoch(lua):
    lua.execute("callbacks.start(); callbacks.room()")
    hello = handshake(lua)
    assert hello.lua_version == "Lua 5.3"
    assert hello.game.version is None
    tick(lua, 35)
    first = snapshots(lua)[-1]
    assert first.player.health.bone_containers == 1
    assert first.player.health.red_half_hearts == 5
    assert first.player.position.x == 100
    lua.execute("X=150; FRAME=21; PAUSED=true; callbacks.update()")
    tick(lua, 35)
    second = snapshots(lua)[-1]
    assert second.status == "paused"
    assert second.player.position.x == 150
    assert second.sequence > first.sequence
    lua.execute("callbacks.start(); callbacks.room(); FRAME=0; PAUSED=false")
    tick(lua, 35)
    third = snapshots(lua)[-1]
    assert third.game_epoch == first.game_epoch + 1
    assert third.frame_id == 0
    assert not lua.globals().CLOSED


@pytest.mark.parametrize("flag", ["NO_PLAYER", "FAIL_STATE"])
def test_lua_unavailable_state(lua, flag):
    lua.execute(f"callbacks.start(); {flag}=true")
    handshake(lua)
    tick(lua, 35)
    snap = snapshots(lua)[-1]
    assert snap.status == "unavailable"
    assert snap.player is None and snap.frame_id is None and snap.room is None
    assert snap.reason == "state_read_failed"


def test_lua_menu_availability_and_cleanup(lua):
    handshake(lua)
    tick(lua, 35)
    assert snapshots(lua)[-1].reason == "not_in_game"
    lua.execute("callbacks.unload(mod,mod)")
    assert lua.globals().CLOSED


@pytest.mark.parametrize("mode", ["refused", "pending", "missing"])
def test_lua_absent_python_or_missing_module_has_bounded_work(lua, mode):
    if mode == "missing":
        lua.execute("SOCKET_MISSING=true")
    else:
        lua.globals().CONNECT_MODE = mode
    tick(lua, 1000, 1)
    assert lua.globals().CONNECT_CALLS <= 1
    assert lua.globals().READ_CALLS == 0
    assert lua.globals().SEND_CALLS == 0


@pytest.mark.parametrize(
    "data",
    [
        "x" * 16385,
        "{broken}\n",
        "{}\n",
        '{"type":"move"}\n',
        '{"type":"hello","type":"hello"}\n',
    ],
)
def test_lua_bad_peer_closes_without_waiting(lua, data):
    tick(lua)
    lua.globals().INCOMING = data
    tick(lua, 6)
    assert lua.globals().CLOSED
    assert lua.globals().READ_CALLS <= 5


def test_lua_trickle_handshake_and_slow_reader_expire(lua):
    tick(lua)
    lua.globals().INCOMING = "{"
    tick(lua)
    tick(lua, delta=3001)
    assert lua.globals().CLOSED
    # New connection, same original mod code, blocked output is bounded.
    tick(lua, delta=1001)
    lua.globals().BLOCK_OUTPUT = True
    request = {
        "type": "hello",
        "protocol_version": 1,
        "schema_version": 1,
        "session_id": "b" * 32,
        "required_capabilities": list(CAPABILITIES),
    }
    lua.globals().INCOMING = json.dumps(request, separators=(",", ":")) + "\n"
    tick(lua)
    assert not lua.globals().CLOSED
    tick(lua, delta=3001)
    assert lua.globals().CLOSED


def test_lua_forbids_post_handshake_requests(lua):
    handshake(lua)
    lua.globals().INCOMING = "x"
    tick(lua)
    assert lua.globals().CLOSED


def test_lua_fragmented_hello_and_reconnect(lua):
    tick(lua)
    request = {
        "type": "hello",
        "protocol_version": 1,
        "schema_version": 1,
        "session_id": "c" * 32,
        "required_capabilities": list(CAPABILITIES),
    }
    payload = json.dumps(request, separators=(",", ":")) + "\n"
    lua.globals().INCOMING = payload[:12]
    tick(lua)
    assert lua.globals().OUTGOING == ""
    lua.globals().INCOMING = payload[12:]
    tick(lua, 15)
    hello = decode(lua.globals().OUTGOING.splitlines()[0].encode(), HelloAck)
    assert hello.session_id == "c" * 32
    lua.execute("PEER_CLOSED=true")
    tick(lua)
    assert lua.globals().CLOSED
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    assert handshake(lua, "d" * 32).session_id != hello.session_id


def test_lua_game_exit_closes_peer(lua):
    handshake(lua)
    lua.execute("callbacks.exit()")
    assert lua.globals().CLOSED


def test_lua_runtime_fault_is_logged_and_peer_closed(lua):
    lua.execute("Isaac.DebugString=function(text) LOGS[#LOGS+1]=text end")
    handshake(lua)
    lua.execute('require("socket.core").tcp().receive=function() error(string.rep("x",1000)) end')
    lua.execute("callbacks.render()")
    assert lua.globals().CLOSED
    messages = list(lua.globals().LOGS.values())
    assert "Observer capability/protocol fault" in messages[-1]
    assert len(messages[-1]) <= 330


def arm_death(lua, *, restart=True):
    lua.execute("callbacks.start(mod,false)")
    handshake(lua, restart=restart)
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")


def commands(lua):
    return list(lua.globals().COMMANDS.values())


def test_death_restart_default_is_read_only(lua):
    arm_death(lua, restart=False)
    tick(lua, 100)
    assert commands(lua) == []


def test_death_restart_delayed_once_and_confirmed(lua):
    arm_death(lua)
    lua.execute("AUTO_START=true; callbacks.game_end(mod,true)")
    tick(lua, 74)
    assert commands(lua) == []
    tick(lua)
    assert commands(lua) == ["restart"]
    assert lua.globals().CLOSED  # own exit closes authority until fresh negotiation
    assert any("confirmed old_epoch=1 new_epoch=2" in x for x in lua.globals().LOGS.values())
    reconnect_restart(lua, "b" * 32)
    tick(lua, 30)
    assert snapshots(lua)[-1].game_epoch == 2


@pytest.mark.parametrize(
    "event",
    [
        "callbacks.game_end(mod,false)",
        "IS_DEAD=false",
        "callbacks.exit()",
        "PEER_CLOSED=true",
        "callbacks.start(mod,false)",
        "callbacks.unload(mod,mod)",
        "NO_PLAYER=true",
        "PLAYER_COUNT=2",
        "FAIL_STATE=true",
    ],
)
def test_death_restart_cancel_guards(lua, event):
    arm_death(lua)
    lua.execute(event)
    tick(lua, 100)
    assert commands(lua) == []


def test_death_restart_requires_future_event_and_full_ack(lua):
    lua.execute("callbacks.start(mod,false); IS_DEAD=true; callbacks.game_end(mod,true)")
    handshake(lua, restart=True)
    tick(lua, 100)
    assert commands(lua) == []  # attaching on an old death screen is inert


def test_death_restart_no_game_over_no_restart(lua):
    lua.execute("callbacks.start(mod,false)")
    handshake(lua, restart=True)
    lua.execute("IS_DEAD=true")
    tick(lua, 100)
    assert commands(lua) == []


@pytest.mark.parametrize("elapsed", [5001, 600001])
def test_death_restart_stale_or_expired(lua, elapsed):
    arm_death(lua)
    tick(lua, delta=elapsed)
    assert commands(lua) == []


@pytest.mark.parametrize("failure", ["COMMAND_FAIL=true", "AUTO_START=false"])
def test_death_restart_uncertain_result_disables_retry(lua, failure):
    arm_death(lua)
    lua.execute(failure)
    tick(lua, 100)
    tick(lua, delta=5001)
    lua.execute("callbacks.start(mod,false); callbacks.game_end(mod,true)")
    tick(lua, 100)
    assert commands(lua) == ["restart"]
    assert any("fault" in x and "disabled" in x for x in lua.globals().LOGS.values())


def reconnect_restart(lua, session):
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    handshake(lua, session, restart=True)


def test_death_restart_budget_survives_reconnect(lua):
    arm_death(lua)
    lua.execute("AUTO_START=true")
    for index in range(3):
        if index:
            reconnect_restart(lua, str(index) * 32)
            lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
        tick(lua, 80)
    assert commands(lua) == ["restart"] * 3
    reconnect_restart(lua, "f" * 32)
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, 100)
    assert len(commands(lua)) == 3


def test_death_restart_normal_exit_invalidates_profile_confirmation(lua):
    arm_death(lua)
    lua.execute("callbacks.exit(); callbacks.start(mod,false)")
    reconnect_restart(lua, "f" * 32)
    lua.execute("callbacks.game_end(mod,true)")
    tick(lua, 100)
    assert commands(lua) == []


def test_death_restart_lease_survives_reconnect(lua):
    arm_death(lua)
    lua.execute("PEER_CLOSED=true")
    tick(lua)
    tick(lua, delta=600001)
    reconnect_restart(lua, "f" * 32)
    lua.execute("callbacks.game_end(mod,true)")
    tick(lua, 100)
    assert commands(lua) == []


def test_death_restart_cannot_arm_on_partial_ack(lua):
    lua.execute("callbacks.start(mod,false); SEND_LIMIT=1")
    tick(lua)
    lua.globals().INCOMING = (
        json.dumps(
            {
                "type": "hello",
                "protocol_version": 1,
                "schema_version": 1,
                "session_id": "a" * 32,
                "required_capabilities": list(CAPABILITIES) + ["death_restart_v1"],
            },
            separators=(",", ":"),
        )
        + "\n"
    )
    tick(lua)
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true); SEND_LIMIT=4096")
    tick(lua, 100)
    assert commands(lua) == []


def test_death_restart_continued_game_is_not_confirmation(lua):
    arm_death(lua)
    tick(lua, 75)
    lua.execute("callbacks.start(mod,true); callbacks.game_end(mod,true)")
    tick(lua, 100)
    assert commands(lua) == ["restart"]
    assert any("unexpected game-start; disabled" in x for x in lua.globals().LOGS.values())
