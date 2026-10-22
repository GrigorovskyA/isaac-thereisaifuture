"""Bounded diagnostic and per-kind oracle negotiation against fake peers; no Isaac acceptance."""

import json
import socket
import threading
from pathlib import Path

import pytest
from test_entity_transport import entity_snapshot
from test_observer import ack, record, snapshot

from isaac_threrisaifuture.entities import EntitySnapshot
from isaac_threrisaifuture.observation import CAPABILITIES, BridgeError, ProtocolError, Snapshot
from isaac_threrisaifuture.observer_client import (
    DEATH_RESTART_CAPABILITY,
    LIVE_LOOP_CAPABILITIES,
    NATIVE_EPISODE_CAPABILITY,
    ORACLE_KINDS,
    ObservationClient,
    ObserverConfig,
    oracle_kind_capability,
)

JOIN_SECONDS = 3


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


@pytest.fixture
def peers():
    sim = SimulatedPeers()
    try:
        yield sim
    finally:
        sim.finish()


def test_entity_opt_in_requests_capability(peers):
    config = ObserverConfig(port=0, entity_observations=True)
    with ObservationClient(config) as client:
        peers.start(client.address, peer("entity_observation_v1", build=entity_snapshot))
        client.accept()
        assert isinstance(client.receive(), EntitySnapshot)
    assert peers.hellos[0]["required_capabilities"] == [*CAPABILITIES, "entity_observation_v1"]


def test_default_attach_does_not_request_entities_even_when_advertised(peers):
    with ObservationClient(ObserverConfig(port=0)) as client:
        peers.start(client.address, peer("entity_observation_v1"))
        client.accept()
        assert isinstance(client.receive(), Snapshot)
    assert peers.hellos[0]["required_capabilities"] == list(CAPABILITIES)


def test_old_peer_fails_without_fallback_or_reusable_socket(peers):
    with ObservationClient(ObserverConfig(port=0, entity_observations=True)) as client:
        peers.start(client.address, peer())
        with pytest.raises(ProtocolError, match="capabilities"):
            client.accept()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive()
    assert len(peers.hellos) == 1


def test_second_explicit_attach_cannot_silently_reuse_old_capability(peers):
    with ObservationClient(ObserverConfig(port=0, entity_observations=True)) as client:
        peers.start(client.address, peer("entity_observation_v1", build=entity_snapshot))
        first = client.accept().session_id
        client.receive()
        client.close_peer()
        peers.start(client.address, peer())
        with pytest.raises(ProtocolError, match="capabilities"):
            client.accept()
    assert peers.hellos[1]["session_id"] != first


# Per-kind OracleEvent negotiation. Handshake only: a peer advertising a name proves neither
# producer coverage nor event delivery, and the current producer advertises none of these names.
KIND_CAPABILITIES = [oracle_kind_capability(kind) for kind in ORACLE_KINDS]
OTHER_ADVERTISED = (*CAPABILITIES, *LIVE_LOOP_CAPABILITIES)
# Everything beyond the three base names in a worst-case HelloAck.
FULL_EXTRAS = [
    *LIVE_LOOP_CAPABILITIES,
    NATIVE_EPISODE_CAPABILITY,
    *KIND_CAPABILITIES,
]


