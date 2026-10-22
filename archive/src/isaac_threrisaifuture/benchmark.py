"""Offline throughput benchmark for the environment stack. See openspec change
benchmark-and-training-optimization.

Only the synthetic backend is measured here; synthetic numbers say nothing about Isaac. Timing is
read from an injectable clock so tests are deterministic. Proposals are returned, never applied.
"""

import json
import os
import platform
import random
import sys
import time
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .encoding import encode
from .entities import EntityFrame
from .env import UPDATES_PER_SECOND, IsaacCombatEnv
from .episodes import Action, EpisodeFault, Scenario, StepResult
from .scenarios import SCENARIO_SET_VERSION, scenarios_for
from .sim import SyntheticRoomBackend

BENCHMARK_SCHEMA_VERSION = 1
BACKEND_LABEL = "synthetic"  # the only backend this module can measure
Clock = Callable[[], float]
MAX_STEPS_LIMIT = 100_000
MAX_SECONDS_LIMIT = 600.0


@dataclass(frozen=True)
class BenchmarkConfig:
    action_repeat: int = 3
    max_steps: int = 500
    max_seconds: float = 30.0
    seed: int = 0

    def __post_init__(self) -> None:
        if not 1 <= self.action_repeat <= 15:  # mirrors the action protocol bound
            raise ValueError("action_repeat must be 1..15")
        if not 1 <= self.max_steps <= MAX_STEPS_LIMIT:
            raise ValueError(f"max_steps must be 1..{MAX_STEPS_LIMIT}")
        if not 0 < self.max_seconds <= MAX_SECONDS_LIMIT:
            raise ValueError(f"max_seconds must be in (0, {MAX_SECONDS_LIMIT}]")


class _TimedBackend:
    """Wraps a backend to time its step calls and remember the latest frame."""

    def __init__(self, inner: SyntheticRoomBackend, clock: Clock) -> None:
        self._inner = inner
        self._clock = clock
        self.supports_seed = inner.supports_seed
        self.latencies: list[float] = []
        self.last_frame: EntityFrame | None = None

    def start_episode(self, scenario: Scenario, seed: int | None) -> StepResult:
        result = self._inner.start_episode(scenario, seed)
        self.last_frame = result.frame
        return result

    def step(self, action: Action, repeat: int) -> StepResult:
        start = self._clock()
        result = self._inner.step(action, repeat)
        self.latencies.append(self._clock() - start)
        self.last_frame = result.frame
        return result

    def release(self) -> None:
        self._inner.release()

    def close(self) -> None:
        self._inner.close()


def _stats(values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {"count": 0, "mean": 0.0, "max": 0.0}
    return {"count": len(values), "mean": sum(values) / len(values), "max": max(values)}


def host_info() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
        "cuda_required": False,
    }


