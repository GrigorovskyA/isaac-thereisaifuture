"""Hand-written obstacle-aware diagnostic baseline, never a learned policy.

Uses only the exported observation vector. Unknown blockers remain unknown; this
local approximation is neither engine pathfinding nor projectile collision proof.
"""

import math
from collections import deque

import numpy as np
from numpy.typing import NDArray

from .encoding import CAPACITY, OBSERVATION_SIZE, PLAYER_FEATURES, SLOT_FEATURES


class ApproachDiagnosticPolicy:
    name = "approach-diagnostic"
    label = "scripted-diagnostic-not-learned"

    def reset(self, seed: int) -> None:
        pass

    def act(self, observation: NDArray[np.float32]) -> NDArray[np.int64]:
        if observation.shape != (OBSERVATION_SIZE,) or not np.isfinite(observation).all():
            raise ValueError("Expected a finite encoded observation")
        if observation[PLAYER_FEATURES] < 0.5:
            return np.zeros(2, dtype=np.int64)
        ex, ey = (float(v) * 1000 for v in observation[10:12])
        offset = PLAYER_FEATURES + SLOT_FEATURES * (CAPACITY["enemy"] + CAPACITY["projectile"])
        obstacles = [
            (float(observation[i + 1]) * 1000, float(observation[i + 2]) * 1000)
            for i in range(offset, offset + SLOT_FEATURES * CAPACITY["obstacle"], SLOT_FEATURES)
            if observation[i] >= 0.5
        ]

        def open_cell(x: float, y: float) -> bool:
            return all(math.hypot(x - ox, y - oy) >= 27 for ox, oy in obstacles)

        def shot(x: float, y: float) -> int:
            dx, dy = ex - x, ey - y
            length2 = dx * dx + dy * dy
            if not 60**2 <= length2 <= 220**2 or min(abs(dx), abs(dy)) > 12:
                return 0
            for ox, oy in obstacles:
                t = max(0.0, min(1.0, ((ox - x) * dx + (oy - y) * dy) / length2))
                if math.hypot(ox - x - t * dx, oy - y - t * dy) < 24:
                    return 0
            return (2 if dx > 0 else 1) if abs(dx) >= abs(dy) else (4 if dy > 0 else 3)

        current_shot = shot(0, 0)
        if current_shot:
            return np.array([0, current_shot], dtype=np.int64)
        start = (0, 0)
        parents: dict[tuple[int, int], tuple[tuple[int, int], int] | None] = {start: None}
        queue = deque([start])
        closest = start
        goal = None
        while queue:
            cell = queue.popleft()
            x, y = cell[0] * 20, cell[1] * 20
            if math.hypot(ex - x, ey - y) < math.hypot(ex - closest[0] * 20, ey - closest[1] * 20):
                closest = cell
            if cell != start and shot(x, y):
                goal = cell
                break
            for direction, (dx, dy) in enumerate(((-1, 0), (1, 0), (0, -1), (0, 1)), 1):
                nxt = cell[0] + dx, cell[1] + dy
                if (
                    abs(nxt[0]) <= 20
                    and abs(nxt[1]) <= 20
                    and nxt not in parents
                    and open_cell(nxt[0] * 20, nxt[1] * 20)
                ):
                    parents[nxt] = (cell, direction)
                    queue.append(nxt)
        end = goal if goal is not None else closest
        direction = 0
        while parents[end] is not None:
            parent = parents[end]
            assert parent is not None
            previous, direction = parent
            if previous == start:
                break
            end = previous
        return np.array([direction, 0], dtype=np.int64)
