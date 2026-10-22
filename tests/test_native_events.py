"""Native oracle envelope, cursor and recording stream tests. Data here is simulated."""

import json

import pytest
from pydantic import ValidationError
from synthetic import SESSION, event, frame

from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.native_events import NativeEventCursor, NativeOracleEvent
from isaac_threrisaifuture.observation import MAX_MESSAGE_BYTES, ProtocolError, decode
from isaac_threrisaifuture.recording import JsonlRecorder, open_replay

BAD = (ValidationError, ProtocolError)
OTHER = "b" * 32
KINDS = ("room_cleared",)


def native(event_id=1, frame_id=5, **changes):
    values = dict(
        session_id=SESSION,
        game_epoch=1,
        room_visit=1,
        frame_id=frame_id,
        event_id=event_id,
        event=event(frame_id=frame_id, provenance="game_api"),
    )
    values.update(changes)
    return NativeOracleEvent(**values)


def test_envelope_round_trips_through_bounded_decode():
    item = native(event_id=7)
    assert decode(item.model_dump_json().encode(), NativeOracleEvent) == item


@pytest.mark.parametrize("value", [0, -1, True, 2**53, 1.0, "1"])
def test_event_id_is_a_positive_bounded_integer(value):
    with pytest.raises(BAD):
        native(event_id=value)


@pytest.mark.parametrize("value", [0, 2, True, "1"])
def test_envelope_version_must_be_exactly_one(value):
    with pytest.raises(BAD):
        native(protocol_version=value)


@pytest.mark.parametrize(
    "bad",
    [
        {"session_id": OTHER},
        {"game_epoch": 2},
        {"room_visit": 2},
        {"event": event(frame_id=6, provenance="game_api")},
    ],
)
def test_nested_identity_must_match_the_envelope(bad):
    with pytest.raises(BAD):
        native(**bad)


def test_native_events_need_game_api_provenance_and_schema_one():
    with pytest.raises(BAD):
        native(event=event(frame_id=5, provenance="synthetic"))
    with pytest.raises(BAD):
        native(event=event(frame_id=5, provenance="game_api", observation_schema_version=2))


def test_unknown_fields_and_oversized_records_fail_decode():
    raw = json.loads(native().model_dump_json())
    raw["extra"] = 1
    with pytest.raises(ProtocolError):
        decode(json.dumps(raw).encode(), NativeOracleEvent)
    padded = native().model_dump_json().encode()[:-1] + b',"x":"' + b"a" * MAX_MESSAGE_BYTES + b'"}'
    with pytest.raises(ProtocolError):
        decode(padded, NativeOracleEvent)


def test_contiguous_ids_and_several_events_in_one_frame():
    cursor = NativeEventCursor(SESSION, 1)
    for i in (1, 2, 3):
        item = native(event_id=i, frame_id=5)
        assert cursor.take(item, 4, 8) is item
    assert cursor.take(native(event_id=4, frame_id=8), 4, 8).event_id == 4
    assert cursor.last_id == 4


def test_duplicate_old_frame_bypasses_only_the_frame_check_not_interval_validation():
    cursor = NativeEventCursor(SESSION, 1)
    cursor.take(native(event_id=1, frame_id=5), 4, 8)
    cursor.take(native(event_id=2, frame_id=12), 8, 16)
    # Replayed event 1 lies outside this interval, which is fine for a duplicate.
    assert cursor.take(native(event_id=1, frame_id=5), 8, 16) is None
    assert cursor.take(native(event_id=2, frame_id=12), 8, 16) is None
    assert cursor.last_id == 2


@pytest.mark.parametrize(
    ("start", "end"), [(8, 8), (16, 8), (-1, 16), (True, 16), (8, True), (8, 2**53), (1.0, 16)]
)
def test_duplicate_with_invalid_bounds_raises_and_keeps_the_cursor(start, end):
    cursor = NativeEventCursor(SESSION, 1)
    cursor.take(native(event_id=1, frame_id=5), 4, 8)
    with pytest.raises(ProtocolError):
        cursor.take(native(event_id=1, frame_id=5), start, end)
    assert cursor.last_id == 1


@pytest.mark.parametrize(
    ("event_id", "frame_id", "start", "end"),
    [
        (3, 5, 4, 8),  # gap
        (1, 4, 4, 8),  # frame equals the exclusive start
        (1, 9, 4, 8),  # frame after the interval
        (1, 5, 8, 4),  # reversed interval
        (1, 5, 5, 5),  # empty interval
        (1, 5, -1, 8),  # negative bound
        (1, 5, True, 8),  # bool is not an integer bound
        (1, 5, 4, 2**53),  # unbounded
    ],
)
def test_invalid_gap_or_interval_does_not_advance_the_cursor(event_id, frame_id, start, end):
    cursor = NativeEventCursor(SESSION, 1)
    with pytest.raises(ProtocolError):
        cursor.take(native(event_id=event_id, frame_id=frame_id), start, end)
    assert cursor.last_id == 0
    assert cursor.take(native(event_id=1, frame_id=5), 4, 8) is not None


@pytest.mark.parametrize("bad", [{"session_id": OTHER}, {"game_epoch": 2}])
def test_foreign_context_faults_even_for_a_consumed_id(bad):
    cursor = NativeEventCursor(SESSION, 1)
    cursor.take(native(event_id=1), 4, 8)
    foreign = native(event_id=1, event=event(frame_id=5, provenance="game_api", **bad), **bad)
    with pytest.raises(ProtocolError):
        cursor.take(foreign, 4, 8)
    assert cursor.last_id == 1


