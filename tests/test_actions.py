"""OFFLINE socket peers and strict action models; no real game integration."""

import json
import time

import pytest
from pydantic import ValidationError
from test_observer import ack, config, record, snapshot
from test_observer import peers as peers

from isaac_threrisaifuture.actions import ActionApproval, ActionClient, Command
from isaac_threrisaifuture.observation import BridgeError, BridgeTimeout, ProtocolError, decode
from isaac_threrisaifuture.observer_client import ObserverConfig


def approval(**changes):
    values = dict(
        profile_id="offline",
        profile_mode="isolated",
        expires_at=int(time.time()) + 600,
        profile_evidence="simulated",
        slot_evidence="simulated",
        runtime_authorization="offline",
        slot=2,
        game_epoch=1,
    )
    values.update(changes)
    return ActionApproval(**values)


def action_hello(session):
    hello = ack(session)
    hello["capabilities"].append("safe_actions_v1")
    return hello


def command_ack(command, **changes):
    result = {
        k: command[k]
        for k in (
            "protocol_version",
            "session_id",
            "sequence",
            "game_epoch",
            "room_visit",
            "frame_id",
            "kind",
        )
    }
    result.update(type="command_ack", status="accepted")
    result.update(changes)
    return result


def test_transactions_fragmented_acks_interleaved_snapshots_and_reconnect(peers):
    received, sessions = [], []

    def send(conn, session):
        sessions.append(session)
        conn.sendall(record(action_hello(session)) + record(snapshot(session)))
        with conn.makefile("rb") as stream:
            for index in range(4):
                raw = stream.readline()
                command = decode(raw.rstrip(b"\n"), Command)
                received.append(command)
                payload = record(command_ack(command.model_dump()))
                # Snapshot arriving before an ack uses the same ordering checks.
                conn.sendall(record(snapshot(session, index + 2)) + payload[:9])
                conn.sendall(payload[9:])
            assert conn.recv(1) == b""  # close releases resources, no replay sender

    with ActionClient(config(), approval()) as client:
        for _ in range(2):
            peers(client.address, send)
            client.accept()
            client.receive()
            assert client.command("action", move="right", shoot="up", frames=5).sequence == 1
            assert client.command("heartbeat").sequence == 2
            assert client.command("action", frames=1).sequence == 3  # explicit neutral
            assert client.command("release").sequence == 4
            client.close_peer()
    assert len(set(sessions)) == 2
    assert [c.sequence for c in received] == [1, 2, 3, 4] * 2
    with pytest.raises(BridgeError):
        client.command("heartbeat")
    with pytest.raises(BridgeError):
        _ = client.address


@pytest.mark.parametrize(
    "change",
    [
        {"session_id": "b" * 32},
        {"sequence": 0},
        {"sequence": 2},
        {"game_epoch": 0},
        {"room_visit": 0},
        {"frame_id": 9},
        {"frame_id": 26},
        {"kind": "heartbeat"},
        {"protocol_version": 2},
        {"status": "applied"},
        {"extra": 1},
    ],
)
def test_bad_ack_invalidates_connection_and_cached_action(peers, change):
    def send(conn, session):
        conn.sendall(record(action_hello(session)) + record(snapshot(session)))
        with conn.makefile("rb") as stream:
            command = json.loads(stream.readline())
        conn.sendall(record(command_ack(command, **change)))
        assert conn.recv(1) == b""

    with ActionClient(config(), approval()) as client:
        peers(client.address, send)
        client.accept()
        client.receive()
        with pytest.raises(ProtocolError):
            client.command("action", frames=1)
        with pytest.raises(BridgeError):
            client.command("heartbeat")


def test_missing_ack_deadline_closes_peer(peers):
    def send(conn, session):
        conn.sendall(record(action_hello(session)) + record(snapshot(session)))
        with conn.makefile("rb") as stream:
            assert json.loads(stream.readline())["type"] == "command"
        assert conn.recv(1) == b""

    with ActionClient(config(message_timeout=0.04), approval()) as client:
        peers(client.address, send)
        client.accept()
        client.receive()
        with pytest.raises(BridgeTimeout):
            client.command("action", frames=15)


@pytest.mark.parametrize("response", [b"{broken}\n", b"[]\n", b"null\n", b"true\n"])
def test_malformed_ack_closes_peer(peers, response):
    def send(conn, session):
        conn.sendall(record(action_hello(session)) + record(snapshot(session)))
        with conn.makefile("rb") as stream:
            stream.readline()
        conn.sendall(response)
        assert conn.recv(1) == b""

    with ActionClient(config(), approval()) as client:
        peers(client.address, send)
        client.accept()
        client.receive()
        with pytest.raises(ProtocolError):
            client.command("release")


