"""Prioritized Level Replay over run seeds (contract `level_replay: plr_v1`).

Jiang, Grefenstette and Rocktaeschel, "Prioritized Level Replay", ICML 2021 (arXiv 2010.03548). A
level is a run seed (the game's start seed string, "XXXX XXXX"). The bank keeps the seeds of runs
the agent played with a score: the mean |GAE advantage| over the trained steps of the latest run of
that seed, computed by the learner from the rollout buffer (`learner.PureRecurrentPPO`). On each New
Run the next seed is a replay with probability `replay_probability`, sampled by

    P = (1 - staleness) * P_score + staleness * P_stale,

with rank prioritization P_score ~ (1 / rank(score)) ** (1 / temperature) and P_stale ~ the runs
since the seed was last started; otherwise the run is unseeded and its seed joins the bank. The
seed is metadata, never an observation, normalizer input or recurrent state. The bank is learner
state saved per checkpoint (`level_replay.json`); evaluation never uses it.
"""

import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray

LevelReplayMode = Literal["none", "plr_v1"]
NONE: LevelReplayMode = "none"
PLR_V1: LevelReplayMode = "plr_v1"
LEVEL_REPLAY_FILE = "level_replay.json"
_FORMAT = 1
# The seed alphabet of the game: A-Z and 0-9 without I, O, U and 5 (wiki "Seeds"). The Lua mod
# validates the same pattern before it sends or dispatches a seed.
SEED_ALPHABET = "ABCDEFGHJKLMNPQRSTVWXYZ012346789"
SEED_PATTERN = r"^[A-HJ-NP-TV-Z0-46-9]{4} [A-HJ-NP-TV-Z0-46-9]{4}$"
_SEED = re.compile(SEED_PATTERN)
MAX_BANK = 100_000


class LevelReplayError(Exception):
    """Missing or corrupt seed bank file."""


def valid_seed(value: object) -> bool:
    return isinstance(value, str) and _SEED.fullmatch(value) is not None


@dataclass
class SeedEntry:
    """One seed of the bank. `score` is None until a trained step of a run with it was scored."""

    score: float | None
    last_run: int  # run counter when a run with this seed last started (staleness clock)
    added: int  # run counter when the seed joined the bank (eviction tie-break)


@dataclass
class _RunScore:
    seed: str | None
    total: float = 0.0
    steps: int = 0


