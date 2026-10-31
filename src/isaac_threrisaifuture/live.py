"""Pragmatic live loop over the real game: entity observation, actions and death restart.

User decisions of 2026-10-18 (openspec change live-training-loop): reward labels are
approximate frame deltas of a separate oracle block, not an exact engine event
oracle; death restarts are autonomous within a bounded training approval; training
on save file 2 is accepted by the operator.
"""

import json
import math
import os
import socket
import threading
import time
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, SupportsFloat

import gymnasium as gym
from pydantic import Field

from .actions import Command, Direction, Use
from .checkpoints import RewardContract
from .entities import EntityFrame, OracleEvent, OracleKind
from .episodes import ACTION_NVEC, DIRECTIONS, USES, Action, EpisodeFault, Scenario, StepResult
from .live_wire import (
    CommandKind,
    LiveCommandAck,
    LiveOracle,
    LiveSnapshot,
    OracleEnemy,
    PlayerHits,
)
from .menu_entry import MenuInput
from .novelty_counts import NoveltyCounts
from .observation import (
    BridgeError,
    BridgeTimeout,
    HelloAck,
    PeerDisconnected,
    ProtocolError,
    WireModel,
    decode,
)
from .observer_client import ObservationClient, ObserverConfig
from .stall_watchdog import DEFAULT_STALL_SECONDS, RunProgress, StallWatchdog

__all__ = ["LiveCommandAck", "LiveOracle", "LiveSnapshot", "OracleEnemy"]

APPROVAL_NAME = "action_authorization.json"
TRAINING_MAX_SECONDS = 28800  # mirrors Config.training_max_seconds in main.lua
MAX_RESTARTS = 5000
MAX_REWARD_IDENTITIES = 4096
LIVE_REWARD_CONTRACT: Literal["pure-v11"] = "pure-v11"
_CONSUMABLES: tuple[Literal["coin", "bomb", "key"], ...] = ("coin", "bomb", "key")
SNAPSHOT_BACKLOG = 512
ACK_TIMEOUT = 1.0
Text = Annotated[str, Field(min_length=1, max_length=128, pattern=r"\S")]


class LiveBudgetExpired(EpisodeFault):
    """The shared run deadline expired; retrying cannot renew it."""


class LiveSessionCancelled(LiveBudgetExpired):
    """Cooperative user stop; never a death, fault retry or completed rollout."""


LIVE_SCENARIO = Scenario(
    id="live-file2",
    split="train",
    difficulty=1,
    max_game_updates=None,  # one episode is one run: death or an explicit truncation ends it
    enemy_count=0,
    enemy_hp=1.0,
    allow_room_change=True,
    end_on_clear=False,
)


class TrainingApproval(WireModel):
    """Operator approval for the live loop; session-scoped, never bound to one game epoch."""

    profile_id: Text
    profile_mode: Literal["training"] = "training"
    expires_at: Annotated[int, Field(ge=1)]
    profile_evidence: Text
    slot_evidence: Text
    runtime_authorization: Text
    slot: Annotated[int, Field(ge=2, le=2)] = 2
    # 0 means unlimited restarts (pure training profile); the lease still bounds the session.
    max_restarts: Annotated[int, Field(ge=0, le=MAX_RESTARTS)]


