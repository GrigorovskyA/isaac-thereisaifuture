"""Producer bookkeeping with fabricated API provenance; no real Isaac acceptance."""

from dataclasses import FrozenInstanceError, replace

import pytest
from pydantic import ValidationError
from synthetic import event, frame
from test_native_protocol import ack, command, completion

from isaac_threrisaifuture.native_events import NativeEventCursor, NativeOracleEvent
from isaac_threrisaifuture.native_outbox import NativeEventOutbox
from isaac_threrisaifuture.native_receipts import NativeReceiptAssembler
from isaac_threrisaifuture.observation import ProtocolError, decode

BAD = (ProtocolError, ValidationError)


def outbox(**limits):
    return NativeEventOutbox(frame(frame_id=100, provenance="game_api"), **limits)


def emit(box, tick=101, **changes):
    return box.append(event(frame_id=tick, provenance="game_api", **changes))


def assert_closed(box):
    assert box.closed and box.pending_count == box.pending_bytes == 0
    for operation in (lambda: emit(box), lambda: box.seal(120), lambda: box.acknowledge(None)):
        with pytest.raises(ProtocolError, match="closed"):
            operation()
    box.close()


def test_precommand_neutral_events_are_retained_until_delivery_and_decoded_by_cursor():
    box = outbox()
    first = emit(box, 101)  # No command acceptance has been observed or required.
    second = emit(box, 105)
    batch = box.seal(107)
    assert batch.events == (first, second)
    assert (batch.start_frame, batch.end_frame, batch.last_event_id) == (100, 107, 2)
    assert box.pending_count == 2 and box.pending_bytes == sum(map(len, batch.records))
    cursor = NativeEventCursor(first.session_id, first.game_epoch)
    for raw in batch.records:
        assert b"\n" not in raw and b"\r" not in raw
        cursor.take(decode(raw, NativeOracleEvent), batch.start_frame, batch.end_frame)
    assert cursor.last_id == batch.last_event_id
    box.acknowledge(batch)
    assert not box.closed and box.pending_count == box.pending_bytes == 0


@pytest.mark.parametrize("count", [0, 32])
def test_outbox_records_complete_a_bounded_consumer_receipt(count):
    box = outbox()
    for _ in range(count):
        emit(box, 101)
    batch = box.seal(107)
    cursor = NativeEventCursor(command().session_id, 1)
    reader = NativeReceiptAssembler(
        command(),
        frame(frame_id=100, provenance="game_api"),
        cursor,
        oracle_kinds=("room_cleared",),
    )
    records = (
        ack().model_dump_json().encode(),
        *batch.records,
        completion(last_event_id=batch.last_event_id).model_dump_json().encode(),
    )
    assert len(records) <= 34 and sum(map(len, records)) <= 65536
    for raw in records[:-1]:
        assert reader.feed(raw) is None
    result = reader.feed(records[-1])
    assert result is not None and result.events == batch.events
    assert cursor.last_id == batch.last_event_id == count
    box.acknowledge(batch)
    assert box.pending_count == box.pending_bytes == 0


def test_future_prefix_empty_watermarks_and_contiguous_ids_across_commits():
    box = outbox()
    emit(box, 110)
    empty = box.seal(105)
    assert empty.last_event_id == 0 and empty.events == empty.records == ()
    emit(box, 111)
    box.acknowledge(empty)
    assert box.pending_count == 2
    one = box.seal(110)
    assert [e.event_id for e in one.events] == [1]
    box.acknowledge(one)
    assert box.pending_count == 1
    two = box.seal(111)
    assert [e.event_id for e in two.events] == [2]
    box.acknowledge(two)
    empty = box.seal(115)
    assert empty.last_event_id == 2 and not empty.events
    box.acknowledge(empty)
    assert emit(box, 116).event_id == 3


def test_multiple_events_in_same_frame_and_detached_batch():
    box = outbox()
    emit(box)
    emit(box)
    batch = box.seal(101)
    assert [e.event_id for e in batch.events] == [1, 2]
    with pytest.raises(FrozenInstanceError):
        batch.end_frame = 999
    box.acknowledge(batch)
    assert batch.end_frame == 101 and len(batch.events) == 2


@pytest.mark.parametrize(
    "changes", [{"session_id": "b" * 32}, {"game_epoch": 2}, {"room_visit": 2}]
)
def test_context_change_faults_and_clears_pending(changes):
    box = outbox()
    emit(box)
    with pytest.raises(ProtocolError, match="identity"):
        emit(box, 102, **changes)
    assert_closed(box)


