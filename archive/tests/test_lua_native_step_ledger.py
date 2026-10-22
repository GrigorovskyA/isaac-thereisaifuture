"""OFFLINE tests for the passive timing ledger. Only the module is loaded into lupa.lua53.

No Isaac/Game globals, observer harness, sockets, or private logs are involved. The
synthetic numbers imitate the measured query/post-update ordering and prove nothing
about engine consumption.
"""

from pathlib import Path

import pytest

lupa = pytest.importorskip("lupa.lua53", reason="Optional isolated Lua 5.3 test runtime required")

SOURCE = Path(__file__).resolve().parents[1] / "mod/experimental/native_step_ledger.lua"
MAX = 2**53 - 1
GET, PRESSED, TRIGGERED = "GET_ACTION_VALUE", "IS_ACTION_PRESSED", "IS_ACTION_TRIGGERED"
NAN, INF = float("nan"), float("inf")

NEW_BAD = [(0, 1, 1), (1, -1, 1), (1, 1, 0), (1, 1, 16), (1, 0.5, 1), (1, 1, 1.5)]
NEW_BAD += [(True, 1, 1), ("1", 1, 1), (1, "1", 1), (1, 1, None), (1, 1, NAN), (1, 1, INF)]
NEW_BAD += [(MAX + 1, 1, 1), (1, MAX + 1, 1), (1, MAX, 1), (1, MAX - 14, 15)]

QUERY_BAD = [(-1, 1, GET, 0, 0.5), (1.5, 1, GET, 0, 0.5), (MAX + 1, 1, GET, 0, 0.5)]
QUERY_BAD += [(1000, -1, GET, 0, 0.5), (1000, True, GET, 0, 0.5), (1000, "1", GET, 0, 0.5)]
QUERY_BAD += [(1000, 1, "GET_ACTION", 0, 0.5), (1000, 1, None, 0, 0.5), (1000, 1, 5, 0, 0.5)]
QUERY_BAD += [(1000, 1, GET, -1, 0.5), (1000, 1, GET, 8, 0.5), (1000, 1, GET, 1.5, 0.5)]
QUERY_BAD += [(1000, 1, GET, True, 0.5), (1000, 1, GET, 0, 1.5), (1000, 1, GET, 0, -0.1)]
QUERY_BAD += [(1000, 1, GET, 0, NAN), (1000, 1, GET, 0, INF), (1000, 1, GET, 0, True)]
QUERY_BAD += [(1000, 1, GET, 0, "0.5"), (1000, 1, GET, 0, None), (1000, 1, PRESSED, 0, 1)]
QUERY_BAD += [(1000, 1, TRIGGERED, 0, 0.0), (1000, 1, PRESSED, 0, "true")]

POST_BAD = [(-1, 1), (1.5, 1), (1000, -1), (1000, 2.5), (True, 1), (1000, "7"), (MAX + 1, 1)]

CLOSE_BAD = [("", 1000, 1), ("  \t", 1000, 1), ("a\nb", 1000, 1), ("a\x00b", 1000, 1)]
CLOSE_BAD += [("x" * 65, 1000, 1), (None, 1000, 1), (5, 1000, 1), ("ok", -1, 1)]
CLOSE_BAD += [("ok", 1000, 1.5), ("ok", MAX + 1, 1)]


def module():
    runtime = lupa.LuaRuntime(unpack_returned_tuples=True, max_memory=16 * 1024 * 1024)
    return runtime, runtime.execute(SOURCE.read_text(encoding="utf-8"))


def ledger(sequence=1, accepted=1000, repeat=2):
    return module()[1]["new"](sequence, accepted, repeat)


def call(obj, name, *args):
    return obj[name](obj, *args)


def py(value):
    if hasattr(value, "items"):
        return {py(k): py(v) for k, v in value.items()}
    return value


def state(obj):
    return py(call(obj, "snapshot"))


def cell(snap, slot, hook, button):
    return snap["query_window"][slot]["cells"][hook].get(button)


def test_module_loads_alone_without_game_globals():
    runtime, mod = module()
    assert runtime.globals().Isaac is None and runtime.globals().Game is None
    snap = state(mod["new"](7, 5, 3))
    assert snap["sequence"] == 7 and snap["accepted_frame"] == 5
    assert snap["limits"] == {
        "query_slots": 3,
        "post_update_slots": 4,
        "hooks": 3,
        "buttons": 8,
        "call_budget": 4096,
    }
    assert "release" not in snap and snap["calls"] == 0


