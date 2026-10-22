"""Terminal spectator and checkpoint browser (offline contract).

Output is plain text on stdout only: no monitor capture and no desktop input. Watching runs
inference only, never training. Lines carry frame id, action, reward and outcome; hidden/oracle
data never appears in them. A real game is controlled only through an explicitly injected env.
"""

import argparse
import json
import sys
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .baselines import Policy, RandomPolicy, ScriptedPolicy
from .checkpoints import CheckpointError, check_compatible, load_checkpoint, read_manifest
from .env import IsaacCombatEnv
from .episodes import EpisodeFault, GameBackend, Scenario, StepResult
from .recording import JsonlRecorder
from .rewards import CombatCoefficients, RewardLedger
from .scenarios import SCENARIOS
from .sim import SyntheticRoomBackend

REPORT_NAME = "report.json"  # optional EvaluationReport.to_dict() written next to the manifest
MODE_RANDOM = "random"
MODE_SCRIPTED = "scripted-baseline"
CHECKPOINT_PREFIX = "checkpoint:"
DEFAULT_MAX_STEPS = 2000

EnvFactory = Callable[[], IsaacCombatEnv]
PolicyLoader = Callable[[Path], Policy]  # loads a model from a validated checkpoint directory


class SpectatorError(Exception):
    """Unusable spectator request (unknown mode, missing checkpoint, no real backend)."""


@dataclass(frozen=True)
class CheckpointEntry:
    directory: str
    checkpoint_id: str | None
    timesteps: int | None
    seed: int | None
    parent_checkpoint_id: str | None
    algorithm: str | None
    compatible: bool
    problem: str | None
    clear_rate: float | None
    eval_episodes: int | None


def _read_eval(directory: Path) -> tuple[float | None, int | None]:
    try:
        overall = json.loads((directory / REPORT_NAME).read_text("utf-8"))["overall"]
        return float(overall["clear_rate"]), int(overall["valid"])
    except (OSError, ValueError, KeyError, TypeError):
        return None, None


def list_checkpoints(root: Path) -> list[CheckpointEntry]:
    """Every subdirectory with a manifest; incompatible or corrupt ones are flagged, not hidden."""
    entries: list[CheckpointEntry] = []
    for directory in sorted(p for p in root.iterdir() if p.is_dir()) if root.is_dir() else []:
        try:
            manifest = read_manifest(directory)
        except CheckpointError as error:
            if (directory / "manifest.json").exists():
                entries.append(
                    CheckpointEntry(
                        directory.name, None, None, None, None, None, False, str(error), None, None
                    )
                )
            continue
        problem: str | None = None
        try:
            check_compatible(manifest, expected_config_hash=None, expected_seed=None)
        except CheckpointError as error:
            problem = str(error)
        rate, episodes = _read_eval(directory)
        entries.append(
            CheckpointEntry(
                directory.name,
                manifest.checkpoint_id,
                manifest.timesteps,
                manifest.seed,
                manifest.parent_checkpoint_id,
                manifest.algorithm,
                problem is None,
                problem,
                rate,
                episodes,
            )
        )
    entries.sort(key=lambda e: (e.timesteps if e.timesteps is not None else -1, e.directory))
    return entries


def format_checkpoints(entries: Sequence[CheckpointEntry]) -> list[str]:
    if not entries:
        return ["no checkpoints found"]
    lines = ["id timesteps seed parent clear_rate(n) status"]
    for e in entries:
        rate = "n/a" if e.clear_rate is None else f"{e.clear_rate:.3f}({e.eval_episodes})"
        status = "ok" if e.compatible else f"INCOMPATIBLE: {e.problem}"
        lines.append(
            f"{e.checkpoint_id or e.directory} {e.timesteps if e.timesteps is not None else '?'} "
            f"{e.seed if e.seed is not None else '?'} {e.parent_checkpoint_id or '-'} "
            f"{rate} {status}"
        )
    return lines


def resolve_policy(
    mode: str, *, checkpoints: Path | None = None, loader: PolicyLoader | None = None
) -> tuple[Policy, str]:
    """Map an explicit mode label to a policy; checkpoints are validated before loading."""
    if mode == MODE_RANDOM:
        return RandomPolicy(), mode
    if mode == MODE_SCRIPTED:
        return ScriptedPolicy(), mode
    if not mode.startswith(CHECKPOINT_PREFIX) or len(mode) == len(CHECKPOINT_PREFIX):
        raise SpectatorError(
            f"Unknown mode {mode!r}; use {MODE_RANDOM}, {MODE_SCRIPTED} or checkpoint:<id>"
        )
    if checkpoints is None or loader is None:
        raise SpectatorError("checkpoint mode needs --checkpoints and a model loader")
    directory = checkpoints / mode[len(CHECKPOINT_PREFIX) :]
    if directory.resolve().parent != checkpoints.resolve():
        raise SpectatorError("Checkpoint id must name a direct subdirectory")
    load_checkpoint(directory, expected_config_hash=None, expected_seed=None)  # may reject
    return loader(directory), mode


