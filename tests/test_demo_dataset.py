"""Demo recordings to BC sequences: labels, decision points, cache, and live-env fidelity."""

import copy
import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from demo_boundary_fixtures import BOUNDARIES
from demo_fixtures import BIT, SESSION, demo_raw, parse, write_recording

from isaac_threrisaifuture import demo_dataset
from isaac_threrisaifuture.demo_dataset import (
    cache_path,
    describe,
    label_window,
    load_demos,
    read_recording,
    watchdog_limits,
)
from isaac_threrisaifuture.encoding import (
    OBSERVATION_SIZE,
    STALL_OFFSET,
    VISITED_OFFSET,
    feature_kinds,
)
from isaac_threrisaifuture.episodes import DIRECTIONS, USES
from isaac_threrisaifuture.live import make_live_env
from isaac_threrisaifuture.live_wire import LiveCommandAck

STALL, CALM = watchdog_limits(13)
STILL = np.array([0, 0, 0])

LEFT, RIGHT, UP, DOWN = (BIT[f"move_{side}"] for side in ("left", "right", "up", "down"))
S_LEFT, S_RIGHT, S_UP, S_DOWN = (BIT[f"shoot_{s}"] for s in ("left", "right", "up", "down"))


def labels(move: str, shoot: str, use: str) -> tuple[int, int, int]:
    return DIRECTIONS.index(move), DIRECTIONS.index(shoot), USES.index(use)


# --- labels ----------------------------------------------------------------------------


def test_watchdog_limits_follow_the_reward_contract():
    assert (STALL, CALM) == (30.0, 15.0)
    assert watchdog_limits(12) == (30.0, None)
    with pytest.raises(ValueError):
        watchdog_limits(1)


def test_no_input_is_none_on_every_head():
    assert label_window([0, 0, 0]) == labels("none", "none", "none")


def test_single_direction_and_majority():
    assert label_window([LEFT, LEFT, 0]) == labels("left", "none", "none")
    assert label_window([UP, DOWN, DOWN, 0, 0, 0]) == labels("down", "none", "none")


def test_diagonal_tie_goes_to_the_faster_axis_then_the_fixed_order():
    diagonal = [LEFT | UP] * 3
    assert label_window(diagonal, (-1.0, 4.0)) == labels("up", "none", "none")
    assert label_window(diagonal, (-4.0, 1.0)) == labels("left", "none", "none")
    assert label_window(diagonal, (2.0, -2.0)) == labels("left", "none", "none")
    # Opposite buttons on one axis have no faster axis: the order decides.
    assert label_window([LEFT | RIGHT] * 3, (0.0, 9.0)) == labels("left", "none", "none")


def test_shoot_tie_goes_to_the_latest_held_direction():
    assert label_window([S_LEFT, S_DOWN, 0]) == labels("none", "down", "none")
    assert label_window([S_DOWN, S_LEFT, 0]) == labels("none", "left", "none")
    assert label_window([S_UP | S_RIGHT, S_UP | S_RIGHT]) == labels("none", "right", "none")
    assert label_window([S_UP, S_UP, S_LEFT]) == labels("none", "up", "none")


def test_use_needs_a_trigger_and_follows_bomb_active_pillcard():
    held = BIT["bomb"] | BIT["active"] | BIT["pillcard"]
    assert label_window([held] * 3) == labels("none", "none", "none")
    assert label_window([BIT["pillcard_triggered"], BIT["active_triggered"], 0]) == labels(
        "none", "none", "active"
    )
    assert label_window([0, BIT["pillcard_triggered"] | BIT["bomb_triggered"], 0]) == labels(
        "none", "none", "bomb"
    )
    assert label_window([BIT["pillcard_triggered"], 0, 0]) == labels("none", "none", "pillcard")


def test_more_than_half_missing_cannot_be_labelled():
    assert label_window([LEFT, None, LEFT]) == labels("left", "none", "none")
    assert label_window([LEFT, None, None]) is None
    assert label_window([LEFT, None, None, LEFT]) == labels("left", "none", "none")
    assert label_window([]) is None


# --- decision points -------------------------------------------------------------------


