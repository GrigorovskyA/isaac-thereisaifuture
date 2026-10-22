"""Directed ordinary-room routes learned from travel, never a hidden floor map."""

from collections import deque


class NoObservedRoute(ValueError):
    """No reachable frontier remains in the observed eligible exits."""


class ObservedRoutes:
    def __init__(self) -> None:
        self.doors: dict[int, tuple[int, ...]] = {}
        self.edges: dict[tuple[int, int], int] = {}
        self.reachable: dict[int, set[int]] = {}

    def observe(self, room: int, slots: list[int]) -> None:
        observed = tuple(sorted(slots))
        if self.doors.get(room) != observed:
            self.reachable.pop(room, None)
        self.doors[room] = observed

    def connect(self, room: int, slot: int, destination: int) -> None:
        self.edges[room, slot] = destination

    def choose(self, room: int, reachable: set[int]) -> int:
        self.reachable[room] = set(reachable)
        unexplored = {
            index
            for index, slots in self.doors.items()
            if any((index, slot) not in self.edges for slot in slots)
        }
        frontiers = {
            index
            for index, slots in self.doors.items()
            if any(
                (index, slot) not in self.edges and slot in self.reachable.get(index, set(slots))
                for slot in slots
            )
        }
        for slot in self.doors.get(room, ()):
            if slot in reachable and (room, slot) not in self.edges:
                return slot
        queue: deque[tuple[int, int | None]] = deque([(room, None)])
        seen = {room}
        while queue:
            current, first = queue.popleft()
            if current != room and current in frontiers:
                assert first is not None
                return first
            for slot in self.doors.get(current, ()):
                if slot not in self.reachable.get(current, set(self.doors[current])):
                    continue
                destination = self.edges.get((current, slot))
                if destination is not None and destination not in seen:
                    seen.add(destination)
                    queue.append((destination, slot if first is None else first))
        if unexplored:
            raise NoObservedRoute("Observed ordinary-room frontier is unreachable")
        raise NoObservedRoute("Observed ordinary-room component exhausted")
