"""Production Lua in a simulated room, using the installed JSON codec only."""

import json

import pytest
from test_lua_observer import build_lua, handshake, snapshots, tick

from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.entities import EntitySnapshot
from isaac_threrisaifuture.observation import CAPABILITIES, decode

STUBS = """
EntityType={ ENTITY_PLAYER=1, ENTITY_TEAR=2, ENTITY_FAMILIAR=3, ENTITY_BOMB=4,
 ENTITY_PICKUP=5, ENTITY_LASER=7, ENTITY_KNIFE=8, ENTITY_PROJECTILE=9 }
GridEntityType={ GRID_ROCK=2, GRID_WALL=15, GRID_DOOR=16 }
ROOM_ENTITIES, GRID_ENTITIES = {}, {}
GRID_SIZE, SCANS, GRID_SCANS = 3, 0, 0
function make_entity(id, x, y, kind, visible)
 return { Index=id, InitSeed=id+5000, Type=kind, Visible=visible~=false,
  Variant=10, SubType=1, Price=0, FrameCount=0,
  ToPickup=function(self) if kind==5 then return self end end,
  Position={X=x,Y=y}, Velocity={X=2,Y=-1},
  Exists=function() return true end, IsDead=function() return false end,
  IsActiveEnemy=function() return kind==10 end }
end
function make_grid(kind, x, y, collision)
 return { CollisionClass=collision or 1, Position={X=x,Y=y},
  GetType=function() return kind end }
end
Isaac.GetRoomEntities=function() SCANS=SCANS+1; return ROOM_ENTITIES end
local base_game=Game
Game=function()
 local game=base_game()
 local base_room=game.GetRoom
 game.GetRoom=function(self)
  local room=base_room(self)
  room.GetGridSize=function() return GRID_SIZE end
  room.GetGridEntity=function(self,i) GRID_SCANS=GRID_SCANS+1; return GRID_ENTITIES[i] end
  return room
 end
 return game
end
"""


def connect(lua, session="a" * 32, extra=None):
    tick(lua)
    payload = {
        "type": "hello",
        "protocol_version": 1,
        "schema_version": 1,
        "session_id": session,
        "required_capabilities": list(CAPABILITIES) + ["entity_observation_v1"] + (extra or []),
    }
    lua.globals().INCOMING = json.dumps(payload, separators=(",", ":")) + "\n"
    tick(lua, 30)


def frames(lua):
    return [
        decode(line.encode(), EntitySnapshot)
        for line in lua.globals().OUTGOING.split("\n")[:-1]  # skip a partly sent record
        if json.loads(line)["type"] == "snapshot"
    ]


@pytest.fixture
def room():
    lua = build_lua()
    lua.execute(STUBS)
    lua.execute("callbacks.start(); SEND_LIMIT=4096")
    return lua


def test_native_entity_offsets_visibility_unknown_hp_and_grid_filter(room):
    room.execute("""
      ROOM_ENTITIES={ make_entity(1,101,200,10), make_entity(2,40,30,9),
        make_entity(3,0,0,10,false), make_entity(4,105,205,5) }
      GRID_ENTITIES[0]=make_grid(2,120,200)
      GRID_ENTITIES[1]=make_grid(16,140,200)
      GRID_ENTITIES[2]=make_grid(2,160,200,0)
    """)
    connect(room)
    sample = frames(room)[-1]
    state = sample.entity_frame
    assert state is not None
    assert [e.kind for e in state.entities] == ["enemy", "projectile", "obstacle", "pickup"]
    assert state.entities[0].position.x == 1 and state.entities[0].position.y == 0
    assert state.entities[0].velocity.x == 2
    assert all(e.hp is None and e.max_hp is None for e in state.entities)
    assert encode(state).overflow == {}
    assert "InitSeed" not in state.model_dump_json()


def test_default_observation_never_scans_entities(room):
    handshake(room)
    tick(room, 30)
    assert snapshots(room)[-1].status == "active"
    assert room.globals().SCANS == room.globals().GRID_SCANS == 0


def test_source_overflow_selects_nearest_and_counts_dropped_entities(room):
    room.execute("for i=1,30 do ROOM_ENTITIES[i]=make_entity(i,100+i,200,10) end")
    connect(room)
    state = frames(room)[-1].entity_frame
    assert len(state.entities) == 12
    assert state.source_overflow == {"enemy": 18}
    assert [e.position.x for e in state.entities] == list(range(1, 13))
    assert encode(state).overflow == {"enemy": 18}


