"""Bounded cardinal paths over measured current-room geometry, all native shapes."""

import math
from collections import deque

from .actions import Direction
from .entities import Vec
from .navigation_wire import NavigationFrame, NavigationGrid, OpenDoor
from .observation import Position

# Native DoorSlot LEFT0..DOWN0 followed by LEFT1..DOWN1.
OUTWARD: tuple[tuple[int, int], ...] = ((-1, 0), (0, -1), (1, 0), (0, 1))
NAMES: tuple[Direction, ...] = ("left", "up", "right", "down")


class NoRoomPath(ValueError):
    """No measured safe route; callers must not fall back to direct movement."""


def _index(grid: NavigationGrid, position: Vec | Position) -> int:
    x = math.floor((position.x - grid.origin.x) / grid.spacing + 0.5)
    y = math.floor((position.y - grid.origin.y) / grid.spacing + 0.5)
    if not (0 <= x < grid.width and 0 <= y < grid.height):
        raise NoRoomPath("Position lies outside measured navigation grid")
    index = y * grid.width + x
    if grid.walkable[index] != "1":
        raise NoRoomPath("Player or doorway approach cell is blocked")
    return index


def cell_position(grid: NavigationGrid, index: int) -> Vec:
    return Vec(
        x=grid.origin.x + (index % grid.width) * grid.spacing,
        y=grid.origin.y + (index // grid.width) * grid.spacing,
    )


def _door_corridor(grid: NavigationGrid, player: Vec | Position, door: OpenDoor) -> bool:
    """The final open-door crossing may leave the interior safe-cell mask."""
    dx, dy = OUTWARD[door.slot % 4]
    ax = door.position.x - dx * grid.spacing
    ay = door.position.y - dy * grid.spacing
    along = (player.x - ax) * dx + (player.y - ay) * dy
    across = abs((player.x - ax) * dy - (player.y - ay) * dx)
    return 0 <= along <= grid.spacing and across <= 8


def room_path(nav: NavigationFrame, player: Vec | Position, door: OpenDoor) -> list[int]:
    """BFS visits at most grid.width*grid.height<=1024 nodes; no row wrapping."""
    grid = nav.grid
    if nav.version != 2 or grid is None:
        raise NoRoomPath("Measured navigation grid v2 is required")
    if door not in nav.doors:
        raise NoRoomPath("Door is not currently open")
    dx, dy = OUTWARD[door.slot % 4]
    approach = Vec(x=door.position.x - dx * grid.spacing, y=door.position.y - dy * grid.spacing)
    goal = _index(grid, approach)
    measured = cell_position(grid, goal)
    if abs(measured.x - approach.x) > 1 or abs(measured.y - approach.y) > 1:
        raise NoRoomPath("Door approach is not on the measured lattice")
    if _door_corridor(grid, player, door):
        return [goal]
    start = _index(grid, player)
    queue = deque([start])
    previous: dict[int, int | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            result = [goal]
            parent = previous[goal]
            while parent is not None:
                result.append(parent)
                parent = previous[parent]
            return list(reversed(result))
        x, y = current % grid.width, current // grid.width
        for ox, oy in OUTWARD:
            nx, ny = x + ox, y + oy
            if 0 <= nx < grid.width and 0 <= ny < grid.height:
                nxt = ny * grid.width + nx
                if grid.walkable[nxt] == "1" and nxt not in previous:
                    previous[nxt] = current
                    queue.append(nxt)
    raise NoRoomPath("No safe path to the doorway approach")


def path_pulse(
    nav: NavigationFrame, player: Vec | Position, door: OpenDoor
) -> tuple[Direction, int]:
    """Replan; compress the first straight segment and align before turning."""
    path = room_path(nav, player, door)
    grid = nav.grid
    assert grid is not None
    if len(path) == 1:
        target = cell_position(grid, path[0])
        if (
            _door_corridor(grid, player, door)
            or max(abs(target.x - player.x), abs(target.y - player.y)) <= 8
        ):
            return NAMES[door.slot % 4], 6  # only the final approach may cross the boundary
        horizontal = abs(target.x - player.x) >= abs(target.y - player.y)
    else:
        step = path[1] - path[0]
        end = 1
        while end + 1 < len(path) and path[end + 1] - path[end] == step:
            end += 1
        target = cell_position(grid, path[end])
        horizontal = abs(step) == 1
        # Correct perpendicular displacement inside the current admitted cell.
        if horizontal and abs(target.y - player.y) > 8:
            horizontal = False
        elif not horizontal and abs(target.x - player.x) > 8:
            horizontal = True
    delta = target.x - player.x if horizontal else target.y - player.y
    direction: Direction = (
        ("right" if delta > 0 else "left") if horizontal else ("down" if delta > 0 else "up")
    )
    # A one-frame lease can expire at the next input callback before being sampled.
    # Keep at least one sampling frame while retaining short bounded corrections.
    return direction, max(2, min(6, int(abs(delta) / 6)))
