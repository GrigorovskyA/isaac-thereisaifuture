"""Pure offline lifecycle decision for ONE native step. No I/O, clock, threads or sender.

A READY decision only says the supplied facts are logically consistent. It is a local
candidate: not a delivered transaction, not a StepCompletion, not proof that input was
physically executed. See openspec/changes/episode-lifecycle/design.md (subtask 3.9).
"""

import re
from dataclasses import dataclass, fields
from typing import Literal

from .native_protocol import StepCommand
from .observation import ProtocolError

MAX_FACTS = 64
MAX_WAIT_MS = 250
_MAX = 2**53 - 1
_SESSION = re.compile(r"[0-9a-f]{32}")
_WINDOW = 15

State = Literal["waiting", "ready", "cancelled", "expired", "faulted", "unsupported_terminal"]
InterruptKind = Literal[
    "pause",
    "explicit_release",
    "input_fault",
    "death_candidate",
    "disconnect",
    "transport_fault",
    "authority_lost",
]
ContextKind = Literal["room_change", "floor_change", "epoch_change", "session_change"]
_INTERRUPTS = (
    "pause",
    "explicit_release",
    "input_fault",
    "death_candidate",
    "disconnect",
    "transport_fault",
    "authority_lost",
)
_CONTEXTS = ("room_change", "floor_change", "epoch_change", "session_change")
# kind -> (state, reason)
_INTERRUPT_OUTCOME: dict[str, tuple[State, str]] = {
    "pause": ("cancelled", "pause"),
    "explicit_release": ("cancelled", "explicit_release"),
    "input_fault": ("cancelled", "input_fault"),
    "death_candidate": ("unsupported_terminal", "death_candidate"),
    "disconnect": ("faulted", "disconnect"),
    "transport_fault": ("faulted", "transport_fault"),
    "authority_lost": ("expired", "authority_lost"),
}


def _int(value: object, name: str) -> None:
    if type(value) is not int or not 0 <= value <= _MAX:
        raise ProtocolError(f"{name} must be an integer in 0..2**53-1")


def _check(fact: object, ints: tuple[str, ...], session: bool = True) -> None:
    for name in ints:
        _int(getattr(fact, name), name)
    sid = getattr(fact, "session_id", None)
    if session and (type(sid) is not str or not _SESSION.fullmatch(sid)):
        raise ProtocolError("session_id must be 32 lowercase hex characters")


@dataclass(frozen=True, slots=True, kw_only=True)
class AcceptanceFact:
    """Command acceptance (the identity and frame of a CommandAck of kind action)."""

    at_ms: int
    session_id: str
    sequence: int
    game_epoch: int
    room_visit: int
    frame_id: int

    def __post_init__(self) -> None:
        _check(self, ("at_ms", "sequence", "game_epoch", "room_visit", "frame_id"))


