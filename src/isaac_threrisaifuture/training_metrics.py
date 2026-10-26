"""Per-update training statistics: one row per optimizer cycle in `metrics/train.csv`.

SB3 logs the train statistics at the end of `train()` and clears them at the next dump,
which comes after the next rollout is collected. So the values are read at the start of
the next rollout (or at the end of training), and pair with the actions captured at the
end of the rollout that was just optimized. A write failure is logged once and never
stops training.
"""

import csv
import logging
import os
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback

from .episodes import DIRECTIONS, USES

LOGGER = logging.getLogger(__name__)
STATS = (
    "learning_rate",
    "entropy_loss",
    "policy_gradient_loss",
    "value_loss",
    "loss",
    "approx_kl",
    "clip_fraction",
    "explained_variance",
    "n_updates",
)
HEADS = (("move", DIRECTIONS), ("shoot", DIRECTIONS), ("use", USES))
SHARES = tuple(f"{head}_{name}" for head, names in HEADS for name in names)
# rollout_seconds: wall clock of the rollout. update_seconds: the pause between the previous
# rollout end and this rollout start (optimizer, checkpoint and any idle wait); empty for the first.
# game_wait_seconds / command_seconds: time inside the bridge snapshot wait and the command send
# of a live backend during the rollout; snapshots_per_step: snapshots taken per env step. All
# three are empty for backends without timing counters.
BRIDGE_TIMING = ("game_wait_seconds", "command_seconds", "snapshots_per_step")
TIMING = ("rollout_seconds", "update_seconds", *BRIDGE_TIMING)
TRAIN_FIELDS = ("wall_time", "timesteps", "rollout_index", *TIMING, *STATS, *SHARES)
# Header of files written before the bridge timing columns; such files are rewritten once with
# the full header, old rows keeping empty timing cells.
LEGACY_FIELDS = tuple(name for name in TRAIN_FIELDS if name not in BRIDGE_TIMING)


def action_shares(actions: Any) -> dict[str, float]:
    """Share of each choice per head over a rollout buffer of shape (steps, envs, heads)."""
    flat = np.asarray(actions).reshape(-1, len(HEADS))
    shares: dict[str, float] = {}
    for column, (head, names) in enumerate(HEADS):
        counts = np.bincount(flat[:, column].astype(np.int64), minlength=len(names))
        total = max(int(counts[: len(names)].sum()), 1)
        for index, name in enumerate(names):
            shares[f"{head}_{name}"] = float(counts[index]) / total
    return shares


class TrainMetricsCallback(BaseCallback):
    def __init__(self, path: Path, clock: Callable[[], float] = time.monotonic) -> None:
        super().__init__()
        self.path = path
        self._clock = clock
        self._rollout_start: float | None = None
        self._last_end: float | None = None
        self._update_seconds: float | None = None
        self._pending: dict[str, Any] | None = None
        self._failed = False
        self._index = 0
        try:
            if path.exists() and path.stat().st_size > 0:
                with path.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.reader(handle))
                if rows[0] == list(LEGACY_FIELDS):
                    self._upgrade(rows)
                elif rows[0] != list(TRAIN_FIELDS):
                    raise ValueError(f"Existing metrics file has a different header: {path}")
                self._index = len(rows) - 1
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                self._append({name: name for name in TRAIN_FIELDS})
        except Exception as error:  # metrics never stop training
            self._fail(error)

    def _on_step(self) -> bool:
        return True

    def _on_rollout_start(self) -> None:
        self._flush()  # the previous update has finished and its values are still in the logger
        now = self._clock()
        self._rollout_start = now
        self._update_seconds = None if self._last_end is None else max(now - self._last_end, 0.0)
        self._bridge_timing()  # drop anything counted outside a rollout

    def _bridge_timing(self) -> dict[str, float | None]:
        """Read and reset the live backend's timing counters; empty values without them."""
        try:
            env: Any = self.training_env.get_attr("unwrapped")[0]
            counters = env.controller.backend.timing_counters()
            steps = max(float(counters["steps"]), 1.0)
            return {
                "game_wait_seconds": float(counters["wait_seconds"]),
                "command_seconds": float(counters["command_seconds"]),
                "snapshots_per_step": float(counters["snapshots"]) / steps,
            }
        except Exception:  # no env, or a backend without counters (sim, fakes)
            return dict.fromkeys(BRIDGE_TIMING)

    def _on_rollout_end(self) -> None:
        now = self._clock()
        started = self._rollout_start
        self._last_end = now
        try:
            buffer: Any = self.model.rollout_buffer  # type: ignore[attr-defined]
            self._pending = {
                "rollout_seconds": None if started is None else max(now - started, 0.0),
                "update_seconds": self._update_seconds,
                **self._bridge_timing(),
                "timesteps": int(self.model.num_timesteps),
                "rollout_index": self._index,
                **action_shares(buffer.actions),
            }
        except Exception as error:
            self._pending = None
            self._fail(error)

    def _on_training_end(self) -> None:
        self._flush()

    def _flush(self) -> None:
        row, self._pending = self._pending, None
        if row is None:
            return
        try:
            logged = self.model.logger.name_to_value
            for name in STATS:
                value = logged.get(f"train/{name}")
                row[name] = None if value is None else float(value)
            row["wall_time"] = datetime.now(UTC).isoformat(timespec="seconds")
            self._append(row)
            self._index += 1
        except Exception as error:
            self._fail(error)

    def _upgrade(self, rows: list[list[str]]) -> None:
        """Rewrite an old-header file with the full header; old rows get empty timing cells."""
        temporary = self.path.with_name(self.path.name + ".upgrade")
        with temporary.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=TRAIN_FIELDS, restval="", lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(dict(zip(LEGACY_FIELDS, row, strict=True)) for row in rows[1:])
        os.replace(temporary, self.path)

    def _append(self, row: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=TRAIN_FIELDS,
                restval="",
                extrasaction="ignore",
                lineterminator="\n",
            )
            writer.writerow(row)
            handle.flush()

    def _fail(self, error: Exception) -> None:
        if not self._failed:
            self._failed = True
            LOGGER.error("Training metrics disabled for this run: %s", error)
