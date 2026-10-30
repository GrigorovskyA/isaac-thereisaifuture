"""Versioned policy-visible entity frames and the separate oracle event type."""

from typing import Annotated, Literal, Self, get_args

from pydantic import Field, model_validator

from .observation import Counter, Health, SessionId, Snapshot, WireModel

# Wire frame schema 6 (observation schema 8) adds the `interactable` kind, door facts and the
# trapdoor, crawlspace, pressure plate, lock block and teleporter obstacle classes, and enemy
# identity facts (type, variant, max HP, boss, champion, flying, invulnerable). Policy
# observation schemas 6-8 also add encoder-side blocks built from successive frames or from
# grouped room types (see encoding.py).
# Wire frame schema 7 (observation schema 9) adds item catalog facts: quality, type, max charges
# and tag bits of pedestal collectibles, quality and tag bits of the active item, and the count of
# held collectibles per tag (ItemConfig facts, never predicted effects).
FRAME_SCHEMA_VERSION = 7
OBSERVATION_SCHEMA_VERSION = 9
ORACLE_SCHEMA_VERSION = 1  # oracle events are unchanged by observation schema 9
MAX_FRAME_BYTES = 131072
MAX_MAP_ROOMS = 64
LEVEL_GRID_CELLS = 169  # 13 x 13 level grid
MAX_COLLECTIBLES = 256
COLLECTIBLE_ID_MAX = 1024
DOOR_SLOTS = 8
BOSS_ROOM_TYPE = 5  # RoomType.ROOM_BOSS in RoomFacts.type and MapRoom.room_type
Coord = Annotated[float, Field(ge=-1e5, le=1e5)]
BOMB_AGE_MAX = 10000
NPC_TYPE_MAX = 1000  # EntityType of an enemy
NPC_VARIANT_MAX = 4095
EntityKind = Literal[
    "enemy", "projectile", "obstacle", "pickup", "own_attack", "bomb", "interactable"
]
ENTITY_KINDS: tuple[EntityKind, ...] = get_args(EntityKind)
# Observer caps per kind, nearest first. mod/observer/main.lua `entity_caps` repeats them and
# the encoder capacity is this table; a test compares the Lua caps.
ENTITY_CAPS: dict[EntityKind, int] = {
    "enemy": 32,
    "projectile": 64,
    "obstacle": 64,
    "pickup": 24,
    "own_attack": 48,
    "bomb": 8,
    "interactable": 16,
}
MAX_ENTITIES = sum(ENTITY_CAPS.values())
MAX_PICKUPS = ENTITY_CAPS["pickup"]
# Obstacle classes in wire and encoding order; the observer maps grid types by name. The last
# five before `wall` are floor features and exits: trapdoor (next floor), crawlspace stairs,
# pressure plate, key lock block and teleporter.
OBSTACLE_CLASSES = (
    "rock",
    "marked_rock",
    "bomb_rock",
    "block",
    "pit",
    "spikes",
    "poop",
    "tnt",
    "fire",
    "trapdoor",
    "crawlspace",
    "pressure_plate",
    "lock_block",
    "teleporter",
    "wall",
    "other",
)
# ItemConfig tags kept as facts, in bit order: bit i of a tag mask is ITEM_TAGS[i]. The observer
# reads each flag by name from the game (ItemConfig.TAG_<NAME>, missing => bit 0) and
# mod/observer/main.lua `item_tag_names` repeats this list; a test compares both. These are the
# transformation sets of the game (Guppy, Beelzebub, Fun Guy, Spun, Bob, Spider Baby, Conjoined,
# Mom): the game counts them itself.
ITEM_TAGS = ("guppy", "fly", "mushroom", "syringe", "bob", "spider", "baby", "mom")
ITEM_TAG_MASK_MAX = 2 ** len(ITEM_TAGS) - 1
ITEM_QUALITY_MAX = 4
ITEM_MAX_CHARGES_MAX = 24
ItemType = Literal["passive", "active", "familiar", "unknown"]
ITEM_TYPES: tuple[ItemType, ...] = get_args(ItemType)
COLLECTIBLE_VARIANT = 100  # PickupVariant.PICKUP_COLLECTIBLE: a pedestal
ObstacleClass = Literal[
    "rock",
    "marked_rock",
    "bomb_rock",
    "block",
    "pit",
    "spikes",
    "poop",
    "tnt",
    "fire",
    "trapdoor",
    "crawlspace",
    "pressure_plate",
    "lock_block",
    "teleporter",
    "wall",
    "other",
]
# Interactable classes: slot machines and beggars by SlotVariant group, plus the light door
# that opens after a boss (heaven_door).
INTERACTABLE_CLASSES = (
    "slot_machine",
    "beggar",
    "blood_donation",
    "fortune_teller",
    "restock_box",
    "crane",
    "other_slot",
    "heaven_door",
)
InteractableClass = Literal[
    "slot_machine",
    "beggar",
    "blood_donation",
    "fortune_teller",
    "restock_box",
    "crane",
    "other_slot",
    "heaven_door",
]
assert get_args(ObstacleClass) == OBSTACLE_CLASSES
assert get_args(InteractableClass) == INTERACTABLE_CLASSES
assert tuple(ENTITY_CAPS) == ENTITY_KINDS
# Fixed wire order of the boolean lists; the Lua observer uses the same order.
TEAR_FLAG_NAMES = (
    "spectral",
    "piercing",
    "homing",
    "slow",
    "poison",
    "freeze",
    "split",
    "growing",
    "boomerang",
    "persistent",
    "wiggle",
    "explosive",
    "charm",
    "confusion",
    "burn",
    "bouncing",
)
WEAPON_NAMES = (
    "tears",
    "brimstone",
    "laser",
    "knife",
    "bombs",
    "rockets",
    "monstros_lungs",
    "ludovico_technique",
    "tech_x",
    "bone",
    "notched_axe",
    "urn_of_souls",
    "spirit_sword",
    "fetus",
    "umbilical_whip",
)
# Declared ranges of the player stats; the observer clamps into them.
STAT_RANGES = {
    "damage": (0.0, 1000.0),
    "tears_per_second": (0.0, 60.0),
    "range": (0.0, 10000.0),
    "shot_speed": (0.0, 10.0),
    "move_speed": (0.0, 10.0),
    "luck": (-100.0, 100.0),
}


