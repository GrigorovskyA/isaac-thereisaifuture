"""Demo recordings to behaviour-cloning sequences at the agent's decision rate.

Each recording is replayed through the same pieces the live env uses (`EventDeriver`,
`RunProgress`, `StallWatchdog` on the recorded clock, `VisitedCells`, `encode`), so an observation
here is the one the live env would have produced at the same decision point. The human's input
masks only give the labels; they never reach the encoder.

Observations are stored as float16. Every feature is in [-1, 1], where float16 keeps an absolute
error below 2.5e-4 (well under 1e-3) and represents 0, 1 and -1 exactly, so binary features
survive unchanged at half the float32 size (23.4 MB per 1000 steps).
"""

import argparse
import hashlib
import json
import os
import zlib
from collections import Counter
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .demo_recorder import IDLE_LIMIT_SECONDS, read_recording
from .encoding import OBSERVATION_SIZE, VisitedCells, encode
from .entities import OBSERVATION_SCHEMA_VERSION, OracleEvent
from .episodes import DIRECTIONS, USES
from .live import EventDeriver, _playable
from .live_wire import HUMAN_INPUT_BITS, DemoSnapshot
from .stall_watchdog import DEFAULT_STALL_SECONDS, RunProgress, StallWatchdog

# Bump when a labeling or replay rule changes: it invalidates every cache.
LABELER_VERSION = 5
MIN_STEPS = 8
GAME_UPDATES_PER_SECOND = 30
RECORDING_GLOB = "*.jsonl.gz"
# Character of a decision point whose snapshot has no player (never kept by a filter).
UNKNOWN_CHARACTER = -1
# Characters (`PlayerType`) whose play transfers to Isaac, the character the agent plays: plain
# tears and ordinary health. Isaac, Magdalene, Cain, Judas, ???, Eve, Samson, Lazarus, Lazarus
# risen, Dark Judas, Apollyon, Bethany and Tainted Isaac (21). Left out: Azazel, Eden, The Lost,
# Lilith, Keeper, The Forgotten and The Soul, Jacob and Esau, and the other tainted characters,
# whose attacks, health or core mechanic differ. They are kept for a lineage that observes the
# character.
DEFAULT_CHARACTERS = (0, 1, 2, 3, 4, 5, 6, 8, 11, 12, 15, 18, 21)

_BIT = {name: 1 << index for index, name in enumerate(HUMAN_INPUT_BITS)}
# Label order of the move and shoot heads, without "none" (index 0).
_SIDES = DIRECTIONS[1:]
_MOVE_BITS = tuple(_BIT[f"move_{side}"] for side in _SIDES)
_SHOOT_BITS = tuple(_BIT[f"shoot_{side}"] for side in _SIDES)
# Triggered use buttons in priority order: bomb, then active item, then pill or card.
_USE_BITS = tuple((USES.index(name), _BIT[f"{name}_triggered"]) for name in USES[1:])
_HORIZONTAL = frozenset({"left", "right"})


@dataclass(frozen=True)
class DemoSequence:
    """One uninterrupted stretch of a human run at the agent's decision rate.

    `observations` are raw encoder vectors (T, OBSERVATION_SIZE) stored as float16; `actions` are
    (T, 3) indices of move, shoot and use in the order of `episodes.DIRECTIONS` and `USES`.
    `seconds` is the game time the sequence covers (its decision frames plus the last action);
    `frames` holds the game frame of each decision point and `characters` the player's
    `character_type` there (`UNKNOWN_CHARACTER` without a player).
    """

    observations: NDArray[np.float16]
    actions: NDArray[np.int64]
    source: str
    seconds: float = 0.0
    frames: NDArray[np.int64] | None = None
    characters: NDArray[np.int64] | None = None


def watchdog_limits(reward_version: int = 13) -> tuple[float, float | None]:
    """Stall and calm-room limits (seconds) of the live watchdog under this reward contract."""
    from .rewards import (
        DEFAULT_CONFIG_V9,
        DEFAULT_CONFIG_V10,
        DEFAULT_CONFIG_V11,
        DEFAULT_CONFIG_V12,
        DEFAULT_CONFIG_V13,
        RewardV4Coefficients,
    )

    configs = {
        9: DEFAULT_CONFIG_V9,
        10: DEFAULT_CONFIG_V10,
        11: DEFAULT_CONFIG_V11,
        12: DEFAULT_CONFIG_V12,
        13: DEFAULT_CONFIG_V13,
    }
    if reward_version not in configs:
        raise ValueError(f"Unsupported reward version {reward_version}; use 9 to 13")
    coefficients = RewardV4Coefficients.load(configs[reward_version])
    stall = coefficients.stall_seconds or DEFAULT_STALL_SECONDS
    return stall, coefficients.stall_calm_seconds