class LiveClient(ObservationClient):
    """One live peer; a reader thread drains the socket so Lua never stalls on output.

    Snapshots queue in a bounded backlog (oldest dropped). Any reader failure is kept
    and re-raised to the caller; it never becomes a transition.
    """

    def __init__(self, config: ObserverConfig, *, stop_on_death: bool = False) -> None:
        super().__init__(replace(config, live_loop=True))
        self.stop_on_death = stop_on_death
        self.fatal_snapshot: LiveSnapshot | None = None
        self._cond = threading.Condition()
        self._inbox: deque[LiveSnapshot] = deque(maxlen=SNAPSHOT_BACKLOG)
        self._acks: dict[int, LiveCommandAck] = {}
        self._failure: BridgeError | None = None
        self._reader: threading.Thread | None = None
        self._command_sequence = 0
        self.dropped_snapshots = 0

    @property
    def connected(self) -> bool:
        return self._peer is not None and self._failure is None

    @property
    def failure(self) -> BridgeError | None:
        with self._cond:
            return self._failure

    def connect(self) -> HelloAck:
        ack = self.accept()
        self._reader = threading.Thread(target=self._read_loop, name="live-reader", daemon=True)
        self._reader.start()
        return ack

    def close_peer(self) -> None:
        peer, reader = self._peer, getattr(self, "_reader", None)
        if peer is not None:
            try:
                peer.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        if reader is not None and reader is not threading.current_thread():
            reader.join(timeout=2.0)
        self._reader = None
        super().close_peer()
        if hasattr(self, "_cond"):
            with self._cond:
                self._inbox.clear()
                self._acks.clear()
                self._failure = None
            self._command_sequence = 0

    def _read_loop(self) -> None:
        try:
            while True:
                raw = self._read_line(time.monotonic() + self.config.message_timeout)
                try:
                    kind = json.loads(raw).get("type")
                except (ValueError, AttributeError, UnicodeError, RecursionError) as exc:
                    raise ProtocolError("Invalid live record") from exc
                if kind == "snapshot":
                    snap = decode(raw, LiveSnapshot)
                    self._validate_snapshot(snap)
                    with self._cond:
                        if len(self._inbox) == self._inbox.maxlen:
                            self.dropped_snapshots += 1
                        self._inbox.append(snap)
                        fatal = (
                            self.stop_on_death
                            and snap.oracle is not None
                            and snap.oracle.player_dead
                        )
                        if fatal:
                            self.fatal_snapshot = snap
                            self._failure = LiveBudgetExpired(
                                "Observed death; zero-restart disconnect"
                            )
                        self._cond.notify_all()
                    if fatal:
                        # Cancel Lua's delayed restart even while the optimizer is busy.
                        if self._peer is not None:
                            try:
                                self._peer.shutdown(socket.SHUT_RDWR)
                            except OSError:
                                pass
                        return
                elif kind == "command_ack":
                    ack = decode(raw, LiveCommandAck)
                    with self._cond:
                        if len(self._acks) >= 64:
                            raise ProtocolError("Unclaimed acknowledgements exceed 64")
                        self._acks[ack.sequence] = ack
                        self._cond.notify_all()
                else:
                    raise ProtocolError("Unexpected live record type")
        except BaseException as exc:
            failure = exc if isinstance(exc, BridgeError) else PeerDisconnected(str(exc))
            with self._cond:
                if self._failure is None:
                    self._failure = failure
                self._cond.notify_all()

    def drain(self) -> list[LiveSnapshot]:
        with self._cond:
            items = list(self._inbox)
            self._inbox.clear()
        return items

    def take(self, timeout: float) -> LiveSnapshot:
        deadline = time.monotonic() + timeout
        with self._cond:
            while not self._inbox:
                if self._failure is not None:
                    raise self._failure
                if self._peer is None:
                    raise BridgeError("No negotiated live peer")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise BridgeTimeout("No live snapshot before the deadline")
                self._cond.wait(remaining)
            return self._inbox.popleft()

    def command(
        self,
        kind: CommandKind,
        reference: LiveSnapshot,
        *,
        move: Direction = "none",
        shoot: Direction = "none",
        use: Use = "none",
        frames: int = 0,
    ) -> LiveCommandAck:
        """Send once and await the matching ack; failures invalidate the peer."""
        try:
            if self._peer is None or self._session is None:
                raise BridgeError("No negotiated live peer")
            if reference.frame_id is None or reference.room is None:
                raise ProtocolError("Commands need an available reference snapshot")
            self._command_sequence += 1
            command = Command(
                session_id=self._session,
                sequence=self._command_sequence,
                game_epoch=reference.game_epoch,
                room_visit=reference.room.visit_id,
                frame_id=reference.frame_id,
                kind=kind,
                move=move,
                shoot=shoot,
                use=use,
                frames=frames,
            )
            try:
                self._peer.sendall(command.wire_bytes())
            except OSError as exc:
                raise PeerDisconnected("Command socket failed") from exc
            deadline = time.monotonic() + ACK_TIMEOUT
            with self._cond:
                while command.sequence not in self._acks:
                    if self._failure is not None:
                        raise self._failure
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise BridgeTimeout("Command acknowledgement deadline expired")
                    self._cond.wait(remaining)
                ack = self._acks.pop(command.sequence)
            if ack.session_id != command.session_id or ack.kind != command.kind:
                raise ProtocolError("Command acknowledgement identity mismatch")
            if ack.status == "accepted" and (
                ack.game_epoch != command.game_epoch
                or ack.room_visit != command.room_visit
                or not command.frame_id <= ack.frame_id <= command.frame_id + 15
            ):
                raise ProtocolError("Accepted acknowledgement identity mismatch")
            return ack
        except BaseException:
            self.close_peer()
            raise


@dataclass
class EventDeriver:
    """Approximate oracle events from consecutive live oracle blocks.

    No kill channel: absence never earns damage or kill credit. Only continuous,
    complete HP decreases below a session/epoch floor pay; all player HP loss is
    still attributed to enemies. History survives software episode resets.
    """

    _enemies: dict[int, float] = field(default_factory=dict)
    _visit: tuple[str, int, int] | None = None
    _namespace: tuple[str, int] | None = None
    _hp_floor: dict[int, tuple[float, float]] = field(default_factory=dict)
    _clear: bool = False
    _health: int | None = None
    _dead: bool = False
    _overflow: bool = False
    # Last (room index, stage, coins/bombs/keys, collectibles) of the current epoch.
    _level: tuple[int, int, tuple[int, int, int], frozenset[int]] | None = None

    def begin(self, snap: LiveSnapshot) -> list[OracleEvent]:
        # Reset membership/health baselines, not the encounter's earned allowance.
        self._enemies, self._visit, self._health, self._dead = {}, None, None, False
        return self.update(snap)

    def update(self, snap: LiveSnapshot) -> list[OracleEvent]:
        frame, oracle = snap.entity_frame, snap.oracle
        if frame is None or oracle is None:
            raise ProtocolError("Event derivation needs an available live snapshot")
        events: list[OracleEvent] = []

        def emit(kind: OracleKind, **payload: Any) -> None:
            events.append(
                OracleEvent(
                    provenance="game_api",
                    session_id=frame.session_id,
                    game_epoch=frame.game_epoch,
                    room_visit=frame.room_visit,
                    frame_id=frame.frame_id,
                    kind=kind,
                    **payload,
                )
            )

        namespace = (frame.session_id, frame.game_epoch)
        if namespace != self._namespace:
            self._hp_floor.clear()
            self._namespace = namespace
            self._level = None  # a new run starts from a silent baseline
        visit = (*namespace, frame.room_visit)
        same_visit = visit == self._visit
        if not same_visit:
            self._enemies, self._visit, self._overflow = {}, visit, False
        current = {enemy.entity_id: enemy for enemy in oracle.enemies}
        complete = oracle.enemy_overflow == 0 and not self._overflow
        for entity_id, enemy in current.items():
            stored = self._hp_floor.get(entity_id)
            if stored is None:
                if len(self._hp_floor) >= MAX_REWARD_IDENTITIES:
                    raise EpisodeFault("Live reward identity history exhausted")
                stored = (enemy.max_hp, enemy.hp)
            maximum, floor = stored
            if enemy.max_hp != maximum:
                floor = 0.0  # unknown transformation: never renew this identity's credit
            if complete and entity_id in self._enemies and enemy.hp < floor:
                emit("enemy_damaged", entity_id=entity_id, spawn_generation=0,
                     amount=floor - enemy.hp)  # fmt: skip
            self._hp_floor[entity_id] = (maximum, min(floor, enemy.hp))
            if entity_id not in self._enemies:
                emit("enemy_spawned", entity_id=entity_id, spawn_generation=0, amount=enemy.max_hp)
        # One-shot kills leave the list between snapshots, so the game's kill report pays
        # the remaining credit once; a zero floor makes the re-sent ring pay nothing more.
        for entity_id in oracle.killed:
            stored = self._hp_floor.get(entity_id)
            if entity_id not in current and stored is not None and stored[1] > 0:
                emit("enemy_damaged", entity_id=entity_id, spawn_generation=0, amount=stored[1])
                self._hp_floor[entity_id] = (stored[0], 0.0)
        # Missing membership is unknown, not death. A later appearance must
        # establish a baseline without claiming damage across the gap.
        self._enemies = {entity_id: enemy.hp for entity_id, enemy in current.items()}
        self._overflow = oracle.enemy_overflow > 0
        if same_visit and oracle.room_clear and not self._clear:
            emit("room_cleared", room_index=oracle.room_index)
        self._clear = oracle.room_clear
        self._derive_level(snap, emit)
        health = frame.health.red_half_hearts + frame.health.soul_half_hearts
        if self._health is not None and health < self._health:
            # Every health loss is charged as "enemy": reward v8 and v9 penalise all sources alike.
            # The oracle hits_* counters, not this label, tell the real source.
            emit("player_damaged", amount=float(self._health - health), damage_source="enemy")
        elif self._health is not None and health > self._health:
            emit("player_healed", amount=float(health - self._health))
        self._health = health
        if oracle.player_dead and not self._dead:
            emit("player_died")
        self._dead = oracle.player_dead
        return events

    def _derive_level(self, snap: LiveSnapshot, emit: Callable[..., None]) -> None:
        """Room, floor and pickup events. Counter decreases and removals emit nothing."""
        frame, oracle = snap.entity_frame, snap.oracle
        assert frame is not None and oracle is not None
        inventory = frame.inventory
        counters = (inventory.coins, inventory.bombs, inventory.keys)
        owned = frozenset(frame.collectibles)
        level = (oracle.room_index, frame.room.stage, counters, owned)
        if self._level is not None:
            room, stage, before, held = self._level
            if frame.room.stage != stage:
                emit("floor_entered", stage=frame.room.stage)
            if oracle.room_index != room:
                emit("room_entered", room_index=oracle.room_index)
            for resource, old, new in zip(_CONSUMABLES, before, counters, strict=True):
                if new > old:
                    emit("pickup_gained", resource=resource, amount=float(new - old), total=new)
            for item_id in sorted(owned - held):
                emit("pickup_gained", resource="collectible", item_id=item_id)
        self._level = level


