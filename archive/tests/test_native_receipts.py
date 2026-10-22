"""Behavioral tests for the bounded receipt assembler. All records here are simulated."""

import pytest
from synthetic import SESSION, event, frame
from test_native_events import OTHER, native
from test_native_protocol import ack, command, completion

from isaac_threrisaifuture import native_receipts
from isaac_threrisaifuture.native_events import NativeEventCursor
from isaac_threrisaifuture.native_receipts import (
    MAX_EVENT_RECORDS,
    MAX_RECORDS,
    MAX_TOTAL_BYTES,
    NativeReceiptAssembler,
    NativeStepReceipt,
)
from isaac_threrisaifuture.observation import MAX_MESSAGE_BYTES, ProtocolError
from isaac_threrisaifuture.observer_client import ORACLE_KINDS

KIND_PAYLOADS = {
    "enemy_spawned": dict(entity_id=1, spawn_generation=1, amount=1.0),
    "enemy_damaged": dict(entity_id=1, spawn_generation=1, amount=1.0),
    "enemy_killed": dict(entity_id=1, spawn_generation=1),
    "player_damaged": dict(amount=1.0, damage_source="enemy"),
    "player_healed": dict(amount=1.0),
    "room_cleared": {},
    "player_died": {},
}


def wire(model):
    return model.model_dump_json().encode()


def baseline(**changes):
    values = dict(frame_id=100, provenance="game_api")
    values.update(changes)
    return frame(**values)


def pad(raw, size=MAX_MESSAGE_BYTES):
    return raw + b" " * (size - len(raw))


def make(cursor=None, kinds=("room_cleared",)):
    cursor = cursor or NativeEventCursor(SESSION, 1)
    return NativeReceiptAssembler(command(), baseline(), cursor, oracle_kinds=kinds), cursor


def feed_all(asm, *records):
    result = None
    for record in records:
        result = asm.feed(record)
    return result


def ev(event_id, frame_id):
    return wire(native(event_id=event_id, frame_id=frame_id))


def foreign(event_id=1, frame_id=103, **ctx):
    nested = event(frame_id=frame_id, provenance="game_api", **ctx)
    return wire(native(event_id=event_id, frame_id=frame_id, event=nested, **ctx))


def kinded(kind, event_id=1, frame_id=103, **ctx):
    nested = event(
        kind=kind, frame_id=frame_id, provenance="game_api", **KIND_PAYLOADS[kind], **ctx
    )
    return native(event_id=event_id, frame_id=frame_id, event=nested, **ctx)


def done(last_event_id=0, **changes):
    return wire(completion(last_event_id=last_event_id, **changes))


def test_limits_are_the_frozen_values():
    assert (MAX_EVENT_RECORDS, MAX_RECORDS, MAX_TOTAL_BYTES, MAX_MESSAGE_BYTES) == (
        32,
        34,
        65536,
        16384,
    )


def test_cursor_exposes_its_binding_read_only():
    cursor = NativeEventCursor(SESSION, 3)
    assert (cursor.session_id, cursor.game_epoch) == (SESSION, 3)
    with pytest.raises(AttributeError):
        cursor.session_id = OTHER  # type: ignore[misc]


def test_zero_events_yield_a_receipt_and_leave_the_cursor():
    asm, cursor = make()
    assert asm.feed(wire(ack())) is None
    receipt = asm.feed(done())
    assert isinstance(receipt, NativeStepReceipt)
    assert receipt.events == ()
    assert receipt.completion.last_event_id == 0
    assert cursor.last_id == 0


def test_multiple_events_preserve_envelopes_and_advance_the_cursor():
    asm, cursor = make()
    sent = [native(event_id=i, frame_id=f) for i, f in ((1, 102), (2, 103), (3, 103))]
    receipt = feed_all(asm, wire(ack()), *[wire(e) for e in sent], done(last_event_id=3))
    assert receipt is not None
    assert list(receipt.events) == sent
    assert [e.event_id for e in receipt.events] == [1, 2, 3]
    assert cursor.last_id == 3


def test_replayed_events_from_earlier_intervals_are_deduplicated():
    cursor = NativeEventCursor(SESSION, 1)
    cursor.take(native(event_id=1, frame_id=50), 40, 60)
    cursor.take(native(event_id=2, frame_id=51), 40, 60)
    asm, _ = make(cursor)
    receipt = feed_all(asm, wire(ack()), ev(1, 50), ev(2, 51), ev(3, 104), done(last_event_id=3))
    assert receipt is not None
    assert [e.event_id for e in receipt.events] == [3]
    assert cursor.last_id == 3


