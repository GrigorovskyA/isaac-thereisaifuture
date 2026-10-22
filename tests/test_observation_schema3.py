"""OFFLINE schema 3 contract: game facts decode strictly and encode to a fixed 1837 vector."""

import json
from typing import Any

import numpy as np
import pytest
from synthetic import enemy, frame, inventory, pickup, room_facts
from test_live import live

from isaac_threrisaifuture.encoding import (
    CAPACITY,
    COLLECTIBLE_OFFSET,
    ENEMY_OFFSET,
    INVENTORY_OFFSET,
    OBSERVATION_SIZE,
    PICKUP_SLOT_FEATURES,
    ROOM_OFFSET,
    SLOT_FEATURES,
    VARIANT_CLASSES,
    encode,
    variant_class,
)
from isaac_threrisaifuture.entities import EntityFrame
from isaac_threrisaifuture.live_wire import LiveOracle
from isaac_threrisaifuture.observation import ProtocolError, decode

PICKUP_OFFSET = ENEMY_OFFSET + SLOT_FEATURES * (
    CAPACITY["enemy"] + CAPACITY["projectile"] + CAPACITY["obstacle"]
)


def wire(item: EntityFrame) -> dict[str, Any]:
    return json.loads(item.model_dump_json())


def decoded(payload: dict[str, Any]) -> EntityFrame:
    return decode(json.dumps(payload).encode(), EntityFrame, 65536)


def test_layout_matches_the_design_table():
    assert OBSERVATION_SIZE == 1837
    assert (INVENTORY_OFFSET, ROOM_OFFSET, ENEMY_OFFSET) == (9, 18, 61)
    assert PICKUP_OFFSET == 61 + 128 + 256 + 192
    assert PICKUP_SLOT_FEATURES == 22 and len(VARIANT_CLASSES) == 12
    assert COLLECTIBLE_OFFSET == PICKUP_OFFSET + 8 * 22 == 1837 - 1024


def test_wire_round_trip_encodes_exactly_1837_finite_values():
    original = frame(
        [enemy(1, 10, 0), pickup(2, 30, 0, variant=100, subtype=33, price=15)],
        inventory=inventory(coins=12, active_item=33, active_charge=3, active_max_charge=6),
        collectibles=[1, 33, 1024],
        room=room_facts(type=5, clear=True, doors=[True, False] * 4),
    )
    again = decoded(wire(original))
    assert again == original
    vector = encode(again).vector
    assert vector.shape == (1837,) and vector.dtype == np.float32
    assert np.isfinite(vector).all() and np.all(np.abs(vector) <= 1.0)


def test_inventory_room_and_collectible_blocks():
    vector = encode(
        frame(
            inventory=inventory(
                coins=50,
                bombs=99,
                keys=200,
                active_item=512,
                active_charge=3,
                active_max_charge=6,
                card=1,
                trinket=9,
            ),  # fmt: skip
            collectibles=[1, 33, 1024],
            room=room_facts(type=7, stage=15, stage_type=7, clear=True, doors=[True] + [False] * 7),
        )
    ).vector
    inv = vector[INVENTORY_OFFSET : INVENTORY_OFFSET + 9]
    assert inv.tolist() == pytest.approx([50 / 99, 1.0, 1.0, 1.0, 0.5, 0.5, 1.0, 0.0, 1.0])
    room = vector[ROOM_OFFSET : ROOM_OFFSET + 43]
    assert room[7] == 1.0 and room[:32].sum() == 1.0
    assert room[32:35].tolist() == [1.0, 1.0, 1.0]  # stage, stage type, clear
    assert room[35:].tolist() == [1.0] + [0.0] * 7
    held = vector[COLLECTIBLE_OFFSET:]
    assert held.shape == (1024,) and np.flatnonzero(held).tolist() == [0, 32, 1023]


@pytest.mark.parametrize(
    ("variant", "name"),
    [
        (10, "heart"), (20, "coin"), (30, "key"), (40, "bomb"), (41, "bomb"),
        (50, "chest"), (55, "chest"), (60, "chest"), (340, "chest"), (360, "chest"),
        (390, "chest"), (69, "sack"), (70, "pill"), (90, "battery"), (100, "collectible"),
        (300, "card"), (350, "trinket"), (0, "other"), (61, "other"), (42, "other"),
        (1023, "other"),
    ],
)  # fmt: skip
def test_variant_class_mapping(variant, name):
    assert VARIANT_CLASSES[variant_class(variant)] == name
    slot = encode(frame([pickup(1, 5, 5, variant=variant, subtype=512, price=-3)])).vector[
        PICKUP_OFFSET : PICKUP_OFFSET + PICKUP_SLOT_FEATURES
    ]
    assert slot[0] == 1.0
    one_hot = slot[SLOT_FEATURES : SLOT_FEATURES + 12]
    assert one_hot.sum() == 1.0 and VARIANT_CLASSES[int(one_hot.argmax())] == name
    assert slot[-2] == 0.5 and slot[-1] == 1.0  # subtype/1024 and shop flag


