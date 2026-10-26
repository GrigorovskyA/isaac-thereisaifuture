"""OFFLINE Lua frame-timing diagnostics: one perf log line per window, then counters reset."""

import re

from test_lua_observer import build_lua, handshake, tick

PERF = re.compile(r"Observer perf (.*)$")


def perf_lines(lua):
    return [m.group(1) for m in map(PERF.search, lua.globals().LOGS.values()) if m]


def fields(line):
    return {k: int(v) for k, v in (pair.split("=") for pair in line.split())}


def test_no_perf_line_before_window_or_while_not_streaming():
    lua = build_lua()
    tick(lua, 40, delta=20)  # 800 ms, connecting
    assert perf_lines(lua) == []
    lua.execute("NOW=NOW+20000; callbacks.render()")
    assert perf_lines(lua) == []  # not streaming: window is reset silently


def test_perf_line_counts_and_reset():
    lua = build_lua()
    handshake(lua)
    lua.execute("callbacks.start(mod, false); NOW=NOW+1; callbacks.render()")
    assert perf_lines(lua) == []
    # Fake clock: 20 ms per step, one update per render, until the 10 s window closes.
    for _ in range(520):
        lua.execute("NOW=NOW+20; callbacks.update(); callbacks.render()")
    lines = perf_lines(lua)
    assert len(lines) == 1
    values = fields(lines[0])
    assert list(values) == [
        "window_ms", "updates", "renders", "snapshots",
        "update_ms", "render_ms", "capture_ms", "encode_ms",
    ]  # fmt: skip
    assert values["window_ms"] >= 10000
    assert values["updates"] > 0 and values["renders"] >= values["updates"]
    assert values["snapshots"] > 0
    # The fake clock does not advance inside callbacks, so time spent is zero.
    assert values["update_ms"] == values["render_ms"] == 0
    assert values["capture_ms"] == values["encode_ms"] == 0
    # Counters reset: a second window reports only its own counts.
    for _ in range(520):
        lua.execute("NOW=NOW+20; callbacks.update(); callbacks.render()")
    second = [fields(line) for line in perf_lines(lua)]
    assert len(second) == 2
    assert second[1]["window_ms"] == 10000
    assert second[1]["updates"] == second[1]["renders"] == 500


def test_time_inside_callbacks_and_capture_is_summed():
    lua = build_lua()
    handshake(lua)
    # Each Isaac.GetTime() call advances the clock by 1 ms, so every measured span is > 0.
    lua.execute("local t = Isaac.GetTime; Isaac.GetTime = function() NOW = NOW + 1; return NOW end")
    for _ in range(300):
        lua.execute("NOW=NOW+40; callbacks.update(); callbacks.render()")
    values = fields(perf_lines(lua)[0])
    assert values["update_ms"] > 0 and values["render_ms"] > 0
    assert values["capture_ms"] > 0 and values["encode_ms"] > 0
    assert values["render_ms"] >= values["capture_ms"] + values["encode_ms"]


def test_perf_line_does_not_change_repeated_message_suppression():
    lua = build_lua()
    handshake(lua)
    lua.execute("callbacks.start(mod, false)")
    before = lua.eval("(function() return 1 end)()")
    assert before == 1
    for _ in range(520):
        lua.execute("NOW=NOW+20; callbacks.render()")
    assert len(perf_lines(lua)) == 1
