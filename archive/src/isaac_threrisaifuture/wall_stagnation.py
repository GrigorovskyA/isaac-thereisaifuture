"""Offline replay of paired learning traces: reproduce a baseline and audit stagnation.

Read-only and bounded. Oracle fields are report labels only: nothing produced here feeds
a policy, normalizer, recurrent state or reward. Frozen-policy probabilities are computed
on recorded encoder outputs and are model diagnostics, not gameplay evidence.
"""

import argparse
import hashlib
import json
import math
from collections import Counter
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from . import firing_progress_v4 as v4
from .encoding import CAPACITY, PLAYER_FEATURES, SLOT_FEATURES
from .episodes import DIRECTIONS
from .exposed_start import phase_metrics, sample_of
from .firing_progress_v5 import FiringProgressV5
from .firing_progress_v5 import potential as v5_potential
from .live import LiveSnapshot
from .policy_geometry import GEOMETRY_OBSERVATION_SIZE, encode_geometry

MAX_RECORDS = 65_536
MAX_LINE_BYTES = 1 << 20
MAX_EVENT_LINES = 1_000_000
MAX_MANIFEST_FILES = 256
WALL_RADIUS = 20.0
ENCODING_TOLERANCE = 1e-6
TRACE_STAGE = "encoder_before_vecnormalize"
MASK_OFFSET = GEOMETRY_OBSERVATION_SIZE - 74 + 2  # (known, blocked) per left/right/up/down


class ReplayError(ValueError):
    """Rejected or inconsistent offline evidence; never silently repaired."""


@dataclass(frozen=True)
class TracePair:
    record_id: int
    move: int
    shoot: int
    observation: NDArray[np.float32]  # encoder output of `before`, as recorded
    after_observation: NDArray[np.float32]
    before: LiveSnapshot
    after: LiveSnapshot


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_manifest(root: Path) -> dict[str, Any]:
    """Check every listed file's size and SHA256; raise on any difference."""
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, dict) or not 0 < len(files) <= MAX_MANIFEST_FILES:
        raise ReplayError("Manifest must list between 1 and 256 files")
    for name, expected in files.items():
        path = (root / name).resolve()
        if root.resolve() not in path.parents or not path.is_file():
            raise ReplayError(f"Manifest file missing or outside bundle: {name}")
        if path.stat().st_size != expected["bytes"] or _sha256(path) != expected["sha256"]:
            raise ReplayError(f"Manifest mismatch: {name}")
    return {k: v for k, v in manifest.items() if k != "files"} | {"verified_files": len(files)}


def _lines(path: Path, limit: int) -> Iterator[dict[str, Any]]:
    with path.open("rb") as handle:
        for number, raw in enumerate(handle, 1):
            if number > limit:
                raise ReplayError(f"{path.name} exceeds {limit} records")
            if len(raw) > MAX_LINE_BYTES:
                raise ReplayError(f"{path.name}:{number} exceeds the line byte cap")
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ReplayError(f"{path.name}:{number} is not an object")
            yield value


def _observation(side: dict[str, Any], record_id: int) -> NDArray[np.float32]:
    if side.get("observation_stage") != TRACE_STAGE or side.get("observation_schema") != 2:
        raise ReplayError(f"Record {record_id} is not a schema-2 encoder output")
    vector = np.asarray(side["observation"], dtype=np.float32)
    if vector.shape != (GEOMETRY_OBSERVATION_SIZE,) or not np.isfinite(vector).all():
        raise ReplayError(f"Record {record_id} observation is malformed")
    return vector


def read_pairs(policy: Path, oracle: Path, max_records: int = MAX_RECORDS) -> list[TracePair]:
    """Pair policy/oracle streams by strictly increasing, identical record IDs."""
    pairs: list[TracePair] = []
    streams = zip(_lines(policy, max_records), _lines(oracle, max_records), strict=True)
    for p, o in streams:
        record_id = p.get("record_id")
        if type(record_id) is not int or record_id != o.get("record_id"):
            raise ReplayError(f"Unpaired record after {len(pairs)} pairs")
        if pairs and record_id <= pairs[-1].record_id:
            raise ReplayError(f"Record {record_id} is not strictly increasing")
        before = LiveSnapshot.model_validate(o["before"])
        after = LiveSnapshot.model_validate(o["after"])
        for side, snap in (("before", before), ("after", after)):
            if (p[side]["session_id"], p[side]["frame_id"]) != (snap.session_id, snap.frame_id):
                raise ReplayError(f"Record {record_id} {side} identity differs across streams")
        action = p.get("selected_action")
        if (
            not isinstance(action, list)
            or len(action) != 2
            or not all(type(a) is int and 0 <= a < len(DIRECTIONS) for a in action)
        ):
            raise ReplayError(f"Record {record_id} has no valid selected action")
        pairs.append(
            TracePair(
                record_id,
                action[0],
                action[1],
                _observation(p["before"], record_id),
                _observation(p["after"], record_id),
                before,
                after,
            )
        )
    return pairs


