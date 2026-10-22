"""Checkpoint manifests: model and normalizer saved together, strict compatibility on load."""

import errno
import hashlib
import json
import os
import random
import re
import shutil
import sys
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, Any, Literal, Self

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .entities import OBSERVATION_SCHEMA_VERSION

CHECKPOINT_SCHEMA_VERSION: Literal[2] = 2
ACTION_SCHEMA_VERSION = 2
REWARD_SCHEMA_VERSION = 1
RewardContract = Literal["combat-v1", "pure-v3"]

MANIFEST_NAME = "manifest.json"
LATEST_POINTER = "latest.txt"


class CheckpointError(Exception):
    """Missing, corrupt or incompatible checkpoint."""


class CheckpointManifest(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    checkpoint_schema_version: Literal[1, 2] = 1
    observation_schema_version: int
    action_schema_version: int
    reward_schema_version: int
    reward_contract: RewardContract = "combat-v1"
    algorithm: str
    config_hash: str
    seed: int
    checkpoint_id: str
    parent_checkpoint_id: str | None
    timesteps: int
    model_file: str
    normalizer_file: str
    rng_state: dict[str, Any]
    model_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None
    normalizer_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")] | None = None
    # Position in the parent chain (first checkpoint is 1); drives retention.
    rollout_index: int | None = None
    # Hyperparameters in effect when this checkpoint was written (config version 2).
    hyperparameters: dict[str, Any] | None = None

    @model_validator(mode="after")
    def complete_hashes(self) -> Self:
        if self.checkpoint_schema_version == 2 and (
            self.model_sha256 is None or self.normalizer_sha256 is None
        ):
            raise ValueError("Checkpoint storage v2 requires both artifact hashes")
        return self


def config_hash(config: dict[str, Any]) -> str:
    canonical = json.dumps(config, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def capture_rng_state() -> dict[str, Any]:
    """Python and NumPy global RNG state as JSON; torch state is added by the trainer."""
    version, internal, gauss = random.getstate()
    kind, keys, pos, has_gauss, cached = np.random.get_state()
    return {
        "python": [version, list(internal), gauss],
        "numpy": [kind, keys.tolist(), int(pos), int(has_gauss), float(cached)],
    }


def restore_rng_state(state: dict[str, Any]) -> None:
    version, internal, gauss = state["python"]
    random.setstate((version, tuple(internal), gauss))
    kind, keys, pos, has_gauss, cached = state["numpy"]
    np.random.set_state((kind, np.array(keys, dtype=np.uint32), pos, has_gauss, cached))


def check_compatible(
    manifest: CheckpointManifest,
    *,
    expected_config_hash: str | None,
    expected_seed: int | None,
    expected_reward_contract: RewardContract | None = None,
) -> None:
    """Reject any checkpoint that does not match the current schemas, config and seed."""
    current = {
        "observation_schema_version": OBSERVATION_SCHEMA_VERSION,
        "action_schema_version": ACTION_SCHEMA_VERSION,
        "reward_schema_version": REWARD_SCHEMA_VERSION,
    }
    for name, value in current.items():
        if getattr(manifest, name) != value:
            raise CheckpointError(f"Incompatible {name}: {getattr(manifest, name)} != {value}")
    if expected_config_hash is not None and manifest.config_hash != expected_config_hash:
        raise CheckpointError("Checkpoint was produced by a different training configuration")
    if expected_seed is not None and manifest.seed != expected_seed:
        raise CheckpointError(f"Checkpoint seed {manifest.seed} != requested seed {expected_seed}")
    if (
        expected_reward_contract is not None
        and manifest.reward_contract != expected_reward_contract
    ):
        raise CheckpointError(
            f"Incompatible reward contract: {manifest.reward_contract} != "
            f"{expected_reward_contract}; explicit lineage migration is required"
        )


def read_manifest(directory: Path) -> CheckpointManifest:
    path = directory / MANIFEST_NAME
    if not path.is_file():
        raise CheckpointError(f"Checkpoint manifest not found: {path}")
    try:
        manifest = CheckpointManifest.model_validate(json.loads(path.read_text("utf-8")))
    except (ValueError, ValidationError) as error:
        raise CheckpointError(f"Invalid checkpoint manifest {path}: {error}") from error
    for name in (manifest.model_file, manifest.normalizer_file):
        _component(name)
        if not (directory / name).is_file():
            raise CheckpointError(f"Checkpoint file missing: {directory / name}")
        if (directory / name).resolve().parent != directory.resolve():
            raise CheckpointError("Checkpoint artifact escapes its directory")
    for name, expected in (
        (manifest.model_file, manifest.model_sha256),
        (manifest.normalizer_file, manifest.normalizer_sha256),
    ):
        if expected is not None and _sha256(directory / name) != expected:
            raise CheckpointError(f"Checkpoint artifact hash mismatch: {name}")
    return manifest


def write_manifest(directory: Path, manifest: CheckpointManifest) -> None:
    (directory / MANIFEST_NAME).write_text(manifest.model_dump_json(indent=2), "utf-8")


def save_checkpoint(
    root: Path,
    *,
    model: Any,
    vec_normalize: Any,
    algorithm: str,
    cfg_hash: str,
    seed: int,
    timesteps: int,
    parent_checkpoint_id: str | None,
    rng_state: dict[str, Any],
    reward_contract: RewardContract = "combat-v1",
    hyperparameters: dict[str, Any] | None = None,
    retention: tuple[int, int] | None = None,
) -> CheckpointManifest:
    """Publish one complete immutable checkpoint, then atomically advance latest.

    With `retention=(keep_latest, keep_every)`, older checkpoints are pruned afterwards.
    """
    root.mkdir(parents=True, exist_ok=True)
    with _writer_lock(root):
        rollout_index = 1
        if (root / LATEST_POINTER).exists():
            parent = load_checkpoint(
                latest_checkpoint_dir(root),
                expected_config_hash=cfg_hash,
                expected_seed=seed,
                expected_reward_contract=reward_contract,
            )
            if parent.checkpoint_id != parent_checkpoint_id or timesteps <= parent.timesteps:
                raise CheckpointError("Stale checkpoint parent or non-increasing timesteps")
            rollout_index = (parent.rollout_index or 0) + 1
        elif any(
            path.is_dir() and not path.name.startswith(".pending-") for path in root.iterdir()
        ):
            raise CheckpointError(
                "Checkpoint pointer missing with completed artifacts; recovery required"
            )
        manifest = _publish_checkpoint(
            root,
            model=model,
            vec_normalize=vec_normalize,
            algorithm=algorithm,
            cfg_hash=cfg_hash,
            seed=seed,
            timesteps=timesteps,
            parent_checkpoint_id=parent_checkpoint_id,
            rng_state=rng_state,
            reward_contract=reward_contract,
            rollout_index=rollout_index,
            hyperparameters=hyperparameters,
        )
        if retention is not None:
            prune_checkpoints(root, keep_latest=retention[0], keep_every=retention[1])
        return manifest


def prune_checkpoints(root: Path, *, keep_latest: int, keep_every: int) -> list[str]:
    """Delete old checkpoints; keep the newest ones and every `keep_every`-th rollout.

    The latest checkpoint and its parent are never deleted. Directories without a rollout
    index (older lineages) and anything unreadable are left alone. Call under the writer lock.
    """
    if keep_latest < 2 or keep_every < 1:
        raise ValueError("Retention needs keep_latest >= 2 and keep_every >= 1")
    latest = latest_checkpoint_dir(root).name
    found: dict[str, tuple[int, str | None]] = {}
    for path in root.iterdir():
        if not path.is_dir() or path.name.startswith("."):
            continue
        try:
            raw = json.loads((path / MANIFEST_NAME).read_text("utf-8"))
        except (OSError, ValueError):
            continue
        index = raw.get("rollout_index") if isinstance(raw, dict) else None
        if isinstance(index, int):
            found[path.name] = (index, raw.get("parent_checkpoint_id"))
    keep = {latest}
    if latest in found and found[latest][1] is not None:
        keep.add(str(found[latest][1]))
    newest = sorted(found, key=lambda name: found[name][0], reverse=True)[:keep_latest]
    keep.update(newest)
    keep.update(name for name, (index, _) in found.items() if index % keep_every == 0)
    deleted: list[str] = []
    for name in found:
        if name in keep:
            continue
        try:
            shutil.rmtree(root / name)
            deleted.append(name)
        except OSError:
            pass  # Windows may hold a file; the next checkpoint retries.
    return deleted


def _publish_checkpoint(
    root: Path,
    *,
    model: Any,
    vec_normalize: Any,
    algorithm: str,
    cfg_hash: str,
    seed: int,
    timesteps: int,
    parent_checkpoint_id: str | None,
    rng_state: dict[str, Any],
    reward_contract: RewardContract,
    rollout_index: int,
    hyperparameters: dict[str, Any] | None,
) -> CheckpointManifest:
    checkpoint_id = f"{cfg_hash[:8]}-s{seed}-t{timesteps}"
    _component(checkpoint_id)
    # An interrupted pointer publication may have left a complete unreferenced
    # candidate. Preserve it; never overwrite or adopt it by directory discovery.
    if (root / checkpoint_id).exists():
        checkpoint_id += "-r" + uuid.uuid4().hex[:12]
    _component(checkpoint_id)
    directory = root / checkpoint_id
    stage = root / (".pending-" + uuid.uuid4().hex)
    pointer = root / (".latest-" + uuid.uuid4().hex + ".tmp")
    stage.mkdir()
    try:
        model.save(stage / "model.zip")
        vec_normalize.save(str(stage / "vecnormalize.pkl"))
        for name in ("model.zip", "vecnormalize.pkl"):
            _sync_file(stage / name)
        manifest = CheckpointManifest(
            checkpoint_schema_version=CHECKPOINT_SCHEMA_VERSION,
            observation_schema_version=OBSERVATION_SCHEMA_VERSION,
            action_schema_version=ACTION_SCHEMA_VERSION,
            reward_schema_version=REWARD_SCHEMA_VERSION,
            reward_contract=reward_contract,
            algorithm=algorithm,
            config_hash=cfg_hash,
            seed=seed,
            checkpoint_id=checkpoint_id,
            parent_checkpoint_id=parent_checkpoint_id,
            timesteps=timesteps,
            model_file="model.zip",
            normalizer_file="vecnormalize.pkl",
            rng_state=rng_state,
            model_sha256=_sha256(stage / "model.zip"),
            normalizer_sha256=_sha256(stage / "vecnormalize.pkl"),
            rollout_index=rollout_index,
            hyperparameters=hyperparameters,
        )
        write_manifest(stage, manifest)
        _sync_file(stage / MANIFEST_NAME)
        read_manifest(stage)
        stage.rename(directory)
        with pointer.open("xb") as stream:
            stream.write(checkpoint_id.encode("utf-8"))
            stream.flush()
            os.fsync(stream.fileno())
        _replace_pointer(pointer, root / LATEST_POINTER)
        return manifest
    finally:
        pointer.unlink(missing_ok=True)
        if stage.exists() and stage.parent.resolve() == root.resolve():
            shutil.rmtree(stage)  # only this invocation's UUID staging directory


def latest_checkpoint_dir(root: Path) -> Path:
    pointer = root / LATEST_POINTER
    try:
        raw = _read_pointer(pointer)
        if len(raw) > 256:
            raise CheckpointError("Checkpoint pointer exceeds size limit")
        name = raw.decode("utf-8").strip()
    except FileNotFoundError as error:
        raise CheckpointError(f"No checkpoint to resume from in {root}") from error
    except (OSError, UnicodeError) as error:
        raise CheckpointError(f"Cannot read checkpoint pointer: {error}") from error
    _component(name)
    directory = root / name
    if directory.resolve().parent != root.resolve():
        raise CheckpointError("Checkpoint pointer escapes its root")
    manifest = read_manifest(directory)
    if manifest.checkpoint_schema_version == 2 and manifest.checkpoint_id != name:
        raise CheckpointError("Checkpoint pointer/manifest identity mismatch")
    return directory


def _read_pointer(pointer: Path) -> bytes:
    """Windows can deny opening a pointer during atomic replacement; never fall back."""
    deadline = time.monotonic() + 1.0
    while True:
        try:
            with pointer.open("rb") as stream:
                return stream.read(257)
        except PermissionError as error:
            known_windows = getattr(error, "winerror", None) in (5, 32, 33) or (
                sys.platform == "win32"
                and error.errno == errno.EACCES
                and getattr(error, "winerror", None) is None
            )
            if not known_windows:
                raise
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)


def _component(name: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", name):
        raise CheckpointError("Invalid checkpoint path component")


def _sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _sync_file(path: Path) -> None:
    with path.open("r+b") as stream:
        stream.flush()
        os.fsync(stream.fileno())


def _replace_pointer(source: Path, destination: Path) -> None:
    deadline = time.monotonic() + 1.0
    while True:
        try:
            os.replace(source, destination)
            return
        except PermissionError as error:
            if getattr(error, "winerror", None) not in (5, 32, 33):
                raise
            if time.monotonic() >= deadline:
                raise CheckpointError("Checkpoint pointer publication blocked") from error
            time.sleep(0.01)


@contextmanager
def _writer_lock(root: Path) -> Iterator[None]:
    with (root / ".writer.lock").open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise CheckpointError("Another checkpoint writer owns this root") from error
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == "win32":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def load_checkpoint(
    directory: Path,
    *,
    expected_config_hash: str | None,
    expected_seed: int | None,
    expected_reward_contract: RewardContract | None = None,
) -> CheckpointManifest:
    """Validate a checkpoint directory; heavy loading of model and stats is done by the trainer."""
    manifest = read_manifest(directory)
    check_compatible(
        manifest,
        expected_config_hash=expected_config_hash,
        expected_seed=expected_seed,
        expected_reward_contract=expected_reward_contract,
    )
    return manifest
