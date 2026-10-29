"""OFFLINE schema 5 contract: typed obstacles, room shape, minimap, stall clock, size."""

import json
from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest
from pydantic import ValidationError
from synthetic import SESSION, door, frame, oracle_metrics, room_facts
from test_entity_transport import entity_snapshot

from isaac_threrisaifuture.encoding import (
    CAPACITY,
    COLLECTIBLE_OFFSET,
    DOOR_FEATURES,
    ENEMY_OFFSET,
    GRID_WIDTH,
    MAP_CHANNELS,
    MAP_OFFSET,
    OBSERVATION_SIZE,
    OFF_GRID_OFFSET,
    ROOM_CLASSES,
    ROOM_FEATURES,
    ROOM_OFFSET,
    ROOM_TYPES,
    SLOT_FEATURES,
    SLOT_WIDTH,
    STALL_OFFSET,
    VISITED_COLS,
    VISITED_OFFSET,
    VISITED_ROWS,
    encode,
)
from isaac_threrisaifuture.entities import (
    ENTITY_CAPS,
    FRAME_SCHEMA_VERSION,
    MAX_ENTITIES,
    MAX_MAP_ROOMS,
    OBSERVATION_SCHEMA_VERSION,
    OBSTACLE_CLASSES,
    Entity,
    EntityFrame,
    MapRoom,
    Vec,
)
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episodes import Scenario
from isaac_threrisaifuture.live import LiveBackend
from isaac_threrisaifuture.live_wire import LiveOracle, LiveSnapshot
from isaac_threrisaifuture.observation import MAX_MESSAGE_BYTES, ProtocolError, decode
from isaac_threrisaifuture.sim import SyntheticRoomBackend
from isaac_threrisaifuture.stall_watchdog import StallWatchdog

# Entity blocks follow in the order enemy, projectile, obstacle, pickup.
OBSTACLE_OFFSET = ENEMY_OFFSET + sum(CAPACITY[k] * SLOT_WIDTH[k] for k in ("enemy", "projectile"))


def wire(item: EntityFrame) -> dict[str, Any]:
    return json.loads(item.model_dump_json())


def decoded(payload: dict[str, Any]) -> EntityFrame:
    return decode(json.dumps(payload).encode(), EntityFrame, 131072)


def obstacle(entity_id: int, x: float, y: float, cls: str | None = "rock") -> Entity:
    return Entity(
        kind="obstacle",
        entity_id=entity_id,
        spawn_generation=0,
        position=Vec(x=x, y=y),
        obstacle_class=cls,  # type: ignore[arg-type]
    )


def room(grid_index, shape=1, *, visited=False, current=False, room_type=None) -> MapRoom:
    return MapRoom(
        grid_index=grid_index, shape=shape, visited=visited, current=current, room_type=room_type
    )


def cells(vector: np.ndarray) -> dict[tuple[int, int], list[float]]:
    """Non-empty minimap cells by (row, column) with their channels."""
    block = vector[MAP_OFFSET:OFF_GRID_OFFSET].reshape(GRID_WIDTH * GRID_WIDTH, MAP_CHANNELS)
    return {
        divmod(i, GRID_WIDTH): [float(v) for v in row] for i, row in enumerate(block) if row.any()
    }


# --- layout ----------------------------------------------------------------------------


def test_layout_is_pinned_to_its_computed_value():
    assert (
        FRAME_SCHEMA_VERSION == 6
        and EntityFrame.model_fields["observation_schema_version"].default == 6
        and OBSERVATION_SCHEMA_VERSION == 8
    )
    assert len(OBSTACLE_CLASSES) == 16 and SLOT_WIDTH["obstacle"] == SLOT_FEATURES + 16
    assert CAPACITY["obstacle"] == 64 and MAX_ENTITIES == 256
    assert ROOM_FEATURES == ROOM_TYPES + 3 + 8 * DOOR_FEATURES + 12
    assert MAP_OFFSET + 169 * MAP_CHANNELS == OFF_GRID_OFFSET
    assert STALL_OFFSET == OFF_GRID_OFFSET + 1 and MAP_CHANNELS == 3 + len(ROOM_CLASSES)
    assert VISITED_OFFSET == STALL_OFFSET + 1
    assert OBSERVATION_SIZE == VISITED_OFFSET + VISITED_COLS * VISITED_ROWS == 9762
    assert encode(frame()).vector.shape == (OBSERVATION_SIZE,)
    assert COLLECTIBLE_OFFSET > ROOM_OFFSET + ROOM_FEATURES