def logged_bonuses(events: Path) -> dict[int, float]:
    """Recorded firing_position_reward bonuses keyed by endpoint frame."""
    result: dict[int, float] = {}
    for event in _lines(events, MAX_EVENT_LINES):
        if event.get("event") == "firing_position_reward":
            frame = event["data"]["frame_id"]
            if frame in result:
                raise ReplayError(f"Duplicate logged firing bonus for frame {frame}")
            result[frame] = float(event["data"]["bonus"])
    return result


def _target(snap: LiveSnapshot) -> int | None:
    firing = snap.oracle.firing if snap.oracle else None
    return firing.target_id if firing else None


def _potentials(snap: LiveSnapshot) -> tuple[float | None, float | None]:
    oracle, frame = snap.oracle, snap.entity_frame
    if oracle is None or oracle.firing is None or frame is None or oracle.navigation is None:
        return None, None
    grid = oracle.navigation.grid
    if grid is None:
        return None, None
    position = frame.player_position
    return (
        v4.potential(grid, oracle.firing, position),
        v5_potential(grid, oracle.firing, position),
    )


def replay(pairs: Sequence[TracePair], logged: dict[int, float] | None) -> list[dict[str, Any]]:
    """Recompute live-firing-v5 shaping per record; a broken chain marks a refresh."""
    progress = FiringProgressV5()
    rows: list[dict[str, Any]] = []
    segment = 0
    for pair in pairs:
        b, a = pair.before, pair.after
        if progress._last != (b.session_id, b.game_epoch, b.frame_id):
            if progress._last is not None:
                segment += 1
            progress.begin(b)
        bonus = progress.transition(b, a)
        assert b.entity_frame is not None and a.entity_frame is not None
        start, end = b.entity_frame.player_position, a.entity_frame.player_position
        geometry = b.combat_geometry
        encoded = (
            encode_geometry(a.entity_frame, a.combat_geometry)
            if a.combat_geometry is not None
            else None
        )
        phi4, phi5 = _potentials(a)
        firing = a.oracle.firing if a.oracle else None
        support = firing.boundary_support if firing else None
        target = _target(a)
        key = next((k for k in progress._debt if k[-1] == target), None)
        rows.append(
            {
                "record_id": pair.record_id,
                "segment": segment,
                "frame_id": a.frame_id,
                "target_id": target,
                "move": DIRECTIONS[pair.move],
                "shoot": DIRECTIONS[pair.shoot],
                "x": end.x,
                "y": end.y,
                "dx": end.x - start.x,
                "dy": end.y - start.y,
                "movement_clear_before": list(geometry.movement) if geometry else None,
                "target_line_clear": next(
                    (
                        e.clear
                        for e in (a.combat_geometry.enemies if a.combat_geometry else ())
                        if e.entity_id == target
                    ),
                    None,
                ),
                "phi_v4": phi4,
                "phi_v5": phi5,
                "support_patch": support.patch if support else None,
                "support_clear": support.clear if support else None,
                "bonus": bonus,
                "logged_bonus": None if logged is None else logged.get(a.frame_id or -1),
                "target_debt": progress._debt.get(key, 0.0) if key else 0.0,
                "room_debt": sum(progress._room_debt.values()),
                "encoding_matches": encoded is not None
                and bool(
                    np.allclose(encoded, pair.after_observation, rtol=0, atol=ENCODING_TOLERANCE)
                ),
            }
        )
    return rows


def _target_events(pairs: Sequence[TracePair]) -> dict[str, Any]:
    hp_drops, last_seen, switches = [], {}, []
    for pair in pairs:
        assert pair.before.oracle is not None and pair.after.oracle is not None
        before = {e.entity_id: e.hp for e in pair.before.oracle.enemies}
        for enemy in pair.after.oracle.enemies:
            last_seen[enemy.entity_id] = (pair.record_id, enemy.hp)
            if enemy.entity_id in before and enemy.hp < before[enemy.entity_id]:
                hp_drops.append(
                    [pair.record_id, enemy.entity_id, before[enemy.entity_id], enemy.hp]
                )
        if _target(pair.before) != _target(pair.after):
            switches.append([pair.record_id, _target(pair.before), _target(pair.after)])
    return {
        "enemy_hp_drops": hp_drops,
        "last_listed": {str(k): list(v) for k, v in sorted(last_seen.items())},
        "target_switches": switches,
    }