# --- labels -----------------------------------------------------------------------------


def label_window(
    masks: Sequence[int | None], velocity: tuple[float, float] = (0.0, 0.0)
) -> tuple[int, int, int] | None:
    """Move, shoot and use indices for the masks of one action window, oldest first.

    None marks a frame without a mask (dropped or missing). With more than half of the window
    missing the result is None: the window cannot be labelled. Move and shoot take the
    direction held on most frames. A move tie across axes (a diagonal) goes to the axis of the
    larger `velocity` component (the player's velocity at the decision frame), a shoot tie to
    the direction held on the latest frame; any remaining tie follows left, right, up, down.
    Use is the triggered button with the highest priority: bomb, active item, pill or card.
    """
    present = [mask for mask in masks if mask is not None]
    if not masks or 2 * (len(masks) - len(present)) > len(masks):
        return None
    move_counts = [sum(1 for mask in present if mask & bit) for bit in _MOVE_BITS]
    move = 0
    if max(move_counts) > 0:
        tied = [
            side
            for side, count in zip(_SIDES, move_counts, strict=True)
            if count == max(move_counts)
        ]
        speed_x, speed_y = abs(velocity[0]), abs(velocity[1])
        if speed_x != speed_y and {*tied} & _HORIZONTAL and {*tied} - _HORIZONTAL:
            tied = [side for side in tied if (side in _HORIZONTAL) == (speed_x > speed_y)]
        move = DIRECTIONS.index(tied[0])
    shoot_counts = [sum(1 for mask in present if mask & bit) for bit in _SHOOT_BITS]
    shoot = 0
    if max(shoot_counts) > 0:
        tied_bits = [
            (side, bit)
            for side, bit, count in zip(_SIDES, _SHOOT_BITS, shoot_counts, strict=True)
            if count == max(shoot_counts)
        ]
        latest = max(
            max(index for index, mask in enumerate(present) if mask & bit) for _, bit in tied_bits
        )
        shoot = DIRECTIONS.index(next(side for side, bit in tied_bits if present[latest] & bit))
    use = next((index for index, bit in _USE_BITS if any(mask & bit for mask in present)), 0)
    return move, shoot, use


# --- replay -----------------------------------------------------------------------------