def run_benchmark(
    config: BenchmarkConfig,
    scenarios: Sequence[Scenario] | None = None,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Step a synthetic environment with seeded random actions until a step or time bound.

    `deterministic` depends only on config, scenarios and seed; `timing` and `host` do not.
    """
    now = clock or time.perf_counter
    pool = tuple(scenarios) if scenarios else scenarios_for("train")
    backend = _TimedBackend(SyntheticRoomBackend(), now)
    env = IsaacCombatEnv(backend, pool, action_repeat=config.action_repeat)
    rng = random.Random(config.seed)
    outcomes: Counter[str] = Counter()
    steps = faults = 0
    game_updates = 0
    step_seconds = 0.0
    encode_times: list[float] = []
    started = now()
    needs_reset = True
    seed_next: int | None = config.seed
    try:
        while steps < config.max_steps and now() - started < config.max_seconds:
            if needs_reset:
                try:
                    env.reset(seed=seed_next)
                except EpisodeFault:
                    faults += 1
                    break  # a failing reset would loop forever
                seed_next = None
                needs_reset = False
            action = np.array([rng.randrange(5), rng.randrange(5)], dtype=np.int64)
            before = env.controller.last_updates
            t0 = now()
            try:
                _, _, terminated, truncated, info = env.step(action)
            except EpisodeFault:
                faults += 1
                needs_reset = True
                continue
            step_seconds += now() - t0
            steps += 1
            game_updates += env.controller.last_updates - before
            if backend.last_frame is not None:
                t1 = now()
                encode(backend.last_frame)
                encode_times.append(now() - t1)
            if terminated or truncated:
                outcomes[str(info["outcome"])] += 1
                needs_reset = True
    finally:
        env.close()
    elapsed = now() - started
    episodes = sum(outcomes.values())
    return {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "backend": BACKEND_LABEL,
        "real_game_throughput": "blocked",
        "deterministic": {
            "config": {
                "action_repeat": config.action_repeat,
                "max_steps": config.max_steps,
                "max_seconds": config.max_seconds,
                "seed": config.seed,
            },
            "scenario_set_version": SCENARIO_SET_VERSION,
            "scenario_ids": [s.id for s in pool],
            "steps": steps,
            "game_updates": game_updates,
            "episodes": episodes,
            "outcomes": dict(sorted(outcomes.items())),
            "faults": faults,
            "clear_rate": outcomes["cleared"] / episodes if episodes else 0.0,
            "fault_rate": faults / (steps + faults) if steps + faults else 0.0,
        },
        "timing": {
            "elapsed_seconds": elapsed,
            "env_steps_per_second": steps / step_seconds if step_seconds > 0 else 0.0,
            "game_updates_per_second": game_updates / step_seconds if step_seconds > 0 else 0.0,
            "realtime_factor": (
                game_updates / UPDATES_PER_SECOND / step_seconds if step_seconds > 0 else 0.0
            ),
            "backend_step_latency_seconds": _stats(backend.latencies),
            "observation_encode_seconds": _stats(encode_times),
        },
        "host": host_info(),
    }


def compare_action_repeat(
    repeats: Sequence[int],
    base: BenchmarkConfig | None = None,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Run the synthetic benchmark once per action_repeat with otherwise identical settings."""
    if not repeats or len(set(repeats)) != len(repeats):
        raise ValueError("repeats must be non-empty and unique")
    base = base or BenchmarkConfig()
    runs = [
        run_benchmark(BenchmarkConfig(r, base.max_steps, base.max_seconds, base.seed), clock=clock)
        for r in repeats
    ]
    return {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "backend": BACKEND_LABEL,
        "note": "Synthetic backend only; says nothing about Isaac throughput or quality.",
        "runs": runs,
    }


def propose_config_changes(
    comparison: dict[str, Any],
    *,
    min_gain: float = 1.2,
    max_clear_rate_drop: float = 0.05,
    min_episodes: int = 5,
) -> list[dict[str, Any]]:
    """Suggest an action_repeat change with evidence. Never edits any configuration.

    The first run is the baseline. A candidate qualifies only if it gains game updates/sec,
    keeps the clear rate and adds no faults, with enough episodes to compare.
    """
    runs = comparison["runs"]
    if comparison.get("backend") != BACKEND_LABEL or len(runs) < 2:
        return []
    base = runs[0]
    best: dict[str, Any] | None = None
    for run in runs[1:]:
        d, bd = run["deterministic"], base["deterministic"]
        gain = _ratio(
            run["timing"]["game_updates_per_second"], base["timing"]["game_updates_per_second"]
        )
        if (
            min(d["episodes"], bd["episodes"]) >= min_episodes
            and gain >= min_gain
            and d["clear_rate"] >= bd["clear_rate"] - max_clear_rate_drop
            and d["fault_rate"] <= bd["fault_rate"]
            and (
                best is None
                or run["timing"]["game_updates_per_second"]
                > best["timing"]["game_updates_per_second"]
            )
        ):
            best = run
    if best is None:
        return []
    d, bd = best["deterministic"], base["deterministic"]
    return [
        {
            "applied": False,
            "key": "action_repeat",
            "from": bd["config"]["action_repeat"],
            "to": d["config"]["action_repeat"],
            "evidence": {
                "backend": BACKEND_LABEL,
                "game_updates_per_second": [
                    base["timing"]["game_updates_per_second"],
                    best["timing"]["game_updates_per_second"],
                ],
                "clear_rate": [bd["clear_rate"], d["clear_rate"]],
                "fault_rate": [bd["fault_rate"], d["fault_rate"]],
                "episodes": [bd["episodes"], d["episodes"]],
            },
            "caveat": "Synthetic evidence only; changes step and reward cadence, so re-validate "
            "on a real backend and a validation split before adopting.",
        }
    ]


def _ratio(value: float, reference: float) -> float:
    return value / reference if reference > 0 else 0.0


def write_report(report: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