class _FrameTap:
    """Backend proxy that copies each policy frame to a recorder; events are never touched."""

    def __init__(self, inner: GameBackend, recorder: JsonlRecorder) -> None:
        self._inner = inner
        self._recorder = recorder

    def start_episode(self, scenario: Scenario, seed: int | None) -> StepResult:
        return self._tap(self._inner.start_episode(scenario, seed))

    def step(self, action: Any, repeat: int) -> StepResult:
        return self._tap(self._inner.step(action, repeat))

    def _tap(self, result: StepResult) -> StepResult:
        self._recorder.record(result.frame)
        return result

    def release(self) -> None:
        self._inner.release()

    def close(self) -> None:
        self._inner.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


def spectate(
    policy: Policy,
    env_factory: EnvFactory,
    scenario: Scenario,
    *,
    mode: str,
    seed: int = 0,
    max_steps: int = DEFAULT_MAX_STEPS,
    recorder: JsonlRecorder | None = None,
) -> Iterator[str]:
    """Play one fixed scenario and yield text lines; control is always released on exit."""
    if max_steps < 1:
        raise ValueError("max_steps must be >= 1")
    env = env_factory()
    if recorder is not None:
        env.controller.backend = _FrameTap(env.controller.backend, recorder)
    steps, total, outcome = 0, 0.0, "stopped"
    try:
        yield f"watch mode={mode} scenario={scenario.id} seed={seed} max_steps={max_steps}"
        policy.reset(seed)
        obs, info = env.reset(seed=seed, options={"scenario": scenario})
        yield f"episode={info['episode_id']} frame_id={info['frame_id']} start"
        while steps < max_steps:
            action = policy.act(obs)
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1
            total += reward
            outcome = info["outcome"] or "running"
            yield (
                f"step={steps} frame_id={info['frame_id']} "
                f"action=move:{int(action[0])},shoot:{int(action[1])} "
                f"reward={reward:.4f} outcome={outcome}"
            )
            if terminated or truncated:
                break
        else:
            outcome = "stopped"
    except EpisodeFault as fault:
        outcome = "fault"
        yield f"fault: {fault}"
    finally:
        env.controller.backend.release()
        env.close()
    yield f"summary mode={mode} outcome={outcome} steps={steps} return={total:.4f}"


def synthetic_env_factory() -> IsaacCombatEnv:
    return IsaacCombatEnv(
        SyntheticRoomBackend(),
        SCENARIOS,
        accountant=RewardLedger(CombatCoefficients.load()),
    )


def _scenario_by_id(scenario_id: str) -> Scenario:
    for scenario in SCENARIOS:
        if scenario.id == scenario_id:
            return scenario
    raise SpectatorError(f"Unknown scenario {scenario_id!r}")


def main(
    argv: Sequence[str] | None = None,
    *,
    env_factory: EnvFactory | None = None,
    policy_loader: PolicyLoader | None = None,
    out: Callable[[str], None] = print,
) -> int:
    parser = argparse.ArgumentParser(prog="spectator")
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="list checkpoints in a directory")
    listing.add_argument("checkpoints", type=Path)
    watch = sub.add_parser("watch", help="watch one deterministic inference episode")
    watch.add_argument("--mode", required=True)
    watch.add_argument("--checkpoints", type=Path)
    watch.add_argument("--scenario", default="val-d1-a")
    watch.add_argument("--seed", type=int, default=0)
    watch.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS)
    watch.add_argument("--record", type=Path, help="write policy frames to a new JSONL file")
    watch.add_argument("--game", action="store_true", help="control the real game")
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            for line in format_checkpoints(list_checkpoints(args.checkpoints)):
                out(line)
            return 0
        if args.game and env_factory is None:
            raise SpectatorError("No real game backend was injected; refusing to control a game")
        policy, label = resolve_policy(
            args.mode, checkpoints=args.checkpoints, loader=policy_loader
        )
        real = env_factory is not None
        if not real:
            out("# SYNTHETIC toy simulator: not Isaac")
        recorder = (
            JsonlRecorder(args.record, "policy_frames", "game_api" if real else "synthetic")
            if args.record
            else None
        )
        try:
            for line in spectate(
                policy,
                env_factory or synthetic_env_factory,
                _scenario_by_id(args.scenario),
                mode=label,
                seed=args.seed,
                max_steps=args.max_steps,
                recorder=recorder,
            ):
                out(line)
        finally:
            if recorder is not None:
                recorder.close()
        return 0
    except (SpectatorError, CheckpointError, FileExistsError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("stopped by user; control released", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
