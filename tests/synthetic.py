"""Synthetic frame factory. Synthetic data never proves anything about the real game."""

from isaac_threrisaifuture.entities import (
    Entity,
    EntityFrame,
    Inventory,
    OracleEvent,
    RoomFacts,
    Vec,
)
from isaac_threrisaifuture.observation import Health

SESSION = "a" * 32


def health(red: int = 6) -> Health:
    return Health(red_half_hearts=red, max_red_half_hearts=6, soul_half_hearts=0, bone_containers=0)


def inventory(**changes: int) -> Inventory:
    values = dict(
        coins=0, bombs=0, keys=0, active_item=0, active_charge=0, active_max_charge=0,
        card=0, pill=0, trinket=0,
    )  # fmt: skip
    values.update(changes)
    return Inventory(**values)


def room_facts(**changes: object) -> RoomFacts:
    values: dict[str, object] = dict(type=1, stage=1, stage_type=0, clear=False, doors=[False] * 8)
    values.update(changes)
    return RoomFacts(**values)


def pickup(entity_id: int, x: float, y: float, *, variant: int = 10, subtype: int = 1, price=0):
    return Entity(
        kind="pickup",
        entity_id=entity_id,
        spawn_generation=0,
        position=Vec(x=x, y=y),
        variant=variant,
        subtype=subtype,
        price=price,
    )


def enemy(entity_id: int, x: float, y: float, *, hp: float | None = 10.0, generation: int = 0):
    return Entity(
        kind="enemy",
        entity_id=entity_id,
        spawn_generation=generation,
        position=Vec(x=x, y=y),
        hp=hp,
        max_hp=None if hp is None else 10.0,
    )


def frame(entities: list[Entity] | None = None, frame_id: int = 1, **changes: object):
    values: dict[str, object] = dict(
        provenance="synthetic",
        session_id=SESSION,
        game_epoch=1,
        room_visit=1,
        frame_id=frame_id,
        player_position=Vec(x=300.0, y=200.0),
        health=health(),
        entities=entities or [],
        inventory=inventory(),
        collectibles=[],
        collectible_overflow=0,
        room=room_facts(),
    )
    values.update(changes)
    return EntityFrame(**values)


def event(kind: str = "room_cleared", frame_id: int = 1, **changes: object):
    values: dict[str, object] = dict(
        provenance="synthetic",
        session_id=SESSION,
        game_epoch=1,
        room_visit=1,
        frame_id=frame_id,
        kind=kind,
    )
    values.update(changes)
    return OracleEvent(**values)