def _playable(snap: LiveSnapshot) -> bool:
    return (
        snap.status == "active"
        and snap.entity_frame is not None
        and snap.oracle is not None
        and not snap.oracle.player_dead
    )


def _status_of(snap: LiveSnapshot) -> str:
    return "dead" if snap.oracle is not None and snap.oracle.player_dead else snap.status


ORACLE_STAT_KEYS = (
    "kills",
    *(f"hits_{name}" for name in PlayerHits.model_fields),
)


def _oracle_counters(oracle: LiveOracle | None) -> dict[str, int]:
    if oracle is None:
        return dict.fromkeys(ORACLE_STAT_KEYS, 0)
    hits = oracle.player_hits
    return {
        "kills": oracle.kills,
        **{f"hits_{name}": getattr(hits, name) for name in PlayerHits.model_fields},
    }


def _step_result(
    frame: EntityFrame, oracle: LiveOracle, events: tuple[OracleEvent, ...]
) -> StepResult:
    """Frame, events and the oracle labels the reward needs: room index, doors and enemies."""
    return StepResult(
        frame,
        events,
        room_index=oracle.room_index,
        doors=tuple(oracle.doors),
        enemies_present=bool(oracle.enemies) or oracle.enemy_overflow > 0,
        room_grid=oracle.room_grid,
    )


