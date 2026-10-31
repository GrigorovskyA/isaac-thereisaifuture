"""Deterministic fixed-shape policy observation. Pure function of one validated frame."""

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from .entities import (
    COLLECTIBLE_ID_MAX,
    COLLECTIBLE_VARIANT,
    DOOR_SLOTS,
    ENTITY_CAPS,
    ENTITY_KINDS,
    INTERACTABLE_CLASSES,
    ITEM_QUALITY_MAX,
    ITEM_TAGS,
    ITEM_TYPES,
    LEVEL_GRID_CELLS,
    OBSTACLE_CLASSES,
    TEAR_FLAG_NAMES,
    WEAPON_NAMES,
    Entity,
    EntityFrame,
    EntityKind,
)
from .observation import ProtocolError

# Hypotheses fixed by observation schema version 9; changing one needs a new version. The
# encoder capacity equals the observer cap, so the encoder never drops what the wire carried.
CAPACITY: dict[EntityKind, int] = dict(ENTITY_CAPS)
# Blocks before the collectible bitmap keep the schema 3 order; schema 4 appends the rest.
BASE_KINDS: tuple[EntityKind, ...] = ("enemy", "projectile", "obstacle", "pickup")
EXTRA_KINDS: tuple[EntityKind, ...] = ("own_attack", "bomb", "interactable")
STAT_SCALES = (50.0, 30.0, 1000.0, 5.0, 5.0, 10.0)  # damage, tears/s, range, shot, move, luck
BOMB_AGE_SCALE = 120.0
POSITION_SCALE = 1000.0
VELOCITY_SCALE = 20.0
HEART_SCALE = 24.0
PLAYER_FEATURES = 9
# Item identity (schema 9): a one-hot of the hashed collectible ID, like the enemy buckets, plus
# ItemConfig facts. Distinct items may share a bucket; the first layer learns one embedding each.
ITEM_BUCKETS = 64
ITEM_TYPE_ONEHOT = tuple(t for t in ITEM_TYPES if t != "unknown")  # passive, active, familiar
TAG_FEATURES = len(ITEM_TAGS)
# Pedestal item block: quality / 4, type one-hot, max charges / 12 (clipped), tag bits, bucket.
ITEM_FEATURES = 1 + len(ITEM_TYPE_ONEHOT) + 1 + TAG_FEATURES + ITEM_BUCKETS
CHARGE_SCALE = 12.0
# Counters, then the active item block: quality / 4, tag bits, bucket one-hot (all zero if none).
INVENTORY_BASE_FEATURES = 9
INVENTORY_FEATURES = INVENTORY_BASE_FEATURES + 1 + TAG_FEATURES + ITEM_BUCKETS
ROOM_TYPES = 32
ROOM_SHAPES = 12
# Room types grouped into classes for doors and the minimap. Types by RoomType value; a type
# not listed here (miniboss, library, planetarium, dice, error, ...) is in "special".
ROOM_CLASSES = (
    "normal",
    "boss",
    "treasure",
    "shop",
    "secret",
    "curse",
    "challenge",
    "devil_angel",
    "sacrifice",
    "arcade",
    "special",
)
_ROOM_CLASS: dict[int, str] = {
    1: "normal",
    5: "boss",
    4: "treasure",
    2: "shop",
    **dict.fromkeys((7, 8, 29), "secret"),  # secret, super secret, ultra secret
    10: "curse",
    **dict.fromkeys((11, 17), "challenge"),  # challenge (and boss challenge), boss rush
    **dict.fromkeys((14, 15), "devil_angel"),
    13: "sacrifice",
    9: "arcade",
}
# Per door slot: exists, open, locked, target visited, then the target room class one-hot
# (all zero when the target type is unknown).
DOOR_FEATURES = 4 + len(ROOM_CLASSES)
# Type one-hot, stage, stage type, clear, doors, then the room shape one-hot.
ROOM_FEATURES = ROOM_TYPES + 3 + DOOR_SLOTS * DOOR_FEATURES + ROOM_SHAPES
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
# Enemy slots add an identity block: identity valid, boss, champion, flying, invulnerable,
# log1p(max HP) / log1p(ENEMY_HP_SCALE), then a one-hot of the hashed (type, variant) bucket.
# A one-hot into the first linear layer is a learned embedding per kind. Distinct kinds may share
# a bucket; a floor shows about 20 kinds, so collisions are rare and accepted.
IDENTITY_BUCKETS = 64
ENEMY_HP_SCALE = 10000.0
ENEMY_IDENTITY_FEATURES = 6 + IDENTITY_BUCKETS
PICKUP_SLOT_FEATURES = SLOT_FEATURES + len(VARIANT_CLASSES) + 2 + ITEM_FEATURES
COUNTER_SCALE = 99.0
SUBTYPE_SCALE = 1024.0
SLOT_WIDTH: dict[EntityKind, int] = {
    "enemy": SLOT_FEATURES + ENEMY_IDENTITY_FEATURES,
    "projectile": SLOT_FEATURES,
    "obstacle": SLOT_FEATURES + len(OBSTACLE_CLASSES),  # plus the class one-hot
    "pickup": PICKUP_SLOT_FEATURES,
    "own_attack": SLOT_FEATURES,
    "bomb": SLOT_FEATURES + 1,  # plus age / BOMB_AGE_SCALE
    "interactable": SLOT_FEATURES + len(INTERACTABLE_CLASSES),  # plus the class one-hot
}
INVENTORY_OFFSET = PLAYER_FEATURES
ROOM_OFFSET = INVENTORY_OFFSET + INVENTORY_FEATURES
ENEMY_OFFSET = ROOM_OFFSET + ROOM_FEATURES  # entity blocks follow in BASE_KINDS order
# Start of each entity kind's slot block: the base kinds follow the room block, the extra kinds
# follow the held tag counts.
ENTITY_OFFSETS: dict[EntityKind, int] = {
    kind: ENEMY_OFFSET + sum(CAPACITY[k] * SLOT_WIDTH[k] for k in BASE_KINDS[:i])
    for i, kind in enumerate(BASE_KINDS)
}
COLLECTIBLE_OFFSET = ENEMY_OFFSET + sum(CAPACITY[k] * SLOT_WIDTH[k] for k in BASE_KINDS)
STATS_OFFSET = COLLECTIBLE_OFFSET + COLLECTIBLE_ID_MAX
TEAR_FLAG_OFFSET = STATS_OFFSET + len(STAT_SCALES)
WEAPON_OFFSET = TEAR_FLAG_OFFSET + len(TEAR_FLAG_NAMES)
HELD_TAG_OFFSET = WEAPON_OFFSET + len(WEAPON_NAMES)  # held collectibles per tag / 3, clipped
HELD_TAG_SCALE = 3.0  # three items complete a transformation
EXTRA_OFFSET = HELD_TAG_OFFSET + TAG_FEATURES  # then EXTRA_KINDS blocks
ENTITY_OFFSETS.update(
    (kind, EXTRA_OFFSET + sum(CAPACITY[k] * SLOT_WIDTH[k] for k in EXTRA_KINDS[:i]))
    for i, kind in enumerate(EXTRA_KINDS)
)
MAP_OFFSET = EXTRA_OFFSET + sum(CAPACITY[k] * SLOT_WIDTH[k] for k in EXTRA_KINDS)
# Minimap channels per level grid cell: known, visited, current, then the room class one-hot
# (all zero while the room's type is hidden).
MAP_CHANNELS = 3 + len(ROOM_CLASSES)
OFF_GRID_OFFSET = MAP_OFFSET + LEVEL_GRID_CELLS * MAP_CHANNELS
STALL_OFFSET = OFF_GRID_OFFSET + 1  # idle time / stall limit
# Visited cells of the current room (schema 6): one cell per 40 px floor tile, counted from the
# room interior corner at world (60, 140), so cells line up with the game's tiles. A 2x2 room is
# 26 x 14 tiles; smaller rooms and L-shapes use the same grid from the same corner. Natively a
# 1x1 room spans x 60..580 and y 140..420; positions in door frames are clipped to the edge cells.
CELL_SIZE = 40.0  # the novelty cell size of reward v4-v9
ROOM_ORIGIN = (60.0, 140.0)
VISITED_COLS, VISITED_ROWS = 26, 14
VISITED_OFFSET = STALL_OFFSET + 1  # row-major rows x columns; the last block
OBSERVATION_SIZE = VISITED_OFFSET + VISITED_COLS * VISITED_ROWS
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
# Interior (width, height) in 40 px tiles of a room's bounding box, by room shape 1..12:
# 1x1, IH, IV, 1x2, IIV, 2x1, IIH, 2x2, then the four L shapes (2x2 bounding box).
SHAPE_TILES: dict[int, tuple[int, int]] = {
    1: (13, 7),
    2: (13, 3),
    3: (5, 7),
    4: (13, 14),
    5: (5, 14),
    6: (26, 7),
    7: (26, 3),
    8: (26, 14),
    **dict.fromkeys((9, 10, 11, 12), (26, 14)),
}
assert set(SHAPE_TILES) == set(SHAPE_CELLS)
assert set(BASE_KINDS + EXTRA_KINDS) == set(ENTITY_KINDS)

