"""Frozen RecurrentPPO checkpoint exposed through the baseline Policy interface.

Inference only: saved observation statistics are applied once and never updated, reward
normalization is off, and nothing is learned or written. Only encoded policy observations
enter; snapshots, oracle data and reward labels never do. The checkpoint must be named by its
exact directory; the moving ``latest.txt`` pointer is refused. Torch and stable-baselines3 are
imported lazily. Artifacts are pickles: load only checkpoints this project produced locally.
"""

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from .checkpoints import (
    LATEST_POINTER,
    MANIFEST_NAME,
    CheckpointError,
    RewardContract,
    load_checkpoint,
)
from .encoding import OBSERVATION_SIZE
from .episodes import ACTION_NVEC

SUPPORTED_ALGORITHM = "RecurrentPPO"


class InvalidPolicyOutput(RuntimeError):
    """The frozen model produced an action outside the action space."""


@dataclass(frozen=True)
class PolicyIdentity:
    """Serializable identity of one immutable checkpoint; equal hashes mean equal artifacts."""

    checkpoint_id: str
    algorithm: str
    config_hash: str
    training_seed: int
    timesteps: int
    observation_schema_version: int
    action_schema_version: int
    reward_schema_version: int
    manifest_sha256: str
    model_sha256: str
    normalizer_sha256: str
    reward_contract: RewardContract = "combat-v1"
    deterministic: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _spaces_only_env(size: int = OBSERVATION_SIZE) -> Any:
    import gymnasium as gym

    class SpacesOnly(gym.Env[NDArray[np.float32], NDArray[np.int64]]):
        """Lets VecNormalize.load validate spaces; it is never stepped."""

        observation_space = gym.spaces.Box(-1.0, 1.0, (size,), np.float32)
        action_space = gym.spaces.MultiDiscrete(list(ACTION_NVEC))

    return SpacesOnly()


def _finite_array(value: Any, name: str, size: int = OBSERVATION_SIZE) -> NDArray[np.float64]:
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError) as error:
        raise CheckpointError(f"Saved {name} is not numeric: {error}") from error
    if array.shape != (size,) or not np.isfinite(array).all():
        raise CheckpointError(f"Saved {name} must be {size} finite values")
    return array


