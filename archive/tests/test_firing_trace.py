"""OFFLINE tests for the private firing-trace parser; no Isaac, log or game data is read."""

import json
import re
from dataclasses import asdict, fields
from pathlib import Path

import pytest

from isaac_threrisaifuture.firing_trace import (
    LIMITATIONS,
    MAX_SCAN_LINES,
    PREFIX,
    GroupSummary,
    IntervalStats,
    ReleaseInterval,
    TraceRecord,
    TraceRecordError,
    TraceSummary,
    ValueRange,
    analyze_trace,
    parse_line,
    parse_trace,
)

A = "0123456789abcdef0123456789abcdef"
B = "fedcba9876543210fedcba9876543210"
SECRET = "SECRETMARKER42"
ACCEPT = " move=none shoot=up frames=3 until=23 deadline_ms=1250"


def line(
    record_id,
    event,
    extra="",
    *,
    time_ms=1000,
    frame=20,
    update=3,
    session=A,
    epoch=1,
    room=2,
    seq=1,
):
    tail = f" time_ms={time_ms} frame={frame} update={update} session={session}"
    tail += f" epoch={epoch} room={room}" + (f" seq={seq}" if seq is not None else "")
    return f"{PREFIX} id={record_id} event={event}{extra}{tail}"


class Log:
    def __init__(self):
        self.lines = []

    def add(self, event, extra="", **kwargs):
        self.lines.append(line(len(self.lines) + 1, event, extra, **kwargs))
        return self

    def summary(self):
        return analyze_trace(self.lines)


def accept(shoot="up", frames=3):
    return f" move=none shoot={shoot} frames={frames} until=23 deadline_ms=1250"


def shoot_input(delay="2.5", max_delay="10.25", hook="GET_ACTION_VALUE", returned="1.0"):
    return (
        f" hook={hook} button=6 returned={returned} fire_delay={delay} max_fire_delay={max_delay}"
    )


def tear(delay="3", max_delay="10"):
    return f" fire_delay={delay} max_fire_delay={max_delay}"


def release(reason="expiry", hold=1):
    return f" reason={reason} hold_seq={hold} frame_due=1 wall_due=0 left=0"


def rejected(text):
    with pytest.raises(TraceRecordError) as error:
        parse_line(text)
    assert str(error.value) == error.value.category
    return error.value.category


EVENT_CASES = [
    (
        "action_accepted",
        ACCEPT,
        {"move": "none", "shoot": "up", "frames": 3, "until": 23, "deadline_ms": 1250},
    ),
    (
        "input",
        shoot_input(),
        {
            "hook": "GET_ACTION_VALUE",
            "button": 6,
            "returned": "1.0",
            "fire_delay": 2.5,
            "max_fire_delay": 10.25,
        },
    ),
    (
        "input",
        " hook=IS_ACTION_PRESSED button=1 returned=true",
        {"hook": "IS_ACTION_PRESSED", "button": 1, "returned": "true"},
    ),
    ("fire_tear", tear("0", "10"), {"fire_delay": 0.0, "max_fire_delay": 10.0}),
    ("hold_update", " hold_seq=1 left=-1 upd_since=2", {"hold_seq": 1, "left": -1, "upd_since": 2}),
    (
        "release_update",
        " hold_seq=1 hold=absent upd_since=1",
        {"hold_seq": 1, "hold": "absent", "upd_since": 1},
    ),
    (
        "release_input",
        " hold_seq=1 hook=2 button=6 override=nil",
        {"hold_seq": 1, "hook": 2, "button": 6, "override": "nil"},
    ),
    ("release_superseded", " hold_seq=1 by_seq=2", {"hold_seq": 1, "by_seq": 2}),
    (
        "release",
        release(),
        {"reason": "expiry", "hold_seq": 1, "frame_due": 1, "wall_due": 0, "left": 0},
    ),
    ("stop", " reason=count", {"reason": "count"}),
    ("stop", " reason=close", {"reason": "close"}),
    ("close", " reason=Peer disconnected", {}),
    ("game_started", " continued=nil", {"continued": "nil"}),
    ("game_end", " game_over=true", {"game_over": "true"}),
    *[
        (name, "", {})
        for name in (
            "render_enter",
            "render_exit",
            "update_enter",
            "update_exit",
            "new_room",
            "new_level",
            "pre_game_exit",
            "pre_mod_unload",
        )
    ],
]


