"""OFFLINE demo recorder: client opt-in, file layout, round trip and truncated files."""

import gzip
import json
import socket
from datetime import UTC, datetime

import pytest
from synthetic import oracle_metrics
from test_entity_transport import entity_snapshot
from test_observer import ack, record

from isaac_threrisaifuture import demo_recorder
from isaac_threrisaifuture.demo_recorder import DemoWriter, read_recording, record_session
from isaac_threrisaifuture.entities import OBSERVATION_SCHEMA_VERSION
from isaac_threrisaifuture.live_wire import DEMO_RECORD_CAPABILITY, DemoSnapshot
from isaac_threrisaifuture.observation import HelloAck
from isaac_threrisaifuture.observer_client import ObservationClient, ObserverConfig

pytest_plugins = ["test_observer"]
SESSION = "c" * 32


def demo_raw(session, sequence, *, masks=(1, 2), dropped=0, status="active"):
    raw = entity_snapshot(session, sequence)
    raw["sequence"] = sequence
    raw["update_id"] = 10 + sequence
    raw["frame_id"] = raw["entity_frame"]["frame_id"] = 10 + sequence
    raw["status"] = status
    raw["oracle"] = {
        "room_clear": False,
        "player_dead": False,
        "enemies": [{"entity_id": 1, "hp": 5.0, "max_hp": 10.0}],
        "enemy_overflow": 0,
        "room_index": 84,
        **oracle_metrics(),
    }
    raw["human_input"] = {"masks": list(masks), "dropped": dropped}
    return raw


def demo_ack(session=SESSION):
    value = ack(session)
    value["capabilities"] += ["entity_observation_v1", DEMO_RECORD_CAPABILITY]
    return value


def hello_ack(session=SESSION):
    return HelloAck.model_validate(demo_ack(session))


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(demo_record=True),
        dict(demo_record=True, entity_observations=True, safe_actions=True),
        dict(demo_record=True, entity_observations=True, restart_after_death=True),
        dict(demo_record=True, live_loop=True),
        dict(demo_record=True, live_loop=True, seeded_restart=True),
        dict(demo_record=True, native_episode_steps=True),
        dict(demo_record=True, entity_observations=True, native_episode_steps=True),
        dict(demo_record=1, entity_observations=True),
    ],
)
def test_demo_config_requires_entity_mode_and_nothing_else(kwargs):
    with pytest.raises(ValueError):
        ObserverConfig(**kwargs)


def test_client_negotiates_and_decodes_demo_snapshots(peers):
    def send(conn, session):
        conn.sendall(record(demo_ack(session)) + record(demo_raw(session, 1)))

    config = ObserverConfig(port=0, entity_observations=True, demo_record=True)
    with ObservationClient(config) as client:
        peers(client.address, send)
        client.accept()
        snap = client.receive()
    assert isinstance(snap, DemoSnapshot) and snap.human_input.masks == [1, 2]


def test_client_requires_the_capability_and_rejects_snapshots_without_input(peers):
    def plain_ack(conn, session):
        value = ack(session)
        value["capabilities"].append("entity_observation_v1")
        conn.sendall(record(value))

    def no_input(conn, session):
        raw = demo_raw(session, 1)
        del raw["human_input"]
        conn.sendall(record(demo_ack(session)) + record(raw))

    config = ObserverConfig(port=0, entity_observations=True, demo_record=True)
    with ObservationClient(config) as client:
        peers(client.address, plain_ack)
        with pytest.raises(Exception, match="capabilities"):
            client.accept()
        peers(client.address, no_input)
        client.accept()
        with pytest.raises(Exception, match="DemoSnapshot"):
            client.receive()


def test_session_file_has_manifest_and_round_trips(peers, tmp_path):
    def send(conn, session):
        conn.sendall(
            record(demo_ack(session))
            + record(demo_raw(session, 1, status="paused", masks=()))
            + record(demo_raw(session, 2, masks=[3] * 16, dropped=14))
            + record(demo_raw(session, 3))
        )

    lines = []
    config = ObserverConfig(port=0, entity_observations=True, demo_record=True)
    with ObservationClient(config) as client:
        peers(client.address, send)
        ack_value = client.accept()
        writer = record_session(client, ack_value, tmp_path, log=lines.append)
    assert writer.path.parent == tmp_path
    assert writer.path.name.endswith(f"-{ack_value.session_id[:8]}.jsonl.gz")
    assert len(writer.path.name) == len("20260101-000000-") + 8 + len(".jsonl.gz")
    assert writer.snapshots == 3 and writer.active_snapshots == 2
    assert writer.input_updates == 32 and writer.play_minutes == pytest.approx(32 / 30 / 60)
    assert any(line.startswith("Closed ") for line in lines)

    manifest, records = read_recording(writer.path)
    assert manifest["type"] == "demo_manifest" and manifest["format"] == 1
    assert manifest["mod_version"] == "offline-test"
    assert DEMO_RECORD_CAPABILITY in manifest["capabilities"]
    assert manifest["observation_schema_version"] == OBSERVATION_SCHEMA_VERSION
    assert datetime.fromisoformat(manifest["created_at"]).tzinfo is not None
    pairs = list(records)
    assert [s.sequence for _, s in pairs] == [1, 2, 3]
    assert all(isinstance(t, float) for t, _ in pairs)
    assert [t for t, _ in pairs] == sorted(t for t, _ in pairs)
    expected = DemoSnapshot.model_validate_json(json.dumps(demo_raw(ack_value.session_id, 2)))
    assert pairs[1][1].oracle == expected.oracle
    assert pairs[1][1].human_input.masks == [3] * 16 and pairs[1][1].human_input.dropped == 14

    # Each stored snapshot is the JSON dump of the model and re-reads with the wire model.
    with gzip.open(writer.path, "rt") as stream:
        stored = [json.loads(line) for line in stream][1:]
    for (_, snap), line in zip(pairs, stored, strict=True):
        assert DemoSnapshot.model_validate_json(json.dumps(line["snapshot"])) == snap


