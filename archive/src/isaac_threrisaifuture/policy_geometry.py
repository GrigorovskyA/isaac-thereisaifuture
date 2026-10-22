"""Observable local geometry extension, separate from reward/oracle evidence."""

import math
from typing import Annotated, Literal, Self

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, field_validator, model_validator

from .encoding import CAPACITY, OBSERVATION_SIZE, encode
from .entities import EntityFrame
from .observation import Counter, WireModel

GEOMETRY_OBSERVATION_SIZE = OBSERVATION_SIZE + 74


class VisibleLine(WireModel):
    entity_id: Counter
    clear: bool | None


class CombatGeometry(WireModel):
    version: Literal[2] = 2
    frame_id: Counter
    weapon: Literal["plain_tears", "unsupported", "unavailable"]
    tear_range: Annotated[float, Field(gt=0, le=4000)] | None = None
    movement: Annotated[list[bool | None], Field(min_length=4, max_length=4)]
    enemies: Annotated[list[VisibleLine], Field(max_length=16)]

    @field_validator("version", mode="before")
    @classmethod
    def strict_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("Policy geometry version must be an integer")
        return value

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if (self.weapon == "plain_tears") != (self.tear_range is not None):
            raise ValueError("Policy weapon range must have known ordinary-tear semantics")
        if len({e.entity_id for e in self.enemies}) != len(self.enemies):
            raise ValueError("Duplicate visible line identity")
        if self.weapon != "plain_tears" and any(e.clear is not None for e in self.enemies):
            raise ValueError("Unknown weapon cannot promise projectile clearance")
        return self


def encode_geometry(frame: EntityFrame, geometry: CombatGeometry) -> NDArray[np.float32]:
    """Observation2=unchanged legacy component plus74 observable,masked features."""
    visible = sorted(
        (e for e in frame.entities if e.kind == "enemy"),
        key=lambda e: (e.position.x**2 + e.position.y**2, e.spawn_generation, e.entity_id),
    )
    lines = {e.entity_id: e.clear for e in geometry.enemies}
    if geometry.frame_id != frame.frame_id or not set(lines).issubset(
        {e.entity_id for e in visible}
    ):
        raise ValueError("Policy geometry disagrees with visible frame identity")
    extension = np.zeros(74, dtype=np.float32)
    if geometry.tear_range is not None:
        extension[:2] = (1, geometry.tear_range / 4000)
    for index, clear in enumerate(geometry.movement):
        if clear is not None:
            extension[2 + index * 2 : 4 + index * 2] = (1, not clear)
    for slot, enemy in enumerate(visible[: CAPACITY["enemy"]]):
        line = lines.get(enemy.entity_id)
        base = 10 + slot * 4
        if line is not None:
            extension[base : base + 2] = (1, line)
        if geometry.tear_range is not None:
            dx, dy = abs(enemy.position.x), abs(enemy.position.y)
            extension[base + 2] = math.hypot(dx, dy) <= geometry.tear_range
            extension[base + 3] = min(dx, dy) <= 8
    return np.concatenate((encode(frame).vector, extension))
