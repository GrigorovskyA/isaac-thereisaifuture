"""Observation schema 6: the visited-cells block, and the oracle doors that never reach it."""

import json

import numpy as np
import pytest
from pydantic import ValidationError
from synthetic import frame, oracle_metrics, room_facts
from test_entity_transport import entity_snapshot

from isaac_threrisaifuture.encoding import (
    FIRST_CELL,
    OBSERVATION_SIZE,
    SHAPE_TILES,
    STALL_OFFSET,
    VISITED_COLS,
    VISITED_OFFSET,
    VISITED_ROWS,
    ProtocolError,
    VisitedCells,
    encode,
    room_diagonal,
)
from isaac_threrisaifuture.entities import (
    FRAME_SCHEMA_VERSION,
    OBSERVATION_SCHEMA_VERSION,
    EntityFrame,
    MapRoom,
    Vec,
)
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episodes import Scenario, StepResult
from isaac_threrisaifuture.live_wire import LiveSnapshot


def at(x, y, *, grid=84, stage=1, epoch=1, visit=1, session=None, frame_id=1):
    changes: dict = dict(
        player_position=Vec(x=x, y=y),
        game_epoch=epoch,
        room_visit=visit,
        frame_id=frame_id,
        room=room_facts(stage=stage),
        map=[MapRoom(grid_index=grid, shape=1, visited=True, current=True, room_type=1)],
    )
    if session is not None:
        changes["session_id"] = session
    return frame(**changes)


def visited(grid_vector):
    return {int(i) for i in np.flatnonzero(grid_vector)}


def cell(col, row):
    return row * VISITED_COLS + col


# --- layout ----------------------------------------------------------------------------


def test_the_block_covers_the_largest_room_and_comes_last():
    assert OBSERVATION_SCHEMA_VERSION == 6 and FRAME_SCHEMA_VERSION == 5
    assert FIRST_CELL == (1, 3) and (VISITED_COLS, VISITED_ROWS) == (27, 15)
    assert VISITED_OFFSET == STALL_OFFSET + 1
    assert OBSERVATION_SIZE == VISITED_OFFSET + 27 * 15 == 3904
    assert encode(frame()).vector.shape == (OBSERVATION_SIZE,)
    # A 2x2 room interior, 1040 x 560 px from (60, 140), has its corners inside the grid.
    cells = VisitedCells()
    assert visited(cells.update(at(60, 140))) == {cell(0, 0)}
    assert visited(cells.update(at(1099, 699))) == {cell(0, 0), cell(26, 14)}


def test_without_visited_cells_the_block_is_zero_and_the_rest_is_unchanged():
    base = encode(frame()).vector
    assert not base[VISITED_OFFSET:].any()
    grid = VisitedCells().update(frame())
    with_block = encode(frame(), visited_cells=grid).vector
    assert np.array_equal(with_block[:VISITED_OFFSET], base[:VISITED_OFFSET])
    assert with_block[VISITED_OFFSET:].sum() == 1.0 and np.all(np.abs(with_block) <= 1.0)
    with pytest.raises(ProtocolError):
        encode(frame(), visited_cells=np.zeros(3, dtype=np.float32))


# --- cells and rooms -------------------------------------------------------------------


def test_cells_are_set_on_visit_and_stay_set():
    cells = VisitedCells()
    first = cells.update(at(300, 200))
    assert visited(first) == {cell(6, 2)}
    second = cells.update(at(100, 200))
    assert visited(second) == {cell(6, 2), cell(1, 2)}
    assert set(np.unique(second)) == {0.0, 1.0} and second.dtype == np.float32
    # The same cell again changes nothing; the player stands still.
    assert visited(cells.update(at(101, 201))) == visited(second)


def test_a_cell_is_the_novelty_cell_of_the_ledger():
    cells = VisitedCells()
    # Positions 39 px apart in one 40 px cell share it; 41 px apart across a boundary do not.
    assert len(visited(cells.update(at(121.0, 200.0)))) == 1
    assert len(visited(cells.update(at(159.0, 200.0)))) == 1
    assert len(visited(cells.update(at(161.0, 200.0)))) == 2


