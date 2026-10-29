"""Production Lua, observation schema 8: floor features, interactables, door facts, caps."""

import pytest
from test_lua_entities import STUBS, connect, frames
from test_lua_observer import build_lua, tick


@pytest.fixture
def room():
    lua = build_lua()
    lua.execute(STUBS)
    lua.execute("callbacks.start(); SEND_LIMIT=4096")
    return lua


def latest(lua):
    return frames(lua)[-1].entity_frame


def by_class(state, field="obstacle_class"):
    return sorted(getattr(e, field) for e in state.entities if getattr(e, field) is not None)


# --- grid classes ----------------------------------------------------------------------


def test_floor_features_are_exported_without_collision_and_broken_rocks_are_not(room):
    room.execute("""
      -- trapdoor, crawlspace, pressure plate and teleporter have no collision; lock is solid
      GRID_ENTITIES[interior(0)] = make_grid(30, 10, 0, 0)
      GRID_ENTITIES[interior(1)] = make_grid(31, 20, 0, 0)
      GRID_ENTITIES[interior(2)] = make_grid(32, 30, 0, 0)
      GRID_ENTITIES[interior(3)] = make_grid(33, 40, 0, 1)
      GRID_ENTITIES[interior(4)] = make_grid(34, 50, 0, 0)
      GRID_ENTITIES[interior(5)] = make_grid(2, 60, 0, 0)    -- a broken rock: still dropped
      GRID_ENTITIES[interior(6)] = make_grid(7, 70, 0, 0)    -- so is a pit without collision
    """)
    connect(room)
    assert by_class(latest(room)) == sorted(
        ["trapdoor", "crawlspace", "pressure_plate", "lock_block", "teleporter"]
    )


def test_a_trapdoor_in_the_room_middle_is_found_but_the_border_ring_is_still_skipped(room):
    room.execute("""
      GRID_ENTITIES[4*15+7] = make_grid(30, 320, 280, 0)   -- room center
      GRID_ENTITIES[0] = make_grid(30, 0, 0, 0)            -- outer ring corner
      GRID_ENTITIES[15*8+3] = make_grid(32, 0, 0, 0)       -- outer ring bottom row
    """)
    connect(room)
    assert by_class(latest(room)) == ["trapdoor"]


def test_missing_new_grid_names_are_skipped_like_other_missing_names(room):
    room.execute("""
      GridEntityType.GRID_TRAPDOOR = nil
      GRID_ENTITIES[interior(0)] = make_grid(30, 10, 0, 0)
      GRID_ENTITIES[interior(1)] = make_grid(33, 20, 0, 1)
    """)
    connect(room)
    assert by_class(latest(room)) == ["lock_block"]


# --- interactables ---------------------------------------------------------------------


def slot(entity_id, variant, x=150):
    return f"""do local m = make_entity({entity_id}, {x}, 200, 6); m.Variant = {variant}
      ROOM_ENTITIES[#ROOM_ENTITIES+1] = m end"""


def test_slot_variants_are_grouped_with_the_documented_numbers_when_the_enum_is_missing(room):
    groups = [
        {1: "slot_machine", 8: "slot_machine", 11: "slot_machine", 2: "blood_donation",
         3: "fortune_teller", 4: "beggar", 5: "beggar", 6: "beggar", 7: "beggar", 9: "beggar"},
        {13: "beggar", 15: "beggar", 18: "beggar", 10: "restock_box", 16: "crane",
         17: "other_slot", 12: "other_slot", 14: "other_slot", 99: "other_slot"},
    ]  # fmt: skip
    for variants in groups:
        # The player stands at x=100, so an entity at 100+v has the relative position v.
        room.execute(
            "ROOM_ENTITIES = {}\n" + "\n".join(slot(100 + v, v, 100 + v) for v in variants)
        )
        connect(room) if not room.globals().OUTGOING else tick(room, 20)
        state = latest(room)
        assert all(e.kind == "interactable" for e in state.entities)
        assert {int(e.position.x): e.interactable_class for e in state.entities} == variants
        assert state.source_overflow == {} and [e.hp for e in state.entities] == [None] * len(
            variants
        )


def test_the_slot_variant_enum_wins_over_the_documented_numbers(room):
    room.execute("SlotVariant = { SLOT_MACHINE = 21, BEGGAR = 24 }")
    room.execute("\n".join([slot(1, 21, 110), slot(2, 1, 120), slot(3, 24, 130), slot(4, 4, 140)]))
    connect(room)
    got = {int(e.position.x): e.interactable_class for e in latest(room).entities}
    # 21 and 24 follow the enum; 1 and 4 are no longer these names, so "other_slot"; the
    # entries missing from the stub enum keep their documented numbers (4 is not one of them).
    assert got[10] == "slot_machine" and got[30] == "beggar"
    assert got[20] == "other_slot" and got[40] == "other_slot"


