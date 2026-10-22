"""Measured boundary links to supported patches; never a navigation controller."""

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from . import firing_progress_v4 as v4
from .entities import Vec
from .firing_position import ROOM_REWARD_CAP, FiringGeometry, _context
from .navigation_wire import NavigationGrid

if TYPE_CHECKING:
    from .live import LiveSnapshot


def nearest_patch(grid: NavigationGrid, position: Vec) -> tuple[int, Vec] | None:
    """Match Lua's bounded row-major nearest fully walkable rectangle projection."""
    best: tuple[int, Vec] | None = None
    distance = math.inf
    for y in range(grid.height - 1):
        for x in range(grid.width - 1):
            index = y * grid.width + x
            if any(
                grid.walkable[i] != "1"
                for i in (index, index + 1, index + grid.width, index + grid.width + 1)
            ):
                continue
            left, top = grid.origin.x + x * 40, grid.origin.y + y * 40
            q = Vec(x=min(max(position.x, left), left + 40), y=min(max(position.y, top), top + 40))
            d = (q.x - position.x) ** 2 + (q.y - position.y) ** 2
            if d <= 3200 and d < distance:
                best, distance = (index, q), d
    return best


def _link(grid: NavigationGrid, geometry: FiringGeometry, position: Vec) -> tuple[int, Vec] | None:
    support = geometry.boundary_support
    if support is None or support.clear is not True or support.source != position:
        return None
    patch = nearest_patch(grid, position)
    if patch is None or patch != (support.patch, support.position):
        return None
    return patch


def potential(grid: NavigationGrid, geometry: FiringGeometry, position: Vec) -> float | None:
    interior = v4.potential(grid, geometry, position)
    if interior is not None:
        return interior
    link = _link(grid, geometry, position)
    if link is None:
        return None
    _, q = link
    projected = v4.potential(grid, geometry, q)
    if projected is None or geometry.tear_range is None:
        return None
    scale = max(40, geometry.tear_range)
    distance = scale * (1 / projected - 1) + math.hypot(q.x - position.x, q.y - position.y)
    return 1 / (1 + distance / scale)


@dataclass
class FiringProgressV5(v4.FiringProgressV4):
    """Capped novelty plus signed, previously charged retreat recovery."""

    _debt: dict[tuple[str, int, int, int, int, int], float] = field(default_factory=dict)
    _room_debt: dict[tuple[str, int, int, int, int], float] = field(default_factory=dict)

    def _recovery(
        self, before: "LiveSnapshot", after: "LiveSnapshot", coherent: FiringGeometry
    ) -> float:
        # Called only after v4 validates context, target, grid, support and motion.
        assert before.oracle is not None and before.oracle.navigation is not None
        assert before.oracle.navigation.grid is not None and before.oracle.firing is not None
        assert before.entity_frame is not None and after.entity_frame is not None
        grid = before.oracle.navigation.grid
        assert after.oracle is not None and after.oracle.firing is not None
        if self._potential(grid, after.oracle.firing, after.entity_frame.player_position) is None:
            return 0.0
        start_geometry = coherent.model_copy(
            update={"boundary_support": before.oracle.firing.boundary_support}
        )
        start = self._potential(grid, start_geometry, before.entity_frame.player_position)
        end = self._potential(grid, coherent, after.entity_frame.player_position)
        room = _context(before)
        assert room is not None and coherent.target_id is not None
        if start is None or end is None:
            return 0.0
        key = (*room, coherent.target_id)
        debt, room_debt = self._debt.get(key, 0.0), self._room_debt.get(room, 0.0)
        delta = ROOM_REWARD_CAP * (end - start)
        if delta < 0:
            charged = min(-delta, max(0.0, ROOM_REWARD_CAP - room_debt))
            self._debt[key] = debt + charged
            self._room_debt[room] = room_debt + charged
            return -charged
        refund = min(delta, debt)
        self._debt[key] = debt - refund
        self._room_debt[room] = max(0.0, room_debt - refund)
        return refund

    def _potential(
        self, grid: NavigationGrid, geometry: FiringGeometry, position: Vec
    ) -> float | None:
        return potential(grid, geometry, position)

    def _shared_geometry(
        self, before: FiringGeometry, after: FiringGeometry, cells: list[int]
    ) -> FiringGeometry:
        # Fixed before target/goals, but each pose requires its own measured line.
        return before.model_copy(
            update={"clear_cells": cells, "boundary_support": after.boundary_support}
        )

    def _same_support(
        self,
        grid: NavigationGrid,
        before: FiringGeometry,
        after: FiringGeometry,
        start: Vec,
        end: Vec,
    ) -> bool:
        patches = []
        for geometry, position in ((before, start), (after, end)):
            if v4.potential(grid, geometry, position) is None:
                link = _link(grid, geometry, position)
                if link is None:
                    return False
                patches.append(link[0])
        if not patches:
            return True
        if any(p != patches[0] for p in patches):
            return False
        index = patches[0]
        left = grid.origin.x + index % grid.width * 40
        top = grid.origin.y + index // grid.width * 40
        # An interior endpoint must be in the boundary endpoint's same patch.
        return all(
            v4.potential(grid, geometry, position) is None
            or (left <= position.x <= left + 40 and top <= position.y <= top + 40)
            for geometry, position in ((before, start), (after, end))
        )
