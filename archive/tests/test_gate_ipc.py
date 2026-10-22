"""Offline Windows sharing recovery, original deadlines, and failure cleanup."""

import json
import threading
import time
from types import SimpleNamespace

import pytest
from test_combat_gate import FakeClock, World, gate_events, gated

from isaac_threrisaifuture import combat_gate as ipc
from isaac_threrisaifuture.live import LiveBudgetExpired


def sharing(code=5):
    error = PermissionError("synthetic Windows sharing conflict")
    error.winerror = code
    return error


@pytest.fixture
def io_clock(monkeypatch):
    clock = SimpleNamespace(now=10.0, sleeps=[])

    def sleep(seconds):
        clock.sleeps.append(seconds)
        clock.now += seconds

    monkeypatch.setattr(ipc, "time", SimpleNamespace(monotonic=lambda: clock.now, sleep=sleep))
    return clock


@pytest.mark.parametrize("code", [5, 32])
def test_transient_sharing_recovers_without_changing_payload(monkeypatch, tmp_path, code):
    target = tmp_path / "request.json"
    target.write_text("old")
    replace = ipc.os.replace
    calls = []

    def transient(source, destination):
        calls.append((source, destination))
        if len(calls) < 3:
            assert target.read_text() == "old"
            raise sharing(code)
        return replace(source, destination)

    monkeypatch.setattr(ipc.os, "replace", transient)
    ipc._write_atomic(target, "complete new payload")
    assert target.read_text() == "complete new payload" and len(calls) == 3
    assert not list(tmp_path.glob("*.tmp"))


def test_persistent_sharing_preserves_first_error_and_old_file(io_clock, monkeypatch, tmp_path):
    target = tmp_path / "request.json"
    target.write_text("old")
    first = sharing()
    calls = []

    def locked(*args):
        calls.append(io_clock.now)
        raise first if len(calls) == 1 else sharing()

    monkeypatch.setattr(ipc.os, "replace", locked)
    with pytest.raises(PermissionError) as caught:
        ipc._write_atomic(target, "new")
    assert caught.value is first
    assert len(calls) <= 26 and io_clock.now <= 10.25
    assert target.read_text() == "old" and not list(tmp_path.glob("*.tmp"))


def test_retry_window_is_clipped_to_original_deadline(io_clock):
    calls = []

    def locked():
        calls.append(io_clock.now)
        raise sharing()

    with pytest.raises(LiveBudgetExpired):
        ipc._file_operation(locked, 10.025)
    assert calls and max(calls) < 10.025 and io_clock.now == 10.025
    assert sum(io_clock.sleeps) == pytest.approx(0.025)


def test_expired_deadline_does_no_work_except_one_final_cleanup_attempt(io_clock):
    calls = []
    with pytest.raises(LiveBudgetExpired):
        ipc._file_operation(lambda: calls.append("normal"), 10.0)
    assert calls == []
    ipc._file_operation(lambda: calls.append("cleanup"), 10.0, final_attempt=True)
    assert calls == ["cleanup"] and io_clock.sleeps == []
    with pytest.raises(LiveBudgetExpired):
        ipc._file_operation(lambda: (_ for _ in ()).throw(sharing()), 10.0, final_attempt=True)
    assert io_clock.sleeps == []


def test_non_sharing_error_is_not_retried(io_clock):
    first = OSError("disk failure")
    calls = []

    def failed():
        calls.append(1)
        raise first

    with pytest.raises(OSError) as caught:
        ipc._file_operation(failed)
    assert caught.value is first and calls == [1] and io_clock.sleeps == []


@pytest.mark.parametrize("platform, expected", [("win32", 3), ("darwin", 1)])
def test_crt_access_denial_is_retried_only_on_windows(io_clock, monkeypatch, platform, expected):
    monkeypatch.setattr(ipc, "sys", SimpleNamespace(platform=platform))
    calls = []

    def access():
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError(13, "CRT access conflict")
        return "complete"

    if platform == "win32":
        assert ipc._file_operation(access) == "complete"
    else:
        with pytest.raises(PermissionError):
            ipc._file_operation(access)
    assert len(calls) == expected


def test_frozen_clock_still_has_an_attempt_limit(io_clock, monkeypatch):
    monkeypatch.setattr(ipc.time, "sleep", lambda seconds: None)
    calls = []

    def locked():
        calls.append(1)
        raise sharing()

    with pytest.raises(PermissionError):
        ipc._file_operation(locked)
    assert len(calls) == 26 and io_clock.now == 10.0


def test_read_and_remove_recover_transient_sharing(monkeypatch, tmp_path):
    target = tmp_path / "ready.json"
    target.write_bytes(b"a" * (ipc.MAX_ACK_BYTES + 100))
    open_file, unlink = type(target).open, type(target).unlink
    reads, deletes = [], []

    def transient_open(path, *args, **kwargs):
        reads.append(1)
        if len(reads) == 1:
            raise sharing(32)
        return open_file(path, *args, **kwargs)

    def transient_unlink(path, *args, **kwargs):
        deletes.append(1)
        if len(deletes) == 1:
            raise sharing()
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(type(target), "open", transient_open)
    assert len(ipc._read(target)) == ipc.MAX_ACK_BYTES + 1
    monkeypatch.setattr(type(target), "unlink", transient_unlink)
    ipc._remove(target)
    assert reads == [1, 1] and deletes == [1, 1] and not target.exists()


