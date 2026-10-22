import numpy as np
import pytest

from isaac_threrisaifuture.navigation import (
    MAP_OBSERVATION_SIZE,
    FloorMap,
    MapTracker,
    NavigationError,
    Room,
    RoomEvent,
    StaleMapEvent,
    door_move,
    encode_known_map,
    next_move,
    shortest_path,
)


# Synthetic layout (x right, y down):
#   0(start) - 1 - 2(treasure)
#   |          |
#   3 ======== 4(boss, locked door to 3)   5 = secret room above room 1
def floor() -> FloorMap:
    return FloorMap(
        rooms=(
            Room(0, 0, 1, "start", {"right": "open", "down": "open"}),
            Room(
                1, 1, 1, "normal", {"left": "open", "right": "open", "down": "open", "up": "open"}
            ),
            Room(2, 2, 1, "treasure", {"left": "open"}),
            Room(3, 0, 2, "normal", {"up": "open", "right": "locked"}),
            Room(4, 1, 2, "boss", {"up": "open", "left": "locked"}),
            Room(5, 1, 0, "secret", {"down": "open"}),
        ),
        start_id=0,
    )


def tracker() -> MapTracker:
    t = MapTracker(floor())
    t.start("s1")
    return t


def test_hidden_rooms_do_not_leak() -> None:
    t = tracker()
    t.apply(RoomEvent("s1", 2, 1))
    known = t.known
    assert 5 not in known.rooms  # adjacent secret room stays hidden
    assert known.door_status(1, "up") == "wall"
    assert set(known.rooms) == {0, 1, 2, 3, 4}
    assert not known.rooms[2].visited and known.rooms[2].type == "treasure"
    vec = encode_known_map(known)
    assert vec.shape == (MAP_OBSERVATION_SIZE,)


def test_secret_room_revealed_only_when_visited() -> None:
    rooms = (Room(0, 0, 0, "start", {"up": "open"}), Room(1, 0, -1, "secret", {"down": "open"}))
    t = MapTracker(FloorMap(rooms, 0))
    t.start("s1")
    assert set(t.known.rooms) == {0}
    t.apply(RoomEvent("s1", 2, 1))
    assert set(t.known.rooms) == {0, 1}


def test_unvisited_room_has_unknown_doors() -> None:
    known = tracker().known
    assert known.door_status(1, "left") == "open"
    assert known.door_status(1, "right") == "unknown"
    assert known.door_status(0, "left") == "wall"


def test_shortest_path_uses_only_open_known_doors() -> None:
    t = tracker()
    t.apply(RoomEvent("s1", 2, 1))
    known = t.known
    assert shortest_path(known, 0, 2) == ("right", "right")
    assert shortest_path(known, 0, 0) == ()
    # 4 is reachable via 1 (down); the locked 3-4 door is never used
    assert shortest_path(known, 3, 4) == ("up", "right", "down")
    assert shortest_path(known, 0, 4) == ("right", "down")


def test_unreachable_when_only_closed_doors_known() -> None:
    rooms = (
        Room(0, 0, 0, "start", {"right": "blocked"}),
        Room(1, 1, 0, "normal", {"left": "blocked"}),
    )
    t = MapTracker(FloorMap(rooms, 0))
    t.start("s1")
    assert shortest_path(t.known, 0, 1) is None


def test_door_move_maps_cardinals_and_refuses_closed_doors() -> None:
    known = tracker().known
    assert door_move(known, 0, "right").move == 2
    assert door_move(known, 0, "down").move == 4
    with pytest.raises(NavigationError):
        door_move(known, 0, "left")  # wall
    with pytest.raises(NavigationError):
        door_move(known, 1, "right")  # unknown (room 1 not visited)
    assert next_move(known, 1) is not None
    assert next_move(known, 0) is None


def test_stale_replayed_and_foreign_events_rejected() -> None:
    t = tracker()
    t.apply(RoomEvent("s1", 2, 1))
    for bad in (
        RoomEvent("s1", 2, 0),  # replayed visit counter
        RoomEvent("s1", 1, 0),  # older visit
        RoomEvent("other", 3, 0),  # foreign session
        RoomEvent("s1", 3, 3),  # not adjacent to the current room through an open door
        RoomEvent("s1", 3, 99),  # unknown room
    ):
        with pytest.raises(StaleMapEvent):
            t.apply(bad)
    assert t.known.current_id == 1


def test_clear_event_marks_room_once() -> None:
    t = tracker()
    t.apply(RoomEvent("s1", 1, 0, "clear"))
    assert t.known.rooms[0].cleared
    with pytest.raises(StaleMapEvent):
        t.apply(RoomEvent("s1", 1, 0, "clear"))
    with pytest.raises(StaleMapEvent):
        t.apply(RoomEvent("s1", 5, 0, "clear"))


def test_encoder_size_is_fixed_and_does_not_leak_ids() -> None:
    t = tracker()
    before = encode_known_map(t.known)
    t.apply(RoomEvent("s1", 2, 1))
    after = encode_known_map(t.known)
    assert before.shape == after.shape == (MAP_OBSERVATION_SIZE,)
    assert before.dtype == np.float32 and after.sum() > before.sum()


def test_invalid_floor_rejected() -> None:
    with pytest.raises(ValueError):
        FloorMap((Room(0, 0, 0, "start", {"right": "open"}),), 0)
    with pytest.raises(ValueError):
        Room(1, 0, 0, "weird")  # type: ignore[arg-type]
