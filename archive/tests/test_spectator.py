"""OFFLINE spectator tests on the toy simulator. Nothing here says anything about Isaac."""

import json
from pathlib import Path

import pytest

from isaac_threrisaifuture.baselines import RandomPolicy
from isaac_threrisaifuture.checkpoints import (
    CheckpointError,
    CheckpointManifest,
    write_manifest,
)
from isaac_threrisaifuture.entities import OBSERVATION_SCHEMA_VERSION, EntityFrame
from isaac_threrisaifuture.episodes import Scenario
from isaac_threrisaifuture.recording import JsonlRecorder, open_replay
from isaac_threrisaifuture.spectator import (
    format_checkpoints,
    list_checkpoints,
    main,
    resolve_policy,
    spectate,
    synthetic_env_factory,
)

EASY = Scenario("easy", "validation", 1, 300, enemy_count=1, enemy_hp=3.5)


def make_checkpoint(
    root: Path, name: str, *, timesteps: int, obs_version: int | None = None
) -> Path:
    directory = root / name
    directory.mkdir()
    (directory / "model.zip").write_bytes(b"x")
    (directory / "vecnormalize.pkl").write_bytes(b"x")
    write_manifest(
        directory,
        CheckpointManifest(
            observation_schema_version=obs_version or OBSERVATION_SCHEMA_VERSION,
            action_schema_version=1,
            reward_schema_version=1,
            algorithm="ppo",
            config_hash="a" * 64,
            seed=1,
            checkpoint_id=name,
            parent_checkpoint_id=None if timesteps == 100 else "ck-100",
            timesteps=timesteps,
            model_file="model.zip",
            normalizer_file="vecnormalize.pkl",
            rng_state={},
        ),
    )
    return directory


def watch(**kwargs: object) -> list[str]:
    return list(
        spectate(  # type: ignore[arg-type]
            RandomPolicy(), synthetic_env_factory, EASY, mode="random", **kwargs
        )
    )


def test_listing_flags_incompatible_and_reads_eval(tmp_path: Path):
    make_checkpoint(tmp_path, "ck-100", timesteps=100)
    good = make_checkpoint(tmp_path, "ck-200", timesteps=200)
    make_checkpoint(tmp_path, "ck-old", timesteps=50, obs_version=OBSERVATION_SCHEMA_VERSION + 1)
    (tmp_path / "ck-bad").mkdir()
    (tmp_path / "ck-bad" / "manifest.json").write_text("{", "utf-8")
    (good / "report.json").write_text(
        json.dumps({"overall": {"clear_rate": 0.5, "valid": 10}}), "utf-8"
    )
    listed = list_checkpoints(tmp_path)
    entries = {e.directory: e for e in listed}
    assert set(entries) == {"ck-100", "ck-200", "ck-old", "ck-bad"}
    assert entries["ck-200"].compatible and entries["ck-200"].clear_rate == 0.5
    assert entries["ck-200"].parent_checkpoint_id == "ck-100"
    assert not entries["ck-old"].compatible
    assert "observation_schema_version" in str(entries["ck-old"].problem)
    assert not entries["ck-bad"].compatible
    text = "\n".join(format_checkpoints(listed))
    assert "INCOMPATIBLE" in text and "0.500(10)" in text


def test_incompatible_checkpoint_is_rejected_for_watching(tmp_path: Path):
    make_checkpoint(tmp_path, "ck-old", timesteps=50, obs_version=OBSERVATION_SCHEMA_VERSION + 1)
    with pytest.raises(CheckpointError):
        resolve_policy("checkpoint:ck-old", checkpoints=tmp_path, loader=lambda _: RandomPolicy())
    assert main(["watch", "--mode", "checkpoint:ck-old", "--checkpoints", str(tmp_path)]) == 2


def test_watch_output_is_deterministic_and_ends_with_summary():
    first, second = watch(seed=3, max_steps=40), watch(seed=3, max_steps=40)
    assert first == second
    assert first[0].startswith("watch mode=random") and first[-1].startswith("summary ")
    assert watch(seed=4, max_steps=40) != first


def test_max_steps_stops_and_releases_control():
    lines = watch(seed=1, max_steps=2)
    assert "outcome=stopped" in lines[-1] and "steps=2" in lines[-1]


def test_output_and_recording_have_no_oracle_data(tmp_path: Path):
    path = tmp_path / "frames.jsonl"
    with JsonlRecorder(path, "policy_frames", "synthetic") as recorder:
        lines = watch(seed=2, max_steps=30, recorder=recorder)
    for line in lines:
        assert "oracle" not in line.lower() and "reward_components" not in line
    manifest, records = open_replay(path, "policy_frames")
    frames = list(records)
    assert manifest.stream == "policy_frames" and frames
    assert all(isinstance(f, EntityFrame) for f in frames)


def test_unknown_mode_and_real_game_refused(capsys: pytest.CaptureFixture[str]):
    assert main(["watch", "--mode", "bogus"]) == 2
    assert main(["watch", "--mode", "random", "--game"]) == 2
    assert "refusing to control a game" in capsys.readouterr().err


def test_cli_watch_labels_synthetic_backend():
    out: list[str] = []
    assert main(["watch", "--mode", "scripted-baseline", "--max-steps", "5"], out=out.append) == 0
    assert out[0].startswith("# SYNTHETIC") and "mode=scripted-baseline" in out[1]