def test_initial_request_failure_keeps_primary_error_and_closes(monkeypatch, tmp_path):
    world, records = World(), []
    env = gated(world, tmp_path, records=records)
    first = OSError("initial publication failed")
    calls = []
    releases = []
    release = env._release

    def watched_release():
        releases.append(1)
        release()

    monkeypatch.setattr(env, "_release", watched_release)

    def broken(*args, **kwargs):
        calls.append(1)
        raise first if len(calls) == 1 else OSError("stop publication failed")

    monkeypatch.setattr(ipc, "_write_atomic", broken)
    with pytest.raises(OSError) as caught:
        env.reset()
    assert caught.value is first and env.state == "stopped"
    assert releases == [1, 1] and world.action_count() == 0
    assert "stop publication failed" in ";".join(env.cleanup_errors)
    assert gate_events(records, "summary") and gate_events(records, "stopped")
    assert caught.value.__notes__
    env.close()
    assert world.closed


def test_stop_still_records_summary_when_ready_removal_fails(monkeypatch, tmp_path):
    world, records = World(), []
    env = gated(world, tmp_path, records=records)
    env._issue("test")
    original = ipc._remove

    def broken(path, *args, **kwargs):
        if path.name == ipc.READY_NAME:
            raise OSError("ready remains locked")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(ipc, "_remove", broken)
    env.close()
    assert world.closed and env.state == "stopped"
    assert gate_events(records, "summary")
    assert "ready remains locked" in ";".join(env.cleanup_errors)


def test_cleanup_logger_failure_does_not_mask_primary(monkeypatch, tmp_path):
    world = World()
    env = gated(world, tmp_path)
    first = OSError("primary publication failed")
    monkeypatch.setattr(ipc, "_write_atomic", lambda *a, **k: (_ for _ in ()).throw(first))
    env.record = lambda *a: (_ for _ in ()).throw(OSError("log unavailable"))
    with pytest.raises(OSError) as caught:
        env.reset()
    assert caught.value is first and any("log unavailable" in e for e in env.cleanup_errors)
    env.close()
    assert world.closed


def test_gate_retry_expiry_releases_and_never_accepts_readiness(monkeypatch, tmp_path):
    clock = FakeClock()
    clock.sleep = lambda seconds: setattr(clock, "now", clock.now + seconds)
    monkeypatch.setattr(ipc, "time", clock)
    world = World()
    env = gated(world, tmp_path, cap=0.025, deadline=clock.now + 10)
    releases = []
    release = env._release

    def watched_release():
        releases.append(1)
        release()

    monkeypatch.setattr(env, "_release", watched_release)
    monkeypatch.setattr(ipc.os, "replace", lambda *a: (_ for _ in ()).throw(sharing()))
    with pytest.raises(ipc.CombatGateExpired):
        env.reset()
    assert clock.now == pytest.approx(1000.025)
    assert env.stats.accepted == 0 and world.action_count() == 0 and env.state == "stopped"
    assert releases == [1, 1]
    env.close()


def test_real_short_reader_releases_in_time_for_atomic_publication(tmp_path):
    path = tmp_path / "request.json"
    path.write_text("old")
    opened, release = threading.Event(), threading.Event()
    errors = []

    def reader():
        try:
            with path.open("rb") as stream:
                opened.set()
                release.wait(0.03)
                assert stream.read() == b"old"
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=reader)
    thread.start()
    try:
        assert opened.wait(1)
        ipc._write_atomic(path, "new")
    finally:
        release.set()
        thread.join(1)
    assert not thread.is_alive() and not errors and path.read_text() == "new"


def test_real_concurrent_operator_and_writer_observe_complete_records(tmp_path):
    gate = tmp_path / "combat_gate"
    gate.mkdir()
    request = ipc.ReadinessRequest(
        request_id="a" * 32,
        handoff=1,
        state="waiting_for_operator",
        issued_at=time.time(),
        session_id="b" * 32,
        game_epoch=1,
        room_visit=1,
        eligibility="combat",
    )
    target = gate / ipc.REQUEST_NAME
    ipc._write_atomic(target, request.model_dump_json())
    stop, started = threading.Event(), threading.Event()
    errors, seen = [], []

    def operator():
        try:
            started.set()
            while not stop.is_set():
                value = ipc.ReadinessRequest.model_validate_json(ipc._read(target))
                seen.append(value.handoff)
                ipc.write_readiness(tmp_path)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=operator)
    thread.start()
    try:
        assert started.wait(1)
        for handoff in range(2, 52):
            ipc._write_atomic(
                target, request.model_copy(update={"handoff": handoff}).model_dump_json()
            )
    finally:
        stop.set()
        thread.join(2)
    assert not thread.is_alive() and not errors and seen
    assert json.loads(target.read_text())["handoff"] == 51
    ipc.ReadinessAck.model_validate_json(ipc._read(gate / ipc.READY_NAME))
    assert not list(gate.glob("*.tmp"))
