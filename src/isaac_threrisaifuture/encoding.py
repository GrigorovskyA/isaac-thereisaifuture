"""Deterministic fixed-shape policy observation. Pure function of one validated frame."""

import math
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from .entities import (
    COLLECTIBLE_ID_MAX,
    DOOR_SLOTS,
    ENTITY_KINDS,
    LEVEL_GRID_CELLS,
    OBSTACLE_CLASSES,
    TEAR_FLAG_NAMES,
    WEAPON_NAMES,
    Entity,
    EntityFrame,
    EntityKind,
)
from .observation import ProtocolError

# Hypotheses fixed by observation schema version 5; changing one needs a new version.
CAPACITY: dict[EntityKind, int] = {
    "enemy": 16,
    "projectile": 32,
    "obstacle": 24,
    "pickup": 8,
    "own_attack": 16,
    "bomb": 4,
}
# Blocks before the collectible bitmap keep the schema 3 order; schema 4 appends the rest.
BASE_KINDS: tuple[EntityKind, ...] = ("enemy", "projectile", "obstacle", "pickup")
EXTRA_KINDS: tuple[EntityKind, ...] = ("own_attack", "bomb")
STAT_SCALES = (50.0, 30.0, 1000.0, 5.0, 5.0, 10.0)  # damage, tears/s, range, shot, move, luck
BOMB_AGE_SCALE = 120.0
POSITION_SCALE = 1000.0
VELOCITY_SCALE = 20.0
HEART_SCALE = 24.0
PLAYER_FEATURES = 9
INVENTORY_FEATURES = 9
ROOM_TYPES = 32
ROOM_SHAPES = 12
# Type one-hot, stage, stage type, clear, doors, then the room shape one-hot.
ROOM_FEATURES = ROOM_TYPES + 3 + DOOR_SLOTS + ROOM_SHAPES
SLOT_FEATURES = 8  # present, x, y, velocity valid, vx, vy, hp valid, hp fraction
# Pickup slots add a variant class one-hot, subtype/1024 and a shop flag.
VARIANT_CLASSES = (
    "heart",
    "coin",
    "key",
    "bomb",
    "chest",
    "sack",
    "pill",
    "battery",
    "collectible",
    "card",
    "trinket",
    "other",
)
PICKUP_SLOT_FEATURES = SLOT_FEATURES + len(VARIANT_CLASSES) + 2
COUNTER_SCALE = 99.0
SUBTYPE_SCALE = 1024.0
SLOT_WIDTH: dict[EntityKind, int] = {
    "enemy": SLOT_FEATURES,
    "projectile": SLOT_FEATURES,
    "obstacle": SLOT_FEATURES + len(OBSTACLE_CLASSES),  # plus the class one-hot
    "pickup": PICKUP_SLOT_FEATURES,
    "own_attack": SLOT_FEATURES,
    "bomb": SLOT_FEATURES + 1,  # plus age / BOMB_AGE_SCALE
}
INVENTORY_OFFSET = PLAYER_FEATURES
ROOM_OFFSET = INVENTORY_OFFSET + INVENTORY_FEATURES
ENEMY_OFFSET = ROOM_OFFSET + ROOM_FEATURES  # entity blocks follow in BASE_KINDS order
COLLECTIBLE_OFFSET = ENEMY_OFFSET + sum(CAPACITY[k] * SLOT_WIDTH[k] for k in BASE_KINDS)
STATS_OFFSET = COLLECTIBLE_OFFSET + COLLECTIBLE_ID_MAX
TEAR_FLAG_OFFSET = STATS_OFFSET + len(STAT_SCALES)
WEAPON_OFFSET = TEAR_FLAG_OFFSET + len(TEAR_FLAG_NAMES)
EXTRA_OFFSET = WEAPON_OFFSET + len(WEAPON_NAMES)  # then EXTRA_KINDS blocks
MAP_OFFSET = EXTRA_OFFSET + sum(CAPACITY[k] * SLOT_WIDTH[k] for k in EXTRA_KINDS)
# Minimap channels per level grid cell: known, visited, current, boss, treasure, shop, other.
MAP_CHANNELS = 7
OFF_GRID_OFFSET = MAP_OFFSET + LEVEL_GRID_CELLS * MAP_CHANNELS
STALL_OFFSET = OFF_GRID_OFFSET + 1  # idle time / stall limit; the last element
OBSERVATION_SIZE = STALL_OFFSET + 1
GRID_WIDTH = 13
# (row, column) offsets of a room's cells from its anchor, by room shape 1..12.
SHAPE_CELLS: dict[int, tuple[tuple[int, int], ...]] = {
    1: ((0, 0),),  # 1x1
    2: ((0, 0),),  # IH
    3: ((0, 0),),  # IV
    4: ((0, 0), (1, 0)),  # 1x2
    5: ((0, 0), (1, 0)),  # IIV
    6: ((0, 0), (0, 1)),  # 2x1
    7: ((0, 0), (0, 1)),  # IIH
    8: ((0, 0), (0, 1), (1, 0), (1, 1)),  # 2x2
    9: ((0, 1), (1, 0), (1, 1)),  # LTL
    10: ((0, 0), (1, 0), (1, 1)),  # LTR
    11: ((0, 0), (0, 1), (1, 1)),  # LBL
    12: ((0, 0), (0, 1), (1, 0)),  # LBR
}
assert set(SHAPE_CELLS) == set(range(1, ROOM_SHAPES + 1))
BOSS_ROOM, TREASURE_ROOM, SHOP_ROOM, DEFAULT_ROOM = 5, 4, 2, 1
assert set(BASE_KINDS + EXTRA_KINDS) == set(ENTITY_KINDS)