class Stream:
    """Builds a recorded snapshot stream; each active snapshot carries one mask per new frame."""

    def __init__(self, t: float = 100.0, frame: int = 50, mask: Any = None) -> None:
        self.records: list[tuple[float, dict[str, Any]]] = []
        self.t, self.frame, self.sequence = t, frame, 0
        self.mask = mask or (lambda frame: LEFT)

    def add(self, dt: float = 0.5, frames: int = 1, **changes: Any) -> None:
        self.sequence += 1
        self.t += dt
        status = changes.get("status", "active")
        if status != "unavailable":
            self.frame += frames
        count = frames if status == "active" else 0
        masks = tuple(self.mask(self.frame - (count - 1 - i)) for i in range(min(count, 16)))
        changes.setdefault("masks", masks)
        frame_id = None if status == "unavailable" else self.frame
        self.records.append((self.t, demo_raw(self.sequence, frame_id, **changes)))

    def write(self, path: Path, **options: Any) -> Path:
        return write_recording(path, self.records, **options)


def frames_of(sequences):
    return [sequence.frames.tolist() for sequence in sequences]


def load(path: Path, *, repeat: int = 3, min_steps: int = 1, **options: Any):
    return load_demos(
        [path],
        repeat=repeat,
        stall_seconds=STALL,
        calm_seconds=CALM,
        cache=False,
        min_steps=min_steps,
        **options,
    )


def test_decisions_wait_repeat_frames_over_irregular_snapshots(tmp_path):
    stream = Stream()
    stream.add(status="unavailable")  # before the run: skipped
    for frames in (1, 2, 1, 1, 3, 1, 2, 2, 1, 4, 1, 1, 1, 1):
        stream.add(frames=frames)
    # Frames 51 53 54 55 58 59 61 63 64 68 69 70 71 72.
    [sequence] = load(stream.write(tmp_path / "a.jsonl.gz"))
    # The last decision, 71, is left out: its window (71, 74] has one of its three frames.
    assert sequence.frames.tolist() == [51, 54, 58, 61, 64, 68]
    assert frames_of(load(tmp_path / "a.jsonl.gz", repeat=6)) == [[51, 58, 64]]


def test_pauses_and_unavailable_snapshots_add_no_decision_and_keep_the_sequence(tmp_path):
    stream = Stream()
    for _ in range(4):
        stream.add(frames=2)  # 52 54 56 58
    stream.add(status="paused", dt=30.0, frames=0)
    stream.add(status="unavailable", dt=30.0)
    for _ in range(4):
        stream.add(frames=2)  # 60 62 64 66
    [sequence] = load(stream.write(tmp_path / "p.jsonl.gz"))
    assert sequence.frames.tolist() == [52, 56, 60, 64]
    # 60 s of pause and menu never counts as idle time.
    assert float(sequence.observations[:, STALL_OFFSET].max()) < 2.5 / STALL


def test_death_and_a_new_epoch_end_the_run(tmp_path):
    stream = Stream()
    for _ in range(4):
        stream.add(frames=3)  # 53 56 59 62
    stream.add(frames=3, dead=True)  # 65: the run ends here
    stream.add(frames=3, dead=True)
    stream.add(frames=3)  # still epoch 1 after the death: no new run
    for _ in range(3):
        stream.add(frames=3, epoch=2)  # 74 77 80
    for _ in range(2):
        stream.add(frames=3, epoch=3)  # 83 86: a new epoch without a death
    sequences = load(stream.write(tmp_path / "d.jsonl.gz"))
    # The last decision of a run that is cut short has no frames in its window.
    assert frames_of(sequences) == [[53, 56, 59, 62], [74, 77], [83]]
    assert [s.source.split(":")[2] for s in sequences] == ["1", "2", "3"]
    assert frames_of(load(tmp_path / "d.jsonl.gz", min_steps=2)) == [[53, 56, 59, 62], [74, 77]]


def test_missing_masks_split_the_sequence_and_short_parts_are_dropped(tmp_path):
    stream = Stream()
    for index in range(20):
        if index == 10:
            stream.add(frames=3, masks=(), dropped=3)  # frames 81 to 83 lost their masks
        else:
            stream.add(frames=3)
    sequences = load(stream.write(tmp_path / "m.jsonl.gz"))
    # Decision 80 covers frames 81-83 and cannot be labelled: the sequence splits around it.
    assert frames_of(sequences) == [list(range(53, 78, 3)), list(range(83, 108, 3))]
    assert all(s.actions[:, 0].tolist() == [1] * len(s.actions) for s in sequences)
    assert load(tmp_path / "m.jsonl.gz", min_steps=10) == []