def test_measured_ordering_with_synthetic_numbers_keeps_queries_and_updates_apart():
    led = ledger(repeat=2)

    def group(frame, update):
        for button in range(8):
            value = 1.0 if button == 0 else 0.0
            assert call(led, "observe_query", frame, update, GET, button, value)
        for button in range(4, 8):
            assert call(led, "observe_query", frame, update, PRESSED, button, False)

    group(1000, 50)  # after post-update 50 at the accepted frame
    group(1001, 50)  # before post-update 51
    assert call(led, "observe_post_update", 1001, 51)
    group(1001, 51)  # after it, same frame ID
    assert call(led, "close", "expiry", 1002, 51) is True
    assert call(led, "observe_post_update", 1002, 52)  # endpoint after release
    snap = state(led)
    first = cell(snap, 1, GET, 0)
    assert (first["count"], first["first_update"], first["last_update"]) == (1, 50, 50)
    assert (first["first_value"], first["last_value"]) == (1.0, 1.0)
    second = cell(snap, 2, GET, 0)
    assert (second["count"], second["first_update"], second["last_update"]) == (2, 50, 51)
    assert cell(snap, 2, PRESSED, 7)["count"] == 2 and cell(snap, 1, PRESSED, 3) is None
    assert cell(snap, 2, TRIGGERED, 0) is None
    posts = snap["post_updates"]  # 1-based: frames 1000, 1001, 1002
    assert [posts[i]["count"] for i in (1, 2, 3)] == [0, 1, 1]
    assert [posts[i]["after_release"] for i in (1, 2, 3)] == [0, 0, 1]
    assert posts[2]["first_update"] == 51 and posts[3]["last_update"] == 52
    assert snap["release"] == {"reason": "expiry", "frame": 1002, "update_counter": 51}
    assert snap["calls"] == 12 * 3 + 2 and sum(snap["dropped"].values()) == 0


@pytest.mark.parametrize("repeat", [1, 15])
def test_window_boundaries_for_one_and_fifteen_frames(repeat):
    last_query, last_post = 1000 + repeat - 1, 1000 + repeat
    led = ledger(accepted=1000, repeat=repeat)
    assert call(led, "observe_query", last_query, 1, GET, 0, 0.5) is True
    assert call(led, "observe_query", last_query + 1, 1, GET, 0, 0.5) is False
    assert call(led, "observe_query", 999, 1, GET, 0, 0.5) is False
    assert call(led, "observe_post_update", last_post, 2) is True
    assert call(led, "observe_post_update", last_post + 1, 2) is False
    assert call(led, "observe_post_update", 999, 2) is False
    snap = state(led)
    assert len(snap["query_window"]) == repeat and len(snap["post_updates"]) == repeat + 1
    assert snap["dropped"]["query_out_of_window"] == 2
    assert snap["dropped"]["post_update_out_of_window"] == 2
    assert snap["dropped"]["query_after_close"] == 0


def test_no_queries_leaves_empty_cells_and_no_release():
    led = ledger(repeat=3)
    assert call(led, "observe_post_update", 1001, 9)
    snap = state(led)
    for slot in snap["query_window"].values():
        assert slot["cells"] == {GET: {}, PRESSED: {}, TRIGGERED: {}}
    assert "release" not in snap and snap["post_updates"][2]["count"] == 1


def test_neutral_values_are_recorded_as_facts_not_outcomes():
    led = ledger(repeat=1)
    assert call(led, "observe_query", 1000, 4, GET, 2, 0.0)
    assert call(led, "observe_query", 1000, 5, GET, 2, 1)  # integer 1 is a valid 0..1 value
    assert call(led, "observe_query", 1000, 4, PRESSED, 1, False)
    assert call(led, "observe_query", 1000, 6, TRIGGERED, 7, True)
    snap = state(led)
    value = cell(snap, 1, GET, 2)
    assert (value["first_value"], value["last_value"]) == (0.0, 1)
    assert (value["first_update"], value["last_update"], value["count"]) == (4, 5, 2)
    assert cell(snap, 1, PRESSED, 1)["last_value"] is False
    assert cell(snap, 1, TRIGGERED, 7)["first_value"] is True
    assert not any(k in snap for k in ("status", "completed", "applied", "outcome"))


def test_close_before_any_post_update_and_queries_after_close_are_dropped():
    led = ledger(repeat=2)
    assert call(led, "observe_query", 1000, 1, GET, 0, 1.0) is True
    assert call(led, "close", "expiry", 1002, 1) is True
    assert call(led, "observe_query", 1001, 1, GET, 0, 1.0) is False
    assert call(led, "observe_query", 5000, 1, GET, 0, 1.0) is False  # closed wins
    assert call(led, "observe_post_update", 1002, 2) is True
    assert call(led, "observe_post_update", 1003, 3) is False
    snap = state(led)
    assert cell(snap, 1, GET, 0)["count"] == 1 and cell(snap, 2, GET, 0) is None
    assert snap["dropped"]["query_after_close"] == 2
    assert snap["dropped"]["query_out_of_window"] == 0
    assert snap["dropped"]["post_update_out_of_window"] == 1
    assert snap["post_updates"][3]["after_release"] == 1


