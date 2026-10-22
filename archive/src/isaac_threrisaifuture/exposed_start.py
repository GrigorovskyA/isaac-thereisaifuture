"""Opt-in exposed-start curriculum (exposed-start-v1).

The scripted setup commands the live client directly: its actions and waits never pass
through a learner environment, normalizer, recurrent state or reward deriver. Learning
then starts from a fresh post-setup snapshot. Frozen parent/child phases are
observational evidence only; Continue cannot reproduce identical world states.
"""

import hashlib
import json
import math
import os
import shutil
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import gymnasium as gym

from .actions import CommandKind, Direction
from .combat_gate import classify, provenance
from .env import UPDATES_PER_SECOND
from .live import LiveBudgetExpired, LiveClient, LiveSnapshot
from .observation import BridgeError, BridgeTimeout
from .shot_diagnostics import shot_evidence

if TYPE_CHECKING:
    from .entities import OracleEvent
    from .live import LiveRunOptions

EXPERIMENT = "exposed-start-v1"
BRANCH_RECEIPT_VERSION = 1
REPORT_VERSION = 1
FRAMES_PER_SECOND = UPDATES_PER_SECOND
OLD_CORNER = (70.0, 410.0)  # v4/v5 pilot occupancy reference, report metric only
COMPARISON_LABEL = "observational"


class SetupRefused(LiveBudgetExpired):
    """Setup or its handoff failed; no learner action follows and no budget renews."""


class CurriculumStop(LiveBudgetExpired):
    """A declared curriculum health/count/disk limit stopped the phase before the next action."""


# --- caps -------------------------------------------------------------------------------


@dataclass(frozen=True)
class PilotCaps:
    """Explicit, hashed cap manifest of the single pilot (design table, unchanged values)."""

    total_seconds: float = 300.0
    startup_seconds: float = 45.0
    setup_seconds: float = 30.0
    setup_commands: int = 240
    entry_seconds: float = 5.0  # inside setup_seconds, never an added lease
    entry_snapshots: int = 100
    learning_seconds: float = 180.0
    learning_steps: int = 2048
    cumulative_target: int = 28416
    frozen_seconds: float = 20.0
    frozen_decisions: int = 64
    frozen_setup_commands: int = 240
    action_commands: int = 3000
    progress_updates: int = 9000
    segment_updates: int = 1800
    output_bytes: int = 2 * 1024**3
    trace_bytes: int = 128 * 1024**2
    faults: int = 0
    retries: int = 0
    death_restarts: int = 0
    new_runs: int = 0
    training_min_health: int = 1  # stop when observed health <= 1 half-heart
    training_health_loss: int = 4  # stop at 4 half-hearts cumulative observed loss
    cleanup_seconds: float = 45.0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if name in ("faults", "retries", "death_restarts", "new_runs"):
                continue
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid positive finite cap: {name}")
        phases = (
            self.startup_seconds + self.setup_seconds + self.learning_seconds
            + 2 * self.frozen_seconds
        )  # fmt: skip
        if phases > self.total_seconds:
            raise ValueError("Phase caps exceed the single shared lease")
        if self.entry_seconds > self.setup_seconds:
            raise ValueError("Entry readiness cap exceeds setup time")
        commands = (
            self.setup_commands
            + self.learning_steps
            + 2 * (self.frozen_setup_commands + self.frozen_decisions)
        )
        if commands > self.action_commands:
            raise ValueError("Per-phase command caps exceed the total action-command cap")
        if any((self.faults, self.retries, self.death_restarts, self.new_runs)):
            raise ValueError("Faults, retries, death restarts and New Run must stay zero")

    def as_record(self) -> dict[str, Any]:
        record = asdict(self)
        record["sha256"] = _digest(record)
        record["experiment"] = EXPERIMENT
        return record


PILOT_CAPS = PilotCaps()


