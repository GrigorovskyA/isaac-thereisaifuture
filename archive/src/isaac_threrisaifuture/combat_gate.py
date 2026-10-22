"""Opt-in operator-gated combat experience for live runs (openspec combat-experience-gate-v1).

The learner acts only during observed eligible combat. Between encounters the gate releases
input and waits, inside `reset()`, for an explicit operator readiness token bound to the
current request, session, game epoch and room visit. Waiting therefore produces no
observation, decision, rollout sample, normalizer update or reward; SB3 auto-reset keeps the
terminal step and the recurrent episode boundary.

Eligibility is management metadata from the separate oracle block. It never reaches the
encoder, policy, recurrent state, normalizer or reward ledger.
"""

import errno
import os
import secrets
import sys
import time
from collections import Counter as Tally
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Literal, SupportsFloat

import gymnasium as gym
from pydantic import Field, ValidationError

from .combat_progress import (
    CombatDiagnosticStop,
    CombatProgressMonitor,
    CombatTrace,
    validate_limits,
)
from .live import TRAINING_MAX_SECONDS, LiveBackend, LiveBudgetExpired, LiveSnapshot
from .observation import BridgeError, Counter, ProtocolError, SessionId, WireModel

Eligibility = Literal[
    "combat", "cleared", "empty", "dead", "paused", "transition", "ambiguous", "unavailable"
]
GateState = Literal["waiting_for_operator", "ready_pending", "combat_active", "stopped"]
REQUEST_NAME = "request.json"
READY_NAME = "ready.json"
MAX_ACK_BYTES = 4096
FUTURE_SKEW_SECONDS = 5.0
RequestId = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]
Timestamp = Annotated[float, Field(ge=0, le=1e11)]
IO_WINDOW_SECONDS = 0.25
IO_RETRY_SECONDS = 0.01
IO_MAX_ATTEMPTS = 26


class CombatGateExpired(LiveBudgetExpired):
    """The operator-wait cap expired; the run stops and is never renewed."""


class GateError(ValueError):
    """The readiness command cannot write an acknowledgment."""


def provenance(snap: LiveSnapshot | None) -> tuple[str, int, int] | None:
    if snap is None or snap.entity_frame is None:
        return None
    frame = snap.entity_frame
    return frame.session_id, frame.game_epoch, frame.room_visit


def classify(snap: LiveSnapshot | None, previous: LiveSnapshot | None = None) -> Eligibility:
    """Conservative eligibility; unknown or incomplete data is never combat."""
    if snap is None or snap.status == "unavailable":
        return "unavailable"
    if snap.status == "paused":
        return "paused"
    oracle = snap.oracle
    if snap.entity_frame is None or oracle is None:
        return "unavailable"
    if oracle.player_dead:
        return "dead"
    if previous is not None and provenance(previous) != provenance(snap):
        return "transition"
    if oracle.enemy_overflow > 0:
        return "ambiguous"
    if oracle.room_clear:
        return "cleared"
    if not any(enemy.hp > 0 for enemy in oracle.enemies):
        return "empty"
    return "combat"


class ReadinessRequest(WireModel):
    type: Literal["combat_gate_request"] = "combat_gate_request"
    version: Literal[1] = 1
    request_id: RequestId
    handoff: Annotated[int, Field(ge=1)]
    state: GateState
    issued_at: Timestamp
    session_id: SessionId | None
    game_epoch: Counter | None
    room_visit: Counter | None
    eligibility: Eligibility


class ReadinessAck(WireModel):
    type: Literal["combat_gate_ready"] = "combat_gate_ready"
    version: Literal[1] = 1
    request_id: RequestId
    session_id: SessionId
    game_epoch: Counter
    room_visit: Counter
    acked_at: Timestamp


