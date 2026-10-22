"""Process interruption and real synthetic continuation; never touches Isaac."""

import copy
import errno
import pickle
import random
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from isaac_threrisaifuture import checkpoints as cp

CFG = cp.config_hash({"fixture": "publication"})


@pytest.mark.parametrize("winerror", [5, 32, 33, None])
@pytest.mark.parametrize("persistent", [False, True])
def test_pointer_read_retries_only_bounded_windows_sharing(
    tmp_path, monkeypatch, winerror, persistent
):
    parent = save(tmp_path)
    if winerror is None:
        monkeypatch.setattr(cp, "sys", SimpleNamespace(platform="win32"))
    original_open = Path.open
    now, attempts = [0.0], []

    def open_pointer(path, *args, **kwargs):
        if path == tmp_path / cp.LATEST_POINTER:
            attempts.append(now[0])
            if persistent or len(attempts) < 4:
                error = PermissionError(errno.EACCES, "Windows sharing conflict")
                error.winerror = winerror
                raise error
        return original_open(path, *args, **kwargs)

    def sleep(seconds):
        now[0] += seconds

    monkeypatch.setattr(Path, "open", open_pointer)
    monkeypatch.setattr(cp.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(cp.time, "sleep", sleep)
    if persistent:
        with pytest.raises(cp.CheckpointError, match="Cannot read checkpoint pointer"):
            cp.latest_checkpoint_dir(tmp_path)
        assert 1 <= now[0] < 1.02
    else:
        assert cp.latest_checkpoint_dir(tmp_path).name == parent.checkpoint_id
        assert len(attempts) == 4 and now[0] == pytest.approx(0.03)


def test_pointer_read_unclassified_permission_error_fails_without_retry(tmp_path, monkeypatch):
    save(tmp_path)
    original_open = Path.open
    calls = []

    def open_pointer(path, *args, **kwargs):
        if path == tmp_path / cp.LATEST_POINTER:
            calls.append(path)
            raise PermissionError("Not a classified Windows sharing conflict")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_pointer)
    with pytest.raises(cp.CheckpointError, match="Cannot read checkpoint pointer"):
        cp.latest_checkpoint_dir(tmp_path)
    assert len(calls) == 1


def test_crt_permission_error_is_not_retried_on_other_platform(tmp_path, monkeypatch):
    save(tmp_path)
    monkeypatch.setattr(cp, "sys", SimpleNamespace(platform="linux"))
    original_open = Path.open
    calls = []

    def open_pointer(path, *args, **kwargs):
        if path == tmp_path / cp.LATEST_POINTER:
            calls.append(path)
            raise PermissionError(errno.EACCES, "Unclassified platform permission denial")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", open_pointer)
    with pytest.raises(cp.CheckpointError, match="Cannot read checkpoint pointer"):
        cp.latest_checkpoint_dir(tmp_path)
    assert len(calls) == 1


class Artifact:
    def __init__(self, value=b"1", fail=False):
        self.value, self.fail = value, fail

    def save(self, path):
        Path(path).write_bytes(self.value)
        if self.fail:
            raise KeyboardInterrupt("Interrupted artifact write")


def save(root, step=1, parent=None, **kwargs):
    return cp.save_checkpoint(
        root,
        model=kwargs.pop("model", Artifact(str(step).encode())),
        vec_normalize=kwargs.pop("vec_normalize", Artifact(str(step).encode())),
        algorithm="PPO",
        cfg_hash=CFG,
        seed=7,
        timesteps=step,
        parent_checkpoint_id=parent,
        rng_state={},
        **kwargs,
    )


def latest(root):
    directory = cp.latest_checkpoint_dir(root)
    manifest = cp.load_checkpoint(directory, expected_config_hash=CFG, expected_seed=7)
    assert (directory / manifest.model_file).read_bytes() == (
        directory / manifest.normalizer_file
    ).read_bytes()
    return manifest


