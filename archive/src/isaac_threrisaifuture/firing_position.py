"""Reward-only firing geometry and capped novelty shaping; never a controller."""

import math
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, Literal, Self

from pydantic import Field, field_validator, model_validator

from .entities import Vec
from .navigation_wire import NavigationGrid
from .observation import Counter, ProtocolError, WireModel

if TYPE_CHECKING:
    from .live import LiveSnapshot

FIRING_CAPABILITY = "firing_geometry_v1"
FIRING_REWARD_CONTRACT: Literal["live-firing-v4"] = "live-firing-v4"
ROOM_REWARD_CAP = 0.25
MAX_ROOMS = 4096


class BoundarySupport(WireModel):
    version: Literal[1]
    patch: Annotated[int, Field(ge=0, le=1023)]
    source: Vec
    position: Vec
    clear: bool | None

    @field_validator("version", mode="before")
    @classmethod
    def strict_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("Boundary support version must be an integer")
        return value


class FiringGeometry(WireModel):
    version: Literal[1] = 1
    status: Literal["plain_tears", "unsupported", "unavailable"]
    tear_range: Annotated[float, Field(gt=0, le=4000)] | None = None
    target_id: Counter | None = None
    target_position: Vec | None = None
    target_vulnerable: bool = False
    clear_cells: Annotated[list[Annotated[int, Field(ge=0, le=1023)]], Field(max_length=32)] = (
        Field(default_factory=list)
    )
    candidate_overflow: Counter = 0
    boundary_support: BoundarySupport | None = None

    @field_validator("version", mode="before")
    @classmethod
    def strict_version(cls, value: object) -> object:
        if type(value) is not int:
            raise ValueError("Firing geometry version must be an integer")
        return value

    @model_validator(mode="after")
    def consistent(self) -> Self:
        if len(set(self.clear_cells)) != len(self.clear_cells):
            raise ValueError("Duplicate firing candidate")
        if self.status == "plain_tears":
            if self.tear_range is None:
                raise ValueError("Ordinary tear geometry needs measured range")
            if (self.target_id is None) != (self.target_position is None):
                raise ValueError("Firing target identity and position must agree")
            if self.clear_cells and (self.target_id is None or not self.target_vulnerable):
                raise ValueError("Clear firing candidates need a vulnerable target")
        elif self.clear_cells or self.target_id is not None or self.target_vulnerable:
            raise ValueError("Unsupported firing geometry cannot carry usable targets")
        return self


def _cell(grid: NavigationGrid, position: Vec) -> int | None:
    x = math.floor((position.x - grid.origin.x) / grid.spacing + 0.5)
    y = math.floor((position.y - grid.origin.y) / grid.spacing + 0.5)
    if not (0 <= x < grid.width and 0 <= y < grid.height):
        return None
    index = y * grid.width + x
    return index if grid.walkable[index] == "1" else None


def potential(grid: NavigationGrid, geometry: FiringGeometry, position: Vec) -> float | None:
    """Shortest measured walk to positively witnessed ordinary-tear firing cells."""
    if geometry.status != "plain_tears" or not geometry.target_vulnerable:
        return None
    if geometry.target_position is None or geometry.tear_range is None:
        return None
    goals = set()
    for index in geometry.clear_cells:
        if index >= len(grid.walkable):
            raise ProtocolError("Firing candidate lies outside its measured grid")
        x = grid.origin.x + index % grid.width * grid.spacing
        y = grid.origin.y + index // grid.width * grid.spacing
        dx, dy = abs(x - geometry.target_position.x), abs(y - geometry.target_position.y)
        distance = math.hypot(dx, dy)
        if (
            grid.walkable[index] == "1"
            and min(dx, dy) <= 8
            and (80 <= distance <= geometry.tear_range - 20)
        ):
            goals.add(index)
    start = _cell(grid, position)
    if start is None or not goals:
        return None
    queue = deque([(start, 0)])
    seen = {start}
    while queue:
        current, steps = queue.popleft()
        if current in goals:
            center_x = grid.origin.x + start % grid.width * grid.spacing
            center_y = grid.origin.y + start // grid.width * grid.spacing
            distance = steps * grid.spacing + math.hypot(
                position.x - center_x, position.y - center_y
            )
            return 1 / (1 + distance / max(40, geometry.tear_range))
        x, y = current % grid.width, current // grid.width
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < grid.width and 0 <= ny < grid.height:
                nxt = ny * grid.width + nx
                if nxt not in seen and grid.walkable[nxt] == "1":
                    seen.add(nxt)
                    queue.append((nxt, steps + 1))
    return None