@dataclass
class LiveBackend:
    """GameBackend over a LiveClient. Episodes are segments of one continuing run."""

    client: LiveClient
    step_timeout: float = 5.0
    restart_timeout: float = 90.0
    pause_limit: float = 600.0
    run_deadline: float | None = None
    stop_file: Path | None = None
    deriver: EventDeriver = field(default_factory=EventDeriver)
    # Optional stall watchdog; `on_stall` ends the episode (truncated) before the restart.
    watchdog: StallWatchdog | None = None
    # First-time facts of the run; only these feed the watchdog as progress.
    progress: RunProgress = field(default_factory=RunProgress)
    on_stall: Callable[[], None] | None = None
    supports_seed: ClassVar[bool] = False
    _current: LiveSnapshot | None = None
    _stall_fired: bool = False
    # (session, epoch) of the run a command restart was accepted for; reset waits it out.
    _restarting_from: tuple[str, int] | None = None
    restart_rejections: int = 0
    # Oracle counters (kills, hits by source) at episode start; metrics only.
    _oracle_start: dict[str, int] = field(default_factory=dict)
    # Wall-time diagnostics since the last `timing_counters()` call (seconds, counts).
    _wait_seconds: float = 0.0
    _command_seconds: float = 0.0
    _timed_steps: int = 0
    _snapshots: int = 0
    # Snapshots read while pausing or resuming for an update; the next step absorbs them first.
    _backlog: list[LiveSnapshot] = field(default_factory=list)

    def start_episode(self, scenario: Scenario, seed: int | None) -> StepResult:
        """Continue the run; after a death wait for the autonomous restart to reconnect."""
        self._backlog.clear()
        deadline = time.monotonic() + self.restart_timeout
        if self.run_deadline is not None:
            deadline = min(deadline, self.run_deadline)
        while True:
            self._check_budget()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise BridgeTimeout("No playable live state before the restart deadline")
            try:
                if not self.client.connected:
                    failure = self.client.failure
                    if isinstance(failure, ProtocolError):
                        raise failure
                    self.client.config = replace(
                        self.client.config,
                        accept_timeout=remaining,
                        handshake_timeout=min(self.client.config.handshake_timeout, remaining),
                    )
                    self.client.connect()
                backlog = self.client.drain()
                snap = backlog[-1] if backlog else self._take(min(remaining, 5.0))
            except ProtocolError:
                raise
            except LiveBudgetExpired:
                raise
            except BridgeError:
                self.client.close_peer()  # a death restart closes the session; reconnect
                continue
            if _playable(snap) and (snap.session_id, snap.game_epoch) != self._restarting_from:
                break
        self._current = snap
        self._restarting_from = None
        self._stall_fired = False
        assert snap.entity_frame is not None
        assert snap.oracle is not None
        if self.watchdog is not None:
            self.watchdog.reset()
        self._oracle_start = _oracle_counters(snap.oracle)
        frame = snap.entity_frame
        self.progress.reset(
            stage=frame.room.stage,
            room_index=snap.oracle.room_index,
            counters={
                "coin": frame.inventory.coins,
                "bomb": frame.inventory.bombs,
                "key": frame.inventory.keys,
            },
            items=frame.collectibles,
        )
        return _step_result(snap.entity_frame, snap.oracle, tuple(self.deriver.begin(snap)))

    def _command(self, *args: Any, **kwargs: Any) -> Any:
        """`client.command` with its wall time added to the diagnostics."""
        start = time.monotonic()
        try:
            return self.client.command(*args, **kwargs)
        finally:
            self._command_seconds += time.monotonic() - start

    def _take(self, timeout: float) -> LiveSnapshot:
        """`client.take` with its wall time and count added to the diagnostics."""
        start = time.monotonic()
        try:
            snap = self.client.take(timeout)
        finally:
            self._wait_seconds += time.monotonic() - start
        self._snapshots += 1
        return snap

    def timing_counters(self) -> dict[str, float]:
        """Read and reset the wall-time diagnostics (metrics only, never a model input).

        `wait_seconds` is time inside `client.take` (waiting for the game),
        `command_seconds` inside `client.command` (send and ack), plus the steps and
        snapshots taken in the same window.
        """
        counters = {
            "wait_seconds": self._wait_seconds,
            "command_seconds": self._command_seconds,
            "steps": float(self._timed_steps),
            "snapshots": float(self._snapshots),
        }
        self._wait_seconds = self._command_seconds = 0.0
        self._timed_steps = self._snapshots = 0
        return counters

    def step(self, action: Action, repeat: int) -> StepResult:
        self._timed_steps += 1
        result = self._advance(action, repeat)
        if self._stall_fired:
            self._stall_fired = False
            current = self._current
            # A death in the same step wins: the death restart handles it.
            if (
                current is not None
                and current.oracle is not None
                and not current.oracle.player_dead
            ):
                if self.on_stall is not None:
                    self.on_stall()
                self.request_restart()
        return result

    def request_restart(self) -> bool:
        """Ask Lua to restart the run. True when accepted; a refusal keeps the session.

        After an accepted restart the old connection is left alone (Lua dispatches only
        while connected); the next reset skips its snapshots and reconnects.
        """
        reference = self._current
        if reference is None:
            raise BridgeError("No live episode")
        ack = self._command("restart", reference)
        if ack.status != "accepted":
            self.restart_rejections += 1
            return False
        self._restarting_from = (reference.session_id, reference.game_epoch)
        return True

    def _advance(self, action: Action, repeat: int) -> StepResult:
        self._check_budget()
        if self._current is None:
            raise BridgeError("No live episode")
        events: list[OracleEvent] = []
        before = self._current.frame_id
        assert before is not None
        backlog, self._backlog = self._backlog, []
        for snap in [*backlog, *self.client.drain()]:
            if self._absorb(snap, events):
                return self._result(events)
        reference = self._current
        assert reference.frame_id is not None
        self._check_budget()
        ack = self._command(
            "action",
            reference,
            move=DIRECTIONS[action.move],
            shoot=DIRECTIONS[action.shoot],
            use=USES[action.use],
            frames=repeat,
        )
        accepted = ack.status == "accepted"
        target = ack.frame_id + repeat if accepted else reference.frame_id + 1
        start = time.monotonic()
        deadline = start + self.step_timeout
        if self.run_deadline is not None:
            deadline = min(deadline, self.run_deadline)
        while self._current.frame_id is not None and self._current.frame_id < target:
            self._check_budget()
            snap = self._take(max(0.0, deadline - time.monotonic()))
            if snap.status == "paused":
                deadline = min(start + self.pause_limit, time.monotonic() + self.step_timeout)
                if self.run_deadline is not None:
                    deadline = min(deadline, self.run_deadline)
            if self._absorb(snap, events):
                break
        return self._result(events)

    def _check_budget(self) -> None:
        if self.run_deadline is not None and time.monotonic() >= self.run_deadline:
            raise LiveBudgetExpired("Live wall-time budget exhausted")
        if self.stop_file is not None and self.stop_file.exists():
            raise LiveSessionCancelled("User cancellation requested")

    @property
    def stall_fraction(self) -> float:
        """Idle time of the stall watchdog as a fraction of its limit; 0 without one."""
        if self.watchdog is None:
            return 0.0
        return min(max(self.watchdog.idle_seconds / self.watchdog.stall_seconds, 0.0), 1.0)

    def oracle_enemy_count(self) -> int | None:
        """Oracle enemies of the last snapshot, overflow included (metrics only)."""
        current = self._current
        if current is None or current.oracle is None:
            return None
        return len(current.oracle.enemies) + current.oracle.enemy_overflow

    @property
    def stall_idle_seconds(self) -> float:
        """Idle seconds on the stall watchdog's clock; 0 without one."""
        return 0.0 if self.watchdog is None else self.watchdog.idle_seconds

    def episode_oracle_stats(self) -> dict[str, int]:
        """Kills and player hits by source since the episode start (metrics only).

        The observer counts per game epoch. A counter that went down means a new epoch, so
        its new value counts from zero; deltas are never negative.
        """
        current = self._current
        if current is None or current.oracle is None:
            return dict.fromkeys(ORACLE_STAT_KEYS, 0)
        now = _oracle_counters(current.oracle)
        return {
            key: value - self._oracle_start.get(key, 0)
            if value >= self._oracle_start.get(key, 0)
            else value
            for key, value in now.items()
        }

    @property
    def latest(self) -> LiveSnapshot | None:
        """Snapshot of the current or most recent episode step (management reads only)."""
        return self._current

    def release(self) -> None:
        if self._current is None or not self.client.connected or self._restarting_from:
            return
        try:
            self._command("release", self._current)
        except BridgeError:
            pass  # the hold expires within 15 frames / 250 ms; the peer is already closed

    def close(self) -> None:
        self.client.close()

    def cancelled(self) -> bool:
        return self.stop_file is not None and self.stop_file.exists()

    def game_status(self, timeout: float) -> str | None:
        """Status of the newest snapshot: active, paused, unavailable or dead; None if none.

        Reads the snapshots into the backlog, so the next step still sees all of them.
        """
        self._backlog.extend(self.client.drain())
        if not self._backlog:
            try:
                self._backlog.append(self.client.take(timeout))
            except BridgeTimeout:
                return None
        return _status_of(self._backlog[-1])

    def wait_game_status(self, wanted: str, timeout: float) -> bool:
        """Wait up to `timeout` seconds for a snapshot with this status (never absorbed here).

        Every snapshot read goes to the backlog in order, so paused ones feed the stall
        watchdog as inactive and no paused time counts as step time or stagnation.
        """
        deadline = time.monotonic() + timeout
        while True:
            self._backlog.extend(self.client.drain())
            if self._backlog and _status_of(self._backlog[-1]) == wanted:
                return True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return False
            try:
                self._backlog.append(self.client.take(remaining))
            except BridgeTimeout:
                return False

    def _absorb(self, snap: LiveSnapshot, events: list[OracleEvent]) -> bool:
        current = self._current
        assert current is not None and current.frame_id is not None
        if snap.session_id != current.session_id or snap.game_epoch != current.game_epoch:
            raise EpisodeFault("Live session or game epoch changed without an observed death")
        if not _playable(snap) and (snap.oracle is None or not snap.oracle.player_dead):
            self._watch(snap, ())
            return False
        if snap.frame_id is None or snap.frame_id <= current.frame_id:
            return False
        new_events = self.deriver.update(snap)
        events.extend(new_events)
        self._current = snap
        self._watch(snap, new_events)
        return snap.oracle is not None and snap.oracle.player_dead

    def _watch(self, snap: LiveSnapshot, events: Sequence[OracleEvent]) -> None:
        """Feed the stall watchdog; paused, unavailable and dead snapshots add no time.

        Only facts new for the run count as progress (see `RunProgress`).
        """
        if self.watchdog is None:
            return
        stage = snap.entity_frame.room.stage if snap.entity_frame is not None else 0
        progress = self.progress.novel(events, stage=stage)
        if self.watchdog.observe(active=_playable(snap), progress=progress):
            self._stall_fired = True

    def _result(self, events: list[OracleEvent]) -> StepResult:
        current = self._current
        assert current is not None and current.entity_frame is not None
        assert current.oracle is not None
        return _step_result(current.entity_frame, current.oracle, tuple(events))