def test_replay_only_receipt_keeps_the_watermark_equal_to_the_cursor():
    cursor = NativeEventCursor(SESSION, 1)
    cursor.take(native(event_id=1, frame_id=50), 40, 60)
    asm, _ = make(cursor)
    receipt = feed_all(asm, wire(ack()), ev(1, 50), done(last_event_id=1))
    assert receipt is not None and receipt.events == ()


@pytest.mark.parametrize(
    "events",
    [
        [(1, 102), (3, 103)],  # gap
        [(1, 102), (2, 103), (4, 104)],  # gap after valid prefix
        [(1, 102), (2, 108)],  # late: after the completion frame
        [(1, 100)],  # not after the baseline
        [(1, 102), (2, 99)],  # early frame
    ],
)
def test_rejected_batches_never_advance_the_cursor(events):
    asm, cursor = make()
    records = [wire(ack()), *[ev(i, f) for i, f in events], done(last_event_id=len(events))]
    with pytest.raises(ProtocolError):
        feed_all(asm, *records)
    assert cursor.last_id == 0


@pytest.mark.parametrize("ctx", [{"session_id": OTHER}, {"game_epoch": 2}, {"room_visit": 2}])
def test_foreign_event_context_is_rejected(ctx):
    asm, cursor = make()
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError):
        asm.feed(foreign(**ctx))
    assert cursor.last_id == 0


def test_foreign_duplicate_context_is_still_checked():
    cursor = NativeEventCursor(SESSION, 1)
    cursor.take(native(event_id=1, frame_id=50), 40, 60)
    asm, _ = make(cursor)
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError):
        asm.feed(foreign(event_id=1, room_visit=2))


def test_requested_kinds_are_accepted_in_wire_order():
    asm, cursor = make(kinds=frozenset(("player_died", "room_cleared")))
    sent = [kinded("room_cleared", 1, 102), kinded("player_died", 2, 103)]
    receipt = feed_all(asm, wire(ack()), *map(wire, sent), done(last_event_id=2))
    assert receipt is not None and list(receipt.events) == sent
    assert cursor.last_id == 2


@pytest.mark.parametrize("kind", ORACLE_KINDS)
def test_each_kind_is_accepted_when_requested_and_faults_when_another_is_requested(kind):
    asm, cursor = make(kinds=(kind,))
    receipt = feed_all(asm, wire(ack()), wire(kinded(kind, 1, 102)), done(last_event_id=1))
    assert receipt is not None and cursor.last_id == 1
    other = next(candidate for candidate in ORACLE_KINDS if candidate != kind)
    asm, cursor = make(kinds=(other,))
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError, match="not requested"):
        asm.feed(wire(kinded(kind, 1, 102)))
    assert cursor.last_id == 0


@pytest.mark.parametrize(
    "sent",
    [
        [(1, "player_died")],
        [(1, "room_cleared"), (2, "player_died")],  # the valid prefix is not committed either
        [(1, "room_cleared"), (2, "room_cleared"), (3, "enemy_killed")],
    ],
)
def test_unrequested_kind_faults_before_any_commit(sent):
    asm, cursor = make()  # requests room_cleared only
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError, match="not requested"):
        for event_id, kind in sent:
            asm.feed(wire(kinded(kind, event_id, 102)))
    assert cursor.last_id == 0 and asm._pending == []
    with pytest.raises(ProtocolError):  # a faulted assembler can never yield a receipt
        asm.feed(done(last_event_id=len(sent)))
    assert cursor.last_id == 0


def test_replayed_event_id_does_not_bypass_the_kind_check():
    cursor = NativeEventCursor(SESSION, 1)
    cursor.take(native(event_id=1, frame_id=50), 40, 60)
    asm, _ = make(cursor)
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError, match="not requested"):
        asm.feed(wire(kinded("player_died", 1, 50)))
    assert cursor.last_id == 1


@pytest.mark.parametrize("kind", ORACLE_KINDS)
def test_default_assembler_accepts_no_native_event(kind):
    cursor = NativeEventCursor(SESSION, 1)
    asm = NativeReceiptAssembler(command(), baseline(), cursor)
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError, match="not requested"):
        asm.feed(wire(kinded(kind, 1, 102)))
    assert cursor.last_id == 0


def test_without_requested_kinds_an_event_free_receipt_still_completes():
    asm, cursor = make(kinds=())
    receipt = feed_all(asm, wire(ack()), done())
    assert receipt is not None and receipt.events == () and cursor.last_id == 0


@pytest.mark.parametrize(
    "kinds",
    ["room_cleared", ["room_cleared"], None, ("bogus",), (1,), ("room_cleared", None)],
)
def test_requested_kinds_must_be_known_names_in_a_tuple_or_frozenset(kinds):
    with pytest.raises(ProtocolError, match="Oracle kinds"):
        make(kinds=kinds)


