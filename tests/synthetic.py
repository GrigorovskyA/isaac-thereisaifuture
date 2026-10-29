"""Synthetic frame factory. Synthetic data never proves anything about the real game."""

from isaac_threrisaifuture.entities import (
    TEAR_FLAG_NAMES,
    WEAPON_NAMES,
    DoorFacts,
    Entity,
    EntityFrame,
    Inventory,
    OracleEvent,
    RoomFacts,
    Stats,
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


def stats(**changes: float) -> Stats:
    values = dict(damage=3.5, tears_per_second=2.73, range=260.0, shot_speed=1.0, move_speed=1.0)
    values.update(changes, luck=changes.get("luck", 0.0))
    return Stats(**values)


def tear_flags(*names: str) -> list[bool]:
    return [name in names for name in TEAR_FLAG_NAMES]


def weapons(*names: str) -> list[bool]:
    return [name in names for name in WEAPON_NAMES]


def oracle_metrics(**hits: int) -> dict[str, object]:
    """Wire fields of LiveOracle that tests rarely care about: kills, hits by source, no doors."""
    sources = dict.fromkeys(
        ("enemy", "projectile", "own_bomb", "explosion", "spikes", "fire", "creep", "other"), 0
    )
    sources.update(hits)
    return {"kills": 0, "killed": [], "player_hits": sources, "doors": []}


def door(
    *, open: bool = True, locked: bool = False, target_type: int | None = 1, visited: bool = False
) -> DoorFacts:
    return DoorFacts(open=open, locked=locked, target_type=target_type, target_visited=visited)


def room_facts(**changes: object) -> RoomFacts:
    values: dict[str, object] = dict(
        type=1, stage=1, stage_type=0, clear=False, doors=[None] * 8, shape=1
    )
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
        stats=stats(),
        tear_flags=tear_flags(),
        weapons=weapons("tears"),
        collectibles=[],
        collectible_overflow=0,
        room=room_facts(),
        map=[],
        map_current_off_grid=False,
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