@pytest.mark.parametrize("tick", [99, 100, 101])
def test_late_or_regressing_frames_fault(tick):
    box = outbox()
    emit(box, 102)
    with pytest.raises(ProtocolError, match="frame"):
        emit(box, tick)
    assert_closed(box)


@pytest.mark.parametrize("tick", [100, 101, 105])
def test_event_at_or_before_staged_boundary_faults_even_before_delivery(tick):
    box = outbox()
    emit(box)
    batch = box.seal(105)
    with pytest.raises(ProtocolError, match="frame"):
        emit(box, tick)
    assert_closed(box)
    with pytest.raises(ProtocolError):
        box.acknowledge(batch)


def test_event_at_committed_endpoint_faults():
    box = outbox()
    batch = box.seal(105)
    box.acknowledge(batch)
    with pytest.raises(ProtocolError):
        emit(box, 105)
    assert_closed(box)


@pytest.mark.parametrize("limit", [1, 32])
def test_record_limit_includes_staged_and_future_events_without_eviction(limit):
    box = outbox(max_events=limit)
    for i in range(limit):
        emit(box, 101 + i)
    box.seal(101)
    assert box.pending_count == limit
    with pytest.raises(ProtocolError, match="budget"):
        emit(box, 150)
    assert_closed(box)


def test_exact_serialized_byte_budget_and_one_byte_short():
    reference = outbox()
    emit(reference)
    emit(reference)
    size = reference.pending_bytes
    box = outbox(max_bytes=size)
    emit(box)
    emit(box)
    assert box.pending_bytes == size
    with pytest.raises(ProtocolError, match="budget"):
        emit(box)
    assert_closed(box)
    short = outbox(max_bytes=size - 1)
    emit(short)
    with pytest.raises(ProtocolError, match="budget"):
        emit(short)
    assert_closed(short)


@pytest.mark.parametrize("value", [0, -1, True, 1.0, "1", 33, 2**53])
def test_record_limits_cannot_be_weakened(value):
    with pytest.raises(ProtocolError):
        outbox(max_events=value)


@pytest.mark.parametrize("value", [0, -1, True, 1.0, "1", 32769, 2**53])
def test_byte_limits_cannot_be_weakened(value):
    with pytest.raises(ProtocolError):
        outbox(max_bytes=value)


@pytest.mark.parametrize("value", [100, 99, -1, True, 101.0, "101", 2**53])
def test_bad_endpoint_faults_and_clears(value):
    box = outbox()
    emit(box)
    with pytest.raises(ProtocolError):
        box.seal(value)
    assert_closed(box)


def test_second_seal_before_delivery_faults():
    box = outbox()
    emit(box)
    box.seal(105)
    with pytest.raises(ProtocolError):
        box.seal(106)
    assert_closed(box)


@pytest.mark.parametrize("wrong", ["copy", "foreign", "none", "replay"])
def test_only_exact_current_batch_can_commit(wrong):
    box = outbox()
    emit(box)
    batch = box.seal(105)
    if wrong == "replay":
        box.acknowledge(batch)
        emit(box, 106)
        box.seal(110)
        supplied = batch
    elif wrong == "copy":
        supplied = replace(batch)
    elif wrong == "foreign":
        supplied = outbox().seal(105)
    else:
        supplied = None
    with pytest.raises(ProtocolError):
        box.acknowledge(supplied)
    assert_closed(box)


def test_delivery_failure_close_and_reconnect_require_new_baseline():
    box = outbox()
    emit(box)
    batch = box.seal(105)
    box.close()  # Future sender's required cleanup after simulated send failure.
    assert_closed(box)
    fresh = NativeEventOutbox(frame(frame_id=105, provenance="game_api", session_id="b" * 32))
    with pytest.raises(ProtocolError):
        fresh.acknowledge(batch)
    assert_closed(fresh)
    fresh = outbox()
    assert emit(fresh).event_id == 1  # No resumption of old delivery state or input authority.


@pytest.mark.parametrize(
    "invalid",
    [None, {}, event(provenance="synthetic"), event().model_copy(update={"kind": "fake"})],
)
def test_invalid_or_synthetic_events_clear_pending(invalid):
    box = outbox()
    emit(box)
    with pytest.raises(BAD):
        box.append(invalid)
    assert_closed(box)


@pytest.mark.parametrize(
    "baseline", [None, {}, frame(), frame().model_copy(update={"frame_id": True})]
)
def test_baseline_requires_valid_native_model(baseline):
    with pytest.raises(BAD):
        NativeEventOutbox(baseline)
