"""OFFLINE simulated peers. None of these tests verifies Isaac compatibility."""

import json
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable

import pytest

from isaac_threrisaifuture.observation import (
    CAPABILITIES,
    MAX_MESSAGE_BYTES,
    BridgeError,
    BridgeTimeout,
    HelloAck,
    PeerDisconnected,
    ProtocolError,
    Snapshot,
    decode,
)
from isaac_threrisaifuture.observer_client import ObservationClient, ObserverConfig


def record(value: dict) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode() + b"\n"


def ack(session: str) -> dict:
    return {
        "type": "hello_ack",
        "protocol_version": 1,
        "schema_version": 1,
        "session_id": session,
        "capabilities": list(CAPABILITIES),
        "mod_version": "offline-test",
        "lua_version": "simulated",
        "extender_present": False,
        "game": {"version": None, "steam_build": None, "provenance": "unavailable"},
    }


def snapshot(session: str, sequence: int = 1, **changes: object) -> dict:
    result = {
        "type": "snapshot",
        "schema_version": 1,
        "session_id": session,
        "sequence": sequence,
        "game_epoch": 1,
        "frame_id": 10,
        "update_id": 10,
        "status": "active",
        "reason": None,
        "room": {"visit_id": 1},
        "player": {
            "index": 0,
            "character_type": 0,
            "position": {"x": 120.0, "y": 80.0},
            "health": {
                "red_half_hearts": 6,
                "max_red_half_hearts": 6,
                "soul_half_hearts": 0,
                "bone_containers": 0,
            },
        },
    }
    result.update(changes)
    return result


@pytest.fixture
def peers():
    """Manage real localhost sockets backed by explicitly simulated Lua peers."""
    threads, errors = [], []

    def start(address: tuple[str, int], handler: Callable[[socket.socket, str], None]) -> None:
        def run() -> None:
            try:
                with socket.create_connection(address, timeout=2) as conn:
                    with conn.makefile("rb") as stream:
                        hello = json.loads(stream.readline())
                    handler(conn, hello["session_id"])
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # Negative cases intentionally close their peer.
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=run, daemon=True)
        threads.append(thread)
        thread.start()

    yield start
    for thread in threads:
        thread.join(timeout=3)
        assert not thread.is_alive(), "Simulated peer leaked"
    assert not errors


def config(**kwargs) -> ObserverConfig:
    return ObserverConfig(port=0, **kwargs)


def test_fragmented_handshake_combined_snapshots_and_reconnect(peers) -> None:
    sessions = []

    def send(conn, session):
        sessions.append(session)
        payload = record(ack(session))
        conn.sendall(payload[:7])
        conn.sendall(payload[7:] + record(snapshot(session)) + record(snapshot(session, 2)))

    with ObservationClient(config()) as client:
        for _ in range(2):
            peers(client.address, send)
            hello = client.accept()
            assert hello.game.version is None
            first, second = client.receive(), client.receive()
            assert first.player.position.x == 120
            assert second.sequence == 2  # Equal engine frame is allowed.
    assert len(set(sessions)) == 2
    with pytest.raises(BridgeError, match="closed"):
        _ = client.address


@pytest.mark.parametrize(
    "field,value",
    [
        ("protocol_version", 2),
        ("schema_version", 2),
        ("protocol_version", True),
        ("session_id", "0" * 32),
        ("capabilities", []),
        ("extra", "rejected"),
    ],
)
def test_invalid_handshake_closes_peer(peers, field, value) -> None:
    def send(conn, session):
        data = ack(session)
        data[field] = value
        conn.sendall(record(data))

    with ObservationClient(config()) as client:
        peers(client.address, send)
        with pytest.raises(ProtocolError):
            client.accept()
        with pytest.raises(BridgeError, match="No negotiated"):
            client.receive()


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"{",
        b"[]",
        b"null",
        b"\xff",
        b'{"type":"x","type":"y"}',
        b"x" * (MAX_MESSAGE_BYTES + 1),
        b"{}\r",
        b"{}\n",
    ],
    ids=["empty", "unfinished", "array", "null", "utf8", "duplicate", "oversize", "cr", "lf"],
)
def test_malformed_json_and_bounds(raw) -> None:
    with pytest.raises(ProtocolError):
        decode(raw, HelloAck)


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": 2},
        {"frame_id": True},
        {"frame_id": -1},
        {"room": None},
        {"player": None},
        {"status": "loading"},
        {"reason": "state_read_failed"},
        {"schema_version": True},
        {"sequence": "1"},
        {"oracle_map": [1, 2]},
    ],
)
def test_malformed_snapshot(change) -> None:
    with pytest.raises(ProtocolError):
        decode(record(snapshot("a" * 32, **change))[:-1], Snapshot)


def test_missing_field_nonfinite_and_wrong_health_type() -> None:
    data = snapshot("a" * 32)
    del data["frame_id"]
    with pytest.raises(ProtocolError):
        decode(record(data)[:-1], Snapshot)
    for invalid in (float("nan"), float("inf"), "bad", True):
        data = snapshot("a" * 32)
        data["player"]["position"]["x"] = invalid
        with pytest.raises(ProtocolError):
            decode(record(data)[:-1], Snapshot)
    data = snapshot("a" * 32)
    data["player"]["health"]["red_half_hearts"] = False
    with pytest.raises(ProtocolError):
        decode(record(data)[:-1], Snapshot)