@dataclass(frozen=True)
class EncodedObservation:
    vector: NDArray[np.float32]
    overflow: dict[EntityKind, int] = field(default_factory=dict)
    clipped_values: int = 0


class _Clip:
    def __init__(self) -> None:
        self.count = 0

    def __call__(self, value: float, scale: float) -> float:
        scaled = value / scale
        if abs(scaled) > 1.0:
            self.count += 1
        return math.copysign(1.0, scaled) if abs(scaled) > 1.0 else scaled


_VARIANT_CLASS: dict[int, str] = {
    10: "heart",
    20: "coin",
    30: "key",
    40: "bomb",
    41: "bomb",
    **dict.fromkeys((*range(50, 61), 340, 360, 390), "chest"),
    69: "sack",
    70: "pill",
    90: "battery",
    100: "collectible",
    300: "card",
    350: "trinket",
}


def variant_class(variant: int) -> int:
    """Index into VARIANT_CLASSES; unlisted variants fall in the last class, 'other'."""
    return VARIANT_CLASSES.index(_VARIANT_CLASS.get(variant, "other"))


def _order(entity: Entity) -> tuple[float, int, int]:
    p = entity.position
    return (p.x * p.x + p.y * p.y, entity.spawn_generation, entity.entity_id)


def _encode_inventory(vector: NDArray[np.float32], frame: EntityFrame) -> None:
    inv = frame.inventory
    base = INVENTORY_OFFSET
    # Counters above 99 saturate; the raw range check already happened at decode.
    vector[base] = min(inv.coins / COUNTER_SCALE, 1.0)
    vector[base + 1] = min(inv.bombs / COUNTER_SCALE, 1.0)
    vector[base + 2] = min(inv.keys / COUNTER_SCALE, 1.0)
    vector[base + 3] = float(inv.active_item > 0)
    vector[base + 4] = inv.active_item / COLLECTIBLE_ID_MAX
    if inv.active_max_charge > 0:  # a battery can overcharge past the maximum
        vector[base + 5] = min(inv.active_charge / inv.active_max_charge, 1.0)
    vector[base + 6] = float(inv.card > 0)
    vector[base + 7] = float(inv.pill > 0)
    vector[base + 8] = float(inv.trinket > 0)


def _encode_room(vector: NDArray[np.float32], frame: EntityFrame) -> None:
    room = frame.room
    base = ROOM_OFFSET
    vector[base + room.type] = 1.0
    vector[base + ROOM_TYPES] = room.stage / 15.0
    vector[base + ROOM_TYPES + 1] = room.stage_type / 7.0
    vector[base + ROOM_TYPES + 2] = float(room.clear)
    for slot, is_open in enumerate(room.doors):
        vector[base + ROOM_TYPES + 3 + slot] = float(is_open)
    vector[base + ROOM_TYPES + 3 + DOOR_SLOTS + room.shape - 1] = 1.0


def _encode_map(vector: NDArray[np.float32], frame: EntityFrame) -> None:
    for room in frame.map:
        row, col = divmod(room.grid_index, GRID_WIDTH)
        for dr, dc in SHAPE_CELLS[room.shape]:
            if row + dr >= GRID_WIDTH or col + dc >= GRID_WIDTH:
                continue  # beyond the 13 x 13 grid: dropped, never wrapped
            base = MAP_OFFSET + ((row + dr) * GRID_WIDTH + col + dc) * MAP_CHANNELS
            vector[base] = 1.0
            vector[base + 1] = float(room.visited)
            vector[base + 2] = float(room.current)
            kind = room.room_type
            if kind is None or kind == DEFAULT_ROOM:
                continue
            if kind == BOSS_ROOM:
                vector[base + 3] = 1.0
            elif kind == TREASURE_ROOM:
                vector[base + 4] = 1.0
            elif kind == SHOP_ROOM:
                vector[base + 5] = 1.0
            else:
                vector[base + 6] = 1.0
    vector[OFF_GRID_OFFSET] = float(frame.map_current_off_grid)