def test_a_stall_rearms_the_watchdog_and_the_sequence_goes_on(tmp_path):
    stream = Stream()
    for _ in range(60):
        stream.add(dt=1.0, frames=3, clear=True)  # calm room, no progress for a minute
    [sequence] = load(stream.write(tmp_path / "s.jsonl.gz"))
    stall = sequence.observations[:, STALL_OFFSET].astype(np.float64)
    assert len(sequence.actions) == 59
    assert stall.max() == pytest.approx(14.0 / CALM, abs=1e-3)  # it fires at 15 s, never 1.0
    # Fired at decision 16 and re-armed; the next gap is not counted, like after a reset.
    assert stall[15] == pytest.approx(14.0 / CALM, abs=1e-3)
    assert stall[16] == stall[17] == 0.0 and stall[18] == pytest.approx(1.0 / CALM, abs=1e-3)


# --- recordings and cache --------------------------------------------------------------


def long_stream() -> Stream:
    stream = Stream()
    for index in range(30):
        stream.add(frames=3, x=120.0 + 10 * index)
    return stream


def _seeded_records():
    stream = Stream(frame=350)
    for index in range(30):
        stream.add(
            frames=3,
            x=120.0 + 10 * index,
            room_index=84 if index < 15 else 85,
            visit=1 if index < 15 else 2,
        )
    records = copy.deepcopy(stream.records)
    for _, raw in records:
        raw["oracle"]["run_seed"] = "AAAA BBBB"
    return records


def _new_session(records):
    for _, raw in records:
        raw["session_id"] = "e" * 32
        raw["entity_frame"]["session_id"] = "e" * 32
    return records


def test_split_same_run_matches_unsplit_vectors_and_actions(tmp_path):
    records = _seeded_records()
    whole = write_recording(tmp_path / "whole.jsonl.gz", records)
    a = write_recording(tmp_path / "a.jsonl.gz", records[:15])
    b = write_recording(tmp_path / "b.jsonl.gz", _new_session(copy.deepcopy(records[15:])))
    expected = load(whole)
    actual = load_demos(
        [a, b], repeat=3, stall_seconds=STALL, calm_seconds=CALM, cache=False, min_steps=1
    )
    assert len(expected) == len(actual) == 1
    assert np.array_equal(actual[0].frames, expected[0].frames)
    assert np.array_equal(actual[0].observations, expected[0].observations)
    assert np.array_equal(actual[0].actions, expected[0].actions)


def test_split_different_seed_stays_separate(tmp_path):
    records = _seeded_records()
    later = _new_session(copy.deepcopy(records[15:]))
    for _, raw in later:
        raw["oracle"]["run_seed"] = "CCCC DDDD"
    a = write_recording(tmp_path / "a.jsonl.gz", records[:15])
    b = write_recording(tmp_path / "b.jsonl.gz", later)
    actual = load_demos(
        [a, b], repeat=3, stall_seconds=STALL, calm_seconds=CALM, cache=False, min_steps=1
    )
    assert len(actual) == 2


def test_missing_seeds_and_reloaded_epoch_allow_small_rewind(tmp_path):
    records = _seeded_records()
    earlier = copy.deepcopy(records[:15])
    later = _new_session(copy.deepcopy(records[15:]))
    for _, raw in earlier + later:
        raw["oracle"]["run_seed"] = None
    for _, raw in later:
        raw["game_epoch"] = 2
        raw["entity_frame"]["game_epoch"] = 2
        raw["frame_id"] -= 12
        raw["entity_frame"]["frame_id"] -= 12
    a = write_recording(tmp_path / "a.jsonl.gz", earlier)
    b = write_recording(tmp_path / "b.jsonl.gz", later)
    assert demo_dataset._groups([a, b]) == [[a, b]]
    [sequence] = load_demos(
        [a, b], repeat=3, stall_seconds=STALL, calm_seconds=CALM, cache=False, min_steps=1
    )
    assert len(sequence.actions) > 15


