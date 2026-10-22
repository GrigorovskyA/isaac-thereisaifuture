"""Combat curriculum, regression gate and append-only results log.

Everything that decides pass/fail (stage thresholds, regression tolerance) is a frozen, hashed
dataclass that must be declared before training. Policies and evaluation callables are passed in
by callers; this module never trains and never touches the test split.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from .baselines import Policy
from .encoding import OBSERVATION_SIZE
from .episodes import Scenario
from .evaluation import Metrics
from .scenarios import SCENARIO_SET_VERSION, scenarios_for

CURRICULUM_VERSION = 1


def _digest(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


@dataclass(frozen=True)
class Stage:
    name: str
    difficulties: tuple[int, ...]
    # Advance only when the validation clear-rate CI lower bound reaches this value.
    advance_min_clear_rate_lower: float
    min_valid_episodes: int = 100

    def __post_init__(self) -> None:
        if not self.name or not self.difficulties:
            raise ValueError("Stage needs a name and at least one difficulty")
        if not 0.0 < self.advance_min_clear_rate_lower <= 1.0 or self.min_valid_episodes < 1:
            raise ValueError("Invalid advancement threshold")

    def scenarios(self, split: Literal["train", "validation"]) -> tuple[Scenario, ...]:
        if split not in ("train", "validation"):
            raise ValueError("Curriculum stages expose train and validation scenarios only")
        return tuple(s for s in scenarios_for(split) if s.difficulty in self.difficulties)


@dataclass(frozen=True)
class Curriculum:
    stages: tuple[Stage, ...]
    version: int = CURRICULUM_VERSION
    scenario_set_version: str = SCENARIO_SET_VERSION

    def __post_init__(self) -> None:
        if not self.stages:
            raise ValueError("Curriculum needs stages")
        if self.scenario_set_version != SCENARIO_SET_VERSION:
            raise ValueError("Curriculum targets a different scenario set version")
        seen: set[int] = set()
        for stage in self.stages:
            if not stage.scenarios("train") or not stage.scenarios("validation"):
                raise ValueError(f"Stage {stage.name!r} has no train or validation scenarios")
            seen |= set(stage.difficulties)
        if len({s.name for s in self.stages}) != len(self.stages):
            raise ValueError("Stage names must be unique")

    def old_task_difficulties(self, stage_index: int) -> tuple[int, ...]:
        """Difficulties of all earlier stages: the set that must not regress."""
        return tuple(sorted({d for s in self.stages[:stage_index] for d in s.difficulties}))

    @property
    def hash(self) -> str:
        return _digest(asdict(self))


DEFAULT_CURRICULUM = Curriculum(
    (
        Stage("stage-1-single-enemy", (1,), 0.6),
        Stage("stage-2-few-enemies", (1, 2), 0.5),
        Stage("stage-3-crowded", (1, 2, 3), 0.4),
    )
)


def should_advance(stage: Stage, validation_metrics: Metrics, split: str = "validation") -> bool:
    """Pure decision; the test split must never steer training."""
    if split != "validation":
        raise ValueError("Advancement is decided on the validation split only")
    return (
        validation_metrics.valid >= stage.min_valid_episodes
        and validation_metrics.clear_rate_ci95[0] >= stage.advance_min_clear_rate_lower
    )


@dataclass(frozen=True)
class RegressionTolerance:
    """Fixed before training; record `hash` in the experiment plan."""

    max_clear_rate_drop: float = 0.05
    max_damage_increase_half_hearts: float = 1.0
    min_valid_episodes: int = 100

    def __post_init__(self) -> None:
        if not 0.0 <= self.max_clear_rate_drop <= 1.0 or self.max_damage_increase_half_hearts < 0:
            raise ValueError("Invalid regression tolerance")

    @property
    def hash(self) -> str:
        return _digest(asdict(self))


@dataclass(frozen=True)
class GateResult:
    passed: bool
    reasons: tuple[str, ...]
    tolerance_hash: str


def regression_gate(snapshot: Metrics, new: Metrics, tolerance: RegressionTolerance) -> GateResult:
    """Compare new-policy metrics on the OLD task set with the pre-extension snapshot."""
    reasons: list[str] = []
    if snapshot.valid < tolerance.min_valid_episodes or new.valid < tolerance.min_valid_episodes:
        reasons.append("too few valid episodes")
    # Fail unless the new CI still reaches the allowed floor: a noisy drop is not excused.
    floor = snapshot.clear_rate - tolerance.max_clear_rate_drop
    if new.clear_rate_ci95[1] < floor:
        reasons.append(f"clear rate regressed below {floor:.3f}")
    elif new.clear_rate < floor:
        reasons.append(f"clear rate point estimate {new.clear_rate:.3f} below {floor:.3f}")
    damage_limit = (
        snapshot.mean_damage_taken_half_hearts + tolerance.max_damage_increase_half_hearts
    )
    if new.mean_damage_taken_half_hearts > damage_limit:
        reasons.append("mean damage taken increased beyond tolerance")
    return GateResult(not reasons, tuple(reasons), tolerance.hash)


@dataclass(frozen=True)
class BaselineComparison:
    beats_random: bool  # CI lower bound above the random CI upper bound
    beats_scripted: bool
    clear_rate_vs_random: float
    clear_rate_vs_scripted: float


def compare_to_baselines(new: Metrics, random: Metrics, scripted: Metrics) -> BaselineComparison:
    """Same split and budget for all three; `beats_scripted` is reported, never hidden."""
    return BaselineComparison(
        beats_random=new.clear_rate_ci95[0] > random.clear_rate_ci95[1],
        beats_scripted=new.clear_rate_ci95[0] > scripted.clear_rate_ci95[1],
        clear_rate_vs_random=new.clear_rate - random.clear_rate,
        clear_rate_vs_scripted=new.clear_rate - scripted.clear_rate,
    )


class ResultsLog:
    """Append-only JSONL hash chain; every stage outcome, including failures, is retained."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def append(self, entry: dict[str, Any]) -> None:
        entries = self.read()
        prev = entries[-1]["hash"] if entries else ""
        body = {"index": len(entries), "prev": prev, "entry": entry}
        line = json.dumps({**body, "hash": _digest(body)}, sort_keys=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def read(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        rows = [json.loads(x) for x in self._path.read_text("utf-8").splitlines() if x]
        prev = ""
        for index, row in enumerate(rows):
            body = {"index": row["index"], "prev": row["prev"], "entry": row["entry"]}
            if row["index"] != index or row["prev"] != prev or row["hash"] != _digest(body):
                raise ValueError(f"Results log tampered with or truncated at entry {index}")
            prev = row["hash"]
        return rows


class OracleLeakageError(ValueError):
    pass


def check_policy_input(observation: NDArray[np.float32]) -> None:
    if observation.shape != (OBSERVATION_SIZE,) or observation.dtype != np.float32:
        raise OracleLeakageError(
            f"Policy input must be float32 ({OBSERVATION_SIZE},), got "
            f"{observation.dtype} {observation.shape}"
        )


class LeakageCheckedPolicy:
    """Wrap any policy so every act() input is verified to be exactly the encoded observation."""

    def __init__(self, inner: Policy) -> None:
        self._inner = inner
        self.name = inner.name
        self.label = inner.label

    def reset(self, seed: int) -> None:
        self._inner.reset(seed)

    def act(self, observation: NDArray[np.float32]) -> NDArray[np.int64]:
        check_policy_input(observation)
        return self._inner.act(observation)
