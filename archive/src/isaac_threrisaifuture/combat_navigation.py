"""Bounded scripted management travel; never a learned navigation policy."""

import math
import time
from collections import Counter
from typing import Any

from .actions import Direction
from .combat_gate import CombatGateEnv, CombatGateExpired, classify, provenance, write_readiness
from .live import LiveBudgetExpired, LiveSnapshot
from .navigation_wire import NavigationFrame, OpenDoor
from .observed_routes import NoObservedRoute, ObservedRoutes
from .room_path import NAMES, NoRoomPath, path_pulse, room_path


class NavigationStopped(LiveBudgetExpired):
    """A management stop, neither character death nor successful progression."""


def pulse_direction(snap: LiveSnapshot, door: OpenDoor) -> tuple[Direction, int]:
    """Follow a measured safe path, then cross the observed doorway."""
    assert snap.player is not None
    nav = snap.oracle.navigation if snap.oracle else None
    if nav is None:
        raise NavigationStopped("Navigation telemetry missing")
    try:
        return path_pulse(nav, snap.player.position, door)
    except NoRoomPath as exc:
        raise NavigationStopped(str(exc)) from exc


class CombatNavigationGate(CombatGateEnv):
    """Same gate/deadlines/readiness protocol, with management inside reset only."""

    def __init__(
        self, *args: Any, budget_scale: int = 1, time_dominant: bool = False, **kwargs: Any
    ) -> None:
        if type(budget_scale) is not int or not 1 <= budget_scale <= 5:
            raise ValueError("Navigation budget scale must be an integer in 1..5")
        super().__init__(*args, **kwargs)
        if type(time_dominant) is not bool or (
            time_dominant
            and (
                self.run_deadline is None
                or not math.isfinite(self.run_deadline)
                or budget_scale != 1
            )
        ):
            raise ValueError("Time-dominant navigation requires a finite run deadline and scale 1")
        self.time_dominant = time_dominant
        self.nav_command_limit = 256 * budget_scale
        self.nav_second_limit = 90 * budget_scale
        self.nav_transition_limit = 4 * budget_scale
        self.nav_commands = 0
        self.nav_seconds = 0.0
        self.nav_transitions = 0
        self._floor: tuple[str, int, int, int] | None = None
        self._used: Counter[tuple[int, int]] = Counter()
        self._navigation_context: tuple[str, int, int] | None = None
        self._routes = ObservedRoutes()
        self._pending_route: tuple[tuple[str, int, int], int, int] | None = None

    def _navigation(self, snap: LiveSnapshot) -> NavigationFrame:
        nav = snap.oracle.navigation if snap.oracle is not None else None
        if nav is None:
            raise NavigationStopped("Navigation telemetry missing")
        if nav.room_type != 1:
            raise NavigationStopped("Navigation requires an ordinary room")
        if nav.version != 2 or nav.grid is None:
            raise NavigationStopped("Measured navigation grid v2 is required")
        floor = (snap.session_id, snap.game_epoch, nav.stage, nav.stage_type)
        if floor != self._floor:
            self._used.clear()
            self._routes = ObservedRoutes()
            self._pending_route = None
            self._floor = floor
        return nav

    def _remember(self, snap: LiveSnapshot) -> None:
        nav = snap.oracle.navigation if snap.oracle else None
        context = provenance(snap)
        if (
            nav is None
            or nav.room_type != 1
            or context is None
            or classify(snap) not in ("cleared", "empty", "combat")
        ):
            return
        nav = self._navigation(snap)
        self._routes.observe(nav.room_index, [d.slot for d in nav.doors])
        pending = self._pending_route
        if pending is not None and context != pending[0]:
            if context[:2] == pending[0][:2] and context[2] > pending[0][2]:
                self._routes.connect(pending[1], pending[2], nav.room_index)
                self._log(
                    "navigation_connection",
                    source=pending[1],
                    slot=pending[2],
                    destination=nav.room_index,
                )
            self._pending_route = None

    def _remaining_seconds(self) -> float:
        return math.inf if self.time_dominant else self.nav_second_limit - self.nav_seconds

    def _choose(self, snap: LiveSnapshot) -> OpenDoor:
        nav = self._navigation(snap)
        if not nav.doors and not self.time_dominant:
            raise NavigationStopped("No open ordinary-room exit")
        assert snap.player is not None
        if self.time_dominant:
            self._remember(snap)
            reachable = set()
            for candidate in nav.doors:
                try:
                    room_path(nav, snap.player.position, candidate)
                    reachable.add(candidate.slot)
                except NoRoomPath:
                    pass
            self._log(
                "navigation_search",
                observed_rooms=len(self._routes.doors),
                confirmed_connections=len(self._routes.edges),
            )
            try:
                slot = self._routes.choose(nav.room_index, reachable)
            except NoObservedRoute as exc:
                self._log("navigation_no_progress", reason=str(exc))
                raise NavigationStopped(str(exc)) from exc
            selected = next(d for d in nav.doors if d.slot == slot)
            self._log("navigation_goal", room_index=nav.room_index, slot=slot, time_dominant=True)
            return selected
        door = None
        for candidate in sorted(
            nav.doors, key=lambda d: (self._used[nav.room_index, d.slot], d.slot)
        ):
            try:
                room_path(nav, snap.player.position, candidate)
            except NoRoomPath:
                continue
            door = candidate
            break
        if door is None:
            raise NavigationStopped("No reachable ordinary-room exit")
        self._used[nav.room_index, door.slot] += 1
        self._log(
            "navigation_goal",
            room_index=nav.room_index,
            shape=nav.shape,
            grid_width=nav.grid.width if nav.grid else None,
            grid_height=nav.grid.height if nav.grid else None,
            slot=door.slot,
        )
        return door

    def _poll_navigation(self, cap: float) -> LiveSnapshot | None:
        now = time.monotonic()
        self._check_deadlines(now, cap)
        snap, seen = self.backend.poll(min(0.15, cap - now))
        self.stats.wait_snapshots += seen
        self._check_deadlines(time.monotonic(), cap)
        context = provenance(snap)
        if self.time_dominant and snap is not None:
            self._remember(snap)
        old = self._navigation_context
        if context is not None:
            if old is not None and context[:2] == old[:2] and context[2] != old[2]:
                self.nav_transitions += 1
                self.stats.wait_room_changes += 1
                self._log("navigation_transition", transitions=self.nav_transitions)
            self._navigation_context = context
        return snap

    def _pulse(self, snap: LiveSnapshot, door: OpenDoor, cap: float) -> LiveSnapshot:
        controller = getattr(self.env.unwrapped, "controller", None)
        if controller is None or controller.running or self.state != "waiting_for_operator":
            raise RuntimeError("Navigation requires a stopped policy controller")
        self._check_deadlines(time.monotonic(), cap)
        if classify(snap) not in ("cleared", "empty"):
            raise NavigationStopped("Navigation requires active clear/empty state")
        nav = self._navigation(snap)
        if door not in nav.doors:
            raise NavigationStopped("Selected door is no longer open")
        assert snap.player is not None
        if not self.time_dominant and (
            self.nav_commands + 2 > self.nav_command_limit
            or self.nav_seconds + 4 > self.nav_second_limit
            or self.nav_transitions >= self.nav_transition_limit
        ):
            raise NavigationStopped("Navigation budget exhausted")
        direction, frames = pulse_direction(snap, door)
        crossing = (
            direction == NAMES[door.slot % 4]
            and len(room_path(nav, snap.player.position, door)) == 1
        )
        identity, latest = provenance(snap), snap
        started = time.monotonic()
        if self.time_dominant:
            self._pending_route = None
        # Reserve release time within the cumulative pulse budget as well as the
        # original gate deadline. The transport itself has bounded ack timeouts.
        end = min(cap, started + 0.8, started + self._remaining_seconds())
        try:
            self.nav_commands += 1
            ack = self.backend.client.command(
                "action", snap, move=direction, shoot="none", frames=frames
            )
            self._log(
                "navigation_action",
                direction=direction,
                frames=frames,
                status=ack.status,
                room_visit=snap.room.visit_id if snap.room else None,
                reference_frame=snap.frame_id,
                ack_frame=ack.frame_id,
                position=snap.player.position.model_dump(),
            )
            if ack.status != "accepted":
                self._pending_route = None
                raise NavigationStopped("Navigation action rejected")
            if self.time_dominant:
                assert identity is not None
                self._pending_route = (identity, nav.room_index, door.slot)
            while time.monotonic() < end:
                try:
                    current = self._poll_navigation(end)
                except CombatGateExpired as exc:
                    self._check_deadlines(time.monotonic(), cap)
                    raise NavigationStopped(
                        "No fresh navigation frame before pulse deadline"
                    ) from exc
                if current is None:
                    continue
                latest = current
                if (latest.session_id, latest.game_epoch) != (snap.session_id, snap.game_epoch):
                    raise NavigationStopped("Session or epoch changed during navigation")
                if latest.oracle is None or latest.oracle.player_dead:
                    raise NavigationStopped("Unavailable or dead during navigation")
                if latest.player is None or latest.player.health != snap.player.health:
                    raise NavigationStopped("Health changed during navigation")
                if provenance(latest) != identity or classify(latest) not in ("cleared", "empty"):
                    break
                if latest.frame_id is not None and latest.frame_id >= ack.frame_id + frames:
                    break
            else:
                raise NavigationStopped("No fresh navigation frame before pulse deadline")
        finally:
            self.nav_commands += 1
            try:
                released = self.backend.client.command("release", latest)
                self._log("navigation_release", status=released.status)
                if released.status != "accepted" and provenance(latest) == identity:
                    # Room callbacks can invalidate a release before the reader
                    # has delivered the new-room snapshot. Do not issue movement
                    # or assume success: require fresh same-epoch transition data.
                    until = min(
                        cap,
                        time.monotonic() + 0.5,
                        started + self._remaining_seconds(),
                    )
                    latest = self._confirm_transition(snap, until, cap)
            finally:
                self.nav_seconds += time.monotonic() - started
        if crossing and provenance(latest) == identity:
            # Native room callbacks can trail a successful release. Poll without
            # another movement pulse before replanning an intermediate boundary pose.
            settling = time.monotonic()
            limit = min(cap, settling + 0.5, settling + self._remaining_seconds())
            try:
                self._log("navigation_crossing_wait", seconds=0.5)
                latest = self._confirm_transition(latest, limit, cap, required=False)
            finally:
                self.nav_seconds += time.monotonic() - settling
        return latest

    def _confirm_transition(
        self, reference: LiveSnapshot, limit: float, cap: float, *, required: bool = True
    ) -> LiveSnapshot:
        identity = provenance(reference)
        assert identity is not None and reference.player is not None
        latest = reference
        phase = "after rejected release" if required else "while waiting for door crossing"
        while time.monotonic() < limit:
            try:
                current = self._poll_navigation(limit)
            except CombatGateExpired:
                # A reconciliation timeout is not an expired operator budget.
                # Preserve the original budget's classification if it did expire.
                self._check_deadlines(time.monotonic(), cap)
                break
            if current is None:
                continue
            if (current.session_id, current.game_epoch) != identity[:2]:
                raise NavigationStopped(f"Session or epoch changed {phase}")
            if current.oracle is None or current.oracle.player_dead or current.player is None:
                raise NavigationStopped(f"Unavailable or dead {phase}")
            if current.player.health != reference.player.health:
                raise NavigationStopped(f"Health changed {phase}")
            latest = current
            context = provenance(current)
            if context is not None and context[2] > identity[2]:
                self._log(
                    "navigation_release_transition"
                    if required
                    else "navigation_crossing_transition",
                    from_visit=identity[2],
                    to_visit=context[2],
                    frame_id=current.frame_id,
                )
                return current
        if not required:
            return latest  # no transition claim; the next fresh grid must authorize any pulse
        raise NavigationStopped("Navigation release rejected in the same room")

    def _wait(self, started: float, cap: float, **kwargs: Any) -> tuple[Any, dict[str, Any]]:
        goal: OpenDoor | None = None
        context: tuple[str, int, int] | None = None
        stationary = 0
        observed = None
        previous: LiveSnapshot | None = None
        advancing = 0
        exit_reference: LiveSnapshot | None = None
        exit_until = 0.0
        waiting_for_exit = False
        while True:
            snap = self._poll_navigation(cap)
            current = provenance(snap)
            if exit_reference is not None:
                if current is not None and current != provenance(exit_reference):
                    exit_reference, waiting_for_exit = None, False
                elif waiting_for_exit:
                    if time.monotonic() >= exit_until:
                        raise NavigationStopped("No open ordinary-room exit after settling wait")
                    if snap is not None and snap.player is not None:
                        assert exit_reference.player is not None
                        if snap.player.health != exit_reference.player.health:
                            raise NavigationStopped("Health changed while waiting for room exits")
            if snap is None:
                continue
            kind = classify(snap)
            key = (provenance(snap), kind)
            if key != observed:
                self._observe(snap, kind)
                observed = key
            if (
                previous is not None
                and provenance(snap) == provenance(previous)
                and kind in ("cleared", "empty", "combat")
                and previous.frame_id is not None
                and snap.frame_id is not None
                and snap.frame_id > previous.frame_id
            ):
                advancing = min(2, advancing + 1)
            else:
                advancing = 0
            previous = snap
            if advancing < 2:
                continue  # render callbacks during Continue/load can precede gameplay updates
            if kind == "combat":
                self._pending_route = None
                assert self._request is not None
                write_readiness(self.config.directory.parent, self._request.request_id)
                self._log("navigation_ready", room_visit=snap.room.visit_id if snap.room else None)
                # The base gate re-polls, judges the token and checks env.reset's
                # context. No retained snapshot can directly authorize actions.
                return super()._wait(started, cap, **kwargs)
            if kind not in ("cleared", "empty"):
                goal, context, stationary = None, None, 0
                continue
            if context != provenance(snap):
                goal, stationary = None, 0
            if goal is None:
                nav = self._navigation(snap)
                if not nav.doors and (kind == "empty" or waiting_for_exit):
                    # Last-enemy removal can precede native room-clear/door updates.
                    # Retain this context's original timer across paused/frozen frames.
                    if exit_reference is None:
                        exit_reference = snap
                        exit_until = min(cap, time.monotonic() + 2.0)
                        self._log("navigation_exit_wait", seconds=2.0)
                    waiting_for_exit = True
                    continue
                waiting_for_exit = False
                goal = self._choose(snap)
                context = provenance(snap)
                continue  # re-poll before acting on the selected exit
            result = self._pulse(snap, goal, cap)
            if provenance(result) != context:
                goal, context, stationary = None, None, 0
            elif snap.player is not None and result.player is not None:
                a, b = snap.player.position, result.player.position
                stationary = stationary + 1 if abs(a.x - b.x) + abs(a.y - b.y) < 0.5 else 0
                if stationary >= 3:
                    raise NavigationStopped("Three stationary navigation pulses")