@dataclass(frozen=True, slots=True, kw_only=True)
class IntervalFact:
    """Hypothetical adapter evidence of the exact consumed update interval."""

    at_ms: int
    session_id: str
    sequence: int
    game_epoch: int
    room_visit: int
    accepted_frame: int
    requested_updates: int
    elapsed_updates: int
    end_frame: int

    def __post_init__(self) -> None:
        _check(
            self,
            (
                "at_ms",
                "sequence",
                "game_epoch",
                "room_visit",
                "accepted_frame",
                "requested_updates",
                "elapsed_updates",
                "end_frame",
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ReleaseFact:
    """Caller assertion that bridge override was cleared; not final-input evidence."""

    at_ms: int
    session_id: str
    sequence: int
    game_epoch: int
    room_visit: int
    frame_id: int

    def __post_init__(self) -> None:
        _check(self, ("at_ms", "sequence", "game_epoch", "room_visit", "frame_id"))


@dataclass(frozen=True, slots=True, kw_only=True)
class SealFact:
    """Event stream explicitly complete through end_frame in this context."""

    at_ms: int
    session_id: str
    game_epoch: int
    room_visit: int
    end_frame: int
    last_event_id: int

    def __post_init__(self) -> None:
        _check(self, ("at_ms", "game_epoch", "room_visit", "end_frame", "last_event_id"))


@dataclass(frozen=True, slots=True, kw_only=True)
class InterruptFact:
    """An explicit interruption observed in the command's own context."""

    at_ms: int
    session_id: str
    sequence: int
    game_epoch: int
    room_visit: int
    frame_id: int
    kind: InterruptKind

    def __post_init__(self) -> None:
        _check(self, ("at_ms", "sequence", "game_epoch", "room_visit", "frame_id"))
        if self.kind not in _INTERRUPTS:
            raise ProtocolError("Unknown interrupt kind")


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextChangeFact:
    """The NEW context after a transition; its frame is never attached to the command."""

    at_ms: int
    session_id: str
    game_epoch: int
    room_visit: int
    frame_id: int
    kind: ContextKind

    def __post_init__(self) -> None:
        _check(self, ("at_ms", "game_epoch", "room_visit", "frame_id"))
        if self.kind not in _CONTEXTS:
            raise ProtocolError("Unknown context change kind")


@dataclass(frozen=True, slots=True, kw_only=True)
class ClockFact:
    """Time only: can expire a step, never complete it."""

    at_ms: int

    def __post_init__(self) -> None:
        _check(self, ("at_ms",), session=False)


Fact = (
    AcceptanceFact
    | IntervalFact
    | ReleaseFact
    | SealFact
    | InterruptFact
    | ContextChangeFact
    | ClockFact
)
_FACTS = (
    AcceptanceFact,
    IntervalFact,
    ReleaseFact,
    SealFact,
    InterruptFact,
    ContextChangeFact,
    ClockFact,
)


@dataclass(frozen=True, slots=True)
class StepCandidate:
    """Local, unserialized endpoint satisfying the full-interval invariants."""

    session_id: str
    sequence: int
    game_epoch: int
    room_visit: int
    accepted_frame: int
    end_frame: int
    requested_updates: int
    elapsed_updates: int
    last_event_id: int
    provenance: Literal["local_reducer_unverified"] = "local_reducer_unverified"


@dataclass(frozen=True, slots=True)
class StepDecision:
    """Immutable snapshot. `fresh` is true only on the submission that changed state."""

    state: State
    reason: str
    fresh: bool
    missing: tuple[str, ...]
    release_required: bool
    candidate: StepCandidate | None
    session_id: str
    sequence: int
    game_epoch: int
    room_visit: int
    facts_counted: int
    conflict_after_ready: bool


def _key(fact: Fact) -> tuple[object, ...]:
    """Identity of a fact's content: a replay at another time is still a duplicate."""
    return tuple((f.name, getattr(fact, f.name)) for f in fields(fact) if f.name != "at_ms")


class _Reject(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class NativeStepLifecycle:
    """One command, one decision. Terminal states are absorbing; nothing renews them."""

    def __init__(
        self,
        command: StepCommand,
        *,
        baseline_last_event_id: int,
        started_ms: int,
        deadline_ms: int,
    ) -> None:
        if not isinstance(command, StepCommand):
            raise ProtocolError("A validated StepCommand is required")
        for name, value in (
            ("baseline_last_event_id", baseline_last_event_id),
            ("started_ms", started_ms),
            ("deadline_ms", deadline_ms),
        ):
            _int(value, name)
        if not started_ms < deadline_ms <= started_ms + MAX_WAIT_MS:
            raise ProtocolError("Deadline must lie within the 250 ms authority window")
        self._sid, self._seq = command.session_id, command.sequence
        self._epoch, self._room = command.game_epoch, command.room_visit
        self._frame, self._frames = command.frame_id, command.frames
        self._baseline = baseline_last_event_id
        self._started, self._deadline = started_ms, deadline_ms
        self._last_at = started_ms
        self._count = 0
        self._ack: AcceptanceFact | None = None
        self._interval: IntervalFact | None = None
        self._release: ReleaseFact | None = None
        self._seal: SealFact | None = None
        self._release_ok = False
        self._release_floor = command.frame_id
        self._state: State = "waiting"
        self._reason = "awaiting_evidence"
        self._candidate: StepCandidate | None = None
        self._conflict = False

    def submit(self, fact: Fact) -> StepDecision:
        """Consume one fact. Never raises for a bad fact; it faults a waiting step."""
        self._count = min(self._count + 1, MAX_FACTS + 1)
        if self._state != "waiting":
            self._after_terminal(fact)
            return self._snapshot(False)
        if self._count > MAX_FACTS:
            return self._end("faulted", "overflow")
        if not isinstance(fact, _FACTS):
            return self._end("faulted", "malformed_fact")
        if fact.at_ms < self._last_at:
            return self._end("faulted", "timestamp_regression")
        self._last_at = fact.at_ms
        if fact.at_ms >= self._deadline:  # the deadline wins every tie
            return self._end("expired", "wall_deadline", late=fact)
        try:
            outcome = self._apply(fact)
        except _Reject as exc:
            return self._end("faulted", exc.reason)
        if outcome is not None:
            return self._end(*outcome)
        if self._ready():
            self._state, self._reason = "ready", "all_evidence_agrees"
            return self._snapshot(True)
        return self._snapshot(False)

    def _end(self, state: State, reason: str, late: Fact | None = None) -> StepDecision:
        self._state, self._reason, self._candidate = state, reason, None
        if late is not None:
            self._after_terminal(late)
        return self._snapshot(True)

    def _snapshot(self, fresh: bool) -> StepDecision:
        missing = tuple(
            name
            for name, value in (
                ("acceptance", self._ack),
                ("interval", self._interval),
                ("release", self._release),
                ("seal", self._seal),
            )
            if value is None
        )
        return StepDecision(
            state=self._state,
            reason=self._reason,
            fresh=fresh,
            missing=missing if self._state == "waiting" else (),
            release_required=not self._release_ok,
            candidate=self._candidate,
            session_id=self._sid,
            sequence=self._seq,
            game_epoch=self._epoch,
            room_visit=self._room,
            facts_counted=min(self._count, MAX_FACTS),
            conflict_after_ready=self._conflict,
        )

    def _after_terminal(self, fact: object) -> None:
        """Keep outcomes absorbing; validate bounded cleanup even after evidence overflow."""
        ready = self._state == "ready"
        if ready and self._count > MAX_FACTS:
            self._invalidate_ready()
        if not isinstance(fact, _FACTS) or fact.at_ms < self._last_at:
            if ready:
                self._invalidate_ready()
            return
        self._last_at = fact.at_ms
        if isinstance(fact, ReleaseFact):
            valid = (fact.session_id, fact.sequence, fact.game_epoch, fact.room_visit) == (
                self._sid,
                self._seq,
                self._epoch,
                self._room,
            ) and fact.frame_id >= self._release_floor
            if not valid:
                if ready:
                    self._invalidate_ready()
                return
            if ready and (self._release is None or _key(fact) != _key(self._release)):
                self._invalidate_ready()
            self._release, self._release_ok = fact, True
            self._raise_release_floor(fact.frame_id)
        elif ready and self._interval is not None:
            known = {_key(k) for k in (self._ack, self._interval, self._seal) if k is not None}
            if isinstance(fact, (InterruptFact, ContextChangeFact)):
                # READY is not delivered: even a later-frame transport fault blocks use.
                self._invalidate_ready()
            elif isinstance(fact, (AcceptanceFact, IntervalFact, SealFact)):
                if _key(fact) not in known:
                    self._invalidate_ready()
        if isinstance(fact, InterruptFact) and (
            fact.session_id,
            fact.sequence,
            fact.game_epoch,
            fact.room_visit,
        ) == (self._sid, self._seq, self._epoch, self._room):
            self._raise_release_floor(fact.frame_id)
        if isinstance(fact, ContextChangeFact):
            self._release_ok = False
            if (fact.session_id, fact.game_epoch) == (self._sid, self._epoch):
                self._raise_release_floor(fact.frame_id)

    def _invalidate_ready(self) -> None:
        """Previously returned snapshots stay immutable; subsequent ones withhold candidates."""
        self._conflict, self._candidate = True, None

    def _raise_release_floor(self, frame: int) -> None:
        self._release_floor = max(self._release_floor, frame)
        if self._release is not None and self._release.frame_id < self._release_floor:
            self._release_ok = False

    def _ident(self, fact: AcceptanceFact | IntervalFact | ReleaseFact | InterruptFact) -> None:
        if (fact.session_id, fact.sequence, fact.game_epoch, fact.room_visit) != (
            self._sid,
            self._seq,
            self._epoch,
            self._room,
        ):
            raise _Reject("foreign_context")

    def _window(self, frame: int) -> None:
        if frame < self._frame:
            raise _Reject("stale_fact")
        if frame > self._frame + _WINDOW:
            raise _Reject("contradictory_fact")

    def _apply(self, fact: Fact) -> tuple[State, str] | None:
        if isinstance(fact, ClockFact):
            return None
        if isinstance(fact, AcceptanceFact):
            self._on_ack(fact)
        elif isinstance(fact, IntervalFact):
            self._on_interval(fact)
        elif isinstance(fact, ReleaseFact):
            self._on_release(fact)
        elif isinstance(fact, SealFact):
            self._on_seal(fact)
        elif isinstance(fact, InterruptFact):
            return self._on_interrupt(fact)
        else:
            return self._on_context(fact)
        return None

    def _store(self, name: str, fact: Fact) -> bool:
        """Return False for an identical duplicate; reject a differing repeat."""
        current = getattr(self, name)
        if current is None:
            return True
        if _key(current) == _key(fact):
            return False
        raise _Reject("contradictory_fact")

    def _on_ack(self, fact: AcceptanceFact) -> None:
        self._ident(fact)
        self._window(fact.frame_id)
        if not self._store("_ack", fact):
            return
        if self._interval is not None and self._interval.accepted_frame != fact.frame_id:
            raise _Reject("contradictory_fact")
        if self._seal is not None and self._seal.end_frame <= fact.frame_id:
            raise _Reject("contradictory_fact")
        if self._release is not None and self._release.frame_id < fact.frame_id:
            self._release_ok = False
            raise _Reject("stale_fact")
        self._ack = fact
        self._raise_release_floor(fact.frame_id)

    def _on_interval(self, fact: IntervalFact) -> None:
        self._ident(fact)
        if fact.requested_updates != self._frames:
            raise _Reject("contradictory_fact")
        if (
            fact.elapsed_updates != fact.requested_updates
            or fact.end_frame - fact.accepted_frame != fact.elapsed_updates
        ):
            raise _Reject("partial_interval")
        self._window(fact.accepted_frame)
        if not self._store("_interval", fact):
            return
        if self._ack is not None and self._ack.frame_id != fact.accepted_frame:
            raise _Reject("contradictory_fact")
        if self._release is not None and self._release.frame_id < fact.end_frame:
            self._release_ok = False
            raise _Reject("contradictory_fact")
        if self._seal is not None and self._seal.end_frame != fact.end_frame:
            raise _Reject("contradictory_fact")
        self._interval = fact
        self._raise_release_floor(fact.end_frame)

    def _on_release(self, fact: ReleaseFact) -> None:
        self._ident(fact)
        if fact.frame_id < self._frame:
            raise _Reject("stale_fact")
        if self._ack is not None and fact.frame_id < self._ack.frame_id:
            raise _Reject("stale_fact")
        if not self._store("_release", fact):
            return
        if self._interval is not None and fact.frame_id < self._interval.end_frame:
            raise _Reject("contradictory_fact")
        self._release = fact
        self._release_ok = True
        self._raise_release_floor(fact.frame_id)

    def _on_seal(self, fact: SealFact) -> None:
        if (fact.session_id, fact.game_epoch, fact.room_visit) != (
            self._sid,
            self._epoch,
            self._room,
        ):
            raise _Reject("foreign_context")
        if fact.end_frame < self._frame:
            raise _Reject("stale_fact")
        if fact.last_event_id < self._baseline:
            raise _Reject("watermark_regression")
        if not self._store("_seal", fact):
            return
        if self._interval is not None and self._interval.end_frame != fact.end_frame:
            raise _Reject("contradictory_fact")
        if self._ack is not None and fact.end_frame <= self._ack.frame_id:
            raise _Reject("contradictory_fact")
        self._seal = fact

    def _on_interrupt(self, fact: InterruptFact) -> tuple[State, str]:
        self._ident(fact)
        if fact.frame_id < self._frame or (
            self._ack is not None and fact.frame_id < self._ack.frame_id
        ):
            raise _Reject("stale_fact")
        self._raise_release_floor(fact.frame_id)
        return _INTERRUPT_OUTCOME[fact.kind]

    def _on_context(self, fact: ContextChangeFact) -> tuple[State, str]:
        if fact.kind == "session_change":
            if fact.session_id == self._sid:
                raise _Reject("contradictory_fact")
            self._release_ok = False
            return "faulted", "session_changed"
        if fact.session_id != self._sid:
            raise _Reject("foreign_context")
        if fact.kind == "epoch_change":
            if fact.game_epoch < self._epoch:
                raise _Reject("stale_fact")
            if fact.game_epoch == self._epoch:
                raise _Reject("contradictory_fact")
            self._release_ok = False
            return "unsupported_terminal", "epoch_change"
        if fact.game_epoch != self._epoch:
            raise _Reject("foreign_context")
        if fact.frame_id < self._frame:
            raise _Reject("stale_fact")
        if fact.room_visit < self._room:
            raise _Reject("stale_fact")
        if fact.kind == "room_change" and fact.room_visit == self._room:
            raise _Reject("contradictory_fact")
        self._raise_release_floor(fact.frame_id)
        self._release_ok = False
        return "cancelled", "transition"

    def _ready(self) -> bool:
        ack, iv, rel, seal = self._ack, self._interval, self._release, self._seal
        if ack is None or iv is None or rel is None or seal is None:
            return False
        self._candidate = StepCandidate(
            session_id=self._sid,
            sequence=self._seq,
            game_epoch=self._epoch,
            room_visit=self._room,
            accepted_frame=iv.accepted_frame,
            end_frame=iv.end_frame,
            requested_updates=iv.requested_updates,
            elapsed_updates=iv.elapsed_updates,
            last_event_id=seal.last_event_id,
        )
        return True


__all__ = [
    "AcceptanceFact",
    "ClockFact",
    "ContextChangeFact",
    "IntervalFact",
    "InterruptFact",
    "NativeStepLifecycle",
    "ReleaseFact",
    "SealFact",
    "StepCandidate",
    "StepDecision",
]