def _file_operation[T](
    operation: Callable[[], T], deadline: float | None = None, *, final_attempt: bool = False
) -> T:
    """Retry Windows sharing conflicts only, without renewing a caller's budget."""
    limit = time.monotonic() + IO_WINDOW_SECONDS
    if deadline is not None:
        limit = min(limit, deadline)
    first: OSError | None = None
    for attempt in range(IO_MAX_ATTEMPTS):
        now = time.monotonic()
        if deadline is not None and now >= deadline and not (final_attempt and attempt == 0):
            raise LiveBudgetExpired("Combat gate file I/O deadline expired") from first
        if first is not None and now >= limit:
            raise first
        try:
            return operation()
        except OSError as exc:
            windows_conflict = getattr(exc, "winerror", None) in (5, 32) or (
                sys.platform == "win32"
                and isinstance(exc, PermissionError)
                and exc.errno == errno.EACCES
                and getattr(exc, "winerror", None) is None
            )
            if not windows_conflict:
                raise
            if first is None:
                first = exc
            remaining = limit - time.monotonic()
            if remaining <= 0 or attempt == IO_MAX_ATTEMPTS - 1:
                if deadline is not None and time.monotonic() >= deadline:
                    raise LiveBudgetExpired("Combat gate file I/O deadline expired") from first
                raise first from None
            time.sleep(min(IO_RETRY_SECONDS, remaining))
    raise AssertionError("Unreachable file retry state")


def _remove(path: Path, deadline: float | None = None, *, final_attempt: bool = False) -> None:
    _file_operation(lambda: path.unlink(missing_ok=True), deadline, final_attempt=final_attempt)


def _read(path: Path, deadline: float | None = None) -> bytes:
    def read() -> bytes:
        with path.open("rb") as stream:
            return stream.read(MAX_ACK_BYTES + 1)

    return _file_operation(read, deadline)


def _write_atomic(
    path: Path, data: str, deadline: float | None = None, *, final_attempt: bool = False
) -> None:
    temporary = path.with_name(path.name + "." + secrets.token_hex(8) + ".tmp")
    prepared = False

    def publish() -> None:
        nonlocal prepared
        if not prepared:
            temporary.write_text(data, encoding="utf-8")
            prepared = True
        os.replace(temporary, path)

    try:
        _file_operation(publish, deadline, final_attempt=final_attempt)
    finally:
        # Do not spend another retry window or hide the publication error.
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def write_readiness(
    session_dir: Path, request_id: str | None = None, *, now: float | None = None
) -> Path:
    """Operator step: acknowledge the current request; writes only `combat_gate/ready.json`."""
    gate_dir = session_dir / "combat_gate"
    try:
        raw = _read(gate_dir / REQUEST_NAME)
    except OSError as exc:
        raise GateError(f"No combat-gate request in {gate_dir}") from exc
    try:
        if len(raw) > MAX_ACK_BYTES:
            raise GateError("The combat-gate request is oversized")
        request = ReadinessRequest.model_validate_json(raw)
    except ValidationError as exc:
        raise GateError("The combat-gate request is invalid") from exc
    if request.state == "stopped":
        raise GateError("The gated run has stopped; nothing to acknowledge")
    if request_id is not None and request_id != request.request_id:
        raise GateError("The request id does not match the current handoff request")
    if request.session_id is None or request.game_epoch is None or request.room_visit is None:
        raise GateError("No observed game state yet; wait for the room to appear")
    ack = ReadinessAck(
        request_id=request.request_id,
        session_id=request.session_id,
        game_epoch=request.game_epoch,
        room_visit=request.room_visit,
        acked_at=time.time() if now is None else now,
    )
    target = gate_dir / READY_NAME
    _write_atomic(target, ack.model_dump_json())
    return target


@dataclass(frozen=True)
class GateConfig:
    directory: Path  # fixed per-session <logs>/combat_gate
    wait_cap_seconds: float = 600.0
    poll_seconds: float = 0.25
    stale_seconds: float = 1.0  # observer samples every 50 ms; older state cannot authorize
    max_deaths: int | None = None
    combat_trace_bytes: int = 0
    combat_progress_updates: int | None = None

    def __post_init__(self) -> None:
        validate_limits(self.combat_trace_bytes, self.combat_progress_updates)
        if self.max_deaths is not None and (
            type(self.max_deaths) is not int or not 1 <= self.max_deaths <= 10
        ):
            raise ValueError("Death limit must be an integer in 1..10")
        if not 0 < self.wait_cap_seconds <= TRAINING_MAX_SECONDS:
            raise ValueError("Operator wait cap must be positive and within the approval cap")
        if not 0 < self.poll_seconds <= 5:
            raise ValueError("Poll interval must be within (0, 5] seconds")
        if not self.poll_seconds <= self.stale_seconds <= 30:
            raise ValueError("Staleness window must be within [poll interval, 30] seconds")


