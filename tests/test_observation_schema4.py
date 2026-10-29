"""OFFLINE schema 4 contract: stats, tear flags, weapons, own attacks and bombs."""

import json
from typing import Any

import numpy as np
import pytest
from synthetic import enemy, frame, stats, tear_flags, weapons

from isaac_threrisaifuture.encoding import (
    BOMB_AGE_SCALE,
    CAPACITY,
    COLLECTIBLE_OFFSET,
    EXTRA_OFFSET,
    MAP_OFFSET,
    OBSERVATION_SIZE,
    SLOT_FEATURES,
    SLOT_WIDTH,
    STATS_OFFSET,
    TEAR_FLAG_OFFSET,
    WEAPON_OFFSET,
    encode,
)
from isaac_threrisaifuture.entities import (
    BOMB_AGE_MAX,
    TEAR_FLAG_NAMES,
    WEAPON_NAMES,
    Entity,
    EntityFrame,
    Vec,
)
from isaac_threrisaifuture.observation import ProtocolError, decode


def wire(item: EntityFrame) -> dict[str, Any]:
    return json.loads(item.model_dump_json())


def decoded(payload: dict[str, Any]) -> EntityFrame:
    return decode(json.dumps(payload).encode(), EntityFrame, 131072)


def own(entity_id: int, x: float, y: float) -> Entity:
    return Entity(
        kind="own_attack",
        entity_id=entity_id,
        spawn_generation=0,
        position=Vec(x=x, y=y),
        velocity=Vec(x=1, y=0),
    )


def bomb(entity_id: int, x: float, y: float, age: int) -> Entity:
    return Entity(
        kind="bomb", entity_id=entity_id, spawn_generation=0, position=Vec(x=x, y=y), age_frames=age
    )


def test_layout_size_is_pinned():
    assert len(TEAR_FLAG_NAMES) == 16 and len(WEAPON_NAMES) == 15
    assert CAPACITY["own_attack"] == 48 and CAPACITY["bomb"] == 8
    assert SLOT_WIDTH["own_attack"] == 8 and SLOT_WIDTH["bomb"] == 9
    assert STATS_OFFSET == COLLECTIBLE_OFFSET + 1024
    assert (TEAR_FLAG_OFFSET, WEAPON_OFFSET) == (STATS_OFFSET + 6, STATS_OFFSET + 22)
    assert EXTRA_OFFSET == STATS_OFFSET + 37
    # The minimap and stall clock follow the extra blocks (tests/test_observation_schema5.py).
    assert MAP_OFFSET == EXTRA_OFFSET + 48 * 8 + 8 * 9 + 16 * SLOT_WIDTH["interactable"]


def test_round_trip_and_vector_shape():
    original = frame(
        [own(1, 10, 0), bomb(2, 20, 0, 12)],
        stats=stats(damage=25, tears_per_second=15, range=500, luck=-5),
        tear_flags=tear_flags("spectral", "burn"),
        weapons=weapons("tears", "bone"),
    )
    again = decoded(wire(original))
    assert again == original
    result = encode(again)
    assert result.vector.shape == (OBSERVATION_SIZE,) and result.vector.dtype == np.float32
    assert np.isfinite(result.vector).all() and np.all(np.abs(result.vector) <= 1.0)
    assert result.clipped_values == 0


def test_stats_flags_and_weapons_reach_the_vector():
    vec = encode(
        frame(
            stats=stats(damage=25, tears_per_second=15, range=500, shot_speed=2.5, luck=-5),
            tear_flags=tear_flags("spectral", "bouncing"),
            weapons=weapons("brimstone", "umbilical_whip"),
        )
    ).vector
    assert list(vec[STATS_OFFSET : STATS_OFFSET + 6]) == pytest.approx(
        [0.5, 0.5, 0.5, 0.5, 0.2, -0.5]
    )
    spectral = TEAR_FLAG_NAMES.index("spectral")
    assert vec[TEAR_FLAG_OFFSET + spectral] == 1.0 and vec[TEAR_FLAG_OFFSET + 1] == 0.0
    assert vec[TEAR_FLAG_OFFSET + 15] == 1.0
    assert vec[WEAPON_OFFSET + 1] == 1.0 and vec[WEAPON_OFFSET + 14] == 1.0
    assert vec[WEAPON_OFFSET] == 0.0


def test_spectral_flag_is_set_in_frame_and_vector_only_when_on():
    on = frame(tear_flags=tear_flags("spectral"))
    assert on.tear_flags[0] is True and sum(on.tear_flags) == 1
    off = frame()
    assert encode(on).vector[TEAR_FLAG_OFFSET] == 1.0
    assert encode(off).vector[TEAR_FLAG_OFFSET] == 0.0


def test_stats_are_clipped_and_counted_at_the_extremes():
    result = encode(frame(stats=stats(damage=1000, range=10000, luck=100)))
    assert result.clipped_values == 3 and np.all(np.abs(result.vector) <= 1.0)


def test_own_attack_and_bomb_slots_encode_features_and_age():
    vec = encode(frame([own(1, 100, -50), bomb(2, 30, 40, 60)])).vector
    base = EXTRA_OFFSET
    assert list(vec[base : base + SLOT_FEATURES]) == pytest.approx(
        [1, 0.1, -0.05, 1, 1 / 20, 0, 0, 0]
    )
    bomb_base = EXTRA_OFFSET + CAPACITY["own_attack"] * SLOT_WIDTH["own_attack"]
    assert list(vec[bomb_base : bomb_base + 3]) == pytest.approx([1, 0.03, 0.04])
    assert vec[bomb_base + SLOT_FEATURES] == pytest.approx(60 / BOMB_AGE_SCALE)