class _Clock:
    """The watchdog's clock: the receipt time of the snapshot being fed."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@dataclass
class _Decision:
    frame_id: int
    observation: NDArray[np.float16]
    velocity: tuple[float, float]
    character: int = UNKNOWN_CHARACTER
    segment_end: int | None = None


@dataclass
class _Run:
    """Replay state of one run, mirroring `LiveBackend` from `start_episode` on."""

    key: tuple[str, int]
    current: DemoSnapshot
    watchdog: StallWatchdog
    progress: RunProgress
    target: int
    decisions: list[_Decision] = field(default_factory=list)
    masks: dict[int, int] = field(default_factory=dict)
    last_frame: int = 0
    segment_start: int = 0


class _Replay:
    """Turns one recording's snapshot stream into decision points and labelled sequences."""

    def __init__(
        self,
        source: str,
        *,
        repeat: int,
        stall_seconds: float,
        calm_seconds: float | None,
        min_steps: int,
    ) -> None:
        if not 1 <= repeat <= 15:
            raise ValueError("Action repeat must be 1..15 game updates")
        self.source = source
        self.repeat = repeat
        self.stall_seconds = stall_seconds
        self.calm_seconds = calm_seconds
        self.min_steps = min_steps
        self.clock = _Clock()
        self.deriver = EventDeriver()  # one per connection, like the backend's
        self.visited = VisitedCells()  # run-long, like the env's
        self.run: _Run | None = None
        self.finished: set[tuple[str, int]] = set()  # runs that ended in a death
        self.sequences: list[DemoSequence] = []
        self.resume_room = False
        self.resume_preserve_target = False

    def feed(self, t: float, snap: DemoSnapshot) -> None:
        self.clock.now = t
        key = (snap.session_id, snap.game_epoch)
        run = self.run
        if run is not None and key != run.key:
            self.close()  # live faults here and starts a new episode on the new run
            run = None
        if run is None:
            if key not in self.finished and _playable(snap):
                self._start(snap, key)
            return
        self._note_masks(run, snap)
        # From here on `LiveBackend._absorb`.
        if not _playable(snap) and (snap.oracle is None or not snap.oracle.player_dead):
            self._watch(run, snap, ())
            return
        assert snap.frame_id is not None and run.current.frame_id is not None
        if snap.frame_id <= run.current.frame_id and not self.resume_room:
            return
        if self.resume_room:
            events = self.deriver.begin(snap)
            self.resume_room = False
            if not self.resume_preserve_target:
                run.target = snap.frame_id
            self.resume_preserve_target = False
        else:
            events = self.deriver.update(snap)
        run.current = snap
        self._watch(run, snap, events)
        if snap.oracle is not None and snap.oracle.player_dead:
            self.finished.add(key)
            self.close()
        elif snap.frame_id >= run.target:
            self._decide(run, snap)

    def close(self) -> None:
        """End the current run: label its decisions and keep its long enough sequences."""
        run, self.run = self.run, None
        if run is None:
            return
        pending: list[tuple[_Decision, tuple[int, int, int]]] = []
        for decision in run.decisions:
            window = [
                run.masks.get(frame)
                if frame <= run.last_frame
                and (decision.segment_end is None or frame <= decision.segment_end)
                else None
                for frame in range(decision.frame_id + 1, decision.frame_id + self.repeat + 1)
            ]
            label = label_window(window, decision.velocity)
            if label is None:
                if decision.segment_end is not None:
                    continue  # no evidence for the old file's unfinished boundary window
                self._flush(run, pending)
                pending = []
            else:
                pending.append((decision, label))
        self._flush(run, pending)

    def _flush(self, run: _Run, pending: list[tuple[_Decision, tuple[int, int, int]]]) -> None:
        if len(pending) < self.min_steps:
            return
        first, last = pending[0][0].frame_id, pending[-1][0].frame_id
        session, epoch = run.key
        self.sequences.append(
            DemoSequence(
                observations=np.stack([decision.observation for decision, _ in pending]),
                actions=np.array([label for _, label in pending], dtype=np.int64),
                source=f"{self.source}:{session[:8]}:{epoch}:{first}",
                seconds=(last + self.repeat - first) / GAME_UPDATES_PER_SECOND,
                frames=np.array([decision.frame_id for decision, _ in pending], dtype=np.int64),
                characters=np.array(
                    [decision.character for decision, _ in pending], dtype=np.int64
                ),
            )
        )

    def _start(self, snap: DemoSnapshot, key: tuple[str, int]) -> None:
        """`LiveBackend.start_episode`: a fresh watchdog and run facts; no watch here."""
        frame, oracle = snap.entity_frame, snap.oracle
        assert frame is not None and oracle is not None and snap.frame_id is not None
        watchdog = StallWatchdog(
            self.stall_seconds, clock=self.clock, calm_seconds=self.calm_seconds
        )
        progress = RunProgress()
        progress.reset(
            stage=frame.room.stage,
            room_index=oracle.room_index,
            counters={
                "coin": frame.inventory.coins,
                "bomb": frame.inventory.bombs,
                "key": frame.inventory.keys,
            },
            items=frame.collectibles,
        )
        self.deriver.begin(snap)
        run = _Run(key, snap, watchdog, progress, target=snap.frame_id)
        self.run = run
        self._note_masks(run, snap)
        self._decide(run, snap)

    def _watch(self, run: _Run, snap: DemoSnapshot, events: Sequence[OracleEvent]) -> None:
        """`LiveBackend._watch`. A firing watchdog is re-armed: the live run would have
        restarted, but the human played on."""
        stage = snap.entity_frame.room.stage if snap.entity_frame is not None else 0
        progress = run.progress.novel(events, stage=stage)
        calm = (
            snap.oracle is not None
            and snap.oracle.room_clear
            and not snap.oracle.enemies
            and snap.oracle.enemy_overflow == 0
        )
        if run.watchdog.observe(active=_playable(snap), progress=progress, calm=calm):
            run.watchdog.reset()

    def _decide(self, run: _Run, snap: DemoSnapshot) -> None:
        """`IsaacCombatEnv._observe` at a decision point; the next one waits `repeat` frames."""
        frame = snap.entity_frame
        assert frame is not None
        watchdog = run.watchdog
        stall = min(max(watchdog.idle_seconds / watchdog.limit, 0.0), 1.0)
        encoded = encode(frame, stall_fraction=stall, visited_cells=self.visited.update(frame))
        velocity = frame.player_velocity
        run.decisions.append(
            _Decision(
                frame.frame_id,
                encoded.vector.astype(np.float16),
                (0.0, 0.0) if velocity is None else (velocity.x, velocity.y),
                UNKNOWN_CHARACTER if snap.player is None else snap.player.character_type,
            )
        )
        run.target = frame.frame_id + self.repeat

    @staticmethod
    def _note_masks(run: _Run, snap: DemoSnapshot) -> None:
        """Mask i of n belongs to frame `frame_id - (n - 1 - i)`; the first mask seen wins."""
        if snap.frame_id is None:
            return
        masks = snap.human_input.masks
        for offset, mask in enumerate(masks):
            run.masks.setdefault(snap.frame_id - (len(masks) - 1 - offset), mask)
        run.last_frame = max(run.last_frame, snap.frame_id)


