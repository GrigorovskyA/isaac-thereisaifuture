"""Bounded native snapshot waiting against simulated peers; no Isaac evidence."""

import time

import pytest
import test_native_protocol
from synthetic import frame
from test_native_negotiation import SimulatedPeers
from test_native_protocol import command, completion
from test_native_receipts import baseline, kinded
from test_observer import ack, record, snapshot

from isaac_threrisaifuture.entities import EntitySnapshot
from isaac_threrisaifuture.episodes import EpisodeFault
from isaac_threrisaifuture.native_client import NativeStepClient, UnsupportedNativeOperation
from isaac_threrisaifuture.native_events import NativeEventCursor
from isaac_threrisaifuture.observation import BridgeError, PeerDisconnected
from isaac_threrisaifuture.observer_client import (
    NATIVE_EPISODE_CAPABILITY,
    ORACLE_KINDS,
    ObserverConfig,
    oracle_kind_capability,
)

NATIVE = ObserverConfig(port=0, native_episode_steps=True)
ROOM = ObserverConfig(port=0, native_episode_steps=True, native_oracle_kinds=("room_cleared",))
BOTH = ObserverConfig(
    port=0, native_episode_steps=True, native_oracle_kinds=("room_cleared", "player_died")
)


@pytest.fixture
def sim():
    peers = SimulatedPeers()
    try:
        yield peers
    finally:
        peers.finish()


def state(session, sequence, kind="active", frame_id=10, epoch=1, room=1, update=None):
    if kind == "unavailable":
        outer = snapshot(
            session,
            sequence,
            status=kind,
            reason="state_read_failed",
            frame_id=None,
            room=None,
            player=None,
            game_epoch=epoch,
            update_id=frame_id if update is None else update,
        )
        outer["entity_frame"] = None
        return outer
    outer = snapshot(
        session,
        sequence,
        status=kind,
        frame_id=frame_id,
        update_id=frame_id,
        game_epoch=epoch,
        room={"visit_id": room},
    )
    outer["entity_frame"] = frame(
        session_id=session,
        game_epoch=epoch,
        room_visit=room,
        frame_id=frame_id,
        provenance="game_api",
        player_position=outer["player"]["position"],
        health=outer["player"]["health"],
    ).model_dump()
    return outer


def peer(*specs, after=None):
    """Simulated peer: native hello_ack, then dict specs (sequenced) or raw bytes."""

    def handler(conn, session):
        hello = ack(session)
        hello["capabilities"].append(NATIVE_EPISODE_CAPABILITY)
        data = record(hello)
        for index, spec in enumerate(specs, start=1):
            data += spec if isinstance(spec, bytes) else record(state(session, index, **spec))
        conn.sendall(data)
        if after is not None:
            after(conn)

    return handler


def hold_until_closed(conn):
    conn.settimeout(2)
    assert conn.recv(4096) == b""  # EOF only: the client never sends command bytes


def test_requires_explicit_native_config():
    with pytest.raises(ValueError, match="native_episode_steps"):
        NativeStepClient(ObserverConfig(port=0))


def test_receive_active_needs_a_negotiated_peer():
    with NativeStepClient(NATIVE) as client:
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive_active()


def test_paused_and_unavailable_are_skipped_then_active_resumes(sim):
    specs = [
        {"frame_id": 10},
        {"kind": "paused", "frame_id": 10},
        {"kind": "paused", "frame_id": 10},
        {"kind": "unavailable", "update": 10},
        {"frame_id": 16},
    ]
    with NativeStepClient(NATIVE) as client:
        sim.start(client.address, peer(*specs, after=hold_until_closed))
        client.accept()
        first, second = client.receive_active(), client.receive_active()
        client.release()
    assert isinstance(first, EntitySnapshot)
    assert (first.frame_id, second.frame_id) == (10, 16)


def test_absolute_deadline_holds_under_frequent_pause_traffic(sim):
    def flood(conn):
        sequence, end = 2, time.monotonic() + 2.0  # bounded peer lifetime
        while time.monotonic() < end:
            conn.sendall(record(state(session_of[0], sequence, kind="paused", frame_id=10)))
            sequence += 1
            time.sleep(0.05)

    session_of: list[str] = []

    def handler(conn, session):
        session_of.append(session)
        peer({"kind": "paused", "frame_id": 10}, after=flood)(conn, session)

    config = ObserverConfig(port=0, native_episode_steps=True, message_timeout=0.5)
    with NativeStepClient(config) as client:
        sim.start(client.address, handler)
        client.accept()
        started = time.monotonic()
        with pytest.raises(EpisodeFault):
            client.receive_active()
        elapsed = time.monotonic() - started
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive_active()
    assert 0.4 <= elapsed < 1.5


@pytest.mark.parametrize("repeat", [10, 9])
def test_active_frame_must_strictly_advance(sim, repeat):
    with NativeStepClient(NATIVE) as client:
        sim.start(client.address, peer({"frame_id": 10}, {"frame_id": repeat}))
        client.accept()
        client.receive_active()
        with pytest.raises(EpisodeFault):
            client.receive_active()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive_active()


@pytest.mark.parametrize("changes", [{"epoch": 2}, {"room": 2}])
def test_epoch_or_room_crossing_between_active_snapshots_faults(sim, changes):
    with NativeStepClient(NATIVE) as client:
        sim.start(client.address, peer({"frame_id": 10}, {"frame_id": 20, **changes}))
        client.accept()
        client.receive_active()
        with pytest.raises(EpisodeFault):
            client.receive_active()


