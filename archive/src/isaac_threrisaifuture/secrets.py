"""Offline secret-room discovery contract (roadmap item 15).

Policy path: ``rank_candidates``, ``SearchBudget``, ``run_search`` use only known (public)
layout cells. Oracle truth is accepted solely by ``evaluate_against_truth`` (evaluation only).
Not verified against the real game.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Literal

Cell = tuple[int, int]
SCHEMA_VERSION = "secret-discovery-v1"
GRID_SIZE = 13
_NEIGHBORS: tuple[Cell, ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _adjacent(cell: Cell) -> list[Cell]:
    return [(cell[0] + dx, cell[1] + dy) for dx, dy in _NEIGHBORS]


def _valid_walls(known: frozenset[Cell], excluded: frozenset[Cell], grid: int) -> list[Cell]:
    """Empty in-bounds cells adjacent to at least one known room, in sorted order."""
    cells = {
        n
        for room in known
        for n in _adjacent(room)
        if 0 <= n[0] < grid and 0 <= n[1] < grid and n not in known and n not in excluded
    }
    return sorted(cells)


@dataclass(frozen=True)
class Candidate:
    cell: Cell
    score: float
    neighbors: int
    explanation: str


def rank_candidates(
    known_rooms: Iterable[Cell],
    *,
    excluded: Iterable[Cell] = (),
    min_neighbors: int = 2,
    grid_size: int = GRID_SIZE,
) -> list[Candidate]:
    """Rank empty cells by the number of adjacent known rooms (public layout only).

    Ordinary secret rooms are expected next to at least two known rooms, so the default
    ``min_neighbors`` is 2. Exceptional layouts may lower it to 1; such cells score lower
    per neighbor count and are explained as exceptional. Ties break by cell coordinates.
    """
    if min_neighbors < 1:
        raise ValueError("min_neighbors must be >= 1")
    known = frozenset(known_rooms)
    ranked: list[Candidate] = []
    for cell in _valid_walls(known, frozenset(excluded), grid_size):
        n = sum(1 for a in _adjacent(cell) if a in known)
        if n < min_neighbors:
            continue
        kind = "ordinary" if n >= 2 else "exceptional"
        ranked.append(
            Candidate(cell, float(n), n, f"{kind}: empty cell adjacent to {n} known room(s)")
        )
    return sorted(ranked, key=lambda c: (-c.score, c.cell))


@dataclass(frozen=True)
class SearchBudget:
    max_bombs: int
    max_steps: int

    def __post_init__(self) -> None:
        if self.max_bombs < 0 or self.max_steps < 0:
            raise ValueError("budget values must be non-negative")


@dataclass(frozen=True)
class AttemptOutcome:
    found: bool
    steps: int = 1


@dataclass(frozen=True)
class AttemptRecord:
    candidate: Cell
    tool: Literal["bomb"]
    outcome: Literal["found", "not_found"]
    steps: int


StopReason = Literal["found", "bombs_exhausted", "steps_exhausted", "no_candidates"]


@dataclass(frozen=True)
class SearchResult:
    attempts: tuple[AttemptRecord, ...]
    stop_reason: StopReason

    @property
    def bombs_used(self) -> int:
        return len(self.attempts)

    @property
    def found(self) -> bool:
        return self.stop_reason == "found"


def run_search(
    known_rooms: Iterable[Cell],
    budget: SearchBudget,
    try_candidate: Callable[[Cell], AttemptOutcome],
    *,
    min_neighbors: int = 2,
    order: Callable[[list[Candidate]], list[Candidate]] | None = None,
) -> SearchResult:
    """Try ranked candidates until found or the budget/candidates run out.

    ``try_candidate`` is the environment: it must not expose hidden layout to this module.
    Tried cells are never retried. ``order`` lets a scripted baseline reorder candidates.
    """
    known = frozenset(known_rooms)
    candidates = rank_candidates(known, min_neighbors=min_neighbors)
    if order is not None:
        candidates = order(candidates)
    return run_search_fixed(candidates, budget, try_candidate)


@dataclass(frozen=True)
class DiscoveryComparison:
    """Evaluation result over a set of floors (oracle-derived; never a policy input)."""

    floors: int
    policy_found: int
    baseline_found: int
    policy_bombs: int
    baseline_bombs: int

    @property
    def policy_rate(self) -> float:
        return self.policy_found / self.floors if self.floors else 0.0

    @property
    def baseline_rate(self) -> float:
        return self.baseline_found / self.floors if self.floors else 0.0

    @property
    def policy_per_bomb(self) -> float:
        return self.policy_found / self.policy_bombs if self.policy_bombs else 0.0

    @property
    def baseline_per_bomb(self) -> float:
        return self.baseline_found / self.baseline_bombs if self.baseline_bombs else 0.0


@dataclass(frozen=True)
class FloorLabel:
    """Evaluation-only floor: public known rooms plus the hidden secret cell."""

    known_rooms: frozenset[Cell]
    secret_cell: Cell = field(repr=False)


def evaluate_against_truth(
    floors: Iterable[FloorLabel], budget: SearchBudget, seed: int
) -> DiscoveryComparison:
    """Evaluation only: compare ranked search with a seeded random valid-wall baseline.

    Both arms get the same bomb/step budget; each attempt costs one step. Not reachable
    from the policy path (nothing in the policy functions calls it or receives labels).
    """
    rng = random.Random(seed)
    n = p_found = b_found = p_bombs = b_bombs = 0
    for floor in floors:
        n += 1
        truth = floor.secret_cell

        def probe(cell: Cell, truth: Cell = truth) -> AttemptOutcome:
            return AttemptOutcome(found=cell == truth)

        policy = run_search(floor.known_rooms, budget, probe)
        walls = _valid_walls(floor.known_rooms, frozenset(), GRID_SIZE)
        rng.shuffle(walls)
        base = _run_order(walls, budget, probe)
        p_found += policy.found
        b_found += base.found
        p_bombs += policy.bombs_used
        b_bombs += base.bombs_used
    return DiscoveryComparison(n, p_found, b_found, p_bombs, b_bombs)


def _run_order(
    cells: list[Cell], budget: SearchBudget, probe: Callable[[Cell], AttemptOutcome]
) -> SearchResult:
    shuffled = [Candidate(c, 0.0, 0, "random valid wall") for c in cells]
    return run_search_fixed(shuffled, budget, probe)


def run_search_fixed(
    candidates: list[Candidate], budget: SearchBudget, probe: Callable[[Cell], AttemptOutcome]
) -> SearchResult:
    attempts: list[AttemptRecord] = []
    steps = 0
    for cand in candidates:
        if len(attempts) >= budget.max_bombs:
            return SearchResult(tuple(attempts), "bombs_exhausted")
        if steps >= budget.max_steps:
            return SearchResult(tuple(attempts), "steps_exhausted")
        out = probe(cand.cell)
        steps += max(out.steps, 0)
        attempts.append(
            AttemptRecord(cand.cell, "bomb", "found" if out.found else "not_found", out.steps)
        )
        if out.found:
            return SearchResult(tuple(attempts), "found")
    return SearchResult(tuple(attempts), "no_candidates")