def test_repeated_close_keeps_the_first_cause():
    led = ledger()
    assert call(led, "close", "first", 1001, 5) is True
    assert call(led, "close", "second", 1002, 6) is False
    assert state(led)["release"] == {"reason": "first", "frame": 1001, "update_counter": 5}
    assert call(led, "close", "x" * 64, 1, 1) is False  # valid input, still false


@pytest.mark.parametrize("args", NEW_BAD)
def test_constructor_rejects_invalid_arguments(args):
    with pytest.raises(lupa.LuaError):
        module()[1]["new"](*args)


def test_constructor_accepts_integer_valued_floats_and_the_last_valid_endpoint():
    mod = module()[1]
    snap = state(mod["new"](3.0, 10.0, 2.0))
    assert snap["sequence"] == 3 and snap["accepted_frame"] == 10
    assert isinstance(snap["requested_frames"], int)
    edge = mod["new"](MAX, MAX - 1, 1)
    assert call(edge, "observe_post_update", MAX, MAX) is True


@pytest.mark.parametrize("args", QUERY_BAD)
def test_invalid_query_fails_before_any_mutation(args):
    led = ledger()
    assert call(led, "observe_query", 1000, 1, GET, 0, 0.25)
    before = state(led)
    with pytest.raises(lupa.LuaError):
        call(led, "observe_query", *args)
    assert state(led) == before


@pytest.mark.parametrize("args", POST_BAD)
def test_invalid_post_update_fails_before_any_mutation(args):
    led = ledger()
    before = state(led)
    with pytest.raises(lupa.LuaError):
        call(led, "observe_post_update", *args)
    assert state(led) == before


@pytest.mark.parametrize("args", CLOSE_BAD)
def test_invalid_close_fails_before_any_mutation(args):
    led = ledger()
    before = state(led)
    with pytest.raises(lupa.LuaError):
        call(led, "close", *args)
    assert state(led) == before
    assert call(led, "close", "x" * 64, 1000, 1) is True  # not sealed by the failures


def test_instances_do_not_share_state():
    runtime, mod = module()
    first, second = mod["new"](1, 100, 2), mod["new"](2, 100, 2)
    assert call(first, "observe_query", 100, 1, GET, 0, 1.0)
    assert call(first, "close", "expiry", 101, 1)
    assert call(first, "observe_query", 100, 1, GET, 0, 1.0) is False
    other = state(second)
    assert other["calls"] == 0 and "release" not in other
    assert other["dropped"]["query_after_close"] == 0
    assert call(second, "observe_query", 100, 1, PRESSED, 0, True) is True
    assert state(first)["query_window"][1]["cells"][PRESSED] == {}
    assert runtime.globals().Ledger is None


def test_call_budget_counts_dropped_observations_and_the_next_call_errors_unchanged():
    led = ledger(repeat=1)
    for _ in range(3):  # invalid calls never spend the budget
        with pytest.raises(lupa.LuaError):
            call(led, "observe_query", 1000, 1, GET, 9, 0.5)
    for index in range(4094):
        if index % 2:
            assert call(led, "observe_query", 1000, index, TRIGGERED, 7, False) is True
        else:
            assert call(led, "observe_query", 9999, index, GET, 0, 0.0) is False  # dropped
    assert state(led)["calls"] == 4094
    assert call(led, "observe_post_update", 1000, 1) is True  # 4095
    assert call(led, "observe_post_update", 777, 1) is False  # 4096, dropped but counted
    before = state(led)
    assert before["calls"] == 4096
    with pytest.raises(lupa.LuaError):
        call(led, "observe_query", 1000, 1, GET, 0, 0.5)  # 4097th
    with pytest.raises(lupa.LuaError):
        call(led, "observe_post_update", 1000, 1)
    assert state(led) == before
    assert call(led, "close", "expiry", 1001, 1) is True  # close/snapshot do not renew it
    with pytest.raises(lupa.LuaError):
        call(led, "observe_post_update", 1001, 1)
    assert state(led)["calls"] == 4096


def test_snapshot_is_a_detached_deep_copy():
    led = ledger()
    assert call(led, "observe_query", 1000, 1, GET, 0, 1.0)
    assert call(led, "close", "expiry", 1001, 1)
    before = state(led)
    snap = call(led, "snapshot")
    snap["dropped"]["query_after_close"] = 99
    snap["release"]["reason"] = "tampered"
    snap["query_window"][1]["cells"][GET][0]["count"] = 99
    snap["post_updates"][1]["count"] = 99
    snap["limits"]["call_budget"] = 1
    assert state(led) == before
    assert call(led, "observe_query", 1000, 2, GET, 0, 1.0) is False
    assert py(snap)["dropped"]["query_after_close"] == 99