def test_bomb_age_increases_in_the_vector_and_clips_after_the_scale():
    ages = [
        encode(frame([bomb(1, 5, 5, age)])).vector[
            EXTRA_OFFSET + CAPACITY["own_attack"] * 8 + SLOT_FEATURES
        ]
        for age in (0, 30, 90)
    ]
    assert ages == sorted(ages) and ages[0] == 0.0 and ages[2] == pytest.approx(0.75)
    late = encode(frame([bomb(1, 5, 5, 500)]))
    assert late.clipped_values == 1


def test_caps_keep_the_nearest_and_count_overflow():
    attacks = [own(i, 10.0 * (60 - i), 0) for i in range(60)]
    bombs = [bomb(100 + i, 10.0 * (12 - i), 0, i) for i in range(12)]
    result = encode(frame(attacks + bombs, source_overflow={"bomb": 1}))
    assert result.overflow == {"own_attack": 12, "bomb": 5}
    first = result.vector[EXTRA_OFFSET + 1]
    assert first == pytest.approx(0.010)  # nearest own attack at x=10
    bomb_base = EXTRA_OFFSET + 48 * 8
    nearest_bomb_age = result.vector[bomb_base + SLOT_FEATURES]
    assert nearest_bomb_age == pytest.approx(11 / BOMB_AGE_SCALE)


def test_own_attacks_and_enemy_shots_use_separate_blocks():
    shot = Entity(kind="projectile", entity_id=7, spawn_generation=0, position=Vec(x=5, y=0))
    vec = encode(frame([own(1, 50, 0), shot, enemy(2, 80, 0)])).vector
    assert vec[EXTRA_OFFSET] == 1.0
    assert encode(frame([shot])).vector[EXTRA_OFFSET] == 0.0


def mutate(path: str, value: Any):
    def apply(payload: dict[str, Any]) -> None:
        *parents, last = path.split(".")
        target: Any = payload
        for part in parents:
            target = target[int(part)] if part.isdigit() else target[part]
        target[int(last) if last.isdigit() else last] = value

    return apply


def with_bomb(payload: dict[str, Any]) -> None:
    payload["entities"] = wire(frame([bomb(1, 1, 1, 5)]))["entities"]


MALFORMED = {
    "damage above range": mutate("stats.damage", 1000.5),
    "negative damage": mutate("stats.damage", -0.1),
    "tears above range": mutate("stats.tears_per_second", 60.5),
    "range above": mutate("stats.range", 10001),
    "shot speed above": mutate("stats.shot_speed", 10.1),
    "move speed negative": mutate("stats.move_speed", -1),
    "luck below": mutate("stats.luck", -100.5),
    "luck above": mutate("stats.luck", 101),
    "stat as string": mutate("stats.damage", "3"),
    "nan stat": mutate("stats.luck", float("nan")),
    "unknown stat": mutate("stats.charisma", 1),
    "missing stat": lambda p: p["stats"].pop("luck"),
    "missing stats": lambda p: p.pop("stats"),
    "short tear flags": mutate("tear_flags", [False] * 15),
    "long tear flags": mutate("tear_flags", [False] * 17),
    "tear flag not bool": mutate("tear_flags", [0] * 16),
    "missing tear flags": lambda p: p.pop("tear_flags"),
    "short weapons": mutate("weapons", [True] * 14),
    "long weapons": mutate("weapons", [True] * 16),
    "weapon not bool": mutate("weapons", [1] * 15),
    "missing weapons": lambda p: p.pop("weapons"),
    "oracle data in the frame": mutate("oracle", {"room_clear": True}),
}


@pytest.mark.parametrize("name", MALFORMED)
def test_malformed_schema4_fields_are_protocol_errors(name):
    payload = wire(frame())
    MALFORMED[name](payload)
    with pytest.raises(ProtocolError):
        decoded(payload)


@pytest.mark.parametrize(
    "change",
    [
        {"age_frames": None},
        {"age_frames": -1},
        {"age_frames": BOMB_AGE_MAX + 1},
        {"age_frames": 1.5},
        {"variant": 1, "subtype": 1, "price": 0},
    ],
)
def test_bomb_age_is_required_and_bounded(change):
    payload = wire(frame())
    with_bomb(payload)
    payload["entities"][0].update(change)
    with pytest.raises(ProtocolError):
        decoded(payload)


def test_only_bombs_carry_an_age():
    payload = wire(frame([own(1, 1, 1)]))
    payload["entities"][0]["age_frames"] = 3
    with pytest.raises(ProtocolError):
        decoded(payload)
    payload = wire(frame([enemy(1, 1, 1)]))
    payload["entities"][0]["age_frames"] = 0
    with pytest.raises(ProtocolError):
        decoded(payload)


def test_schema_3_frames_are_refused():
    payload = wire(frame())
    payload["observation_schema_version"] = 3
    for key in ("stats", "tear_flags", "weapons"):
        payload.pop(key)
    with pytest.raises(ProtocolError):
        decoded(payload)


def test_a_full_message_fits_the_wire_limit():
    from isaac_threrisaifuture.observation import MAX_MESSAGE_BYTES

    assert MAX_MESSAGE_BYTES == 131072