class FaultTolerantEnv(gym.Wrapper[Any, Any, Any, Any]):
    """Bounded fault budget for live runs; faults are logged and never become deaths.

    A step fault ends the segment as truncated with `info["fault"]`; reset retries.
    Protocol errors (malformed data) are never retried. With `max_consecutive_faults`, that
    many faults in a row (no successful step or reset between them) end the session.
    """

    def __init__(
        self,
        env: gym.Env[Any, Any],
        *,
        max_faults: int = 20,
        on_record: Callable[[str, dict[str, Any]], None] | None = None,
        run_deadline: float | None = None,
        max_consecutive_faults: int | None = None,
    ) -> None:
        super().__init__(env)
        if max_faults < 0 or (max_consecutive_faults is not None and max_consecutive_faults < 1):
            raise ValueError("Fault budgets must be nonnegative (consecutive cap positive)")
        self.max_faults = max_faults
        self.max_consecutive_faults = max_consecutive_faults
        self.faults = 0
        self.consecutive_faults = 0
        self.on_record = on_record
        self.run_deadline = run_deadline
        self._last_obs: Any = None

    def _fault(self, exc: EpisodeFault) -> None:
        if isinstance(exc.__cause__, ProtocolError) or isinstance(exc, ProtocolError):
            raise exc
        self._check_budget()
        if isinstance(exc, LiveBudgetExpired):
            raise exc
        self.faults += 1
        self.consecutive_faults += 1
        if self.on_record is not None:
            self.on_record(
                "fault",
                {
                    "reason": str(exc),
                    "faults": self.faults,
                    "consecutive": self.consecutive_faults,
                },
            )
        if self.faults > self.max_faults:
            raise exc
        if (
            self.max_consecutive_faults is not None
            and self.consecutive_faults >= self.max_consecutive_faults
        ):
            raise exc

    def reset(self, **kwargs: Any) -> tuple[Any, dict[str, Any]]:
        while True:
            self._check_budget()
            try:
                obs, info = self.env.reset(**kwargs)
            except EpisodeFault as exc:
                self._fault(exc)
                continue
            self._last_obs = obs
            return obs, info  # a reset alone does not clear the streak; a step must succeed

    def step(self, action: Any) -> tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]:
        self._check_budget()
        try:
            obs, reward, terminated, truncated, info = self.env.step(action)
        except EpisodeFault as exc:
            self._fault(exc)
            return self._last_obs, 0.0, False, True, {"fault": str(exc), "outcome": None}
        self._last_obs = obs
        self.consecutive_faults = 0
        if "episode" in info and self.on_record is not None:
            self.on_record("episode", info["episode"])
        return obs, reward, terminated, truncated, info

    def _check_budget(self) -> None:
        if self.run_deadline is not None and time.monotonic() >= self.run_deadline:
            raise LiveBudgetExpired("Live wall-time budget exhausted")