def test_menu_only_session_leaves_no_file(peers, tmp_path):
    def send(conn, session):
        raw = demo_raw(session, 1, masks=())
        raw.update(status="unavailable", reason="not_in_game", frame_id=None, room=None)
        raw.update(player=None, entity_frame=None, oracle=None)
        conn.sendall(record(demo_ack(session)) + record(raw))

    config = ObserverConfig(port=0, entity_observations=True, demo_record=True)
    with ObservationClient(config) as client:
        peers(client.address, send)
        writer = record_session(client, client.accept(), tmp_path, log=lambda _: None)
    assert writer.snapshots == 1 and not writer.path.exists()


def write_file(tmp_path, count=50):
    snaps = [
        DemoSnapshot.model_validate_json(json.dumps(demo_raw(SESSION, i))) for i in range(1, count)
    ]
    clock = iter(float(i) for i in range(1000))
    writer = DemoWriter(
        tmp_path,
        hello_ack(),
        created=datetime(2026, 11, 2, 9, 5, 7, tzinfo=UTC),
        clock=lambda: next(clock),
    )
    for i, snap in enumerate(snaps):
        writer.write(0.5 * i, snap)
    writer.close()
    return writer, snaps


def test_writer_names_files_by_utc_time_and_session(tmp_path):
    writer, snaps = write_file(tmp_path)
    assert writer.path == tmp_path / f"20261102-090507-{SESSION[:8]}.jsonl.gz"
    manifest, records = read_recording(writer.path)
    assert manifest["created_at"] == "2026-11-02T09:05:07+00:00"
    assert [s for _, s in records] == snaps


@pytest.mark.parametrize("keep", [0.95, 0.6, 0.3])
def test_truncated_gzip_tail_is_tolerated(tmp_path, keep):
    writer, snaps = write_file(tmp_path)
    data = writer.path.read_bytes()
    cut = tmp_path / "cut.jsonl.gz"
    cut.write_bytes(data[: int(len(data) * keep)])
    _, records = read_recording(cut)
    read = [s for _, s in records]
    assert read == snaps[: len(read)]
    assert len(read) < len(snaps)


def test_flushed_data_survives_a_crash_and_corrupt_tail(tmp_path):
    clock = iter(float(i) for i in range(1000))
    writer = DemoWriter(tmp_path, hello_ack(), clock=lambda: next(clock) * 2)  # 2 s per write
    snaps = [DemoSnapshot.model_validate_json(json.dumps(demo_raw(SESSION, i))) for i in (1, 2)]
    for snap in snaps:
        writer.write(1.0, snap)
    # No close (a crash): the second write flushed, the file is cut and has junk appended.
    crashed = writer.path.read_bytes() + b"\x00garbage"
    writer.close()
    writer.path.write_bytes(crashed)
    _, records = read_recording(writer.path)
    assert [s for _, s in records] == snaps


def test_invalid_complete_record_or_missing_manifest_raises(tmp_path):
    path = tmp_path / "bad.jsonl.gz"
    with gzip.open(path, "wb") as stream:
        stream.write(b'{"type":"demo_manifest","format":1}\n{"t":1.0,"snapshot":{}}\n')
    _, records = read_recording(path)
    with pytest.raises(ValueError, match=":2:"):
        list(records)
    with gzip.open(path, "wb") as stream:
        stream.write(b'{"type":"other"}\n')
    with pytest.raises(ValueError, match="not a demo recording"):
        read_recording(path)


def test_busy_port_exits_with_a_stop_training_message(capsys):
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen(1)
        port = busy.getsockname()[1]
        assert demo_recorder.main(["--port", str(port)]) == 2
    assert "Train-Stop.cmd" in capsys.readouterr().err


def test_ctrl_c_exits_cleanly(monkeypatch, tmp_path):
    def interrupted(self):
        raise KeyboardInterrupt

    monkeypatch.setattr(ObservationClient, "accept", interrupted)
    lines = []
    assert demo_recorder.run(tmp_path, 0, log=lines.append) == 0
    assert lines[-1] == "Stopped."