# --- validation ------------------------------------------------------------------------


def test_obstacle_needs_a_class_and_other_kinds_must_not_have_one():
    with pytest.raises(ValidationError):
        obstacle(1, 0, 0, None)
    with pytest.raises(ValidationError):
        Entity(
            kind="enemy",
            entity_id=1,
            spawn_generation=0,
            position=Vec(x=0, y=0),
            obstacle_class="rock",
        )
    with pytest.raises(ValidationError):
        obstacle(1, 0, 0, "lava")


def test_missing_obstacle_class_fails_decoding():
    payload = wire(frame([obstacle(1, 10, 0)]))
    payload["entities"][0].pop("obstacle_class")
    with pytest.raises(ProtocolError):
        decoded(payload)


def test_map_validation():
    with pytest.raises(ValidationError):
        frame(map=[room(5), room(5, visited=True)])
    with pytest.raises(ValidationError):
        frame(map=[room(5, current=True), room(6, current=True)])
    with pytest.raises(ValidationError):
        frame(map=[room(5, current=True)], map_current_off_grid=True)
    with pytest.raises(ValidationError):
        frame(map=[room(i) for i in range(MAX_MAP_ROOMS + 1)])
    with pytest.raises(ValidationError):
        room(169)
    with pytest.raises(ValidationError):
        room(5, shape=13)
    with pytest.raises(ValidationError):
        frame(room=room_facts(shape=0))
    ok = frame(map=[room(5, current=True)], map_current_off_grid=False)
    assert decoded(wire(ok)) == ok
    off = frame(map=[room(5)], map_current_off_grid=True)
    assert decoded(wire(off)) == off


# --- encoder ---------------------------------------------------------------------------


def test_obstacle_class_one_hot_follows_the_base_slot_features():
    items = [obstacle(i + 1, 10 * (i + 1), 0, cls) for i, cls in enumerate(OBSTACLE_CLASSES)]
    vector = encode(frame(items)).vector
    width = SLOT_WIDTH["obstacle"]
    for slot, cls in enumerate(OBSTACLE_CLASSES):
        base = OBSTACLE_OFFSET + slot * width
        assert vector[base] == 1.0
        hot = vector[base + SLOT_FEATURES : base + width]
        assert hot.sum() == 1.0 and hot[OBSTACLE_CLASSES.index(cls)] == 1.0
    empty = OBSTACLE_OFFSET + len(items) * width
    assert not vector[empty : empty + width].any()


def test_room_shape_one_hot_comes_after_the_existing_room_features():
    for shape in (1, 8, 12):
        vector = encode(frame(room=room_facts(shape=shape))).vector
        block = vector[ROOM_OFFSET : ROOM_OFFSET + ROOM_FEATURES]
        shape_part = block[ROOM_TYPES + 3 + 8 * DOOR_FEATURES :]
        assert len(shape_part) == 12 and shape_part.sum() == 1.0
        assert shape_part[shape - 1] == 1.0
        assert not block[ROOM_TYPES + 3 : ROOM_TYPES + 3 + 8 * DOOR_FEATURES].any()  # no doors


def test_map_cells_for_each_shape_and_dropped_overflow():
    # grid index = row * 13 + column; the start room sits at (6, 6) = 84.
    cases = {
        1: ([(6, 6)], 84),
        2: ([(6, 6)], 84),
        3: ([(6, 6)], 84),
        4: ([(6, 6), (7, 6)], 84),
        5: ([(6, 6), (7, 6)], 84),
        6: ([(6, 6), (6, 7)], 84),
        7: ([(6, 6), (6, 7)], 84),
        8: ([(6, 6), (6, 7), (7, 6), (7, 7)], 84),
        9: ([(6, 7), (7, 6), (7, 7)], 84),  # LTL
        10: ([(6, 6), (7, 6), (7, 7)], 84),  # LTR
        11: ([(6, 6), (6, 7), (7, 7)], 84),  # LBL
        12: ([(6, 6), (6, 7), (7, 6)], 84),  # LBR
    }
    for shape, (expected, anchor) in cases.items():
        vector = encode(frame(map=[room(anchor, shape, visited=True, current=True)])).vector
        found = cells(vector)
        assert sorted(found) == sorted(expected), shape
        assert all(row == [1.0, 1.0, 1.0] + [0.0] * len(ROOM_CLASSES) for row in found.values())