@pytest.mark.parametrize("boundary", ["late", "frame_back", "death", "stage", "character"])
def test_split_unsafe_boundaries_stay_separate(tmp_path, boundary):
    records = _seeded_records()
    earlier = copy.deepcopy(records[:15])
    later = _new_session(copy.deepcopy(records[15:]))
    if boundary == "late":
        later = [(t + 1801, raw) for t, raw in later]
    elif boundary == "frame_back":
        for _, raw in later:
            raw["frame_id"] -= 200
            raw["entity_frame"]["frame_id"] -= 200
    elif boundary == "stage":
        for _, raw in later:
            raw["entity_frame"]["room"]["stage"] = 3
    elif boundary == "character":
        for _, raw in later:
            raw["player"]["character_type"] = 2
    else:
        earlier[-1][1]["oracle"]["player_dead"] = True
    a = write_recording(tmp_path / "a.jsonl.gz", earlier)
    b = write_recording(tmp_path / "b.jsonl.gz", later)
    assert demo_dataset._groups([a, b]) == [[a], [b]]


def test_group_cache_depends_on_every_recording(tmp_path):
    records = _seeded_records()
    a = write_recording(tmp_path / "a.jsonl.gz", records[:15])
    b = write_recording(tmp_path / "b.jsonl.gz", _new_session(copy.deepcopy(records[15:])))
    options = dict(repeat=3, stall_seconds=STALL, calm_seconds=CALM, min_steps=1)
    first = load_demos([a, b], **options)
    cached = load_demos([a, b], **options)
    assert np.array_equal(first[0].observations, cached[0].observations)
    before = set(tmp_path.glob("*.npz"))
    later = _new_session(copy.deepcopy(records[15:]))
    later[-2][1]["human_input"]["masks"] = [RIGHT] * 3
    write_recording(b, later)
    updated = load_demos([a, b], **options)
    assert not np.array_equal(first[0].actions, updated[0].actions)
    assert len(set(tmp_path.glob("*.npz")) - before) == 1


def test_legacy_boundary_regression_fixture():
    def boundary(item):
        _, first, last, active_dead = item

        def snap(values, dead=False):
            _, frame_id, stage, stage_type, character, _ = values
            raw = demo_raw(1, frame_id, dead=dead)
            raw["entity_frame"]["room"]["stage"] = stage
            raw["entity_frame"]["room"]["stage_type"] = stage_type
            raw["player"]["character_type"] = character
            return parse(raw)

        return demo_dataset._Boundary(
            None,
            first[0],
            (first[0], snap(first)),
            (last[0], snap(last)),
            (last[0], snap(last, dead=active_dead)),
        )

    expected = {
        "20261102-135928",
        "20261102-140605",
        "20261102-140916",
        "20261102-150907",
        "20261103-105033",
        "20261103-110043",
        "20261103-110054",
        "20261103-110114",
        "20261103-111604",
        "20261103-111740",
        "20261103-112033",
        "20261103-112337",
        "20261103-112440",
        "20261103-113834",
    }
    assert len(BOUNDARIES) == 36
    actual = {
        b[0]
        for a, b in zip(BOUNDARIES, BOUNDARIES[1:], strict=False)
        if demo_dataset._continues(boundary(a), boundary(b))
    }
    assert actual == expected


def test_truncated_gzip_tail_is_tolerated(tmp_path):
    stream = long_stream()
    whole = load(stream.write(tmp_path / "w.jsonl.gz"))
    cut = load(stream.write(tmp_path / "c.jsonl.gz", cut=40))
    assert 0 < len(cut[0].actions) < len(whole[0].actions)
    assert np.array_equal(cut[0].observations, whole[0].observations[: len(cut[0].actions)])
    _, records = read_recording(tmp_path / "c.jsonl.gz")
    assert 0 < len(list(records)) < 30


def test_not_a_recording_is_refused(tmp_path):
    path = tmp_path / "x.jsonl.gz"
    path.write_bytes(gzip.compress(json.dumps({"type": "other"}).encode() + b"\n"))
    with pytest.raises(ValueError, match="not a demo recording of format 1"):
        read_recording(path)