def _context(snap: "LiveSnapshot") -> tuple[str, int, int, int, int] | None:
    nav = snap.oracle.navigation if snap.oracle else None
    if nav is None or nav.grid is None or nav.room_type != 1:
        return None
    return snap.session_id, snap.game_epoch, nav.stage, nav.stage_type, nav.room_index


@dataclass
class FiringProgress:
    """Monotone room record: no repeated credit for reset, reentry or oscillation."""

    _best: dict[tuple[str, int, int, int, int], float] = field(default_factory=dict)
    _last: tuple[str, int, int] | None = None

    def _baseline(
        self, snap: "LiveSnapshot"
    ) -> tuple[tuple[str, int, int, int, int], float] | None:
        context = _context(snap)
        oracle = snap.oracle
        frame = snap.entity_frame
        if context is None or oracle is None or oracle.firing is None or frame is None:
            return None
        assert oracle.navigation is not None and oracle.navigation.grid is not None
        if oracle.player_dead or oracle.room_clear or snap.status != "active":
            return None
        value = potential(oracle.navigation.grid, oracle.firing, frame.player_position)
        if value is None:
            return None
        if context not in self._best and len(self._best) >= MAX_ROOMS:
            raise ProtocolError(
                "Firing room history exhausted; credit is never renewed by eviction"
            )
        self._best[context] = max(self._best.get(context, 0.0), value)
        return context, value

    def begin(self, snap: "LiveSnapshot") -> None:
        if (
            self._last is not None
            and snap.frame_id is not None
            and (
                self._last[:2] == (snap.session_id, snap.game_epoch)
                and snap.frame_id < self._last[2]
            )
        ):
            raise ProtocolError("Firing baseline frame regressed")
        self._baseline(snap)
        if snap.frame_id is not None:
            self._last = (snap.session_id, snap.game_epoch, snap.frame_id)

    def transition(self, before: "LiveSnapshot", after: "LiveSnapshot") -> float:
        if before.frame_id is None or after.frame_id is None:
            raise ProtocolError("Firing shaping requires available frames")
        if self._last is not None and self._last != (
            before.session_id,
            before.game_epoch,
            before.frame_id,
        ):
            raise ProtocolError("Firing transition does not continue its baseline")
        last = (after.session_id, after.game_epoch, after.frame_id)
        if self._last is not None and self._last[:2] == last[:2] and last[2] <= self._last[2]:
            raise ProtocolError("Replayed firing reward frame")
        self._last = last
        baseline = self._baseline(before)
        if baseline is None or _context(before) != _context(after):
            self._baseline(after)
            return 0.0
        context, _ = baseline
        b, a = before.oracle, after.oracle
        assert b is not None and b.navigation is not None and b.navigation.grid is not None
        if a is None or a.firing is None or b.firing is None or a.navigation is None:
            return 0.0
        if (
            before.room is None
            or after.room is None
            or before.room.visit_id != after.room.visit_id
            or a.navigation.grid != b.navigation.grid
            or a.firing.status != "plain_tears"
            or a.firing.target_id != b.firing.target_id
            or not a.firing.target_vulnerable
            or a.firing.tear_range != b.firing.tear_range
            or a.player_dead
            or a.room_clear
            or after.status != "active"
        ):
            self._baseline(after)
            return 0.0
        assert before.entity_frame is not None and after.entity_frame is not None
        start, end = before.entity_frame.player_position, after.entity_frame.player_position
        if math.hypot(end.x - start.x, end.y - start.y) <= 0.5:
            self._baseline(after)
            return 0.0
        shared_cells = sorted(set(b.firing.clear_cells).intersection(a.firing.clear_cells))
        coherent = b.firing.model_copy(update={"clear_cells": shared_cells})
        value = (
            potential(b.navigation.grid, coherent, end)
            if potential(b.navigation.grid, a.firing, end) is not None
            else None
        )
        old = self._best[context]
        self._best[context] = max(old, value or 0.0)
        # New geometry cannot lower the historical record to renew credit.
        self._baseline(after)
        return ROOM_REWARD_CAP * max(0.0, (value or 0.0) - old)