class Vec(WireModel):
    x: Coord
    y: Coord


class Entity(WireModel):
    """One visible object. Optional fields are None when the game does not expose them."""

    kind: EntityKind
    entity_id: Counter
    spawn_generation: Counter
    position: Vec  # relative to the player
    velocity: Vec | None = None
    hp: Annotated[float, Field(ge=0, le=1e6)] | None = None
    max_hp: Annotated[float, Field(gt=0, le=1e6)] | None = None
    # Pickups only: the three go together. Price 0 is free; non-zero is a shop or devil deal.
    variant: Annotated[int, Field(ge=0, le=1023)] | None = None
    subtype: Annotated[int, Field(ge=0, le=1024)] | None = None
    price: Annotated[int, Field(ge=-1000, le=999)] | None = None
    # Bombs only: frames since the bomb appeared.
    age_frames: Annotated[int, Field(ge=0, le=BOMB_AGE_MAX)] | None = None
    # Pedestal collectibles only (variant 100, subtype > 0): ItemConfig facts, all four together.
    # `item_tags` is a bit mask over ITEM_TAGS; type "unknown" and zeros mean unreadable.
    item_quality: Annotated[int, Field(ge=0, le=ITEM_QUALITY_MAX)] | None = None
    item_type: ItemType | None = None
    item_max_charges: Annotated[int, Field(ge=0, le=ITEM_MAX_CHARGES_MAX)] | None = None
    item_tags: Annotated[int, Field(ge=0, le=ITEM_TAG_MASK_MAX)] | None = None
    # Obstacles only: what the obstacle is.
    obstacle_class: ObstacleClass | None = None
    # Interactables only: what the machine, beggar or door is.
    interactable_class: InteractableClass | None = None
    # Enemies only: identity and static facts, all seven together or none (identity unknown).
    # `npc_type` and `npc_variant` are EntityType and Variant; `npc_max_hp` is the full health
    # (current enemy HP stays unknown). The flags are rules of the observer, see the protocol doc.
    npc_type: Annotated[int, Field(ge=0, le=NPC_TYPE_MAX)] | None = None
    npc_variant: Annotated[int, Field(ge=0, le=NPC_VARIANT_MAX)] | None = None
    npc_max_hp: Annotated[float, Field(ge=0, le=1e6)] | None = None
    boss: bool | None = None
    champion: bool | None = None
    flying: bool | None = None
    invulnerable: bool | None = None

    @model_validator(mode="after")
    def obstacle_typed(self) -> Self:
        if (self.kind == "obstacle") != (self.obstacle_class is not None):
            raise ValueError("Exactly obstacles carry obstacle_class")
        return self

    @model_validator(mode="after")
    def interactable_typed(self) -> Self:
        if (self.kind == "interactable") != (self.interactable_class is not None):
            raise ValueError("Exactly interactables carry interactable_class")
        return self

    @model_validator(mode="after")
    def enemy_identity(self) -> Self:
        facts = (
            self.npc_type,
            self.npc_variant,
            self.npc_max_hp,
            self.boss,
            self.champion,
            self.flying,
            self.invulnerable,
        )
        if any(value is not None for value in facts):
            if self.kind != "enemy":
                raise ValueError("Only enemies carry identity facts")
            if any(value is None for value in facts):
                raise ValueError("Enemy identity facts go together")
        return self

    @model_validator(mode="after")
    def bomb_age(self) -> Self:
        if (self.kind == "bomb") != (self.age_frames is not None):
            raise ValueError("Exactly bombs carry age_frames")
        return self

    @model_validator(mode="after")
    def pickup_facts(self) -> Self:
        facts = (self.variant, self.subtype, self.price)
        if self.kind == "pickup":
            if any(value is None for value in facts):
                raise ValueError("Pickups need variant, subtype and price")
        elif any(value is not None for value in facts):
            raise ValueError("Only pickups carry variant, subtype and price")
        return self

    @model_validator(mode="after")
    def item_facts(self) -> Self:
        facts = (self.item_quality, self.item_type, self.item_max_charges, self.item_tags)
        if any(value is not None for value in facts):
            if self.kind != "pickup" or self.variant != COLLECTIBLE_VARIANT or not self.subtype:
                raise ValueError("Only pedestal collectibles carry item facts")
            if any(value is None for value in facts):
                raise ValueError("Item facts go together")
        return self

    @model_validator(mode="after")
    def hp_consistent(self) -> Self:
        if (self.hp is None) != (self.max_hp is None):
            raise ValueError("hp and max_hp must be both known or both unknown")
        if self.hp is not None and self.max_hp is not None and self.hp > self.max_hp:
            raise ValueError("hp cannot exceed max_hp")
        return self


