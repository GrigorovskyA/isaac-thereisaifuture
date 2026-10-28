"""Episode lifecycle: identity checks, outcomes and fault separation over a GameBackend.

A transport or identity fault is never returned as a transition and never counts as
a character death. See openspec change episode-lifecycle.
"""

from dataclasses import dataclass, field
from typing import Literal, NoReturn, Protocol

from .entities import EntityFrame, OracleDoor, OracleEvent
from .observation import BridgeError

Split = Literal["train", "validation", "test"]
Outcome = Literal["death", "cleared", "timeout", "unknown", "truncated"]
TerminalKind = Literal["player_died", "room_cleared"]
TERMINAL_KINDS: tuple[TerminalKind, ...] = ("player_died", "room_cleared")
ALL_TERMINAL_KINDS: frozenset[TerminalKind] = frozenset(TERMINAL_KINDS)
DIRECTIONS = ("none", "left", "right", "up", "down")
USES = ("none", "bomb", "active", "pillcard")
# Player hits by damage source counted by the observer (metrics only, never policy input).
HIT_SOURCES = ("enemy", "projectile", "own_bomb", "explosion", "spikes", "fire", "creep", "other")
HIT_FIELDS = tuple(f"hits_{name}" for name in HIT_SOURCES)
ACTION_NVEC = (len(DIRECTIONS), len(DIRECTIONS), len(USES))  # MultiDiscrete([5, 5, 4])


@dataclass(frozen=True)
class Scenario:
    """Enemy fields describe the room; the synthetic backend builds its room from them."""

    id: str
    split: Split
    difficulty: int
    max_game_updates: int | None  # None: no time cap (a live run ends by death or truncation)
    enemy_count: int
    enemy_hp: float
    allow_room_change: bool = False
    end_on_clear: bool = True  # False: a room clear is reward-relevant but never ends the episode

    def __post_init__(self) -> None:
        limit = self.max_game_updates
        if not self.id or self.difficulty < 1 or (limit is not None and limit < 1):
            raise ValueError("Scenario needs an id, difficulty >= 1 and a positive time limit")
        if self.enemy_count < 0 or self.enemy_hp <= 0:
            raise ValueError("Scenario enemy count must be >= 0 and enemy HP positive")


@dataclass(frozen=True)
class Action:
    """Independent move and shoot directions (0 none, 1 left, 2 right, 3 up, 4 down) and use.

    Use is 0 none, 1 bomb, 2 active item, 3 pill or card.
    """

    move: int = 0
    shoot: int = 0
    use: int = 0

    def __post_init__(self) -> None:
        if not (0 <= self.move < len(DIRECTIONS) and 0 <= self.shoot < len(DIRECTIONS)):
            raise ValueError("Action directions must be 0..4")
        if not 0 <= self.use < len(USES):
            raise ValueError("Action use must be 0..3")


@dataclass(frozen=True)
class StepResult:
    """One backend result.

    `terminal_coverage` lists the terminal kinds whose events the backend delivered
    exhaustively for this exact interval (previous frame, frame]. It is an explicit
    claim, never inferred from requested kinds, provenance or an empty `events`; the
    default (empty) means unknown for both kinds.
    """

    frame: EntityFrame
    events: tuple[OracleEvent, ...]
    terminal_coverage: frozenset[TerminalKind] = frozenset()
    # Oracle level index of the current room (reward key only, never a policy input).
    room_index: int | None = None
    # Oracle doors of the current room and whether enemies are present (door shaping labels only);
    # None doors means the backend has no door data.
    doors: tuple[OracleDoor, ...] | None = None
    enemies_present: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.terminal_coverage, frozenset) or not (
            self.terminal_coverage <= ALL_TERMINAL_KINDS
        ):
            raise ValueError(f"terminal_coverage must be a frozenset of {TERMINAL_KINDS}")


class GameBackend(Protocol):
    """The seam between episode logic and the real bridge or an offline simulator."""

    def start_episode(self, scenario: Scenario, seed: int | None) -> StepResult: ...

    def step(self, action: Action, repeat: int) -> StepResult:
        """Run up to `repeat` game updates, stopping early on a terminal event."""
        ...

    def release(self) -> None:
        """Neutral input; must be idempotent and safe after faults."""
        ...

    def close(self) -> None: ...


