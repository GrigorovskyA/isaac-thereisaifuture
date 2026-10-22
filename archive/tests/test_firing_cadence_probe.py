"""Offline safety tests for the fixed stationary cadence probe."""

import io
import json
from dataclasses import replace
from time import time
from types import SimpleNamespace

import pytest
from test_observer import ack, record, snapshot

import isaac_threrisaifuture.firing_cadence_probe as probe
from isaac_threrisaifuture.actions import ActionApproval
from isaac_threrisaifuture.observation import BridgeTimeout, Health, ProtocolError

pytest_plugins = ["test_observer"]


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def monotonic(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeAck:
    def __init__(self, session_id: str, sequence: int, frame_id: int, kind: str) -> None:
        self.session_id = session_id
        self.sequence = sequence
        self.frame_id = frame_id
        self.kind = kind
        self.game_epoch = 1
        self.room_visit = 1
        self.status = "accepted"

    def model_dump(self, *, mode: str) -> dict[str, object]:
        assert mode == "json"
        return {
            "session_id": self.session_id,
            "sequence": self.sequence,
            "frame_id": self.frame_id,
            "kind": self.kind,
            "game_epoch": self.game_epoch,
            "room_visit": self.room_visit,
            "status": self.status,
        }


class FakeClient:
    def __init__(self, config: object, approval: ActionApproval, clock: FakeClock) -> None:
        self.config = config
        self.approval = approval
        self.clock = clock
        self._peer: object | None = None
        self.frame = 100
        self.room = 1
        self.health = Health(
            red_half_hearts=4,
            max_red_half_hearts=8,
            soul_half_hearts=0,
            bone_containers=0,
        )
        self.character_type = 0
        self.x = 320.0
        self.y = 240.0
        self.receive_count = 0
        self.accept_count = 0
        self.handshake_modes: list[tuple[bool, bool]] = []
        self.preflight_snapshot = empty_room_snapshot()
        self.change_room_at: int | None = None
        self.change_position_at: int | None = None
        self.change_health_at: int | None = None
        self.stall = False
        self.commands: list[dict[str, object]] = []
        self.closed = False

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *_args: object) -> None:
        self._peer = None
        self.closed = True

    def accept(self) -> SimpleNamespace:
        self._peer = object()
        self.accept_count += 1
        self.handshake_modes.append((self.config.entity_observations, self.config.safe_actions))
        return SimpleNamespace(session_id="a" * 32)

    def close_peer(self) -> None:
        self._peer = None

    def receive(self) -> object:
        if self.config.entity_observations:
            self.clock.advance(0.01)
            return self.preflight_snapshot
        self.receive_count += 1
        self.clock.advance(0.1 if self.stall else 0.01)
        if not self.stall:
            self.frame += 1
        if self.change_room_at == self.receive_count:
            self.room += 1
        if self.change_position_at == self.receive_count:
            self.x += 10
        if self.change_health_at == self.receive_count:
            self.health = Health(
                red_half_hearts=2,
                max_red_half_hearts=8,
                soul_half_hearts=0,
                bone_containers=0,
            )
        return SimpleNamespace(
            status="active",
            frame_id=self.frame,
            session_id="a" * 32,
            game_epoch=1,
            room=SimpleNamespace(visit_id=self.room),
            player=SimpleNamespace(
                health=self.health,
                character_type=self.character_type,
                position=SimpleNamespace(x=self.x, y=self.y),
            ),
        )

    def command(self, kind: str, *, move: str, shoot: str, frames: int) -> FakeAck:
        self.commands.append({"kind": kind, "move": move, "shoot": shoot, "frames": frames})
        return FakeAck("a" * 32, len(self.commands), self.frame, kind)


def empty_room_snapshot(
    *,
    status: str = "active",
    room_visit: int = 1,
    character_type: int = 0,
    x: float = 320.0,
    y: float = 240.0,
    entities: list[dict[str, object]] | None = None,
    overflow: dict[str, int] | None = None,
):
    from isaac_threrisaifuture.entities import EntitySnapshot

    health = {
        "red_half_hearts": 4,
        "max_red_half_hearts": 8,
        "soul_half_hearts": 0,
        "bone_containers": 0,
    }
    frame = {
        "type": "entity_frame",
        "observation_schema_version": 1,
        "provenance": "game_api",
        "session_id": "a" * 32,
        "game_epoch": 1,
        "room_visit": room_visit,
        "frame_id": 100,
        "player_position": {"x": x, "y": y},
        "player_velocity": {"x": 0, "y": 0},
        "health": health,
        "entities": entities or [],
        "source_overflow": overflow or {},
    }
    return EntitySnapshot.model_validate(
        {
            "type": "snapshot",
            "schema_version": 1,
            "session_id": "a" * 32,
            "sequence": 1,
            "game_epoch": 1,
            "frame_id": 100,
            "update_id": 100,
            "status": status,
            "reason": None,
            "room": {"visit_id": room_visit},
            "player": {
                "index": 0,
                "character_type": character_type,
                "position": {"x": x, "y": y},
                "health": health,
            },
            "entity_frame": frame,
        }
    )


