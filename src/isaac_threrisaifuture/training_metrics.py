"""Per-update training statistics: one row per optimizer cycle in `metrics/train.csv`.

SB3 logs the train statistics at the end of `train()` and clears them at the next dump,
which comes after the next rollout is collected. So the values are read at the start of
the next rollout (or at the end of training), and pair with the actions captured at the
end of the rollout that was just optimized. A write failure is logged once and never
stops training.
"""

import csv
import logging
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
TRAIN_FIELDS = ("wall_time", "timesteps", "rollout_index", *STATS, *SHARES)


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
    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self._pending: dict[str, Any] | None = None
        self._failed = False
        self._index = 0
        try:
            if path.exists() and path.stat().st_size > 0:
                with path.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.reader(handle))
                if rows[0] != list(TRAIN_FIELDS):
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

    def _on_rollout_end(self) -> None:
        try:
            buffer: Any = self.model.rollout_buffer  # type: ignore[attr-defined]
            self._pending = {
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

    def _append(self, row: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=TRAIN_FIELDS, restval="", lineterminator="\n"
            )
            writer.writerow(row)
            handle.flush()

    def _fail(self, error: Exception) -> None:
        if not self._failed:
            self._failed = True
            LOGGER.error("Training metrics disabled for this run: %s", error)