def test_identity_survives_sampling_and_hidden_interval_but_not_reused_lifetime(room):
    room.execute("ROOM_ENTITIES={make_entity(1,101,200,10)}")
    connect(room)
    original = frames(room)[-1].entity_frame.entities[0].entity_id
    tick(room, 20)
    assert frames(room)[-1].entity_frame.entities[0].entity_id == original
    room.execute("ROOM_ENTITIES[1].Visible=false")
    tick(room, 20)
    assert frames(room)[-1].entity_frame.entities == []
    room.execute("ROOM_ENTITIES[1].Visible=true")
    tick(room, 20)
    assert frames(room)[-1].entity_frame.entities[0].entity_id == original
    room.execute("ROOM_ENTITIES[1].InitSeed=999")
    tick(room, 20)
    assert frames(room)[-1].entity_frame.entities[0].entity_id > original


def test_room_change_and_reconnect_do_not_reuse_old_identity(room):
    room.execute("ROOM_ENTITIES={make_entity(1,101,200,10)}")
    connect(room)
    first = frames(room)[-1].entity_frame
    room.execute("callbacks.room(); FRAME=FRAME+1")
    tick(room, 20)
    second = frames(room)[-1].entity_frame
    assert second.room_visit > first.room_visit
    assert second.entities[0].entity_id > first.entities[0].entity_id
    room.execute("PEER_CLOSED=true")
    tick(room)
    room.execute('PEER_CLOSED=false; OUTGOING=""; NOW=NOW+1001')
    connect(room, "b" * 32)
    third = frames(room)[-1].entity_frame
    assert third.session_id != second.session_id
    assert third.entities[0].entity_id == second.entities[0].entity_id


@pytest.mark.parametrize(
    "change",
    [
        "GRID_SIZE=2049",
        "GRID_SIZE=-1",
        "GRID_SIZE=1.5",
        "ROOM_ENTITIES={make_entity(1,0/0,200,10)}",
        "for i=1,1025 do ROOM_ENTITIES[i]=make_entity(i,101,200,10) end",
        "Isaac.GetRoomEntities=function() error('injected read fault') end",
    ],
)
def test_entity_capture_fault_never_returns_partial_state(room, change):
    room.execute(change)
    connect(room)
    snap = frames(room)[-1]
    assert snap.status == "unavailable" and snap.entity_frame is None
    assert snap.reason == "state_read_failed"


def test_empty_arrays_use_codec_array_marker(room):
    connect(room)
    state = frames(room)[-1].entity_frame
    assert state.entities == [] and state.source_overflow == {}


def test_mixed_capacity_frame_fits_existing_wire_limit(room):
    room.execute("""
      GRID_SIZE=30
      for i=1,30 do
        ROOM_ENTITIES[#ROOM_ENTITIES+1]=make_entity(i,100+i,200,10)
        ROOM_ENTITIES[#ROOM_ENTITIES+1]=make_entity(i+30,100+i,200,9)
        ROOM_ENTITIES[#ROOM_ENTITIES+1]=make_entity(i+60,100+i,200,5)
        GRID_ENTITIES[i-1]=make_grid(2,100+i,200)
      end
    """)
    connect(room)
    tick(room, 20)
    state = frames(room)[-1].entity_frame
    assert len(state.entities) == 52
    assert state.source_overflow == {"enemy": 18, "projectile": 10, "obstacle": 18, "pickup": 22}
    assert max(len(line.encode()) for line in room.globals().OUTGOING.split("\n")[:-1]) <= 32768


@pytest.mark.parametrize("extra", [["death_restart_v1"], ["safe_actions_v1"]])
def test_entity_mode_cannot_arm_control(room, extra):
    connect(room, extra=extra)
    assert room.globals().CLOSED
    assert len(room.globals().COMMANDS) == 0


def latest(lua):
    return frames(lua)[-1].entity_frame