def kind_config(*kinds: str) -> ObserverConfig:
    return ObserverConfig(
        port=0,
        native_episode_steps=True,
        native_oracle_kinds=kinds,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize("kind", ORACLE_KINDS)
def test_single_kind_request_adds_exact_name_after_native_transport(peers, kind):
    name = f"oracle_{kind}_v1"
    assert oracle_kind_capability(kind) == name
    with ObservationClient(kind_config(kind)) as client:
        peers.start(client.address, peer(NATIVE_EPISODE_CAPABILITY, name, build=entity_snapshot))
        client.accept()
        assert isinstance(client.receive(), EntitySnapshot)
    required = peers.hellos[0]["required_capabilities"]
    assert required == [*CAPABILITIES, NATIVE_EPISODE_CAPABILITY, name]


def test_only_requested_kinds_are_required_in_request_order(peers):
    with ObservationClient(kind_config("player_died", "enemy_spawned")) as client:
        peers.start(client.address, peer(NATIVE_EPISODE_CAPABILITY, *KIND_CAPABILITIES))
        client.accept()
    assert peers.hellos[0]["required_capabilities"] == [
        *CAPABILITIES,
        NATIVE_EPISODE_CAPABILITY,
        "oracle_player_died_v1",
        "oracle_enemy_spawned_v1",
    ]


def test_all_kinds_and_native_transport_fill_fifteen_ack_entries(peers):
    assert len(OTHER_ADVERTISED) == len(set(OTHER_ADVERTISED)) == 7
    lua = (Path(__file__).parents[1] / "mod/observer/main.lua").read_text(encoding="utf-8")
    assert all(f'"{name}"' in lua for name in OTHER_ADVERTISED)
    with ObservationClient(kind_config(*ORACLE_KINDS)) as client:
        peers.start(client.address, peer(*FULL_EXTRAS, build=entity_snapshot))
        ack = client.accept()
        assert isinstance(client.receive(), EntitySnapshot)
    assert len(ack.capabilities) == 15
    assert set(ack.capabilities) == {
        *OTHER_ADVERTISED,
        NATIVE_EPISODE_CAPABILITY,
        *KIND_CAPABILITIES,
    }
    assert peers.hellos[0]["required_capabilities"] == [
        *CAPABILITIES,
        NATIVE_EPISODE_CAPABILITY,
        *KIND_CAPABILITIES,
    ]


def test_seventeenth_ack_entry_is_rejected_even_when_every_required_name_is_present(peers):
    with ObservationClient(kind_config(*ORACLE_KINDS)) as client:
        peers.start(client.address, peer(*FULL_EXTRAS, "unrelated_v1", "unrelated_v2"))
        with pytest.raises(ProtocolError, match="HelloAck"):
            client.accept()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive()


EXISTING_MODES = [
    ({}, []),
    ({"safe_actions": True}, ["safe_actions_v1"]),
    ({"restart_after_death": True}, [DEATH_RESTART_CAPABILITY]),
    ({"entity_observations": True}, ["entity_observation_v1"]),
    ({"native_episode_steps": True}, [NATIVE_EPISODE_CAPABILITY]),
    ({"live_loop": True}, list(LIVE_LOOP_CAPABILITIES)),
]


@pytest.mark.parametrize(("options", "extra"), EXISTING_MODES)
def test_existing_modes_never_request_kinds_even_when_every_name_is_advertised(
    peers, options, extra
):
    config = ObserverConfig(port=0, **options)
    assert config.native_oracle_kinds is None
    with ObservationClient(config) as client:
        peers.start(client.address, peer(*FULL_EXTRAS))
        client.accept()
    assert peers.hellos[0]["required_capabilities"] == [*CAPABILITIES, *extra]


def test_positional_construction_of_existing_fields_is_unchanged():
    positional = ObserverConfig("127.0.0.1", 0, 1.0, 2.0, 3.0, False, False, False, True, False)
    keyword = ObserverConfig(
        port=0,
        accept_timeout=1.0,
        handshake_timeout=2.0,
        message_timeout=3.0,
        native_episode_steps=True,
    )
    assert positional == keyword
    assert positional.native_oracle_kinds is None


@pytest.mark.parametrize("missing", ORACLE_KINDS)
def test_partial_peer_missing_a_requested_kind_fails_before_data(peers, missing):
    names = [name for name in KIND_CAPABILITIES if name != oracle_kind_capability(missing)]
    with ObservationClient(kind_config(*ORACLE_KINDS)) as client:
        peers.start(client.address, peer(NATIVE_EPISODE_CAPABILITY, *names, build=entity_snapshot))
        with pytest.raises(ProtocolError, match="capabilities"):
            client.accept()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive()
    assert len(peers.hellos[0]["required_capabilities"]) == len(CAPABILITIES) + 1 + 7


@pytest.mark.parametrize(
    "advertised",
    [
        pytest.param([], id="old-peer"),
        pytest.param([NATIVE_EPISODE_CAPABILITY], id="transport-without-kinds"),
        pytest.param(["oracle_enemy_killed_v1"], id="kind-without-transport"),
        pytest.param(
            [
                NATIVE_EPISODE_CAPABILITY,
                "oracle_enemy_killed_v2",
                "oracle_enemy_killed",
                "oracle_enemy_damaged_v1",
                "oracle_all_v1",
            ],
            id="no-version-prefix-or-aggregate-fallback",
        ),
    ],
)
def test_peer_without_exact_name_and_transport_is_rejected_without_fallback(peers, advertised):
    with ObservationClient(kind_config("enemy_killed")) as client:
        peers.start(client.address, peer(*advertised, build=entity_snapshot))
        with pytest.raises(ProtocolError, match="capabilities"):
            client.accept()
        with pytest.raises(BridgeError, match="No negotiated peer"):
            client.receive()
    assert peers.hellos[0]["required_capabilities"][-2:] == [
        NATIVE_EPISODE_CAPABILITY,
        "oracle_enemy_killed_v1",
    ]


def test_reconnect_cannot_reuse_a_kind_the_next_handshake_omits(peers):
    with ObservationClient(kind_config("enemy_killed")) as client:
        name = "oracle_enemy_killed_v1"
        peers.start(client.address, peer(NATIVE_EPISODE_CAPABILITY, name))
        first = client.accept().session_id
        client.close_peer()
        peers.start(client.address, peer(NATIVE_EPISODE_CAPABILITY))
        with pytest.raises(ProtocolError, match="capabilities"):
            client.accept()
    assert peers.hellos[1]["session_id"] != first
    assert peers.hellos[1]["required_capabilities"] == peers.hellos[0]["required_capabilities"]


@pytest.mark.parametrize(
    "kinds",
    [(), [], ["enemy_killed"], {"enemy_killed"}, "enemy_killed", frozenset({"enemy_killed"})],
)
def test_kinds_must_be_a_nonempty_tuple(kinds):
    with pytest.raises(ValueError, match="nonempty tuple"):
        ObserverConfig(native_episode_steps=True, native_oracle_kinds=kinds)


class _StrSubclass(str):
    pass


@pytest.mark.parametrize(
    "kinds",
    [
        ("enemy_healed",),
        ("Enemy_Killed",),
        ("oracle_enemy_killed_v1",),
        ("enemy_killed", "bogus"),
        ("",),
        (None,),
        (1,),
        (("enemy_killed",),),
        (["enemy_killed"],),
        (_StrSubclass("enemy_killed"),),
    ],
)
def test_unknown_or_non_string_kinds_are_rejected(kinds):
    with pytest.raises(ValueError, match="Unknown native oracle kind"):
        ObserverConfig(native_episode_steps=True, native_oracle_kinds=kinds)


@pytest.mark.parametrize(
    "kinds",
    [("enemy_killed", "enemy_killed"), (*ORACLE_KINDS, "player_died")],
)
def test_duplicate_kinds_are_rejected(kinds):
    with pytest.raises(ValueError, match="Duplicate native oracle kind"):
        ObserverConfig(native_episode_steps=True, native_oracle_kinds=kinds)


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"live_loop": True},
        {"safe_actions": True},
        {"restart_after_death": True},
        {"entity_observations": True},
    ],
)
def test_kinds_without_native_episode_mode_are_rejected_locally(options):
    with pytest.raises(ValueError, match="require native episode mode"):
        ObserverConfig(native_oracle_kinds=("enemy_killed",), **options)


@pytest.mark.parametrize(
    "option",
    ["live_loop", "safe_actions", "restart_after_death", "entity_observations"],
)
def test_kinds_cannot_combine_native_mode_with_other_opt_ins(option):
    with pytest.raises(ValueError):
        ObserverConfig(
            native_episode_steps=True, native_oracle_kinds=("enemy_killed",), **{option: True}
        )
