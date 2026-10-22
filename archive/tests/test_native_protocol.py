"""Offline contract tests for native step models. All peers and data here are simulated."""

import json

import pytest
from pydantic import ValidationError
from synthetic import SESSION, frame

from isaac_threrisaifuture.actions import Command, CommandAck
from isaac_threrisaifuture.native_protocol import (
    StepCommand,
    StepCompletion,
    validate_completion,
    validate_event_barrier,
)
from isaac_threrisaifuture.observation import MAX_MESSAGE_BYTES, ProtocolError, decode

BAD = (ValidationError, ProtocolError)


def command(**changes):
    values = dict(
        session_id=SESSION, sequence=1, game_epoch=1, room_visit=1, frame_id=100, frames=6
    )
    values.update(changes)
    return StepCommand(**values)


def ack(**changes):
    values = dict(
        type="command_ack",
        protocol_version=1,
        session_id=SESSION,
        sequence=1,
        game_epoch=1,
        room_visit=1,
        frame_id=101,
        kind="action",
        status="accepted",
    )
    values.update(changes)
    return CommandAck(**values)


def completion(
    status="completed", reason="interval_elapsed", elapsed=6, accepted=101, requested=6, **changes
):
    values = dict(
        session_id=SESSION,
        sequence=1,
        game_epoch=1,
        room_visit=1,
        accepted_frame=accepted,
        requested_updates=requested,
        elapsed_updates=elapsed,
        status=status,
        reason=reason,
        frame=frame(frame_id=accepted + elapsed, provenance="game_api"),
        last_event_id=0,
    )
    values.update(changes)
    return StepCompletion(**values)


def test_exact_interval_is_a_valid_receipt():
    result = completion()
    validate_completion(command(), ack(), result)
    assert decode(result.model_dump_json().encode(), StepCompletion) == result


def test_acknowledgement_alone_is_not_completion():
    with pytest.raises(BAD):
        completion(elapsed=0)  # completed needs the full requested interval


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("expired", "wall_deadline"),
        ("cancelled", "pause"),
        ("cancelled", "transition"),
        ("cancelled", "input_fault"),
        ("cancelled", "explicit_release"),
    ],
)
def test_expired_and_cancelled_receipts_are_valid_failure_facts(status, reason):
    result = completion(status=status, reason=reason, elapsed=2)
    validate_completion(command(), ack(), result)
    assert result.status != "completed"


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("completed", "wall_deadline"),
        ("completed", "pause"),
        ("expired", "interval_elapsed"),
        ("expired", "pause"),
        ("cancelled", "wall_deadline"),
        ("cancelled", "interval_elapsed"),
    ],
)
def test_inconsistent_status_and_reason_are_rejected(status, reason):
    with pytest.raises(BAD):
        completion(status=status, reason=reason, elapsed=6)


def test_late_frame_cannot_be_a_false_completion():
    with pytest.raises(BAD):
        completion(elapsed=9)  # completed, but far later than the requested six updates


def test_elapsed_must_equal_frame_delta():
    with pytest.raises(BAD):
        completion(elapsed=6, frame=frame(frame_id=110, provenance="game_api"))


def test_frame_before_acceptance_is_rejected():
    with pytest.raises(BAD):
        completion(
            status="cancelled",
            reason="pause",
            elapsed=0,
            frame=frame(frame_id=100, provenance="game_api"),
        )


@pytest.mark.parametrize("value", [-1, True, 2**53, 1.0, "1"])
def test_counters_must_be_bounded_integers(value):
    with pytest.raises(BAD):
        command(frame_id=value)
    with pytest.raises(BAD):
        completion(game_epoch=value)


@pytest.mark.parametrize("value", [0, 16, True])
def test_step_frames_are_one_to_fifteen(value):
    with pytest.raises(BAD):
        command(frames=value)
    with pytest.raises(BAD):
        completion(requested=value)


@pytest.mark.parametrize("value", [0, 2, True, "1"])
def test_versions_must_be_exactly_one(value):
    with pytest.raises(BAD):
        command(protocol_version=value)
    with pytest.raises(BAD):
        completion(protocol_version=value)


def test_unknown_fields_and_bad_json_are_rejected():
    raw = json.loads(completion().model_dump_json())
    raw["extra"] = 1
    with pytest.raises(ProtocolError):
        decode(json.dumps(raw).encode(), StepCompletion)
    with pytest.raises(ProtocolError):
        decode(b"{not json}", StepCompletion)


def test_sequence_starts_at_one():
    with pytest.raises(BAD):
        command(sequence=0)
    with pytest.raises(BAD):
        completion(sequence=0)


