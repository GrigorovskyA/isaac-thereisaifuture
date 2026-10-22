"""Conservative interpolated progress; historical v3 remains in firing_position."""

import math
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .entities import Vec
from .firing_position import MAX_ROOMS, ROOM_REWARD_CAP, FiringGeometry, _context
from .navigation_wire import NavigationGrid
from .observation import ProtocolError

if TYPE_CHECKING:
    from .live import LiveSnapshot

MAX_TARGETS = 65536


def potential(grid: NavigationGrid, geometry: FiringGeometry, position: Vec) -> float | None:
    """Interpolate a bounded graph field only over measured reachable support."""
    if (
        geometry.status != "plain_tears"
        or not geometry.target_vulnerable
        or geometry.target_position is None
        or geometry.tear_range is None
    ):
        return None
    distances: dict[int, int] = {}
    for index in geometry.clear_cells:
        if index >= len(grid.walkable):
            raise ProtocolError("Firing candidate lies outside its measured grid")
        x = grid.origin.x + index % grid.width * grid.spacing
        y = grid.origin.y + index // grid.width * grid.spacing
        dx, dy = abs(x - geometry.target_position.x), abs(y - geometry.target_position.y)
        if (
            grid.walkable[index] == "1"
            and min(dx, dy) <= 8
            and 80 <= math.hypot(dx, dy) <= geometry.tear_range - 20
        ):
            distances[index] = 0
    queue = deque(distances)
    while queue:
        index = queue.popleft()
        x, y = index % grid.width, index // grid.width
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, ny = x + dx, y + dy
            nxt = ny * grid.width + nx
            if (
                0 <= nx < grid.width
                and 0 <= ny < grid.height
                and grid.walkable[nxt] == "1"
                and nxt not in distances
            ):
                distances[nxt] = distances[index] + 1
                queue.append(nxt)
    gx = (position.x - grid.origin.x) / grid.spacing
    gy = (position.y - grid.origin.y) / grid.spacing
    if not (0 <= gx <= grid.width - 1 and 0 <= gy <= grid.height - 1):
        return None
    x0, y0 = math.floor(gx), math.floor(gy)
    fx, fy = gx - x0, gy - y0
    distance = 0.0
    for x, wx in ((x0, 1 - fx), (x0 + 1, fx)):
        for y, wy in ((y0, 1 - fy), (y0 + 1, fy)):
            weight = wx * wy
            if weight == 0:
                continue
            index = y * grid.width + x
            if x >= grid.width or y >= grid.height or index not in distances:
                return None
            distance += weight * distances[index] * grid.spacing
    return 1 / (1 + distance / max(40, geometry.tear_range))


@dataclass
class FiringProgressV4:
    """Monotone room record: no repeated credit for reset, reentry or oscillation."""

    _best: dict[tuple[str, int, int, int, int, int], float] = field(default_factory=dict)
    _paid: dict[tuple[str, int, int, int, int], float] = field(default_factory=dict)
    _last: tuple[str, int, int] | None = None

    def _potential(
        self, grid: NavigationGrid, geometry: FiringGeometry, position: Vec
    ) -> float | None:
        return potential(grid, geometry, position)

    def _shared_geometry(
        self, before: FiringGeometry, after: FiringGeometry, cells: list[int]
    ) -> FiringGeometry:
        return before.model_copy(update={"clear_cells": cells})

    def _same_support(
        self,
        grid: NavigationGrid,
        before: FiringGeometry,
        after: FiringGeometry,
        start: Vec,
        end: Vec,
    ) -> bool:
        return True

    def _recovery(
        self, before: "LiveSnapshot", after: "LiveSnapshot", coherent: FiringGeometry
    ) -> float:
        return 0.0

    def _baseline(
        self, snap: "LiveSnapshot"
    ) -> tuple[tuple[str, int, int, int, int, int], float] | None:
        context = _context(snap)
        oracle = snap.oracle
        frame = snap.entity_frame
        if context is None or oracle is None or oracle.firing is None or frame is None:
            return None
        assert oracle.navigation is not None and oracle.navigation.grid is not None
        if oracle.player_dead or oracle.room_clear or snap.status != "active":
            return None
        value = self._potential(oracle.navigation.grid, oracle.firing, frame.player_position)
        if value is None:
            return None
        target = oracle.firing.target_id
        if target is None:
            return None
        if context not in self._paid and len(self._paid) >= MAX_ROOMS:
            raise ProtocolError("Firing room history exhausted")
        self._paid.setdefault(context, 0.0)
        key = (*context, target)
        if key not in self._best and len(self._best) >= MAX_TARGETS:
            raise ProtocolError(
                "Firing room history exhausted; credit is never renewed by eviction"
            )
        self._best[key] = max(self._best.get(key, 0.0), value)
        return key, value

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
        if not self._same_support(b.navigation.grid, b.firing, a.firing, start, end):
            self._baseline(after)
            return 0.0
        if math.hypot(end.x - start.x, end.y - start.y) <= 0.5:
            self._baseline(after)
            return 0.0
        shared_cells = sorted(set(b.firing.clear_cells).intersection(a.firing.clear_cells))
        coherent = self._shared_geometry(b.firing, a.firing, shared_cells)
        value = (
            self._potential(b.navigation.grid, coherent, end)
            if self._potential(b.navigation.grid, a.firing, end) is not None
            else None
        )
        old = self._best[context]
        self._best[context] = max(old, value or 0.0)
        # New geometry cannot lower the historical record to renew credit.
        self._baseline(after)
        room = context[:5]
        bonus = min(
            max(0.0, ROOM_REWARD_CAP - self._paid[room]),
            ROOM_REWARD_CAP * max(0.0, (value or 0.0) - old),
        )
        self._paid[room] += bonus
        return bonus + self._recovery(before, after, coherent)