def test_inventory_room_and_pickup_facts_are_read_and_clamped(room):
    room.execute("""
      ROOM_ENTITIES={ make_entity(1,101,200,5), make_entity(2,110,200,10) }
      ROOM_ENTITIES[1].Variant, ROOM_ENTITIES[1].SubType = 100, 500
      ROOM_ENTITIES[1].Price = 15
      COINS, BOMBS, KEYS = 1500, 3, 0
      ACTIVE, CHARGE, MAX_CHARGES = 33, 40, 6
      CARD, PILL, TRINKET = 5, 2, 7
      ROOM_TYPE, STAGE, STAGE_TYPE = 5, 3, 1
      DOORS[0], DOORS[1], DOORS[4] = true, false, true
    """)
    connect(room)
    state = latest(room)
    pickup, enemy = state.entities[1], state.entities[0]
    assert (pickup.kind, pickup.variant, pickup.subtype, pickup.price) == ("pickup", 100, 500, 15)
    assert (enemy.variant, enemy.subtype, enemy.price) == (None, None, None)
    inv = state.inventory
    assert (inv.coins, inv.bombs, inv.keys) == (999, 3, 0)  # coins clamp to the wire range
    assert (inv.active_item, inv.active_charge, inv.active_max_charge) == (33, 24, 6)
    assert (inv.card, inv.pill, inv.trinket) == (5, 2, 7)
    assert (state.room.type, state.room.stage, state.room.stage_type) == (5, 3, 1)
    assert state.room.doors == [True, False, False, False, True, False, False, False]


def test_missing_item_config_and_no_active_item_read_as_zero_charge(room):
    room.execute("ACTIVE, CHARGE = 33, 4")  # MAX_CHARGES stays nil: no item config entry
    connect(room)
    inv = latest(room).inventory
    assert (inv.active_item, inv.active_charge, inv.active_max_charge) == (33, 4, 0)
    room.execute("ACTIVE, CHARGE, MAX_CHARGES = 0, 9, 6")
    tick(room, 20)
    inv = latest(room).inventory
    assert (inv.active_item, inv.active_charge, inv.active_max_charge) == (0, 0, 0)


def test_collectibles_are_cached_and_recomputed_only_on_cadence_or_room_change(room):
    room.execute("HELD[5]=true; FRAME=100")
    connect(room)
    assert latest(room).collectibles == [5]
    scans = room.globals().HAS_CALLS
    assert scans == 732  # every ID up to the item config size, once
    room.execute("HELD[7]=true; FRAME=129")
    tick(room, 20)  # more snapshots, same cached list
    assert latest(room).collectibles == [5] and room.globals().HAS_CALLS == scans
    room.execute("FRAME=130")  # 30 frames after the last scan
    tick(room, 20)
    assert latest(room).collectibles == [5, 7] and room.globals().HAS_CALLS == 2 * scans
    room.execute("HELD[9]=true; callbacks.room(); FRAME=131")
    tick(room, 20)  # room change forces a rescan
    assert latest(room).collectibles == [5, 7, 9] and room.globals().HAS_CALLS == 3 * scans
    room.execute("HELD[11]=true; callbacks.start(); FRAME=132")
    tick(room, 20)  # so does a game start
    assert latest(room).collectibles == [5, 7, 9, 11]
    assert room.globals().HAS_CALLS == 4 * scans
    room.execute("HELD[13]=true; FRAME=10")  # frame counter went backwards: new run
    tick(room, 20)
    assert latest(room).collectibles == [5, 7, 9, 11, 13]
    assert room.globals().HAS_CALLS == 5 * scans


def test_collectible_scan_is_capped_by_id_range_and_count(room):
    room.execute("ITEM_SIZE=5000; for i=1,300 do HELD[i]=true end; HELD[1025]=true")
    connect(room)
    state = latest(room)
    assert state.collectibles == list(range(1, 257)) and state.collectible_overflow == 44
    assert room.globals().HAS_CALLS == 1024  # never scans past ID 1024


def test_empty_collectibles_use_the_array_marker(room):
    connect(room)
    state = latest(room)
    assert state.collectibles == [] and state.collectible_overflow == 0
    assert '"collectibles":[]' in room.globals().OUTGOING


