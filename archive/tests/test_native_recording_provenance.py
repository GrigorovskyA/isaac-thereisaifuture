"""Requested-kind metadata in native oracle recordings. Simulated data only; no game."""

import json

import pytest
from synthetic import event, frame
from test_native_events import native

from isaac_threrisaifuture.observation import ProtocolError
from isaac_threrisaifuture.recording import JsonlRecorder, open_replay

NATIVE = "native_oracle_events"
HEAD = {
    "type": "recording_manifest",
    "observation_schema_version": 1,
    "stream": NATIVE,
    "provenance": "game_api",
}
ROOM = ("room_cleared",)
BOTH = ("room_cleared", "player_died")


def item(kind, event_id=1):
    return native(event_id=event_id, event=event(kind=kind, frame_id=5, provenance="game_api"))


def line(value):
    return json.dumps(value, separators=(",", ":")).encode()


def handwritten(path, manifest, *records):
    lines = [line(manifest), *(r.model_dump_json().encode() for r in records)]
    path.write_bytes(b"\n".join(lines) + b"\n")
    return path


def test_explicit_kinds_are_persisted_in_order_and_replayed(tmp_path):
    path = tmp_path / "n.jsonl"
    with JsonlRecorder(path, NATIVE, "game_api", native_oracle_kinds=BOTH) as recorder:
        recorder.record(item("player_died", 1))
        recorder.record(item("room_cleared", 2))
    assert json.loads(path.read_bytes().split(b"\n")[0])["native_oracle_kinds"] == list(BOTH)
    manifest, records = open_replay(path, NATIVE)
    assert manifest.native_oracle_kinds == BOTH
    assert [r.event.kind for r in records] == ["player_died", "room_cleared"]


def test_subset_of_requested_kinds_needs_no_event_of_every_kind(tmp_path):
    path = tmp_path / "n.jsonl"
    with JsonlRecorder(path, NATIVE, "game_api", native_oracle_kinds=BOTH):
        pass
    manifest, records = open_replay(path, NATIVE)
    assert manifest.native_oracle_kinds == BOTH
    assert list(records) == []  # requested is not delivered; absence is not a negative outcome


def test_empty_request_is_persisted_as_empty_and_rejects_every_event(tmp_path):
    path = tmp_path / "n.jsonl"
    with JsonlRecorder(path, NATIVE, "game_api", native_oracle_kinds=()) as recorder:
        with pytest.raises(ProtocolError):
            recorder.record(item("room_cleared"))
    assert json.loads(path.read_bytes().split(b"\n")[0])["native_oracle_kinds"] == []
    manifest, records = open_replay(path, NATIVE)
    assert manifest.native_oracle_kinds == ()
    assert list(records) == []
    forged = handwritten(
        tmp_path / "f.jsonl", {**HEAD, "native_oracle_kinds": []}, item("player_died")
    )
    _, records = open_replay(forged, NATIVE)
    with pytest.raises(ProtocolError):
        next(records)


def test_writer_rejects_an_event_outside_the_requested_set_without_writing_it(tmp_path):
    path = tmp_path / "n.jsonl"
    with JsonlRecorder(path, NATIVE, "game_api", native_oracle_kinds=ROOM) as recorder:
        recorder.record(item("room_cleared", 1))
        with pytest.raises(ProtocolError):
            recorder.record(item("player_died", 2))
    assert [r.event_id for r in open_replay(path, NATIVE)[1]] == [1]


def test_replay_rejects_an_event_outside_the_manifest_set_before_yielding_it(tmp_path):
    manifest = {**HEAD, "native_oracle_kinds": ["room_cleared"]}
    leading = handwritten(tmp_path / "a.jsonl", manifest, item("player_died", 1))
    _, records = open_replay(leading, NATIVE)
    with pytest.raises(ProtocolError):
        next(records)
    later = handwritten(
        tmp_path / "b.jsonl", manifest, item("room_cleared", 1), item("player_died", 2)
    )
    _, records = open_replay(later, NATIVE)
    assert next(records).event_id == 1
    with pytest.raises(ProtocolError):
        next(records)


def test_legacy_native_manifest_without_metadata_is_unknown_not_empty(tmp_path):
    path = handwritten(tmp_path / "l.jsonl", HEAD, item("room_cleared", 1), item("player_died", 2))
    manifest, records = open_replay(path, NATIVE)
    assert manifest.native_oracle_kinds is None
    assert [r.event.kind for r in records] == ["room_cleared", "player_died"]
    assert (
        open_replay(handwritten(tmp_path / "e.jsonl", HEAD), NATIVE)[0].native_oracle_kinds is None
    )


@pytest.mark.parametrize(
    "kinds",
    [
        None,
        "room_cleared",
        {"room_cleared": 1},
        ["nope"],
        [1],
        [True],
        [None],
        [["room_cleared"]],
        ["room_cleared", "room_cleared"],
        ["Room_Cleared"],
    ],
)
def test_malformed_replay_metadata_is_rejected_for_a_native_stream(tmp_path, kinds):
    path = handwritten(tmp_path / "m.jsonl", {**HEAD, "native_oracle_kinds": kinds})
    with pytest.raises(ProtocolError):
        open_replay(path, NATIVE)


@pytest.mark.parametrize("stream", ["policy_frames", "oracle_events"])
@pytest.mark.parametrize("kinds", [None, [], ["room_cleared"]])
def test_non_native_manifests_reject_native_kind_metadata(tmp_path, stream, kinds):
    path = handwritten(
        tmp_path / "x.jsonl", {**HEAD, "stream": stream, "native_oracle_kinds": kinds}
    )
    with pytest.raises(ProtocolError):
        open_replay(path, stream)


@pytest.mark.parametrize(
    "kinds",
    [
        ["room_cleared"],
        ("nope",),
        (1,),
        (True,),
        ("room_cleared", "room_cleared"),
        ("room_cleared", None),
    ],
)
def test_writer_rejects_malformed_kinds_and_leaves_no_file(tmp_path, kinds):
    path = tmp_path / "n.jsonl"
    with pytest.raises(ProtocolError):
        JsonlRecorder(path, NATIVE, "game_api", native_oracle_kinds=kinds)
    assert not path.exists()


def test_new_native_recording_needs_an_explicit_kind_tuple(tmp_path):
    path = tmp_path / "n.jsonl"
    with pytest.raises(ProtocolError):
        JsonlRecorder(path, NATIVE, "game_api")
    assert not path.exists()


@pytest.mark.parametrize("stream", ["policy_frames", "oracle_events"])
@pytest.mark.parametrize("kinds", [(), ROOM])
def test_writer_rejects_native_kinds_for_non_native_streams(tmp_path, stream, kinds):
    path = tmp_path / "x.jsonl"
    with pytest.raises(ProtocolError):
        JsonlRecorder(path, stream, "synthetic", native_oracle_kinds=kinds)
    assert not path.exists()


@pytest.mark.parametrize("stream", ["policy_frames", "oracle_events"])
def test_non_native_manifest_bytes_and_replay_are_unchanged(tmp_path, stream):
    path = tmp_path / "x.jsonl"
    with JsonlRecorder(path, stream, "synthetic") as recorder:
        recorder.record(frame(provenance="synthetic") if stream == "policy_frames" else event())
    first = path.read_bytes().split(b"\n")[0]
    assert first == line({**HEAD, "stream": stream, "provenance": "synthetic"})
    manifest, records = open_replay(path, stream)
    assert manifest.native_oracle_kinds is None
    assert len(list(records)) == 1