class SeedBank:
    """Seed bank, PLR sampler and per-run score attribution (one env, learner state)."""

    def __init__(
        self,
        *,
        replay_probability: float = 0.5,
        temperature: float = 0.1,
        staleness: float = 0.1,
        capacity: int = 500,
        seed: int = 0,
    ) -> None:
        if not 0 <= replay_probability <= 1 or not 0 <= staleness <= 1:
            raise ValueError("Replay probability and staleness must be within 0..1")
        if temperature <= 0 or not 1 <= capacity <= MAX_BANK:
            raise ValueError(f"Temperature must be positive and capacity 1..{MAX_BANK}")
        self.replay_probability = replay_probability
        self.temperature = temperature
        self.staleness = staleness
        self.capacity = capacity
        self.seed = seed
        self.entries: dict[str, SeedEntry] = {}
        self.runs = 0  # runs started so far in the lineage
        self._scores: dict[int, _RunScore] = {}  # open runs, by run id (in memory only)
        self.current_run: int | None = None
        self.current_seed: str | None = None
        self.current_replayed: bool | None = None
        self._current_key: tuple[int, str | None] | None = None
        self.planned_seed: str | None = None  # seed asked for the next New Run, None = fresh

    def __len__(self) -> int:
        return len(self.entries)

    # --- sampling -------------------------------------------------------------------------

    def probabilities(self) -> tuple[list[str], NDArray[np.float64]]:
        """Replay distribution over the scored seeds (empty when none is scored)."""
        seeds = [seed for seed, entry in self.entries.items() if entry.score is not None]
        if not seeds:
            return [], np.zeros(0)
        scores = np.array([self.entries[seed].score for seed in seeds], dtype=np.float64)
        # Rank 1 is the highest score; ties keep the bank order (a stable sort).
        order = np.argsort(-scores, kind="stable")
        ranks = np.empty(len(seeds), dtype=np.float64)
        ranks[order] = np.arange(1, len(seeds) + 1)
        weights = (1.0 / ranks) ** (1.0 / self.temperature)
        by_score = weights / weights.sum()
        age = np.array([self.runs - self.entries[seed].last_run for seed in seeds], np.float64)
        by_age = age / age.sum() if age.sum() > 0 else np.full(len(seeds), 1.0 / len(seeds))
        return seeds, (1.0 - self.staleness) * by_score + self.staleness * by_age

    def plan_next(self) -> str | None:
        """Decide the seed of the next New Run: a replayed bank seed or None (a fresh run).

        The random stream depends only on the lineage seed and the run counter, so a resumed
        lineage makes the same decision without saving a generator state.
        """
        rng = np.random.default_rng([self.seed, self.runs])
        seeds, probabilities = self.probabilities()
        if not seeds or rng.random() >= self.replay_probability:
            self.planned_seed = None
        else:
            self.planned_seed = seeds[int(rng.choice(len(seeds), p=probabilities))]
        return self.planned_seed

    # --- runs -----------------------------------------------------------------------------

    def begin_run(self, seed: str | None, epoch: int) -> bool:
        """Note the run seen at an episode start; True when it is a new run.

        A run is new when its (game epoch, seed) differs from the current one, so a reconnect or
        a fault reset inside the same run changes nothing. A run counts as replayed when its seed
        was in the bank already (also when the game repeated a seed unasked); a new valid seed
        joins the bank. The next New Run is planned here.
        """
        key = (epoch, seed if valid_seed(seed) else None)
        if key == self._current_key:
            return False
        self._current_key = key
        self.runs += 1
        run = self.runs
        known = key[1] is not None and key[1] in self.entries
        if key[1] is not None:
            if known:
                self.entries[key[1]].last_run = run
            else:
                self._add(key[1], run)
        self.current_run, self.current_seed = run, key[1]
        self.current_replayed = known
        # Runs that can get no more steps are dropped; the learner scores the rest per rollout.
        self._scores[run] = _RunScore(key[1])
        self.plan_next()
        return True

    def _add(self, seed: str, run: int) -> None:
        while len(self.entries) >= self.capacity:
            self._evict()
        self.entries[seed] = SeedEntry(score=None, last_run=run, added=run)

    def _evict(self) -> None:
        """Drop the lowest-scored seed, the oldest first on ties; unscored seeds go last."""

        def key(item: tuple[str, SeedEntry]) -> tuple[int, float, int, int]:
            entry = item[1]
            unscored = entry.score is None
            return (int(unscored), 0.0 if unscored else float(entry.score or 0.0),
                    entry.last_run, entry.added)  # fmt: skip

        victim = min(self.entries.items(), key=key)[0]
        del self.entries[victim]

    def facts(self) -> dict[str, object]:
        """Episode metrics (`run_seed`, `seed_replayed`); never a policy input."""
        return {
            "run_seed": self.current_seed,
            "seed_replayed": None if self.current_replayed is None else int(self.current_replayed),
        }

    # --- scores ---------------------------------------------------------------------------

    def score_rollout(self, runs: Sequence[int | None], advantages: NDArray[np.floating]) -> int:
        """Add one rollout's |GAE advantage| to the runs its steps belong to; return steps scored.

        `runs[i]` is the run id of buffer step i (None: unattributed, for example a fault step).
        A run spanning rollouts accumulates; its seed's score is the running mean over all its
        trained steps. Runs that are not in this rollout and not current are closed.
        """
        values = np.abs(np.asarray(advantages, dtype=np.float64).reshape(-1))
        if len(values) != len(runs):
            raise ValueError("One run id per rollout step is required")
        scored = 0
        for run in sorted({run for run in runs if run is not None}):
            record = self._scores.get(run)
            if record is None:
                continue  # a run from before a resume: its first steps are not attributed
            mask = np.fromiter((item == run for item in runs), dtype=bool, count=len(runs))
            record.total += float(values[mask].sum())
            record.steps += int(mask.sum())
            scored += int(mask.sum())
            entry = self.entries.get(record.seed) if record.seed is not None else None
            if entry is not None and record.steps > 0 and math.isfinite(record.total):
                entry.score = record.total / record.steps
        keep = {run for run in runs if run is not None} | {self.current_run}
        self._scores = {run: rec for run, rec in self._scores.items() if run in keep}
        return scored

    # --- persistence ----------------------------------------------------------------------

    def save(self, path: Path) -> None:
        data = {
            "format": _FORMAT,
            "runs": self.runs,
            "entries": [
                [seed, entry.score, entry.last_run, entry.added]
                for seed, entry in self.entries.items()
            ],
        }
        path.write_text(json.dumps(data, separators=(",", ":")), "utf-8")

    def load(self, path: Path) -> None:
        """Replace the bank with the file's content; a smaller capacity evicts down to it."""
        try:
            data = json.loads(path.read_text("utf-8"))
            if not isinstance(data, dict) or data.get("format") != _FORMAT:
                raise ValueError("unsupported format")
            runs = data["runs"]
            rows = data["entries"]
            if type(runs) is not int or runs < 0 or not isinstance(rows, list):
                raise ValueError("invalid header")
            if len(rows) > MAX_BANK:
                raise ValueError("too many seeds")
            entries: dict[str, SeedEntry] = {}
            for row in rows:
                seed, score, last_run, added = row
                valid_score = score is None or (
                    isinstance(score, int | float) and math.isfinite(score) and score >= 0
                )
                if (
                    not valid_seed(seed)
                    or seed in entries
                    or not valid_score
                    or type(last_run) is not int
                    or type(added) is not int
                    or not 0 <= added <= last_run <= runs
                ):
                    raise ValueError(f"invalid seed entry {row!r}")
                entries[seed] = SeedEntry(None if score is None else float(score), last_run, added)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise LevelReplayError(f"Cannot read seed bank {path}: {error}") from error
        self.entries, self.runs = entries, runs
        self._scores, self._current_key = {}, None
        self.current_run = self.current_seed = self.current_replayed = None
        while len(self.entries) > self.capacity:
            self._evict()