@pytest.mark.parametrize(
    "changes",
    [
        {"sequence": 1},
        {"sequence": 0},
        {"frame_id": 9},
        {"game_epoch": 0},
        {"session_id": "f" * 32},
        {"update_id": 9},
        {"room": {"visit_id": 0}},
    ],
)
def test_stale_identity_or_order_is_rejected(peers, changes) -> None:
    def send(conn, session):
        conn.sendall(record(ack(session)) + record(snapshot(session)))
        data = snapshot(session, 2)
        data.update(changes)
        conn.sendall(record(data))

    with ObservationClient(config()) as client:
        peers(client.address, send)
        client.accept()
        client.receive()
        with pytest.raises(ProtocolError):
            client.receive()


def test_availability_pause_and_new_epoch(peers) -> None:
    def send(conn, session):
        messages = [
            ack(session),
            snapshot(session),
            snapshot(session, 2, status="paused"),
            snapshot(
                session,
                3,
                status="unavailable",
                frame_id=None,
                room=None,
                player=None,
                reason="not_in_game",
            ),
            snapshot(session, 4, game_epoch=2, frame_id=0, room={"visit_id": 0}),
        ]
        conn.sendall(b"".join(record(m) for m in messages))

    with ObservationClient(config()) as client:
        peers(client.address, send)
        client.accept()
        assert client.receive().status == "active"
        assert client.receive().status == "paused"
        assert client.receive().player is None
        assert client.receive().frame_id == 0


def test_absolute_trickle_timeout(peers) -> None:
    def send(conn, session):
        conn.sendall(record(ack(session)))
        for _ in range(15):
            conn.sendall(b" ")
            time.sleep(0.02)

    with ObservationClient(config(message_timeout=0.08)) as client:
        peers(client.address, send)
        client.accept()
        start = time.monotonic()
        with pytest.raises(BridgeTimeout):
            client.receive()
        assert time.monotonic() - start < 1


def test_accept_handshake_disconnect_and_oversize(peers) -> None:
    with ObservationClient(config(accept_timeout=0.01)) as client:
        with pytest.raises(BridgeTimeout):
            client.accept()
    for payload, error in (
        (b"", PeerDisconnected),
        (b"x" * (MAX_MESSAGE_BYTES + 1), ProtocolError),
    ):

        def send(conn, session, payload=payload):
            conn.sendall(record(ack(session)) + payload)

        with ObservationClient(config()) as client:
            peers(client.address, send)
            client.accept()
            with pytest.raises(error):
                client.receive()

    def silent(conn, session):
        time.sleep(0.15)

    with ObservationClient(config(handshake_timeout=0.03)) as client:
        peers(client.address, silent)
        with pytest.raises(BridgeTimeout):
            client.accept()


def test_interruption_closes_sockets(peers) -> None:
    eof = threading.Event()

    def send(conn, session):
        conn.sendall(record(ack(session)))
        if conn.recv(1) == b"":
            eof.set()

    with pytest.raises(KeyboardInterrupt), ObservationClient(config()) as client:
        peers(client.address, send)
        client.accept()
        raise KeyboardInterrupt
    assert eof.wait(1)
    client.close()  # Idempotent


@pytest.mark.parametrize(
    "kwargs",
    [
        {"host": "0.0.0.0"},
        {"port": -1},
        {"port": True},
        {"message_timeout": 0},
        {"accept_timeout": float("nan")},
        {"handshake_timeout": float("inf")},
    ],
)
def test_invalid_configuration(kwargs) -> None:
    with pytest.raises(ValueError):
        ObserverConfig(**kwargs)


def test_cli_with_simulated_peer() -> None:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "isaac_threrisaifuture.cli",
            "observe",
            "--port",
            "0",
            "--samples",
            "1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        listening = json.loads(process.stdout.readline())
        address = tuple(listening["address"])
        with socket.create_connection(address, timeout=2) as conn:
            with conn.makefile("rb") as stream:
                hello = json.loads(stream.readline())
            session = hello["session_id"]
            conn.sendall(record(ack(session)) + record(snapshot(session)))
        stdout, stderr = process.communicate(timeout=3)
        assert process.returncode == 0, stderr
        messages = [json.loads(line) for line in stdout.splitlines()]
        assert [m["type"] for m in messages] == ["hello_ack", "snapshot"]
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


@pytest.mark.parametrize("supports_restart", [False, True])
def test_optional_restart_requires_peer_capability(peers, supports_restart):
    def send(conn, session):
        response = ack(session)
        if supports_restart:
            response["capabilities"].append("death_restart_v1")
        conn.sendall(record(response))

    with ObservationClient(config(restart_after_death=True)) as client:
        peers(client.address, send)
        if supports_restart:
            assert "death_restart_v1" in client.accept().capabilities
        else:
            with pytest.raises(ProtocolError, match="capabilities"):
                client.accept()


def test_restart_cli_requires_manual_profile_confirmation():
    result = subprocess.run(
        [sys.executable, "-m", "isaac_threrisaifuture.cli", "observe", "--restart-after-death"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 2
    assert "--confirmed-save-slot 2" in result.stderr
