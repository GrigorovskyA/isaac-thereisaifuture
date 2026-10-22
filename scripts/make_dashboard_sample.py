"""SYNTHETIC dashboard sample for visual review. Not real training data.

Writes ~3000 invented episodes and ~1000 invented PPO updates (metrics/train.csv) with
slowly improving noisy metrics, a fake latest checkpoint and a fake supervisor status
under `reports/local/dashboard-sample`, then:

    python -m isaac_threrisaifuture.dashboard --run-root reports/local/dashboard-sample
"""

import argparse
import csv
import json
import math
import random
import shutil
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from isaac_threrisaifuture.checkpoints import save_checkpoint
from isaac_threrisaifuture.episode_metrics import FIELDS, PICKUPS
from isaac_threrisaifuture.rewards import REWARD_V4_COLUMNS
from isaac_threrisaifuture.training_metrics import TRAIN_FIELDS


class _Artifact:
    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(b"synthetic")


def _shares(rng: random.Random, weights: list[float]) -> list[float]:
    noisy = [max(1e-4, w * rng.uniform(0.9, 1.1)) for w in weights]
    total = sum(noisy)
    return [v / total for v in noisy]


def write_train(root: Path, updates: int, rng: random.Random, end: datetime) -> None:
    start = end - timedelta(seconds=40 * updates)
    with (root / "metrics" / "train.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRAIN_FIELDS, lineterminator="\n")
        writer.writeheader()
        for i in range(updates):
            progress = i / max(1, updates - 1)
            bomb = 0.25 - 0.22 * progress**0.6
            move = _shares(rng, [0.3 - 0.1 * progress, 0.17, 0.17, 0.18, 0.18 + 0.1 * progress])
            shoot = _shares(rng, [0.4 - 0.2 * progress, 0.15, 0.15, 0.15, 0.15 + 0.2 * progress])
            use_rest = _shares(rng, [0.8, 0.12 - 0.05 * progress, 0.05, 0.03])
            use = [use_rest[0] * (1 - bomb) / max(use_rest[0] + use_rest[2] + use_rest[3], 1e-9)]
            rest = 1 - bomb - use[0]
            use += [bomb, rest * 0.6, rest * 0.4]
            row: dict[str, object] = {
                "wall_time": (start + timedelta(seconds=40 * i)).isoformat(timespec="seconds"),
                "timesteps": 4096 * (i + 1),
                "rollout_index": i + 1,
                "learning_rate": 3e-4,
                "entropy_loss": -(3.2 - 1.1 * (1 - math.exp(-3 * progress)) + rng.gauss(0, 0.03)),
                "policy_gradient_loss": rng.gauss(-0.004, 0.002),
                "value_loss": max(0.01, 40 * math.exp(-2.5 * progress) + 8 + rng.gauss(0, 2)),
                "loss": rng.gauss(20, 3),
                "approx_kl": abs(rng.gauss(0.008, 0.003)),
                "clip_fraction": max(0.0, rng.gauss(0.09 - 0.03 * progress, 0.02)),
                "explained_variance": min(
                    0.95, 0.6 * (1 - math.exp(-4 * progress)) + rng.gauss(0, 0.05)
                ),
                "n_updates": 10 * (i + 1),
            }
            for head, values in (("move", move), ("shoot", shoot), ("use", use)):
                names = (
                    ("none", "left", "right", "up", "down")
                    if head != "use"
                    else ("none", "bomb", "active", "pillcard")
                )
                for name, share in zip(names, values, strict=True):
                    row[f"{head}_{name}"] = round(share, 5)
            writer.writerow(row)


def build(root: Path, episodes: int, seed: int, updates: int = 1000) -> None:
    rng = random.Random(seed)
    if root.exists():
        shutil.rmtree(root)
    (root / "metrics").mkdir(parents=True)
    clock = datetime.now(UTC).replace(microsecond=0) - timedelta(minutes=2)
    clock -= timedelta(seconds=75 * episodes)
    train_end = clock + timedelta(seconds=75 * episodes)
    total_steps = 0
    with (root / "metrics" / "episodes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for i in range(episodes):
            skill = 1 - 1 / (1 + i / 800)  # 0 -> 1, slowly
            stall = rng.random() < 0.28 * (1 - 0.6 * skill)
            steps = int(rng.gauss(900 + 700 * skill, 250))
            steps = max(120, steps)
            total_steps += steps
            cleared = max(0, round(rng.gauss(1 + 5 * skill, 1.2)))
            visited = cleared + max(0, round(rng.gauss(2 + 2 * skill, 1)))
            stage = 1 + (rng.random() < 0.05 + 0.5 * skill) + (rng.random() < 0.4 * skill**2)
            damage = min(1.5, max(0, rng.gauss(0.2 + 0.9 * skill, 0.18)))
            exit_step = None if rng.random() < 0.7 - 0.55 * skill else rng.randint(60, 600)
            row: dict[str, object] = {
                "use_bomb": max(0, round(rng.gauss(3.5 * (1 - 0.88 * skill), 1.5))),
                "use_active": rng.randint(0, 1),
                "use_pillcard": rng.randint(0, 1) if rng.random() < 0.3 else 0,
                "half_hearts_lost": max(0, round(rng.gauss(5 - 2 * skill, 1.5))),
                "steps_to_first_exit": exit_step if exit_step is not None else "",
                "steps_to_first_damage": rng.randint(30, 500) if rng.random() < 0.8 else "",
                "episode_id": f"ep-{i:06d}",
                "scenario_id": "pure-v1",
                "timesteps": steps,
                "game_updates": steps * 4,
                "outcome": "truncated" if stall else "terminated",
                "end_reason": "stall" if stall else "death",
                "truncation_reason": "stall" if stall else "",
                "damage_dealt_fraction": round(damage, 3),
                "rooms_visited": visited,
                "rooms_cleared": cleared,
                "max_stage": int(stage),
                "wall_time": clock.isoformat(timespec="seconds"),
            }
            for name in PICKUPS:
                row[f"pickups_{name}"] = max(0, round(rng.gauss(0.5 + 2 * skill, 1)))
            total = 0.0
            for name in REWARD_V4_COLUMNS:
                part = round(rng.gauss(0.5 * skill, 0.3), 3)
                if name == "stall":
                    part = -5.0 if stall else 0.0
                elif name in ("damage_taken", "death", "time"):
                    part = -abs(part) - 0.2
                row[f"col_{name}"] = part
                total += part
            row["return"] = round(total, 3)
            writer.writerow(row)
            clock += timedelta(seconds=rng.randint(30, 120))
    write_train(root, updates, rng, train_end)
    checkpoints = root / "seed-1" / "checkpoints"
    save_checkpoint(
        checkpoints,
        model=_Artifact(),
        vec_normalize=_Artifact(),
        algorithm="RecurrentPPO",
        cfg_hash="0" * 64,
        seed=1,
        timesteps=total_steps,
        parent_checkpoint_id=None,
        rng_state={},
        reward_contract="pure-v4",
        hyperparameters={"learning_rate": 3e-4, "n_steps": 2048, "synthetic": True},
    )
    session = root / "supervisor" / "session-synthetic-0001"
    session.mkdir(parents=True)
    status = {"state": "training", "updated_at": time.time(), "reason": None, "fault": None}
    (session / "status.json").write_text(json.dumps(status), "utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("reports/local/dashboard-sample"))
    parser.add_argument("--episodes", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    build(args.out, args.episodes, args.seed)
    print(f"Synthetic sample written to {args.out}")


if __name__ == "__main__":
    main()