@pytest.mark.parametrize("snap_changes", [{"game_epoch": 2}, {"status": "paused"}])
def test_wrong_epoch_or_paused_observation_blocks_action(peers, snap_changes):
    def send(conn, session):
        conn.sendall(record(action_hello(session)) + record(snapshot(session, **snap_changes)))
        assert conn.recv(1) == b""  # no command reaches the peer

    with ActionClient(config(), approval()) as client:
        peers(client.address, send)
        client.accept()
        with pytest.raises(ProtocolError):
            client.receive()
            client.command("action", frames=1)


def test_missing_capability_rejected(peers):
    def send(conn, session):
        conn.sendall(record(ack(session)))
        assert conn.recv(1) == b""

    with ActionClient(config(), approval()) as client:
        peers(client.address, send)
        with pytest.raises(ProtocolError):
            client.accept()


@pytest.mark.parametrize(
    "changes",
    [
        {"protocol_version": True},
        {"protocol_version": 2},
        {"sequence": True},
        {"sequence": 0},
        {"sequence": -1},
        {"frames": True},
        {"frames": 1.5},
        {"frames": 16},
        {"frames": 0},
        {"kind": "restart"},
        {"move": "diagonal"},
        {"shoot": "diagonal"},
        {"session_id": "old"},
        {"game_epoch": -1},
        {"extra": 1},
        {"kind": "heartbeat"},
        {"kind": "release"},
        {"use": "grenade"},
        {"use": 1},
        {"use": None},
        {"kind": "heartbeat", "move": "none", "shoot": "none", "frames": 0, "use": "bomb"},
        {"kind": "release", "move": "none", "shoot": "none", "frames": 0, "use": "active"},
        {"kind": "heartbeat", "move": "none", "shoot": "none", "frames": 0, "use": "pillcard"},
    ],
)
def test_strict_command_payload(changes):
    values = dict(
        session_id="a" * 32,
        sequence=1,
        game_epoch=1,
        room_visit=1,
        frame_id=10,
        kind="action",
        move="right",
        shoot="up",
        frames=15,
    )
    values.update(changes)
    with pytest.raises((ValidationError, ProtocolError)):
        Command(**values).wire_bytes()


@pytest.mark.parametrize("use", ["none", "bomb", "active", "pillcard"])
def test_canonical_command_carries_use_between_shoot_and_frames(use):
    command = Command(
        session_id="a" * 32,
        sequence=1,
        game_epoch=1,
        room_visit=1,
        frame_id=10,
        kind="action",
        move="right",
        shoot="up",
        use=use,
        frames=5,
    )
    assert command.wire_bytes() == (
        b'{"type":"command","protocol_version":1,"session_id":"' + b"a" * 32 + b'",'
        b'"sequence":1,"game_epoch":1,"room_visit":1,"frame_id":10,"kind":"action",'
        b'"move":"right","shoot":"up","use":"' + use.encode() + b'","frames":5}\n'
    )
    assert decode(command.wire_bytes().rstrip(b"\n"), Command) == command


@pytest.mark.parametrize(
    "changes",
    [
        {"slot": 1},
        {"slot": True},
        {"slot_evidence": ""},
        {"profile_evidence": ""},
        {"slot_evidence": " "},
        {"game_epoch": -1},
    ],
)
def test_approval_requires_valid_evidence_references(changes):
    with pytest.raises(ValidationError):
        approval(**changes)


def test_modes_cannot_be_combined():
    with pytest.raises(ValueError):
        ObserverConfig(safe_actions=True, restart_after_death=True)
    with pytest.raises(ValueError):
        ActionClient(config(restart_after_death=True), approval())


def test_interrupt_during_command_closes_peer(peers, monkeypatch):
    def send(conn, session):
        conn.sendall(record(action_hello(session)) + record(snapshot(session)))
        with conn.makefile("rb") as stream:
            assert json.loads(stream.readline())["type"] == "command"
        assert conn.recv(1) == b""

    with ActionClient(config(), approval()) as client:
        peers(client.address, send)
        client.accept()
        client.receive()

        def interrupt(deadline):
            raise KeyboardInterrupt

        monkeypatch.setattr(client, "_read_line", interrupt)
        with pytest.raises(KeyboardInterrupt):
            client.command("action", frames=15)
        with pytest.raises(BridgeError):
            client.command("heartbeat")


def test_expired_approval_cannot_accept_or_send():
    with ActionClient(config(), approval(expires_at=1)) as client:
        with pytest.raises(ProtocolError, match="expired"):
            client.accept()
        with pytest.raises(ProtocolError, match="expired"):
            client.command("action", frames=1)