def test_free_pickup_has_no_shop_flag():
    slot = encode(frame([pickup(1, 5, 5, price=0)])).vector[PICKUP_OFFSET:]
    assert slot[PICKUP_SLOT_FEATURES - 1] == 0.0


def test_pickup_capacity_is_eight_with_overflow_counted():
    encoded = encode(frame([pickup(i, i, 0) for i in range(11)]))
    assert encoded.overflow == {"pickup": 3}


def mutate(path: str, value: Any):
    def apply(payload: dict[str, Any]) -> None:
        *parents, last = path.split(".")
        target: Any = payload
        for part in parents:
            target = target[int(part)] if part.isdigit() else target[part]
        target[int(last) if last.isdigit() else last] = value

    return apply


def with_pickup(payload: dict[str, Any]) -> None:
    payload["entities"] = wire(frame([pickup(1, 1, 1)]))["entities"]


MALFORMED = {
    "unknown inventory field": mutate("inventory.gems", 1),
    "unknown room field": mutate("room.secret", True),
    "unknown top field": mutate("hidden", 1),
    "negative coins": mutate("inventory.coins", -1),
    "coins above range": mutate("inventory.coins", 1000),
    "negative charge": mutate("inventory.active_charge", -1),
    "charge above range": mutate("inventory.active_max_charge", 25),
    "unsorted collectibles": mutate("collectibles", [5, 3]),
    "duplicate collectibles": mutate("collectibles", [3, 3]),
    "collectible zero": mutate("collectibles", [0, 3]),
    "collectible above range": mutate("collectibles", [3, 1025]),
    "more than 256 without overflow": mutate("collectibles", list(range(1, 258))),
    "overflow with a short list": mutate("collectible_overflow", 1),
    "negative overflow": mutate("collectible_overflow", -1),
    "room type": mutate("room.type", 32),
    "stage": mutate("room.stage", 16),
    "stage type": mutate("room.stage_type", 8),
    "seven doors": mutate("room.doors", [False] * 7),
    "nine doors": mutate("room.doors", [False] * 9),
    "door not bool": mutate("room.doors", [0] * 8),
    "clear not bool": mutate("room.clear", 1),
    "schema 1": mutate("observation_schema_version", 1),
    "schema 2": mutate("observation_schema_version", 2),
    "missing inventory": lambda p: p.pop("inventory"),
    "missing room": lambda p: p.pop("room"),
    "missing collectibles": lambda p: p.pop("collectibles"),
}


@pytest.mark.parametrize("name", MALFORMED)
def test_malformed_facts_are_protocol_errors(name):
    payload = wire(frame())
    MALFORMED[name](payload)
    with pytest.raises(ProtocolError):
        decoded(payload)


def test_overflow_is_valid_only_with_a_full_list():
    payload = wire(frame(collectibles=list(range(1, 257)), collectible_overflow=40))
    assert decoded(payload).collectible_overflow == 40


@pytest.mark.parametrize(
    "change",
    [
        {"variant": None},
        {"subtype": None},
        {"price": None},
        {"variant": 1024},
        {"subtype": 1025},
        {"subtype": -1},
        {"price": 1000},
        {"price": -1001},
    ],
)
def test_pickup_facts_are_required_and_bounded(change):
    payload = wire(frame())
    with_pickup(payload)
    payload["entities"][0].update(change)
    with pytest.raises(ProtocolError):
        decoded(payload)


def test_non_pickups_cannot_carry_pickup_facts():
    payload = wire(frame([enemy(1, 1, 1)]))
    payload["entities"][0]["variant"] = 10
    with pytest.raises(ProtocolError):
        decoded(payload)


def test_oracle_only_difference_gives_identical_vectors():
    first = live(1)
    assert first.oracle is not None and first.entity_frame is not None
    other_oracle = first.oracle.model_copy(
        update={"room_index": 7, "room_clear": True, "enemy_overflow": 3}
    )
    other = first.model_copy(update={"oracle": other_oracle})
    assert other.oracle != first.oracle and other.entity_frame == first.entity_frame
    assert np.array_equal(encode(first.entity_frame).vector, encode(other.entity_frame).vector)
    assert "room_index" in LiveOracle.model_fields
    assert "room_index" not in EntityFrame.model_fields