def test_heaven_light_door_is_an_interactable_and_other_effects_are_not(room):
    room.execute("""
      local door = make_entity(1, 110, 200, 1000); door.Variant = 39
      local poof = make_entity(2, 120, 200, 1000); poof.Variant = 15
      ROOM_ENTITIES = { door, poof }
    """)
    connect(room)
    state = latest(room)
    assert [(e.kind, e.interactable_class) for e in state.entities] == [
        ("interactable", "heaven_door")
    ]
    room.execute("EffectVariant = { HEAVEN_LIGHT_DOOR = 77 }; ROOM_ENTITIES[1].Variant = 77")
    tick(room, 20)
    assert [e.interactable_class for e in latest(room).entities] == ["heaven_door"]


def test_hidden_or_dead_slots_are_not_exported(room):
    room.execute(
        "\n".join([slot(1, 1, 110), slot(2, 1, 120), slot(3, 1, 130)])
        + "\nROOM_ENTITIES[1].Visible = false; ROOM_ENTITIES[2].IsDead = function() return true end"
    )
    connect(room)
    assert [int(e.position.x) for e in latest(room).entities] == [30]


def test_interactable_cap_keeps_the_nearest_and_counts_overflow(room):
    room.execute("\n".join(slot(i, 1, 100 + i * 10) for i in range(1, 21)))
    connect(room)
    state = latest(room)
    assert [e.position.x for e in state.entities] == [10.0 * i for i in range(1, 17)]
    assert state.source_overflow == {"interactable": 4}


@pytest.mark.parametrize(
    ("kind", "count", "cap"),
    [(10, 40, 32), (9, 70, 64), (5, 30, 24)],
)
def test_caps_keep_the_nearest_entities(room, kind, count, cap):
    # Far to near in list order, so the cap must select by distance, not by order.
    room.execute(f"""
      for i=1,{count} do ROOM_ENTITIES[i] = make_entity(i, 100+({count}-i+1)*10, 200, {kind}) end
    """)
    connect(room)
    state = latest(room)
    assert [e.position.x for e in state.entities] == [10.0 * i for i in range(1, cap + 1)]
    name = {10: "enemy", 9: "projectile", 5: "pickup"}[kind]
    assert state.source_overflow == {name: count - cap}


# --- door facts ------------------------------------------------------------------------


def doors(lua):
    return latest(lua).room.doors


def test_door_facts_carry_open_lock_target_type_and_visit(room):
    room.execute("""
      DOORS[0] = { open=true, locked=false, type=1, target=70 }
      DOORS[2] = { open=false, locked=true, type=4, target=71 }
      DOORS[5] = { open=false, locked=false, type=5, target=72 }
      ROOM_DESCS[70] = make_desc(70, 1, 1, 2, 0)   -- visited twice
      ROOM_DESCS[71] = make_desc(71, 1, 4, 0, 0)   -- never visited
      -- room 72 has no descriptor: the visit is unknown and reads as not visited
    """)
    connect(room)
    found = doors(room)
    assert [d is not None for d in found] == [True, False, True, False, False, True, False, False]
    assert (found[0].open, found[0].locked, found[0].target_type, found[0].target_visited) == (
        True,
        False,
        1,
        True,
    )
    assert (found[2].open, found[2].locked, found[2].target_type, found[2].target_visited) == (
        False,
        True,
        4,
        False,
    )
    assert (found[5].open, found[5].target_type, found[5].target_visited) == (False, 5, False)


def test_a_closed_door_to_a_secret_room_is_hidden_and_an_opened_one_is_seen(room):
    room.execute("""
      DOORS[1] = { open=false, type=7, target=70 }     -- secret room wall: not visible
      DOORS[3] = { open=false, type=8, target=71 }     -- super secret
      DOORS[4] = { open=false, type=29, target=72 }    -- ultra secret
      DOORS[6] = { open=true, type=7, target=73 }      -- bombed open: visible
      DOORS[7] = { open=false, type=2, target=74 }     -- a closed shop door is visible
    """)
    connect(room)
    found = doors(room)
    assert [d is not None for d in found] == [False, False, False, False, False, False, True, True]
    assert found[6].open and found[6].target_type == 7
    assert not found[7].open and found[7].target_type == 2


def test_secret_room_types_follow_the_enum_when_it_exists(room):
    room.execute("""
      RoomType = { ROOM_SECRET = 20, ROOM_SUPERSECRET = 21, ROOM_ULTRASECRET = 22 }
      DOORS[0] = { open=false, type=7, target=1 }      -- 7 is an ordinary type in this enum
      DOORS[1] = { open=false, type=21, target=2 }
    """)
    connect(room)
    found = doors(room)
    assert found[0] is not None and found[1] is None