def approval(**changes: object) -> ActionApproval:
    values: dict[str, object] = {
        "profile_id": "ordinary-test",
        "profile_mode": "ordinary_profile_exception",
        "expires_at": int(time()) + 600,
        "profile_evidence": "user-confirmed test profile",
        "slot_evidence": "manual file 2 selection",
        "runtime_authorization": "finite 30-second cadence comparison",
        "slot": 2,
        "game_epoch": 1,
    }
    values.update(changes)
    return ActionApproval.model_validate(values)


def install_fake(monkeypatch: pytest.MonkeyPatch, clock: FakeClock) -> FakeClient:
    client = FakeClient(None, approval(), clock)
    monkeypatch.setattr(probe, "monotonic", clock.monotonic)
    monkeypatch.setattr(probe, "ActionClient", lambda config, _approval: _configure(client, config))
    return client


def _configure(client: FakeClient, config: object) -> FakeClient:
    client.config = replace(config, safe_actions=True)
    return client


def test_probe_is_exactly_stationary_bounded_and_releases(monkeypatch):
    clock = FakeClock()
    client = install_fake(monkeypatch, clock)
    output = io.StringIO()

    probe.run_firing_cadence_probe(approval(), output)

    actions = [command for command in client.commands if command["kind"] == "action"]
    assert [command["frames"] for command in actions] == [3] * 7 + [1] + [6] * 7
    assert all(command["move"] == "none" for command in client.commands)
    assert all(command["shoot"] == "right" for command in actions if command["frames"] != 1)
    assert client.commands[-1] == {
        "kind": "release",
        "move": "none",
        "shoot": "none",
        "frames": 0,
    }
    assert len(client.commands) == probe.MAX_COMMANDS
    assert client.handshake_modes == [(True, False), (False, True)]
    assert client.closed
    records = [json.loads(line) for line in output.getvalue().splitlines()]
    assert records[-1]["event"] == "completed"
    assert records[-1]["data"]["release"] == "explicit"
    assert sum(record["event"] == "sample_window" for record in records) == 14


def test_probe_stops_on_room_change_and_attempts_release(monkeypatch):
    clock = FakeClock()
    client = install_fake(monkeypatch, clock)
    client.change_room_at = 3

    with pytest.raises(ProtocolError, match="Room, epoch, session, health or position changed"):
        probe.run_firing_cadence_probe(approval(), io.StringIO())

    assert client.commands[-1]["kind"] == "release"
    assert all(command["move"] == "none" for command in client.commands)
    assert client.closed


def test_probe_stops_after_unexpected_player_displacement(monkeypatch):
    clock = FakeClock()
    client = install_fake(monkeypatch, clock)
    client.change_position_at = 3

    with pytest.raises(ProtocolError, match="health or position changed"):
        probe.run_firing_cadence_probe(approval(), io.StringIO())

    assert client.commands[-1]["kind"] == "release"
    assert all(command["move"] == "none" for command in client.commands)
    assert client.closed


def test_probe_stops_after_health_change_and_releases(monkeypatch):
    clock = FakeClock()
    client = install_fake(monkeypatch, clock)
    client.change_health_at = 3

    with pytest.raises(ProtocolError, match="health or position changed"):
        probe.run_firing_cadence_probe(approval(), io.StringIO())

    assert client.commands[-1]["kind"] == "release"
    assert client.closed


@pytest.mark.parametrize("field,value", [("character_type", 1), ("x", 80.0), ("y", 450.0)])
def test_probe_rejects_unapproved_character_or_room_position_before_actions(
    monkeypatch, field, value
):
    clock = FakeClock()
    client = install_fake(monkeypatch, clock)
    setattr(client, field, value)

    with pytest.raises(ProtocolError):
        probe.run_firing_cadence_probe(approval(), io.StringIO())

    assert client.commands == []
    assert client.closed


def test_probe_deadline_stops_a_stalled_frame_stream_and_closes(monkeypatch):
    clock = FakeClock()
    client = install_fake(monkeypatch, clock)
    client.stall = True

    with pytest.raises(BridgeTimeout, match="Firing probe deadline reached"):
        probe.run_firing_cadence_probe(approval(), io.StringIO())

    assert len(client.commands) <= probe.MAX_COMMANDS
    assert client.commands[0]["move"] == "none"
    assert client.closed


def test_probe_refuses_a_training_approval_before_connecting(monkeypatch):
    connected = False

    def unexpected_client(*_args: object) -> FakeClient:
        nonlocal connected
        connected = True
        raise AssertionError("No client may be created for training approval")

    monkeypatch.setattr(probe, "ActionClient", unexpected_client)
    with pytest.raises(ValueError, match="ordinary-profile file-2 approval"):
        probe.run_firing_cadence_probe(approval(profile_mode="isolated"), io.StringIO())
    assert not connected