def _encode_pickup(vector: NDArray[np.float32], base: int, entity: Entity) -> None:
    assert entity.variant is not None and entity.subtype is not None and entity.price is not None
    vector[base + variant_class(entity.variant)] = 1.0
    vector[base + len(VARIANT_CLASSES)] = entity.subtype / SUBTYPE_SCALE
    vector[base + len(VARIANT_CLASSES) + 1] = float(entity.price != 0)


def encode(frame: EntityFrame, *, stall_fraction: float = 0.0) -> EncodedObservation:
    """Nearest-first, fixed capacity; zero slots are told apart by the presence bit.

    `stall_fraction` is the stall watchdog's idle time over its limit, clipped to [0, 1].
    """
    if not isinstance(frame, EntityFrame):
        raise ProtocolError("Only a validated policy EntityFrame can be encoded")
    clip = _Clip()
    vector = np.zeros(OBSERVATION_SIZE, dtype=np.float32)
    player = frame.player_position
    vel = frame.player_velocity
    vector[0] = clip(player.x, POSITION_SCALE)
    vector[1] = clip(player.y, POSITION_SCALE)
    if vel is not None:
        vector[2] = 1.0
        vector[3] = clip(vel.x, VELOCITY_SCALE)
        vector[4] = clip(vel.y, VELOCITY_SCALE)
    h = frame.health
    vector[5] = min(h.red_half_hearts / HEART_SCALE, 1.0)
    vector[6] = min(h.max_red_half_hearts / HEART_SCALE, 1.0)
    vector[7] = min(h.soul_half_hearts / HEART_SCALE, 1.0)
    vector[8] = min(h.bone_containers / HEART_SCALE, 1.0)
    _encode_inventory(vector, frame)
    _encode_room(vector, frame)
    _encode_map(vector, frame)
    vector[STALL_OFFSET] = min(max(stall_fraction, 0.0), 1.0)
    overflow: dict[EntityKind, int] = dict(frame.source_overflow)
    for collectible in frame.collectibles:
        vector[COLLECTIBLE_OFFSET + collectible - 1] = 1.0
    stats = frame.stats
    raw_stats = (
        stats.damage,
        stats.tears_per_second,
        stats.range,
        stats.shot_speed,
        stats.move_speed,
        stats.luck,
    )
    for i, (value, scale) in enumerate(zip(raw_stats, STAT_SCALES, strict=True)):
        vector[STATS_OFFSET + i] = clip(value, scale)
    for i, flag in enumerate(frame.tear_flags):
        vector[TEAR_FLAG_OFFSET + i] = float(flag)
    for i, flag in enumerate(frame.weapons):
        vector[WEAPON_OFFSET + i] = float(flag)
    offset = ENEMY_OFFSET
    for kind in (*BASE_KINDS, *EXTRA_KINDS):
        if kind == "own_attack":
            offset = EXTRA_OFFSET
        capacity = CAPACITY[kind]
        width = SLOT_WIDTH[kind]
        ordered = sorted((e for e in frame.entities if e.kind == kind), key=_order)
        if len(ordered) > capacity:
            overflow[kind] = overflow.get(kind, 0) + len(ordered) - capacity
        for slot, entity in enumerate(ordered[:capacity]):
            base = offset + slot * width
            vector[base] = 1.0
            vector[base + 1] = clip(entity.position.x, POSITION_SCALE)
            vector[base + 2] = clip(entity.position.y, POSITION_SCALE)
            if entity.velocity is not None:
                vector[base + 3] = 1.0
                vector[base + 4] = clip(entity.velocity.x, VELOCITY_SCALE)
                vector[base + 5] = clip(entity.velocity.y, VELOCITY_SCALE)
            if entity.hp is not None and entity.max_hp is not None:
                vector[base + 6] = 1.0
                vector[base + 7] = entity.hp / entity.max_hp
            if kind == "obstacle":
                assert entity.obstacle_class is not None
                vector[base + SLOT_FEATURES + OBSTACLE_CLASSES.index(entity.obstacle_class)] = 1.0
            if kind == "pickup":
                _encode_pickup(vector, base + SLOT_FEATURES, entity)
            if kind == "bomb":
                assert entity.age_frames is not None
                vector[base + SLOT_FEATURES] = clip(entity.age_frames, BOMB_AGE_SCALE)
        offset += capacity * width
    return EncodedObservation(vector, overflow, clip.count)