class EpisodeFault(BridgeError):
    """Infrastructure or identity fault; the episode is invalid, not lost or won."""


@dataclass
class EpisodeSummary:
    """Gameplay outcome facts, kept apart from training reward.

    `room_cleared` and `died` are True after a positive event, False only when that
    kind was covered over the whole episode and never occurred, otherwise None (unknown).
    """

    episode_id: int
    scenario_id: str
    split: Split
    outcome: Outcome | None = None
    steps: int = 0
    game_updates: int = 0
    damage_taken_half_hearts: float = 0.0
    enemy_hp_removed: float = 0.0
    enemies_spawned: int = 0
    enemies_killed: int = 0
    room_cleared: bool | None = None
    died: bool | None = None
    truncation_reason: str | None = None


@dataclass(frozen=True)
class FaultRecord:
    episode_id: int
    reason: str
    game_updates: int


@dataclass(frozen=True)
class Transition:
    episode_id: int
    step_index: int
    frame: EntityFrame
    events: tuple[OracleEvent, ...]
    terminated: bool
    truncated: bool
    outcome: Outcome | None
    summary: EpisodeSummary
    truncation_reason: str | None = None
    room_index: int | None = None
    doors: tuple[OracleDoor, ...] | None = None
    enemies_present: bool = False


@dataclass
class EpisodeController:
    backend: GameBackend
    repeat: int = 3
    faults: list[FaultRecord] = field(default_factory=list)
    _episode_id: int = 0
    _scenario: Scenario | None = None
    _running: bool = False
    _first_frame: EntityFrame | None = None
    _last_frame: EntityFrame | None = None
    _summary: EpisodeSummary | None = None
    _complete: set[TerminalKind] = field(default_factory=set)
    _observed: set[TerminalKind] = field(default_factory=set)
    _truncation: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.repeat <= 15:
            raise ValueError("Action repeat must be 1..15 game updates")

    @property
    def episode_id(self) -> int:
        return self._episode_id

    @property
    def running(self) -> bool:
        return self._running

    @property
    def last_updates(self) -> int:
        """Game updates elapsed in the current or most recent episode."""
        return self._updates() if self._last_frame is not None else 0

    def request_truncation(self, reason: str) -> None:
        """End the running episode as truncated after its next step (for example a stall)."""
        if not reason:
            raise ValueError("A truncation needs a reason")
        if not self._running:
            raise RuntimeError("No running episode to truncate")
        self._truncation = self._truncation or reason

    def start(self, scenario: Scenario, seed: int | None = None) -> Transition:
        if self._running:
            self.stop("restarted")
        self._truncation = None
        self._episode_id += 1
        self._scenario = scenario
        self._first_frame = self._last_frame = None
        self._summary = EpisodeSummary(self._episode_id, scenario.id, scenario.split)
        self._complete, self._observed = set(ALL_TERMINAL_KINDS), set()
        try:
            result = self.backend.start_episode(scenario, seed)
            self._accept(result, initial=True)
            if self._observed:
                # A reset must establish a playable baseline, never ignore a terminal event.
                raise EpisodeFault("Episode initial result contains a terminal event")
        except BaseException as exc:
            self._raise_fault(exc)
        self._running = True
        return self._transition(result, None)

    def step(self, action: Action) -> Transition:
        if not self._running or self._summary is None:
            raise RuntimeError("No running episode; call start() first")
        try:
            result = self.backend.step(action, self.repeat)
            self._accept(result, initial=False)
        except BaseException as exc:
            self._raise_fault(exc)
        self._summary.steps += 1
        return self._transition(result, self._outcome(result))

    def stop(self, reason: str = "stopped") -> None:
        """Release control; idempotent. Used on interruption and after every episode end."""
        self._running = False
        self.backend.release()

    def close(self) -> None:
        self.stop("closed")
        self.backend.close()

    def _updates(self) -> int:
        assert self._first_frame is not None and self._last_frame is not None
        return self._last_frame.frame_id - self._first_frame.frame_id

    def _raise_fault(self, exc: BaseException) -> NoReturn:
        """Record the fault, stop control, then raise it (wrapped when it is infrastructure)."""
        self._running = False
        updates = self._updates() if self._last_frame is not None else 0
        try:
            self.backend.release()
        except Exception:  # release must not hide the original fault
            pass
        if isinstance(exc, EpisodeFault):
            fault = exc
        elif isinstance(exc, (BridgeError, ValueError)):
            fault = EpisodeFault(f"Episode {self._episode_id} fault: {exc}")
        else:
            raise exc
        self.faults.append(FaultRecord(self._episode_id, str(fault), updates))
        if fault is exc:
            raise fault
        raise fault from exc

    def _accept(self, result: StepResult, *, initial: bool) -> None:
        frame = result.frame
        first, last = self._first_frame, self._last_frame
        scenario = self._scenario
        assert scenario is not None
        if first is not None and last is not None:
            if frame.session_id != first.session_id or frame.game_epoch != first.game_epoch:
                raise EpisodeFault("Session or game epoch changed during the episode")
            if frame.frame_id <= last.frame_id:
                raise EpisodeFault("Stale or repeated frame")
            if not scenario.allow_room_change and frame.room_visit != first.room_visit:
                raise EpisodeFault("Room changed during a single-room episode")
        elif not initial:
            raise EpisodeFault("Step before an initial frame")
        floor = last.frame_id if last is not None else frame.frame_id - 1
        for event in result.events:
            if event.session_id != frame.session_id or event.game_epoch != frame.game_epoch:
                raise EpisodeFault("Event identity differs from its frame")
            if not floor < event.frame_id <= frame.frame_id:
                raise EpisodeFault("Event outside the step interval")
        if first is None:
            self._first_frame = frame
        self._last_frame = frame
        # A kind stays complete only while every interval so far covered it.
        self._complete &= result.terminal_coverage
        kinds = {event.kind for event in result.events}
        self._observed |= {kind for kind in TERMINAL_KINDS if kind in kinds}

    def _outcome(self, result: StepResult) -> Outcome | None:
        kinds = {event.kind for event in result.events}
        scenario = self._scenario
        assert scenario is not None
        if "player_died" in kinds:
            return "death"  # death wins a same-interval tie with a clear
        if "room_cleared" in kinds and scenario.end_on_clear:
            # A clear is only resolved when no unreported death can precede or accompany it.
            return "cleared" if "player_died" in self._complete else "unknown"
        if self._truncation is not None:
            return "truncated"
        limit = scenario.max_game_updates
        if limit is not None and self._updates() >= limit:
            known_absent = self._complete == ALL_TERMINAL_KINDS and not self._observed
            return "timeout" if known_absent else "unknown"
        return None

    def _fact(self, kind: TerminalKind) -> bool | None:
        if kind in self._observed:
            return True
        return False if kind in self._complete else None

    def _transition(self, result: StepResult, outcome: Outcome | None) -> Transition:
        summary = self._summary
        assert summary is not None and self._last_frame is not None
        for event in result.events:
            if event.kind == "enemy_spawned":
                summary.enemies_spawned += 1
            elif event.kind == "enemy_damaged" and event.amount is not None:
                summary.enemy_hp_removed += event.amount
            elif event.kind == "enemy_killed":
                summary.enemies_killed += 1
            elif event.kind == "player_damaged" and event.amount is not None:
                summary.damage_taken_half_hearts += event.amount
        oracle_stats = getattr(self.backend, "episode_oracle_stats", None)
        if oracle_stats is not None:  # the live observer counts kills; no enemy_killed events
            summary.enemies_killed = int(oracle_stats()["kills"])
        summary.game_updates = self._updates()
        summary.died = self._fact("player_died")
        summary.room_cleared = self._fact("room_cleared")
        reason = {"truncated": self._truncation, "timeout": "timeout", "unknown": "unknown"}.get(
            outcome or ""
        )
        if outcome is not None:
            summary.outcome = outcome
            summary.truncation_reason = reason
            self._running = False
            self.backend.release()
        return Transition(
            self._episode_id,
            summary.steps,
            result.frame,
            result.events,
            terminated=outcome in ("death", "cleared"),
            truncated=outcome in ("timeout", "unknown", "truncated"),
            outcome=outcome,
            summary=summary,
            truncation_reason=reason,
            room_index=result.room_index,
            doors=result.doors,
            enemies_present=result.enemies_present,
        )