def write_training_approval(
    game_directory: Path,
    *,
    hours: float,
    max_restarts: int,
    profile_id: str = "save-file-2",
    evidence: str = "operator-confirmed",
    now: float | None = None,
) -> Path:
    """Write the private live-loop approval next to the deployed observer mod."""
    if not 0 <= max_restarts <= MAX_RESTARTS:
        raise ValueError(f"max_restarts must be 0 (unlimited) or 1..{MAX_RESTARTS}")
    seconds = int(hours * 3600)
    if not 60 <= seconds <= TRAINING_MAX_SECONDS:
        raise ValueError(f"Approval duration must be 1 minute .. {TRAINING_MAX_SECONDS // 3600} h")
    approval = TrainingApproval(
        profile_id=profile_id,
        expires_at=int(time.time() if now is None else now) + seconds,
        profile_evidence=evidence,
        slot_evidence=evidence,
        runtime_authorization=f"live-training-{time.strftime('%Y%m%d-%H%M%S')}",
        max_restarts=max_restarts,
    )
    target = game_directory / "mods" / "isaac_threrisaifuture_observer" / APPROVAL_NAME
    if not target.parent.is_dir():
        raise ValueError(f"Observer mod is not deployed in {target.parent}")
    data = approval.model_dump_json().encode()
    if len(data) > 2048:
        raise ValueError("Approval exceeds the 2048-byte Lua limit")
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, target)
    return target


def make_live_env(
    client: LiveClient,
    *,
    action_repeat: int = 3,
    max_faults: int = 20,
    record: Callable[[str, dict[str, Any]], None] | None = None,
    oracle_sink: Callable[[OracleEvent], None] | None = None,
    run_deadline: float | None = None,
    stop_file: Path | None = None,
    reward_version: int = 12,
    gamma: float | None = None,
    stall_seconds: float | None = None,
    clock: Callable[[], float] = time.monotonic,
    max_consecutive_faults: int | None = None,
    novelty_counts: NoveltyCounts | None = None,
) -> FaultTolerantEnv:
    """Live env; the pure profile pays reward v9 to v12 (v1 stays for old comparisons).

    `gamma` is the training discount that door shaping needs (reward v9); without it door shaping
    is off, which suits attach-only runs that learn nothing. Training and the frozen pure
    evaluation always pass it.
    With `stall_seconds`, a stall truncates the episode with reason `stall` and sends
    one restart command. Leave it unset for attach-only runs such as evaluation.
    `novelty_counts` is the reward v11 cross-run table: training shares it with the checkpoints,
    evaluation passes a frozen one, and without it v11 and v12 count only in memory.
    Reward v12 carries the stall limit (`stall.seconds`): a different `stall_seconds` raises
    ValueError, and without one the ledger uses the contract's limit.
    """
    from .env import IsaacCombatEnv, RewardAccountant
    from .rewards import (
        DEFAULT_CONFIG_V9,
        DEFAULT_CONFIG_V10,
        DEFAULT_CONFIG_V11,
        DEFAULT_CONFIG_V12,
        CombatCoefficients,
        RewardLedger,
        RewardLedgerV4,
        RewardV4Coefficients,
    )

    if reward_version not in (1, 9, 10, 11, 12):
        raise ValueError(f"Unsupported reward version {reward_version}; use 1, 9, 10, 11 or 12")
    configs = {
        9: DEFAULT_CONFIG_V9,
        10: DEFAULT_CONFIG_V10,
        11: DEFAULT_CONFIG_V11,
        12: DEFAULT_CONFIG_V12,
    }
    coefficients = RewardV4Coefficients.load(configs.get(reward_version, DEFAULT_CONFIG_V9))
    contract_stall = coefficients.stall_seconds
    if contract_stall is not None:
        if stall_seconds is not None and stall_seconds != contract_stall:
            raise ValueError("The stall limit must match the reward contract")
    if gamma is None:
        coefficients = replace(coefficients, door_shaping_coefficient=0.0)
    accountant: RewardAccountant = (
        RewardLedgerV4(
            coefficients,
            stall_seconds=(
                (contract_stall or DEFAULT_STALL_SECONDS)
                if stall_seconds is None
                else stall_seconds
            ),
            gamma=gamma,
            novelty_counts=novelty_counts,
        )
        if reward_version in (9, 10, 11, 12)
        else RewardLedger(CombatCoefficients.load())
    )

    backend = LiveBackend(client, run_deadline=run_deadline, stop_file=stop_file)
    if stall_seconds is not None:
        backend.watchdog = StallWatchdog(stall_seconds, clock=clock)
    env = IsaacCombatEnv(
        backend,
        [LIVE_SCENARIO],
        action_repeat=action_repeat,
        accountant=accountant,
        oracle_sink=oracle_sink,
    )
    backend.on_stall = lambda: env.request_truncation("stall")
    return FaultTolerantEnv(
        env,
        max_faults=max_faults,
        on_record=record,
        run_deadline=run_deadline,
        max_consecutive_faults=max_consecutive_faults,
    )


