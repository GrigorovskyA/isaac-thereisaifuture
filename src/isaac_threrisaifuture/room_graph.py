"""Floor graph of the rooms the agent has seen, for reward v10 door shaping (reward labels only).

Nodes are level grid indexes. An edge is a door of a room the player stood in; it is usable when
the door is not locked and does not lead to a closed secret room. Hop counts say how many rooms
the agent still has to cross to reach a goal: a room it has never entered, or the boss room.
Nothing here reaches the policy, the encoder or the recurrent state.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from .entities import OracleDoor


class RoomGraph:
    """Rooms and doors seen on the current floor; cleared by `clear` and on a floor change."""

    def __init__(self) -> None:
        self._floor: tuple[int, int] | None = None
        self.visited: set[int] = set()
        self.edges: dict[int, dict[int, bool]] = {}  # room -> target room -> usable
        self.boss: int | None = None

    def clear(self) -> None:
        self._floor = None
        self.visited.clear()
        self.edges.clear()
        self.boss = None

    def observe(
        self,
        floor: tuple[int, int],
        room_grid: int,
        doors: Sequence[OracleDoor],
        *,
        boss_room: bool,
    ) -> None:
        """Record the room the player stands in and its doors; a new floor starts a new graph."""
        if floor != self._floor:
            self.clear()
            self._floor = floor
        self.visited.add(room_grid)
        edges: dict[int, bool] = {}
        for door in doors:
            if door.target >= 0:
                edges[door.target] = edges.get(door.target, False) or door.usable
        self.edges[room_grid] = edges
        if boss_room:
            self.boss = room_grid

    def hops(self) -> dict[int, int]:
        """Hop distance to the nearest goal for every room that has a path to one.

        Goals have distance 0: unvisited targets of known usable doors and the boss room. A
        visited room is one more than its best usable neighbour. Other rooms are absent.
        """
        reverse: dict[int, list[int]] = {}
        goals: set[int] = set()
        for room, edges in self.edges.items():
            for target, usable in edges.items():
                if not usable:
                    continue
                reverse.setdefault(target, []).append(room)
                if target not in self.visited:
                    goals.add(target)
        if self.boss is not None:
            goals.add(self.boss)
        distance = dict.fromkeys(goals, 0)
        queue = deque(goals)
        while queue:
            room = queue.popleft()
            for previous in reverse.get(room, ()):
                if previous not in distance:
                    distance[previous] = distance[room] + 1
                    queue.append(previous)
        return distance
