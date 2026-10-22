"""OFFLINE launch guards and simulated peers; no Isaac executable is run."""

import json
import socket
import threading
import time
from unittest.mock import Mock

import pytest
from test_observer import ack, record, snapshot

from isaac_threrisaifuture import launcher
from isaac_threrisaifuture.observation import BridgeError, ProtocolError
from isaac_threrisaifuture.observer_client import ObservationClient, ObserverConfig


@pytest.fixture
def installation(tmp_path, monkeypatch):
    game = tmp_path / "game"
    project = tmp_path / "project"
    deployed = game / launcher.MOD_DIRECTORY
    source = project / "mod/observer"
    deployed.mkdir(parents=True)
    source.mkdir(parents=True)
    (game / "isaac-ng.exe").write_bytes(b"not executable; offline fixture only")
    for name in ("main.lua", "metadata.xml"):
        (deployed / name).write_text("fixture", encoding="utf-8")
        (source / name).write_text("fixture", encoding="utf-8")
    monkeypatch.setattr(launcher, "game_running", lambda: False)
    return game, project


@pytest.mark.parametrize("invalid", [0, -1, True, 100001])
def test_sample_budget_rejected(invalid):
    with pytest.raises(ValueError):
        launcher.LaunchOptions(samples=invalid)


@pytest.mark.parametrize("invalid", [0, -1, float("nan"), float("inf"), 3601])
def test_duration_budget_rejected(invalid):
    with pytest.raises(ValueError):
        launcher.LaunchOptions(duration=invalid)


@pytest.mark.parametrize("invalid", [-1, 11, True])
def test_reconnect_budget_rejected(invalid):
    with pytest.raises(ValueError):
        launcher.LaunchOptions(reconnects=invalid)


def test_refuses_existing_game_without_writes(installation, monkeypatch):
    game, project = installation
    monkeypatch.setattr(launcher, "game_running", lambda: True)
    popen = Mock()
    monkeypatch.setattr(launcher, "request_steam_launch", popen)
    with pytest.raises(ValueError, match="already running"):
        launcher.observe_game(game, launcher.LaunchOptions(), project)
    popen.assert_not_called()
    assert not (project / "runs").exists()


@pytest.mark.parametrize("fault", ["missing", "different"])
def test_refuses_unreviewed_deployment(installation, monkeypatch, fault):
    game, project = installation
    deployed = game / launcher.MOD_DIRECTORY / "main.lua"
    if fault == "missing":
        deployed.unlink()
    else:
        deployed.write_text("other version", encoding="utf-8")
    popen = Mock()
    monkeypatch.setattr(launcher, "request_steam_launch", popen)
    with pytest.raises(ValueError, match="Observer artifact"):
        launcher.observe_game(game, launcher.LaunchOptions(), project)
    popen.assert_not_called()
    assert not (project / "runs").exists()


def test_library_discovery_uses_vdf_paths_only(tmp_path):
    (tmp_path / "steamapps").mkdir()
    second = str(tmp_path / "second").replace("\\", "\\\\")
    (tmp_path / "steamapps/libraryfolders.vdf").write_text(
        f'"libraryfolders"\n{{\n "1"\n {{\n "path" "{second}"\n }}\n}}', encoding="utf-8"
    )
    assert launcher.library_paths(tmp_path) == [tmp_path, tmp_path / "second"]


def test_bind_failure_does_not_launch_game(installation, monkeypatch):
    game, project = installation
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        config = ObserverConfig(port=occupied.getsockname()[1])
        monkeypatch.setattr(launcher, "ObservationClient", lambda _: ObservationClient(config))
        popen = Mock()
        monkeypatch.setattr(launcher, "request_steam_launch", popen)
        with pytest.raises(BridgeError, match="Cannot bind"):
            launcher.observe_game(game, launcher.LaunchOptions(), project)
        popen.assert_not_called()


def test_game_appearing_after_preflight_cancels_launch(installation, monkeypatch):
    game, project = installation
    client = ObservationClient(ObserverConfig(port=0))
    monkeypatch.setattr(launcher, "ObservationClient", lambda _: client)
    monkeypatch.setattr(launcher, "game_running", Mock(side_effect=[False, True]))
    popen = Mock()
    monkeypatch.setattr(launcher, "request_steam_launch", popen)
    with pytest.raises(ValueError, match="appeared"):
        launcher.observe_game(game, launcher.LaunchOptions(), project)
    popen.assert_not_called()
    with pytest.raises(BridgeError, match="closed"):
        _ = client.address


