"""Negotiated management data; never part of a policy EntityFrame."""

from typing import Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from .entities import Vec
from .observation import Counter, WireModel

NAVIGATION_CAPABILITY = "combat_navigation_v1"
NAVIGATION_GRID_CAPABILITY = "combat_navigation_grid_v2"


class NavigationGrid(WireModel):
    origin: Vec
    spacing: Literal[40]
    width: Annotated[int, Field(ge=3, le=32)]
    height: Annotated[int, Field(ge=3, le=32)]
    walkable: Annotated[str, Field(min_length=9, max_length=1024, pattern=r"^[01]+$")]

    @model_validator(mode="after")
    def complete_mask(self) -> Self:
        if len(self.walkable) != self.width * self.height:
            raise ValueError("Navigation grid dimensions do not match mask")
        return self


class OpenDoor(WireModel):
    slot: Annotated[int, Field(ge=0, le=7)]
    position: Vec


class NavigationFrame(WireModel):
    version: Literal[1, 2]
    room_index: Annotated[int, Field(ge=0, le=168)]
    stage: Counter
    stage_type: Counter
    room_type: Annotated[int, Field(ge=1, le=100)]
    shape: Annotated[int, Field(ge=1, le=12)]
    doors: Annotated[list[OpenDoor], Field(max_length=8)]
    grid: NavigationGrid | None = None

    @field_validator("version", mode="before")
    @classmethod
    def strict_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("Navigation version must be an integer")
        return value

    @model_validator(mode="after")
    def unique_slots(self) -> Self:
        if len({door.slot for door in self.doors}) != len(self.doors):
            raise ValueError("Duplicate navigation door slot")
        if (self.version == 2) != (self.grid is not None):
            raise ValueError("Only navigation version 2 requires a measured grid")
        return self