def _actions(rows: Sequence[dict[str, Any]], target: int | None) -> dict[str, Any]:
    picked = [r for r in rows if r["target_id"] == target]
    table: dict[str, dict[str, Any]] = {}
    for name in DIRECTIONS:
        subset = [r for r in picked if r["move"] == name]
        if not subset:
            continue
        side = DIRECTIONS.index(name) - 1
        blocked = sum(
            1
            for r in subset
            if 0 <= side < 4
            and r["movement_clear_before"] is not None
            and r["movement_clear_before"][side] is False
        )
        table[name] = {
            "count": len(subset),
            "mean_dx": sum(r["dx"] for r in subset) / len(subset),
            "mean_dy": sum(r["dy"] for r in subset) / len(subset),
            "displaced_over_0_5": sum(math.hypot(r["dx"], r["dy"]) > 0.5 for r in subset),
            "probe_blocked_before": blocked,
        }
    return {
        "records": len(picked),
        "move": table,
        "shoot": dict(Counter(r["shoot"] for r in picked)),
        "max_x": max((r["x"] for r in picked), default=None),
    }


def _shaping(rows: Sequence[dict[str, Any]], target: int | None) -> dict[str, Any]:
    picked = [r for r in rows if r["target_id"] == target]
    phi = [r["phi_v5"] for r in picked if r["phi_v5"] is not None]
    return {
        "records": len(picked),
        "positive": sum(r["bonus"] for r in picked if r["bonus"] > 0),
        "negative": sum(r["bonus"] for r in picked if r["bonus"] < 0),
        "nonzero": sum(r["bonus"] != 0 for r in picked),
        "phi_v5_unknown": len(picked) - len(phi),
        "phi_v5_range": [min(phi), max(phi)] if phi else None,
        "phi_v4_unknown": sum(r["phi_v4"] is None for r in picked),
    }


def summarize(
    pairs: Sequence[TracePair],
    rows: Sequence[dict[str, Any]],
    *,
    wall: tuple[float, float],
) -> dict[str, Any]:
    if not pairs:
        raise ReplayError("No paired records")
    samples = [sample_of(pairs[0].before), *(sample_of(p.after) for p in pairs)]
    if any(s is None for s in samples):
        raise ReplayError("A paired endpoint lacks a reportable sample")
    learning = phase_metrics("learning_trace_endpoints", [s for s in samples if s is not None])
    for key in ("start", "end"):
        learning.pop(key)
    targets = sorted({r["target_id"] for r in rows}, key=lambda t: (t is None, t))
    near = sum(math.hypot(r["x"] - wall[0], r["y"] - wall[1]) <= WALL_RADIUS for r in rows)
    logged = [r for r in rows if r["logged_bonus"] is not None]
    return {
        "records": len(rows),
        "record_ids": [rows[0]["record_id"], rows[-1]["record_id"]],
        "frames": [pairs[0].before.frame_id, pairs[-1].after.frame_id],
        "segments": rows[-1]["segment"] + 1,
        "segment_first_records": [
            r["record_id"]
            for i, r in enumerate(rows)
            if i == 0 or r["segment"] != rows[i - 1]["segment"]
        ],
        "learning_metrics": learning,
        "near_wall": {"point": list(wall), "radius": WALL_RADIUS, "endpoints": near},
        "targets": _target_events(pairs),
        "actions_by_target": {str(t): _actions(rows, t) for t in targets},
        "shaping_by_target": {str(t): _shaping(rows, t) for t in targets},
        "shaping_replay": {
            "compared": len(logged),
            "missing_log": len(rows) - len(logged),
            "mismatches": sum(abs(r["bonus"] - r["logged_bonus"]) > 1e-12 for r in logged),
        },
        "encoding_matches": sum(r["encoding_matches"] for r in rows),
        "final_room_debt": rows[-1]["room_debt"],
    }


def _enemy_x_indices() -> list[int]:
    base = PLAYER_FEATURES  # enemy slots come first in ENTITY_KINDS order
    return [base + slot * SLOT_FEATURES + 1 for slot in range(CAPACITY["enemy"])]