def test_listener_precedes_launch_and_budget_closes_it(installation, monkeypatch):
    game, project = installation
    client = ObservationClient(ObserverConfig(port=0))
    monkeypatch.setattr(launcher, "ObservationClient", lambda _: client)
    errors = []
    threads = []
    process = Mock(pid=123)

    def fake_launch():
        address = client.address  # Raises unless the real listener is already bound.

        def peer():
            try:
                with socket.create_connection(address, timeout=2) as conn:
                    with conn.makefile("rb") as stream:
                        session = json.loads(stream.readline())["session_id"]
                        conn.sendall(record(ack(session)) + record(snapshot(session)))
                        assert stream.read(1) == b""  # Sample budget closes the real peer.
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=peer)
        threads.append(thread)
        thread.start()
        return process

    monkeypatch.setattr(launcher, "request_steam_launch", fake_launch)
    run = launcher.observe_game(game, launcher.LaunchOptions(samples=1), project)
    for thread in threads:
        thread.join(timeout=4)
        assert not thread.is_alive()
    assert not errors
    events = [
        json.loads(line)["event"] for line in (run / "observer.jsonl").read_text().splitlines()
    ]
    ready = next(
        json.loads(line)["data"]
        for line in (run / "observer.jsonl").read_text().splitlines()
        if json.loads(line)["event"] == "bridge_ready"
    )
    assert ready["save_slot_verified"] is False
    assert ready["requested_save"] == 2
    assert ready["session"]
    assert events == [
        "configuration",
        "listening",
        "launch_requested",
        "waiting_for_run",
        "handshake",
        "bridge_ready",
        "snapshot",
        "progress",
        "completed",
    ]
    process.kill.assert_not_called()
    process.terminate.assert_not_called()
    with pytest.raises(BridgeError, match="closed"):
        _ = client.address


@pytest.mark.parametrize("failure", [KeyboardInterrupt(), OSError("launch failed")])
def test_launch_interruption_closes_listener(installation, monkeypatch, failure):
    game, project = installation
    client = ObservationClient(ObserverConfig(port=0))
    monkeypatch.setattr(launcher, "ObservationClient", lambda _: client)
    monkeypatch.setattr(launcher, "request_steam_launch", Mock(side_effect=failure))
    with pytest.raises(type(failure)):
        launcher.observe_game(game, launcher.LaunchOptions(), project)
    with pytest.raises(BridgeError, match="closed"):
        _ = client.address


def test_total_deadline_without_peer_closes_listener(installation, monkeypatch):
    game, project = installation
    client = ObservationClient(ObserverConfig(port=0))
    monkeypatch.setattr(launcher, "ObservationClient", lambda _: client)
    monkeypatch.setattr(launcher, "request_steam_launch", lambda: None)
    with pytest.raises(BridgeError, match="deadline"):
        launcher.observe_game(game, launcher.LaunchOptions(duration=0.05), project)
    with pytest.raises(BridgeError, match="closed"):
        _ = client.address


def test_two_simulated_runs_reconnect_with_new_identity(tmp_path):
    errors, sessions = [], []
    with ObservationClient(ObserverConfig(port=0)) as client:
        address = client.address

        def peer():
            try:
                for frame in (100, 1):
                    with socket.create_connection(address, timeout=2) as conn:
                        with conn.makefile("rb") as stream:
                            session = json.loads(stream.readline())["session_id"]
                            sessions.append(session)
                            conn.sendall(
                                record(ack(session)) + record(snapshot(session, frame_id=frame))
                            )
                            if frame == 1:
                                assert stream.read(1) == b""
            except Exception as exc:
                errors.append(exc)

        thread = threading.Thread(target=peer)
        thread.start()
        try:
            with launcher.EventLog(tmp_path / "events.jsonl") as log:
                launcher.observe_sessions(
                    client, launcher.LaunchOptions(samples=2), time.monotonic() + 5, log
                )
        finally:
            client.close()
            thread.join(timeout=4)
    assert not thread.is_alive()
    assert not errors
    assert len(set(sessions)) == 2
    events = [json.loads(line) for line in (tmp_path / "events.jsonl").read_text().splitlines()]
    assert sum(e["event"] == "handshake" for e in events) == 2
    retry = next(e for e in events if e["event"] == "reconnecting")
    assert retry["data"]["outcome"] == "unknown"
    assert events[-1]["event"] == "completed"