@pytest.mark.parametrize(
    "records",
    [
        [lambda: ev(1, 102)],  # event before acknowledgement
        [lambda: done()],  # completion before acknowledgement
        [lambda: wire(ack()), lambda: wire(ack())],  # second acknowledgement
        [lambda: wire(ack(sequence=2))],
        [lambda: wire(ack(session_id=OTHER))],
        [lambda: wire(ack(game_epoch=2))],
        [lambda: wire(ack(room_visit=2))],
        [lambda: wire(ack(kind="heartbeat"))],
        [lambda: wire(ack(frame_id=116))],  # outside freshness window
        [lambda: wire(ack(frame_id=99))],
    ],
)
def test_ack_order_and_identity_are_strict(records):
    asm, cursor = make()
    with pytest.raises(ProtocolError):
        feed_all(asm, *[make_record() for make_record in records])
    assert cursor.last_id == 0


def test_ack_after_events_is_rejected():
    asm, _ = make()
    feed_all(asm, wire(ack()), ev(1, 102))
    with pytest.raises(ProtocolError):
        asm.feed(wire(ack()))


@pytest.mark.parametrize(
    ("events", "watermark"),
    [([(1, 102)], 0), ([(1, 102)], 2), ([], 1), ([(1, 102), (2, 103)], 1)],
)
def test_watermark_must_equal_the_assembled_last_event(events, watermark):
    asm, cursor = make()
    records = [wire(ack()), *[ev(i, f) for i, f in events], done(last_event_id=watermark)]
    with pytest.raises(ProtocolError):
        feed_all(asm, *records)
    assert cursor.last_id == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "expired", "reason": "wall_deadline", "elapsed": 3},
        {"status": "cancelled", "reason": "pause", "elapsed": 0},
        {"status": "cancelled", "reason": "transition", "elapsed": 2},
    ],
)
def test_noncompleted_results_are_faults_not_receipts(changes):
    asm, cursor = make()
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError):
        asm.feed(done(**changes))
    assert cursor.last_id == 0


def test_completion_must_match_command_and_ack():
    asm, _ = make()
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError):
        asm.feed(done(sequence=2))
    asm, _ = make()
    asm.feed(wire(ack()))
    with pytest.raises(ProtocolError):  # acceptance frame differs from the ack
        asm.feed(done(accepted=102, elapsed=6))


def test_exactly_thirty_two_events_in_thirty_four_records_succeed():
    asm, cursor = make()
    events = [ev(i, 101 + i % 6) for i in range(1, 33)]
    receipt = feed_all(asm, wire(ack()), *events, done(last_event_id=32))
    assert receipt is not None and len(receipt.events) == 32
    assert cursor.last_id == 32


def test_thirty_third_event_record_is_rejected_and_clears_pending():
    asm, cursor = make()
    feed_all(asm, wire(ack()), *[ev(i, 101) for i in range(1, 33)])
    with pytest.raises(ProtocolError):
        asm.feed(ev(33, 101))
    assert asm._pending == []
    assert cursor.last_id == 0


def test_duplicate_records_consume_the_event_budget():
    cursor = NativeEventCursor(SESSION, 1)
    cursor.take(native(event_id=1, frame_id=50), 40, 60)
    asm, _ = make(cursor)
    asm.feed(wire(ack()))
    for _ in range(32):
        asm.feed(ev(1, 50))
    with pytest.raises(ProtocolError):
        asm.feed(ev(1, 50))


def test_record_and_byte_budgets_apply_before_storing(monkeypatch):
    monkeypatch.setattr(native_receipts, "MAX_RECORDS", 2)
    asm, _ = make()
    feed_all(asm, wire(ack()), ev(1, 102))
    with pytest.raises(ProtocolError):
        asm.feed(done(last_event_id=1))
    monkeypatch.undo()
    first, second = wire(ack()), ev(1, 102)
    monkeypatch.setattr(native_receipts, "MAX_TOTAL_BYTES", len(first) + len(second) - 1)
    asm, _ = make()
    asm.feed(first)
    with pytest.raises(ProtocolError):
        asm.feed(second)


def test_oversized_record_is_rejected():
    asm, _ = make()
    raw = b'{"type":"command_ack","pad":"' + b"a" * MAX_MESSAGE_BYTES + b'"}'
    with pytest.raises(ProtocolError):
        asm.feed(raw)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"{not json}",
        b"\xff\xfe",
        b"[]",
        b'{"type":"bogus"}',
        b'{"type":"command_ack"}\n',
        b'{"type":"command_ack"}',
        "text",
    ],
)
def test_malformed_records_fail_closed(raw):
    asm, cursor = make()
    with pytest.raises(ProtocolError):
        asm.feed(raw)
    assert cursor.last_id == 0
    with pytest.raises(ProtocolError):  # failed assemblers are never reusable
        asm.feed(wire(ack()))