# Kind of every observation index, in encoding order. Only "continuous" features are normalized
# by the learner (`observation_normalization: continuous_only`); "binary" flags and "one_hot"
# groups (at most one 1, all zero when unknown) reach the policy as the encoder wrote them.
FeatureKind = Literal["continuous", "binary", "one_hot"]


@dataclass(frozen=True)
class FeatureBlock:
    name: str
    offset: int
    size: int
    kind: FeatureKind


def _feature_blocks() -> tuple[FeatureBlock, ...]:
    blocks: list[FeatureBlock] = []

    def add(name: str, size: int, kind: FeatureKind) -> None:
        end = blocks[-1].offset + blocks[-1].size if blocks else 0
        blocks.append(FeatureBlock(name, end, size, kind))

    def anchor(offset: int) -> None:  # the table must follow the layout constants
        assert blocks[-1].offset + blocks[-1].size == offset

    def item(prefix: str) -> None:  # pedestal item block, without its quality
        add(f"{prefix}.type", len(ITEM_TYPE_ONEHOT), "one_hot")
        add(f"{prefix}.max_charges", 1, "continuous")
        add(f"{prefix}.tags", TAG_FEATURES, "binary")
        add(f"{prefix}.bucket", ITEM_BUCKETS, "one_hot")

    def slots(kind: EntityKind) -> None:
        anchor(ENTITY_OFFSETS[kind])
        for slot in range(CAPACITY[kind]):
            at = f"{kind}[{slot}]"
            add(f"{at}.present", 1, "binary")
            add(f"{at}.position", 2, "continuous")
            add(f"{at}.velocity_valid", 1, "binary")
            add(f"{at}.velocity", 2, "continuous")
            add(f"{at}.hp_valid", 1, "binary")
            add(f"{at}.hp_fraction", 1, "continuous")
            if kind == "enemy":
                add(f"{at}.identity_flags", 5, "binary")  # valid, boss, champion, flying, invuln.
                add(f"{at}.max_hp", 1, "continuous")
                add(f"{at}.identity_bucket", IDENTITY_BUCKETS, "one_hot")
            if kind == "obstacle":
                add(f"{at}.class", len(OBSTACLE_CLASSES), "one_hot")
            if kind == "pickup":
                add(f"{at}.variant_class", len(VARIANT_CLASSES), "one_hot")
                add(f"{at}.subtype", 1, "continuous")
                add(f"{at}.shop", 1, "binary")
                add(f"{at}.item_quality", 1, "continuous")
                item(f"{at}.item")
            if kind == "bomb":
                add(f"{at}.age", 1, "continuous")
            if kind == "interactable":
                add(f"{at}.class", len(INTERACTABLE_CLASSES), "one_hot")

    add("player.position", 2, "continuous")
    add("player.velocity_valid", 1, "binary")
    add("player.velocity", 2, "continuous")
    add("player.hearts", 4, "continuous")
    anchor(INVENTORY_OFFSET)
    add("inventory.counters", 3, "continuous")  # coins, bombs, keys
    add("inventory.active_present", 1, "binary")
    add("inventory.active_id", 1, "continuous")
    add("inventory.active_charge", 1, "continuous")
    add("inventory.consumables", 3, "binary")  # card, pill, trinket
    add("inventory.active_quality", 1, "continuous")
    add("inventory.active_tags", TAG_FEATURES, "binary")
    add("inventory.active_bucket", ITEM_BUCKETS, "one_hot")
    anchor(ROOM_OFFSET)
    add("room.type", ROOM_TYPES, "one_hot")
    add("room.stage", 2, "continuous")  # stage, stage type
    add("room.clear", 1, "binary")
    for slot in range(DOOR_SLOTS):
        add(f"room.door[{slot}].flags", 4, "binary")  # exists, open, locked, target visited
        add(f"room.door[{slot}].target_class", len(ROOM_CLASSES), "one_hot")
    add("room.shape", ROOM_SHAPES, "one_hot")
    for kind in BASE_KINDS:
        slots(kind)
    anchor(COLLECTIBLE_OFFSET)
    add("collectibles", COLLECTIBLE_ID_MAX, "binary")
    add("stats", len(STAT_SCALES), "continuous")
    add("tear_flags", len(TEAR_FLAG_NAMES), "binary")
    add("weapons", len(WEAPON_NAMES), "binary")
    add("held_tags", TAG_FEATURES, "continuous")  # count / 3: four levels
    for kind in EXTRA_KINDS:
        slots(kind)
    anchor(MAP_OFFSET)
    for cell in range(LEVEL_GRID_CELLS):
        add(f"map[{cell}].flags", 3, "binary")  # known, visited, current
        add(f"map[{cell}].room_class", len(ROOM_CLASSES), "one_hot")
    add("map.off_grid", 1, "binary")
    anchor(STALL_OFFSET)
    add("stall", 1, "continuous")
    anchor(VISITED_OFFSET)
    add("visited_cells", VISITED_COLS * VISITED_ROWS, "binary")
    anchor(OBSERVATION_SIZE)
    return tuple(blocks)


