"""OFFLINE schema 9 contract: item identity, ItemConfig facts and held tag counts."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml
from pydantic import ValidationError
from synthetic import enemy, frame, inventory, pedestal, pickup

from isaac_threrisaifuture.checkpoints import config_hash
from isaac_threrisaifuture.encoding import (
    CAPACITY,
    CHARGE_SCALE,
    ENEMY_OFFSET,
    EXTRA_OFFSET,
    HELD_TAG_OFFSET,
    INVENTORY_FEATURES,
    INVENTORY_OFFSET,
    ITEM_BUCKETS,
    ITEM_FEATURES,
    OBSERVATION_SIZE,
    PICKUP_SLOT_FEATURES,
    ROOM_OFFSET,
    SLOT_FEATURES,
    SLOT_WIDTH,
    TAG_FEATURES,
    VARIANT_CLASSES,
    WEAPON_OFFSET,
    encode,
    item_bucket,
)
from isaac_threrisaifuture.entities import (
    FRAME_SCHEMA_VERSION,
    ITEM_TAGS,
    OBSERVATION_SCHEMA_VERSION,
    Entity,
    EntityFrame,
    Vec,
)
from isaac_threrisaifuture.observation import ProtocolError, decode
from isaac_threrisaifuture.training import load_training_config

ROOT = Path(__file__).resolve().parents[1]
PICKUP_OFFSET = ENEMY_OFFSET + sum(
    CAPACITY[k] * SLOT_WIDTH[k] for k in ("enemy", "projectile", "obstacle")
)
ITEM_AT = SLOT_FEATURES + len(VARIANT_CLASSES) + 2  # item block inside a pickup slot


def item_block(vector: np.ndarray, slot: int = 0) -> np.ndarray:
    start = PICKUP_OFFSET + slot * PICKUP_SLOT_FEATURES + ITEM_AT
    return vector[start : start + ITEM_FEATURES]


def wire(item: EntityFrame) -> dict[str, Any]:
    import json

    return json.loads(item.model_dump_json())


# --- versions, layout ----------------------------------------------------------------------


def test_versions_and_layout():
    assert (OBSERVATION_SCHEMA_VERSION, FRAME_SCHEMA_VERSION) == (9, 7)
    assert EntityFrame.model_fields["observation_schema_version"].default == 7
    assert (ITEM_BUCKETS, TAG_FEATURES, ITEM_FEATURES) == (64, 8, 77)
    assert INVENTORY_FEATURES == 9 + 1 + 8 + 64 == 82
    assert PICKUP_SLOT_FEATURES == SLOT_FEATURES + len(VARIANT_CLASSES) + 2 + 77 == 99
    assert ROOM_OFFSET == INVENTORY_OFFSET + INVENTORY_FEATURES
    assert EXTRA_OFFSET == HELD_TAG_OFFSET + TAG_FEATURES
    assert HELD_TAG_OFFSET == WEAPON_OFFSET + 15
    assert OBSERVATION_SIZE == 11691


def test_schema_6_frames_are_refused():
    payload = wire(frame())
    payload["observation_schema_version"] = 6
    import json

    with pytest.raises(ProtocolError):
        decode(json.dumps(payload).encode(), EntityFrame, 131072)


def test_the_config_pins_9_and_schema_8_changes_the_contract_hash():
    config, digest = load_training_config(ROOT / "configs/training-pure-v4.yaml")
    raw = yaml.safe_load((ROOT / "configs/training-pure-v4.yaml").read_text("utf-8"))
    assert config.contract.observation_schema_version == 9 and config.contract.reward_version == 11
    assert config_hash(raw["contract"]) == digest
    raw["contract"]["observation_schema_version"] = 8
    assert config_hash(raw["contract"]) != digest


# --- item_bucket -----------------------------------------------------------------------------


def test_item_bucket_is_the_top_bits_of_a_multiplicative_hash():
    for item_id in (1, 2, 33, 118, 245, 729, 1024):
        assert item_bucket(item_id) == (item_id * 2654435761 % 2**32) >> 26
        assert 0 <= item_bucket(item_id) < ITEM_BUCKETS
    # The low bits of the product only depend on the low bits of the ID; the top bits do not.
    assert len({item_bucket(i * 64) for i in range(1, 17)}) > 8


def test_item_bucket_spreads_the_collectible_ids_over_most_buckets():
    counts = np.bincount([item_bucket(i) for i in range(1, 730)], minlength=ITEM_BUCKETS)
    assert (counts > 0).sum() >= 60
    assert counts.max() <= 20


# --- pedestal items ---------------------------------------------------------------------------


def test_a_pedestal_collectible_fills_bucket_quality_type_charges_and_tags():
    item = pedestal(1, 10, 0, 245, quality=3, item_type="active", max_charges=6, tags=0b1010_0001)
    block = item_block(encode(frame(entities=[item])).vector)
    assert block[0] == pytest.approx(3 / 4)
    assert block[1:4].tolist() == [0.0, 1.0, 0.0]  # passive, active, familiar
    assert block[4] == pytest.approx(6 / CHARGE_SCALE)
    assert block[5:13].tolist() == [1.0, 0, 0, 0, 0, 1.0, 0, 1.0]
    hot = block[13:]
    assert hot.sum() == 1.0 and hot[item_bucket(245)] == 1.0


@pytest.mark.parametrize(("item_type", "slot"), [("passive", 0), ("active", 1), ("familiar", 2)])
def test_item_types_are_a_one_hot_and_unknown_is_all_zero(item_type, slot):
    block = item_block(encode(frame(entities=[pedestal(1, 10, 0, 5, item_type=item_type)])).vector)
    assert block[1:4].tolist() == [float(i == slot) for i in range(3)]
    block = item_block(encode(frame(entities=[pedestal(1, 10, 0, 5, item_type="unknown")])).vector)
    assert block[1:4].tolist() == [0.0, 0.0, 0.0] and block[13:].sum() == 1.0


def test_max_charges_are_clipped_to_one():
    block = item_block(encode(frame(entities=[pedestal(1, 10, 0, 5, max_charges=24)])).vector)
    assert block[4] == 1.0


def test_collectible_without_item_facts_still_gets_its_bucket():
    legacy = pickup(1, 10, 0, variant=100, subtype=118)
    block = item_block(encode(frame(entities=[legacy])).vector)
    assert block[:13].tolist() == [0.0] * 13 and block[13 + item_bucket(118)] == 1.0


def test_other_pickups_and_empty_pedestals_leave_the_item_block_zero():
    entities = [pickup(1, 10, 0, variant=10, subtype=1), pickup(2, 20, 0, variant=100, subtype=0)]
    vector = encode(frame(entities=entities)).vector
    assert item_block(vector, 0).tolist() == [0.0] * ITEM_FEATURES
    assert item_block(vector, 1).tolist() == [0.0] * ITEM_FEATURES


def test_the_old_subtype_scalar_and_shop_flag_stay():
    vector = encode(frame(entities=[pedestal(1, 10, 0, 512, price=15)])).vector
    base = PICKUP_OFFSET + SLOT_FEATURES
    assert vector[base + len(VARIANT_CLASSES)] == pytest.approx(512 / 1024)
    assert vector[base + len(VARIANT_CLASSES) + 1] == 1.0


# --- active item and held tags ----------------------------------------------------------------


def test_the_active_item_gets_bucket_quality_and_tags():
    inv = inventory(active_item=33, active_charge=2, active_max_charge=4)
    inv = inv.model_copy(update={"active_quality": 4, "active_tags": 0b100})
    vector = encode(frame(inventory=inv)).vector
    block = vector[INVENTORY_OFFSET + 9 : INVENTORY_OFFSET + INVENTORY_FEATURES]
    assert block[0] == 1.0
    assert block[1:9].tolist() == [0, 0, 1.0, 0, 0, 0, 0, 0]
    assert block[9:].sum() == 1.0 and block[9 + item_bucket(33)] == 1.0
    assert vector[INVENTORY_OFFSET + 4] == pytest.approx(33 / 1024)  # the old scalar stays


def test_no_active_item_leaves_the_block_zero():
    inv = inventory().model_copy(update={"active_quality": 3, "active_tags": 255})
    vector = encode(frame(inventory=inv)).vector
    assert not vector[INVENTORY_OFFSET + 9 : INVENTORY_OFFSET + INVENTORY_FEATURES].any()


def test_held_tag_counts_are_scaled_by_three_and_clipped():
    counts = [0, 1, 2, 3, 4, 40, 0, 1]
    vector = encode(frame().model_copy(update={"tag_counts": counts})).vector
    got = vector[HELD_TAG_OFFSET : HELD_TAG_OFFSET + TAG_FEATURES]
    assert got.tolist() == pytest.approx([0, 1 / 3, 2 / 3, 1, 1, 1, 0, 1 / 3])
    assert not encode(frame()).vector[HELD_TAG_OFFSET : HELD_TAG_OFFSET + TAG_FEATURES].any()


def test_the_vector_stays_within_the_observation_bounds():
    items = [
        pedestal(i, 10 + i, 0, 1 + i, quality=4, item_type="active", max_charges=24, tags=255)
        for i in range(1, 25)
    ]
    inv = inventory(active_item=1024).model_copy(update={"active_quality": 4, "active_tags": 255})
    vector = encode(frame(entities=items, inventory=inv)).vector
    assert vector.min() >= -1.0 and vector.max() <= 1.0 and len(vector) == OBSERVATION_SIZE


# --- wire validation --------------------------------------------------------------------------


def entity(**changes: Any) -> Entity:
    values: dict[str, Any] = dict(
        kind="pickup",
        entity_id=1,
        spawn_generation=0,
        position=Vec(x=1, y=1),
        variant=100,
        subtype=5,
        price=0,
        item_quality=1,
        item_type="passive",
        item_max_charges=0,
        item_tags=0,
    )
    values.update(changes)
    return Entity(**values)


def test_item_facts_are_valid_on_a_pedestal_collectible():
    assert entity().item_type == "passive"


@pytest.mark.parametrize(
    "changes",
    [
        {"variant": 10},  # a heart
        {"subtype": 0},  # an empty pedestal
        {"kind": "enemy", "variant": None, "subtype": None, "price": None},
        {"item_quality": None},  # partial facts
        {"item_tags": None},
        {"item_type": None},
        {"item_max_charges": None},
        {"item_quality": 5},
        {"item_quality": -1},
        {"item_type": "trinket"},
        {"item_max_charges": 25},
        {"item_tags": 256},
        {"item_tags": -1},
    ],
)
def test_item_facts_are_rejected_off_pedestals_when_partial_or_out_of_range(changes):
    with pytest.raises(ValidationError):
        entity(**changes)


def test_inventory_and_frame_ranges_are_validated():
    for bad in ({"active_quality": 5}, {"active_tags": 256}, {"active_quality": -1}):
        with pytest.raises(ValidationError):
            inventory(**bad)
    base = wire(frame())
    for counts in ([0] * 7, [0] * 9, [-1] + [0] * 7, [257] + [0] * 7):
        with pytest.raises(ValidationError):
            EntityFrame(**{**base, "tag_counts": counts})


def test_enemies_do_not_accept_item_facts():
    with pytest.raises(ValidationError):
        enemy_with = enemy(1, 10, 0).model_dump() | {"item_quality": 1}
        Entity(**enemy_with)


def test_the_tag_list_has_eight_unique_names():
    assert len(ITEM_TAGS) == len(set(ITEM_TAGS)) == 8
