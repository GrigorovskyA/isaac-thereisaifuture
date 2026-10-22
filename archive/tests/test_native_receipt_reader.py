"""Receipt socket reader against simulated bounded peers; no Isaac or sender evidence."""

import time
from types import SimpleNamespace

import pytest
import test_native_protocol
import test_native_receipts
import test_observer
from synthetic import event, frame
from test_native_client import ROOM, hold_until_closed, state
from test_native_events import OTHER, native
from test_native_negotiation import SimulatedPeers
from test_native_protocol import command, completion
from test_native_receipts import baseline, wire
from test_observer import record

from isaac_threrisaifuture import native_client
from isaac_threrisaifuture.episodes import EpisodeFault
from isaac_threrisaifuture.native_client import NativeStepClient, UnsupportedNativeOperation
from isaac_threrisaifuture.native_events import NativeEventCursor
from isaac_threrisaifuture.native_receipts import NativeReceiptAssembler
from isaac_threrisaifuture.observation import BridgeError, BridgeTimeout, ProtocolError
from isaac_threrisaifuture.observer_client import (
    NATIVE_EPISODE_CAPABILITY,
    ObserverConfig,
    oracle_kind_capability,
)

NATIVE = ROOM  # every e() event below is room_cleared
FAST = ObserverConfig(port=0, native_episode_steps=True, message_timeout=0.4)
KINDS = ("room_cleared",)


@pytest.fixture
def sim():
    peers = SimulatedPeers()
    try:
        yield peers
    finally:
        peers.finish()


def peer(build, hold=True):
    """Hello_ack, then items from build(session): bytes, float (sleep) or callable(conn)."""

    def run(conn, session):
        hello = test_observer.ack(session)
        hello["capabilities"].extend(
            [NATIVE_EPISODE_CAPABILITY, *map(oracle_kind_capability, KINDS)]
        )
        conn.sendall(record(hello))
        for item in build(session):
            if isinstance(item, float):
                time.sleep(item)
            elif callable(item):
                item(conn)
            else:
                conn.sendall(item)
        if hold:
            hold_until_closed(conn)  # EOF only: the reader never sends command bytes

    return run


def line(model):
    return model.model_dump_json().encode() + b"\n"


def first(s, frame_id=100):
    return record(state(s, 1, frame_id=frame_id))


def a(s, seq=1, fid=101, **changes):
    return line(test_native_protocol.ack(session_id=s, sequence=seq, frame_id=fid, **changes))


def e(s, i, f):
    nested = event(frame_id=f, provenance="game_api", session_id=s)
    return line(native(event_id=i, frame_id=f, session_id=s, event=nested))


def d(s, seq=1, accepted=101, last=0, **changes):
    elapsed = changes.get("elapsed", 6)
    changes.setdefault(
        "frame", frame(session_id=s, frame_id=accepted + elapsed, provenance="game_api")
    )
    return line(
        completion(session_id=s, sequence=seq, accepted=accepted, last_event_id=last, **changes)
    )


def base(s, frame_id=100):
    return baseline(session_id=s, frame_id=frame_id)


def sid(sim):
    return sim.hellos[-1]["session_id"]


def connect(client, sim, build, hold=True):
    sim.start(client.address, peer(build, hold))
    client.accept()
    s = sid(sim)
    return s, NativeEventCursor(s, 1)


def assert_closed(client, cursor):
    assert client._peer is None and client._active is None and client._receipts == 0
    assert cursor.last_id == 0


def test_split_and_coalesced_records_yield_a_receipt_and_no_outbound_bytes(sim):
    def build(s):
        return [first(s), a(s) + e(s, 1, 102), 0.05, d(s, last=1)[:40], 0.05, d(s, last=1)[40:]]

    with NativeStepClient(NATIVE) as client:
        s, cursor = connect(client, sim, build)
        client.receive_active()
        receipt = client.receive_receipt(command(session_id=s), base(s), cursor)
        assert [x.event_id for x in receipt.events] == [1]
        assert cursor.last_id == 1
        assert (client._active, client._receipts) == ((1, 1, 107), 1)
        client.release()


def test_sequential_receipts_with_replayed_event_are_deduplicated(sim):
    def build(s):
        txn1 = a(s) + e(s, 1, 102) + d(s, last=1)
        txn2 = a(s, 2, 108) + e(s, 1, 102) + e(s, 2, 110) + d(s, 2, 108, last=2)
        return [first(s), txn1 + txn2]

    with NativeStepClient(NATIVE) as client:
        s, cursor = connect(client, sim, build)
        client.receive_active()
        client.receive_receipt(command(session_id=s), base(s), cursor)
        second = client.receive_receipt(
            command(session_id=s, sequence=2, frame_id=107), base(s, 107), cursor
        )
        assert [x.event_id for x in second.events] == [2]
        assert cursor.last_id == 2
        assert (client._active, client._receipts) == ((1, 1, 114), 2)
        client.release()