@dataclass(frozen=True)
class LiveRunOptions:
    mode: Literal["random", "train", "evaluate"]
    out_dir: Path
    connection_timeout: float = 300.0
    steps: int = 3000
    minutes: float = 30.0
    max_faults: int = 20
    seed: int | None = None
    config_path: Path | None = None
    resume: bool = False
    launch_directory: Path | None = None
    port: int = 9528
    session_deadline: float | None = None
    stop_file: Path | None = None
    require_initial_isaac: bool = False
    # Evaluate mode only: a frozen policy under the training protocol; nothing is learned.
    eval_policy: Literal["checkpoint", "random", "random-prior"] | None = None
    eval_checkpoint: Path | None = None
    # Train mode: guarded game keyboard used to pause the game during updates (config flag
    # `live.pause_during_updates`); without one, pausing is skipped and recorded.
    keyboard: MenuInput | None = None

    def __post_init__(self) -> None:
        if self.session_deadline is not None and not math.isfinite(self.session_deadline):
            raise ValueError("Session deadline must be finite")
        if self.steps < 1 or not 0 < self.minutes <= TRAINING_MAX_SECONDS / 60:
            raise ValueError("Steps must be positive; minutes must be within the approval cap")
        if self.max_faults < 0 or self.connection_timeout <= 0:
            raise ValueError("Fault budget and connection timeout must be nonnegative/positive")
        if self.mode != "evaluate":
            if self.eval_policy is not None or self.eval_checkpoint is not None:
                raise ValueError("Evaluation policy options apply to evaluate mode only")
            return
        if self.resume:
            raise ValueError("Evaluation never resumes or writes a training lineage")
        if self.eval_policy == "checkpoint":
            if self.eval_checkpoint is None:
                raise ValueError("Checkpoint evaluation needs an exact checkpoint directory")
        elif self.eval_policy in ("random", "random-prior"):
            if self.eval_checkpoint is not None:
                raise ValueError(f"The {self.eval_policy} policy takes no checkpoint")
        else:
            raise ValueError(
                "Evaluate mode needs eval_policy 'checkpoint', 'random' or 'random-prior'"
            )


def run_live(
    options: LiveRunOptions, *, on_record: Callable[[str, Any], None] | None = None
) -> Path:
    """Listen, optionally launch Isaac, then act randomly or train; returns the log folder."""
    import subprocess
    import uuid

    import numpy as np

    from .launcher import EventLog, game_running, preflight

    stamp = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    logs = options.out_dir / "sessions" / stamp
    logs.mkdir(parents=True)
    print(f"Local logs: {logs}", flush=True)
    directory = preflight(options.launch_directory) if options.launch_directory else None
    with (
        EventLog(logs / "live.jsonl") as log,
        (logs / "oracle.jsonl").open("x", encoding="utf-8") as oracle,
    ):

        def sink(event: OracleEvent) -> None:
            oracle.write(event.model_dump_json() + "\n")

        def record(event: str, data: Any = None) -> None:
            log.record(event, data)
            if on_record is not None:
                on_record(event, data)

        record("configuration", {k: str(v) for k, v in vars(options).items()})
        client = LiveClient(
            ObserverConfig(
                port=options.port,
                accept_timeout=min(
                    options.connection_timeout,
                    max(0.001, (options.session_deadline or math.inf) - time.monotonic()),
                ),
                live_loop=True,
            ),
        )
        with client:
            record("listening", client.address)
            if directory is not None:
                if game_running():
                    raise ValueError("Another game instance appeared; launch cancelled")
                process = subprocess.Popen(
                    [str(directory / "isaac-ng.exe"), "--luadebug"], cwd=directory
                )
                log.record("launch_requested", {"launcher_pid": process.pid})
            print(
                "Waiting for the observer: select file 2 and start or continue a run.", flush=True
            )
            record("connected", client.connect().model_dump(mode="json"))
            try:
                if options.require_initial_isaac:
                    limit = min(time.monotonic() + 30, options.session_deadline or math.inf)
                    while True:
                        if options.stop_file is not None and options.stop_file.exists():
                            raise LiveSessionCancelled("User cancellation requested during startup")
                        remaining = limit - time.monotonic()
                        if remaining <= 0:
                            raise LiveBudgetExpired("Initial active Isaac deadline exhausted")
                        snap = client.take(min(3, remaining))
                        if snap.status != "active" or snap.player is None:
                            continue
                        if snap.player.character_type != 0:
                            raise ValueError(
                                "Initial active character is not Isaac; no learner created"
                            )
                        record(
                            "initial_isaac_verified",
                            {
                                "session": snap.session_id,
                                "epoch": snap.game_epoch,
                                "frame": snap.frame_id,
                                "character": 0,
                            },
                        )
                        break
                if options.mode == "random":
                    _random_run(client, options, record, sink, np.random.default_rng(options.seed))
                elif options.mode == "evaluate":
                    _evaluate_run(client, options, record, sink)
                else:
                    _train_run(client, options, record, sink)
            except LiveBudgetExpired as exc:
                record("budget", str(exc))
            except KeyboardInterrupt:
                record("stopped", "Operator interrupt; input released, game left running")
            except (BridgeError, ValueError) as exc:
                record("fault", str(exc))
                raise
    return logs


def _random_run(
    client: LiveClient,
    options: LiveRunOptions,
    record: Callable[[str, Any], None],
    sink: Callable[[OracleEvent], None],
    rng: Any,
) -> None:
    deadline = min(time.monotonic() + options.minutes * 60, options.session_deadline or math.inf)
    env: gym.Env[Any, Any] = make_live_env(
        client,
        max_faults=options.max_faults,
        record=record,
        oracle_sink=sink,
        run_deadline=deadline,
        stop_file=options.stop_file,
    )
    try:
        env.reset(seed=options.seed)
        for _ in range(options.steps):
            if time.monotonic() >= deadline:
                record("budget", "wall time reached")
                break
            _, _, terminated, truncated, _ = env.step(rng.integers(0, ACTION_NVEC))
            if terminated or truncated:
                env.reset()
    except LiveBudgetExpired:
        record("budget", "wall time reached")
    finally:
        env.close()