@pytest.mark.parametrize(
    "error, expected_attempts", [(BridgeError("closed"), 3), (ProtocolError("bad"), 1)]
)
def test_retry_budget_exhaustion_and_protocol_failure(
    tmp_path, monkeypatch, error, expected_attempts
):
    with ObservationClient(ObserverConfig(port=0)) as client:
        accept = Mock(side_effect=error)
        monkeypatch.setattr(client, "accept", accept)
        with launcher.EventLog(tmp_path / "fault.jsonl") as log:
            with pytest.raises(type(error)):
                launcher.observe_sessions(
                    client, launcher.LaunchOptions(reconnects=2), time.monotonic() + 5, log
                )
        assert accept.call_count == expected_attempts


def test_steam_dispatch_preserves_existing_launch_options(monkeypatch):
    start = Mock()
    monkeypatch.setattr(launcher.os, "startfile", start, raising=False)
    launcher.request_steam_launch()
    start.assert_called_once_with("steam://rungameid/250900")


def test_handshake_without_snapshot_never_reports_ready(tmp_path, monkeypatch):
    with ObservationClient(ObserverConfig(port=0)) as client:
        monkeypatch.setattr(client, "accept", lambda: Mock(model_dump=lambda **_: {}))
        monkeypatch.setattr(client, "receive", Mock(side_effect=BridgeError("no snapshot")))
        path = tmp_path / "events.jsonl"
        with launcher.EventLog(path) as log:
            with pytest.raises(BridgeError, match="no snapshot"):
                launcher.observe_sessions(
                    client, launcher.LaunchOptions(reconnects=0), time.monotonic() + 1, log
                )
    assert "bridge_ready" not in path.read_text()


def test_automatic_menu_failure_closes_listener_before_observation(installation, monkeypatch):
    from isaac_threrisaifuture import windows_menu
    from isaac_threrisaifuture.menu_entry import MenuEntryError

    game, project = installation
    client = ObservationClient(ObserverConfig(port=0))
    monkeypatch.setattr(launcher, "ObservationClient", lambda _: client)
    monkeypatch.setattr(launcher, "request_steam_launch", lambda: None)
    monkeypatch.setattr(windows_menu, "WindowsMenu", Mock())
    monkeypatch.setattr(launcher, "continue_file2", Mock(side_effect=MenuEntryError("no focus")))
    observe = Mock()
    monkeypatch.setattr(launcher, "observe_sessions", observe)
    with pytest.raises(MenuEntryError, match="no focus"):
        launcher.observe_game(
            game,
            launcher.LaunchOptions(continue_file2=True),
            project,
            game_log=project / "native-log.txt",
        )
    observe.assert_not_called()
    with pytest.raises(BridgeError, match="closed"):
        _ = client.address


def test_new_run_and_continue_are_mutually_exclusive():
    with pytest.raises(ValueError, match="mutually exclusive"):
        launcher.LaunchOptions(continue_file2=True, new_run_file2=True)


@pytest.mark.parametrize("character", [0, 1])
def test_new_run_waits_for_active_isaac_and_refuses_other_character(
    tmp_path, monkeypatch, character
):
    from isaac_threrisaifuture.observation import Snapshot

    initial = snapshot(
        "a" * 32,
        status="unavailable",
        reason="not_in_game",
        frame_id=None,
        room=None,
        player=None,
    )
    active = snapshot("a" * 32, sequence=2)
    active["player"]["character_type"] = character
    client = Mock()
    client.accept.return_value = Mock(model_dump=lambda **_: {})
    client.receive.side_effect = [Snapshot.model_validate(initial), Snapshot.model_validate(active)]
    path = tmp_path / "events.jsonl"
    with launcher.EventLog(path) as log:
        if character == 0:
            launcher.observe_sessions(
                client,
                launcher.LaunchOptions(samples=1, new_run_file2=True),
                time.monotonic() + 5,
                log,
            )
        else:
            with pytest.raises(ValueError, match="not Isaac"):
                launcher.observe_sessions(
                    client,
                    launcher.LaunchOptions(samples=1, new_run_file2=True),
                    time.monotonic() + 5,
                    log,
                )
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert events[1]["event"] == "waiting_for_active_isaac"
    ready = [entry for entry in events if entry["event"] == "bridge_ready"]
    if character == 0:
        assert ready[0]["data"]["character_verified"] == 0
        assert ready[0]["data"]["slot_evidence"] == "native_new_log"
        assert events[-1]["data"]["samples"] == 1
    else:
        assert not ready