def replay_recording(
    path: Path,
    *,
    repeat: int,
    stall_seconds: float,
    calm_seconds: float | None,
    min_steps: int = MIN_STEPS,
) -> list[DemoSequence]:
    """Sequences of one recording, without the cache."""
    _, records = read_recording(path)
    replay = _Replay(
        path.name,
        repeat=repeat,
        stall_seconds=stall_seconds,
        calm_seconds=calm_seconds,
        min_steps=min_steps,
    )
    for t, snap in records:
        replay.feed(t, snap)
    replay.close()
    return replay.sequences


@dataclass(frozen=True)
class _Boundary:
    created: datetime | None
    first_receipt: float | None
    first: tuple[float, DemoSnapshot] | None
    last: tuple[float, DemoSnapshot] | None
    last_active: tuple[float, DemoSnapshot] | None


def _boundary(path: Path) -> _Boundary:
    """Read the identity and time evidence at a recording boundary."""
    manifest, records = read_recording(path)
    try:
        created = (
            datetime.fromisoformat(manifest["created_at"]) if manifest.get("created_at") else None
        )
    except (TypeError, ValueError):
        created = None
    first = last = last_active = None
    first_receipt = None
    for t, snap in records:
        if first_receipt is None:
            first_receipt = t
        if snap.oracle is not None and snap.frame_id is not None:
            if first is None:
                first = (t, snap)
            last = (t, snap)
            if snap.status == "active":
                last_active = (t, snap)
    return _Boundary(created, first_receipt, first, last, last_active)


def _continues(previous: _Boundary, current: _Boundary) -> bool:
    earlier, later = previous.last, current.first
    if earlier is None or later is None or previous.last_active is None:
        return False
    t1, a = earlier
    t2, b = later
    assert a.oracle is not None and b.oracle is not None
    active = previous.last_active[1]
    if active.oracle is None or active.oracle.player_dead:
        return False
    if a.entity_frame is None or b.entity_frame is None or a.player is None or b.player is None:
        return False
    room_a, room_b = a.entity_frame.room, b.entity_frame.room
    gap_seconds = t2 - t1
    if not 0 <= gap_seconds <= IDLE_LIMIT_SECONDS:
        if previous.created is None or current.created is None or previous.first_receipt is None:
            return False
        try:
            gap_seconds = (current.created - previous.created).total_seconds() - (
                t1 - previous.first_receipt
            )
        except TypeError:
            return False
    if (
        a.frame_id is None
        or b.frame_id is None
        or b.frame_id < 300
        or not 0 <= gap_seconds <= IDLE_LIMIT_SECONDS
        or not a.frame_id - 900 <= b.frame_id <= a.frame_id + 30 * gap_seconds + 300
        or (room_a.stage, room_a.stage_type, a.player.character_type)
        != (room_b.stage, room_b.stage_type, b.player.character_type)
        or (
            a.oracle.run_seed is not None
            and b.oracle.run_seed is not None
            and a.oracle.run_seed != b.oracle.run_seed
        )
    ):
        return False
    return True