def test_old_receipt_replay_for_the_next_command_faults(sim):
    def build(s):
        txn = a(s) + d(s)
        return [first(s), txn + txn]

    with NativeStepClient(NATIVE) as client:
        s, cursor = connect(client, sim, build)
        client.receive_active()
        client.receive_receipt(command(session_id=s), base(s), cursor)
        with pytest.raises(EpisodeFault):
            client.receive_receipt(
                command(session_id=s, sequence=2, frame_id=107), base(s, 107), cursor
            )
        assert client._peer is None


@pytest.mark.parametrize(("frame_id", "ok"), [(105, False), (107, False), (120, True)])
def test_snapshot_after_a_receipt_must_be_newer_than_its_frame(sim, frame_id, ok):
    def build(s):
        return [first(s), a(s) + d(s), record(state(s, 2, frame_id=frame_id))]

    with NativeStepClient(NATIVE) as client:
        s, cursor = connect(client, sim, build)
        client.receive_active()
        client.receive_receipt(command(session_id=s), base(s), cursor)
        if ok:
            assert client.receive_active().frame_id == frame_id
            client.release()
        else:
            with pytest.raises(EpisodeFault):
                client.receive_active()
            assert client._peer is None


def test_silent_peer_times_out_without_advancing_the_cursor(sim):
    with NativeStepClient(FAST) as client:
        s, cursor = connect(client, sim, lambda s: [first(s)])
        client.receive_active()
        with pytest.raises(EpisodeFault) as info:
            client.receive_receipt(command(session_id=s), base(s), cursor)
        assert isinstance(info.value.__cause__, BridgeTimeout)
        assert_closed(client, cursor)


def test_slow_trickle_is_cut_by_one_absolute_deadline(sim):
    def build(s):
        return [first(s), *[item for byte in a(s) for item in (bytes([byte]), 0.05)]]

    with NativeStepClient(FAST) as client:
        s, cursor = connect(client, sim, build)
        client.receive_active()
        started = time.monotonic()
        with pytest.raises(EpisodeFault) as info:
            client.receive_receipt(command(session_id=s), base(s), cursor)
        assert time.monotonic() - started < 1.5
        assert isinstance(info.value.__cause__, BridgeTimeout)
        assert_closed(client, cursor)


def test_late_receipt_is_rejected_before_the_cursor_advances(sim, monkeypatch):
    real = time.monotonic
    calls = []

    def fake():
        calls.append(1)
        return real() + (1000 if len(calls) >= 5 else 0)  # deadline, 3 reads, then commit

    def build(s):
        return [first(s), a(s) + e(s, 1, 102) + d(s, last=1)]

    with NativeStepClient(NATIVE) as client:
        s, cursor = connect(client, sim, build)
        client.receive_active()
        monkeypatch.setattr(native_client, "time", SimpleNamespace(monotonic=fake))
        with pytest.raises(EpisodeFault) as info:
            client.receive_receipt(command(session_id=s), base(s), cursor)
        assert isinstance(info.value.__cause__, BridgeTimeout)
        assert_closed(client, cursor)


BAD_STREAMS = {
    "event_before_ack": lambda s: [e(s, 1, 102), a(s), d(s, last=1)],
    "wrong_sequence": lambda s: [a(s, 2)],
    "second_ack": lambda s: [a(s), a(s)],
    "completion_first": lambda s: [d(s)],
    "event_gap": lambda s: [a(s), e(s, 2, 102), d(s, last=2)],
    "watermark_missing": lambda s: [a(s), e(s, 1, 102), d(s, last=0)],
    "watermark_ahead": lambda s: [a(s), d(s, last=1)],
    "expired": lambda s: [a(s), d(s, status="expired", reason="wall_deadline", elapsed=3)],
    "foreign_session_event": lambda s: [a(s), foreign_event(OTHER)],
    "snapshot_in_receipt": lambda s: [a(s), record(state(s, 2, frame_id=104))],
    "invalid_json": lambda s: [b"not json\n"],
    "invalid_utf8": lambda s: [b"\xff\xfe\n"],
    "empty_record": lambda s: [b"\n"],
}


def foreign_event(session):
    nested = event(frame_id=102, provenance="game_api", session_id=session)
    return line(native(event_id=1, frame_id=102, session_id=session, event=nested))


@pytest.mark.parametrize("name", sorted(BAD_STREAMS))
def test_invalid_receipts_close_the_peer_and_keep_the_cursor(sim, name):
    def build(s):
        return [first(s), *BAD_STREAMS[name](s)]

    with NativeStepClient(NATIVE) as client:
        s, cursor = connect(client, sim, build)
        client.receive_active()
        with pytest.raises(EpisodeFault):
            client.receive_receipt(command(session_id=s), base(s), cursor)
        assert_closed(client, cursor)


