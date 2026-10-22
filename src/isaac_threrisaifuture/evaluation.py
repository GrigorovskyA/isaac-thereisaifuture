"""Equal-budget policy evaluation with a JSON-serializable report.

Infrastructure faults are counted separately: they are neither deaths nor clears and are
excluded from the clear-rate denominator, so a flaky transport cannot flatter or punish a policy.
An `unknown` outcome (terminal evidence not covered by the backend) is also kept out of the
death/clear/timeout counts and the clear-rate denominator; it is not a fault either.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from .baselines import Policy
from .env import IsaacCombatEnv
from .episodes import EpisodeFault, Scenario
from .scenarios import SCENARIO_SET_VERSION

REPORT_VERSION = 2  # 2: Metrics gained `unknown`; `valid` is now the known-outcome count


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)  # no data: the interval is uninformative
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (min(p, max(0.0, center - half)), max(p, min(1.0, center + half)))


@dataclass(frozen=True)
class EpisodeRecord:
    scenario_id: str
    seed: int
    outcome: str  # death | cleared | timeout | unknown | fault
    damage_taken_half_hearts: float = 0.0
    episode_return: float = 0.0
    game_updates: int = 0
    fault: str | None = None


@dataclass(frozen=True)
class Metrics:
    """`attempted == valid + unknown + faults` and `valid == cleared + deaths + timeouts`.

    `valid` is the known-outcome count behind `clear_rate` and its Wilson interval, so the
    minimum-sample checks keep counting exactly that population. The damage and
    return means cover every non-fault episode, `unknown` ones included.
    """

    attempted: int
    valid: int
    cleared: int
    deaths: int
    timeouts: int
    unknown: int
    faults: int
    clear_rate: float
    clear_rate_ci95: tuple[float, float]
    mean_damage_taken_half_hearts: float
    mean_return: float


@dataclass
class EvaluationReport:
    report_version: int
    scenario_set_version: str
    policy: str
    label: str
    split: str
    episodes_per_scenario_seed: int
    seeds: list[int]
    overall: Metrics
    per_scenario: dict[str, Metrics]
    episodes: list[EpisodeRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def summarize(records: Sequence[EpisodeRecord]) -> Metrics:
    non_fault = [r for r in records if r.outcome != "fault"]
    known = [r for r in non_fault if r.outcome != "unknown"]
    cleared = sum(r.outcome == "cleared" for r in known)
    n, m = len(known), len(non_fault)
    return Metrics(
        attempted=len(records),
        valid=n,
        cleared=cleared,
        deaths=sum(r.outcome == "death" for r in known),
        timeouts=sum(r.outcome == "timeout" for r in known),
        unknown=m - n,
        faults=len(records) - m,
        clear_rate=cleared / n if n else 0.0,
        clear_rate_ci95=wilson_interval(cleared, n),
        mean_damage_taken_half_hearts=sum(r.damage_taken_half_hearts for r in non_fault) / m
        if m
        else 0.0,
        mean_return=sum(r.episode_return for r in non_fault) / m if m else 0.0,
    )


def _run_episode(
    policy: Policy, env: IsaacCombatEnv, scenario: Scenario, seed: int
) -> EpisodeRecord:
    policy.reset(seed)
    try:
        obs, _ = env.reset(seed=seed, options={"scenario": scenario})
        while True:
            obs, _, terminated, truncated, info = env.step(policy.act(obs))
            if terminated or truncated:
                break
    except EpisodeFault as exc:
        return EpisodeRecord(scenario.id, seed, "fault", fault=str(exc))
    summary = info["episode"]
    return EpisodeRecord(
        scenario.id,
        seed,
        str(summary["outcome"]),
        float(summary["damage_taken_half_hearts"]),
        float(summary["return"]),
        int(summary["game_updates"]),
    )


def evaluate(
    policy: Policy,
    env_factory: Callable[[], IsaacCombatEnv],
    scenarios: Sequence[Scenario],
    episodes: int,
    seeds: Sequence[int],
) -> EvaluationReport:
    """Run `episodes` episodes for every (scenario, seed); all policies get the same budget."""
    if episodes < 1 or not seeds or not scenarios:
        raise ValueError("Evaluation needs episodes >= 1, at least one seed and one scenario")
    splits = {s.split for s in scenarios}
    if len(splits) != 1:
        raise ValueError("Evaluate one split at a time; scenarios mix splits")
    records: list[EpisodeRecord] = []
    env = env_factory()
    try:
        for scenario in scenarios:
            for seed in seeds:
                for index in range(episodes):
                    # Distinct, reproducible per-episode seed shared by every policy.
                    records.append(_run_episode(policy, env, scenario, seed * 10_000 + index))
    finally:
        env.close()
    return EvaluationReport(
        report_version=REPORT_VERSION,
        scenario_set_version=SCENARIO_SET_VERSION,
        policy=policy.name,
        label=policy.label,
        split=next(iter(splits)),
        episodes_per_scenario_seed=episodes,
        seeds=list(seeds),
        overall=summarize(records),
        per_scenario={
            s.id: summarize([r for r in records if r.scenario_id == s.id]) for s in scenarios
        },
        episodes=records,
    )