def _positive_scalar(value: Any, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise CheckpointError(f"Saved {name} is not a number: {value!r}")
    if not np.isfinite(value) or value <= 0:
        raise CheckpointError(f"Saved {name} must be finite and positive, got {value!r}")


def _validate_normalizer(normalizer: Any, size: int = OBSERVATION_SIZE) -> None:
    """Reject corrupt observation statistics before any inference; nothing is repaired."""
    stats = getattr(normalizer, "obs_rms", None)
    if not getattr(normalizer, "norm_obs", False) or stats is None:
        raise CheckpointError("Saved normalizer does not normalize observations")
    _finite_array(getattr(stats, "mean", None), "observation mean", size)
    var = _finite_array(getattr(stats, "var", None), "observation variance", size)
    if (var < 0).any():
        raise CheckpointError("Saved observation variance has negative values")
    _positive_scalar(getattr(stats, "count", None), "statistics count")
    _positive_scalar(getattr(normalizer, "epsilon", None), "normalization epsilon")
    _positive_scalar(getattr(normalizer, "clip_obs", None), "observation clip limit")


class CheckpointPolicy:
    """Deterministic frozen policy over one explicit checkpoint directory."""

    label = "frozen-recurrentppo"
    deterministic = True

    def __init__(
        self,
        directory: Path,
        *,
        expected_config_hash: str,
        expected_seed: int | None = None,
    ) -> None:
        directory = Path(directory)
        if directory.name == LATEST_POINTER or (directory / LATEST_POINTER).exists():
            raise CheckpointError("Name one checkpoint directory, not the latest pointer root")
        if not directory.is_dir():
            raise CheckpointError(f"Checkpoint directory not found: {directory}")
        self.observation_size = OBSERVATION_SIZE
        manifest = load_checkpoint(
            directory,
            expected_config_hash=expected_config_hash,
            expected_seed=expected_seed,
        )
        if manifest.algorithm != SUPPORTED_ALGORITHM:
            raise CheckpointError(f"Unsupported algorithm {manifest.algorithm!r}")
        if manifest.checkpoint_id != directory.name:
            raise CheckpointError(
                f"Manifest id {manifest.checkpoint_id!r} != directory {directory.name!r}"
            )
        self._paths = {
            "manifest": directory / MANIFEST_NAME,
            "model": directory / manifest.model_file,
            "normalizer": directory / manifest.normalizer_file,
        }
        hashes = {key: _sha256(path) for key, path in self._paths.items()}
        self.identity = PolicyIdentity(
            checkpoint_id=manifest.checkpoint_id,
            algorithm=manifest.algorithm,
            config_hash=manifest.config_hash,
            training_seed=manifest.seed,
            timesteps=manifest.timesteps,
            observation_schema_version=manifest.observation_schema_version,
            action_schema_version=manifest.action_schema_version,
            reward_schema_version=manifest.reward_schema_version,
            manifest_sha256=hashes["manifest"],
            model_sha256=hashes["model"],
            normalizer_sha256=hashes["normalizer"],
            reward_contract=manifest.reward_contract,
        )
        self.name = f"checkpoint:{manifest.checkpoint_id}"
        self._model, self._normalizer = self._load()
        self._state: tuple[NDArray[Any], ...] | None = None
        self._episode_start = np.ones((1,), dtype=bool)

    def _load(self) -> tuple[Any, Any]:
        from sb3_contrib import RecurrentPPO
        from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

        try:
            normalizer = VecNormalize.load(
                str(self._paths["normalizer"]),
                DummyVecEnv([lambda: _spaces_only_env(self.observation_size)]),
            )
            model = RecurrentPPO.load(self._paths["model"], device="cpu", print_system_info=False)
        except Exception as error:  # any unreadable artifact is a checkpoint fault
            raise CheckpointError(f"Cannot load checkpoint artifacts: {error}") from error
        if not isinstance(normalizer, VecNormalize):
            raise CheckpointError("Normalizer file is not a VecNormalize state")
        normalizer.training = False  # freeze observation statistics
        normalizer.norm_reward = False  # rewards are never seen at inference
        _validate_normalizer(normalizer, self.observation_size)
        if getattr(model.observation_space, "shape", None) != (self.observation_size,):
            raise CheckpointError("Model observation shape does not match the current encoder")
        nvec = getattr(model.action_space, "nvec", None)
        if nvec is None or tuple(int(n) for n in nvec) != ACTION_NVEC:
            raise CheckpointError("Model action space does not match MultiDiscrete([5, 5, 4])")
        model.policy.set_training_mode(False)
        return model, normalizer

    def reset(self, seed: int) -> None:
        """Start a new episode: clear recurrent state. The seed reproduces no game state."""
        self._state = None
        self._episode_start = np.ones((1,), dtype=bool)

    def act(self, observation: NDArray[np.float32]) -> NDArray[np.int64]:
        try:
            obs = np.asarray(observation, dtype=np.float32)
        except (TypeError, ValueError) as error:
            raise ValueError(f"Observation is not numeric: {error}") from error
        if obs.shape != (self.observation_size,):
            raise ValueError(f"Observation shape {obs.shape} != ({self.observation_size},)")
        if not np.isfinite(obs).all():
            raise ValueError("Observation contains non-finite values")
        normalized = self._normalizer.normalize_obs(obs[None, :])
        if not np.isfinite(normalized).all():
            raise CheckpointError("Normalized observation is non-finite; normalizer is corrupt")
        action, state = self._model.predict(
            normalized,
            state=self._state,
            episode_start=self._episode_start,
            deterministic=True,
        )
        result = np.asarray(action)
        if result.shape == (1, len(ACTION_NVEC)):
            result = result[0]
        if (
            result.shape != (len(ACTION_NVEC),)
            or not np.issubdtype(result.dtype, np.integer)
            or (result < 0).any()
            or (result >= np.array(ACTION_NVEC)).any()
        ):
            raise InvalidPolicyOutput(
                f"Model action {result!r} is outside MultiDiscrete([5, 5, 4])"
            )
        self._state = state
        self._episode_start = np.zeros((1,), dtype=bool)
        return result.astype(np.int64)

    def verify_unchanged(self) -> None:
        """Re-hash the artifacts; raise if any file differs from the loaded identity."""
        expected = {
            "manifest": self.identity.manifest_sha256,
            "model": self.identity.model_sha256,
            "normalizer": self.identity.normalizer_sha256,
        }
        for key, path in self._paths.items():
            if not path.is_file() or _sha256(path) != expected[key]:
                raise CheckpointError(f"Checkpoint {key} changed after loading: {path}")