@pytest.mark.parametrize(("event", "extra", "expected"), EVENT_CASES)
def test_every_source_event_parses_with_provenance(event, extra, expected):
    text = line(7, event, extra, time_ms=70295142, frame=826, update=51, epoch=2, room=4, seq=150)
    record = parse_line("decorated log prefix: " + text + "\r\n")
    assert record == TraceRecord(
        record_id=7,
        event=event,
        time_ms=70295142,
        frame=826,
        update=51,
        session=A,
        epoch=2,
        room=4,
        sequence=150,
        fields=expected,
    )


def test_sequence_is_optional_before_the_first_action():
    record = parse_line(line(1, "render_enter", seq=None))
    assert record is not None and record.sequence is None


def test_trace_events_in_the_lua_source_are_all_supported():
    source = (Path(__file__).parents[1] / "mod/observer/main.lua").read_text(encoding="utf-8")
    trace_part = source[
        source.index("Bounded opt-in callback trace") : source.index(
            "Raw callback facts only. No OracleEvent"
        )
    ]
    emitted = set(re.findall(r'trace_event\("([a-z_]+)"', source))
    emitted |= set(re.findall(r'event="([a-z_]+)"', trace_part)) | {"stop"}
    assert len(emitted) >= 18
    assert emitted <= {event for event, _, _ in EVENT_CASES}


def test_unrelated_lines_are_discarded_without_counting_or_rejecting():
    parsed = parse_trace(
        [
            "",
            "Action release reason=expiry session=x time_ms=1",
            "Lua Debug: hello",
            "[Isaac Future] id=1",
            "[Isaac Future OracleProbe] id=1 event=stop reason=count",
            "x" * 5000 + line(1, "render_enter"),
            line(1, "render_enter")[3:],
        ]
    )
    assert parsed.records == () and parsed.trace_lines == 0 and parsed.rejected == {}
    assert parsed.scanned_lines == 7


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("0", 0.0),
        ("2.5", 2.5),
        ("10.25", 10.25),
        ("-1.5", -1.5),
        ("0.000123457", 0.000123457),
        ("1.5e-05", 1.5e-05),
        ("123457", 123457.0),
        ("1e+06", 1e6),
        ("-1e+06", -1e6),
    ],
)
def test_finite_cooldowns_in_bound_keep_fractions(token, expected):
    record = parse_line(line(1, "fire_tear", tear(token, token)))
    assert record.fields == {"fire_delay": expected, "max_fire_delay": expected}


@pytest.mark.parametrize(
    "token",
    [
        "nan",
        "NaN",
        "inf",
        "-inf",
        "Infinity",
        "1e+07",
        "-2000000",
        "1000000.5",
        "1e999",
        "0x10",
        "1.0.0",
        "",
        "1,5",
        "NA",
        "-",
    ],
)
@pytest.mark.parametrize("slot", ["fire_delay", "max_fire_delay"])
def test_nonfinite_or_out_of_bound_cooldowns_reject_the_record(token, slot):
    values = {"fire_delay": "1", "max_fire_delay": "1", slot: token}
    assert (
        rejected(
            line(
                1,
                "fire_tear",
                tear(**{"delay": values["fire_delay"], "max_delay": values["max_fire_delay"]}),
            )
        )
        == "invalid_cooldown"
    )


def test_na_stays_missing_and_never_becomes_zero():
    log = Log().add("input", shoot_input("na", "10")).add("input", shoot_input("na", "na"))
    log.add("fire_tear", tear("na", "8")).add("fire_tear", tear("0", "8"))
    summary = log.summary()
    assert summary.cooldowns["input.fire_delay"] == ValueRange(0, 2, None, None)
    assert summary.cooldowns["input.max_fire_delay"] == ValueRange(1, 1, 10.0, 10.0)
    assert summary.cooldowns["fire_tear.fire_delay"] == ValueRange(1, 1, 0.0, 0.0)
    assert summary.cooldowns["fire_tear.max_fire_delay"] == ValueRange(2, 0, 8.0, 8.0)