def fill_worst_case(lua):
    """Every capacity full, widest numbers, 256 four-digit collectible IDs."""
    lua.execute("""
      GRID_SIZE=30; ITEM_SIZE=1025
      for i=769,1024 do HELD[i]=true end
      for i=1,30 do
        for n, kind in ipairs({10, 9, 5}) do
          local e=make_entity(i+30*n,-700.123+i,-600.456,kind)
          e.Velocity, e.Variant, e.SubType, e.Price = {X=-12.345,Y=-12.345}, 1023, 1024, -999
          ROOM_ENTITIES[#ROOM_ENTITIES+1]=e
        end
        GRID_ENTITIES[i-1]=make_grid(2,-700.123+i,-600.456)
      end
      COINS, BOMBS, KEYS, ACTIVE, CHARGE, MAX_CHARGES = 999, 999, 999, 1024, 24, 24
      CARD, PILL, TRINKET, ROOM_TYPE, STAGE, STAGE_TYPE = 65535, 65535, 65535, 31, 15, 7
      -- Own attacks and bombs overfill their caps; every flag and weapon on; widest stats.
      for i=1,20 do
        local a=make_entity(200+i,-700.123+i,-600.456,2)
        a.SpawnerType, a.Velocity = 1, {X=-12.345,Y=-12.345}
        ROOM_ENTITIES[#ROOM_ENTITIES+1]=a
      end
      for i=1,6 do
        local b=make_entity(300+i,-700.123+i,-600.456,4)
        b.FrameCount, b.Velocity = 99999, {X=-12.345,Y=-12.345}
        ROOM_ENTITIES[#ROOM_ENTITIES+1]=b
      end
      STAT_DAMAGE, STAT_FIRE_DELAY, STAT_RANGE = -999.123, -1, 99999.987
      STAT_SHOT, STAT_MOVE, STAT_LUCK = -9.999, 9.999, -99.999
      PLAYER_TEAR_FLAGS = bit_set(0xFFFF, 1)
      for _, kind in pairs(WeaponType) do WEAPONS[kind] = true end
    """)


def test_maximal_snapshot_stays_below_the_wire_limit(room):
    fill_worst_case(room)
    connect(room)
    tick(room, 20)
    state = latest(room)
    assert len(state.collectibles) == 256 and len(state.entities) == 72
    kinds = [e.kind for e in state.entities]
    assert (kinds.count("own_attack"), kinds.count("bomb")) == (16, 4)
    assert state.source_overflow["own_attack"] == 4 and state.source_overflow["bomb"] == 2
    sizes = [len(line.encode()) for line in room.globals().OUTGOING.split("\n")[:-1]]
    print("worst-case lua snapshot bytes:", max(sizes))
    assert sizes and max(sizes) < 32768


def test_stats_are_read_derived_and_clamped(room):
    room.execute("STAT_DAMAGE, STAT_FIRE_DELAY, STAT_RANGE = 7.25, 9, 300")
    room.execute("STAT_SHOT, STAT_MOVE, STAT_LUCK = 1.5, 1.2, 3")
    connect(room)
    stats = latest(room).stats
    assert (stats.damage, stats.tears_per_second, stats.range) == (7.25, 3.0, 300.0)
    assert (stats.shot_speed, stats.move_speed, stats.luck) == (1.5, 1.2, 3.0)
    room.execute("STAT_DAMAGE, STAT_FIRE_DELAY, STAT_RANGE = 5000, -1, -5")
    room.execute("STAT_SHOT, STAT_MOVE, STAT_LUCK = 99, -4, -500")
    tick(room, 20)
    stats = latest(room).stats
    assert (stats.damage, stats.tears_per_second, stats.range) == (1000.0, 60.0, 0.0)
    assert (stats.shot_speed, stats.move_speed, stats.luck) == (10.0, 0.0, -100.0)


def test_tear_flags_follow_the_set_bits_in_fixed_order(room):
    connect(room)
    assert latest(room).tear_flags == [False] * 16
    # Spectral, piercing and (high word) bounce.
    room.execute("PLAYER_TEAR_FLAGS = bit_set(0x3, 1)")
    tick(room, 20)
    flags = latest(room).tear_flags
    assert [i for i, on in enumerate(flags) if on] == [0, 1, 15]
    room.execute("TearFlags.TEAR_HOMING = nil")  # a missing enum entry reads false
    room.execute("PLAYER_TEAR_FLAGS = bit_set(0xFFFF, 1)")
    tick(room, 20)
    flags = latest(room).tear_flags
    assert flags[2] is False and sum(flags) == 15


