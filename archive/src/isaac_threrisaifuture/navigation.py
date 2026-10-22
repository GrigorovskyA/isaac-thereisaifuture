"""Known-map memory and navigation primitives (offline contract).

``FloorMap`` is the full layout and is oracle data. The policy only ever sees a
``KnownMap`` snapshot built from rooms the agent visited or legitimately saw through a
door. Secret and super-secret rooms stay hidden until visited. See openspec change
known-map-and-navigation.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
from numpy.typing import NDArray

from .episodes import DIRECTIONS, Action

Direction = Literal["left", "right", "up", "down"]
DoorState = Literal["open", "locked", "blocked"]
DoorStatus = Literal["open", "locked", "blocked", "wall", "unknown"]
RoomType = Literal[
    "start", "normal", "treasure", "shop", "boss", "miniboss", "secret", "super_secret"
]

MAP_OBSERVATION_VERSION = 1
ROOM_TYPES: tuple[RoomType, ...] = (
    "start",
    "normal",
    "treasure",
    "shop",
    "boss",
    "miniboss",
    "secret",
    "super_secret",
)
HIDDEN_TYPES: frozenset[str] = frozenset({"secret", "super_secret"})
MOVES: tuple[Direction, ...] = ("left", "right", "up", "down")  # BFS tie-break order
DELTA: dict[Direction, tuple[int, int]] = {
    "left": (-1, 0),
    "right": (1, 0),
    "up": (0, -1),
    "down": (0, 1),
}
OPPOSITE: dict[Direction, Direction] = {
    "left": "right",
    "right": "left",
    "up": "down",
    "down": "up",
}
# Hypothesis fixed by map observation version 1; changing it needs a new version.
WINDOW_RADIUS = 3
CELL_FEATURES = 4 + 4 + 4 + len(ROOM_TYPES)  # known, visited, cleared, current, open, closed, type
MAP_OBSERVATION_SIZE = (2 * WINDOW_RADIUS + 1) ** 2 * CELL_FEATURES


class NavigationError(ValueError):
    """A door or path request that cannot be honoured."""


class StaleMapEvent(ValueError):
    """A room event that is stale, replayed, or inconsistent with the known session."""


@dataclass(frozen=True)
class Room:
    id: int
    x: int
    y: int
    type: RoomType
    doors: dict[Direction, DoorState] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.type not in ROOM_TYPES:
            raise ValueError(f"Unknown room type: {self.type}")


def _neighbor_coords(room: Room, direction: Direction) -> tuple[int, int]:
    dx, dy = DELTA[direction]
    return room.x + dx, room.y + dy


@dataclass(frozen=True)
class FloorMap:
    """Full layout. Oracle data: never pass it to the policy, encoder or its logs."""

    rooms: tuple[Room, ...]
    start_id: int

    def __post_init__(self) -> None:
        by_id = {r.id: r for r in self.rooms}
        by_xy = {(r.x, r.y): r for r in self.rooms}
        if len(by_id) != len(self.rooms) or len(by_xy) != len(self.rooms):
            raise ValueError("Room ids and grid coordinates must be unique")
        if self.start_id not in by_id:
            raise ValueError("start_id is not a room of the floor")
        for room in self.rooms:
            for direction, state in room.doors.items():
                other = by_xy.get(_neighbor_coords(room, direction))
                if other is None or other.doors.get(OPPOSITE[direction]) != state:
                    raise ValueError(f"Door {direction} of room {room.id} has no matching door")

    def room(self, room_id: int) -> Room:
        for r in self.rooms:
            if r.id == room_id:
                return r
        raise KeyError(room_id)

    def at(self, x: int, y: int) -> Room | None:
        return next((r for r in self.rooms if (r.x, r.y) == (x, y)), None)


@dataclass(frozen=True)
class KnownRoom:
    id: int
    x: int
    y: int
    type: RoomType
    visited: bool
    cleared: bool
    doors: dict[Direction, DoorState]


@dataclass(frozen=True)
class KnownMap:
    """Policy-visible snapshot. Holds only discovered rooms and their known doors."""

    rooms: dict[int, KnownRoom]
    current_id: int

    def door_status(self, room_id: int, direction: Direction) -> DoorStatus:
        room = self.rooms[room_id]
        if direction in room.doors:
            return room.doors[direction]
        return "wall" if room.visited else "unknown"

    def neighbor(self, room_id: int, direction: Direction) -> int | None:
        """Known room behind a known door, else None."""
        room = self.rooms[room_id]
        if direction not in room.doors:
            return None
        dx, dy = DELTA[direction]
        return next(
            (r.id for r in self.rooms.values() if (r.x, r.y) == (room.x + dx, room.y + dy)), None
        )


def shortest_path(known: KnownMap, start_id: int, goal_id: int) -> tuple[Direction, ...] | None:
    """BFS over open known doors. Locked, blocked and unknown doors are never used.

    Returns the door directions to take (empty at the goal) or None when unreachable.
    """
    if start_id not in known.rooms or goal_id not in known.rooms:
        raise NavigationError("Start and goal must be known rooms")
    parents: dict[int, tuple[int, Direction] | None] = {start_id: None}
    queue = deque([start_id])
    while queue:
        current = queue.popleft()
        if current == goal_id:
            break
        for direction in MOVES:
            if known.door_status(current, direction) != "open":
                continue
            nxt = known.neighbor(current, direction)
            if nxt is not None and nxt not in parents:
                parents[nxt] = (current, direction)
                queue.append(nxt)
    if goal_id not in parents:
        return None
    steps: list[Direction] = []
    node = goal_id
    while (link := parents[node]) is not None:
        node, direction = link
        steps.append(direction)
    return tuple(reversed(steps))


def door_move(known: KnownMap, room_id: int, direction: Direction) -> Action:
    """Cardinal move action that walks through a door; refuses anything but an open door."""
    status = known.door_status(room_id, direction)
    if status != "open":
        raise NavigationError(f"Door {direction} of room {room_id} is {status}")
    return Action(move=DIRECTIONS.index(direction))


def next_move(known: KnownMap, goal_id: int) -> Action | None:
    """First move toward the goal from the current room, None if unreachable or already there."""
    path = shortest_path(known, known.current_id, goal_id)
    if not path:
        return None
    return door_move(known, known.current_id, path[0])


@dataclass(frozen=True)
class RoomEvent:
    """Synthetic room-change event. ``enter`` moves the agent, ``clear`` marks the current room."""

    session_id: str
    room_visit: int
    room_id: int
    kind: Literal["enter", "clear"] = "enter"


class MapTracker:
    """Builds the known map from room events; the hidden layout never leaves this object."""

    def __init__(self, floor: FloorMap) -> None:
        self._floor = floor
        self._session: str | None = None
        self._visit = 0
        self._current = floor.start_id
        self._visited: set[int] = {floor.start_id}
        self._cleared: set[int] = set()

    def start(self, session_id: str, room_visit: int = 1) -> None:
        """Begin a floor in the start room; resets all memory."""
        self._session = session_id
        self._visit = room_visit
        self._current = self._floor.start_id
        self._visited = {self._floor.start_id}
        self._cleared = set()

    def apply(self, event: RoomEvent) -> None:
        if self._session is None or event.session_id != self._session:
            raise StaleMapEvent("Event session does not match the running map session")
        if event.kind == "clear":
            if event.room_visit != self._visit or event.room_id != self._current:
                raise StaleMapEvent("Clear event is not for the current room visit")
            if event.room_id in self._cleared:
                raise StaleMapEvent("Replayed clear event")
            self._cleared.add(event.room_id)
            return
        if event.room_visit <= self._visit:
            raise StaleMapEvent("Stale or replayed room visit")
        here = self._floor.room(self._current)
        target = self._floor.room(event.room_id) if self._has(event.room_id) else None
        if target is None or not any(
            _neighbor_coords(here, d) == (target.x, target.y) and s == "open"
            for d, s in here.doors.items()
        ):
            raise StaleMapEvent("Entered room is not behind an open door of the current room")
        self._visit = event.room_visit
        self._current = event.room_id
        self._visited.add(event.room_id)

    def _has(self, room_id: int) -> bool:
        return any(r.id == room_id for r in self._floor.rooms)

    @property
    def known(self) -> KnownMap:
        """Snapshot with only visited rooms and rooms seen through a door."""
        shown: dict[int, dict[Direction, DoorState]] = {i: {} for i in self._visited}
        for rid in self._visited:
            room = self._floor.room(rid)
            for direction, state in room.doors.items():
                other = self._floor.at(*_neighbor_coords(room, direction))
                if other is None or (other.type in HIDDEN_TYPES and other.id not in self._visited):
                    continue
                shown[rid][direction] = state
                shown.setdefault(other.id, {})[OPPOSITE[direction]] = state
        rooms = {}
        for rid, doors in shown.items():
            r = self._floor.room(rid)
            rooms[rid] = KnownRoom(
                r.id, r.x, r.y, r.type, rid in self._visited, rid in self._cleared, doors
            )
        return KnownMap(rooms, self._current)


def encode_known_map(known: KnownMap) -> NDArray[np.float32]:
    """Fixed-size window centred on the current room (relative coordinates, no room ids)."""
    side = 2 * WINDOW_RADIUS + 1
    out = np.zeros((side, side, CELL_FEATURES), dtype=np.float32)
    here = known.rooms[known.current_id]
    for room in known.rooms.values():
        col, row = room.x - here.x + WINDOW_RADIUS, room.y - here.y + WINDOW_RADIUS
        if not (0 <= col < side and 0 <= row < side):
            continue
        cell = out[row, col]
        cell[0:4] = (1.0, room.visited, room.cleared, room.id == known.current_id)
        for i, direction in enumerate(MOVES):
            state = room.doors.get(direction)
            if state == "open":
                cell[4 + i] = 1.0
            elif state is not None:
                cell[8 + i] = 1.0
        cell[12 + ROOM_TYPES.index(room.type)] = 1.0
    return out.reshape(-1)
