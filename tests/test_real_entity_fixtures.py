"""Replay actual J460 observations; tests do not start or communicate with Isaac."""

import json
from pathlib import Path

import numpy as np
import pytest

from isaac_threrisaifuture.encoding import OBSERVATION_SIZE, encode
from isaac_threrisaifuture.entities import EntityFrame
from isaac_threrisaifuture.recording import open_replay

FIXTURES = Path(__file__).parent / "fixtures/entities"
NEUTRAL_FACTS = {
    "inventory": {
        "coins": 0,
        "bombs": 0,
        "keys": 0,
        "active_item": 0,
        "active_charge": 0,
        "active_max_charge": 0,
        "card": 0,
        "pill": 0,
        "trinket": 0,
    },
    "collectibles": [],
    "collectible_overflow": 0,
    "room": {"type": 1, "stage": 1, "stage_type": 0, "clear": False, "doors": [False] * 8},
}


def upgraded(name: str, tmp_path: Path) -> Path:
    """Copy a recorded schema 1 fixture to schema 3 with neutral, clearly invented facts.

    Only the real positions, velocities and identities are replayed; the added inventory,
    room and pickup fields are placeholders (pickups become 'other' variant 999, free).
    """
    lines = (FIXTURES / name).read_text("utf-8").splitlines()
    out = []
    for line in lines:
        record = json.loads(line)
        record["observation_schema_version"] = 3
        if record["type"] == "entity_frame":
            record.update(NEUTRAL_FACTS)
            for entity in record["entities"]:
                is_pickup = entity["kind"] == "pickup"
                entity.update(
                    variant=999 if is_pickup else None,
                    subtype=0 if is_pickup else None,
                    price=0 if is_pickup else None,
                )
        out.append(json.dumps(record, separators=(",", ":")))
    path = tmp_path / name
    path.write_text("\n".join(out) + "\n", "utf-8", newline="\n")
    return path


@pytest.mark.parametrize("name", ["j460-obstacles-v1.jsonl", "j460-gameplay-v1.jsonl"])
def test_real_j460_recording_replays_with_finite_policy_vectors(name, tmp_path):
    path = upgraded(name, tmp_path)
    manifest, records = open_replay(path, "policy_frames")
    assert manifest.provenance == "game_api"
    frames = list(records)
    assert len(frames) >= 3
    for frame in frames:
        assert isinstance(frame, EntityFrame)
        encoded = encode(frame)
        assert encoded.vector.shape == (OBSERVATION_SIZE,)
        assert encoded.vector.dtype == np.float32
        assert np.isfinite(encoded.vector).all()
        assert np.all(np.abs(encoded.vector) <= 1.0)
        assert all(entity.hp is None and entity.max_hp is None for entity in frame.entities)
    _, again = open_replay(path, "policy_frames")
    for original, replayed in zip(frames, again, strict=True):
        assert isinstance(replayed, EntityFrame)
        assert np.array_equal(encode(original).vector, encode(replayed).vector)


def test_gameplay_fixture_contains_each_real_kind_and_room_transition(tmp_path):
    _, records = open_replay(upgraded("j460-gameplay-v1.jsonl", tmp_path), "policy_frames")
    frames = list(records)
    assert all(isinstance(frame, EntityFrame) for frame in frames)
    assert {entity.kind for frame in frames for entity in frame.entities} == {
        "enemy",
        "projectile",
        "obstacle",
        "pickup",
    }
    assert len({frame.room_visit for frame in frames}) > 1
    assert any(encode(frame).overflow.get("obstacle", 0) > 0 for frame in frames)