def test_cells_beyond_the_grid_are_dropped_not_wrapped():
    row5_col12 = 5 * 13 + 12
    found = cells(encode(frame(map=[room(row5_col12, 6)])).vector)  # 2x1 at the last column
    assert list(found) == [(5, 12)]  # the overflow cell is gone, not at (6, 0)
    last = 12 * 13 + 12
    assert list(cells(encode(frame(map=[room(last, 8)])).vector)) == [(12, 12)]
    bottom = 12 * 13 + 3
    assert sorted(cells(encode(frame(map=[room(bottom, 4)])).vector)) == [(12, 3)]
    assert sorted(cells(encode(frame(map=[room(bottom, 8)])).vector)) == [(12, 3), (12, 4)]


def test_room_class_channels_and_unknown_type():
    def row(*hot: str, visited=False, current=False) -> list[float]:
        classes = [1.0 if name in hot else 0.0 for name in ROOM_CLASSES]
        return [1.0, float(visited), float(current), *classes]

    rooms = [
        room(10, visited=True, room_type=1),
        room(11, room_type=5),
        room(12, room_type=4),
        room(13, room_type=2),
        room(14, room_type=7),
        room(15, visited=True, current=True, room_type=None),
        room(16, room_type=0),
        room(17, room_type=29),
        room(18, room_type=14),
        room(19, room_type=17),
        room(20, room_type=24),
    ]
    found = cells(encode(frame(map=rooms)).vector)
    by_index = {r * 13 + c: values for (r, c), values in found.items()}
    assert by_index[10] == row("normal", visited=True)
    assert by_index[11] == row("boss")
    assert by_index[12] == row("treasure")
    assert by_index[13] == row("shop")
    assert by_index[14] == by_index[17] == row("secret")  # secret and ultra secret
    assert by_index[15] == row(visited=True, current=True)  # type hidden: no class channel
    assert by_index[16] == row("special")  # an unlisted type is "special"
    assert by_index[18] == row("devil_angel") and by_index[19] == row("challenge")
    assert by_index[20] == row("special")  # planetarium


def test_off_grid_flag_and_stall_clock_precede_the_visited_block():
    assert OFF_GRID_OFFSET + 1 == STALL_OFFSET and STALL_OFFSET + 1 == VISITED_OFFSET
    vector = encode(frame(map_current_off_grid=True)).vector
    assert vector[OFF_GRID_OFFSET] == 1.0 and vector[STALL_OFFSET] == 0.0
    assert encode(frame()).vector[OFF_GRID_OFFSET] == 0.0


def test_stall_fraction_is_written_and_clipped():
    base = encode(frame()).vector
    for given, written in ((0.0, 0.0), (0.5, 0.5), (1.0, 1.0), (7.0, 1.0), (-0.3, 0.0)):
        vector = encode(frame(), stall_fraction=given).vector
        assert vector[STALL_OFFSET] == pytest.approx(written)
        assert np.array_equal(vector[:STALL_OFFSET], base[:STALL_OFFSET])
        assert np.all(np.abs(vector) <= 1.0)


# --- stall clock sources ---------------------------------------------------------------


def test_live_backend_stall_fraction_with_and_without_a_watchdog():
    backend = LiveBackend(MagicMock())
    assert backend.stall_fraction == 0.0
    now = [0.0]
    backend.watchdog = StallWatchdog(90.0, clock=lambda: now[0])
    backend.watchdog.observe(active=True)
    assert backend.stall_fraction == 0.0
    for _ in range(45):  # one second per snapshot; the watchdog caps long gaps
        now[0] += 1.0
        backend.watchdog.observe(active=True)
    assert backend.stall_fraction == pytest.approx(0.5)
    backend.watchdog.observe(active=True, progress=True)
    assert backend.stall_fraction == 0.0
    backend.watchdog._idle = 200.0  # past the limit: clipped
    assert backend.stall_fraction == 1.0


def test_env_passes_the_backend_stall_fraction_to_the_encoder():
    class Stalling(SyntheticRoomBackend):
        stall_fraction = 0.25

    toy = Scenario("toy", "train", 1, 90, enemy_count=1, enemy_hp=7.0)
    env = IsaacCombatEnv(Stalling(), [toy])
    obs, _ = env.reset(seed=1)
    assert obs[STALL_OFFSET] == pytest.approx(0.25)
    plain = IsaacCombatEnv(SyntheticRoomBackend(), [toy])
    assert plain.reset(seed=1)[0][STALL_OFFSET] == 0.0


# --- oracle metrics --------------------------------------------------------------------