def test_disconnect_mid_record_faults(sim):
    def build(s):
        return [first(s), a(s)[:30], lambda conn: conn.close()]

    with NativeStepClient(NATIVE) as client:
        s, cursor = connect(client, sim, build, hold=False)
        client.receive_active()
        with pytest.raises(EpisodeFault):
            client.receive_receipt(command(session_id=s), base(s), cursor)
        assert_closed(client, cursor)


def test_preconditions_fault_and_close(sim):
    cases = [
        lambda s: (command(session_id=s, sequence=2), base(s)),
        lambda s: (command(session_id=s, frame_id=101), base(s, 101)),
        lambda s: (command(session_id=OTHER), base(OTHER)),
        lambda s: (command(session_id=s, game_epoch=2), base(s, 100)),
    ]
    for make in cases:
        with NativeStepClient(NATIVE) as client:
            s, cursor = connect(client, sim, lambda s: [first(s)])
            client.receive_active()
            with pytest.raises(EpisodeFault):
                client.receive_receipt(*make(s), cursor)
            assert client._peer is None


def test_receipt_needs_peer_and_a_prior_active_snapshot(sim):
    with NativeStepClient(NATIVE) as client:
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive_receipt(command(), base(command().session_id), None)
        s, cursor = connect(client, sim, lambda s: [])
        with pytest.raises(EpisodeFault):
            client.receive_receipt(command(session_id=s), base(s), cursor)
        assert client._peer is None


def test_same_listener_reconnect_resets_the_receipt_sequence(sim):
    def build(s):
        return [first(s), a(s) + d(s)]

    with NativeStepClient(NATIVE) as client:
        s, cursor = connect(client, sim, build)
        client.receive_active()
        client.receive_receipt(command(session_id=s), base(s), cursor)
        s2, cursor2 = connect(client, sim, build)  # accept() closes the earlier peer
        assert s2 != s and client._receipts == 0
        client.receive_active()
        assert client.receive_receipt(command(session_id=s2), base(s2), cursor2).events == ()
        client.release()


def test_sender_operations_stay_unsupported(sim):
    with NativeStepClient(NATIVE) as client:
        connect(client, sim, lambda s: [first(s)])
        with pytest.raises(UnsupportedNativeOperation):
            client.step()
        assert client._peer is None


def guarded(callback):
    cursor = NativeEventCursor(command().session_id, 1)
    return (
        NativeReceiptAssembler(
            command(), baseline(), cursor, oracle_kinds=KINDS, before_commit=callback
        ),
        cursor,
    )


def test_guard_runs_once_after_validation_and_before_the_cursor_advances():
    seen = []
    cursor = NativeEventCursor(command().session_id, 1)
    asm = NativeReceiptAssembler(
        command(),
        baseline(),
        cursor,
        oracle_kinds=KINDS,
        before_commit=lambda: seen.append(cursor.last_id),
    )
    ev = test_native_receipts.ev
    for raw in (wire(test_native_protocol.ack()), ev(1, 102), ev(2, 103)):
        asm.feed(raw)
    assert asm.feed(test_native_receipts.done(last_event_id=2)) is not None
    assert seen == [0] and cursor.last_id == 2


def test_guard_is_not_called_for_malformed_receipts():
    seen = []
    asm, cursor = guarded(lambda: seen.append(1))
    asm.feed(wire(test_native_protocol.ack()))
    with pytest.raises(ProtocolError):
        asm.feed(test_native_receipts.done(last_event_id=1))  # watermark mismatch
    assert seen == [] and cursor.last_id == 0


def test_guard_error_leaves_the_cursor_and_fails_the_assembler():
    def late():
        raise BridgeTimeout("late")

    asm, cursor = guarded(late)
    feeds = (wire(test_native_protocol.ack()), test_native_receipts.ev(1, 102))
    for raw in feeds:
        asm.feed(raw)
    with pytest.raises(BridgeTimeout):
        asm.feed(test_native_receipts.done(last_event_id=1))
    assert cursor.last_id == 0
    with pytest.raises(ProtocolError):
        asm.feed(wire(test_native_protocol.ack()))


def test_guard_induced_external_cursor_mutation_is_detected():
    cursor = NativeEventCursor(command().session_id, 1)

    def mutate():
        cursor.take(native(event_id=1, frame_id=50), 40, 60)

    asm = NativeReceiptAssembler(
        command(), baseline(), cursor, oracle_kinds=KINDS, before_commit=mutate
    )
    asm.feed(wire(test_native_protocol.ack()))
    asm.feed(test_native_receipts.ev(1, 102))
    with pytest.raises(ProtocolError, match="cursor changed"):
        asm.feed(test_native_receipts.done(last_event_id=1))