def _digest(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


# --- scripted setup ---------------------------------------------------------------------


@dataclass(frozen=True)
class SetupSpec:
    """Measured room-83 scenario of the qualified mixed-control run (743a655)."""

    room_index: int = 83
    door: tuple[float, float] = (560.0, 280.0)
    door_tolerance: float = 20.0
    target: tuple[float, float] = (80.0, 200.0)
    target_tolerance: float = 2.0
    waypoints: tuple[tuple[float, float], ...] = ((560.0, 200.0), (320.0, 200.0))
    tolerance: tuple[float, float] = (6.0, 4.0)
    settle_speed: float = 0.1
    axis_tolerance: float = 8.0
    max_commands: int = 240
    max_seconds: float = 30.0
    entry_seconds: float = 5.0
    entry_snapshots: int = 100


@dataclass
class RouteState:
    waypoint: int = 0
    braking: bool = False


def route_step(
    state: RouteState,
    position: tuple[float, float],
    velocity: tuple[float, float],
    spec: SetupSpec,
) -> Direction | None:
    """One-frame route/braking decision; None once settled at the final waypoint.

    Braking holds neutral until speed <= settle_speed, then rechecks the position after
    coasting. Movement is axis-major (x first) and never shoots.
    """
    if state.waypoint >= len(spec.waypoints):
        return None
    (x, y), (tx, ty) = spec.waypoints[state.waypoint], spec.tolerance
    dx, dy = x - position[0], y - position[1]
    near = abs(dx) <= tx and abs(dy) <= ty
    if state.braking or near:
        state.braking = True
        if math.hypot(*velocity) <= spec.settle_speed:
            state.braking = False
            if near:
                state.waypoint += 1
                if state.waypoint >= len(spec.waypoints):
                    return None
        return "none"
    if abs(dx) > tx:
        return "right" if dx > 0 else "left"
    return "down" if dy > 0 else "up"


@dataclass(frozen=True)
class SetupResult:
    """Separate setup provenance; never policy input, reward or normalizer data."""

    context: tuple[str, int, int]
    target_id: int
    start_frame: int
    handoff_frame: int
    commands: int
    seconds: float
    direction: int  # 1..4 cardinal clear direction of the handoff evidence
    health: int | None = None

    def as_record(self) -> dict[str, Any]:
        return {"phase": "setup", "status": "handoff", **asdict(self)}


def _health(snap: LiveSnapshot) -> int:
    assert snap.entity_frame is not None
    health = snap.entity_frame.health
    return health.red_half_hearts + health.soul_half_hearts


def _target(snap: LiveSnapshot, spec: SetupSpec, target_id: int | None) -> int:
    assert snap.entity_frame is not None and snap.oracle is not None
    p = snap.entity_frame.player_position
    for e in snap.entity_frame.entities:
        if e.kind != "enemy" or (target_id is not None and e.entity_id != target_id):
            continue
        if (
            abs(p.x + e.position.x - spec.target[0]) <= spec.target_tolerance
            and abs(p.y + e.position.y - spec.target[1]) <= spec.target_tolerance
            and any(o.entity_id == e.entity_id for o in snap.oracle.enemies)
        ):
            return e.entity_id
    raise SetupRefused("Expected visible target unavailable or moved")


def _walkable(snap: LiveSnapshot, spec: SetupSpec) -> bool:
    nav = snap.oracle.navigation if snap.oracle is not None else None
    if nav is None or nav.grid is None:
        return False
    grid = nav.grid
    points = [(spec.door[0], spec.door[1]), *spec.waypoints]
    for (ax, ay), (bx, by) in zip(points, points[1:], strict=False):
        steps = max(1, int(max(abs(bx - ax), abs(by - ay)) // grid.spacing))
        for i in range(steps + 1):
            x, y = ax + (bx - ax) * i / steps, ay + (by - ay) * i / steps
            gx = round((x - grid.origin.x) / grid.spacing)
            gy = round((y - grid.origin.y) / grid.spacing)
            if not (0 <= gx < grid.width and 0 <= gy < grid.height):
                return False
            if grid.walkable[gy * grid.width + gx] != "1":
                return False
    return True


def precheck(snap: LiveSnapshot, spec: SetupSpec, *, at_door: bool = True) -> str | None:
    """Reason the measured scenario is unavailable, or None. Pure; sends nothing."""
    if snap.status != "active" or snap.entity_frame is None or snap.oracle is None:
        return "Snapshot is not active gameplay"
    if snap.player is None or snap.player.character_type != 0:
        return "Active character is not Isaac"
    nav = snap.oracle.navigation
    if nav is None or nav.room_type != 1 or nav.room_index != spec.room_index:
        return "Unexpected room"
    if classify(snap) != "combat":
        return "Room is not in eligible combat"
    geometry = snap.combat_geometry
    if geometry is None or geometry.weapon != "plain_tears" or geometry.tear_range is None:
        return "Unsupported or unmeasured weapon"
    p = snap.entity_frame.player_position
    if at_door and math.hypot(p.x - spec.door[0], p.y - spec.door[1]) > spec.door_tolerance:
        return "Unexpected door start"
    if not _walkable(snap, spec):
        return "Measured grid blocks the setup route"
    try:
        _target(snap, spec, None)
    except SetupRefused as exc:
        return str(exc)
    return None


def _newer(
    client: LiveClient, after: int | None, deadline: float, stop_file: Path | None
) -> LiveSnapshot:
    """Newest snapshot with frame_id > after; bounded by the setup deadline."""
    latest: LiveSnapshot | None = None
    for snap in client.drain():
        latest = snap
    while True:
        if stop_file is not None and stop_file.exists():
            raise SetupRefused("User cancellation requested during setup")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SetupRefused("Setup deadline exhausted")
        if latest is not None and (after is None or (latest.frame_id or -1) > after):
            if latest.status != "active" or latest.entity_frame is None:
                raise SetupRefused("Gameplay paused or unavailable during setup")
            return latest
        try:
            latest = client.take(min(remaining, 1.0))
        except BridgeTimeout:
            continue


def _entry_visibility(
    client: LiveClient,
    current: LiveSnapshot,
    spec: SetupSpec,
    deadline: float,
    stop_file: Path | None,
    log: Callable[[str, Any], None],
    *,
    at_door: bool,
) -> LiveSnapshot:
    """Wait without commands only for an initially empty visible enemy set."""
    missing = "Expected visible target unavailable or moved"
    reason = precheck(current, spec, at_door=at_door)
    if reason is None:
        return current

    def invisible(snap: LiveSnapshot) -> bool:
        return snap.entity_frame is not None and not any(
            e.kind == "enemy" for e in snap.entity_frame.entities
        )

    if reason != missing or not invisible(current):
        raise SetupRefused(reason)
    assert current.oracle is not None and current.oracle.navigation is not None
    context, grid = provenance(current), current.oracle.navigation.grid
    members = {e.entity_id for e in current.oracle.enemies}
    health, count, started = _health(current), 1, time.monotonic()
    deadline = min(deadline, started + spec.entry_seconds)
    log("exposed_start_readiness", {"status": "waiting", "frame": current.frame_id})
    while count < spec.entry_snapshots:
        if stop_file is not None and stop_file.exists():
            raise SetupRefused("User cancellation during initial visibility wait")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SetupRefused("Initial visibility deadline exhausted")
        try:
            current = client.take(min(remaining, 1.0))
        except BridgeTimeout:
            continue
        count += 1
        if time.monotonic() >= deadline:
            raise SetupRefused("Initial visibility deadline exhausted")
        if provenance(current) != context:
            raise SetupRefused("Context changed during initial visibility wait")
        if current.entity_frame is None or current.oracle is None:
            raise SetupRefused("Structured state unavailable during initial visibility wait")
        if _health(current) < health:
            raise SetupRefused("First observed health loss during initial visibility wait")
        health = _health(current)
        nav = current.oracle.navigation
        if nav is None or nav.grid != grid:
            raise SetupRefused("Measured grid changed during initial visibility wait")
        if {e.entity_id for e in current.oracle.enemies} != members:
            raise SetupRefused("Enemy membership changed during initial visibility wait")
        reason = precheck(current, spec, at_door=at_door)
        if reason is None:
            log(
                "exposed_start_readiness",
                {
                    "status": "ready",
                    "snapshots": count,
                    "seconds": time.monotonic() - started,
                    "frame": current.frame_id,
                },
            )
            log("exposed_start_readiness_observation", current.model_dump(mode="json"))
            return current
        if reason != missing or not invisible(current):
            raise SetupRefused(reason)
    raise SetupRefused("Initial visibility snapshot cap exhausted")


def run_setup(
    client: LiveClient,
    spec: SetupSpec,
    *,
    deadline: float,
    stop_file: Path | None = None,
    record: Callable[[str, Any], None] | None = None,
    at_door: bool = True,
) -> SetupResult:
    """Drive the one-frame route to a settled exposed start, release, then verify freshly."""
    started = time.monotonic()
    deadline = min(deadline, started + spec.max_seconds)
    log = record or (lambda *_: None)
    current = _newer(client, None, deadline, stop_file)
    # One bounded raw record preserves why an entry was refused, before any action.
    # Oracle fields stay in diagnostics and never enter the learner.
    log("exposed_start_setup_observation", current.model_dump(mode="json"))
    current = _entry_visibility(client, current, spec, deadline, stop_file, log, at_door=at_door)
    target_id = _target(current, spec, None)
    context = provenance(current)
    assert context is not None and current.oracle is not None and current.frame_id is not None
    assert current.oracle.navigation is not None
    grid, health0, start = current.oracle.navigation.grid, _health(current), current.frame_id
    commands = 0

    def guard(snap: LiveSnapshot) -> None:
        assert snap.oracle is not None and snap.entity_frame is not None
        if provenance(snap) != context:
            raise SetupRefused("Session, epoch or room changed during setup")
        if snap.oracle.player_dead or snap.oracle.room_clear:
            raise SetupRefused("Native terminal boundary during setup; no reset")
        nav = snap.oracle.navigation
        if nav is None or nav.grid != grid:
            raise SetupRefused("Measured grid changed during setup")
        geometry = snap.combat_geometry
        if geometry is None or geometry.weapon != "plain_tears":
            raise SetupRefused("Weapon changed during setup")
        if _health(snap) < health0:
            raise SetupRefused("First observed player health loss during setup")
        _target(snap, spec, target_id)

    state = RouteState()
    try:
        while True:
            guard(current)
            frame = current.entity_frame
            assert frame is not None
            if frame.player_velocity is None:
                raise SetupRefused("Player velocity unavailable; settling is unmeasurable")
            move = route_step(
                state,
                (frame.player_position.x, frame.player_position.y),
                (frame.player_velocity.x, frame.player_velocity.y),
                spec,
            )
            if move is None:
                break
            if commands >= spec.max_commands:
                raise SetupRefused("Setup command cap exhausted")
            ack = client.command("action", current, move=move, shoot="none", frames=1)
            commands += 1
            if ack.status != "accepted":
                raise SetupRefused(f"Setup command not accepted: {ack.status}")
            log("exposed_start_setup", {"move": move, "frame": ack.frame_id, "n": commands})
            current = _newer(client, ack.frame_id, deadline, stop_file)
        client.command("release", current)
        assert current.frame_id is not None
        released = current.frame_id
        current = _newer(client, released, deadline, stop_file)
        guard(current)
        direction = handoff_direction(current, target_id, spec)
    except BaseException:
        _release(client, current)
        raise
    assert current.frame_id is not None
    result = SetupResult(
        context, target_id, start, current.frame_id, commands,
        time.monotonic() - started, direction, _health(current),
    )  # fmt: skip
    log("exposed_start_handoff", result.as_record())
    return result


def handoff_direction(snap: LiveSnapshot, target_id: int, spec: SetupSpec) -> int:
    """Clear cardinal direction of a visible aligned in-range target, else refuse."""
    assert snap.entity_frame is not None
    evidence = shot_evidence(
        snap.entity_frame, snap.combat_geometry, axis_tolerance=spec.axis_tolerance
    )
    for index, direction in enumerate(evidence.directions, start=1):
        if target_id in direction.clear:
            return index
    raise SetupRefused("No fresh clear aligned in-range firing opportunity at handoff")


def _release(client: LiveClient, reference: LiveSnapshot | None) -> None:
    if reference is None or not client.connected:
        return
    try:
        client.command("release", reference)
    except BridgeError:
        pass  # native hold expires within 15 frames / 250 ms


# --- learner boundary ------------------------------------------------------------------


def _backend(env: gym.Env[Any, Any]) -> Any:
    return cast(Any, env.unwrapped).controller.backend


@dataclass(frozen=True)
class PhaseSample:
    frame: int
    x: float
    y: float
    health: int
    enemy_hp: tuple[tuple[int, float], ...]
    clear: bool
    dead: bool
    clear_shot: bool | None
    context: tuple[str, int, int] | None
    room_index: int | None = None
    grid_sha256: str | None = None
    weapon: str | None = None
    tear_range: float | None = None
    enemy_positions: tuple[tuple[int, float, float], ...] = ()


def sample_of(snap: LiveSnapshot) -> PhaseSample | None:
    """Report-only digest of one snapshot; never returned to a policy or normalizer."""
    if snap.entity_frame is None or snap.oracle is None or snap.frame_id is None:
        return None
    try:
        shot = shot_evidence(snap.entity_frame, snap.combat_geometry)
        evidence: bool | None = bool(shot.clear_directions)
        if not evidence and (not shot.supported_weapon or not shot.complete_visible_set):
            evidence = None
    except ValueError:
        evidence = None
    p = snap.entity_frame.player_position
    nav, geometry = snap.oracle.navigation, snap.combat_geometry
    return PhaseSample(
        snap.frame_id, p.x, p.y, _health(snap),
        tuple(sorted((e.entity_id, e.hp) for e in snap.oracle.enemies)),
        snap.oracle.room_clear, snap.oracle.player_dead, evidence, provenance(snap),
        nav.room_index if nav else None,
        _digest(nav.grid.model_dump(mode="json")) if nav and nav.grid else None,
        geometry.weapon if geometry else None, geometry.tear_range if geometry else None,
        tuple((e.entity_id, p.x + e.position.x, p.y + e.position.y)
              for e in snap.entity_frame.entities if e.kind == "enemy"),
    )  # fmt: skip


class ExposedStartEnv(gym.Wrapper[Any, Any, Any, Any]):
    """Learner boundary: fresh handoff check on the first reset and training health stops.

    Observations, rewards and info pass through unchanged; samples are report-only.
    """

    def __init__(
        self,
        env: gym.Env[Any, Any],
        setup: SetupResult,
        spec: SetupSpec,
        caps: PilotCaps = PILOT_CAPS,
        record: Callable[[str, Any], None] | None = None,
    ) -> None:
        super().__init__(env)
        self.setup, self.setup_spec, self.caps = setup, spec, caps
        self.record = record or (lambda *_: None)
        self.samples: list[PhaseSample] = []
        self.handed_off = False
        self.health_loss = 0
        self.stop_reason: str | None = None
        self._health: int | None = None
        self.decisions = 0

    def reset(self, **kwargs: Any) -> tuple[Any, dict[str, Any]]:
        self._check()
        observation, info = self.env.reset(**kwargs)
        snap = _backend(self.env).latest
        if not self.handed_off:
            reason = self._stale(snap)
            if reason is not None:
                _backend(self.env).release()
                self.record("exposed_start_handoff_refused", {"reason": reason})
                raise SetupRefused(f"Stale setup handoff: {reason}")
            self.handed_off = True
            self.record("exposed_start_learning_start", {"frame": snap.frame_id})
        self._observe(snap)
        return observation, info

    def step(self, action: Any) -> tuple[Any, Any, bool, bool, dict[str, Any]]:
        self._check()
        result = self.env.step(action)
        self.decisions += 1
        self._observe(_backend(self.env).latest)
        return result

    def _stale(self, snap: LiveSnapshot | None) -> str | None:
        if snap is None or snap.frame_id is None:
            return "No learner snapshot"
        if provenance(snap) != self.setup.context:
            return "Session, epoch or room changed after setup"
        if snap.frame_id <= self.setup.handoff_frame:
            return "Learner snapshot is not newer than the handoff"
        if classify(snap) != "combat":
            return "Learner state is not eligible combat"
        if self.setup.health is not None and _health(snap) != self.setup.health:
            return "Player health changed after setup"
        try:
            _target(snap, self.setup_spec, self.setup.target_id)
            handoff_direction(snap, self.setup.target_id, self.setup_spec)
        except SetupRefused as exc:
            return str(exc)
        return None

    def _observe(self, snap: LiveSnapshot | None) -> None:
        sample = sample_of(snap) if snap is not None else None
        if sample is None:
            return
        self.samples.append(sample)
        if self._health is not None and sample.health < self._health:
            self.health_loss += self._health - sample.health
        self._health = sample.health
        if sample.health <= self.caps.training_min_health:
            self.stop_reason = f"Observed health {sample.health} <= minimum"
        elif self.health_loss >= self.caps.training_health_loss:
            self.stop_reason = f"Observed cumulative health loss {self.health_loss}"
        elif sample.dead:
            self.stop_reason = "Observed death; no reset"

    def _check(self) -> None:
        if self.stop_reason is not None:
            _backend(self.env).release()
            raise CurriculumStop(self.stop_reason)


# --- exact branch -----------------------------------------------------------------------


def _hashes(directory: Path) -> dict[str, str]:
    from .checkpoints import _sha256

    files = sorted(p for p in directory.rglob("*") if p.is_file())
    return {p.relative_to(directory).as_posix(): _sha256(p) for p in files}


def branch_checkpoint(
    parent: Path,
    child_run_root: Path,
    *,
    seed: int,
    cfg_hash: str,
    reward_contract: Any,
    observation_schema: int,
    copy: Callable[[Path, Path], Any] = shutil.copytree,
) -> dict[str, Any]:
    """Copy one named compatible checkpoint into an absent child run; publish pointer last."""
    from .checkpoints import (
        LATEST_POINTER,
        CheckpointError,
        _replace_pointer,
        latest_checkpoint_dir,
        load_checkpoint,
    )

    parent = Path(parent)
    if not parent.is_dir() or (parent / LATEST_POINTER).exists():
        raise CheckpointError("Name one existing parent checkpoint directory")
    manifest = load_checkpoint(
        parent,
        expected_config_hash=cfg_hash,
        expected_seed=seed,
        expected_reward_contract=reward_contract,
        expected_observation_schema=observation_schema,
    )
    if manifest.checkpoint_id != parent.name or manifest.model_sha256 is None:
        raise CheckpointError("Parent requires storage v2 hashes and a matching identity")
    hashes = _hashes(parent)
    if (
        hashes.get(manifest.model_file) != manifest.model_sha256
        or hashes.get(manifest.normalizer_file) != manifest.normalizer_sha256
    ):
        raise CheckpointError("Parent artifact hashes disagree with its manifest")
    pointer = parent.parent / LATEST_POINTER
    pointer_bytes = pointer.read_bytes() if pointer.exists() else None
    seed_root = Path(child_run_root) / f"seed-{seed}"
    if seed_root.exists():
        raise CheckpointError("Child run already exists; refusing to overwrite or resume it")
    stage = seed_root / ".branch-stage"
    stage.mkdir(parents=True)
    copy(parent, stage / parent.name)
    if _hashes(stage / parent.name) != hashes:
        raise CheckpointError("Staged copy differs from the parent")
    checkpoints = seed_root / "checkpoints"
    checkpoints.mkdir()
    os.replace(stage / parent.name, checkpoints / parent.name)
    temporary = checkpoints / f".{LATEST_POINTER}.branch"
    temporary.write_text(parent.name, encoding="utf-8")
    _replace_pointer(temporary, checkpoints / LATEST_POINTER)
    stage.rmdir()
    child = latest_checkpoint_dir(checkpoints)
    loaded = load_checkpoint(
        child,
        expected_config_hash=cfg_hash,
        expected_seed=seed,
        expected_reward_contract=reward_contract,
        expected_observation_schema=observation_schema,
    )
    if loaded != manifest or _hashes(child) != hashes:
        raise CheckpointError("Child readback differs from the parent")
    if _hashes(parent) != hashes or (pointer.read_bytes() if pointer.exists() else None) != (
        pointer_bytes
    ):
        raise CheckpointError("Parent artifacts or pointer changed during branching")
    receipt = {
        "version": BRANCH_RECEIPT_VERSION,
        "experiment": EXPERIMENT,
        "parent_path": str(parent.resolve()),
        "parent_pointer_sha256": (
            hashlib.sha256(pointer_bytes).hexdigest() if pointer_bytes is not None else None
        ),
        "checkpoint_id": manifest.checkpoint_id,
        "timesteps": manifest.timesteps,
        "config_hash": cfg_hash,
        "seed": seed,
        "reward_contract": reward_contract,
        "observation_schema": observation_schema,
        "artifact_sha256": hashes,
        "child_path": str(child.resolve()),
    }
    with (seed_root / "branch-receipt.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
    return receipt


# --- metrics ----------------------------------------------------------------------------


def _windows(samples: list[PhaseSample], seconds: float) -> int:
    if not samples:
        return 0
    count, start = 0, samples[0]
    xmin = xmax = start.x
    ymin = ymax = start.y
    for prev, nxt in zip(samples, samples[1:], strict=False):
        xmin, xmax = min(xmin, nxt.x), max(xmax, nxt.x)
        ymin, ymax = min(ymin, nxt.y), max(ymax, nxt.y)
        broken = (
            math.hypot(xmax - xmin, ymax - ymin) >= 20
            or _hp_loss(prev, nxt) > 0
            or (nxt.clear and not prev.clear)
            or nxt.context != prev.context
            or nxt.frame <= prev.frame
        )
        complete = nxt.frame - start.frame >= seconds * FRAMES_PER_SECOND
        if not broken and complete:
            count += 1
        if broken or complete:
            start = nxt
            xmin = xmax = nxt.x
            ymin = ymax = nxt.y
    return count


def _hp_loss(a: PhaseSample, b: PhaseSample) -> float:
    before = dict(a.enemy_hp)
    return sum(max(0.0, before[k] - v) for k, v in b.enemy_hp if k in before)


def fingerprint(sample: PhaseSample | None) -> dict[str, Any] | None:
    return None if sample is None else {k: v for k, v in asdict(sample).items()}


def phase_metrics(
    name: str,
    samples: list[PhaseSample],
    *,
    status: str = "completed",
    reason: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Descriptive per-phase evidence. Lower bounds only; never rewards or features."""
    pairs = list(zip(samples, samples[1:], strict=False))
    same = [(a, b) for a, b in pairs if a.context == b.context]
    shots = [s.clear_shot for s in samples if s.clear_shot is not None]
    frames = sum(max(0, b.frame - a.frame) for a, b in same)
    return {
        "phase": name,
        "status": status,
        "reason": reason,
        "decisions": max(0, len(samples) - 1),
        "active_seconds": frames / FRAMES_PER_SECOND,
        "exposure_basis": "same-context observed frame spans; unsampled gaps remain partial",
        "enemy_hp_loss_lower_bound": sum(_hp_loss(a, b) for a, b in same),
        "half_hearts_lost": sum(max(0, a.health - b.health) for a, b in same),
        "clears": sum(b.clear and not a.clear for a, b in same),
        "deaths": sum(b.dead and not a.dead for a, b in pairs),
        "context_changes": len(pairs) - len(same),
        "near_old_corner": sum(
            math.hypot(s.x - OLD_CORNER[0], s.y - OLD_CORNER[1]) < 20 for s in samples
        ),
        "stagnation_windows_10s": _windows(samples, 10.0),
        "clear_line_exposure": {"clear": sum(shots), "denominator": len(shots)},
        "samples": len(samples),
        "start": fingerprint(samples[0] if samples else None),
        "end": fingerprint(samples[-1] if samples else None),
        "coverage": "partial",
        **(extra or {}),
    }


def write_report(path: Path, phases: list[dict[str, Any]], caps: PilotCaps) -> dict[str, Any]:
    report = {
        "version": REPORT_VERSION,
        "experiment": EXPERIMENT,
        "comparison": COMPARISON_LABEL,
        "note": (
            "Continue cannot restore identical world states; frozen phases are observational,"
            " not paired, held-out or multi-seed evaluation."
        ),
        "caps": caps.as_record(),
        "phases": phases,
    }
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


# --- phase orchestration ----------------------------------------------------------------


class PhaseClient:
    """Shared client view for one phase: close() releases ownership but keeps the listener."""

    _client: LiveClient

    def __init__(self, client: LiveClient) -> None:
        object.__setattr__(self, "_client", client)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._client, name, value)

    def close(self) -> None:
        """The pilot owns the real client; a phase environment may not close it."""


class PilotClient(PhaseClient):
    """Enforce shared limits at the final command boundary, including gate navigation."""

    def __init__(self, client: LiveClient, deadline: float, root: Path, caps: PilotCaps) -> None:
        super().__init__(client)
        self._pilot_caps, self._pilot_root = caps, root
        self._pilot_lease = deadline
        self._pilot_deadline = deadline
        self._pilot_phase = "setup"
        self._pilot_actions = 0
        self._pilot_scanned = -math.inf
        self._pilot_halt: str | None = None
        self._pilot_health: int | None = None
        self._pilot_loss = 0
        self._pilot_epoch: int | None = None
        self._pilot_first: Callable[[LiveSnapshot], None] | None = None

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_pilot_"):
            object.__setattr__(self, name, value)
        else:
            super().__setattr__(name, value)

    def phase(self, name: str, seconds: float) -> None:
        self._pilot_phase = name
        self._pilot_deadline = min(self._pilot_lease, time.monotonic() + seconds)

    def check(self, *, force_files: bool = False) -> None:
        fatal = getattr(self._client, "fatal_snapshot", None)
        if fatal is not None:
            self._pilot_halt = "Observed death; zero-restart pilot stopped"
        if self._pilot_halt is not None:
            raise CurriculumStop(self._pilot_halt)
        now = time.monotonic()
        if now >= self._pilot_deadline:
            raise CurriculumStop(f"{self._pilot_phase} deadline exhausted")
        if force_files or now - self._pilot_scanned >= 0.25:
            self._pilot_scanned = now
            files = list(self._pilot_root.rglob("*"))
            output, traces = 0, 0
            for path in files:
                if path.is_file():
                    size = path.stat().st_size
                    output += size
                    if "diagnostics" in path.parts or path.name == "oracle.jsonl":
                        traces += size
            if output > self._pilot_caps.output_bytes:
                self._pilot_halt = "Shared output cap exceeded"
            elif traces > self._pilot_caps.trace_bytes:
                self._pilot_halt = "Shared trace cap exceeded"
            if self._pilot_halt is not None:
                raise CurriculumStop(self._pilot_halt)

    def command(self, kind: CommandKind, reference: LiveSnapshot, **kwargs: Any) -> Any:
        if kind != "release":
            self.check()
            if reference.oracle is not None and reference.entity_frame is not None:
                health = _health(reference)
                if self._pilot_epoch is None:
                    self._pilot_epoch = reference.game_epoch
                if reference.oracle.player_dead or reference.game_epoch != self._pilot_epoch:
                    self._pilot_halt = "Death or epoch change; no restart"
                elif health <= self._pilot_caps.training_min_health:
                    self._pilot_halt = "Minimum pilot health reached"
                elif self._pilot_phase == "learning":
                    if self._pilot_health is not None:
                        self._pilot_loss += max(0, self._pilot_health - health)
                    self._pilot_health = health
                    if self._pilot_loss >= self._pilot_caps.training_health_loss:
                        self._pilot_halt = "Cumulative pilot health loss reached"
                self.check()
            if kind == "action":
                if self._pilot_actions >= self._pilot_caps.action_commands:
                    self._pilot_halt = "Shared action-command cap exhausted"
                    raise CurriculumStop(self._pilot_halt)
                if self._pilot_first is not None:
                    self._pilot_first(reference)
                self._pilot_actions += 1
        ack = self._client.command(kind, reference, **kwargs)
        if kind == "action" and ack.status == "accepted":
            self._pilot_first = None
        return ack

    def take(self, timeout: float) -> LiveSnapshot:
        self.check()
        return self._client.take(min(timeout, self._pilot_deadline - time.monotonic()))

    def drain(self) -> list[LiveSnapshot]:
        self.check()
        return self._client.drain()

    def connect(self) -> Any:
        raise CurriculumStop("Transport lost; no unverified game-instance reconnect")


def _dir_bytes(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.exists() else 0


def _latest_child(options: "LiveRunOptions", seed: int) -> Path | None:
    from .checkpoints import CheckpointError, latest_checkpoint_dir

    try:
        return latest_checkpoint_dir(options.out_dir / f"seed-{seed}" / "checkpoints")
    except CheckpointError:
        return None


def run_frozen_phase(
    name: str,
    client: LiveClient,
    checkpoint: Path | None,
    options: "LiveRunOptions",
    *,
    cfg_hash: str,
    seed: int,
    deadline: float,
    record: Callable[[str, Any], None],
    sink: Callable[["OracleEvent"], None] | None,
    spec: SetupSpec,
    caps: PilotCaps = PILOT_CAPS,
    unavailable: str | None = None,
) -> dict[str, Any]:
    """Deterministic frozen observation; unavailable inputs are not_run, never substituted."""
    from .checkpoint_policy import CheckpointPolicy
    from .live import make_live_env

    if unavailable is not None or checkpoint is None:
        return phase_metrics(name, [], status="not_run", reason=unavailable or "No checkpoint")
    deadline = min(deadline, time.monotonic() + caps.frozen_seconds)
    if deadline - time.monotonic() <= 1.0:
        return phase_metrics(name, [], status="not_run", reason="Shared lease exhausted")
    if not client.connected:
        return phase_metrics(
            name, [], status="not_run", reason="Transport lost; owned instance unverified"
        )
    if isinstance(client, PilotClient):
        client.phase(name, caps.frozen_seconds)
    policy = CheckpointPolicy(checkpoint, expected_config_hash=cfg_hash, expected_seed=seed)
    phase_client = cast(LiveClient, PhaseClient(client))
    samples: list[PhaseSample] = []
    status, reason, setup = "completed", "Decision cap", None
    env = make_live_env(
        phase_client,
        action_repeat=3,
        max_faults=0,
        record=record,
        oracle_sink=sink,
        run_deadline=deadline,
        stop_file=options.stop_file,
        firing_position_reward=options.firing_position_reward,
        boundary_progress_reward=options.boundary_progress_reward,
        combat_geometry=options.combat_geometry,
    )
    backend = _backend(env)
    try:
        latest = _newer(client, None, deadline, options.stop_file)
        if precheck(latest, spec, at_door=False) is None:
            setup = run_setup(
                client, replace(spec, max_commands=caps.frozen_setup_commands),
                deadline=deadline, stop_file=options.stop_file, record=record, at_door=False,
            )  # fmt: skip
        elif classify(latest) != "combat":
            return phase_metrics(name, [], status="not_run", reason="No eligible combat state")
        observation, _ = env.reset()
        policy.reset(seed)
        first = backend.latest
        if setup is not None and (
            provenance(first) != setup.context or first.frame_id <= setup.handoff_frame
        ):
            return phase_metrics(name, [], status="not_run", reason="Stale frozen handoff")
        health0 = _health(first)
        context = provenance(first)
        first_command = True

        def eligible(snap: LiveSnapshot) -> str | None:
            if _health(snap) < health0:
                raise CurriculumStop("First observed frozen player health loss")
            if classify(snap) != "combat" or provenance(snap) != context:
                return "Frozen combat eligibility/context changed"
            if first_command and setup is not None:
                _target(snap, spec, setup.target_id)
                handoff_direction(snap, setup.target_id, spec)
            return None

        backend.action_gate = eligible
        samples.append(cast(PhaseSample, sample_of(first)))
        for _ in range(caps.frozen_decisions):
            observation, _, terminated, truncated, _ = env.step(policy.act(observation))
            first_command = False
            sample = sample_of(backend.latest)
            if sample is not None:
                samples.append(sample)
            if terminated or truncated:
                reason = "Episode boundary; no reset"
                break
            if sample is not None and sample.health < health0:
                reason = "First observed player health loss"
                break
    except SetupRefused as exc:
        status, reason = "not_run", f"Setup unavailable: {exc}"
    except LiveBudgetExpired as exc:
        reason = f"{type(exc).__name__}: {exc}"
    finally:
        backend.release()
        env.close()
        policy.verify_unchanged()
    return phase_metrics(
        name,
        samples,
        status=status if samples or status == "not_run" else "not_run",
        reason=reason,
        extra={
            "checkpoint": checkpoint.name,
            "policy": policy.identity.to_dict(),
            "setup": setup.as_record() if setup is not None else None,
            "deterministic": True,
        },
    )


def run_pilot(
    client: LiveClient,
    options: "LiveRunOptions",
    record: Callable[[str, Any], None],
    sink: Callable[["OracleEvent"], None],
    logs: Path,
    *,
    spec: SetupSpec | None = None,
    caps: PilotCaps = PILOT_CAPS,
) -> dict[str, Any]:
    """Setup -> learning -> frozen parent -> frozen child, inside one never-renewed lease."""
    from .live import _train_run
    from .training import DEFAULT_CONFIG, load_training_config

    spec = spec or SetupSpec(
        max_commands=caps.setup_commands,
        max_seconds=caps.setup_seconds,
        entry_seconds=caps.entry_seconds,
        entry_snapshots=caps.entry_snapshots,
    )
    if spec.entry_seconds > caps.entry_seconds or spec.entry_snapshots > caps.entry_snapshots:
        raise ValueError("Setup readiness exceeds declared cap manifest")
    assert options.session_deadline is not None and options.exposed_start_parent is not None
    lease = min(options.session_deadline, time.monotonic() + caps.total_seconds)
    _, cfg_hash = load_training_config(options.config_path or DEFAULT_CONFIG)
    seed = options.seed if options.seed is not None else 0
    parent = Path(options.exposed_start_parent)
    start = _latest_child(options, seed)
    if start is None or start.name != parent.name:
        raise ValueError("Child run must start at the branched parent checkpoint")
    if _hashes(start) != _hashes(parent):
        raise ValueError("Initial child artifacts do not match the declared parent")
    from .checkpoints import read_manifest

    if (
        options.steps != caps.cumulative_target
        or read_manifest(parent).timesteps + caps.learning_steps != caps.cumulative_target
        or options.combat_progress_updates != caps.progress_updates
        or options.combat_trace_bytes > caps.trace_bytes
    ):
        raise ValueError("Pilot options disagree with the declared cap manifest")
    record("exposed_start_caps", caps.as_record())
    client.stop_on_death = True
    client = cast(LiveClient, PilotClient(client, lease, options.out_dir, caps))
    guarded = cast(PilotClient, client)
    guarded.phase("setup", caps.setup_seconds)
    phases: list[dict[str, Any]] = []
    learner: list[ExposedStartEnv] = []
    setup_start: dict[str, Any] | None = None

    def setup_record(event: str, data: Any = None) -> None:
        nonlocal setup_start
        if event == "exposed_start_setup_observation":
            setup_start = fingerprint(sample_of(LiveSnapshot.model_validate(data)))
        record(event, data)

    def finish() -> dict[str, Any]:
        report = write_report(logs / "exposed-start-phases.json", phases, caps)
        report["action_commands"] = guarded._pilot_actions
        (logs / "exposed-start-phases.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        record("exposed_start_report", {"phases": [(p["phase"], p["status"]) for p in phases]})
        return report

    try:
        setup = run_setup(
            client, spec, deadline=min(lease, time.monotonic() + caps.setup_seconds),
            stop_file=options.stop_file, record=setup_record,
        )  # fmt: skip
    except LiveBudgetExpired as exc:
        record("exposed_start_setup_refused", str(exc))
        phases.append(
            {"phase": "setup", "status": "refused", "reason": str(exc), "start": setup_start}
        )
        phases.append(phase_metrics("learning", [], status="not_run", reason="Setup failed"))
        for name in ("frozen_parent", "frozen_child"):
            phases.append(phase_metrics(name, [], status="not_run", reason="Setup failed"))
        return finish()
    phases.append({**setup.as_record(), "start": setup_start})

    def wrap(env: gym.Env[Any, Any]) -> gym.Env[Any, Any]:
        learner.append(ExposedStartEnv(env, setup, spec, caps, record))
        return learner[-1]

    learning = replace(
        options, session_deadline=min(lease, time.monotonic() + caps.learning_seconds)
    )
    learn_records: list[tuple[str, Any]] = []

    def tee(event: str, data: Any = None) -> None:
        if event in ("budget", "training_result", "combat_gate"):
            learn_records.append((event, data))
        record(event, data)

    def first_action(snap: LiveSnapshot) -> None:
        reason = (
            learner[0]._stale(snap)
            if learner and learner[0].handed_off
            else "No completed learner handoff"
        )
        if reason is not None:
            _release(client, snap)
            raise SetupRefused(f"First learner command refused: {reason}")

    guarded.phase("learning", caps.learning_seconds)
    guarded._pilot_first = first_action
    _train_run(cast(LiveClient, PhaseClient(client)), learning, tee, sink, logs, wrap=wrap)
    guarded._pilot_first = None
    samples = learner[0].samples if learner else []
    fatal = getattr(client, "fatal_snapshot", None)
    if fatal is not None and (not samples or samples[-1].frame != fatal.frame_id):
        endpoint = sample_of(fatal)
        if endpoint is not None:
            samples.append(endpoint)
    if learner and learner[0].stop_reason is not None:
        guarded._pilot_halt = learner[0].stop_reason
    accounting = [
        d for e, d in learn_records if e == "combat_gate" and d.get("event") == "rollout_accounting"
    ]
    phases.append(
        phase_metrics(
            "learning", samples,
            status="completed" if samples else "not_run",
            reason=next((str(d) for e, d in learn_records if e == "budget"), None),
            extra={
                "stochastic": True,
                "decisions": learner[0].decisions if learner else 0,
                "rollout_accounting": accounting[-1] if accounting else None,
                "training_result": next(
                    (d for e, d in learn_records if e == "training_result"), None),
            },
        )
    )  # fmt: skip
    child = _latest_child(options, seed)
    learned = child if child is not None and child.name != parent.name else None
    too_big = _dir_bytes(options.out_dir) > caps.output_bytes
    blocked = guarded._pilot_halt or ("Output cap exceeded" if too_big else None)
    common = dict(cfg_hash=cfg_hash, seed=seed, record=record, sink=sink, spec=spec, caps=caps)
    phases.append(
        run_frozen_phase(
            "frozen_parent", client, parent, options, deadline=lease,
            unavailable=blocked, **common,  # type: ignore[arg-type]
        )
    )  # fmt: skip
    phases.append(
        run_frozen_phase(
            "frozen_child", client, learned, options, deadline=lease,
            unavailable=(
                blocked if blocked is not None
                else None if learned is not None
                else "No learned child checkpoint; the copied initial child is not substituted"
            ),
            **common,  # type: ignore[arg-type]
        )
    )  # fmt: skip
    return finish()