def test_oracle_metrics_are_required_and_never_in_the_frame():
    raw = entity_snapshot(SESSION, 1)
    raw["oracle"] = {
        "room_clear": False,
        "player_dead": False,
        "enemies": [],
        "enemy_overflow": 0,
        "room_index": 84,
        **oracle_metrics(own_bomb=2),
    }
    snap = LiveSnapshot.model_validate_json(json.dumps(raw))
    assert snap.oracle is not None and snap.oracle.player_hits.own_bomb == 2
    for missing in ("kills", "player_hits"):
        broken = {**raw, "oracle": {k: v for k, v in raw["oracle"].items() if k != missing}}
        with pytest.raises(ValidationError):
            LiveSnapshot.model_validate_json(json.dumps(broken))
    partial = {**raw["oracle"], "player_hits": {"enemy": 1}}
    with pytest.raises(ValidationError):
        LiveSnapshot.model_validate_json(json.dumps({**raw, "oracle": partial}))
    assert "kills" in LiveOracle.model_fields
    assert "kills" not in EntityFrame.model_fields
    assert "player_hits" not in EntityFrame.model_fields


# --- message size ----------------------------------------------------------------------


ENEMY_FACT_NAMES = (
    "npc_type",
    "npc_variant",
    "npc_max_hp",
    "boss",
    "champion",
    "flying",
    "invulnerable",
)


def test_worst_case_snapshot_fits_the_message_limit():
    caps = dict(ENTITY_CAPS)
    assert sum(caps.values()) == MAX_ENTITIES
    items: list[Entity] = []
    for kind, count in caps.items():
        for i in range(count):
            fields: dict[str, Any] = dict(
                kind=kind,
                entity_id=2**53 - 1 - i,
                spawn_generation=2**53 - 1,
                position=Vec(x=-99999.123456789, y=-99999.123456789),
                velocity=Vec(x=-99999.123456789, y=-99999.123456789),
                hp=123456.789012345,
                max_hp=234567.890123456,
            )
            if kind == "pickup":
                fields.update(variant=1023, subtype=1024, price=-1000)
            if kind == "enemy":
                fields.update(
                    npc_type=1000,
                    npc_variant=4095,
                    npc_max_hp=999999.999,
                    boss=True,
                    champion=True,
                    flying=True,
                    invulnerable=True,
                )
            if kind == "bomb":
                fields.update(age_frames=10000)
            if kind == "obstacle":
                fields.update(obstacle_class="pressure_plate")
            if kind == "interactable":
                fields.update(interactable_class="blood_donation")
            items.append(Entity(**fields))
    big = frame(
        items,
        collectibles=list(range(1, 257)),
        collectible_overflow=768,
        source_overflow={k: 2**53 - 1 for k in caps},
        map=[room(i, 12, visited=True, current=i == 0, room_type=31) for i in range(64)],
        room=room_facts(
            shape=12,
            doors=[door(target_type=31, visited=True, locked=True)] * 8,
        ),
    )
    raw = entity_snapshot(SESSION, 1)
    raw["entity_frame"] = wire(big)
    raw["entity_frame"]["session_id"] = SESSION
    # The observer sends the enemy identity facts on enemies only and omits them elsewhere.
    for item in raw["entity_frame"]["entities"]:
        if item["kind"] != "enemy":
            for name in ENEMY_FACT_NAMES:
                del item[name]
    raw["oracle"] = {
        "room_clear": True,
        "player_dead": False,
        "enemies": [
            {"entity_id": 2**53 - 1 - i, "hp": 123456.789012345, "max_hp": 234567.890123456}
            for i in range(64)
        ],
        "enemy_overflow": 2**53 - 1,
        "room_index": -64,
        "kills": 2**53 - 1,
        "killed": [2**53 - 1] * 16,
        "doors": [
            {"slot": i, "x": -99999.123456, "y": -99999.654321, "open": True, "unexplored": True}
            for i in range(8)
        ],
        "player_hits": dict.fromkeys(
            ("enemy", "projectile", "own_bomb", "explosion", "spikes", "fire", "creep", "other"),
            2**53 - 1,
        ),
    }
    message = json.dumps(raw, separators=(",", ":")).encode() + b"\n"
    # Pydantic would validate the whole thing only if the outer snapshot agrees with it;
    # the size is what is pinned here, so also check that the frame itself decodes.
    compact = json.dumps(raw["entity_frame"], separators=(",", ":")).encode()
    assert decode(compact, EntityFrame, MAX_MESSAGE_BYTES) == big
    margin = MAX_MESSAGE_BYTES - len(message)
    print(f"worst-case python message: {len(message)} bytes, margin {margin}")
    assert margin >= 16384