def test_cooldown_pairs_are_both_or_neither():
    assert (
        rejected(line(1, "input", " hook=GET_ACTION_VALUE button=6 returned=1.0 fire_delay=1"))
        == "missing_field"
    )
    assert rejected(line(1, "fire_tear", " fire_delay=1")) == "missing_field"
    assert rejected(line(1, "fire_tear")) == "missing_field"


@pytest.mark.parametrize(
    ("text", "category"),
    [
        (line(1, "render_enter").replace(" room=2", ""), "missing_field"),
        (line(1, "render_enter").replace(f" session={A}", ""), "missing_field"),
        (line(1, "render_enter").replace(" id=1", ""), "missing_field"),
        (line(1, "render_enter").replace(" event=render_enter", ""), "missing_field"),
        (f"{PREFIX} id=1 event=render_enter", "missing_field"),
        (line(1, "render_enter") + f" session={B}", "duplicate_field"),
        (line(1, "render_enter").replace(" frame=20", " time_ms=5 frame=20"), "duplicate_field"),
        (line(1, "render_enter") + " seq=5", "duplicate_field"),
        (line(1, "render_enter", " id=9"), "duplicate_field"),
        (line(1, "hold_update", " hold_seq=1 left=0 upd_since=1 left=2"), "duplicate_field"),
        (line(1, "teleport"), "unknown_event"),
        (line(1, "render_enter", " foo=1"), "unknown_field"),
        (line(1, "render_enter", " foo"), "malformed"),
        (line(1, "hold_update", "  hold_seq=1 left=0 upd_since=1"), "malformed"),
        (line(1, "render_enter") + " extra=1", "malformed"),
        (line(1, "render_enter") + " \u00e9", "malformed"),
        (line(1, "render_enter") + "\x07", "malformed"),
        (line(1, "render_enter").replace("room=2 ", "room=2\t"), "malformed"),
        (line(1, "render_enter", session="nil"), "malformed"),
        (line(1, "render_enter", session=A.upper()), "malformed"),
        (line(1, "render_enter", session=A[:-1]), "malformed"),
        (line(1, "render_enter", frame=-1), "malformed"),
        (line(1, "render_enter", frame="1" * 17), "malformed"),
        (line(0, "render_enter"), "malformed"),
        (line(513, "render_enter"), "malformed"),
        (line(1, "render_enter", seq=0), "malformed"),
        (line(1, "stop", " reason=weather"), "malformed"),
        (line(1, "release", release().replace("frame_due=1", "frame_due=2")), "malformed"),
        (line(1, "close", " reason=" + "x" * 61), "malformed"),
        (line(1, "action_accepted", ACCEPT.replace("frames=3", "frames=three")), "malformed"),
        (line(1, "input", " hook=GET_ACTION_VALUE button=6"), "missing_field"),
        (line(1, "render_enter", " pad=" + "x" * 300), "oversized"),
        (PREFIX + " " * 400 + "id=1", "oversized"),
    ],
)
def test_malformed_records_fail_with_a_fixed_category(text, category):
    assert rejected(text) == category


def test_huge_prefixed_line_is_rejected_and_late_prefix_is_ignored():
    assert rejected(PREFIX + " " + "x" * 1_000_000) == "oversized"
    assert parse_line("x" * 2000 + line(1, "render_enter")) is None
    assert parse_line("x" * 900 + line(1, "render_enter")) is not None