@dataclass
class GateStats:
    handoffs: int = 0
    accepted: int = 0
    rejected: Tally[str] = field(default_factory=Tally)
    wait_seconds: float = 0.0
    wait_snapshots: int = 0
    wait_room_changes: int = 0
    resume_races: int = 0
    observation_gaps: int = 0
    withheld_actions: int = 0
    combat_steps: int = 0
    combat_reward: float = 0.0
    outcomes: Tally[str] = field(default_factory=Tally)

    def as_record(self) -> dict[str, Any]:
        return {
            "handoffs": self.handoffs,
            "accepted": self.accepted,
            "rejected": dict(self.rejected),
            "wait_seconds": round(self.wait_seconds, 3),
            "wait_snapshots": self.wait_snapshots,
            "wait_room_changes": self.wait_room_changes,
            "resume_races": self.resume_races,
            "observation_gaps": self.observation_gaps,
            "withheld_actions": self.withheld_actions,
            "combat_decisions": self.combat_steps,
            "combat_reward": self.combat_reward,
            "outcomes": dict(self.outcomes),
        }


class CombatGateEnv(gym.Wrapper[Any, Any, Any, Any]):
    """Gates a live env; see the module docstring and docs/COMBAT_EXPERIENCE_GATE.md."""

    def __init__(
        self,
        env: gym.Env[Any, Any],
        config: GateConfig,
        *,
        run_deadline: float | None = None,
        record: Callable[[str, Any], None] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        super().__init__(env)
        controller = getattr(env.unwrapped, "controller", None)
        backend = getattr(controller, "backend", None)
        if not isinstance(backend, LiveBackend):
            raise TypeError("The combat gate needs a live environment over a LiveBackend")
        self.backend = backend
        self.config = config
        self.run_deadline = run_deadline
        self.record = record
        self.clock = clock
        self.state: GateState = "waiting_for_operator"
        self.stats = GateStats()
        self._request: ReadinessRequest | None = None
        self._consumed: set[str] = set()
        self._episode: tuple[str, int, int] | None = None
        self._episode_steps = 0
        self._episode_return = 0.0
        self._collection_boundary: dict[str, Any] | None = None
        self._last_progress = 0.0
        self.cleanup_errors: list[str] = []
        self._diagnostic_stop: str | None = None
        self._diagnostic_before: tuple[LiveSnapshot, Any] | None = None
        self._trace = (
            CombatTrace(config.directory / "diagnostics", config.combat_trace_bytes)
            if config.combat_trace_bytes
            else None
        )
        self._combat_progress = (
            CombatProgressMonitor(config.combat_progress_updates)
            if config.combat_progress_updates is not None
            else None
        )
        holders: list[Any] = [backend]
        layer: Any = env
        while True:
            if hasattr(layer, "run_deadline"):
                holders.append(layer)
            if not isinstance(layer, gym.Wrapper):
                break
            layer = layer.env
        self._deadline_holders = holders
        backend.action_gate = self._veto
        config.directory.mkdir(parents=True, exist_ok=True)
        if self._trace is not None or self._combat_progress is not None:
            self._log(
                "diagnostic_limits",
                combat_trace_bytes=config.combat_trace_bytes,
                combat_progress_updates=config.combat_progress_updates,
                coverage="combat_endpoints_only",
            )

    # --- reset: the operator handoff ----------------------------------------------------

    def end_collection_segment(self) -> dict[str, Any]:
        """Release before optimizer work; only reset may authorize collection again."""
        self._check_diagnostic_stop()
        self._check_deadlines(time.monotonic(), self.run_deadline or float("inf"))
        if self.state != "combat_active" or self._collection_boundary is not None:
            raise GateError("No active collection segment to end")
        snap = self.backend.latest
        if snap is None:
            raise GateError("Collection boundary has no live frame")
        self._set_state("waiting_for_operator")
        ack = self.backend.client.command("release", snap)
        if ack.status != "accepted":
            raise GateError("Collection release was rejected")
        self._release()
        boundary = {
            "session_id": snap.session_id,
            "game_epoch": snap.game_epoch,
            "frame_id": snap.frame_id,
            "room_visit": snap.room.visit_id if snap.room is not None else None,
            "monotonic": time.monotonic(),
            "steps": self._episode_steps,
            "segment_return": self._episode_return,
        }
        self._collection_boundary = boundary
        self._set_state("waiting_for_operator")
        self._log("collection_segment_ended", **boundary)
        return dict(boundary)

    def reset(self, **kwargs: Any) -> tuple[Any, dict[str, Any]]:
        self._check_diagnostic_stop()
        if self.state == "stopped":
            raise RuntimeError("The combat gate has stopped")
        self._release()
        started = time.monotonic()
        cap = started + self.config.wait_cap_seconds
        try:
            with self._bounded(cap):
                if (
                    self.config.max_deaths is not None
                    and self.stats.outcomes["death"] >= self.config.max_deaths
                ):
                    raise LiveBudgetExpired("Death limit reached")
                self._issue("episode_end" if self.stats.handoffs else "run_start")
                return self._wait(started, cap, **kwargs)
        except BaseException as exc:
            self.stats.wait_seconds += time.monotonic() - started
            self._stop(f"{type(exc).__name__}: {exc}", deadline=cap)
            if self.cleanup_errors:
                exc.add_note("Combat gate cleanup: " + "; ".join(self.cleanup_errors))
            expired = self._expired(exc, cap)
            if expired is not None:
                raise expired from exc
            raise

    def _wait(self, started: float, cap: float, **kwargs: Any) -> tuple[Any, dict[str, Any]]:
        latest: LiveSnapshot | None = None
        fresh_at = started
        observed: tuple[str | None, int | None, int | None, Eligibility] | None = None
        accepted: tuple[str, int, int] | None = None
        while True:
            now = time.monotonic()
            self._check_deadlines(now, cap)
            snap, seen = self.backend.poll(min(self.config.poll_seconds, cap - now))
            self.stats.wait_snapshots += seen
            now = time.monotonic()
            self._check_deadlines(now, cap)
            if snap is not None:
                kind = classify(snap, latest)
                if kind == "transition" and latest is not None:
                    self.stats.wait_room_changes += 1
                latest, fresh_at = snap, now
                key = (*(provenance(snap) or (None, None, None)), kind)
                if key != observed:
                    observed = key
                    self._observe(snap, kind)
            elif latest is not None and (
                not self.backend.client.connected or now - fresh_at > self.config.stale_seconds
            ):
                # A gap or disconnect: retained state must not authorize a resume.
                latest, observed = None, None
                self.stats.observation_gaps += 1
                self._observe(None, "unavailable")
            if accepted is None:
                accepted = self._judge_ack(latest)
                if accepted is not None:
                    self._set_state("ready_pending")
            if accepted is not None and provenance(latest) == accepted:
                if latest is not None and classify(latest) == "combat":
                    result = self._resume(accepted, latest, started, cap, **kwargs)
                    if result is not None:
                        return result
                    accepted, latest, observed = None, None, None
            elif accepted is not None:
                self._log("ready_revoked", reason="provenance_changed")
                accepted = None
                self._issue("ready_revoked")

    def _resume(
        self,
        accepted: tuple[str, int, int],
        previous: LiveSnapshot,
        started: float,
        cap: float,
        **kwargs: Any,
    ) -> tuple[Any, dict[str, Any]] | None:
        # Every reset/reconnect below sees the narrowed deadline via _bounded().
        obs, info = self.env.reset(**kwargs)  # deriver/ledger baselines restart here
        self._check_deadlines(time.monotonic(), cap)
        current = self.backend.latest
        if provenance(current) == accepted and classify(current, previous) == "combat":
            assert current is not None
            waited = time.monotonic() - started
            self.stats.wait_seconds += waited
            self._episode = accepted
            self._episode_steps, self._episode_return = 0, 0.0
            self._diagnostic_reset(current, obs)
            self._set_state("combat_active")
            if self._collection_boundary is not None:
                boundary = self._collection_boundary
                self._log(
                    "collection_refreshed",
                    previous=boundary,
                    session_id=current.session_id,
                    game_epoch=current.game_epoch,
                    frame_id=current.frame_id,
                    room_visit=current.room.visit_id if current.room is not None else None,
                    elapsed_seconds=max(0.0, time.monotonic() - boundary["monotonic"]),
                    coverage="unknown_idle_gap_no_transition_or_outcome",
                )
                self._collection_boundary = None
            self._log(
                "combat_resumed", wait_seconds=round(waited, 3), episode_id=info.get("episode_id")
            )
            return obs, info
        self.stats.resume_races += 1
        self._log("resume_race", eligibility=classify(current, previous))
        self._release()
        self._issue("resume_race")
        return None

    # --- step: combat only --------------------------------------------------------------

    def step(self, action: Any) -> tuple[Any, SupportsFloat, bool, bool, dict[str, Any]]:
        self._check_diagnostic_stop()
        if self.state != "combat_active":
            raise RuntimeError(f"No gated combat episode (state {self.state}); call reset()")
        self.backend.blocked = None
        obs, reward, terminated, truncated, info = self.env.step(action)
        withheld = self.backend.blocked
        self.stats.combat_steps += 1
        self.stats.combat_reward += float(reward)
        self._episode_steps += 1
        self._episode_return += float(reward)
        now = time.monotonic()
        if now - self._last_progress >= 1.0:
            self._last_progress = now
            self._log(
                "combat_progress",
                combat_decisions=self.stats.combat_steps,
                withheld_actions=self.stats.withheld_actions,
            )
        exit_reason = None
        if withheld is not None:
            self.stats.withheld_actions += 1
            info = {**info, "action_withheld": withheld}
        if not (terminated or truncated):
            exit_reason = withheld or self._ineligible(self.backend.latest)
            if exit_reason is not None:
                truncated = True  # no fabricated clear/death; the next action is never sent
                info = {**info, "gate_exit": exit_reason}
        if terminated or truncated:
            self._release()
            outcome = info.get("outcome") or ("fault" if "fault" in info else exit_reason)
            self.stats.outcomes[str(outcome)] += 1
            self._log(
                "combat_ended",
                outcome=outcome,
                gate_exit=exit_reason,
                action_withheld=withheld,
                fault=info.get("fault"),
                steps=self._episode_steps,
                episode_return=self._episode_return,
            )
            self._set_state("waiting_for_operator")
        self._diagnostic_step(action, obs, terminated, truncated, withheld, info.get("fault"))
        return obs, reward, terminated, truncated, info

    def _check_diagnostic_stop(self) -> None:
        if self._diagnostic_stop is not None:
            reason = self._diagnostic_stop
            self._stop(reason)
            raise CombatDiagnosticStop(reason)

    def _diagnostic_reset(self, snap: LiveSnapshot | None, obs: Any) -> None:
        if self._trace is None and self._combat_progress is None:
            return
        assert snap is not None
        self._diagnostic_before = (snap, obs.copy())
        if self._combat_progress is not None:
            self._combat_progress.begin(snap)

    def _diagnostic_step(
        self,
        action: Any,
        obs: Any,
        terminated: bool,
        truncated: bool,
        withheld: str | None,
        fault: str | None,
    ) -> None:
        if self._diagnostic_before is None:
            return
        before, previous_obs = self._diagnostic_before
        after = self.backend.latest
        if after is None:
            raise ProtocolError("Combat diagnostic result snapshot is unavailable")
        if self._trace is not None and not self._trace.transition(
            before,
            previous_obs,
            after,
            obs,
            action,
            terminated=terminated,
            truncated=truncated,
            action_withheld=withheld,
            fault=fault,
        ):
            self._diagnostic_stop = "Combat diagnostic byte limit reached; capture incomplete"
        if self._combat_progress is not None and self._combat_progress.transition(
            before,
            after,
            eligible=withheld is None and classify(before) == "combat",
        ):
            self._diagnostic_stop = (
                "Combat registered-progress window exhausted: "
                f"{self._combat_progress.updates_without_progress} game updates; "
                "endpoint coverage is partial, actual damage is unknown"
            )
        self._diagnostic_before = (after, obs.copy())
        if self._diagnostic_stop is not None:
            self._release()
            self._log(
                "diagnostic_stop_pending",
                reason=self._diagnostic_stop,
                combat_decisions=self.stats.combat_steps,
                trace_records=self._trace.records if self._trace is not None else None,
                trace_bytes=self._trace.bytes_written if self._trace is not None else None,
                updates_without_progress=(
                    self._combat_progress.updates_without_progress
                    if self._combat_progress is not None
                    else None
                ),
            )

    def _ineligible(self, snap: LiveSnapshot | None) -> str | None:
        if snap is not None and provenance(snap) not in (None, self._episode):
            return "room_changed"
        kind = classify(snap)
        return None if kind == "combat" else kind

    def _veto(self, snap: LiveSnapshot | None) -> str | None:
        """Backend hook: checked on fresh transport state before any action is sent."""
        if self.state != "combat_active":
            return "not_active"
        return self._ineligible(snap)

    def close(self) -> None:
        try:
            if self.state != "stopped":
                self._stop("closed")
        finally:
            super().close()

    # --- handshake ----------------------------------------------------------------------

    def _issue(self, reason: str) -> None:
        self.stats.handoffs += 1
        _remove(self.config.directory / READY_NAME, self.backend.run_deadline)
        self._request = ReadinessRequest(
            request_id=secrets.token_hex(16),
            handoff=self.stats.handoffs,
            state="waiting_for_operator",
            issued_at=self.clock(),
            session_id=None,
            game_epoch=None,
            room_visit=None,
            eligibility="unavailable",
        )
        self.state = "waiting_for_operator"
        self._write_request()
        self._log("wait_started", reason=reason, request_id=self._request.request_id)
        print(
            f"Combat gate: input released (handoff {self.stats.handoffs}, {reason}). Navigate to "
            "a fight, then run: .venv\\Scripts\\python.exe -m isaac_threrisaifuture.cli "
            f'combat-ready --session-dir "{self.config.directory.parent}"',
            flush=True,
        )

    def _observe(self, snap: LiveSnapshot | None, kind: Eligibility) -> None:
        assert self._request is not None
        session, epoch, visit = provenance(snap) or (None, None, None)
        self._request = self._request.model_copy(
            update={
                "session_id": session,
                "game_epoch": epoch,
                "room_visit": visit,
                "eligibility": kind,
            }
        )
        self._write_request()
        self._log("observed", eligibility=kind, game_epoch=epoch, room_visit=visit)

    def _judge_ack(self, latest: LiveSnapshot | None) -> tuple[str, int, int] | None:
        path = self.config.directory / READY_NAME
        try:
            raw = _read(path, self.backend.run_deadline)
        except FileNotFoundError:
            return None
        _remove(path, self.backend.run_deadline)
        try:
            ack = ReadinessAck.model_validate_json(raw) if len(raw) <= MAX_ACK_BYTES else None
        except ValidationError:
            ack = None
        reason = self._reject_reason(ack, latest)
        if reason is not None:
            self.stats.rejected[reason] += 1
            self._log("ready_rejected", reason=reason)
            return None
        assert ack is not None and self._request is not None
        self._consumed.add(ack.request_id)
        self.stats.accepted += 1
        self._log("ready_accepted", request_id=ack.request_id, game_epoch=ack.game_epoch,
                  room_visit=ack.room_visit)  # fmt: skip
        return ack.session_id, ack.game_epoch, ack.room_visit

    def _reject_reason(self, ack: ReadinessAck | None, latest: LiveSnapshot | None) -> str | None:
        request = self._request
        assert request is not None
        if ack is None:
            return "invalid"
        if ack.request_id in self._consumed:
            return "replayed"
        if ack.request_id != request.request_id:
            return "stale_request"
        if ack.acked_at < request.issued_at:
            return "predates_wait"
        if ack.acked_at > self.clock() + FUTURE_SKEW_SECONDS:
            return "future_timestamp"
        current = provenance(latest)
        if current is None:
            return "no_observation"
        if ack.session_id != current[0]:
            return "cross_session"
        if ack.game_epoch != current[1]:
            return "cross_epoch"
        if ack.room_visit != current[2]:
            return "cross_room"
        if classify(latest) != "combat":
            return "not_eligible"
        return None

    # --- helpers ------------------------------------------------------------------------

    def _release(self) -> None:
        controller = getattr(self.env.unwrapped, "controller", None)
        if controller is not None and controller.running:
            controller.stop("combat_gate")
        else:
            self.backend.release()

    def _stop(self, reason: str, *, deadline: float | None = None) -> None:
        errors: list[str] = []
        try:
            self._release()
        except Exception as exc:
            errors.append(f"release: {type(exc).__name__}: {exc}")
        self.state = "stopped"
        if self._request is not None:
            self._request = self._request.model_copy(update={"state": "stopped"})
            try:
                self._write_request(deadline=deadline, final_attempt=True)
            except Exception as exc:
                errors.append(f"request: {type(exc).__name__}: {exc}")
        try:
            limit = self.backend.run_deadline
            if deadline is not None:
                limit = min(limit, deadline) if limit is not None else deadline
            _remove(self.config.directory / READY_NAME, limit, final_attempt=True)
        except Exception as exc:
            errors.append(f"ready: {type(exc).__name__}: {exc}")
        self.cleanup_errors = errors
        for event, payload in (
            ("stopped", {"reason": reason, "cleanup_errors": errors}),
            ("summary", self.stats.as_record()),
        ):
            try:
                self._log(event, **payload)
            except Exception as exc:
                errors.append(f"log: {type(exc).__name__}: {exc}")

    @contextmanager
    def _bounded(self, limit: float) -> Iterator[None]:
        """Narrow every shared deadline to `limit` for the handoff; restore it afterwards."""
        saved = [holder.run_deadline for holder in self._deadline_holders]
        for holder, old in zip(self._deadline_holders, saved, strict=True):
            holder.run_deadline = limit if old is None else min(old, limit)
        try:
            yield
        finally:
            for holder, old in zip(self._deadline_holders, saved, strict=True):
                holder.run_deadline = old

    def _check_deadlines(self, now: float, cap: float) -> None:
        if self.run_deadline is not None and now >= self.run_deadline:
            raise LiveBudgetExpired("Live wall-time budget exhausted during the handoff")
        if now >= cap:
            raise CombatGateExpired("Operator wait cap expired without readiness")

    def _expired(self, exc: BaseException, cap: float) -> BaseException | None:
        """Report a narrowed-deadline expiry as the cap or global budget it really was."""
        if isinstance(exc, CombatGateExpired | ProtocolError) or not isinstance(exc, BridgeError):
            return None
        now = time.monotonic()
        if self.run_deadline is not None and now >= self.run_deadline:
            return None if isinstance(exc, LiveBudgetExpired) else LiveBudgetExpired(str(exc))
        if now >= cap:
            return CombatGateExpired(f"Operator wait cap expired during the handoff: {exc}")
        return None

    def _set_state(self, state: GateState) -> None:
        self.state = state
        if self._request is not None and self._request.state != state:
            self._request = self._request.model_copy(update={"state": state})
            self._write_request()

    def _write_request(self, *, deadline: float | None = None, final_attempt: bool = False) -> None:
        assert self._request is not None
        limit = self.backend.run_deadline
        if deadline is not None:
            limit = min(limit, deadline) if limit is not None else deadline
        _write_atomic(
            self.config.directory / REQUEST_NAME,
            self._request.model_dump_json(),
            limit,
            final_attempt=final_attempt,
        )

    def _log(self, event: str, **payload: Any) -> None:
        if self.record is not None:
            handoff = self._request.handoff if self._request else 0
            self.record(
                "combat_gate", {"event": event, "state": self.state, "handoff": handoff, **payload}
            )