class Inventory(WireModel):
    """Raw counters and held-item identifiers; 0 means none for the item fields."""

    coins: Annotated[int, Field(ge=0, le=999)]
    bombs: Annotated[int, Field(ge=0, le=999)]
    keys: Annotated[int, Field(ge=0, le=999)]
    active_item: Annotated[int, Field(ge=0, le=COLLECTIBLE_ID_MAX)]
    active_charge: Annotated[int, Field(ge=0, le=24)]
    active_max_charge: Annotated[int, Field(ge=0, le=24)]
    # ItemConfig facts of the active item; 0 when none or unreadable. Tags: a mask over ITEM_TAGS.
    active_quality: Annotated[int, Field(ge=0, le=ITEM_QUALITY_MAX)] = 0
    active_tags: Annotated[int, Field(ge=0, le=ITEM_TAG_MASK_MAX)] = 0
    card: Annotated[int, Field(ge=0, le=65535)]
    pill: Annotated[int, Field(ge=0, le=65535)]
    trinket: Annotated[int, Field(ge=0, le=65535)]


class Stats(WireModel):
    """Raw player stats; ranges are STAT_RANGES."""

    damage: Annotated[float, Field(ge=0, le=1000)]
    tears_per_second: Annotated[float, Field(ge=0, le=60)]
    range: Annotated[float, Field(ge=0, le=10000)]
    shot_speed: Annotated[float, Field(ge=0, le=10)]
    move_speed: Annotated[float, Field(ge=0, le=10)]
    luck: Annotated[float, Field(ge=-100, le=100)]


class DoorFacts(WireModel):
    """One door the player can see. `target_type` is the RoomType behind it (None if unread).

    A door to a secret, super secret or ultra secret room that is still closed is hidden in the
    game and is not reported at all (its slot is None in `RoomFacts.doors`).
    """

    open: bool
    locked: bool  # needs a key
    target_type: Annotated[int, Field(ge=0, le=31)] | None
    target_visited: bool  # the room behind the door has been entered


class RoomFacts(WireModel):
    """Observed room facts: type, floor, clear flag and the visible doors by slot (or None)."""

    type: Annotated[int, Field(ge=0, le=31)]
    stage: Annotated[int, Field(ge=0, le=15)]
    stage_type: Annotated[int, Field(ge=0, le=7)]
    clear: bool
    doors: Annotated[list[DoorFacts | None], Field(min_length=DOOR_SLOTS, max_length=DOOR_SLOTS)]
    shape: Annotated[int, Field(ge=1, le=12)]  # room:GetRoomShape()