FEATURE_BLOCKS = _feature_blocks()


def feature_kinds() -> tuple[FeatureKind, ...]:
    """Kind of each observation index, from FEATURE_BLOCKS."""
    return tuple(block.kind for block in FEATURE_BLOCKS for _ in range(block.size))


def continuous_mask() -> NDArray[np.bool_]:
    """True for the observation indices the learner normalizes (a fresh array)."""
    return np.array([kind == "continuous" for kind in feature_kinds()], dtype=np.bool_)


def room_class(room_type: int) -> int:
    """Index into ROOM_CLASSES for a RoomType value."""
    return ROOM_CLASSES.index(_ROOM_CLASS.get(room_type, "special"))


def identity_bucket(npc_type: int, npc_variant: int) -> int:
    """Stable bucket of an enemy (type, variant): Knuth multiplicative hash, never hash().

    The top bits are used: the low bits of the product depend only on the low bits of the key,
    so they would ignore the type.
    """
    product = (npc_type * 4096 + npc_variant) * 2654435761 % 2**32
    return product >> (32 - IDENTITY_BUCKETS.bit_length() + 1)


def item_bucket(item_id: int) -> int:
    """Stable bucket of a collectible ID: Knuth multiplicative hash, top bits, never hash().

    Same idea as `identity_bucket`, one hash per ID; the top 6 bits give 64 buckets.
    """
    return item_id * 2654435761 % 2**32 >> (32 - ITEM_BUCKETS.bit_length() + 1)


