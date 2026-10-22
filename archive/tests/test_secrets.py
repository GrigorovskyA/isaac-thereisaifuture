"""Offline tests for secret-room discovery. Floors here are SYNTHETIC fixtures, not Isaac."""

from __future__ import annotations

import inspect
import random

from isaac_threrisaifuture import secrets
from isaac_threrisaifuture.secrets import (
    AttemptOutcome,
    FloorLabel,
    SearchBudget,
    evaluate_against_truth,
    rank_candidates,
    run_search,
)


def synthetic_floor(seed: int) -> FloorLabel:
    """SYNTHETIC: random blob of rooms; secret placed at a cell touching >= 2 rooms."""
    rng = random.Random(seed)
    rooms = {(6, 6)}
    while len(rooms) < 10:
        x, y = rng.choice(sorted(rooms))
        dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        if 0 <= x + dx < 13 and 0 <= y + dy < 13:
            rooms.add((x + dx, y + dy))
    known = frozenset(rooms)
    options = rank_candidates(known)
    if not options:
        return synthetic_floor(seed + 1000)
    return FloorLabel(known, rng.choice(options).cell)


def test_ranking_is_deterministic_and_explained() -> None:
    known = {(5, 5), (6, 6), (5, 7)}
    a = rank_candidates(known)
    assert a == rank_candidates(known)
    assert a[0].cell == (5, 6) and a[0].neighbors == 3
    assert all(c.neighbors >= 2 and "ordinary" in c.explanation for c in a)


def test_exceptional_single_neighbor_layouts_are_opt_in() -> None:
    known = {(6, 6)}
    assert rank_candidates(known) == []
    single = rank_candidates(known, min_neighbors=1)
    assert len(single) == 4 and "exceptional" in single[0].explanation


def test_grid_bounds_and_exclusions() -> None:
    assert all(0 <= c.cell[0] < 13 for c in rank_candidates({(0, 0), (1, 1)}))
    assert (0, 1) not in {c.cell for c in rank_candidates({(0, 0), (1, 1)}, excluded=[(0, 1)])}


def test_scoring_signatures_have_no_oracle_inputs() -> None:
    for fn in (rank_candidates, run_search):
        names = set(inspect.signature(fn).parameters)
        assert not names & {"truth", "secret_cell", "label", "floor", "oracle"}
    assert "secret_cell" not in inspect.getsource(rank_candidates)
    assert "secret_cell" not in inspect.getsource(run_search)
    assert "evaluate_against_truth" not in inspect.getsource(run_search)
    assert hasattr(secrets, "evaluate_against_truth")


def test_budget_stops_search_and_records_attempts() -> None:
    known = {(5, 5), (6, 6), (5, 7), (7, 5), (7, 7)}
    never = run_search(known, SearchBudget(2, 100), lambda c: AttemptOutcome(False))
    assert never.stop_reason == "bombs_exhausted" and never.bombs_used == 2
    assert all(a.tool == "bomb" and a.outcome == "not_found" for a in never.attempts)
    slow = run_search(known, SearchBudget(10, 3), lambda c: AttemptOutcome(False, steps=2))
    assert slow.stop_reason == "steps_exhausted" and slow.bombs_used == 2
    none = run_search({(6, 6)}, SearchBudget(5, 5), lambda c: AttemptOutcome(False))
    assert none.stop_reason == "no_candidates"


def test_found_stops_and_no_retry() -> None:
    known = {(5, 5), (6, 6), (5, 7)}
    seen: list[tuple[int, int]] = []

    def probe(cell: tuple[int, int]) -> AttemptOutcome:
        seen.append(cell)
        return AttemptOutcome(found=cell == (5, 6))

    res = run_search(known, SearchBudget(5, 5), probe)
    assert res.found and res.attempts[-1].outcome == "found"
    assert len(seen) == len(set(seen))


def test_baseline_comparison_is_deterministic_and_policy_wins() -> None:
    floors = [synthetic_floor(s) for s in range(200)]
    budget = SearchBudget(max_bombs=3, max_steps=3)
    first = evaluate_against_truth(floors, budget, seed=7)
    assert first == evaluate_against_truth(floors, budget, seed=7)
    assert first.floors == 200
    assert first.policy_rate > first.baseline_rate
    assert first.policy_per_bomb >= first.baseline_per_bomb
