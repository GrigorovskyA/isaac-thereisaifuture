"""Observed directed routes only; no native game or hidden neighbor data."""

import pytest

from isaac_threrisaifuture.observed_routes import NoObservedRoute, ObservedRoutes


def test_backtrack_to_observed_frontier_without_inventing_reverse_edges():
    routes = ObservedRoutes()
    routes.observe(1, [0, 2])
    routes.observe(2, [0])
    routes.connect(1, 0, 2)
    assert routes.choose(2, {0}) == 0  # reverse direction is still unexplored
    routes.connect(2, 0, 1)
    assert routes.choose(2, {0}) == 0  # confirmed path back to room 1's frontier
    assert routes.choose(1, {0, 2}) == 2


def test_closed_observed_cycle_stops_without_claiming_floor_clear():
    routes = ObservedRoutes()
    routes.observe(1, [2])
    routes.observe(2, [0])
    routes.connect(1, 2, 2)
    routes.connect(2, 0, 1)
    with pytest.raises(NoObservedRoute, match="Observed ordinary-room component exhausted"):
        routes.choose(1, {2})


def test_frontier_requires_current_measured_first_hop():
    routes = ObservedRoutes()
    routes.observe(1, [2])
    routes.observe(2, [0, 2])
    routes.connect(1, 2, 2)
    with pytest.raises(NoObservedRoute, match="frontier is unreachable"):
        routes.choose(1, set())
    assert routes.choose(1, {2}) == 2


def test_closed_observed_door_is_not_used_from_stale_connection():
    routes = ObservedRoutes()
    routes.observe(1, [2])
    routes.connect(1, 2, 2)
    routes.observe(2, [0])
    routes.observe(1, [])
    with pytest.raises(NoObservedRoute, match="frontier is unreachable"):
        routes.choose(1, {2})


def test_unexplored_local_exit_without_path_is_unreachable_not_exhausted():
    routes = ObservedRoutes()
    routes.observe(1, [2])
    with pytest.raises(NoObservedRoute, match="frontier is unreachable"):
        routes.choose(1, set())


def test_two_blocked_frontiers_do_not_send_the_search_back_and_forth():
    routes = ObservedRoutes()
    routes.observe(1, [0, 2])
    routes.observe(2, [0, 2])
    routes.connect(1, 2, 2)
    routes.connect(2, 0, 1)
    assert routes.choose(1, {2}) == 2  # room 2's unexplored exit has not been measured yet
    with pytest.raises(NoObservedRoute, match="frontier is unreachable"):
        routes.choose(2, {0})  # both remaining exits have now been measured unreachable


def test_changed_observed_doors_and_fresh_paths_can_reopen_a_frontier():
    routes = ObservedRoutes()
    routes.observe(1, [0])
    with pytest.raises(NoObservedRoute, match="frontier is unreachable"):
        routes.choose(1, set())
    routes.observe(1, [0, 2])
    assert routes.choose(1, {0, 2}) == 0


def test_known_blocked_intermediate_edges_cannot_sustain_a_route_cycle():
    routes = ObservedRoutes()
    for room in (1, 2):
        routes.observe(room, [0, 2])
    routes.observe(3, [2])
    routes.connect(1, 0, 2)
    routes.connect(2, 0, 1)
    routes.connect(1, 2, 3)
    routes.connect(2, 2, 3)
    assert routes.choose(1, {0}) == 0  # room 2's route has not been remeasured yet
    with pytest.raises(NoObservedRoute, match="frontier is unreachable"):
        routes.choose(2, {0})  # both previously confirmed routes to room 3 are now blocked
