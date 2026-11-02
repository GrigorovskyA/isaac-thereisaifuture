"""Synthetic demo recordings: wire snapshots with human input, and the files that hold them."""

import gzip
import json
from pathlib import Path
from typing import Any

from synthetic import enemy, frame, oracle_metrics
from test_observer import snapshot

from isaac_threrisaifuture.entities import Vec
from isaac_threrisaifuture.live_wire import HUMAN_INPUT_BITS, DemoSnapshot

SESSION = "d" * 32
BIT = {name: 1 << index for index, name in enumerate(HUMAN_INPUT_BITS)}


def demo_raw(
    sequence: int,
    frame_id: int | None,
    *,
    epoch: int = 1,
    status: str = "active",
    x: float = 120.0,
    y: float = 200.0,
    velocity: tuple[float, float] = (0.0, 0.0),
    enemies: tuple[tuple[int, float], ...] = (),
    clear: bool = False,
    dead: bool = False,
    room_index: int = 84,
    visit: int = 1,
    masks: tuple[int, ...] = (),
    dropped: int = 0,
) -> dict[str, Any]:
    """Wire JSON of one DemoSnapshot (`status="unavailable"` drops every game field)."""
    human_input = {"masks": list(masks), "dropped": dropped}
    if status == "unavailable":
        raw = snapshot(
            SESSION, sequence, game_epoch=epoch, frame_id=None, status="unavailable",
            reason="not_in_game", room=None, player=None,
        )  # fmt: skip
        return {**raw, "entity_frame": None, "oracle": None, "human_input": human_input}
    assert frame_id is not None
    raw = snapshot(
        SESSION, sequence, game_epoch=epoch, frame_id=frame_id, update_id=frame_id,
        status=status, room={"visit_id": visit},
    )  # fmt: skip
    raw["player"]["position"] = {"x": x, "y": y}
    inner = frame(
        [enemy(entity_id, 300.0, 150.0, hp=hp) for entity_id, hp in enemies if hp > 0],
        session_id=SESSION,
        game_epoch=epoch,
        room_visit=visit,
        frame_id=frame_id,
        provenance="game_api",
        player_position=Vec(x=x, y=y),
        player_velocity=Vec(x=velocity[0], y=velocity[1]),
        health=raw["player"]["health"],
    ).model_dump(mode="json")
    raw["entity_frame"] = inner
    raw["oracle"] = {
        "room_clear": clear,
        "player_dead": dead,
        "enemies": [{"entity_id": i, "hp": hp, "max_hp": 10.0} for i, hp in enemies if hp > 0],
        "enemy_overflow": 0,
        "room_index": room_index,
        **oracle_metrics(),
    }
    raw["human_input"] = human_input
    return raw


def parse(raw: dict[str, Any]) -> DemoSnapshot:
    return DemoSnapshot.model_validate_json(json.dumps(raw))


def write_recording(
    path: Path, records: list[tuple[float, dict[str, Any]]], *, cut: int | None = None
) -> Path:
    """Gzip JSON lines: the manifest, then one record per snapshot; `cut` drops trailing bytes."""
    lines = [json.dumps({"type": "demo_manifest", "format": 1, "session_id": SESSION})]
    lines += [json.dumps({"t": t, "snapshot": raw}) for t, raw in records]
    data = gzip.compress(("\n".join(lines) + "\n").encode())
    path.write_bytes(data if cut is None else data[:-cut])
    return path
