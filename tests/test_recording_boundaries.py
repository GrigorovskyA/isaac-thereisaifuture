"""Adversarial recording/replay boundaries. Synthetic data only; no game involved."""

from pathlib import Path

import pytest
from synthetic import frame

from isaac_threrisaifuture.entities import MAX_FRAME_BYTES
from isaac_threrisaifuture.observation import ProtocolError
from isaac_threrisaifuture.recording import JsonlRecorder, open_replay


def _write(path: Path, count: int = 1) -> list[bytes]:
    with JsonlRecorder(path, "policy_frames", "synthetic") as recorder:
        for index in range(count):
            recorder.record(frame(frame_id=index + 1))
    return path.read_bytes().splitlines()


def _padded(line: bytes, size: int) -> bytes:
    assert len(line) <= size
    return line + b" " * (size - len(line))  # trailing whitespace is legal JSON


def _join(lines: list[bytes]) -> bytes:
    return b"".join(line + b"\n" for line in lines)


def test_data_record_at_limit_is_accepted_and_one_byte_more_is_rejected(tmp_path):
    lines = _write(tmp_path / "base.jsonl")
    manifest, record = lines

    at_limit = tmp_path / "at_limit.jsonl"
    at_limit.write_bytes(_join([manifest, _padded(record, MAX_FRAME_BYTES)]))
    _, records = open_replay(at_limit, "policy_frames")
    assert next(records).frame_id == 1  # type: ignore[union-attr]
    assert list(records) == []

    over = tmp_path / "over.jsonl"
    over.write_bytes(_join([manifest, _padded(record, MAX_FRAME_BYTES + 1)]))
    _, records = open_replay(over, "policy_frames")
    with pytest.raises(ProtocolError, match="size limit"):
        next(records)


def test_manifest_at_limit_is_accepted_and_one_byte_more_is_rejected(tmp_path):
    manifest, record = _write(tmp_path / "base.jsonl")

    at_limit = tmp_path / "at_limit.jsonl"
    at_limit.write_bytes(_join([_padded(manifest, MAX_FRAME_BYTES), record]))
    parsed, records = open_replay(at_limit, "policy_frames")
    assert parsed.stream == "policy_frames"
    assert next(records).frame_id == 1  # type: ignore[union-attr]

    over = tmp_path / "over.jsonl"
    over.write_bytes(_join([_padded(manifest, MAX_FRAME_BYTES + 1), record]))
    with pytest.raises(ProtocolError, match="size limit"):
        open_replay(over, "policy_frames")


def test_provenance_change_fails_before_yielding_that_record(tmp_path):
    path = tmp_path / "frames.jsonl"
    lines = _write(path, count=2)
    foreign = frame(frame_id=3, provenance="game_api").model_dump_json().encode()
    path.write_bytes(_join([*lines, foreign]))

    _, records = open_replay(path, "policy_frames")
    assert [next(records).frame_id, next(records).frame_id] == [1, 2]  # type: ignore[union-attr]
    with pytest.raises(ProtocolError, match="provenance"):
        next(records)


@pytest.mark.parametrize("trailing_newline", [True, False])
def test_malformed_final_record_is_an_error_not_eof(tmp_path, trailing_newline):
    path = tmp_path / "frames.jsonl"
    lines = _write(path, count=3)
    truncated = lines[-1][:-10]  # cut mid-record, as after a crash during a write
    body = _join(lines[:-1]) + truncated + (b"\n" if trailing_newline else b"")
    path.write_bytes(body)

    _, records = open_replay(path, "policy_frames")
    assert [next(records).frame_id, next(records).frame_id] == [1, 2]  # type: ignore[union-attr]
    with pytest.raises(ProtocolError):
        next(records)
