"""Stall watchdog, the restart command model and the live wiring, with fake clocks."""

import json

import numpy as np
import pytest
from test_live import SESSION, live

from isaac_threrisaifuture.actions import Command
from isaac_threrisaifuture.entities import OracleEvent
from isaac_threrisaifuture.live import (
    LIVE_SCENARIO,
    LiveBackend,
    LiveCommandAck,
    make_live_env,
)
from isaac_threrisaifuture.observation import BridgeTimeout, ProtocolError
from isaac_threrisaifuture.stall_watchdog import RunProgress, StallWatchdog

STILL = np.array([0, 0, 0])


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def restart_command(**changes):
    values = dict(
        session_id=SESSION, sequence=1, game_epoch=1, room_visit=1, frame_id=5, kind="restart"
    )
    values.update(changes)
    return Command(**values)


# --- the restart command model ---------------------------------------------------------


def test_restart_command_is_canonical_and_carries_no_action():
    command = restart_command()
    raw = json.loads(command.wire_bytes())
    assert raw["kind"] == "restart" and raw["frames"] == 0
    assert (raw["move"], raw["shoot"], raw["use"]) == ("none", "none", "none")
    assert Command.model_validate_json(command.wire_bytes()) == command


@pytest.mark.parametrize(
    "changes", [dict(move="left"), dict(shoot="up"), dict(use="bomb"), dict(frames=1)]
)
def test_restart_command_rejects_action_fields(changes):
    with pytest.raises(ProtocolError):
        restart_command(**changes)


# --- the watchdog itself ---------------------------------------------------------------


def run(dog, clock, seconds, *, active=True, gap=1.0):
    fired = 0
    for _ in range(int(seconds / gap)):
        clock.now += gap
        fired += dog.observe(active=active)
    return fired


def test_fires_after_ninety_active_seconds_without_progress():
    clock = Clock()
    dog = StallWatchdog(90, clock=clock)
    dog.observe(active=True)
    assert run(dog, clock, 89) == 0
    assert run(dog, clock, 1) == 1 and dog.fired


def test_fires_only_once_until_reset():
    clock = Clock()
    dog = StallWatchdog(90, clock=clock)
    dog.observe(active=True)
    assert run(dog, clock, 300) == 1


def test_paused_or_unavailable_time_does_not_count():
    clock = Clock()
    dog = StallWatchdog(90, clock=clock)
    dog.observe(active=True)
    run(dog, clock, 60)
    assert run(dog, clock, 120, active=False) == 0
    clock.now += 100  # the gap before the first active snapshot is not game time either
    assert dog.observe(active=True) is False
    assert run(dog, clock, 29) == 0 and dog.idle_seconds == pytest.approx(89.0)
    assert run(dog, clock, 1) == 1


def test_long_gaps_between_snapshots_are_capped():
    clock = Clock()
    dog = StallWatchdog(90, clock=clock, max_gap=2.0)
    dog.observe(active=True)
    clock.now += 500  # a busy learner or a stuck transport, not 500 s of play
    dog.observe(active=True)
    assert dog.idle_seconds == pytest.approx(2.0) and not dog.fired


def test_progress_restarts_the_window():
    clock = Clock()
    dog = StallWatchdog(90, clock=clock)
    dog.observe(active=True)
    assert run(dog, clock, 80) == 0
    clock.now += 1
    dog.observe(active=True, progress=True)
    assert dog.idle_seconds == 0.0
    assert run(dog, clock, 89) == 0
    assert run(dog, clock, 1) == 1


def test_reset_for_a_new_epoch_rearms_the_watchdog():
    clock = Clock()
    dog = StallWatchdog(90, clock=clock)
    dog.observe(active=True)
    assert run(dog, clock, 100) == 1
    dog.reset()
    assert not dog.fired and dog.idle_seconds == 0.0
    dog.observe(active=True)
    assert run(dog, clock, 100) == 1


def test_invalid_limits_are_refused():
    with pytest.raises(ValueError):
        StallWatchdog(0)


# --- run progress: only first-time facts count -------------------------------------------


def event(kind, **payload):
    return OracleEvent(
        provenance="game_api", session_id=SESSION, game_epoch=1, room_visit=1, frame_id=1,
        kind=kind, **payload,
    )  # fmt: skip


def fresh_progress():
    progress = RunProgress()
    progress.reset(stage=1, room_index=84, counters={"coin": 0, "bomb": 1, "key": 0}, items=())
    return progress


def test_revisiting_known_rooms_is_not_progress():
    progress = fresh_progress()
    assert progress.novel([event("room_entered", room_index=85)], stage=1)
    assert not progress.novel([event("room_entered", room_index=84)], stage=1)  # start room
    assert not progress.novel([event("room_entered", room_index=85)], stage=1)
    # The same room index on a new floor is a new room.
    assert progress.novel([event("room_entered", room_index=85)], stage=2)


def test_counters_only_count_above_the_run_peak():
    progress = fresh_progress()
    # Placing the starting bomb and picking up one bomb returns to the peak.
    assert not progress.novel([event("pickup_gained", resource="bomb", amount=1, total=1)], stage=1)
    assert progress.novel([event("pickup_gained", resource="bomb", amount=1, total=2)], stage=1)
    assert progress.novel([event("pickup_gained", resource="coin", amount=1, total=1)], stage=1)


def test_collectibles_floors_damage_and_clears():
    progress = fresh_progress()
    item = event("pickup_gained", resource="collectible", item_id=7)
    assert progress.novel([item], stage=1)
    assert not progress.novel([item], stage=1)  # dropped and taken again
    assert progress.novel([event("floor_entered", stage=2)], stage=2)
    assert not progress.novel([event("floor_entered", stage=1)], stage=1)
    hit = event("enemy_damaged", entity_id=1, spawn_generation=0, amount=1.0)
    assert progress.novel([hit], stage=1)
    assert progress.novel([event("room_cleared", room_index=84)], stage=1)
    assert not progress.novel([event("player_damaged", amount=1.0, damage_source="enemy")], stage=1)