class NoCopy(str):
    """Fails if the parser slices, strips or otherwise copies the (possibly huge) line."""

    def __getitem__(self, key):
        raise AssertionError("line was copied")

    def rstrip(self, *args):
        raise AssertionError("line was copied")

    strip = lstrip = split = splitlines = replace = rstrip


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(PREFIX + " " + "x" * 2_000_000, id="multi-megabyte-record"),
        pytest.param(PREFIX + " id=1" + " " * 2_000_000, id="multi-megabyte-whitespace"),
        pytest.param("decorated: " + PREFIX + "\r\n" * 1_000_000, id="many-line-endings"),
    ],
)
def test_oversized_prefixed_input_is_rejected_before_any_copy(text):
    with pytest.raises(TraceRecordError) as error:
        parse_line(NoCopy(text))
    assert error.value.category == "oversized"
    parsed = parse_trace([NoCopy(text)])
    assert parsed.rejected == {"oversized": 1} and parsed.records == ()


def test_record_length_boundary_allows_only_a_line_ending_after_300_characters():
    record = PREFIX + "x" * (300 - len(PREFIX))
    assert rejected(record) == "missing_field"  # within the limit, so it reaches field checks
    assert rejected("log decoration " + record + "\r\n") == "missing_field"
    assert rejected(record + "\n") == "missing_field"
    assert rejected(record + "x") == "oversized"
    assert rejected(record + "   ") == "oversized"


@pytest.mark.parametrize("ending", ["", "\n", "\r\n", "\r"])
def test_one_terminal_line_ending_is_accepted(ending):
    record = parse_line("decorated: " + line(1, "action_accepted", ACCEPT) + ending)
    assert record is not None and record.record_id == 1


@pytest.mark.parametrize(
    "suffix",
    [
        pytest.param(" ", id="space"),
        pytest.param("\t", id="tab"),
        pytest.param("\r\n ", id="crlf-space"),
        pytest.param("\r\n\t", id="crlf-tab"),
        pytest.param("\n ", id="lf-space"),
        pytest.param(" \r\n", id="space-crlf"),
        pytest.param("\r\n\r\n", id="double-crlf"),
        pytest.param("\n\n", id="double-lf"),
        pytest.param("\n\r", id="lf-cr"),
    ],
)
def test_trailing_whitespace_beyond_one_line_ending_is_malformed(suffix):
    text = line(1, "action_accepted", ACCEPT) + suffix
    assert rejected(text) == "malformed"
    parsed = parse_trace([text])
    assert parsed.records == () and parsed.rejected == {"malformed": 1}
    assert parsed.trace_lines == 1 and parsed.rejected_lines == ((1, "malformed"),)
    assert PREFIX not in repr(parsed)


@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r"])
def test_embedded_line_endings_are_malformed(ending):
    text = line(1, "action_accepted", ACCEPT).replace("room=2", f"room=2{ending}")
    assert rejected(text) == "malformed"
    assert parse_trace([text + ending]).rejected == {"malformed": 1}


def test_rejections_are_counted_without_echoing_input():
    lines = [
        line(1, "teleport", f" note={SECRET}"),
        line(2, "close", f" reason={SECRET}"),
        line(3, "release", release(f"{SECRET} hold_seq=9")),
        line(4, "render_enter", f" {SECRET}=1"),
        f"{PREFIX} id=5 event=input {SECRET}",
        line(6, "render_enter") + SECRET * 100,
        line(7, "release", release("Peer disconnected")),
        b"bytes are not text lines",
    ]
    summary = analyze_trace(lines)
    assert summary.records == 3 and summary.trace_lines == 8
    assert summary.rejected == {
        "unknown_event": 1,
        "unknown_field": 1,
        "missing_field": 1,
        "oversized": 1,
        "malformed": 1,
    }
    assert SECRET not in repr(summary) and SECRET not in json.dumps(asdict(summary))
    assert "Peer" not in repr(summary)
    assert all(isinstance(n, int) and isinstance(c, str) for n, c in summary.rejected_lines)
    with pytest.raises(TraceRecordError) as error:
        parse_line(lines[0])
    assert SECRET not in str(error.value) and SECRET not in repr(error.value)


def test_duplicate_record_ids_keep_the_first_record():
    first, second = line(3, "new_room"), line(3, "render_exit")
    parsed = parse_trace([first, second])
    assert [r.event for r in parsed.records] == ["new_room"]
    assert parsed.rejected == {"duplicate_id": 1} and parsed.rejected_lines == (
        (2, "duplicate_id"),
    )