def room_diagonal(shape: int) -> float:
    """Diagonal in pixels of the bounding box of a room shape (reward label scale, not an input)."""
    width, height = SHAPE_TILES[shape]
    return math.hypot(width * CELL_SIZE, height * CELL_SIZE)


@dataclass(frozen=True)
class EncodedObservation:
    vector: NDArray[np.float32]
    overflow: dict[EntityKind, int] = field(default_factory=dict)
    clipped_values: int = 0
    # Entities per kind in the frame, including those the observer cut (metrics only).
    counts: dict[EntityKind, int] = field(default_factory=dict)
    # Distinct enemy (type, variant) pairs in the frame (metrics only).
    enemy_kinds: frozenset[tuple[int, int]] = frozenset()


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
    if inv.active_item > 0:
        at = base + INVENTORY_BASE_FEATURES
        vector[at] = inv.active_quality / ITEM_QUALITY_MAX
        _encode_tags(vector, at + 1, inv.active_tags)
        vector[at + 1 + TAG_FEATURES + item_bucket(inv.active_item)] = 1.0


def _encode_tags(vector: NDArray[np.float32], base: int, mask: int) -> None:
    for bit in range(TAG_FEATURES):
        vector[base + bit] = float(mask >> bit & 1)


def _encode_room(vector: NDArray[np.float32], frame: EntityFrame) -> None:
    room = frame.room
    base = ROOM_OFFSET
    vector[base + room.type] = 1.0
    vector[base + ROOM_TYPES] = room.stage / 15.0
    vector[base + ROOM_TYPES + 1] = room.stage_type / 7.0
    vector[base + ROOM_TYPES + 2] = float(room.clear)
    for slot, door in enumerate(room.doors):
        if door is None:
            continue
        at = base + ROOM_TYPES + 3 + slot * DOOR_FEATURES
        vector[at] = 1.0
        vector[at + 1] = float(door.open)
        vector[at + 2] = float(door.locked)
        vector[at + 3] = float(door.target_visited)
        if door.target_type is not None:
            vector[at + 4 + room_class(door.target_type)] = 1.0
    vector[base + ROOM_TYPES + 3 + DOOR_SLOTS * DOOR_FEATURES + room.shape - 1] = 1.0


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
            if room.room_type is not None:
                vector[base + 3 + room_class(room.room_type)] = 1.0
    vector[OFF_GRID_OFFSET] = float(frame.map_current_off_grid)


