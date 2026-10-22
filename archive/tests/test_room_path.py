"""Synthetic topology/steering checks for all twelve native room-shape families."""

import pytest
from pydantic import ValidationError

from isaac_threrisaifuture.entities import Vec
from isaac_threrisaifuture.navigation_wire import NavigationFrame, NavigationGrid, OpenDoor
from isaac_threrisaifuture.room_path import NoRoomPath, cell_position, path_pulse, room_path


def shape_grid(shape):
    width = 15 if shape <= 5 else 28
    height = 9 if shape <= 3 or shape in (6, 7) else 16
    cells = set()
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if shape in (2, 7) and not 3 <= y <= 5:
                continue
            if shape in (3, 5) and not 6 <= x <= 8:
                continue
            # Four rotated missing quadrants; no rectangular-envelope shortcut.
            if shape >= 9:
                missing_left = shape in (9, 11)
                missing_top = shape in (9, 10)
                if (x < width // 2) == missing_left and (y < height // 2) == missing_top:
                    continue
            cells.add(y * width + x)
    return NavigationGrid(
        origin=Vec(x=40.0, y=120.0),
        spacing=40,
        width=width,
        height=height,
        walkable="".join("1" if i in cells else "0" for i in range(width * height)),
    )


def navigation(grid, shape, slot, goal):
    target = cell_position(grid, goal)
    ox, oy = ((-1, 0), (0, -1), (1, 0), (0, 1))[slot % 4]
    door = OpenDoor(slot=slot, position=Vec(x=target.x + ox * 40, y=target.y + oy * 40))
    return NavigationFrame(
        version=2,
        room_index=1,
        stage=1,
        stage_type=0,
        room_type=1,
        shape=shape,
        grid=grid,
        doors=[door],
    )


@pytest.mark.parametrize("shape", range(1, 13))
def test_every_shape_route_remains_in_measured_connected_cells(shape):
    grid = shape_grid(shape)
    admitted = [i for i, c in enumerate(grid.walkable) if c == "1"]
    start, goal = admitted[0], admitted[-1]
    nav = navigation(grid, shape, 2, goal)
    path = room_path(nav, cell_position(grid, start), nav.doors[0])
    assert path[0] == start and path[-1] == goal
    assert all(grid.walkable[i] == "1" for i in path)
    assert all(
        abs(a % grid.width - b % grid.width) + abs(a // grid.width - b // grid.width) == 1
        for a, b in zip(path, path[1:], strict=False)
    )
    assert len(path) <= grid.width * grid.height


@pytest.mark.parametrize("shape", range(9, 13))
def test_each_rotated_l_routes_between_arms_without_crossing_missing_corner(shape):
    grid = shape_grid(shape)
    cells = [i for i, c in enumerate(grid.walkable) if c == "1"]
    # Select endpoints in opposing arms, forcing a turn around the absent quadrant.
    left_missing = shape in (9, 11)
    top_missing = shape in (9, 10)
    x_vertical = grid.width - 2 if left_missing else 1
    y_horizontal = grid.height - 2 if top_missing else 1
    start = (1 if top_missing else grid.height - 2) * grid.width + x_vertical
    goal = y_horizontal * grid.width + (1 if left_missing else grid.width - 2)
    assert start in cells and goal in cells
    nav = navigation(grid, shape, 2, goal)
    path = room_path(nav, cell_position(grid, start), nav.doors[0])
    assert any(abs(b - a) == grid.width for a, b in zip(path, path[1:], strict=False))
    assert any(abs(b - a) == 1 for a, b in zip(path, path[1:], strict=False))
    assert all(grid.walkable[i] == "1" for i in path)


@pytest.mark.parametrize("slot", range(8))
def test_all_primary_and_secondary_slots_cross_in_the_correct_direction(slot):
    grid = shape_grid(8)
    goal = 5 * grid.width + 5
    nav = navigation(grid, 8, slot, goal)
    assert path_pulse(nav, cell_position(grid, goal), nav.doors[0]) == (
        ("left", "up", "right", "down")[slot % 4],
        6,
    )


def test_obstacle_detour_and_dynamic_blocking_have_no_direct_fallback():
    grid = shape_grid(1)
    w = grid.width
    start, goal = 4 * w + 2, 4 * w + 12
    mask = list(grid.walkable)
    for y in range(1, 7):
        mask[y * w + 7] = "0"
    grid = grid.model_copy(update={"walkable": "".join(mask)})
    nav = navigation(grid, 1, 2, goal)
    position = cell_position(grid, start)
    route = room_path(nav, position, nav.doors[0])
    assert max(i // w for i in route) == 7  # real detour around the wall's lower end
    mask[7 * w + 7] = "0"
    blocked = nav.model_copy(update={"grid": grid.model_copy(update={"walkable": "".join(mask)})})
    with pytest.raises(NoRoomPath):
        path_pulse(blocked, position, nav.doors[0])


@pytest.mark.parametrize(
    "changes",
    [
        {"width": 33},
        {"width": True},
        {"height": 0},
        {"spacing": 20},
        {"walkable": "1"},
        {"walkable": "2" * 135},
        {"origin": {"x": float("nan"), "y": 0.0}},
    ],
)
def test_invalid_geometry_is_rejected_at_transport_boundary(changes):
    data = shape_grid(1).model_dump()
    data.update(changes)
    with pytest.raises(ValidationError):
        NavigationGrid.model_validate(data)


def test_misaligned_door_and_blocked_player_are_rejected():
    grid = shape_grid(1)
    nav = navigation(grid, 1, 2, 4 * grid.width + 12)
    with pytest.raises(NoRoomPath):
        room_path(nav, cell_position(grid, 0), nav.doors[0])
    bad = nav.doors[0].model_copy(update={"position": Vec(x=nav.doors[0].position.x + 10, y=280.0)})
    nav = nav.model_copy(update={"doors": [bad]})
    with pytest.raises(NoRoomPath):
        room_path(nav, cell_position(grid, 4 * grid.width + 2), bad)


@pytest.mark.parametrize("shape", range(1, 13))
def test_pulse_following_reaches_approach_without_cutting_walls(shape):
    grid = shape_grid(shape)
    cells = [i for i, c in enumerate(grid.walkable) if c == "1"]
    position = cell_position(grid, cells[0])
    goal = cell_position(grid, cells[-1])
    nav = navigation(grid, shape, 2, cells[-1])
    for _ in range(128):
        if max(abs(position.x - goal.x), abs(position.y - goal.y)) <= 8:
            break
        direction, frames = path_pulse(nav, position, nav.doors[0])
        ox, oy = {"left": (-1, 0), "up": (0, -1), "right": (1, 0), "down": (0, 1)}[direction]
        for _ in range(frames):
            position = Vec(x=position.x + ox * 5, y=position.y + oy * 5)
            x = round((position.x - grid.origin.x) / 40)
            y = round((position.y - grid.origin.y) / 40)
            assert 0 <= x < grid.width and 0 <= y < grid.height
            assert grid.walkable[y * grid.width + x] == "1"
    else:
        pytest.fail("Steering failed to reach the doorway approach in 128 pulses")


def test_row_boundaries_and_legacy_geometry_cannot_create_shortcuts():
    grid = NavigationGrid(
        origin=Vec(x=0.0, y=0.0), spacing=40, width=3, height=3, walkable="001100000"
    )
    nav = navigation(grid, 1, 2, 3)
    with pytest.raises(NoRoomPath):
        room_path(nav, cell_position(grid, 2), nav.doors[0])
    legacy = nav.model_copy(update={"version": 1, "grid": None})
    with pytest.raises(NoRoomPath):
        room_path(legacy, cell_position(grid, 2), legacy.doors[0])


def test_observed_short_alignment_works_with_one_input_frame_sampling_margin():
    grid = shape_grid(7)
    # Replay the observed native stall offset against an unobstructed doorway approach.
    nav = navigation(grid, 7, 2, 4 * grid.width + 26)
    goal = cell_position(grid, 4 * grid.width + 26)
    position = Vec(x=goal.x + 9.7366943359, y=goal.y + 8.58288574219)
    for _ in range(8):
        direction, frames = path_pulse(nav, position, nav.doors[0])
        assert 2 <= frames <= 6
        if direction == "right":
            break
        ox, oy = {"left": (-1, 0), "up": (0, -1), "right": (1, 0), "down": (0, 1)}[direction]
        position = Vec(x=position.x + ox * (frames - 1) * 5, y=position.y + oy * (frames - 1) * 5)
    else:
        pytest.fail("Door alignment corrections never converged")


@pytest.mark.parametrize("slot", range(8))
def test_partial_open_door_crossing_continues_outward_without_centering_back(slot):
    grid = shape_grid(8)
    goal = 4 * grid.width + 26
    nav = navigation(grid, 8, slot, goal)
    door = nav.doors[0]
    ox, oy = ((-1, 0), (0, -1), (1, 0), (0, 1))[slot % 4]
    point = cell_position(grid, goal)
    position = Vec(x=point.x + ox * 30, y=point.y + oy * 30)
    # The corridor exception requires the observed open door and safe approach;
    # it is not a general nearest-cell fallback for blocked interior positions.
    assert path_pulse(nav, position, door) == (("left", "up", "right", "down")[slot % 4], 6)
    closed = nav.model_copy(update={"doors": []})
    with pytest.raises(NoRoomPath):
        path_pulse(closed, position, door)