@pytest.mark.parametrize(
    "snapshot, message",
    [
        (
            empty_room_snapshot(
                entities=[
                    {
                        "kind": "enemy",
                        "entity_id": 4,
                        "spawn_generation": 0,
                        "position": {"x": 20, "y": 0},
                    }
                ]
            ),
            "empty room",
        ),
        (
            empty_room_snapshot(
                entities=[
                    {
                        "kind": "projectile",
                        "entity_id": 5,
                        "spawn_generation": 0,
                        "position": {"x": 20, "y": 0},
                    }
                ]
            ),
            "empty room",
        ),
        (empty_room_snapshot(overflow={"enemy": 1}), "overflow prevents proving"),
        (empty_room_snapshot(status="paused"), "approved active file-2"),
        (empty_room_snapshot(character_type=1), "approved active file-2"),
    ],
)
def test_preflight_requires_active_empty_room_before_action_commands(
    monkeypatch, snapshot, message
):
    clock = FakeClock()
    monkeypatch.setattr(probe, "monotonic", clock.monotonic)
    client = FakeClient(None, approval(), clock)
    client.preflight_snapshot = snapshot
    monkeypatch.setattr(probe, "ActionClient", lambda config, _approval: _configure(client, config))
    with pytest.raises(ProtocolError, match=message):
        probe.run_firing_cadence_probe(approval(), io.StringIO())
    assert client.commands == []
    assert client.accept_count == 1
    assert client.closed


def test_action_connection_must_match_preflight_room(monkeypatch):
    clock = FakeClock()
    client = install_fake(monkeypatch, clock)
    client.room = 2
    with pytest.raises(ProtocolError, match="Room, epoch, session, health or position changed"):
        probe.run_firing_cadence_probe(approval(), io.StringIO())
    assert client.commands == []
    assert client.closed


def test_real_action_client_reuses_one_listener_for_readonly_then_action_handshake(
    monkeypatch, peers
):
    real_action_client = probe.ActionClient
    real_config = probe.ObserverConfig
    sent_commands: list[dict[str, object]] = []
    handshake_modes: list[tuple[bool, bool]] = []

    class SocketProbeClient(real_action_client):
        def accept(self):
            mode = len(handshake_modes)
            handshake_modes.append((mode == 0, mode != 0))
            peers(self.address, readonly_peer if mode == 0 else action_peer)
            return super().accept()

    def configured_client(config, _approval):
        return SocketProbeClient(config, _approval)

    def make_snapshot(session: str, sequence: int, frame_id: int, *, entity: bool):
        health = {
            "red_half_hearts": 4,
            "max_red_half_hearts": 8,
            "soul_half_hearts": 0,
            "bone_containers": 0,
        }
        value = snapshot(
            session,
            sequence,
            frame_id=frame_id,
            update_id=frame_id,
            player={
                "index": 0,
                "character_type": 0,
                "position": {"x": 320.0, "y": 240.0},
                "health": health,
            },
        )
        if entity:
            value["entity_frame"] = {
                "type": "entity_frame",
                "observation_schema_version": 1,
                "provenance": "game_api",
                "session_id": session,
                "game_epoch": 1,
                "room_visit": 1,
                "frame_id": frame_id,
                "player_position": {"x": 320.0, "y": 240.0},
                "player_velocity": {"x": 0.0, "y": 0.0},
                "health": health,
                "entities": [],
                "source_overflow": {},
            }
        return value

    def readonly_peer(conn, session):
        hello_ack = ack(session)
        hello_ack["capabilities"].append("entity_observation_v1")
        conn.sendall(record(hello_ack) + record(make_snapshot(session, 1, 100, entity=True)))
        assert conn.recv(1) == b""

    def action_peer(conn, session):
        hello_ack = ack(session)
        hello_ack["capabilities"].append("safe_actions_v1")
        conn.sendall(record(hello_ack) + record(make_snapshot(session, 1, 100, entity=False)))
        with conn.makefile("rb") as stream:
            sequence = 1
            while True:
                raw = stream.readline()
                if not raw:
                    return
                command = json.loads(raw)
                sent_commands.append(command)
                command_ack = {
                    key: command[key]
                    for key in (
                        "protocol_version",
                        "session_id",
                        "sequence",
                        "game_epoch",
                        "room_visit",
                        "frame_id",
                        "kind",
                    )
                }
                command_ack.update(
                    type="command_ack",
                    status="accepted",
                )
                conn.sendall(record(command_ack))
                if command["kind"] == "action":
                    sequence += 1
                    conn.sendall(
                        record(
                            make_snapshot(
                                session,
                                sequence,
                                int(command["frame_id"]) + int(command["frames"]),
                                entity=False,
                            )
                        )
                    )

    monkeypatch.setattr(probe, "ObserverConfig", lambda **kwargs: real_config(port=0, **kwargs))
    monkeypatch.setattr(probe, "ActionClient", configured_client)
    output = io.StringIO()

    probe.run_firing_cadence_probe(approval(), output)

    assert handshake_modes == [(True, False), (False, True)]
    assert len(sent_commands) == probe.MAX_COMMANDS
    assert all(command["move"] == "none" for command in sent_commands)
    assert sent_commands[-1]["kind"] == "release"
