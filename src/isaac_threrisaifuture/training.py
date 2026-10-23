"""Bounded PPO training, predeclared selection rule and multi-seed driver.

Torch and stable-baselines3 are imported lazily so manifests and selection run without them.
Scenarios and the environment factory are parameters; nothing here knows the game.
"""

import argparse
import json
import math
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .checkpoints import (
    ACTION_SCHEMA_VERSION,
    CheckpointError,
    RewardContract,
    capture_rng_state,
    config_hash,
    latest_checkpoint_dir,
    load_checkpoint,
    restore_rng_state,
    save_checkpoint,
)
from .entities import OBSERVATION_SCHEMA_VERSION

DEFAULT_CONFIG = Path("configs/training-v1.yaml")  # offline and synthetic runs
PURE_REWARD_VERSION = 6  # the contract must name the reward version this code pays
PURE_CONFIG = Path(__file__).resolve().parents[2] / "configs" / "training-pure-v4.yaml"
TEMPLATE_STATUS = "template_not_executable_yet"
StopReason = Literal["completed", "wall_time", "disk_limit", "timesteps"]


class TrainingConfigError(ValueError):
    """Invalid training configuration or refused run."""


class BudgetConfig(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    total_timesteps: int
    wall_time_minutes: float
    stop_on_infrastructure_fault: bool
    disk_limit_mb: int = 512


class EvaluationConfig(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    episodes: int
    split: Literal["train", "validation", "test"]
    update_normalizer: bool


class TrainingConfig(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    config_version: Literal[1]
    status: str
    algorithm: Literal["PPO", "RecurrentPPO"]
    device: Literal["cpu"]
    num_envs: Literal[1]
    seed: int
    learning_rate: float
    gamma: float
    gae_lambda: float
    clip_range: float
    ent_coef: float
    n_steps: int
    batch_size: int
    n_epochs: int
    lstm_hidden_size: int
    action_repeat_game_updates: int
    budget: BudgetConfig
    evaluation: EvaluationConfig


class PureContract(BaseModel):
    """What binds the lineage. Any change here needs a new lineage, never a resume."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    algorithm: Literal["RecurrentPPO"]
    device: Literal["cpu"]
    seed: int
    lstm_hidden_size: Annotated[int, Field(gt=0)]
    action_repeat_game_updates: Annotated[int, Field(gt=0)]
    observation_schema_version: int
    action_schema_version: int
    reward_version: int
    use_head_initial_none_probability: Annotated[float, Field(gt=0, lt=1)]


class Hyperparameters(BaseModel):
    """May change between sessions; applied on resume and recorded in each manifest."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    learning_rate: Annotated[float, Field(gt=0)]
    gamma: Annotated[float, Field(gt=0, le=1)]
    gae_lambda: Annotated[float, Field(gt=0, le=1)]
    clip_range: Annotated[float, Field(gt=0)]
    ent_coef: Annotated[float, Field(ge=0)]
    n_steps: Annotated[int, Field(gt=1)]
    batch_size: Annotated[int, Field(gt=0)]
    n_epochs: Annotated[int, Field(gt=0)]


class PureBudget(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    wall_time_minutes: Annotated[float, Field(gt=0)]  # per session
    disk_limit_mb: Annotated[int, Field(gt=0)]
    max_consecutive_faults: Annotated[int, Field(gt=0)]


class RetentionConfig(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    keep_latest: Annotated[int, Field(ge=2)]  # the parent of latest is never deleted
    keep_every: Annotated[int, Field(gt=0)]


class WatchdogConfig(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    stall_seconds: Annotated[float, Field(gt=0)]


class PureTrainingConfig(BaseModel):
    """Config version 2: one continuous lineage; only `contract` is hashed."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    config_version: Literal[2]
    status: str
    contract: PureContract
    hyperparameters: Hyperparameters
    budget: PureBudget
    retention: RetentionConfig
    watchdog: WatchdogConfig

    @property
    def seed(self) -> int:
        return self.contract.seed

    @property
    def algorithm(self) -> Literal["RecurrentPPO"]:
        return self.contract.algorithm

    @property
    def device(self) -> Literal["cpu"]:
        return self.contract.device

    @property
    def lstm_hidden_size(self) -> int:
        return self.contract.lstm_hidden_size

    @property
    def action_repeat_game_updates(self) -> int:
        return self.contract.action_repeat_game_updates

    @property
    def use_head_initial_none_probability(self) -> float:
        return self.contract.use_head_initial_none_probability


AnyTrainingConfig = TrainingConfig | PureTrainingConfig


def load_training_config(path: Path = DEFAULT_CONFIG) -> tuple[AnyTrainingConfig, str]:
    """Return the validated config and its lineage hash.

    Version 1 hashes the whole file. Version 2 hashes the `contract` section only.
    """
    try:
        raw = yaml.safe_load(path.read_text("utf-8"))
        if not isinstance(raw, dict):
            raise TrainingConfigError("Training configuration must be a mapping")
        if raw.get("config_version") == 2:
            pure = PureTrainingConfig.model_validate(raw)
            contract = pure.contract
            if (
                contract.observation_schema_version != OBSERVATION_SCHEMA_VERSION
                or contract.action_schema_version != ACTION_SCHEMA_VERSION
            ):
                raise TrainingConfigError("Contract schema versions do not match this code")
            if contract.reward_version != PURE_REWARD_VERSION:
                raise TrainingConfigError("Contract reward version does not match this code")
            if pure.hyperparameters.batch_size > pure.hyperparameters.n_steps:
                raise TrainingConfigError("batch_size must not exceed n_steps")
            return pure, config_hash(raw["contract"])
        config = TrainingConfig.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise TrainingConfigError(f"Invalid training configuration {path}: {error}") from error
    if config.budget.total_timesteps <= 0 or config.budget.wall_time_minutes <= 0:
        raise TrainingConfigError("Budget limits must be positive")
    if config.evaluation.split == "test":
        raise TrainingConfigError("The test split is held out for final evaluation only")
    return config, config_hash(raw)


def apply_use_head_prior(model: Any, none_probability: float) -> None:
    """Start the use head (the last head of the MultiDiscrete action) at P(none) = p.

    The other three choices share the rest equally. Weights of those rows are zeroed so the
    prior holds for any observation. Only for a fresh model; learning may move it anywhere.
    """
    import numpy as np
    import torch

    nvec = [int(n) for n in model.action_space.nvec]
    use = nvec[-1]
    rest = (1.0 - none_probability) / (use - 1)
    logits = np.log([none_probability] + [rest] * (use - 1))
    logits -= logits.mean()
    net = model.policy.action_net
    with torch.no_grad():
        net.weight[-use:] = 0.0
        net.bias[-use:] = torch.tensor(logits, dtype=net.bias.dtype)


def _hyperparameters(config: AnyTrainingConfig) -> dict[str, Any]:
    names = tuple(Hyperparameters.model_fields)
    source = config.hyperparameters if isinstance(config, PureTrainingConfig) else config
    return {name: getattr(source, name) for name in names}


# --- selection rule -------------------------------------------------------------------------


@dataclass(frozen=True)
class EvalResult:
    """Valid gameplay episodes only; infrastructure faults are counted separately."""

    episodes: int
    cleared: int
    infrastructure_faults: int = 0

    def __post_init__(self) -> None:
        if self.episodes < 0 or not 0 <= self.cleared <= self.episodes:
            raise ValueError("Invalid evaluation counts")

    @property
    def clear_rate(self) -> float:
        return self.cleared / self.episodes if self.episodes else 0.0


@dataclass(frozen=True)
class SelectionRule:
    """Predeclared before experiments; changing it requires a documented new criterion."""

    min_improvement: float = 0.20
    min_episodes: int = 100


@dataclass(frozen=True)
class SelectionDecision:
    accepted: bool
    improvement: float
    ci95_low: float
    ci95_high: float
    reason: str


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return centre - half, centre + half


DEFAULT_RULE = SelectionRule()


def select(
    model: EvalResult, baseline: EvalResult, rule: SelectionRule = DEFAULT_RULE
) -> SelectionDecision:
    """Accept when the clear-rate gain over the baseline meets the rule on enough episodes.

    The interval is Newcombe's hybrid-score 95% interval for the difference; it is reported,
    not part of the acceptance rule.
    """
    improvement = model.clear_rate - baseline.clear_rate
    ml, mh = wilson_interval(model.cleared, model.episodes)
    bl, bh = wilson_interval(baseline.cleared, baseline.episodes)
    low = improvement - math.sqrt((model.clear_rate - ml) ** 2 + (bh - baseline.clear_rate) ** 2)
    high = improvement + math.sqrt((mh - model.clear_rate) ** 2 + (baseline.clear_rate - bl) ** 2)
    if min(model.episodes, baseline.episodes) < rule.min_episodes:
        reason = f"fewer than {rule.min_episodes} evaluation episodes"
        return SelectionDecision(False, improvement, low, high, reason)
    if improvement < rule.min_improvement - 1e-12:
        reason = f"improvement {improvement:.3f} below {rule.min_improvement:.3f}"
        return SelectionDecision(False, improvement, low, high, reason)
    return SelectionDecision(True, improvement, low, high, "meets predeclared rule")


# --- training -------------------------------------------------------------------------------


@dataclass(frozen=True)
class TrainingResult:
    seed: int
    stop_reason: StopReason
    timesteps: int
    checkpoint_id: str | None
    elapsed_seconds: float


def _dir_size_mb(path: Path) -> float:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / 1_000_000


def train(
    config: AnyTrainingConfig,
    cfg_hash: str,
    *,
    seed: int,
    env_factory: Callable[[int], Any],
    out_dir: Path,
    resume: bool = False,
    max_timesteps: int | None = None,
    allow_template: bool = False,
    reward_contract: RewardContract = "combat-v1",
    run_deadline: float | None = None,
    on_progress: Callable[[str, Any], None] | None = None,
    train_metrics_path: Path | None = None,
) -> TrainingResult:
    """Train in n_steps chunks; checkpoint after each chunk; stop on any hard budget limit.

    With a version 2 config, the hyperparameters are applied to the resumed model (the
    rollout buffer is rebuilt for a new n_steps; weights and Adam state are kept) and
    recorded in each manifest. Old checkpoints are pruned per the retention section.
    """
    pure = isinstance(config, PureTrainingConfig)
    hyper = _hyperparameters(config)
    if config.status == TEMPLATE_STATUS and not allow_template:
        raise TrainingConfigError("Configuration is a template; refusing to run without opt-in")
    checkpoints = out_dir / "checkpoints"
    if (
        not resume
        and checkpoints.exists()
        and any(path.name != ".writer.lock" for path in checkpoints.iterdir())
    ):
        raise CheckpointError("Checkpoint artifacts exist; explicit resume/recovery required")
    directory = latest_checkpoint_dir(checkpoints) if resume else None
    # Reject incompatible lineage before creating an environment or loading Torch.
    parent = (
        load_checkpoint(
            directory,
            expected_config_hash=cfg_hash,
            expected_seed=seed,
            expected_reward_contract=reward_contract,
        )
        if directory is not None
        else None
    )
    import torch
    from stable_baselines3.common.monitor import Monitor
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    from .training_metrics import TrainMetricsCallback

    if config.algorithm == "RecurrentPPO":
        from sb3_contrib import RecurrentPPO as Algo
    else:
        from stable_baselines3 import PPO as Algo  # type: ignore[assignment]

    # Version 2 has no total: a session ends on wall time, disk, faults or max_timesteps.
    target = config.budget.total_timesteps if isinstance(config, TrainingConfig) else 2**62
    if max_timesteps is not None:
        target = min(target, max_timesteps)
    # Monitor owns info["episode"] (r/l/t) for SB3 logging; the env's own summary under that
    # key would otherwise crash rollout logging after the first finished episode.
    base_env = DummyVecEnv([lambda: Monitor(env_factory(seed))])
    try:
        if directory is not None:
            assert parent is not None
            venv = VecNormalize.load(str(directory / parent.normalizer_file), base_env)
            # custom_objects overrides saved values before the model is rebuilt, so the new
            # schedule, clip range and n_steps (rollout buffer) take effect; the weights and
            # optimizer state are loaded afterwards by SB3.
            model = Algo.load(
                directory / parent.model_file,
                env=venv,
                device=config.device,
                custom_objects=dict(hyper) if pure else None,
            )
            if pure:
                venv.gamma = hyper["gamma"]
            restore_rng_state(parent.rng_state)
            if "torch" in parent.rng_state:
                torch.set_rng_state(torch.tensor(parent.rng_state["torch"], dtype=torch.uint8))
        else:
            if (checkpoints / "latest.txt").exists():
                raise CheckpointError(f"Checkpoints exist in {checkpoints}; pass resume explicitly")
            venv = VecNormalize(base_env, norm_obs=True, norm_reward=True, gamma=hyper["gamma"])
            kwargs: dict[str, Any] = {}
            if config.algorithm == "RecurrentPPO":
                kwargs["policy_kwargs"] = {"lstm_hidden_size": config.lstm_hidden_size}
            model = Algo(
                "MlpLstmPolicy" if config.algorithm == "RecurrentPPO" else "MlpPolicy",
                venv,
                **hyper,
                seed=seed,
                device=config.device,
                verbose=0,
                **kwargs,
            )
            if isinstance(config, PureTrainingConfig):
                apply_use_head_prior(model, config.use_head_initial_none_probability)

    except BaseException:
        base_env.close()
        raise

    retention = (
        (config.retention.keep_latest, config.retention.keep_every)
        if isinstance(config, PureTrainingConfig)
        else None
    )
    metrics_callback = TrainMetricsCallback(train_metrics_path) if train_metrics_path else None
    started = time.monotonic()
    deadline = started + config.budget.wall_time_minutes * 60
    if run_deadline is not None:
        deadline = min(deadline, run_deadline)
    done = parent.timesteps if parent else 0
    parent_id = parent.checkpoint_id if parent else None
    reason: StopReason = "completed"
    try:
        while done < target:
            if time.monotonic() >= deadline:
                reason = "wall_time"
                break
            if checkpoints.exists() and _dir_size_mb(checkpoints) > config.budget.disk_limit_mb:
                reason = "disk_limit"
                break
            model.learn(
                total_timesteps=hyper["n_steps"],
                reset_num_timesteps=False,
                callback=metrics_callback,
            )
            done = int(model.num_timesteps)
            rng = capture_rng_state()
            rng["torch"] = torch.get_rng_state().tolist()
            if on_progress is not None:
                on_progress("checkpointing", {"timesteps": done})
            manifest = save_checkpoint(
                checkpoints,
                model=model,
                vec_normalize=venv,
                algorithm=config.algorithm,
                cfg_hash=cfg_hash,
                seed=seed,
                timesteps=done,
                parent_checkpoint_id=parent_id,
                rng_state=rng,
                reward_contract=reward_contract,
                hyperparameters=hyper,
                retention=retention,
            )
            parent_id = manifest.checkpoint_id
            if on_progress is not None:
                on_progress("checkpoint_completed", {"id": parent_id, "steps": done})
    finally:
        venv.close()
    return TrainingResult(seed, reason, done, parent_id, time.monotonic() - started)


def run_seeds(
    seeds: Sequence[int],
    train_fn: Callable[[int], TrainingResult],
    report_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Run every seed; a failing seed is recorded, never dropped, and does not stop the others."""
    records: list[dict[str, Any]] = []
    for seed in seeds:
        try:
            records.append({"seed": seed, "status": "ok", **asdict(train_fn(seed))})
        except Exception as error:  # report all seeds including failures
            records.append(
                {"seed": seed, "status": "failed", "error": f"{type(error).__name__}: {error}"}
            )
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(records, indent=2), "utf-8")
    return records


def main(
    argv: Sequence[str] | None = None,
    env_factory: Callable[[int], Any] | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="isaac-train", description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--seed", type=int, action="append", help="repeat for several seeds")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--max-timesteps", type=int)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/training"))
    parser.add_argument("--allow-template", action="store_true")
    args = parser.parse_args(argv)
    try:
        config, cfg_hash = load_training_config(args.config)
        if args.max_timesteps is not None and args.max_timesteps <= 0:
            raise TrainingConfigError("--max-timesteps must be positive")
        if env_factory is None:
            raise TrainingConfigError("No environment factory: the scenario pool is not wired yet")
        seeds = args.seed or [config.seed]
        if args.resume and len(seeds) > 1:
            raise TrainingConfigError("--resume supports a single seed")
        factory = env_factory

        def run(seed: int) -> TrainingResult:
            return train(
                config,
                cfg_hash,
                seed=seed,
                env_factory=factory,
                out_dir=args.out_dir / f"seed-{seed}",
                resume=args.resume,
                max_timesteps=args.max_timesteps,
                allow_template=args.allow_template,
            )

        records = run_seeds(seeds, run, args.out_dir / "seeds.json")
    except (TrainingConfigError, CheckpointError) as error:
        print(f"error: {error}")
        return 2
    print(json.dumps(records, indent=2))
    return 0 if all(r["status"] == "ok" for r in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