@pytest.mark.parametrize(
    "build",
    [
        lambda: (command(), baseline(frame_id=99), NativeEventCursor(SESSION, 1)),
        lambda: (command(), baseline(session_id=OTHER), NativeEventCursor(SESSION, 1)),
        lambda: (command(), baseline(game_epoch=2), NativeEventCursor(SESSION, 1)),
        lambda: (command(), baseline(room_visit=2), NativeEventCursor(SESSION, 1)),
        lambda: (command(), frame(frame_id=100), NativeEventCursor(SESSION, 1)),
        lambda: (command(), baseline(), NativeEventCursor(OTHER, 1)),
        lambda: (command(), baseline(), NativeEventCursor(SESSION, 2)),
        lambda: (command(), None, NativeEventCursor(SESSION, 1)),
        lambda: (command(), baseline(), None),
    ],
)
def test_baseline_and_cursor_binding_are_required(build):
    with pytest.raises(ProtocolError):
        NativeReceiptAssembler(*build())


def test_external_cursor_mutation_is_detected():
    asm, cursor = make()
    asm.feed(wire(ack()))
    asm.feed(ev(1, 102))
    cursor.take(native(event_id=1, frame_id=50), 40, 60)  # another consumer advanced it
    with pytest.raises(ProtocolError, match="cursor changed"):
        asm.feed(done(last_event_id=1))
    assert cursor.last_id == 1


def test_finished_assembler_rejects_reuse():
    asm, _ = make()
    assert feed_all(asm, wire(ack()), done()) is not None
    with pytest.raises(ProtocolError):
        asm.feed(wire(ack()))
    with pytest.raises(ProtocolError):
        asm.feed(done())


def test_oversized_record_is_rejected_before_any_json_parse(monkeypatch):
    calls = []
    monkeypatch.setattr(native_receipts.json, "loads", lambda *a: calls.append(a))
    asm, _ = make()
    with pytest.raises(ProtocolError):
        asm.feed(b"x" * (MAX_MESSAGE_BYTES + 1))
    assert calls == []
    assert asm._pending == []


def test_budget_is_enforced_before_any_json_parse(monkeypatch):
    asm, _ = make()
    feed_all(asm, pad(wire(ack())), *[pad(ev(i, 101 + i)) for i in (1, 2, 3)])
    calls = []
    monkeypatch.setattr(native_receipts.json, "loads", lambda *a: calls.append(a))
    with pytest.raises(ProtocolError):
        asm.feed(b"{}")
    assert calls == []


def test_record_of_exactly_the_per_record_limit_is_accepted_and_one_more_is_not():
    asm, _ = make()
    assert asm.feed(pad(wire(ack()))) is None
    asm, cursor = make()
    with pytest.raises(ProtocolError):
        asm.feed(pad(wire(ack()), MAX_MESSAGE_BYTES + 1))
    assert cursor.last_id == 0


def test_real_total_byte_boundary_accepts_exactly_65536_then_faults():
    asm, cursor = make()
    records = [pad(wire(ack())), *[pad(ev(i, 101 + i)) for i in (1, 2, 3)]]
    assert sum(map(len, records)) == MAX_TOTAL_BYTES
    assert feed_all(asm, *records) is None
    with pytest.raises(ProtocolError):
        asm.feed(ev(4, 105))
    assert cursor.last_id == 0


def test_padded_four_record_receipt_of_exactly_65536_bytes_completes():
    asm, cursor = make()
    records = [
        pad(wire(ack())),
        pad(ev(1, 102)),
        pad(ev(2, 103)),
        pad(done(last_event_id=2)),
    ]
    assert sum(map(len, records)) == MAX_TOTAL_BYTES
    receipt = feed_all(asm, *records)
    assert receipt is not None and len(receipt.events) == 2
    assert cursor.last_id == 2


@pytest.mark.parametrize("tail", [b"\n", b"\r\n", b"\r"])
def test_complete_valid_ack_with_line_delimiter_is_rejected(tail):
    asm, cursor = make()
    with pytest.raises(ProtocolError):
        asm.feed(wire(ack()) + tail)
    assert cursor.last_id == 0


def test_spaces_and_tabs_are_ordinary_json_whitespace():
    asm, _ = make()
    assert asm.feed(wire(ack()) + b" \t ") is None
