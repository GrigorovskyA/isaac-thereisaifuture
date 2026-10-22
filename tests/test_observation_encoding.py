"""OFFLINE contract tests with synthetic frames. No real-game fixtures exist yet."""

import json
import random

import numpy as np
import pytest
from pydantic import ValidationError
from synthetic import enemy, event, frame

from isaac_threrisaifuture.encoding import (
    CAPACITY,
    ENEMY_OFFSET,
    OBSERVATION_SIZE,
    PLAYER_FEATURES,
    SLOT_FEATURES,
    encode,
)
from isaac_threrisaifuture.entities import Entity, EntityFrame, Vec
from isaac_threrisaifuture.observation import ProtocolError, decode
from isaac_threrisaifuture.recording import JsonlRecorder, open_replay


def first_enemy_slot(vector: np.ndarray) -> np.ndarray:
    return vector[ENEMY_OFFSET : ENEMY_OFFSET + SLOT_FEATURES]


def test_shape_is_constant_and_overflow_is_counted():
    sizes = {encode(frame([enemy(i, i, 0) for i in range(n)])).vector.shape for n in (0, 3, 20)}
    assert sizes == {(OBSERVATION_SIZE,)}
    overflowing = encode(frame([enemy(i, i, 0) for i in range(20)]))
    assert overflowing.overflow == {"enemy": 20 - CAPACITY["enemy"]}


def test_nearest_enemies_survive_overflow():
    far_first = [enemy(i, 900 - i, 0) for i in range(20)]
    encoded = encode(frame(far_first))
    assert first_enemy_slot(encoded.vector)[1] == pytest.approx((900 - 19) / 1000)


def test_object_at_origin_differs_from_no_object():
    empty = first_enemy_slot(encode(frame()).vector)
    at_origin = first_enemy_slot(encode(frame([enemy(1, 0, 0)])).vector)
    assert empty[0] == 0.0 and at_origin[0] == 1.0
    assert not np.array_equal(empty, at_origin)


def test_unknown_hp_has_invalid_bit_not_zero_hp():
    unknown = first_enemy_slot(encode(frame([enemy(1, 5, 5, hp=None)])).vector)
    zero_hp = first_enemy_slot(encode(frame([enemy(1, 5, 5, hp=0.0)])).vector)
    assert unknown[6] == 0.0 and zero_hp[6] == 1.0


def test_input_order_does_not_change_output():
    entities = [enemy(i, random.Random(i).uniform(-300, 300), i * 7) for i in range(12)]
    shuffled = entities[:]
    random.Random(5).shuffle(shuffled)
    assert np.array_equal(encode(frame(entities)).vector, encode(frame(shuffled)).vector)


def test_out_of_range_values_are_clipped_and_counted():
    encoded = encode(frame([enemy(1, 50_000, 0)]))
    assert encoded.clipped_values == 1
    assert first_enemy_slot(encoded.vector)[1] == 1.0


def test_hp_must_be_known_together():
    with pytest.raises(ValidationError):
        Entity(kind="enemy", entity_id=1, spawn_generation=0, position=Vec(x=0, y=0), hp=3.0)


def test_duplicate_identity_rejected():
    with pytest.raises(ValidationError):
        frame([enemy(1, 0, 0), enemy(1, 5, 5)])


def test_same_id_with_new_spawn_generation_is_distinct():
    assert len(frame([enemy(1, 0, 0), enemy(1, 5, 5, generation=1)]).entities) == 2


def test_oracle_fields_cannot_enter_a_policy_frame():
    payload = json.loads(frame().model_dump_json())
    payload["hidden_secret_room"] = {"x": 1, "y": 2}
    with pytest.raises(ProtocolError):
        decode(json.dumps(payload).encode(), EntityFrame, 65536)


def test_encoder_rejects_oracle_events():
    with pytest.raises(ProtocolError):
        encode(event())  # type: ignore[arg-type]


def test_event_payload_rules():
    with pytest.raises(ValidationError):
        event("enemy_damaged", amount=1.0)
    with pytest.raises(ValidationError):
        event("player_damaged", amount=1.0)
    assert event("enemy_killed", entity_id=1, spawn_generation=0).kind == "enemy_killed"


def test_record_replay_round_trip(tmp_path):
    frames = [frame([enemy(1, i, 0)], frame_id=i + 1) for i in range(5)]
    path = tmp_path / "frames.jsonl"
    with JsonlRecorder(path, "policy_frames", "synthetic") as recorder:
        for item in frames:
            recorder.record(item)
    manifest, replayed = open_replay(path, "policy_frames")
    assert manifest.observation_schema_version == 4
    for live, again in zip(frames, replayed, strict=True):
        assert np.array_equal(encode(live).vector, encode(again).vector)  # type: ignore[arg-type]


def test_streams_do_not_mix(tmp_path):
    with JsonlRecorder(tmp_path / "frames.jsonl", "policy_frames", "synthetic") as recorder:
        with pytest.raises(ProtocolError):
            recorder.record(event())
    with JsonlRecorder(tmp_path / "events.jsonl", "oracle_events", "synthetic") as recorder:
        recorder.record(event())
    with pytest.raises(ProtocolError):
        open_replay(tmp_path / "events.jsonl", "policy_frames")


def test_incompatible_version_rejected_before_any_record(tmp_path):
    path = tmp_path / "old.jsonl"
    manifest = {
        "type": "recording_manifest",
        "observation_schema_version": 2,
        "stream": "policy_frames",
        "provenance": "synthetic",
    }
    path.write_bytes((json.dumps(manifest) + "\n" + frame().model_dump_json() + "\n").encode())
    with pytest.raises(ProtocolError, match="Unsupported"):
        open_replay(path, "policy_frames")


def test_recorder_refuses_to_overwrite(tmp_path):
    path = tmp_path / "frames.jsonl"
    JsonlRecorder(path, "policy_frames", "synthetic").close()
    with pytest.raises(FileExistsError):
        JsonlRecorder(path, "policy_frames", "synthetic")


def test_entity_offsets_are_already_player_relative():
    # The player is at room (300, 200); offsets are NOT room coordinates.
    encoded = encode(frame([enemy(1, 301, 200), enemy(2, 1, 0)]))
    assert first_enemy_slot(encoded.vector)[1] == pytest.approx(1 / 1000)
    translated = encode(
        frame([enemy(1, 301, 200), enemy(2, 1, 0)], player_position=Vec(x=600, y=400))
    )
    assert np.array_equal(encoded.vector[PLAYER_FEATURES:], translated.vector[PLAYER_FEATURES:])


def test_replay_rejects_oversized_lines_and_blank_records(tmp_path):
    path = tmp_path / "frames.jsonl"
    with JsonlRecorder(path, "policy_frames", "synthetic") as recorder:
        recorder.record(frame())
    original = path.read_bytes()
    path.write_bytes(original + b" " * 100_000 + b"\n")
    _, records = open_replay(path, "policy_frames")
    next(records)
    with pytest.raises(ProtocolError, match="size limit"):
        next(records)
    path.write_bytes(original + b"\n" + original.splitlines(keepends=True)[1])
    _, records = open_replay(path, "policy_frames")
    next(records)
    with pytest.raises(ProtocolError, match="Empty"):
        next(records)
