"""Simulated peers and strict entity-envelope tests; no Isaac evidence."""

import json

import pytest
from synthetic import enemy, frame
from test_observer import ack, record, snapshot

from isaac_threrisaifuture.encoding import OBSERVATION_SIZE, encode
from isaac_threrisaifuture.entities import EntitySnapshot
from isaac_threrisaifuture.observation import BridgeError, ProtocolError, Snapshot, decode
from isaac_threrisaifuture.observer_client import ObservationClient, ObserverConfig

CAPABILITY = "entity_observation_v1"
pytest_plugins = ["test_observer"]


def entity_snapshot(session, sequence=1, **frame_changes):
    outer = snapshot(session, sequence)
    inner = frame(
        [enemy(1, 1, 0)],
        session_id=session,
        frame_id=outer["frame_id"],
        provenance="game_api",
        player_position=outer["player"]["position"],
        health=outer["player"]["health"],
    ).model_dump()
    inner.update(frame_changes)
    outer["entity_frame"] = inner
    return outer


def send_entity(conn, session):
    hello = ack(session)
    hello["capabilities"].append(CAPABILITY)
    conn.sendall(record(hello) + record(entity_snapshot(session)))


def test_opt_in_entity_receive_and_fresh_reconnect(peers):
    sessions = []
    with ObservationClient(ObserverConfig(port=0, entity_observations=True)) as client:
        for _ in range(2):
            peers(client.address, send_entity)
            sessions.append(client.accept().session_id)
            snap = client.receive()
            assert isinstance(snap, EntitySnapshot)
            assert snap.entity_frame is not None
            assert encode(snap.entity_frame).vector.shape == (OBSERVATION_SIZE,)
    assert sessions[0] != sessions[1]


def test_default_client_rejects_unsolicited_extension(peers):
    with ObservationClient(ObserverConfig(port=0)) as client:
        peers(client.address, send_entity)
        client.accept()
        with pytest.raises(ProtocolError):
            client.receive()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive()


@pytest.mark.parametrize(
    "changes",
    [
        {"session_id": "b" * 32},
        {"game_epoch": 2},
        {"room_visit": 2},
        {"frame_id": 11},
        {"provenance": "synthetic"},
        {"player_position": {"x": 999.0, "y": 80.0}},
        {
            "health": {
                "red_half_hearts": 0,
                "max_red_half_hearts": 6,
                "soul_half_hearts": 0,
                "bone_containers": 0,
            }
        },
        {"observation_schema_version": True},
        {"source_overflow": {"enemy": -1}},
        {"source_overflow": {"hidden_room": 1}},
    ],
)
def test_entity_envelope_rejects_incompatible_state(changes):
    payload = entity_snapshot("a" * 32, **changes)
    with pytest.raises(ProtocolError):
        decode(record(payload).rstrip(b"\n"), EntitySnapshot)


def test_unavailable_entity_snapshot_carries_no_stale_frame():
    payload = snapshot(
        "a" * 32,
        status="unavailable",
        reason="state_read_failed",
        frame_id=None,
        room=None,
        player=None,
    )
    payload["entity_frame"] = None
    assert decode(record(payload).rstrip(b"\n"), EntitySnapshot).entity_frame is None
    payload["entity_frame"] = entity_snapshot("a" * 32)["entity_frame"]
    with pytest.raises(ProtocolError):
        decode(record(payload).rstrip(b"\n"), EntitySnapshot)


def test_plain_snapshot_model_remains_strict():
    with pytest.raises(ProtocolError):
        decode(json.dumps(entity_snapshot("a" * 32)).encode(), Snapshot)


@pytest.mark.parametrize("option", ["safe_actions", "restart_after_death"])
def test_entity_opt_in_cannot_enable_control(option):
    with pytest.raises(ValueError, match="read-only"):
        ObserverConfig(entity_observations=True, **{option: True})


def test_source_and_encoder_overflow_are_combined():
    encoded = encode(frame([enemy(i, i, 0) for i in range(40)], source_overflow={"enemy": 7}))
    assert encoded.overflow == {"enemy": 15}


def test_old_peer_cannot_silently_downgrade_entity_mode(peers):
    def old_peer(conn, session):
        conn.sendall(record(ack(session)))

    with ObservationClient(ObserverConfig(port=0, entity_observations=True)) as client:
        peers(client.address, old_peer)
        with pytest.raises(ProtocolError, match="capabilities"):
            client.accept()


def test_entity_duplicate_sequence_closes_peer(peers):
    def duplicate(conn, session):
        hello = ack(session)
        hello["capabilities"].append(CAPABILITY)
        conn.sendall(record(hello) + record(entity_snapshot(session)) * 2)

    with ObservationClient(ObserverConfig(port=0, entity_observations=True)) as client:
        peers(client.address, duplicate)
        client.accept()
        client.receive()
        with pytest.raises(ProtocolError, match="sequence"):
            client.receive()
