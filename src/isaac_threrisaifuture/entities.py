"""Versioned policy-visible entity frames and the separate oracle event type."""

from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from .observation import Counter, Health, SessionId, Snapshot, WireModel

OBSERVATION_SCHEMA_VERSION = 3
ORACLE_SCHEMA_VERSION = 1  # oracle events are unchanged by observation schema 3
MAX_FRAME_BYTES = 65536
MAX_ENTITIES = 64
MAX_PICKUPS = 8
MAX_COLLECTIBLES = 256
COLLECTIBLE_ID_MAX = 1024
DOOR_SLOTS = 8
Coord = Annotated[float, Field(ge=-1e5, le=1e5)]
EntityKind = Literal["enemy", "projectile", "obstacle", "pickup"]
ENTITY_KINDS: tuple[EntityKind, ...] = ("enemy", "projectile", "obstacle", "pickup")


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


class RoomFacts(WireModel):
    """Observed room facts: type, floor, clear flag and open doors by slot."""

    type: Annotated[int, Field(ge=0, le=31)]
    stage: Annotated[int, Field(ge=0, le=15)]
    stage_type: Annotated[int, Field(ge=0, le=7)]
    clear: bool
    doors: Annotated[list[bool], Field(min_length=DOOR_SLOTS, max_length=DOOR_SLOTS)]


class EntityFrame(WireModel):
    """Policy-visible state only. Hidden map data and reward labels do not belong here."""

    type: Literal["entity_frame"] = "entity_frame"
    observation_schema_version: Literal[3] = 3
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
    # Sorted unique held collectible IDs; overflow counts the IDs cut by the cap.
    collectibles: Annotated[
        list[Annotated[int, Field(ge=1, le=COLLECTIBLE_ID_MAX)]],
        Field(max_length=MAX_COLLECTIBLES),
    ]
    collectible_overflow: Annotated[int, Field(ge=0, le=COLLECTIBLE_ID_MAX - MAX_COLLECTIBLES)]
    room: RoomFacts

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