def _encode_enemy(vector: NDArray[np.float32], base: int, entity: Entity) -> None:
    if entity.npc_type is None or entity.npc_variant is None or entity.npc_max_hp is None:
        return  # identity unknown: all zeros, valid flag stays 0
    vector[base] = 1.0
    vector[base + 1] = float(bool(entity.boss))
    vector[base + 2] = float(bool(entity.champion))
    vector[base + 3] = float(bool(entity.flying))
    vector[base + 4] = float(bool(entity.invulnerable))
    vector[base + 5] = min(math.log1p(entity.npc_max_hp) / math.log1p(ENEMY_HP_SCALE), 1.0)
    vector[base + 6 + identity_bucket(entity.npc_type, entity.npc_variant)] = 1.0


def _encode_pickup(vector: NDArray[np.float32], base: int, entity: Entity) -> None:
    assert entity.variant is not None and entity.subtype is not None and entity.price is not None
    vector[base + variant_class(entity.variant)] = 1.0
    vector[base + len(VARIANT_CLASSES)] = entity.subtype / SUBTYPE_SCALE
    vector[base + len(VARIANT_CLASSES) + 1] = float(entity.price != 0)
    # Item block: only a pedestal collectible (an empty pedestal has subtype 0).
    if entity.variant != COLLECTIBLE_VARIANT or entity.subtype == 0:
        return
    at = base + len(VARIANT_CLASSES) + 2
    if entity.item_type is not None:
        assert entity.item_quality is not None and entity.item_max_charges is not None
        assert entity.item_tags is not None
        vector[at] = entity.item_quality / ITEM_QUALITY_MAX
        if entity.item_type != "unknown":
            vector[at + 1 + ITEM_TYPE_ONEHOT.index(entity.item_type)] = 1.0
        vector[at + 1 + len(ITEM_TYPE_ONEHOT)] = min(entity.item_max_charges / CHARGE_SCALE, 1.0)
        _encode_tags(vector, at + 2 + len(ITEM_TYPE_ONEHOT), entity.item_tags)
    vector[at + 2 + len(ITEM_TYPE_ONEHOT) + TAG_FEATURES + item_bucket(entity.subtype)] = 1.0