def test_interleaved_sessions_and_reconnects_never_merge():
    log = Log()
    log.add("action_accepted", accept(), session=A, time_ms=1000, frame=10, seq=1)
    log.add("action_accepted", accept("left"), session=B, time_ms=1005, frame=10, seq=1)
    log.add("release", release(), session=A, time_ms=1100, frame=13, seq=1)
    log.add("release", release(), session=B, time_ms=1110, frame=13, seq=1)
    log.add("action_accepted", accept(), session=A, time_ms=1150, frame=14, seq=2)
    log.add("action_accepted", accept(), session=B, time_ms=1400, frame=20, seq=2)
    summary = log.summary()
    assert [(g.session, g.epoch, g.sequence) for g in summary.groups] == [
        (A, 1, 1),
        (B, 1, 1),
        (A, 1, 2),
        (B, 1, 2),
    ]
    assert summary.groups[0].events == {"action_accepted": 1, "release": 1}
    assert [(i.session, i.gap_ms, i.gap_frames) for i in summary.intervals] == [
        (A, 50, 1),
        (B, 290, 7),
    ]
    assert summary.unpaired_releases == 0 and summary.excluded_intervals == 0


def test_release_to_accept_never_crosses_session_or_epoch():
    log = Log()
    log.add("action_accepted", accept(), seq=1, time_ms=1000)
    log.add("release", release(), seq=1, time_ms=1100)
    log.add("action_accepted", accept(), seq=2, epoch=2, time_ms=1120)
    log.add("action_accepted", accept(), seq=2, session=B, time_ms=1130)
    summary = log.summary()
    assert summary.intervals == () and summary.interval_stats is None
    assert summary.unpaired_releases == 1 and summary.excluded_intervals == 0


@pytest.mark.parametrize(
    "between",
    [
        [("new_room", "", {"room": 3}, {})],
        [("new_level", "", {}, {})],
        [("game_end", " game_over=true", {}, {})],
        [("close", " reason=Peer disconnected", {}, {})],
        [("pre_game_exit", "", {}, {})],
        [],  # room change on the accepted action alone
    ],
)
def test_handoff_and_transition_gaps_are_excluded(between):
    log = Log().add("action_accepted", accept(), seq=1, time_ms=1000)
    log.add("release", release(), seq=1, time_ms=1100)
    for event, extra, ident, _ in between:
        log.add(event, extra, seq=1, time_ms=1110, **ident)
    log.add("action_accepted", accept(), seq=2, time_ms=1200, room=3)
    summary = log.summary()
    assert summary.intervals == () and summary.excluded_intervals == 1


def test_game_start_epoch_change_is_unpaired_not_bridged():
    log = Log().add("release", release(), seq=1, time_ms=1100)
    log.add("game_started", " continued=true", seq=1, epoch=2, time_ms=1110)
    log.add("action_accepted", accept(), seq=2, epoch=2, time_ms=1200)
    summary = log.summary()
    assert summary.intervals == () and summary.unpaired_releases == 1


def test_nonadvancing_or_backwards_intervals_are_excluded():
    log = Log().add("release", release(hold=5), seq=5, time_ms=1100, frame=30)
    log.add("action_accepted", accept(), seq=5, time_ms=1200, frame=33)
    log.add("release", release(hold=6), seq=6, time_ms=1300, frame=40)
    log.add("action_accepted", accept(), seq=7, time_ms=1250, frame=45)
    log.add("release", release(hold=7), seq=7, time_ms=1400, frame=50)
    log.add("action_accepted", accept(), seq=8, time_ms=1500, frame=49)
    log.add("release", release(hold=8), seq=8, time_ms=1600, frame=60)
    log.add("action_accepted", accept(), seq=None, time_ms=1650, frame=61)
    summary = log.summary()
    assert summary.intervals == () and summary.excluded_intervals == 4


