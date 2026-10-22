"""Combined native-episode negotiation against simulated peers; no Isaac evidence."""

import json
import socket
import threading

import pytest
from synthetic import event, frame
from test_entity_transport import entity_snapshot
from test_native_protocol import completion
from test_observer import ack, record, snapshot

from isaac_threrisaifuture.entities import EntitySnapshot
from isaac_threrisaifuture.native_events import NativeOracleEvent
from isaac_threrisaifuture.observation import BridgeError, ProtocolError, Snapshot
from isaac_threrisaifuture.observer_client import (
    CAPABILITIES,
    DEATH_RESTART_CAPABILITY,
    NATIVE_EPISODE_CAPABILITY,
    ObservationClient,
    ObserverConfig,
)

JOIN_SECONDS = 3
NATIVE = ObserverConfig(port=0, native_episode_steps=True)


class SimulatedPeers:
    """Simulated Lua peers: bounded sockets, recorded hellos, errors kept for the test thread."""

    def __init__(self) -> None:
        self.threads: list[threading.Thread] = []
        self.errors: list[BaseException] = []
        self.hellos: list[dict] = []

    def start(self, address, handler) -> None:
        def run() -> None:
            try:
                with socket.create_connection(address, timeout=2) as conn:
                    with conn.makefile("rb") as stream:
                        hello = json.loads(stream.readline())
                    self.hellos.append(hello)
                    handler(conn, hello["session_id"])
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # Negative cases intentionally close their peer.
            except BaseException as exc:
                self.errors.append(exc)

        thread = threading.Thread(target=run, daemon=True)
        self.threads.append(thread)
        thread.start()

    def finish(self) -> None:
        for thread in self.threads:
            thread.join(timeout=JOIN_SECONDS)
        alive = [thread for thread in self.threads if thread.is_alive()]
        if self.errors:
            raise self.errors[0]
        assert not alive, "Simulated peer leaked"


@pytest.fixture
def sim():
    peers = SimulatedPeers()
    try:
        yield peers
    finally:
        peers.finish()


def peer(*capabilities, build=None, frames=1):
    """Simulated peer: hello_ack with extra capabilities, then `frames` payloads."""

    def handler(conn, session):
        hello = ack(session)
        hello["capabilities"].extend(capabilities)
        data = record(hello)
        for sequence in range(1, frames + 1):
            data += record((build or snapshot)(session, sequence))
        conn.sendall(data)

    return handler


def native_event_record(session, _sequence=1):
    item = NativeOracleEvent(
        session_id=session,
        game_epoch=1,
        room_visit=1,
        frame_id=10,
        event_id=1,
        event=event(
            session_id=session, game_epoch=1, room_visit=1, frame_id=10, provenance="game_api"
        ),
    )
    return json.loads(item.model_dump_json())


def step_completion_record(session, _sequence=1):
    item = completion(
        session_id=session,
        accepted=10,
        frame=frame(
            frame_id=16, session_id=session, game_epoch=1, room_visit=1, provenance="game_api"
        ),
    )
    return json.loads(item.model_dump_json())


def test_combined_negotiation_requests_only_entity_action_and_decodes_entities(sim):
    with ObservationClient(NATIVE) as client:
        sim.start(client.address, peer(NATIVE_EPISODE_CAPABILITY, build=entity_snapshot))
        session = client.accept().session_id
        snap = client.receive()
    assert isinstance(snap, EntitySnapshot)
    assert snap.entity_frame is not None
    assert snap.session_id == session
    assert sim.hellos[0]["required_capabilities"] == [*CAPABILITIES, NATIVE_EPISODE_CAPABILITY]


def test_same_client_reconnect_gets_fresh_session_and_counters(sim):
    sessions = []
    with ObservationClient(NATIVE) as client:
        for _ in range(2):
            sim.start(client.address, peer(NATIVE_EPISODE_CAPABILITY, build=entity_snapshot))
            sessions.append(client.accept().session_id)
            assert client.receive().sequence == 1  # a stale counter would reject sequence 1
            client.close_peer()
            with pytest.raises(BridgeError, match="No negotiated peer"):
                client.receive()
    assert sessions[0] != sessions[1]
    assert [h["session_id"] for h in sim.hellos] == sessions


def test_old_peer_is_rejected_without_fallback_or_state(sim):
    with ObservationClient(NATIVE) as client:
        sim.start(client.address, peer(build=entity_snapshot))
        with pytest.raises(ProtocolError, match="capabilities"):
            client.accept()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive()


def test_missing_entity_frame_is_rejected_and_closes_peer(sim):
    def without_frame(session, sequence):
        payload = entity_snapshot(session, sequence)
        del payload["entity_frame"]
        return payload

    with ObservationClient(NATIVE) as client:
        sim.start(client.address, peer(NATIVE_EPISODE_CAPABILITY, build=without_frame))
        client.accept()
        with pytest.raises(ProtocolError):
            client.receive()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive()


@pytest.mark.parametrize("build", [native_event_record, step_completion_record])
def test_unsolicited_native_message_is_rejected_and_closes_peer(sim, build):
    with ObservationClient(NATIVE) as client:
        sim.start(client.address, peer(NATIVE_EPISODE_CAPABILITY, build=build))
        client.accept()
        with pytest.raises(ProtocolError):
            client.receive()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive()


@pytest.mark.parametrize("option", ["safe_actions", "entity_observations", "restart_after_death"])
def test_native_mode_rejects_other_opt_ins(option):
    with pytest.raises(ValueError, match="Native episode"):
        ObserverConfig(native_episode_steps=True, **{option: True})


@pytest.mark.parametrize("value", [1, "yes", None])
def test_native_flag_requires_real_bool(value):
    with pytest.raises(ValueError, match="boolean"):
        ObserverConfig(native_episode_steps=value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("options", "extra", "entity"),
    [
        ({}, [], False),
        ({"safe_actions": True}, ["safe_actions_v1"], False),
        ({"restart_after_death": True}, [DEATH_RESTART_CAPABILITY], False),
        ({"entity_observations": True}, ["entity_observation_v1"], True),
    ],
)
def test_legacy_modes_keep_exact_hello_and_snapshot_shape(sim, options, extra, entity):
    assert ObserverConfig().native_episode_steps is False
    with ObservationClient(ObserverConfig(port=0, **options)) as client:
        sim.start(client.address, peer(*extra, build=entity_snapshot if entity else snapshot))
        client.accept()
        snap = client.receive()
    assert sim.hellos[0]["required_capabilities"] == [*CAPABILITIES, *extra]
    assert type(snap) is (EntitySnapshot if entity else Snapshot)
    assert hasattr(snap, "entity_frame") is entity