class MapRoom(WireModel):
    """One minimap room: only what the in-game minimap shows or the player visited."""

    grid_index: Annotated[int, Field(ge=0, le=LEVEL_GRID_CELLS - 1)]
    shape: Annotated[int, Field(ge=1, le=12)]
    visited: bool
    current: bool
    # None while the room's icon is hidden and the room is unvisited.
    room_type: Annotated[int, Field(ge=0, le=31)] | None


class EntityFrame(WireModel):
    """Policy-visible state only. Hidden map data and reward labels do not belong here."""

    type: Literal["entity_frame"] = "entity_frame"
    observation_schema_version: Literal[7] = 7  # FRAME_SCHEMA_VERSION
    provenance: Literal["synthetic", "game_api"]
    session_id: SessionId
    game_epoch: Counter
    room_visit: Counter
    frame_id: Counter
    player_position: Vec
    player_velocity: Vec | None = None
    health: Health
    entities: Annotated[list[Entity], Field(max_length=MAX_ENTITIES)]
    source_overflow: dict[EntityKind, Counter] = Field(default_factory=dict)
    inventory: Inventory
    stats: Stats
    # Booleans in TEAR_FLAG_NAMES and WEAPON_NAMES order.
    tear_flags: Annotated[
        list[bool], Field(min_length=len(TEAR_FLAG_NAMES), max_length=len(TEAR_FLAG_NAMES))
    ]
    weapons: Annotated[
        list[bool], Field(min_length=len(WEAPON_NAMES), max_length=len(WEAPON_NAMES))
    ]
    # Sorted unique held collectible IDs; overflow counts the IDs cut by the cap.
    collectibles: Annotated[
        list[Annotated[int, Field(ge=1, le=COLLECTIBLE_ID_MAX)]],
        Field(max_length=MAX_COLLECTIBLES),
    ]
    collectible_overflow: Annotated[int, Field(ge=0, le=COLLECTIBLE_ID_MAX - MAX_COLLECTIBLES)]
    # Held collectibles per ITEM_TAGS entry, in order (the game counts these for transformations).
    tag_counts: Annotated[
        list[Annotated[int, Field(ge=0, le=MAX_COLLECTIBLES)]],
        Field(min_length=len(ITEM_TAGS), max_length=len(ITEM_TAGS)),
    ] = Field(default_factory=lambda: [0] * len(ITEM_TAGS))
    room: RoomFacts
    map: Annotated[list[MapRoom], Field(max_length=MAX_MAP_ROOMS)]
    # True when the current room has no grid position (devil, angel, error rooms...).
    map_current_off_grid: bool

    @model_validator(mode="after")
    def map_consistent(self) -> Self:
        indexes = [m.grid_index for m in self.map]
        if len(set(indexes)) != len(indexes):
            raise ValueError("Duplicate map grid index")
        current = sum(m.current for m in self.map)
        if current > 1:
            raise ValueError("At most one map room is current")
        if self.map_current_off_grid and current:
            raise ValueError("An off-grid current room has no current map entry")
        return self

    @model_validator(mode="after")
    def unique_identity(self) -> Self:
        keys = {(e.kind, e.entity_id, e.spawn_generation) for e in self.entities}
        if len(keys) != len(self.entities):
            raise ValueError("Duplicate entity identity in one frame")
        return self

    @model_validator(mode="after")
    def collectibles_canonical(self) -> Self:
        ids = self.collectibles
        if any(a >= b for a, b in zip(ids, ids[1:], strict=False)):
            raise ValueError("Collectibles must be strictly increasing (sorted, unique)")
        if self.collectible_overflow > 0 and len(ids) != MAX_COLLECTIBLES:
            raise ValueError("Collectible overflow is only valid with a full list")
        return self


class EntitySnapshot(Snapshot):
    """Opt-in snapshot extension; identity must agree with its outer envelope."""

    entity_frame: EntityFrame | None

    @model_validator(mode="after")
    def frame_matches_snapshot(self) -> Self:
        frame = self.entity_frame
        if self.status == "unavailable":
            if frame is not None:
                raise ValueError("Unavailable snapshots cannot carry entity state")
            return self
        if frame is None or self.player is None or self.room is None:
            raise ValueError("Available entity snapshots need an entity frame")
        if (
            frame.provenance != "game_api"
            or frame.session_id != self.session_id
            or frame.game_epoch != self.game_epoch
            or frame.frame_id != self.frame_id
            or frame.room_visit != self.room.visit_id
            or frame.player_position.x != self.player.position.x
            or frame.player_position.y != self.player.position.y
            or frame.health != self.player.health
        ):
            raise ValueError("Entity frame disagrees with snapshot identity or player")
        return self