def _groups(paths: Sequence[Path]) -> list[list[Path]]:
    groups: list[list[Path]] = []
    previous = None
    entries = [(path, _boundary(path)) for path in paths]
    entries.sort(
        key=lambda entry: (
            entry[1].created.timestamp() if entry[1].created else float("inf"),
            str(entry[0]),
        )
    )
    for path, boundary in entries:
        if groups and previous is not None and _continues(previous, boundary):
            groups[-1].append(path)
        else:
            groups.append([path])
        previous = boundary
    return groups


def replay_recordings(
    paths: Sequence[Path],
    *,
    repeat: int,
    stall_seconds: float,
    calm_seconds: float | None,
    min_steps: int = MIN_STEPS,
) -> list[DemoSequence]:
    """Replay a verified continuation group without resetting its run state."""
    replay = _Replay(
        paths[0].name,
        repeat=repeat,
        stall_seconds=stall_seconds,
        calm_seconds=calm_seconds,
        min_steps=min_steps,
    )
    canonical_session: str | None = None
    epoch_offset = 0
    frame_offset = 0
    previous_end: tuple[float, int] | None = None
    for file_index, path in enumerate(paths):
        _, records = read_recording(path)
        boundary_pending = file_index > 0
        shift_pending = file_index > 0
        epoch_pending = file_index > 0
        file_end: tuple[float, int] | None = None
        for t, snap in records:
            if snap.frame_id is not None and snap.oracle is not None:
                file_end = (t, snap.frame_id)
                if boundary_pending and replay.run is not None:
                    run = replay.run
                    contiguous = (
                        previous_end is not None
                        and 0 <= t - previous_end[0] <= 1.0
                        and 0 <= snap.frame_id - previous_end[1] <= repeat
                    )
                    if not contiguous:
                        for decision in run.decisions[run.segment_start :]:
                            if decision.frame_id + repeat > run.last_frame:
                                decision.segment_end = run.last_frame
                    run.segment_start = len(run.decisions)
                    run.watchdog.reset()
                    replay.resume_room = True
                    replay.resume_preserve_target = contiguous
                    boundary_pending = False
            if canonical_session is None:
                canonical_session = snap.session_id
            if epoch_pending:
                if replay.run is not None:
                    epoch_offset = replay.run.key[1] - snap.game_epoch
                epoch_pending = False
            if shift_pending and snap.frame_id is not None:
                if replay.run is not None and snap.frame_id + frame_offset < replay.run.last_frame:
                    frame_offset = replay.run.last_frame + 1 - snap.frame_id
                shift_pending = False
            frame = snap.entity_frame
            if frame is not None:
                frame = frame.model_copy(
                    update={
                        "session_id": canonical_session,
                        "game_epoch": frame.game_epoch + epoch_offset,
                        "frame_id": frame.frame_id + frame_offset,
                    }
                )
            snap = snap.model_copy(
                update={
                    "session_id": canonical_session,
                    "game_epoch": snap.game_epoch + epoch_offset,
                    "entity_frame": frame,
                    "frame_id": None if snap.frame_id is None else snap.frame_id + frame_offset,
                }
            )
            replay.feed(t, snap)
        previous_end = file_end
    replay.close()
    return replay.sequences


# --- cache ------------------------------------------------------------------------------