@pytest.mark.parametrize(
    "phase", ["model", "normalizer", "flush", "manifest", "rename", "pointer", "after_pointer"]
)
def test_interruptions_never_publish_partial_state(tmp_path, monkeypatch, phase):
    root = tmp_path / "checkpoints"
    parent = save(root)
    original_manifest = cp.write_manifest
    original_rename = Path.rename
    original_pointer = cp._replace_pointer

    def interrupt(*args, **kwargs):
        raise KeyboardInterrupt("Injected publication interruption")

    if phase == "flush":
        monkeypatch.setattr(cp, "_sync_file", interrupt)
    elif phase == "manifest":

        def manifest(*args):
            original_manifest(*args)
            interrupt()

        monkeypatch.setattr(cp, "write_manifest", manifest)
    elif phase == "rename":

        def rename(path, target):
            if path.name.startswith(".pending-"):
                interrupt()
            return original_rename(path, target)

        monkeypatch.setattr(Path, "rename", rename)
    elif phase in ("pointer", "after_pointer"):

        def pointer(*args):
            if phase == "after_pointer":
                original_pointer(*args)
            interrupt()

        monkeypatch.setattr(cp, "_replace_pointer", pointer)
    with pytest.raises(KeyboardInterrupt):
        save(
            root,
            2,
            parent.checkpoint_id,
            model=Artifact(b"2", phase == "model"),
            vec_normalize=Artifact(b"2", phase == "normalizer"),
        )
    selected = latest(root)
    assert selected.timesteps == (2 if phase == "after_pointer" else 1)
    assert (root / parent.checkpoint_id / "model.zip").read_bytes() == b"1"
    assert not list(root.glob(".pending-*")) and not list(root.glob(".latest-*.tmp"))


def test_orphan_is_not_selected_or_overwritten_when_publication_retries(tmp_path, monkeypatch):
    parent = save(tmp_path)
    original = cp._replace_pointer

    def fail(*args):
        raise OSError("Pointer publication failed")

    monkeypatch.setattr(cp, "_replace_pointer", fail)
    with pytest.raises(OSError, match="publication failed"):
        save(tmp_path, 2, parent.checkpoint_id)
    orphan = tmp_path / f"{CFG[:8]}-s7-t2"
    assert cp.read_manifest(orphan).timesteps == 2
    assert latest(tmp_path).checkpoint_id == parent.checkpoint_id
    monkeypatch.setattr(cp, "_replace_pointer", original)
    child = save(
        tmp_path,
        2,
        parent.checkpoint_id,
        model=Artifact(b"retry"),
        vec_normalize=Artifact(b"retry"),
    )
    assert child.checkpoint_id != orphan.name
    assert (orphan / "model.zip").read_bytes() == b"2"
    assert latest(tmp_path).checkpoint_id == child.checkpoint_id


def test_concurrent_readers_only_observe_complete_generations(tmp_path):
    parent = save(tmp_path)
    stop = threading.Event()
    observed, errors = [], []

    def read():
        while not stop.is_set():
            try:
                observed.append(latest(tmp_path).timesteps)
            except BaseException as error:
                errors.append(error)
                stop.set()

    reader = threading.Thread(target=read)
    reader.start()
    try:
        for step in range(2, 9):
            parent = save(tmp_path, step, parent.checkpoint_id)
    finally:
        stop.set()
        reader.join(timeout=5)
    assert not reader.is_alive() and not errors
    assert observed and set(observed) <= set(range(1, 9))
    assert latest(tmp_path).timesteps == 8


def test_competing_and_stale_writers_cannot_replace_published_history(tmp_path):
    parent = save(tmp_path)
    with cp._writer_lock(tmp_path):
        with pytest.raises(cp.CheckpointError, match="writer"):
            save(tmp_path, 2, parent.checkpoint_id)
    child = save(tmp_path, 2, parent.checkpoint_id)
    with pytest.raises(cp.CheckpointError, match="Stale"):
        save(tmp_path, 3, parent.checkpoint_id)
    with pytest.raises(cp.CheckpointError, match="non-increasing"):
        save(tmp_path, 2, child.checkpoint_id)
    assert latest(tmp_path).checkpoint_id == child.checkpoint_id