def test_cache_is_reused_and_a_corrupt_one_is_rebuilt(tmp_path, monkeypatch):
    path = long_stream().write(tmp_path / "r.jsonl.gz")
    options: dict[str, Any] = dict(repeat=3, stall_seconds=STALL, calm_seconds=CALM)
    first = load_demos([tmp_path], **options)
    target = cache_path(path, **options)
    assert target.exists() and target.name.startswith("r.bc-")
    assert cache_path(path, **{**options, "repeat": 6}) != target

    def no_replay(*_: Any, **__: Any):
        raise AssertionError("the cache should have been used")

    with monkeypatch.context() as patch:
        patch.setattr(demo_dataset, "replay_recording", no_replay)
        cached = load_demos([path], **options)
    assert len(cached) == len(first) == 1
    for a, b in zip(cached, first, strict=True):
        assert np.array_equal(a.observations, b.observations)
        assert np.array_equal(a.actions, b.actions) and np.array_equal(a.frames, b.frames)
        assert (a.source, a.seconds, a.observations.dtype) == (b.source, b.seconds, np.float16)
    target.write_bytes(b"not a zip")
    rebuilt = load_demos([path], **options)
    assert np.array_equal(rebuilt[0].observations, first[0].observations)
    assert np.load(target)["observations"].shape == (len(first[0].actions), OBSERVATION_SIZE)
    path.write_bytes(path.read_bytes())  # same bytes, same key
    assert cache_path(path, **options) == target
    assert not list(tmp_path.glob("*.tmp.npz"))


def test_describe_and_cli(tmp_path, capsys):
    path = long_stream().write(tmp_path / "r.jsonl.gz")
    sequences = load(path)
    summary = describe(sequences)
    assert summary["steps"] == 29 and summary["sequences"] == 1
    assert summary["seconds"] == pytest.approx((137 + 3 - 53) / 30)
    assert summary["labels"]["move"] == {"left": 29} and summary["labels"]["use"] == {"none": 29}
    assert describe([])["steps"] == 0
    assert demo_dataset.main([str(tmp_path), "--repeat", "3", "--no-cache"]) == 0
    assert json.loads(capsys.readouterr().out)["steps"] == 29


def test_float16_keeps_continuous_features_within_1e3_and_binary_ones_exact():
    from isaac_threrisaifuture.encoding import VisitedCells, encode

    kinds = np.array(feature_kinds())
    snap = parse(scripted()[5][1])
    assert snap.entity_frame is not None
    vector = encode(
        snap.entity_frame,
        stall_fraction=1 / 3,
        visited_cells=VisitedCells().update(snap.entity_frame),
    ).vector
    half = vector.astype(np.float16).astype(np.float32)
    continuous = kinds == "continuous"
    assert np.abs(half - vector)[continuous].max() < 1e-3
    assert np.array_equal(half[~continuous], vector[~continuous])


# --- fidelity against the live env -----------------------------------------------------


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class Exhausted(Exception):
    """The recording has no more snapshots (not a bridge error: no reconnect loop)."""


class ReplayClient:
    """Serves the recorded snapshots one per take(), at their recorded clock; acks every
    command at the reference frame, as a game with no latency would."""

    connected = True
    failure = None

    def __init__(self, records: list[tuple[float, dict[str, Any]]], clock: Clock) -> None:
        self.records, self.clock, self.index = records, clock, 0
        self.sent: list[str] = []

    def drain(self):
        return []

    def take(self, timeout):
        if self.index >= len(self.records):
            raise Exhausted
        t, raw = self.records[self.index]
        self.index += 1
        self.clock.now = t
        return parse(raw)

    def command(self, kind, reference, **_):
        self.sent.append(kind)
        return LiveCommandAck(
            type="command_ack", protocol_version=1, session_id=SESSION, sequence=len(self.sent),
            game_epoch=reference.game_epoch, room_visit=reference.room.visit_id,
            frame_id=reference.frame_id, kind=kind, status="accepted",
        )  # fmt: skip

    def close_peer(self):
        pass

    def close(self):
        pass