def cache_path(
    path: Path,
    *,
    repeat: int,
    stall_seconds: float,
    calm_seconds: float | None,
    min_steps: int = MIN_STEPS,
) -> Path:
    """`<name>.bc-<key>.npz` beside the recording; the key covers its bytes and every rule."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1 << 20):
            digest.update(chunk)
    parts = (
        digest.hexdigest(),
        repeat,
        float(stall_seconds),
        None if calm_seconds is None else float(calm_seconds),
        min_steps,
        OBSERVATION_SIZE,
        OBSERVATION_SCHEMA_VERSION,
        LABELER_VERSION,
    )
    key = hashlib.sha256(repr(parts).encode()).hexdigest()[:16]
    stem = path.name.removesuffix(".gz").removesuffix(".jsonl")
    return path.with_name(f"{stem}.bc-{key}.npz")


def _save(target: Path, sequences: Sequence[DemoSequence]) -> None:
    observations = [s.observations for s in sequences]
    actions = [s.actions for s in sequences]
    frames = [np.array([], np.int64) if s.frames is None else s.frames for s in sequences]
    characters = [
        np.full(len(s.actions), UNKNOWN_CHARACTER, np.int64)
        if s.characters is None
        else s.characters
        for s in sequences
    ]
    temporary = target.with_name(f"{target.name}.{os.getpid()}.tmp.npz")
    np.savez_compressed(
        temporary,
        observations=np.concatenate(
            [np.zeros((0, OBSERVATION_SIZE), dtype=np.float16), *observations]
        ),
        actions=np.concatenate([np.zeros((0, 3), dtype=np.int64), *actions]),
        frames=np.concatenate([np.zeros(0, dtype=np.int64), *frames]),
        characters=np.concatenate([np.zeros(0, dtype=np.int64), *characters]),
        lengths=np.array([len(s.actions) for s in sequences], dtype=np.int64),
        seconds=np.array([s.seconds for s in sequences], dtype=np.float64),
        sources=np.array([s.source for s in sequences], dtype=np.str_),
    )
    os.replace(temporary, target)


def _load(target: Path) -> list[DemoSequence]:
    with np.load(target, allow_pickle=False) as data:
        observations, actions, frames = data["observations"], data["actions"], data["frames"]
        characters = data["characters"]
        lengths, seconds, sources = data["lengths"], data["seconds"], data["sources"]
    if (
        observations.dtype != np.float16
        or observations.shape[1:] != (OBSERVATION_SIZE,)
        or actions.shape != (len(observations), 3)
        or frames.shape != (len(observations),)
        or characters.shape != (len(observations),)
        or int(lengths.sum()) != len(observations)
        or not len(lengths) == len(seconds) == len(sources)
    ):
        raise ValueError(f"{target}: inconsistent cache")
    if not len(lengths):
        return []
    bounds = np.cumsum(lengths)[:-1]
    return [
        DemoSequence(
            obs,
            act.astype(np.int64),
            str(source),
            float(span),
            ids.astype(np.int64),
            types.astype(np.int64),
        )
        for obs, act, source, span, ids, types in zip(
            np.split(observations, bounds),
            np.split(actions, bounds),
            sources,
            seconds,
            np.split(frames, bounds),
            np.split(characters, bounds),
            strict=True,
        )
    ]


# --- character filter -------------------------------------------------------------------


def filter_characters(
    sequences: Sequence[DemoSequence],
    characters: Collection[int],
    *,
    repeat: int,
    min_steps: int = MIN_STEPS,
) -> list[DemoSequence]:
    """Only the decision points of `characters`; a point outside them splits its sequence.

    A switch between two kept characters (Lazarus rising, Judas turning dark) stays in one
    sequence: it is the same run. Pieces shorter than `min_steps` are dropped. A sequence
    without per-step characters counts as `UNKNOWN_CHARACTER` and is dropped.
    """
    allowed = np.array(sorted(set(characters)), dtype=np.int64)
    kept: list[DemoSequence] = []
    for sequence in sequences:
        types = (
            np.full(len(sequence.actions), UNKNOWN_CHARACTER, np.int64)
            if sequence.characters is None
            else sequence.characters
        )
        keep = np.isin(types, allowed)
        if keep.all():
            kept.append(sequence)
            continue
        edges = np.flatnonzero(np.diff(np.concatenate(([0], keep.astype(np.int8), [0]))))
        for start, stop in zip(edges[::2], edges[1::2], strict=True):
            if stop - start < min_steps:
                continue
            frames = None if sequence.frames is None else sequence.frames[start:stop]
            seconds = (
                sequence.seconds * (stop - start) / len(sequence.actions)
                if frames is None
                else (int(frames[-1]) + repeat - int(frames[0])) / GAME_UPDATES_PER_SECOND
            )
            kept.append(
                DemoSequence(
                    observations=sequence.observations[start:stop],
                    actions=sequence.actions[start:stop],
                    source=f"{sequence.source}+{start}",
                    seconds=seconds,
                    frames=frames,
                    characters=types[start:stop],
                )
            )
    return kept


# --- public API -------------------------------------------------------------------------


def recordings(paths: Sequence[Path]) -> list[Path]:
    """Recording files of `paths`: files as given, directories as their sorted `*.jsonl.gz`."""
    found: list[Path] = []
    for path in map(Path, paths):
        found.extend(sorted(path.glob(RECORDING_GLOB)) if path.is_dir() else [path])
    return found


def load_demos(
    paths: Sequence[Path],
    *,
    repeat: int,
    stall_seconds: float,
    calm_seconds: float | None,
    cache: bool = True,
    min_steps: int = MIN_STEPS,
    characters: Collection[int] | None = None,
) -> list[DemoSequence]:
    """Behaviour-cloning sequences of every recording in `paths`, in file order.

    Per run, the first playable snapshot is a decision point, then each first playable snapshot
    at least `repeat` frames after the previous decision, as the live step waits. Paused and
    unavailable snapshots only feed the watchdog; a death or a new run ends the run. A decision
    whose action window has more than half of its masks missing splits the sequence, and
    sequences shorter than `min_steps` are dropped. With `cache`, results are kept beside each
    recording (`cache_path`); a missing or corrupt cache is rebuilt. With `characters`, only
    their decision points are kept (`filter_characters`); the cache holds every character.
    """
    options: dict[str, Any] = dict(
        repeat=repeat, stall_seconds=stall_seconds, calm_seconds=calm_seconds, min_steps=min_steps
    )
    sequences: list[DemoSequence] = []
    for group in _groups(recordings(paths)):
        path = group[0]
        target = cache_path(path, **options) if cache else None
        if target is not None and len(group) > 1:
            digest = hashlib.sha256()
            for member in group:
                with member.open("rb") as stream:
                    while chunk := stream.read(1 << 20):
                        digest.update(chunk)
            target = target.with_name(f"{target.stem}-{digest.hexdigest()[:16]}.npz")
        if target is not None and target.exists():
            try:
                sequences.extend(_load(target))
                continue
            except (OSError, ValueError, KeyError, EOFError, zlib.error):
                pass  # a corrupt or foreign cache is rebuilt
        found = (
            replay_recording(path, **options)
            if len(group) == 1
            else replay_recordings(group, **options)
        )
        if target is not None:
            try:
                _save(target, found)
            except OSError:
                pass  # a read-only recording folder only costs the next replay
        sequences.extend(found)
    if characters is not None:
        return filter_characters(sequences, characters, repeat=repeat, min_steps=min_steps)
    return sequences


def describe(sequences: Sequence[DemoSequence]) -> dict[str, Any]:
    """Steps, sequences, game seconds and the label distribution per head, for logs."""
    actions = np.concatenate([np.zeros((0, 3), dtype=np.int64), *(s.actions for s in sequences)])
    heads = {"move": DIRECTIONS, "shoot": DIRECTIONS, "use": USES}
    labels = {
        head: {names[index]: count for index, count in sorted(Counter(column.tolist()).items())}
        for (head, names), column in zip(heads.items(), actions.T, strict=True)
    }
    return {
        "steps": len(actions),
        "sequences": len(sequences),
        "seconds": round(sum(s.seconds for s in sequences), 3),
        "labels": labels,
        "characters": _character_steps(sequences),
    }


def _character_steps(sequences: Sequence[DemoSequence]) -> dict[str, int]:
    """Decision steps per `character_type`, as strings for JSON."""
    counts: Counter[int] = Counter()
    for sequence in sequences:
        if sequence.characters is None:
            counts[UNKNOWN_CHARACTER] += len(sequence.actions)
        else:
            counts.update(sequence.characters.tolist())
    return {str(character): count for character, count in sorted(counts.items())}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarise demo recordings as BC sequences.")
    parser.add_argument("paths", nargs="+", type=Path, help="recordings or directories")
    parser.add_argument("--repeat", type=int, default=6, help="action repeat in game updates")
    parser.add_argument("--reward-version", type=int, default=13, help="source of stall limits")
    parser.add_argument("--min-steps", type=int, default=MIN_STEPS)
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument(
        "--characters",
        default=",".join(map(str, DEFAULT_CHARACTERS)),
        help="comma-separated character types to keep (default: the training default), or 'all'",
    )
    args = parser.parse_args(argv)
    stall, calm = watchdog_limits(args.reward_version)
    every = load_demos(
        args.paths,
        repeat=args.repeat,
        stall_seconds=stall,
        calm_seconds=calm,
        cache=not args.no_cache,
        min_steps=args.min_steps,
    )
    if args.characters == "all":
        kept = every
    else:
        try:
            wanted = [int(value) for value in args.characters.split(",") if value.strip()]
        except ValueError:
            parser.error("--characters takes comma-separated integers or 'all'")
        kept = filter_characters(every, wanted, repeat=args.repeat, min_steps=args.min_steps)
    summary = describe(kept)
    summary["dropped_steps"] = describe(every)["steps"] - summary["steps"]
    summary["recorded_characters"] = _character_steps(every)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