def test_missing_pointer_with_completed_history_is_not_first_publication(tmp_path):
    parent = save(tmp_path)
    (tmp_path / cp.LATEST_POINTER).unlink()
    with pytest.raises(cp.CheckpointError, match="pointer missing"):
        save(tmp_path, 2, parent.checkpoint_id)
    assert (tmp_path / parent.checkpoint_id / "model.zip").read_bytes() == b"1"


@pytest.mark.parametrize("file", ["model.zip", "vecnormalize.pkl"])
def test_v2_hashes_reject_corruption_and_v1_remains_readable(tmp_path, file):
    saved = save(tmp_path)
    directory = tmp_path / saved.checkpoint_id
    assert saved.checkpoint_schema_version == 2
    (directory / file).write_bytes(b"corrupt")
    with pytest.raises(cp.CheckpointError, match="hash mismatch"):
        cp.load_checkpoint(directory, expected_config_hash=CFG, expected_seed=7)
    legacy = saved.model_copy(
        update={"checkpoint_schema_version": 1, "model_sha256": None, "normalizer_sha256": None}
    )
    cp.write_manifest(directory, legacy)
    # Legacy storage only declared existence/compatibility, not embedded hashes.
    assert cp.load_checkpoint(directory, expected_config_hash=CFG, expected_seed=7) == legacy


@pytest.mark.parametrize("pointer", ["", "../escape", ".pending-crash", "x" * 300, "missing"])
def test_latest_never_discovers_unpublished_or_external_state(tmp_path, pointer):
    save(tmp_path)
    (tmp_path / cp.LATEST_POINTER).write_text(pointer)
    with pytest.raises(cp.CheckpointError):
        cp.latest_checkpoint_dir(tmp_path)


def test_v2_pointer_identity_is_strict_and_legacy_alias_stays_readable(tmp_path):
    saved = save(tmp_path)
    alias = tmp_path / "legacy-alias"
    (tmp_path / saved.checkpoint_id).rename(alias)
    (tmp_path / cp.LATEST_POINTER).write_text(alias.name)
    with pytest.raises(cp.CheckpointError, match="identity mismatch"):
        cp.latest_checkpoint_dir(tmp_path)
    legacy = saved.model_copy(
        update={"checkpoint_schema_version": 1, "model_sha256": None, "normalizer_sha256": None}
    )
    cp.write_manifest(alias, legacy)
    assert cp.latest_checkpoint_dir(tmp_path) == alias
    assert cp.read_manifest(alias).checkpoint_id == saved.checkpoint_id


def test_killed_writer_releases_os_lock_and_ignores_partial_stage(tmp_path):
    parent = save(tmp_path)
    marker = tmp_path / "writer-ready"
    script = """
import sys,time
from pathlib import Path
from isaac_threrisaifuture.checkpoints import save_checkpoint
root,marker,cfg,parent=map(str,sys.argv[1:])
class Interrupted:
 def save(self,path):
  Path(path).write_bytes(b'partial')
  Path(marker).touch()
  time.sleep(30)
save_checkpoint(Path(root),model=Interrupted(),vec_normalize=Interrupted(),algorithm='PPO',
 cfg_hash=cfg,seed=7,timesteps=2,parent_checkpoint_id=parent,rng_state={})
"""
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(tmp_path), str(marker), CFG, parent.checkpoint_id],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    try:
        deadline = time.monotonic() + 10
        while not marker.exists() and time.monotonic() < deadline:
            assert process.poll() is None
            time.sleep(0.02)
        assert marker.exists()
    finally:
        process.terminate()
        process.wait(timeout=5)
    assert list(tmp_path.glob(".pending-*"))
    assert latest(tmp_path).checkpoint_id == parent.checkpoint_id
    child = save(tmp_path, 2, parent.checkpoint_id)
    assert latest(tmp_path).checkpoint_id == child.checkpoint_id


def test_partial_artifacts_refuse_fresh_initialization_before_environment(tmp_path):
    from test_checkpoint_policy import RAW_CONFIG

    from isaac_threrisaifuture.training import TrainingConfig, train

    root = tmp_path / "checkpoints"
    (root / ".pending-crash").mkdir(parents=True)
    called = []
    for resume in (False, True):
        with pytest.raises(cp.CheckpointError):
            train(
                TrainingConfig.model_validate(RAW_CONFIG),
                cp.config_hash(RAW_CONFIG),
                seed=7,
                env_factory=lambda _: called.append(True),
                out_dir=tmp_path,
                resume=resume,
            )
    assert called == []