def test_tear_flag_api_faults_read_false(room):
    room.execute("PLAYER_TEAR_FLAGS = 5")  # not a set: the & fails inside pcall
    connect(room)
    assert latest(room).tear_flags == [False] * 16
    assert not room.globals().CLOSED


def test_weapons_follow_has_weapon_type_and_missing_enum_is_false(room):
    room.execute("WEAPONS = { [2]=true, [14]=true }")  # brimstone, fetus
    connect(room)
    weapons = latest(room).weapons
    assert [i for i, on in enumerate(weapons) if on] == [1, 13] and len(weapons) == 15
    room.execute("for _, kind in pairs(WeaponType) do WEAPONS[kind]=true end")
    tick(room, 20)
    weapons = latest(room).weapons
    assert weapons[:14] == [True] * 14 and weapons[14] is False  # umbilical whip not in enum


def test_own_attacks_are_told_apart_from_enemy_projectiles(room):
    room.execute("""
      local mine = make_entity(1,110,200,2); mine.SpawnerType = 1
      local familiar = make_entity(2,120,200,7); familiar.SpawnerType = 3
      local child = make_entity(3,130,200,8); child.Parent = Isaac.GetPlayer(0)
      local hostile = make_entity(4,140,200,2); hostile.SpawnerType = 10
      local unowned = make_entity(5,150,200,2)
      local shot = make_entity(6,160,200,9); shot.SpawnerType = 10
      ROOM_ENTITIES = { mine, familiar, child, hostile, unowned, shot }
    """)
    connect(room)
    by_id = {(e.kind, e.position.x): e for e in latest(room).entities}
    assert sorted(x for kind, x in by_id if kind == "own_attack") == [10, 20, 30]
    assert [x for kind, x in by_id if kind == "projectile"] == [60]
    assert len(by_id) == 4  # the other player's or monster's tears are not reported


def test_bombs_carry_a_growing_clamped_age_and_are_not_pickups(room):
    room.execute("""
      BOMB = make_entity(1,110,200,4); BOMB.FrameCount = 5
      ROOM_ENTITIES = { BOMB, make_entity(2,150,200,5) }
      ROOM_ENTITIES[2].Variant = 40
    """)
    connect(room)
    bomb = [e for e in latest(room).entities if e.kind == "bomb"][0]
    assert (bomb.age_frames, bomb.variant) == (5, None)
    assert [e.kind for e in latest(room).entities].count("pickup") == 1
    room.execute("BOMB.FrameCount = 35")
    tick(room, 20)
    assert [e.age_frames for e in latest(room).entities if e.kind == "bomb"] == [35]
    room.execute("BOMB.FrameCount = 123456")
    tick(room, 20)
    assert [e.age_frames for e in latest(room).entities if e.kind == "bomb"] == [10000]


def test_own_attack_and_bomb_caps_keep_the_nearest_and_count_overflow(room):
    room.execute("""
      for i=1,20 do
        local a = make_entity(i,100+i*10,200,2); a.SpawnerType = 1
        ROOM_ENTITIES[#ROOM_ENTITIES+1] = a
      end
      for i=1,6 do
        local b = make_entity(100+i,100+i*10,200,4)
        ROOM_ENTITIES[#ROOM_ENTITIES+1] = b
      end
    """)
    connect(room)
    state = latest(room)
    own = [e.position.x for e in state.entities if e.kind == "own_attack"]
    bombs = [e.position.x for e in state.entities if e.kind == "bomb"]
    assert own == [10.0 * i for i in range(1, 17)] and bombs == [10.0, 20.0, 30.0, 40.0]
    assert state.source_overflow == {"own_attack": 4, "bomb": 2}


def test_lua_frame_encodes_stats_flags_and_weapons_into_the_vector(room):
    from isaac_threrisaifuture.encoding import STATS_OFFSET, TEAR_FLAG_OFFSET, WEAPON_OFFSET

    room.execute("PLAYER_TEAR_FLAGS = bit_set(1, 0); STAT_DAMAGE = 25")
    connect(room)
    vector = encode(latest(room)).vector
    assert vector[STATS_OFFSET] == pytest.approx(0.5)
    assert vector[TEAR_FLAG_OFFSET] == 1.0 and vector[TEAR_FLAG_OFFSET + 1] == 0.0
    assert vector[WEAPON_OFFSET] == 1.0
