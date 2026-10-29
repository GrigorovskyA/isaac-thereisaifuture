from pathlib import Path

import pytest
import yaml

from isaac_threrisaifuture.checkpoints import (
    ACTION_SCHEMA_VERSION,
    CheckpointError,
    CheckpointManifest,
    config_hash,
    load_checkpoint,
    read_manifest,
    write_manifest,
)
from isaac_threrisaifuture.entities import OBSERVATION_SCHEMA_VERSION
from isaac_threrisaifuture.training import (
    EvalResult,
    TrainingConfigError,
    TrainingResult,
    load_training_config,
    main,
    run_seeds,
    select,
)

ROOT = Path(__file__).resolve().parents[1]


def manifest(**overrides: object) -> CheckpointManifest:
    fields: dict[str, object] = {
        "observation_schema_version": OBSERVATION_SCHEMA_VERSION,
        "action_schema_version": ACTION_SCHEMA_VERSION,
        "reward_schema_version": 1,
        "algorithm": "PPO",
        "config_hash": config_hash({"a": 1}),
        "seed": 7,
        "checkpoint_id": "abc-s7-t10",
        "parent_checkpoint_id": None,
        "timesteps": 10,
        "model_file": "model.zip",
        "normalizer_file": "vecnormalize.pkl",
        "rng_state": {},
    }
    fields.update(overrides)
    return CheckpointManifest.model_validate(fields)


def write_checkpoint(directory: Path, **overrides: object) -> CheckpointManifest:
    directory.mkdir(parents=True)
    (directory / "model.zip").write_bytes(b"x")
    (directory / "vecnormalize.pkl").write_bytes(b"x")
    value = manifest(**overrides)
    write_manifest(directory, value)
    return value


def test_shipped_config_validates() -> None:
    config, digest = load_training_config(ROOT / "configs" / "training-v1.yaml")
    assert config.budget.total_timesteps == 10000
    assert len(digest) == 64


def test_unknown_config_key_and_test_split_rejected(tmp_path: Path) -> None:
    text = (ROOT / "configs" / "training-v1.yaml").read_text("utf-8")
    bad = tmp_path / "bad.yaml"
    bad.write_text(text + "surprise: 1\n", "utf-8")
    with pytest.raises(TrainingConfigError):
        load_training_config(bad)
    held = tmp_path / "held.yaml"
    held.write_text(text.replace("split: validation", "split: test"), "utf-8")
    with pytest.raises(TrainingConfigError, match="held out"):
        load_training_config(held)


def test_compatible_checkpoint_loads(tmp_path: Path) -> None:
    saved = write_checkpoint(tmp_path / "ck")
    loaded = load_checkpoint(
        tmp_path / "ck", expected_config_hash=saved.config_hash, expected_seed=7
    )
    assert loaded == saved


@pytest.mark.parametrize(
    "overrides",
    [
        {"observation_schema_version": 1},
        {"observation_schema_version": 2},
        {"observation_schema_version": 7},
        {"action_schema_version": 1},
        {"reward_schema_version": 2},
        {"config_hash": config_hash({"a": 2})},
        {"seed": 8},
    ],
)
def test_incompatible_checkpoint_rejected(tmp_path: Path, overrides: dict[str, object]) -> None:
    write_checkpoint(tmp_path / "ck", **overrides)
    with pytest.raises(CheckpointError):
        load_checkpoint(
            tmp_path / "ck", expected_config_hash=config_hash({"a": 1}), expected_seed=7
        )


def test_missing_normalizer_file_and_corrupt_manifest_rejected(tmp_path: Path) -> None:
    write_checkpoint(tmp_path / "ck")
    (tmp_path / "ck" / "vecnormalize.pkl").unlink()
    with pytest.raises(CheckpointError, match="missing"):
        read_manifest(tmp_path / "ck")
    (tmp_path / "ck" / "manifest.json").write_text("{not json", "utf-8")
    with pytest.raises(CheckpointError, match="Invalid"):
        read_manifest(tmp_path / "ck")


def test_resume_without_checkpoint_is_an_explicit_error(tmp_path: Path) -> None:
    code = main(
        ["--resume", "--seed", "1", "--allow-template", "--out-dir", str(tmp_path)],
        env_factory=lambda seed: None,
    )
    assert code == 1
    report = (tmp_path / "seeds.json").read_text("utf-8")
    assert "No checkpoint to resume from" in report


def test_run_seeds_records_failures_and_all_seeds(tmp_path: Path) -> None:
    def fake(seed: int) -> TrainingResult:
        if seed == 2:
            raise RuntimeError("boom")
        return TrainingResult(seed, "completed", 10, "id", 0.1)

    records = run_seeds([1, 2, 3], fake, tmp_path / "r.json")
    assert [r["status"] for r in records] == ["ok", "failed", "ok"]
    assert (tmp_path / "r.json").is_file()


def test_selection_rule_threshold_and_episode_floor() -> None:
    baseline = EvalResult(episodes=100, cleared=30)
    accepted = select(EvalResult(episodes=100, cleared=50), baseline)
    assert accepted.accepted and accepted.improvement == pytest.approx(0.20)
    assert accepted.ci95_low < 0.20 < accepted.ci95_high
    assert not select(EvalResult(episodes=100, cleared=49), baseline).accepted
    few = select(EvalResult(episodes=99, cleared=99), EvalResult(episodes=100, cleared=0))
    assert not few.accepted and "fewer" in few.reason


def test_training_survives_episodes_that_finish_inside_a_rollout(tmp_path: Path) -> None:
    """Regression: the env's own info["episode"] summary crashed SB3 rollout logging."""
    import gymnasium as gym

    from isaac_threrisaifuture.env import IsaacCombatEnv
    from isaac_threrisaifuture.episodes import Scenario
    from isaac_threrisaifuture.sim import SyntheticRoomBackend
    from isaac_threrisaifuture.training import TrainingConfig, train

    finished: list[dict[str, object]] = []

    class Count(gym.Wrapper):  # type: ignore[type-arg]
        def step(self, action):  # type: ignore[no-untyped-def]
            result = super().step(action)
            if "episode" in result[4]:
                finished.append(result[4]["episode"])
            return result

    raw = yaml.safe_load((ROOT / "configs/training-live-v1.yaml").read_text("utf-8"))
    raw.update(n_steps=64, batch_size=64, n_epochs=1, lstm_hidden_size=8, status="test")
    raw["budget"] = {**raw["budget"], "total_timesteps": 64}
    short = Scenario("short", "train", 1, 30, enemy_count=1, enemy_hp=7.0)
    result = train(
        TrainingConfig.model_validate(raw),
        config_hash(raw),
        seed=1,
        env_factory=lambda _: Count(IsaacCombatEnv(SyntheticRoomBackend(), [short])),
        out_dir=tmp_path,
    )
    assert finished and "outcome" in finished[0]  # inner summary intact below Monitor
    assert result.stop_reason == "completed" and result.checkpoint_id is not None