def test_release_intervals_report_reason_class_gaps_and_stats_only():
    log = Log()
    for seq, (reason, gap) in enumerate(
        [("expiry", 17), ("explicit_release", 900), ("Peer disconnected", 51), ("replaced", 0)], 1
    ):
        log.add("release", release(reason, seq), seq=seq, time_ms=1000 * seq, frame=10 * seq)
        log.add(
            "action_accepted", accept(), seq=seq + 1, time_ms=1000 * seq + gap, frame=10 * seq + 2
        )
    summary = log.summary()
    assert [(i.reason, i.gap_ms, i.gap_frames) for i in summary.intervals] == [
        ("expiry", 17, 2),
        ("explicit_release", 900, 2),
        ("other", 51, 2),
        ("replaced", 0, 2),
    ]
    assert summary.intervals[0] == ReleaseInterval(A, 1, 1, 2, 1, 2, "expiry", 17, 2)
    assert summary.interval_stats == IntervalStats(4, 0, 34.0, 900)
    assert "Peer" not in repr(summary)


def test_sequence_grouping_counts_inputs_tears_releases_and_directions():
    log = Log().add("action_accepted", accept("left", 6), seq=1, time_ms=1000, frame=10)
    for delay in ("4", "2.5", "na"):
        log.add("input", shoot_input(delay, "10"), seq=1, time_ms=1010, frame=11)
    log.add("input", " hook=IS_ACTION_PRESSED button=6 returned=true", seq=1)
    for _ in range(4):
        log.add("fire_tear", tear("9", "10"), seq=1, time_ms=1020, frame=12)
    log.add("release", release(), seq=1, time_ms=1100, frame=16)
    log.add("action_accepted", accept("none", 3), seq=2, time_ms=1120, frame=17)
    log.add("input", shoot_input("1", "10"), seq=2, time_ms=1130, frame=18)
    for _ in range(3):
        log.add("fire_tear", tear("5.5", "10"), seq=2, time_ms=1140, frame=19)
    log.add("action_accepted", accept("left", 3), seq=3, time_ms=1200, frame=21)
    summary = log.summary()
    first, second, third = summary.groups
    assert (first.sequence, first.shoot, first.frames, first.move) == (1, "left", 6, "none")
    assert first.events == {"action_accepted": 1, "input": 4, "fire_tear": 4, "release": 1}
    assert first.tear_log_saturated and not second.tear_log_saturated
    assert (first.first_id, first.last_id, first.first_frame, first.last_frame) == (1, 10, 10, 16)
    assert (first.first_time_ms, first.last_time_ms) == (1000, 1100)
    assert first.cooldowns["input.fire_delay"] == ValueRange(2, 1, 2.5, 4.0)
    assert first.cooldowns["fire_tear.fire_delay"] == ValueRange(4, 0, 9.0, 9.0)
    assert second.cooldowns["fire_tear.fire_delay"] == ValueRange(3, 0, 5.5, 5.5)
    assert third.events == {"action_accepted": 1} and third.cooldowns == {}
    assert summary.shoot_directions == {"left": 2, "none": 1}
    assert summary.input_phases == {"GET_ACTION_VALUE/1.0": 4, "IS_ACTION_PRESSED/true": 1}
    assert summary.cooldowns["input.fire_delay"] == ValueRange(3, 1, 1.0, 4.0)
    assert summary.events["fire_tear"] == 7


@pytest.mark.parametrize("reason", ["count", "deadline", "line_limit"])
def test_budget_stops_mark_the_trace_incomplete(reason):
    summary = Log().add("action_accepted", accept()).add("stop", f" reason={reason}").summary()
    assert summary.stop_reason == reason and summary.incomplete
    assert summary.incomplete_reasons == (f"stopped_by_{reason}",)


def test_explicit_close_stop_ends_the_window_without_flagging_a_budget_stop():
    log = Log().add("action_accepted", accept()).add("input", shoot_input())
    summary = log.add("release", release("closed")).add("stop", " reason=close").summary()
    assert summary.stop_reason == "close"
    assert not summary.incomplete and summary.incomplete_reasons == ()
    assert "physical keyboard neutrality" in " ".join(summary.limitations)


def test_close_stop_is_a_handoff_boundary_for_release_intervals():
    log = Log().add("action_accepted", accept(), seq=1).add("release", release(), seq=1)
    log.add("stop", " reason=close", seq=1).add("action_accepted", accept(), seq=2)
    summary = log.summary()
    assert summary.intervals == () and summary.excluded_intervals == 1
    assert "records_after_stop" in summary.incomplete_reasons