# Kinds the native game observer can request, and kinds derived from successive frames.
NativeOracleKind = Literal[
    "enemy_spawned",
    "enemy_damaged",
    "enemy_killed",
    "player_damaged",
    "player_healed",
    "room_cleared",
    "player_died",
]
DerivedOracleKind = Literal["room_entered", "floor_entered", "pickup_gained"]
OracleKind = NativeOracleKind | DerivedOracleKind
PickupResource = Literal["coin", "bomb", "key", "collectible"]


class OracleDoor(WireModel):
    """One existing door of the current room. Reward label only, never a policy input.

    `x`, `y` is the world position of the door slot. `unexplored` is True when the room behind
    the door has never been visited in this run. `target` is the level grid index of the room
    behind the door (-1 when unreadable or off the grid). `usable` is False for a locked door
    and for a closed door to a secret room; the room graph ignores such doors.
    """

    slot: Annotated[int, Field(ge=0, le=DOOR_SLOTS - 1)]
    x: Coord
    y: Coord
    open: bool
    unexplored: bool
    target: Annotated[int, Field(ge=-1, le=168)]
    usable: bool


class OracleEvent(WireModel):
    """Reward/evaluation label. Never an input of the encoder, policy or normalizer."""

    type: Literal["oracle_event"] = "oracle_event"
    observation_schema_version: Literal[1] = 1  # ORACLE_SCHEMA_VERSION
    provenance: Literal["synthetic", "game_api"]
    session_id: SessionId
    game_epoch: Counter
    room_visit: Counter
    frame_id: Counter
    kind: OracleKind
    entity_id: Counter | None = None
    spawn_generation: Counter | None = None
    amount: Annotated[float, Field(ge=0, le=1e6)] | None = None
    damage_source: Literal["enemy", "self", "environment"] | None = None
    # Level facts. room_index: room_entered, optional on room_cleared. stage: floor_entered.
    room_index: Annotated[int, Field(ge=-64, le=255)] | None = None
    stage: Annotated[int, Field(ge=0, le=15)] | None = None
    # pickup_gained: coin/bomb/key carry the gain in `amount` and the new counter in `total`.
    resource: PickupResource | None = None
    item_id: Annotated[int, Field(ge=1, le=COLLECTIBLE_ID_MAX)] | None = None
    total: Annotated[int, Field(ge=1, le=999)] | None = None

    @model_validator(mode="after")
    def level_payload(self) -> Self:
        if self.room_index is None and self.kind == "room_entered":
            raise ValueError("room_entered needs a room_index")
        if self.room_index is not None and self.kind not in ("room_entered", "room_cleared"):
            raise ValueError("Only room_entered and room_cleared carry a room_index")
        if (self.stage is None) == (self.kind == "floor_entered"):
            raise ValueError("Exactly floor_entered carries a stage")
        pickup = (self.resource, self.item_id, self.total)
        if self.kind != "pickup_gained":
            if any(value is not None for value in pickup):
                raise ValueError("Only pickup_gained carries resource, item_id and total")
        elif self.resource == "collectible":
            if self.item_id is None or self.total is not None or self.amount is not None:
                raise ValueError("A collectible pickup carries only an item_id")
        elif self.resource is None or self.item_id is not None:
            raise ValueError("pickup_gained needs a resource")
        elif self.total is None or not self.amount or self.amount > self.total:
            raise ValueError("A consumable pickup needs a positive amount and its new total")
        return self

    @model_validator(mode="after")
    def payload_matches_kind(self) -> Self:
        has_entity = self.entity_id is not None and self.spawn_generation is not None
        if (self.entity_id is None) != (self.spawn_generation is None):
            raise ValueError("entity_id and spawn_generation go together")
        if self.kind in ("enemy_spawned", "enemy_damaged", "enemy_killed") and not has_entity:
            raise ValueError("Enemy events need entity identity and spawn generation")
        if self.kind in ("enemy_spawned", "enemy_damaged", "player_damaged", "player_healed"):
            if self.amount is None:
                raise ValueError("This event kind needs an amount")
        if self.kind == "player_damaged" and self.damage_source is None:
            raise ValueError("player_damaged needs a damage source")
        return self