def scripted_mask(frame: int) -> int:
    move = (0, LEFT, RIGHT, UP, DOWN, LEFT | UP)[(frame // 4) % 6]
    shoot = (0, S_UP, S_LEFT | S_DOWN)[(frame // 5) % 3]
    use = BIT["bomb_triggered"] if frame % 37 == 0 else 0
    return move | shoot | use


def scripted() -> list[tuple[float, dict[str, Any]]]:
    """Two runs: a fight with damage, a stale frame and a long gap, a calm cleared room with a
    pause and a menu, a new room, a death, then a second epoch that also dies."""
    stream = Stream(mask=scripted_mask)
    steps = (1, 2, 1, 3, 2, 1, 1, 2)
    stream.add(status="unavailable")
    hp = 10.0
    for i in range(40):
        hp -= 2.0 if i % 12 == 6 else 0.0
        stream.add(0.5, steps[i % 8], x=100.0 + 6 * i, velocity=(3.0, 1.0), enemies=((1, hp),))
    stream.add(0.05, 0, x=340.0, enemies=((1, hp),))  # a repeated frame is ignored
    stream.add(5.0, 2, x=340.0, enemies=((1, hp),))  # a long gap counts 2 s at most
    for i in range(18):
        stream.add(0.5, steps[i % 8], clear=True, x=340.0, y=200.0 + 8 * i, velocity=(0.0, 2.0))
    for _ in range(3):
        stream.add(4.0, 0, status="paused", clear=True, x=340.0, y=344.0)
    stream.add(1.0, status="unavailable")
    for i in range(6):
        stream.add(0.5, steps[i % 8], clear=True, x=340.0 - 9 * i, y=344.0)
    for i in range(12):
        stream.add(0.4, steps[i % 8], visit=2, room_index=85, x=200.0 + 5 * i,
                   enemies=((2, 10.0),))  # fmt: skip
    stream.add(0.4, 2, visit=2, room_index=85, dead=True, enemies=((2, 10.0),))
    stream.add(0.4, 2, visit=2, room_index=85, dead=True, enemies=((2, 10.0),))
    stream.add(2.0, status="unavailable", epoch=2)
    for i in range(25):
        stream.add(0.6, steps[i % 8], epoch=2, x=150.0 + 7 * i, y=250.0, clear=i > 12)
    stream.add(0.6, 2, epoch=2, dead=True, x=325.0, y=250.0)
    return stream.records


def live_observations(records, repeat: int) -> list[list[np.ndarray]]:
    """Each run's observations from a real live env (reset, then STILL steps until it ends)."""
    clock = Clock()
    client = ReplayClient(records, clock)
    env = make_live_env(
        client, reward_version=13, stall_seconds=STALL, clock=clock, action_repeat=repeat
    )
    runs: list[list[np.ndarray]] = []
    while True:
        try:
            obs, _ = env.reset()
        except Exhausted:
            return runs
        observations = [obs]
        while True:
            obs, _, terminated, truncated, info = env.step(STILL)
            assert "fault" not in info
            if terminated or truncated:
                assert info["outcome"] == "death"
                break
            observations.append(obs)
        runs.append(observations)


@pytest.mark.parametrize("repeat", [3, 6])
def test_observations_match_the_live_env_step_by_step(tmp_path, repeat):
    records = scripted()
    live = live_observations(records, repeat)
    demo = load(write_recording(tmp_path / "f.jsonl.gz", records), repeat=repeat)
    assert len(live) == len(demo) == 2
    stall_seen = visited_seen = False
    for live_run, sequence in zip(live, demo, strict=True):
        steps = len(sequence.actions)
        # Only the last decision can lack a label (its window runs past the death).
        assert len(live_run) - 1 <= steps <= len(live_run)
        expected = np.stack(live_run[:steps])
        assert np.array_equal(sequence.observations, expected.astype(np.float16))
        assert np.abs(sequence.observations.astype(np.float32) - expected).max() < 1e-3
        stall = expected[:, STALL_OFFSET]
        stall_seen |= bool(stall.max() > 0.2)
        visited_seen |= bool(expected[:, VISITED_OFFSET:].sum(axis=1).max() > 3)
    assert stall_seen and visited_seen
    # The second run starts with a fresh watchdog and visited grid.
    assert demo[1].observations[0, STALL_OFFSET] == 0.0
    assert demo[1].observations[0, VISITED_OFFSET:].astype(np.float32).sum() == 1.0
