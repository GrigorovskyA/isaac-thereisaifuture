"""Versioned policy-visible entity frames and the separate oracle event type."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .observation import Counter, Health, SessionId, Snapshot, WireModel

OBSERVATION_SCHEMA_VERSION = 5
ORACLE_SCHEMA_VERSION = 1  # oracle events are unchanged by observation schema 5
MAX_FRAME_BYTES = 65536
# Observer caps: 12 enemies, 20 projectiles, 24 obstacles, 8 pickups, 16 own attacks, 4 bombs.
MAX_ENTITIES = 84
MAX_MAP_ROOMS = 64
LEVEL_GRID_CELLS = 169  # 13 x 13 level grid
MAX_PICKUPS = 8
MAX_COLLECTIBLES = 256
COLLECTIBLE_ID_MAX = 1024
DOOR_SLOTS = 8
Coord = Annotated[float, Field(ge=-1e5, le=1e5)]
BOMB_AGE_MAX = 10000
EntityKind = Literal["enemy", "projectile", "obstacle", "pickup", "own_attack", "bomb"]
ENTITY_KINDS: tuple[EntityKind, ...] = (
    "enemy",
    "projectile",
    "obstacle",
    "pickup",
    "own_attack",
    "bomb",
)
# Obstacle classes in wire and encoding order; the observer maps grid types by name.
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
    "wall",
    "other",
)
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
    "wall",
    "other",
]
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
    # Obstacles only: what the obstacle is.
    obstacle_class: ObstacleClass | None = None

    @model_validator(mode="after")
    def obstacle_typed(self) -> Self:
        if (self.kind == "obstacle") != (self.obstacle_class is not None):
            raise ValueError("Exactly obstacles carry obstacle_class")
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


class RoomFacts(WireModel):
    """Observed room facts: type, floor, clear flag and open doors by slot."""

    type: Annotated[int, Field(ge=0, le=31)]
    stage: Annotated[int, Field(ge=0, le=15)]
    stage_type: Annotated[int, Field(ge=0, le=7)]
    clear: bool
    doors: Annotated[list[bool], Field(min_length=DOOR_SLOTS, max_length=DOOR_SLOTS)]
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
    observation_schema_version: Literal[5] = 5
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