@pytest.mark.parametrize("last", ["close", "pre_game_exit", "release"])
def test_missing_stop_record_is_incomplete(last):
    extra = {"close": " reason=Peer disconnected", "release": release()}.get(last, "")
    summary = Log().add("action_accepted", accept()).add(last, extra).summary()
    assert summary.stop_reason is None and summary.incomplete
    assert summary.incomplete_reasons == ("no_stop_record",)


def test_empty_input_is_incomplete_without_records():
    summary = analyze_trace([])
    assert summary.records == 0 and summary.groups == () and summary.incomplete
    assert summary.incomplete_reasons == ("no_stop_record",)


def test_rejects_gaps_scan_limit_and_extra_stops_add_incompleteness_reasons():
    log = Log().add("action_accepted", accept())
    log.lines.append(line(4, "stop", " reason=count"))  # ids 2 and 3 missing
    log.lines.append(line(5, "stop", " reason=deadline"))
    log.lines.append(line(6, "teleport"))
    summary = log.summary()
    assert summary.missing_ids == 2 and summary.rejected == {"unknown_event": 1}
    assert summary.incomplete_reasons == (
        "stopped_by_count",
        "multiple_stop_records",
        "records_after_stop",
        "rejected_records",
        "id_gaps",
    )
    late = Log().add("stop", " reason=count").add("render_enter").summary()
    assert "records_after_stop" in late.incomplete_reasons


def test_scan_is_bounded_and_flagged_without_reading_the_whole_iterable():
    consumed = []

    def source():
        for number in range(1000):
            consumed.append(number)
            yield f"unrelated {number}"

    summary = analyze_trace(source(), max_lines=10)
    assert summary.scanned_lines == 10 and len(consumed) == 11
    assert "scan_limit_reached" in summary.incomplete_reasons


@pytest.mark.parametrize("max_lines", [MAX_SCAN_LINES + 1, 10**12, -1])
def test_scan_budget_cannot_be_raised_above_the_hard_cap(max_lines):
    consumed = []

    def source():
        consumed.append(1)
        yield line(1, "render_enter")

    for function in (parse_trace, analyze_trace):
        with pytest.raises(ValueError, match="max_lines"):
            function(source(), max_lines=max_lines)
    assert consumed == []
    assert parse_trace([], max_lines=MAX_SCAN_LINES).scanned_lines == 0
    assert parse_trace([line(1, "render_enter")], max_lines=0).scan_truncated


def test_summary_is_json_safe_and_bounded_by_the_record_id_range():
    log = Log()
    for _ in range(600):
        log.add("render_enter", seq=None)
    parsed = parse_trace(log.lines)
    assert len(parsed.records) == 512 and parsed.rejected == {"malformed": 88}
    assert len(parsed.rejected_lines) == 16
    text = json.dumps(asdict(analyze_trace(log.lines)), allow_nan=False)
    assert json.loads(text)["records"] == 512


def test_summary_makes_no_rate_loss_or_causal_claims():
    names = {
        f.name
        for cls in (TraceSummary, GroupSummary, ValueRange, IntervalStats, ReleaseInterval)
        for f in fields(cls)
    }
    claims = {
        "rate",
        "rates",
        "shot",
        "shots",
        "loss",
        "lost",
        "consumed",
        "consumption",
        "cause",
        "causal",
        "effect",
    }
    assert not [n for n in names if claims & set(n.split("_"))]
    assert ValueRange.__slots__ == ("samples", "missing", "minimum", "maximum")
    summary = Log().add("action_accepted", accept()).add("input", shoot_input()).summary()
    assert "fire_tear" not in summary.groups[0].events and not summary.groups[0].tear_log_saturated
    text = " ".join(summary.limitations)
    assert summary.limitations == LIMITATIONS
    assert "first four" in text and "not evidence that no shot" in text
    assert "No maximum firing rate" in text and "physical keyboard neutrality" in text
