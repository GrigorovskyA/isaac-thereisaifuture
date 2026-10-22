"""Offline-only motion and measured walking-grid diagnostics; never a controller.

Future poses and management grids are analysis data, not policy inputs. A short
movement or blocked walking cell is not proof of a projectile collision.
"""

import math
from collections import deque
from dataclasses import dataclass

from .actions import Direction
from .entities import Vec
from .navigation_wire import NavigationGrid

MOVE_VECTOR = {"none": (0, 0), "left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}
Cell = tuple[int, int]


@dataclass(frozen=True)
class MotionPoint:
    session_id: str
    game_epoch: int
    room_visit: int
    frame_id: int
    position: Vec
    move: Direction


@dataclass(frozen=True)
class MotionProxy:
    frame_gap: int
    movement_requested: bool
    distance: float
    progress_along_command: float
    near_stationary: bool


def motion_proxy(before: MotionPoint, after: MotionPoint) -> MotionProxy | None:
    """Return unavailable across context changes or gaps; do not infer collisions."""
    if before.move not in MOVE_VECTOR or after.move not in MOVE_VECTOR:
        raise ValueError("Unknown movement direction")

    def context(p: MotionPoint) -> tuple[str, int, int]:
        return p.session_id, p.game_epoch, p.room_visit

    gap = after.frame_id - before.frame_id
    if context(before) != context(after) or not 1 <= gap <= 15:
        return None
    dx, dy = after.position.x - before.position.x, after.position.y - before.position.y
    sx, sy = MOVE_VECTOR[before.move]
    distance = math.hypot(dx, dy)
    requested = before.move != "none"
    return MotionProxy(gap, requested, distance, dx * sx + dy * sy, requested and distance < 0.5)


def measured_route(grid: NavigationGrid, start: Vec, goal: Vec) -> tuple[Cell, ...] | None:
    """Cardinal shortest route on a measured mask, not a live combat path command."""

    def cell(position: Vec) -> Cell | None:
        x = (position.x - grid.origin.x) / grid.spacing
        y = (position.y - grid.origin.y) / grid.spacing
        if not 0 <= x <= grid.width - 1 or not 0 <= y <= grid.height - 1:
            return None
        return math.floor(x + 0.5), math.floor(y + 0.5)

    a, b = cell(start), cell(goal)
    if a is None or b is None:
        return None

    def walkable(c: Cell) -> bool:
        x, y = c
        return (
            0 <= x < grid.width
            and 0 <= y < grid.height
            and grid.walkable[y * grid.width + x] == "1"
        )

    if not walkable(a) or not walkable(b):
        return None
    parents: dict[Cell, Cell | None] = {a: None}
    queue = deque([a])
    while queue:
        current = queue.popleft()
        if current == b:
            path = [b]
            while (previous := parents[path[-1]]) is not None:
                path.append(previous)
            return tuple(reversed(path))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nxt = current[0] + dx, current[1] + dy
            if walkable(nxt) and nxt not in parents:
                parents[nxt] = current
                queue.append(nxt)
    return None
