from dataclasses import replace

import pytest

from isaac_threrisaifuture.combat_spatial_diagnostics import (
    MotionPoint,
    measured_route,
    motion_proxy,
)
from isaac_threrisaifuture.entities import Vec
from isaac_threrisaifuture.navigation_wire import NavigationGrid


def point(**changes):
    return replace(MotionPoint("a" * 32, 1, 0, 10, Vec(x=0.0, y=0.0), "right"), **changes)


def test_motion_projection_and_inertia_are_not_collision_labels():
    before = point()
    after = point(frame_id=14, position=Vec(x=-2.0, y=3.0))
    result = motion_proxy(before, after)
    assert result is not None and result.movement_requested
    assert result.progress_along_command == -2
    assert result.distance == pytest.approx(13**0.5)
    assert not result.near_stationary


@pytest.mark.parametrize("move", ["left", "right", "up", "down"])
def test_requested_but_stationary_movement(move):
    result = motion_proxy(point(move=move), point(frame_id=13, position=Vec(x=0.1, y=0.1)))
    assert result is not None and result.near_stationary


def test_idle_is_not_a_failed_movement():
    result = motion_proxy(point(move="none"), point(frame_id=13))
    assert result is not None and not result.movement_requested and not result.near_stationary


@pytest.mark.parametrize(
    "change",
    [
        {"session_id": "b" * 32},
        {"game_epoch": 2},
        {"room_visit": 1},
        {"frame_id": 10},
        {"frame_id": 9},
        {"frame_id": 26},
    ],
)
def test_context_and_time_gaps_are_unavailable(change):
    assert motion_proxy(point(), point(**({"frame_id": 14} | change))) is None


def grid(mask):
    return NavigationGrid(
        origin=Vec(x=0.0, y=0.0),
        spacing=40,
        width=len(mask[0]),
        height=len(mask),
        walkable="".join(mask),
    )


def test_grid_route_takes_detour_without_using_blocked_cells():
    g = grid(["11111", "10001", "11111"])
    path = measured_route(g, Vec(x=0.0, y=40.0), Vec(x=160.0, y=40.0))
    assert path is not None and len(path) - 1 == 6
    assert path[0] == (0, 1) and path[-1] == (4, 1)
    assert all(g.walkable[y * g.width + x] == "1" for x, y in path)
    assert all(abs(x - u) + abs(y - v) == 1 for (x, y), (u, v) in zip(path, path[1:], strict=False))


@pytest.mark.parametrize(
    "start,goal",
    [
        ((-1.0, 40.0), (160.0, 40.0)),
        ((0.0, 40.0), (161.0, 40.0)),
        ((40.0, 40.0), (160.0, 40.0)),
    ],
)
def test_invalid_grid_endpoints_are_not_snapped(start, goal):
    assert (
        measured_route(
            grid(["11111", "10001", "11111"]),
            Vec(x=start[0], y=start[1]),
            Vec(x=goal[0], y=goal[1]),
        )
        is None
    )


def test_disconnected_and_same_cell_routes():
    g = grid(["11011", "11011", "11011"])
    assert measured_route(g, Vec(x=0.0, y=40.0), Vec(x=160.0, y=40.0)) is None
    assert measured_route(g, Vec(x=0.0, y=40.0), Vec(x=0.0, y=40.0)) == ((0, 1),)