def test_new_session_gets_a_fresh_cursor():
    old = NativeEventCursor(SESSION, 1)
    old.take(native(event_id=1), 4, 8)
    fresh = NativeEventCursor(OTHER, 1)
    item = native(
        session_id=OTHER,
        event=event(frame_id=5, provenance="game_api", session_id=OTHER),
    )
    assert fresh.take(item, 4, 8) is item and fresh.last_id == 1


def test_cursor_state_stays_constant_after_many_events():
    cursor = NativeEventCursor(SESSION, 1)
    for i in range(1, 2001):
        cursor.take(native(event_id=i, frame_id=i + 1), i, i + 1)
    assert cursor.last_id == 2000
    assert not hasattr(cursor, "__dict__")  # fixed slots, no growing seen-set


@pytest.mark.parametrize("session", ["", "A" * 32, "a" * 31, None])
def test_cursor_rejects_invalid_identity(session):
    with pytest.raises(ProtocolError):
        NativeEventCursor(session, 1)
    with pytest.raises(ProtocolError):
        NativeEventCursor(SESSION, True)


def test_native_stream_round_trip_keeps_event_ids(tmp_path):
    path = tmp_path / "native.jsonl"
    items = [native(event_id=i, frame_id=5 + i) for i in (1, 2, 3)]
    with JsonlRecorder(
        path, "native_oracle_events", "game_api", native_oracle_kinds=KINDS
    ) as recorder:
        for item in items:
            recorder.record(item)
    manifest, records = open_replay(path, "native_oracle_events")
    assert manifest.stream == "native_oracle_events"
    assert list(records) == items
    assert [r.event_id for r in open_replay(path, "native_oracle_events")[1]] == [1, 2, 3]


def test_streams_stay_separate(tmp_path):
    policy = JsonlRecorder(tmp_path / "p.jsonl", "policy_frames", "game_api")
    legacy = JsonlRecorder(tmp_path / "o.jsonl", "oracle_events", "game_api")
    nat = JsonlRecorder(
        tmp_path / "n.jsonl", "native_oracle_events", "game_api", native_oracle_kinds=KINDS
    )
    with policy, legacy, nat:
        with pytest.raises(ProtocolError):
            policy.record(native())
        with pytest.raises(ProtocolError):
            legacy.record(native())
        with pytest.raises(ProtocolError):
            nat.record(event(frame_id=5, provenance="game_api"))
        with pytest.raises(ProtocolError):
            nat.record(frame(provenance="game_api"))
    for path, stream in (("p", "policy_frames"), ("o", "oracle_events")):
        with pytest.raises(ProtocolError):
            open_replay(tmp_path / f"{path}.jsonl", "native_oracle_events")
        assert open_replay(tmp_path / f"{path}.jsonl", stream)
    for stream in ("policy_frames", "oracle_events"):
        with pytest.raises(ProtocolError):
            open_replay(tmp_path / "n.jsonl", stream)


def test_legacy_oracle_replay_rejects_a_native_record_line(tmp_path):
    path = tmp_path / "mixed.jsonl"
    with JsonlRecorder(path, "oracle_events", "game_api"):
        pass
    with path.open("ab") as handle:
        handle.write(native().model_dump_json().encode() + b"\n")
    _, records = open_replay(path, "oracle_events")
    with pytest.raises(ProtocolError):
        list(records)


def test_encoder_rejects_native_events():
    with pytest.raises(ProtocolError):
        encode(native())


def test_synthetic_manifest_cannot_hold_native_events(tmp_path):
    with JsonlRecorder(
        tmp_path / "s.jsonl", "native_oracle_events", "synthetic", native_oracle_kinds=KINDS
    ) as recorder:
        with pytest.raises(ProtocolError):
            recorder.record(native())


def test_incompatible_manifest_version_and_provenance_are_rejected(tmp_path):
    path = tmp_path / "n.jsonl"
    with JsonlRecorder(
        path, "native_oracle_events", "game_api", native_oracle_kinds=KINDS
    ) as recorder:
        recorder.record(native())
    lines = path.read_bytes().split(b"\n")
    versioned = tmp_path / "v.jsonl"
    versioned.write_bytes(
        lines[0].replace(b'"observation_schema_version":4', b'"observation_schema_version":2')
        + b"\n"
        + lines[1]
        + b"\n"
    )
    with pytest.raises(ProtocolError):
        open_replay(versioned, "native_oracle_events")
    synthetic = tmp_path / "s.jsonl"
    synthetic.write_bytes(
        lines[0].replace(b'"game_api"', b'"synthetic"') + b"\n" + lines[1] + b"\n"
    )
    _, records = open_replay(synthetic, "native_oracle_events")
    with pytest.raises(ProtocolError):
        list(records)


def test_corrupt_and_blank_replay_lines_fail(tmp_path):
    path = tmp_path / "n.jsonl"
    with JsonlRecorder(
        path, "native_oracle_events", "game_api", native_oracle_kinds=KINDS
    ) as recorder:
        recorder.record(native())
    good = path.read_bytes()
    for tail in (b"{broken\n", b"\n"):
        bad = tmp_path / f"bad{len(tail)}.jsonl"
        bad.write_bytes(good + tail)
        _, records = open_replay(bad, "native_oracle_events")
        with pytest.raises(ProtocolError):
            list(records)