@pytest.mark.parametrize(
    "bad",
    [
        {"session_id": "b" * 32},
        {"game_epoch": 2},
        {"room_visit": 2},
    ],
)
def test_nested_frame_identity_must_match(bad):
    with pytest.raises(BAD):
        completion(frame=frame(frame_id=107, provenance="game_api", **bad))


def test_synthetic_frame_is_not_accepted_as_native_receipt():
    with pytest.raises(BAD):
        completion(frame=frame(frame_id=107, provenance="synthetic"))


@pytest.mark.parametrize(
    "bad",
    [
        {"session_id": "b" * 32},
        {"sequence": 2},
        {"game_epoch": 2},
        {"room_visit": 2},
    ],
)
def test_cross_message_identity_mismatch_is_rejected(bad):
    with pytest.raises(ProtocolError):
        validate_completion(command(), ack(**bad), completion())
    with pytest.raises(ProtocolError):
        validate_completion(command(), ack(), completion(**bad))


def test_repeat_and_accepted_frame_must_match():
    with pytest.raises(ProtocolError):
        validate_completion(command(frames=5), ack(), completion())
    with pytest.raises(ProtocolError):
        validate_completion(command(), ack(frame_id=102), completion())


@pytest.mark.parametrize(
    "foreign",
    [{"session_id": "b" * 32}, {"game_epoch": 2}, {"room_visit": 2}],
)
def test_internally_consistent_foreign_result_is_rejected_by_validate_completion(foreign):
    nested = frame(frame_id=107, provenance="game_api", **foreign)
    result = completion(frame=nested, **foreign)  # valid on its own, wrong for this command
    with pytest.raises(ProtocolError):
        validate_completion(command(), ack(), result)


@pytest.mark.parametrize("value", [0, 1, 7, 2**53 - 1])
def test_watermark_round_trips_including_zero_and_maximum(value):
    result = completion(last_event_id=value)
    assert result.last_event_id == value
    decoded = decode(result.model_dump_json().encode(), StepCompletion)
    assert decoded == result


def test_receipt_without_watermark_is_rejected():
    raw = json.loads(completion().model_dump_json())
    del raw["last_event_id"]
    with pytest.raises(ProtocolError):
        decode(json.dumps(raw).encode(), StepCompletion)
    with pytest.raises(BAD):
        StepCompletion(**{k: v for k, v in dict(completion()).items() if k != "last_event_id"})


@pytest.mark.parametrize("value", [-1, True, 2**53, 1.0, "1", None])
def test_watermark_must_be_a_bounded_strict_integer(value):
    with pytest.raises(BAD):
        completion(last_event_id=value)


@pytest.mark.parametrize("seen", [0, 5, 2**53 - 1])
def test_matching_barrier_is_accepted(seen):
    validate_event_barrier(completion(last_event_id=seen), seen)


@pytest.mark.parametrize(("watermark", "seen"), [(5, 4), (5, 0), (0, 1), (5, 6)])
def test_missing_tail_or_cursor_ahead_is_rejected(watermark, seen):
    with pytest.raises(ProtocolError):
        validate_event_barrier(completion(last_event_id=watermark), seen)


@pytest.mark.parametrize("seen", [-1, True, False, 2**53, 1.0, "0", None])
def test_malformed_observed_counter_is_rejected(seen):
    with pytest.raises(ProtocolError):
        validate_event_barrier(completion(last_event_id=0), seen)


@pytest.mark.parametrize(
    ("ack_frame", "valid"), [(99, False), (100, True), (115, True), (116, False)]
)
def test_acknowledgement_freshness_window(ack_frame, valid):
    result = completion(accepted=ack_frame, elapsed=6)
    if valid:
        validate_completion(command(), ack(frame_id=ack_frame), result)
    else:
        with pytest.raises(ProtocolError):
            validate_completion(command(), ack(frame_id=ack_frame), result)


def test_legacy_command_rejects_step_command_and_keeps_field_order():
    wire = command().wire_bytes()
    assert wire.startswith(b'{"type":"step_command","protocol_version":1,"session_id"')
    with pytest.raises(ProtocolError):
        decode(wire.rstrip(b"\n"), Command)
    legacy = json.loads(Command(**{**json.loads(wire), "type": "command"}).model_dump_json())
    assert list(legacy) == list(json.loads(wire))


def test_step_command_is_action_only():
    with pytest.raises(BAD):
        command(kind="heartbeat")


def test_oversized_record_is_rejected_by_bounded_decode():
    raw = completion().model_dump_json().encode()
    padded = raw[:-1] + b',"x":"' + b"a" * MAX_MESSAGE_BYTES + b'"}'
    with pytest.raises(ProtocolError):
        decode(padded, StepCompletion)