def test_rooms_and_stages_have_separate_maps():
    cells = VisitedCells()
    cells.update(at(300, 200, grid=84))
    other = cells.update(at(500, 300, grid=85))
    assert visited(other) == {cell(500 // 40 - 1, 300 // 40 - 3)}
    back = cells.update(at(300, 200, grid=84, frame_id=2))  # back in the first room
    assert visited(back) == {cell(300 // 40 - 1, 200 // 40 - 3)}
    floor_two = cells.update(at(300, 200, grid=84, stage=2))  # same grid index on the next floor
    assert visited(floor_two) == {cell(300 // 40 - 1, 200 // 40 - 3)}
    cells.update(at(100, 200, grid=84, stage=2))
    assert len(visited(cells.update(at(300, 200, grid=84, stage=1)))) == 1  # floor 1 unchanged


def test_a_room_without_a_grid_position_starts_empty_on_each_visit():
    cells = VisitedCells()
    off_grid = dict(map=[], map_current_off_grid=True)
    cells.update(frame(player_position=Vec(x=300, y=200), room_visit=3, **off_grid))
    again = cells.update(frame(player_position=Vec(x=500, y=300), room_visit=4, **off_grid))
    assert visited(again) == {cell(500 // 40 - 1, 300 // 40 - 3)}


def test_a_new_run_clears_every_map():
    cells = VisitedCells()
    cells.update(at(300, 200))
    cells.update(at(100, 200))
    assert len(visited(cells.update(at(300, 200, epoch=2)))) == 1  # a new game epoch
    cells.update(at(100, 200, epoch=2))
    assert len(visited(cells.update(at(300, 200, epoch=2, session="b" * 32)))) == 1  # new session


def test_positions_outside_the_room_are_clipped_to_the_edge_cells():
    cells = VisitedCells()
    grid = cells.update(at(-500, -500))
    assert visited(grid) == {cell(0, 0)}
    grid = cells.update(at(5000, 5000))
    assert visited(grid) == {cell(0, 0), cell(VISITED_COLS - 1, VISITED_ROWS - 1)}
    grid = cells.update(at(5000, 150))
    assert cell(VISITED_COLS - 1, 0) in visited(grid) and len(visited(grid)) == 3


# --- environment -----------------------------------------------------------------------


class Walker:
    """Backend that returns the given frames one by one."""

    supports_seed = False

    def __init__(self, frames):
        self.frames = list(frames)

    def start_episode(self, scenario, seed):
        return StepResult(self.frames.pop(0), ())

    def step(self, action, repeat):
        return StepResult(self.frames.pop(0), ())

    def release(self):
        pass

    def close(self):
        pass


def test_the_env_shows_the_visited_cells_and_forgets_them_on_a_new_run():
    scenario = Scenario(
        "walk", "train", 1, None, 0, 1.0, allow_room_change=True, end_on_clear=False
    )
    env = IsaacCombatEnv(
        Walker([at(300, 200), at(100, 200, frame_id=2), at(300, 200, frame_id=3, epoch=2)]),
        [scenario],
    )
    obs, _ = env.reset()
    assert visited(obs[VISITED_OFFSET:]) == {cell(6, 2)}
    obs, *_ = env.step(np.array([0, 0, 0]))
    assert visited(obs[VISITED_OFFSET:]) == {cell(6, 2), cell(1, 2)}
    obs, _ = env.reset()  # a new game epoch is a new run
    assert visited(obs[VISITED_OFFSET:]) == {cell(6, 2)}


# --- oracle doors never reach the policy -----------------------------------------------


def snapshot_with_doors(doors):
    raw = entity_snapshot("a" * 32, 1)
    raw["oracle"] = {
        "room_clear": True,
        "player_dead": False,
        "enemies": [],
        "enemy_overflow": 0,
        "room_index": 84,
        **{**oracle_metrics(), "doors": doors},
    }
    return json.dumps(raw)


def door(slot=0, **changes):
    return {"slot": slot, "x": 20.5, "y": 280.0, "open": True, "unexplored": True, **changes}


def test_oracle_doors_are_validated_and_stay_out_of_the_frame():
    snap = LiveSnapshot.model_validate_json(snapshot_with_doors([door(0), door(7, open=False)]))
    assert snap.oracle is not None and [d.slot for d in snap.oracle.doors] == [0, 7]
    assert "unexplored" not in snap.entity_frame.model_dump_json()
    assert not any("unexplored" in name for name in EntityFrame.model_fields)
    assert LiveSnapshot.model_validate_json(snapshot_with_doors([])).oracle.doors == []


@pytest.mark.parametrize(
    "doors",
    [
        [door(slot) for slot in range(8)] + [door(0)],  # nine doors
        [door(8)],
        [door(-1)],
        [door(0), door(0)],  # duplicate slot
        [door(0, x=1e6)],
        [door(0, x="20")],
        [door(0, open=1)],
        [{"slot": 0, "x": 1.0, "y": 1.0, "open": True}],  # missing unexplored
        [door(0, extra=True)],
    ],
)
def test_malformed_oracle_doors_are_rejected(doors):
    with pytest.raises(ValidationError):
        LiveSnapshot.model_validate_json(snapshot_with_doors(doors))


def test_non_finite_door_coordinates_are_rejected():
    text = (
        snapshot_with_doors([door(0)])
        .replace('"x": 20.5', '"x": NaN')
        .replace('"x":20.5', '"x":NaN')
    )
    with pytest.raises(ValidationError):
        LiveSnapshot.model_validate_json(text)
    with pytest.raises(ValidationError):
        LiveSnapshot.model_validate_json(snapshot_with_doors([door(0)]).replace("20.5", "Infinity"))


def test_a_snapshot_without_the_doors_field_is_rejected():
    raw = json.loads(snapshot_with_doors([]))
    del raw["oracle"]["doors"]
    with pytest.raises(ValidationError):
        LiveSnapshot.model_validate_json(json.dumps(raw))


def test_room_diagonal_comes_from_the_shape_bounding_box():
    assert set(SHAPE_TILES) == set(range(1, 13))
    assert room_diagonal(1) == pytest.approx((520**2 + 280**2) ** 0.5)
    assert room_diagonal(8) == room_diagonal(9) == pytest.approx((1040**2 + 560**2) ** 0.5)
    assert room_diagonal(2) < room_diagonal(1) < room_diagonal(4) < room_diagonal(8)