def test_first_active_may_be_any_epoch_and_reconnect_clears_active_state(sim):
    with NativeStepClient(NATIVE) as client:
        sim.start(client.address, peer({"frame_id": 50, "epoch": 1, "room": 1}))
        client.accept()
        assert client.receive_active().frame_id == 50
        client.close_peer()
        sim.start(client.address, peer({"frame_id": 10, "epoch": 5, "room": 3}))
        client.accept()
        snap = client.receive_active()
        assert (snap.game_epoch, snap.frame_id) == (5, 10)
        client.close_peer()
        sim.start(client.address, peer({"frame_id": 10, "epoch": 5, "room": 3}))
        client.accept()
        assert client.receive_active().frame_id == 10  # lower frame is fine on a new session


@pytest.mark.parametrize("raw", [b"not json\n", b'{"type":"snapshot"}\n'])
def test_malformed_message_faults_and_closes(sim, raw):
    with NativeStepClient(NATIVE) as client:
        sim.start(client.address, peer(raw))
        client.accept()
        with pytest.raises(EpisodeFault):
            client.receive_active()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive_active()


def test_disconnect_faults_and_keeps_the_cause(sim):
    with NativeStepClient(NATIVE) as client:
        sim.start(client.address, peer())
        client.accept()
        with pytest.raises(EpisodeFault) as info:
            client.receive_active()
    assert isinstance(info.value.__cause__, PeerDisconnected)


def test_release_is_idempotent_and_peer_sees_eof(sim):
    with NativeStepClient(NATIVE) as client:
        sim.start(client.address, peer({"frame_id": 10}, after=hold_until_closed))
        client.accept()
        client.receive_active()
        client.release()
        client.release()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive_active()


@pytest.mark.parametrize("name", ["start_episode", "reset", "step"])
def test_unsupported_operations_fault_and_send_no_command_bytes(sim, name):
    with NativeStepClient(NATIVE) as client:
        sim.start(client.address, peer(after=hold_until_closed))
        client.accept()
        with pytest.raises(UnsupportedNativeOperation):
            getattr(client, name)()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive_active()
    assert issubclass(UnsupportedNativeOperation, EpisodeFault)


def receipt_peer(build):
    """Peer that advertises every oracle kind, sends one active frame, then build(session)."""

    def handler(conn, session):
        hello = ack(session)
        hello["capabilities"].extend(
            [NATIVE_EPISODE_CAPABILITY, *map(oracle_kind_capability, ORACLE_KINDS)]
        )
        data = record(hello) + record(state(session, 1, frame_id=100)) + build(session)
        conn.sendall(data)
        hold_until_closed(conn)

    return handler


def step(session, *events):
    """Acknowledgement, the given native events and a completion whose watermark covers them."""
    done = completion(
        session_id=session,
        last_event_id=len(events),
        frame=frame(session_id=session, frame_id=107, provenance="game_api"),
    )
    models = (test_native_protocol.ack(session_id=session), *events, done)
    return b"".join(model.model_dump_json().encode() + b"\n" for model in models)


def open_step(client, sim, events):
    sim.start(client.address, receipt_peer(lambda s: step(s, *events(s))))
    client.accept()
    session = sim.hellos[-1]["session_id"]
    client.receive_active()
    return session, NativeEventCursor(session, 1)


def receive(client, session, cursor):
    return client.receive_receipt(
        command(session_id=session), baseline(session_id=session, frame_id=100), cursor
    )


def assert_closed_and_uncommitted(client, cursor):
    assert cursor.last_id == 0
    assert (client._peer, client._active, client._receipts) == (None, None, 0)


def test_requested_kinds_are_accepted_through_the_client(sim):
    def events(s):
        return [
            kinded("room_cleared", 1, 102, session_id=s),
            kinded("player_died", 2, 103, session_id=s),
        ]

    with NativeStepClient(BOTH) as client:
        session, cursor = open_step(client, sim, events)
        receipt = receive(client, session, cursor)
        assert [item.event.kind for item in receipt.events] == ["room_cleared", "player_died"]
        assert (cursor.last_id, client._receipts) == (2, 1)
        client.release()


@pytest.mark.parametrize(
    "events",
    [
        lambda s: [kinded("player_died", 1, 102, session_id=s)],
        lambda s: [  # the valid first event is not committed when the second is rejected
            kinded("room_cleared", 1, 102, session_id=s),
            kinded("enemy_killed", 2, 103, session_id=s),
        ],
    ],
)
def test_advertised_but_unrequested_kind_faults_before_commit(sim, events):
    with NativeStepClient(ROOM) as client:
        session, cursor = open_step(client, sim, events)
        assert sim.hellos[-1]["required_capabilities"][-1] == oracle_kind_capability("room_cleared")
        assert oracle_kind_capability("player_died") not in sim.hellos[-1]["required_capabilities"]
        with pytest.raises(EpisodeFault, match="not requested"):
            receive(client, session, cursor)
        assert_closed_and_uncommitted(client, cursor)
        with pytest.raises(BridgeError, match="No negotiated peer"):
            receive(client, session, cursor)


@pytest.mark.parametrize("kind", ORACLE_KINDS)
def test_without_requested_kinds_the_client_rejects_every_native_event(sim, kind):
    with NativeStepClient(NATIVE) as client:  # the peer advertises the kind; nobody asked for it
        session, cursor = open_step(client, sim, lambda s: [kinded(kind, 1, 102, session_id=s)])
        assert not any(
            name.startswith("oracle_") for name in sim.hellos[-1]["required_capabilities"]
        )
        with pytest.raises(EpisodeFault, match="not requested"):
            receive(client, session, cursor)
        assert_closed_and_uncommitted(client, cursor)


def test_event_free_receipt_still_completes_without_requested_kinds(sim):
    with NativeStepClient(NATIVE) as client:
        session, cursor = open_step(client, sim, lambda s: [])
        receipt = receive(client, session, cursor)
        assert receipt.events == () and cursor.last_id == 0 and client._receipts == 1
        client.release()