class VisitedCells:
    """Cells the player occupied in each room of the current run; built from policy facts only.

    A room is told apart by stage and the current minimap grid index, like the novelty ledger's
    room key. A room without a grid position (devil, angel...) is keyed by its visit, so each
    visit starts empty. A new session or game epoch starts a new run and clears everything.
    """

    def __init__(self) -> None:
        self._run: tuple[str, int] | None = None
        self._rooms: dict[tuple[int, int], set[tuple[int, int]]] = {}

    def update(self, frame: EntityFrame) -> NDArray[np.float32]:
        """Mark the player's cell and return the room's grid (1.0 for visited cells)."""
        run = (frame.session_id, frame.game_epoch)
        if run != self._run:
            self._run = run
            self._rooms.clear()
        current = next((room.grid_index for room in frame.map if room.current), None)
        room = current if current is not None else -1 - frame.room_visit
        cells = self._rooms.setdefault((frame.room.stage, room), set())
        player = frame.player_position
        col = math.floor((player.x - ROOM_ORIGIN[0]) / CELL_SIZE)
        row = math.floor((player.y - ROOM_ORIGIN[1]) / CELL_SIZE)
        cells.add((min(max(col, 0), VISITED_COLS - 1), min(max(row, 0), VISITED_ROWS - 1)))
        grid = np.zeros(VISITED_COLS * VISITED_ROWS, dtype=np.float32)
        for col, row in cells:
            grid[row * VISITED_COLS + col] = 1.0
        return grid


def encode(
    frame: EntityFrame,
    *,
    stall_fraction: float = 0.0,
    visited_cells: NDArray[np.float32] | None = None,
) -> EncodedObservation:
    """Nearest-first, fixed capacity; zero slots are told apart by the presence bit.

    `stall_fraction` is the stall watchdog's idle time over its limit, clipped to [0, 1].
    `visited_cells` is the run's visited grid of the current room (`VisitedCells.update`).
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
    if visited_cells is not None:
        if visited_cells.shape != (VISITED_COLS * VISITED_ROWS,):
            raise ProtocolError("The visited cell grid has the wrong size")
        vector[VISITED_OFFSET:] = visited_cells
    overflow: dict[EntityKind, int] = dict(frame.source_overflow)
    counts: dict[EntityKind, int] = dict.fromkeys(ENTITY_KINDS, 0)
    for entity in frame.entities:
        counts[entity.kind] += 1
    for kind, dropped in frame.source_overflow.items():
        counts[kind] += dropped
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
    for i, count in enumerate(frame.tag_counts):
        vector[HELD_TAG_OFFSET + i] = min(count / HELD_TAG_SCALE, 1.0)
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
            if kind == "enemy":
                _encode_enemy(vector, base + SLOT_FEATURES, entity)
            if kind == "obstacle":
                assert entity.obstacle_class is not None
                vector[base + SLOT_FEATURES + OBSTACLE_CLASSES.index(entity.obstacle_class)] = 1.0
            if kind == "pickup":
                _encode_pickup(vector, base + SLOT_FEATURES, entity)
            if kind == "bomb":
                assert entity.age_frames is not None
                vector[base + SLOT_FEATURES] = clip(entity.age_frames, BOMB_AGE_SCALE)
            if kind == "interactable":
                assert entity.interactable_class is not None
                index = INTERACTABLE_CLASSES.index(entity.interactable_class)
                vector[base + SLOT_FEATURES + index] = 1.0
        offset += capacity * width
    kinds = frozenset(
        (e.npc_type, e.npc_variant)
        for e in frame.entities
        if e.npc_type is not None and e.npc_variant is not None
    )
    return EncodedObservation(vector, overflow, clip.count, counts, kinds)