@pytest.fixture
def actual(tmp_path):
    from test_checkpoint_policy import RAW_CONFIG, synthetic_env

    from isaac_threrisaifuture.training import TrainingConfig, train

    raw = copy.deepcopy(RAW_CONFIG)
    raw["budget"]["total_timesteps"] = 64
    config, cfg = TrainingConfig.model_validate(raw), cp.config_hash(raw)
    first = train(
        config, cfg, seed=7, env_factory=synthetic_env, out_dir=tmp_path, max_timesteps=32
    )
    directory = tmp_path / "checkpoints" / first.checkpoint_id
    return config, cfg, directory, tmp_path, synthetic_env


def assert_state_equal(left, right):
    import torch

    if isinstance(left, torch.Tensor):
        assert torch.equal(left, right)
    elif isinstance(left, dict):
        assert left.keys() == right.keys()
        for key in left:
            assert_state_equal(left[key], right[key])
    elif isinstance(left, (list, tuple)):
        assert len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            assert_state_equal(a, b)
    else:
        assert left == right


def test_real_resume_restores_optimizer_normalizer_rng_then_saves_update(actual, monkeypatch):
    import torch
    from sb3_contrib import RecurrentPPO

    from isaac_threrisaifuture.training import train

    config, cfg, directory, out, env = actual
    manifest = cp.read_manifest(directory)
    reference = RecurrentPPO.load(directory / "model.zip", device="cpu")
    optimizer = copy.deepcopy(reference.policy.optimizer.state_dict())
    assert optimizer["state"]
    with (directory / "vecnormalize.pkl").open("rb") as stream:
        normalizer = pickle.load(stream)
    observed = []
    original = RecurrentPPO.learn

    def learn(model, *args, **kwargs):
        assert model.num_timesteps == 32
        assert_state_equal(model.policy.optimizer.state_dict(), optimizer)
        stats = model.get_vec_normalize_env().obs_rms
        np.testing.assert_array_equal(stats.mean, normalizer.obs_rms.mean)
        np.testing.assert_array_equal(stats.var, normalizer.obs_rms.var)
        assert stats.count == normalizer.obs_rms.count
        assert cp.capture_rng_state() == {
            k: v for k, v in manifest.rng_state.items() if k != "torch"
        }
        assert torch.equal(
            torch.get_rng_state(), torch.tensor(manifest.rng_state["torch"], dtype=torch.uint8)
        )
        observed.append(True)
        return original(model, *args, **kwargs)

    monkeypatch.setattr(RecurrentPPO, "learn", learn)
    random.random(), np.random.random(), torch.rand(3)
    result = train(config, cfg, seed=7, env_factory=env, out_dir=out, resume=True)
    assert observed == [True] and result.timesteps == 64
    child = cp.read_manifest(out / "checkpoints" / result.checkpoint_id)
    assert child.parent_checkpoint_id == manifest.checkpoint_id
    updated = RecurrentPPO.load(out / "checkpoints" / result.checkpoint_id / "model.zip")
    assert any(
        not torch.equal(value, updated.policy.state_dict()[key])
        for key, value in reference.policy.state_dict().items()
    )


def test_failed_heavy_restore_closes_environment_and_never_initializes(actual, monkeypatch):
    from sb3_contrib import RecurrentPPO

    from isaac_threrisaifuture.training import train

    config, cfg, directory, out, factory = actual
    environments = []

    def env(seed):
        value = factory(seed)
        original = value.close

        def close():
            environments.append("closed")
            original()

        value.close = close
        return value

    def fail(*args, **kwargs):
        raise ValueError("Heavy restore failed")

    monkeypatch.setattr(RecurrentPPO, "load", fail)
    with pytest.raises(ValueError, match="Heavy restore failed"):
        train(config, cfg, seed=7, env_factory=env, out_dir=out, resume=True)
    assert environments == ["closed"]
    assert cp.latest_checkpoint_dir(out / "checkpoints") == directory