def test_unreadable_door_parts_read_as_not_locked_or_unknown_and_never_close_the_peer(room):
    room.execute("""
      DOORS[0] = { open=true, type=1, target=70, lock_fault=true }   -- IsLocked errors
      DOORS[1] = { open=true, target=71 }                            -- no TargetRoomType
      DOORS[2] = { open=true, type=1, target=999999 }                -- target lookup misses
      local base = Game
      Game = function()
        local game = base()
        local base_room = game.GetRoom
        game.GetRoom = function(self)
          local room = base_room(self)
          local get = room.GetDoor
          room.GetDoor = function(self, slot)
            if slot == 3 then error("simulated door fault") end
            return get(self, slot)
          end
          return room
        end
        return game
      end
    """)
    connect(room)
    found = doors(room)
    assert not room.globals().CLOSED
    assert found[0].locked is False and found[0].target_type == 1
    assert found[1].target_type is None and found[1].target_visited is False
    assert found[2].target_visited is False
    assert found[3] is None  # a door whose read fails is absent


def test_doors_encode_into_the_room_block_of_the_vector(room):
    from isaac_threrisaifuture.encoding import (
        DOOR_FEATURES,
        ROOM_CLASSES,
        ROOM_OFFSET,
        ROOM_TYPES,
        encode,
    )

    room.execute("""
      DOORS[2] = { open=false, locked=true, type=14, target=70 }
      ROOM_DESCS[70] = make_desc(70, 1, 14, 1, 0)
    """)
    connect(room)
    vector = encode(latest(room)).vector
    at = ROOM_OFFSET + ROOM_TYPES + 3 + 2 * DOOR_FEATURES
    assert vector[at : at + 4].tolist() == [1.0, 0.0, 1.0, 1.0]
    hot = vector[at + 4 : at + DOOR_FEATURES]
    assert hot.tolist() == [1.0 if n == "devil_angel" else 0.0 for n in ROOM_CLASSES]


# --- enemy identity ----------------------------------------------------------------------

FACT_NAMES = ("npc_type", "npc_variant", "npc_max_hp", "boss", "champion", "flying", "invulnerable")


def test_enemy_identity_facts_come_from_the_npc_api_and_other_kinds_carry_none(room):
    room.execute("""
      local e = make_entity(1, 101, 200, 10)
      e.Type, e.Variant, e.MaxHitPoints, e.GridCollisionClass = 23, 2, 40.5, 4
      e.IsBoss = function() return true end
      e.ToNPC = function(self) return { IsChampion = function() return true end } end
      e.IsVulnerableEnemy = function() return true end
      e.IsInvincible = function() return true end
      ROOM_ENTITIES = { e, make_entity(2, 300, 200, 9), make_entity(3, 400, 200, 5) }
    """)
    connect(room)
    enemy, projectile, pickup = latest(room).entities
    assert (enemy.npc_type, enemy.npc_variant, enemy.npc_max_hp) == (23, 2, 40.5)
    assert enemy.boss and enemy.champion and enemy.flying and enemy.invulnerable
    for other in (projectile, pickup):
        assert all(getattr(other, name) is None for name in FACT_NAMES)


@pytest.mark.parametrize(
    ("collision", "flying"), [(0, True), (4, True), (1, False), (2, False), (3, False), (5, False)]
)
def test_flying_means_grid_collision_none_or_wall(room, collision, flying):
    room.execute(f"""
      local e = make_entity(1, 101, 200, 10)
      e.GridCollisionClass = {collision}
      ROOM_ENTITIES = {{ e }}
    """)
    connect(room)
    assert latest(room).entities[0].flying is flying


def test_invulnerable_is_not_vulnerable_or_invincible(room):
    room.execute("""
      local a, b, c = make_entity(1, 101, 200, 10), make_entity(2, 201, 200, 10),
        make_entity(3, 301, 200, 10)
      a.IsVulnerableEnemy = function() return false end
      b.IsVulnerableEnemy = function() return true end
      c.IsVulnerableEnemy = function() return true end
      c.IsInvincible = function() return true end
      ROOM_ENTITIES = { a, b, c }
    """)
    connect(room)
    assert [e.invulnerable for e in latest(room).entities] == [True, False, True]


def test_missing_or_failing_enemy_methods_read_false_and_zero(room):
    room.execute("""
      local e = make_entity(1, 101, 200, 10)   -- no IsBoss, ToNPC, IsVulnerableEnemy at all
      e.MaxHitPoints = nil
      local f = make_entity(2, 201, 200, 10)
      f.IsBoss = function() error("boom") end
      f.ToNPC = function() return nil end      -- a non-NPC: IsChampion cannot be reached
      f.IsVulnerableEnemy = function() error("boom") end
      f.MaxHitPoints = 0/0
      ROOM_ENTITIES = { e, f }
    """)
    connect(room)
    for item in latest(room).entities:
        assert (item.npc_type, item.npc_variant, item.npc_max_hp) == (10, 10, 0)
        assert not (item.boss or item.champion or item.flying or item.invulnerable)


def test_enemy_identity_values_are_clamped_into_the_wire_ranges(room):
    room.execute("""
      local e = make_entity(1, 101, 200, 10)
      e.Type, e.Variant, e.MaxHitPoints = 5000, 99999, 1e9
      ROOM_ENTITIES = { e }
    """)
    connect(room)
    item = latest(room).entities[0]
    assert (item.npc_type, item.npc_variant, item.npc_max_hp) == (1000, 4095, 1000000)
