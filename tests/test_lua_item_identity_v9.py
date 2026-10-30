"""Production Lua, observation schema 9: item catalog facts from a stubbed ItemConfig."""

import re
from pathlib import Path

import pytest
from test_lua_entities import STUBS, connect, frames
from test_lua_observer import build_lua, tick

from isaac_threrisaifuture.entities import ITEM_TAGS

SOURCE = (Path(__file__).resolve().parents[1] / "mod/observer/main.lua").read_text("utf-8")
TAG_VALUES = "{ TAG_GUPPY=1, TAG_FLY=2, TAG_MUSHROOM=4, TAG_SYRINGE=8, TAG_BOB=16, " + (
    "TAG_SPIDER=32, TAG_BABY=64, TAG_MOM=128 }"
)
# Item 10 is a passive, 20 an active with 6 charges, 30 a familiar; tag masks use TAG_VALUES.
CATALOG = """
  ItemConfig = TAG_VALUES_LUA
  CATALOG = {
    [10] = { Quality=3, Type=1, MaxCharges=0, tags=1 + 8 },
    [20] = { Quality=2, Type=3, MaxCharges=6, tags=2 },
    [30] = { Quality=1, Type=4, MaxCharges=0, tags=1 + 2 + 128 },
  }
  ITEM_CONFIG = function(id)
    local entry = CATALOG[id]
    if not entry then return nil end
    return { Quality=entry.Quality, Type=entry.Type, MaxCharges=entry.MaxCharges,
      HasTags=function(self, tag) return entry.tags & tag == tag end }
  end
""".replace("TAG_VALUES_LUA", TAG_VALUES)


@pytest.fixture
def room():
    lua = build_lua()
    lua.execute(STUBS)
    lua.execute("callbacks.start(); SEND_LIMIT=4096")
    lua.execute(CATALOG)
    return lua


def latest(lua):
    return frames(lua)[-1].entity_frame


def pedestal(entity_id, item, extra=""):
    return f"""do local p = make_entity({entity_id}, 100 + {entity_id}, 200, 5)
      p.Variant, p.SubType = 100, {item}; {extra}
      ROOM_ENTITIES[#ROOM_ENTITIES+1] = p end"""


def test_the_lua_tag_names_match_the_python_list():
    names = re.search(r"local item_tag_names = \{([^}]*)\}", SOURCE)
    assert names is not None
    assert [n.strip(' "').lower() for n in names.group(1).split(",")] == list(ITEM_TAGS)


def test_pedestal_collectibles_carry_quality_type_charges_and_tags(room):
    room.execute("\n".join([pedestal(1, 10), pedestal(2, 20), pedestal(3, 30)]))
    connect(room)
    one, two, three = latest(room).entities
    assert (one.item_quality, one.item_type, one.item_max_charges, one.item_tags) == (
        3,
        "passive",
        0,
        0b1001,
    )
    assert (two.item_quality, two.item_type, two.item_max_charges, two.item_tags) == (
        2,
        "active",
        6,
        0b10,
    )
    assert (three.item_type, three.item_tags) == ("familiar", 0b10000011)


def test_other_pickups_and_empty_pedestals_carry_no_item_facts(room):
    room.execute("""
      ROOM_ENTITIES = { make_entity(1, 101, 200, 5), make_entity(2, 102, 200, 5) }
      ROOM_ENTITIES[1].Variant = 10                                   -- a heart
      ROOM_ENTITIES[2].Variant, ROOM_ENTITIES[2].SubType = 100, 0     -- an empty pedestal
    """)
    connect(room)
    for item in latest(room).entities:
        assert item.item_quality is item.item_type is item.item_max_charges is None
        assert item.item_tags is None


def test_an_item_missing_from_the_catalog_reads_as_unknown_zeros(room):
    room.execute(pedestal(1, 999))
    connect(room)
    (item,) = latest(room).entities
    assert (item.item_quality, item.item_type, item.item_max_charges, item.item_tags) == (
        0,
        "unknown",
        0,
        0,
    )
    assert item.subtype == 999