# --- wiring in the live backend --------------------------------------------------------


class FakeClient:
    """Serves one backlog snapshot, then one new frame per take(); advances the fake clock."""

    connected = True
    failure = None

    def __init__(self, clock, *, per_take=2.0, enemies=None, timeout_after=None, rooms=None):
        self.clock, self.per_take = clock, per_take
        self.rooms = rooms
        self.frame = 1
        self.enemies = enemies or (lambda frame: [(1, 10.0)])
        self.timeout_after = timeout_after
        self.sent: list[str] = []
        self.status = "accepted"
        self.peer_closed = 0

    def _snapshot(self):
        snap = live(self.frame, enemies=self.enemies(self.frame))
        if self.rooms is None:
            return snap
        oracle = snap.oracle.model_copy(update={"room_index": self.rooms(self.frame)})
        return snap.model_copy(update={"oracle": oracle})

    def drain(self):
        if self.frame == 1:
            return [self._snapshot()]
        return []

    def take(self, timeout):
        if self.timeout_after is not None and self.frame >= self.timeout_after:
            self.clock.now += 200  # the game stops answering
            raise BridgeTimeout("No live snapshot before the deadline")
        self.frame += 1
        self.clock.now += self.per_take
        return self._snapshot()

    def command(self, kind, reference, **_):
        self.sent.append(kind)
        return LiveCommandAck(
            type="command_ack", protocol_version=1, session_id=SESSION, sequence=len(self.sent),
            game_epoch=reference.game_epoch, room_visit=reference.room.visit_id,
            frame_id=reference.frame_id, kind=kind, status=self.status,
        )  # fmt: skip

    def close_peer(self):
        self.peer_closed += 1


def stalled_env(client, clock, **options):
    return make_live_env(client, stall_seconds=90, clock=clock, max_faults=1, **options)


def play(env, steps):
    for _ in range(steps):
        _, _, terminated, truncated, info = env.step(STILL)
        if terminated or truncated:
            return info
    return None


def test_stall_truncates_with_reason_and_sends_one_restart():
    clock = Clock()
    client = FakeClient(clock)
    env = stalled_env(client, clock)
    env.reset()
    info = play(env, 200)
    assert info is not None and info["truncation_reason"] == "stall" and "fault" not in info
    assert client.sent.count("restart") == 1 and client.sent[-1] == "restart"
    assert "release" not in client.sent  # the restarting game is left alone
    # 90 active seconds at 2 s per snapshot and 3 snapshots per step.
    assert 14 <= client.sent.count("action") <= 16
    assert env.faults == 0


def test_damage_progress_keeps_the_episode_running():
    clock = Clock()
    # A fresh enemy every 10 frames (20 s) that takes damage at once.
    client = FakeClient(clock, enemies=lambda f: [(f // 10, 10.0 if f % 10 == 0 else 5.0)])
    env = stalled_env(client, clock)
    env.reset()
    assert play(env, 100) is None  # 600 s of play with steady damage
    assert client.sent.count("restart") == 0


def test_walking_between_two_known_rooms_still_stalls():
    clock = Clock()
    # The agent crosses a door between rooms 84 and 85 every 5 frames (10 s).
    client = FakeClient(clock, rooms=lambda f: 84 + (f // 5) % 2)
    env = stalled_env(client, clock)
    env.reset()
    info = play(env, 200)
    assert info is not None and info["truncation_reason"] == "stall"
    assert client.sent.count("restart") == 1


def test_refused_restart_still_truncates_and_keeps_the_session():
    clock = Clock()
    client = FakeClient(clock)
    client.status = "rejected"
    env = stalled_env(client, clock)
    env.reset()
    info = play(env, 200)
    backend = env.env.controller.backend
    assert info["truncation_reason"] == "stall" and backend.restart_rejections == 1
    assert client.peer_closed == 0 and client.sent.count("restart") == 1


def test_missing_snapshots_are_an_infrastructure_fault_never_a_stall():
    clock = Clock()
    client = FakeClient(clock, timeout_after=10)
    env = stalled_env(client, clock)
    env.reset()
    info = play(env, 50)
    assert info is not None and "fault" in info and "truncation_reason" not in info
    assert env.faults == 1 and "restart" not in client.sent


def test_a_new_epoch_resets_the_watchdog_in_start_episode():
    clock = Clock()
    client = FakeClient(clock)
    backend = LiveBackend(client)  # type: ignore[arg-type]
    backend.watchdog = StallWatchdog(90, clock=clock)
    backend.start_episode(LIVE_SCENARIO, None)
    backend.watchdog.observe(active=True)
    run(backend.watchdog, clock, 100)
    assert backend.watchdog.fired
    client.frame = 0  # a fresh run: the backlog serves a new first snapshot
    backend.start_episode(LIVE_SCENARIO, None)
    assert not backend.watchdog.fired and backend.watchdog.idle_seconds == 0.0


def test_request_restart_waits_out_old_epoch_snapshots():
    clock = Clock()
    client = FakeClient(clock)
    backend = LiveBackend(client)  # type: ignore[arg-type]
    backend.start_episode(LIVE_SCENARIO, None)
    assert backend.request_restart() is True and client.sent == ["restart"]
    backend._current = None  # simulate the controller dropping the episode
    client.frame = 0
    backend.restart_timeout = 0.2
    # The old connection still serves the old epoch's snapshots until the game exits.
    with pytest.raises(BridgeTimeout):
        backend.start_episode(LIVE_SCENARIO, None)