def _train_run(
    client: LiveClient,
    options: LiveRunOptions,
    record: Callable[[str, Any], None],
    sink: Callable[[OracleEvent], None],
) -> None:
    from .episode_metrics import EpisodeMetricsEnv, EpisodeMetricsWriter
    from .training import PURE_CONFIG, PureTrainingConfig, load_training_config, train
    from .update_pause import UpdatePause

    config, cfg_hash = load_training_config(options.config_path or PURE_CONFIG)
    reward_contract: RewardContract = LIVE_REWARD_CONTRACT
    seed = config.seed if options.seed is None else options.seed
    minutes = min(options.minutes, config.budget.wall_time_minutes)
    config = config.model_copy(
        update={"budget": config.budget.model_copy(update={"wall_time_minutes": minutes})}
    )
    record("training", {"config_hash": cfg_hash, "seed": seed, "status": config.status,
                        "reward_contract": reward_contract})  # fmt: skip
    deadline = min(time.monotonic() + minutes * 60, options.session_deadline or math.inf)

    pure = isinstance(config, PureTrainingConfig)
    counts = (
        NoveltyCounts()
        if isinstance(config, PureTrainingConfig) and config.contract.reward_version >= 11
        else None
    )
    writer = EpisodeMetricsWriter(options.out_dir / "metrics" / "episodes.csv") if pure else None
    pause = (
        UpdatePause(options.keyboard, record)
        if isinstance(config, PureTrainingConfig) and config.live.pause_during_updates
        else None
    )

    def factory(_: int) -> gym.Env[Any, Any]:
        env: gym.Env[Any, Any] = make_live_env(
            client,
            action_repeat=config.action_repeat_game_updates,
            # The pure profile has no total fault budget; the consecutive cap ends a session.
            max_faults=10**9 if pure else options.max_faults,
            record=record,
            oracle_sink=sink,
            run_deadline=deadline,
            stop_file=options.stop_file,
            reward_version=config.contract.reward_version
            if isinstance(config, PureTrainingConfig)
            else 9,
            gamma=config.hyperparameters.gamma
            if isinstance(config, PureTrainingConfig)
            else config.gamma,
            stall_seconds=config.watchdog.stall_seconds
            if isinstance(config, PureTrainingConfig)
            else None,
            max_consecutive_faults=config.budget.max_consecutive_faults
            if isinstance(config, PureTrainingConfig)
            else None,
            novelty_counts=counts,
        )
        return EpisodeMetricsEnv(env, writer) if writer is not None else env

    try:
        result = train(
            config,
            cfg_hash,
            seed=seed,
            env_factory=factory,
            out_dir=options.out_dir / f"seed-{seed}",
            resume=options.resume,
            max_timesteps=options.steps,
            reward_contract=reward_contract,
            run_deadline=deadline,
            on_progress=record,
            train_metrics_path=options.out_dir / "metrics" / "train.csv" if pure else None,
            update_pause=pause,
            novelty_counts=counts,
        )
    except LiveBudgetExpired as exc:
        record("budget", f"{exc}; unfinished rollout has no new checkpoint")
        return
    record("training_result", {k: str(v) for k, v in vars(result).items()})


def _evaluate_run(
    client: LiveClient,
    options: LiveRunOptions,
    record: Callable[[str, Any], None],
    sink: Callable[[OracleEvent], None],
) -> None:
    """Frozen evaluation under the training protocol: same env, no learning, no checkpoints."""
    from .baselines import Policy, RandomPolicy, RandomPriorPolicy
    from .checkpoint_policy import CheckpointPolicy
    from .episode_metrics import EpisodeMetricsEnv, EpisodeMetricsWriter
    from .training import PURE_CONFIG, PureTrainingConfig, load_training_config

    config, cfg_hash = load_training_config(options.config_path or PURE_CONFIG)
    if not isinstance(config, PureTrainingConfig):
        raise ValueError("Evaluation needs a config version 2 (pure) profile")
    seed = config.seed if options.seed is None else options.seed
    policy: Policy
    checkpoint: CheckpointPolicy | None = None
    if options.eval_policy == "checkpoint":
        assert options.eval_checkpoint is not None
        checkpoint = CheckpointPolicy(
            options.eval_checkpoint,
            expected_config_hash=cfg_hash,
            expected_seed=config.seed,
            expected_reward_contract=LIVE_REWARD_CONTRACT,
            deterministic=False,  # sample like training does
            sampling_seed=seed,
            observation_normalization=config.contract.observation_normalization,
        )
        policy = checkpoint
        identity = checkpoint.identity
        details: dict[str, Any] = {
            "checkpoint_id": identity.checkpoint_id,
            "timesteps": identity.timesteps,
        }
    else:
        if options.eval_policy == "random-prior":
            policy = RandomPriorPolicy(config.use_head_initial_none_probability)
        else:
            policy = RandomPolicy()
        details = {"checkpoint_id": None, "timesteps": None}
    record("evaluation", {"policy": options.eval_policy, **details, "config_hash": cfg_hash,
                          "seed": seed, "reward_contract": LIVE_REWARD_CONTRACT})  # fmt: skip
    deadline = min(time.monotonic() + options.minutes * 60, options.session_deadline or math.inf)
    writer = EpisodeMetricsWriter(options.out_dir / "metrics" / "episodes.csv")
    env: gym.Env[Any, Any] = EpisodeMetricsEnv(
        make_live_env(
            client,
            action_repeat=config.action_repeat_game_updates,
            max_faults=10**9,  # as in training, only the consecutive cap ends a session
            record=record,
            oracle_sink=sink,
            run_deadline=deadline,
            stop_file=options.stop_file,
            reward_version=config.contract.reward_version,
            gamma=config.hyperparameters.gamma,
            stall_seconds=config.watchdog.stall_seconds,
            max_consecutive_faults=config.budget.max_consecutive_faults,
            novelty_counts=NoveltyCounts(frozen=True),  # evaluation never writes counts
        ),
        writer,
    )
    episodes = steps = 0
    try:
        observation, _ = env.reset()
        policy.reset(seed)
        while True:
            if time.monotonic() >= deadline:
                raise LiveBudgetExpired("Live wall-time budget exhausted")
            observation, _, terminated, truncated, _ = env.step(policy.act(observation))
            steps += 1
            if terminated or truncated:
                episodes += 1
                observation, _ = env.reset()
                policy.reset(seed + episodes)
    finally:
        env.close()
        record("evaluation_result", {"episodes": episodes, "steps": steps})
        if checkpoint is not None:
            checkpoint.verify_unchanged()