def probe_inputs(observations: NDArray[np.float32], start: int) -> dict[str, NDArray[np.float32]]:
    """Counterfactual model inputs from `start` on; they are not game states."""
    mirrored = observations.copy()
    mirrored[start:, _enemy_x_indices()] *= -1
    unknown_mask = observations.copy()
    unknown_mask[start:, MASK_OFFSET : MASK_OFFSET + 8] = 0
    return {"recorded": observations, "mirror_enemy_x": mirrored, "movement_unknown": unknown_mask}


def policy_probabilities(
    directory: Path, config_hash: str, seed: int, observations: NDArray[np.float32]
) -> tuple[dict[str, Any], NDArray[np.float64]]:
    """Per-record move/shoot probabilities with recurrent state carried from record 1."""
    import torch
    from sb3_contrib.common.recurrent.type_aliases import RNNStates

    from .checkpoint_policy import CheckpointPolicy

    frozen = CheckpointPolicy(directory, expected_config_hash=config_hash, expected_seed=seed)
    policy = frozen._model.policy
    normalized = frozen._normalizer.normalize_obs(observations)
    shape = policy.lstm_hidden_state_shape
    zeros = (torch.zeros(shape), torch.zeros(shape))
    state = RNNStates(zeros, zeros)
    out = np.zeros((len(normalized), 10))
    with torch.no_grad():
        for index, row in enumerate(normalized):
            obs = torch.as_tensor(row[None, :])
            start = torch.tensor([float(index == 0)])
            distribution, _ = policy.get_distribution(obs, state.pi, start)
            _, _, _, state = policy.forward(obs, state, start, deterministic=True)
            out[index] = np.concatenate([d.probs[0].numpy() for d in distribution.distribution])
    frozen.verify_unchanged()
    return frozen.identity.to_dict(), out


def _probability_summary(probs: NDArray[np.float64], start: int) -> dict[str, Any]:
    window = probs[start:]
    move = window[:, :5]
    return {
        "records": len(window),
        "mean_move": dict(zip(DIRECTIONS, move.mean(0).round(4).tolist(), strict=True)),
        "mean_shoot": dict(zip(DIRECTIONS, window[:, 5:].mean(0).round(4).tolist(), strict=True)),
        "argmax_move": dict(
            zip(DIRECTIONS, np.bincount(move.argmax(1), minlength=5).tolist(), strict=True)
        ),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True, help="Extracted evidence root")
    parser.add_argument("--output", type=Path, required=True, help="Absent or empty directory")
    parser.add_argument("--wall", type=float, nargs=2, default=(70.0, 209.35))
    parser.add_argument("--max-records", type=int, default=MAX_RECORDS)
    parser.add_argument("--checkpoint", type=Path, action="append", default=[])
    parser.add_argument("--config-hash")
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    if args.checkpoint and (args.config_hash is None or args.seed is None):
        parser.error("--checkpoint needs --config-hash and --seed")
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("--output must be absent or empty; evidence is never overwritten")
    manifest = verify_manifest(args.bundle)
    pairs = read_pairs(
        args.bundle / "traces/learning-policy.jsonl",
        args.bundle / "traces/learning-oracle.jsonl",
        args.max_records,
    )
    rows = replay(pairs, logged_bonuses(args.bundle / "run/live-events.jsonl"))
    summary: dict[str, Any] = {
        "manifest": manifest,
        **summarize(pairs, rows, wall=tuple(args.wall)),
    }
    phases = json.loads((args.bundle / "run/phases.json").read_text(encoding="utf-8"))
    keep = ("phase", "status", "decisions", "commands", "enemy_hp_loss_lower_bound",
            "half_hearts_lost", "clears", "deaths", "stagnation_windows_10s",
            "clear_line_exposure", "checkpoint", "samples")  # fmt: skip
    summary["published_phases"] = [
        {k: p[k] for k in keep if k in p} for p in phases.get("phases", [])
    ]
    switch = summary["targets"]["target_switches"]
    start = (
        next((i for i, p in enumerate(pairs) if p.record_id == switch[-1][0]), 0) if switch else 0
    )
    observations = np.stack([p.observation for p in pairs])
    audits = []
    for directory in args.checkpoint:
        audit: dict[str, Any] = {"from_record": pairs[start].record_id, "probes": {}}
        for name, inputs in probe_inputs(observations, start).items():
            identity, probs = policy_probabilities(directory, args.config_hash, args.seed, inputs)
            audit["identity"] = identity
            audit["probes"][name] = _probability_summary(probs, start)
        audits.append(audit)
    summary["frozen_policy_audit"] = audits or "not_run: no checkpoint supplied"
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "rows.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: summary[k] for k in ("records", "segments", "shaping_replay")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