def test_a_missing_tag_enum_or_failing_has_tags_gives_zero_bits(room):
    room.execute("ItemConfig.TAG_FLY = nil")
    room.execute(pedestal(1, 20))  # its only tag is FLY
    room.execute(pedestal(2, 10))
    connect(room)
    first, second = latest(room).entities
    assert first.item_tags == 0 and second.item_tags == 0b1001


def test_catalog_numbers_are_clamped_into_the_wire_ranges(room):
    room.execute("""
      ITEM_CONFIG = function(id) return { Quality=99, Type=3, MaxCharges=500,
        HasTags=function() return true end } end
    """)
    room.execute(pedestal(1, 10))
    connect(room)
    (item,) = latest(room).entities
    assert (item.item_quality, item.item_max_charges, item.item_tags) == (4, 24, 255)


def test_the_item_type_enum_wins_over_the_documented_numbers(room):
    room.execute("ItemType = { ITEM_PASSIVE = 7, ITEM_ACTIVE = 8, ITEM_FAMILIAR = 9 }")
    room.execute(pedestal(1, 10))  # Type=1 is no longer a passive in this enum
    connect(room)
    assert latest(room).entities[0].item_type == "unknown"


def test_a_blind_pedestal_hides_its_item(room):
    room.execute(pedestal(1, 10, "p.IsBlind = function() return true end"))
    room.execute(pedestal(2, 10, "p.IsBlind = function() return false end"))
    room.execute(pedestal(3, 10, "p.IsBlind = function() error('boom') end"))
    connect(room)
    blind, seen, faulty = latest(room).entities
    assert blind.subtype == 0 and blind.item_type is None and blind.item_tags is None
    assert seen.subtype == faulty.subtype == 10 and seen.item_type == faulty.item_type == "passive"


def test_the_curse_of_the_blind_hides_every_pedestal_item(room):
    # The plain Repentance API has no IsBlind; the level curse (bit 64) decides instead.
    room.execute(pedestal(1, 10, ""))
    room.execute("CURSES = 64")
    connect(room)
    (cursed,) = latest(room).entities
    assert cursed.subtype == 0 and cursed.item_type is None and cursed.item_tags is None
    room.execute("CURSES = 1")  # another curse keeps the item visible
    tick(room, 20)
    (seen,) = latest(room).entities
    assert seen.subtype == 10 and seen.item_type == "passive"


def test_the_active_item_carries_quality_and_tags(room):
    room.execute("ACTIVE, CHARGE = 20, 3")
    connect(room)
    inventory = latest(room).inventory
    assert (inventory.active_item, inventory.active_quality, inventory.active_tags) == (20, 2, 0b10)
    room.execute("ACTIVE = 0")
    tick(room, 20)
    inventory = latest(room).inventory
    assert (inventory.active_quality, inventory.active_tags) == (0, 0)


def test_held_collectibles_are_counted_per_tag_on_the_list_cadence(room):
    room.execute("ITEM_SIZE = 40; HELD[10], HELD[20], HELD[30] = true, true, true")
    connect(room)
    # GUPPY: items 10 and 30; FLY: 20 and 30; SYRINGE: 10; MOM: 30; the rest none.
    assert latest(room).tag_counts == [2, 2, 0, 1, 0, 0, 0, 1]
    room.execute("HELD[30] = nil; FRAME = 200")  # the cache refreshes on its period
    tick(room, 20)
    assert latest(room).tag_counts == [1, 1, 0, 1, 0, 0, 0, 0]


def test_tag_counts_are_zero_without_a_catalog(room):
    room.execute("ITEM_SIZE = 40; HELD[10] = true; ITEM_CONFIG = function() return nil end")
    connect(room)
    assert latest(room).tag_counts == [0] * len(ITEM_TAGS)


def test_a_failing_has_tags_reads_zero_tags_but_keeps_the_other_facts(room):
    room.execute("""
      ITEM_CONFIG = function(id) return { Quality=2, Type=1, MaxCharges=0,
        HasTags=function() error("boom") end } end
    """)
    room.execute(pedestal(1, 10))
    connect(room)
    (item,) = latest(room).entities
    assert (item.item_quality, item.item_type, item.item_tags) == (2, "passive", 0)
