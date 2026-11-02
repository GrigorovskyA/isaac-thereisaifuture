"""OFFLINE tests for Prioritized Level Replay over run seeds (contract `level_replay: plr_v1`): the
sampler, eviction and score attribution of the seed bank, its checkpoint round trip, the contract
hash, the live backend's seed plumbing, the learner's scoring and the episode columns. Synthetic
runs prove plumbing only, never Isaac play."""

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from test_live import SESSION, live
from test_pure_training import RAW, run, write_config
from test_stall_watchdog import Clock, FakeClient

from isaac_threrisaifuture.actions import Command
from isaac_threrisaifuture.checkpoints import CheckpointError, latest_checkpoint_dir, read_manifest
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import (
    FIELDS,
    LEVEL_REPLAY_FIELDS,
    PRE_LEVEL_REPLAY_HEADER,
    EpisodeMetricsWriter,
)
from isaac_threrisaifuture.level_replay import (
    LEVEL_REPLAY_FILE,
    SEED_ALPHABET,
    LevelReplayError,
    SeedBank,
    valid_seed,
)
from isaac_threrisaifuture.live import LIVE_SCENARIO, LiveBackend
from isaac_threrisaifuture.observation import ProtocolError
from isaac_threrisaifuture.scenarios import Scenario
from isaac_threrisaifuture.sim import SyntheticRoomBackend
from isaac_threrisaifuture.training import (
    PURE_CONFIG,
    TrainingConfigError,
    contract_hash,
    load_training_config,
)

NEXT_LINEAGE_HASH = "54be12af1dcec7f0ade2dc109cbcb2f90b71d6e58cb7d51d17b3b704fa4859cc"
SEEDS = ["AAAA BBBB", "CCCC DDDD", "EEEE FFFF", "GGGG HHHH", "JJJJ KKKK", "LLLL MMMM"]
TOY = Scenario("toy", "validation", 1, 90, enemy_count=2, enemy_hp=7.0)


def bank(**kwargs: Any) -> SeedBank:
    options = dict(replay_probability=1.0, temperature=1.0, staleness=0.0, capacity=10)
    return SeedBank(**{**options, **kwargs})


def scored(values: dict[str, float], **kwargs: Any) -> SeedBank:
    """A bank whose seeds were each played once and scored with `values`."""
    seeds = bank(**kwargs)
    for epoch, (seed, score) in enumerate(values.items(), start=1):
        seeds.begin_run(seed, epoch)
        seeds.score_rollout([seeds.current_run], np.array([score]))
    return seeds


# --- seed strings ------------------------------------------------------------------------------


def test_seed_strings_follow_the_game_alphabet():
    assert len(SEED_ALPHABET) == 32 and not set("IOU5") & set(SEED_ALPHABET)
    assert valid_seed("T1MM AY48") and valid_seed("GGGG GGGG")
    for bad in ("t1mm ay48", "T1MMAY48", "T1MM  AY48", "IIII AAAA", "5AAA AAAA", "OAAA AAAA",
                "AAAA AAA", "AAAA AAAAA", "AAAA\tAAAA", "AAAA AAAA\n", None, 12345678):  # fmt: skip
        assert not valid_seed(bad), bad


def test_commands_carry_a_seed_only_on_restart_and_next_seed():
    values = dict(session_id=SESSION, sequence=1, game_epoch=1, room_visit=1, frame_id=5)
    plain = Command(**values, kind="restart")
    assert b"seed" not in plain.wire_bytes()  # the earlier protocol, byte for byte
    seeded = Command(**values, kind="restart", seed="T1MM AY48")
    assert json.loads(seeded.wire_bytes())["seed"] == "T1MM AY48"
    assert seeded.wire_bytes().endswith(b',"frames":0,"seed":"T1MM AY48"}\n')
    Command(**values, kind="next_seed", seed="T1MM AY48")
    with pytest.raises(ProtocolError):
        Command(**values, kind="next_seed")
    with pytest.raises(ProtocolError):
        Command(**values, kind="heartbeat", seed="T1MM AY48")
    with pytest.raises(ValueError):
        Command(**values, kind="restart", seed="t1mm ay48")


# --- sampler -----------------------------------------------------------------------------------


def test_rank_prioritization_follows_the_temperature():
    seeds = scored({"AAAA BBBB": 0.1, "CCCC DDDD": 3.0, "EEEE FFFF": 1.0}, temperature=1.0)
    names, p = seeds.probabilities()
    weights = {"CCCC DDDD": 1.0, "EEEE FFFF": 1 / 2, "AAAA BBBB": 1 / 3}  # 1 / rank
    total = sum(weights.values())
    assert dict(zip(names, p, strict=True)) == pytest.approx(
        {name: w / total for name, w in weights.items()}
    )
    sharp = scored({"AAAA BBBB": 0.1, "CCCC DDDD": 3.0, "EEEE FFFF": 1.0}, temperature=0.1)
    names, p = sharp.probabilities()
    best = dict(zip(names, p, strict=True))["CCCC DDDD"]
    assert best == pytest.approx(1 / (1 + 2**-10 + 3**-10)) and best > 0.999


def test_staleness_mixes_in_the_runs_since_a_seed_was_last_played():
    seeds = scored({"AAAA BBBB": 1.0, "CCCC DDDD": 2.0}, temperature=1.0, staleness=0.5)
    # Run counter 2: AAAA BBBB started at run 1 (age 1), CCCC DDDD at run 2 (age 0).
    names, p = seeds.probabilities()
    by_score = {"CCCC DDDD": 2 / 3, "AAAA BBBB": 1 / 3}
    by_age = {"AAAA BBBB": 1.0, "CCCC DDDD": 0.0}
    expected = {name: 0.5 * by_score[name] + 0.5 * by_age[name] for name in names}
    assert dict(zip(names, p, strict=True)) == pytest.approx(expected)
    assert p.sum() == pytest.approx(1.0)


def test_only_scored_seeds_are_replayed_and_the_replay_probability_holds():
    seeds = bank(replay_probability=0.5)
    seeds.begin_run("AAAA BBBB", 1)  # in the bank, but not scored yet
    assert seeds.probabilities()[0] == [] and seeds.plan_next() is None
    seeds.score_rollout([seeds.current_run], np.array([1.0]))
    plans = []
    for epoch in range(2, 402):
        seeds.begin_run(None, epoch)  # a run without a readable seed keeps the bank unchanged
        plans.append(seeds.planned_seed)
    assert set(plans) == {None, "AAAA BBBB"}
    assert 0.4 < plans.count("AAAA BBBB") / len(plans) < 0.6


def test_the_plan_depends_only_on_the_lineage_seed_and_the_run_counter():
    def plans(seed: int) -> list[str | None]:
        seeds = scored(dict(zip(SEEDS[:3], (1.0, 2.0, 3.0), strict=True)), seed=seed)
        seeds.replay_probability = 0.5
        result = []
        for epoch in range(10, 40):
            seeds.begin_run(None, epoch)
            result.append(seeds.planned_seed)
        return result

    assert plans(1) == plans(1) and plans(1) != plans(2)


# --- runs, eviction and scores -----------------------------------------------------------------


def test_new_runs_join_the_bank_and_replays_are_flagged():
    seeds = bank()
    assert seeds.begin_run("AAAA BBBB", 1) and seeds.facts() == {
        "run_seed": "AAAA BBBB", "seed_replayed": 0,
    }  # fmt: skip
    assert not seeds.begin_run("AAAA BBBB", 1)  # a reconnect or fault reset in the same run
    assert seeds.runs == 1
    assert seeds.begin_run("AAAA BBBB", 2)  # a new run of a known seed is a replay
    assert seeds.facts() == {"run_seed": "AAAA BBBB", "seed_replayed": 1}
    assert seeds.begin_run("not a seed", 3) and seeds.facts() == {
        "run_seed": None, "seed_replayed": 0,
    }  # fmt: skip
    assert len(seeds) == 1 and seeds.entries["AAAA BBBB"].last_run == 2


def test_a_full_bank_evicts_the_lowest_score_then_the_oldest_and_keeps_unscored_seeds():
    seeds = scored({"AAAA BBBB": 2.0, "CCCC DDDD": 1.0, "EEEE FFFF": 1.0}, capacity=3)
    seeds.begin_run("GGGG HHHH", 4)  # lowest score 1.0, of those the older CCCC DDDD goes
    assert set(seeds.entries) == {"AAAA BBBB", "EEEE FFFF", "GGGG HHHH"}
    seeds.begin_run("JJJJ KKKK", 5)  # unscored GGGG HHHH stays; EEEE FFFF (1.0) goes
    assert set(seeds.entries) == {"AAAA BBBB", "GGGG HHHH", "JJJJ KKKK"}
    assert seeds.entries["GGGG HHHH"].score is None


def test_scores_accumulate_over_runs_that_span_rollouts():
    seeds = bank()
    seeds.begin_run("AAAA BBBB", 1)
    first = seeds.current_run
    seeds.begin_run("CCCC DDDD", 2)
    second = seeds.current_run
    # Rollout 1: two steps of the first run, then two of the second.
    assert seeds.score_rollout([first, first, second, second], np.array([1.0, -3.0, 2.0, 2.0])) == 4
    assert seeds.entries["AAAA BBBB"].score == pytest.approx(2.0)
    assert seeds.entries["CCCC DDDD"].score == pytest.approx(2.0)
    # Rollout 2: the second run goes on; its score is the mean over all of its trained steps.
    seeds.score_rollout([second, second, None], np.array([-5.0, 7.0, 100.0]))
    assert seeds.entries["CCCC DDDD"].score == pytest.approx((2 + 2 + 5 + 7) / 4)
    assert seeds.entries["AAAA BBBB"].score == pytest.approx(2.0)  # closed, unchanged
    assert first not in seeds._scores  # a run that can get no more steps is dropped
    # A replay of the first seed starts a new run whose own steps replace the old score.
    seeds.begin_run("AAAA BBBB", 3)
    seeds.score_rollout([seeds.current_run], np.array([0.5]))
    assert seeds.entries["AAAA BBBB"].score == pytest.approx(0.5)
    with pytest.raises(ValueError):
        seeds.score_rollout([seeds.current_run], np.array([1.0, 2.0]))


def test_seed_bank_round_trip_and_corrupt_files(tmp_path):
    seeds = scored({"AAAA BBBB": 2.0, "CCCC DDDD": 1.0})
    seeds.begin_run("EEEE FFFF", 3)  # unscored
    path = tmp_path / LEVEL_REPLAY_FILE
    seeds.save(path)
    loaded = bank()
    loaded.load(path)
    assert loaded.entries == seeds.entries and loaded.runs == seeds.runs == 3
    assert loaded.current_run is None  # open runs are not learner state
    smaller = bank(capacity=1)
    smaller.load(path)
    # Evicted down to the capacity: scored seeds go first, the unscored one stays.
    assert list(smaller.entries) == ["EEEE FFFF"]
    good = json.loads(path.read_text("utf-8"))
    for broken in (
        {**good, "format": 2},
        {**good, "entries": [["bad seed", 1.0, 1, 1]]},
        {**good, "entries": [["AAAA BBBB", -1.0, 1, 1]]},
        {**good, "entries": [["AAAA BBBB", 1.0, 9, 1]]},
        {**good, "entries": [["AAAA BBBB", 1.0, 1, 1], ["AAAA BBBB", 1.0, 1, 1]]},
        {"format": 1},
    ):
        path.write_text(json.dumps(broken), "utf-8")
        with pytest.raises(LevelReplayError):
            bank().load(path)
    path.write_text("{", "utf-8")
    with pytest.raises(LevelReplayError):
        bank().load(path)


# --- contract ----------------------------------------------------------------------------------


def test_level_replay_none_keeps_the_next_lineage_hash(tmp_path):
    config, digest = load_training_config(PURE_CONFIG)
    assert config.contract.level_replay == "none" and digest == NEXT_LINEAGE_HASH
    explicit = dict(RAW, contract={**RAW["contract"], "level_replay": "none"})
    path = tmp_path / "explicit.yaml"
    path.write_text(json.dumps(explicit), "utf-8")  # YAML is a superset of JSON
    assert load_training_config(path)[1] == NEXT_LINEAGE_HASH
    assert contract_hash({**RAW["contract"], "level_replay": "plr_v1"}) != NEXT_LINEAGE_HASH
    hyper = config.hyperparameters
    assert (hyper.plr_replay_probability, hyper.plr_temperature) == (0.5, 0.1)
    assert (hyper.plr_staleness, hyper.plr_bank_size) == (0.1, 500)
    for bad in ({"plr_replay_probability": 1.5}, {"plr_temperature": 0.0}, {"plr_bank_size": 0}):
        with pytest.raises(TrainingConfigError):
            load_training_config(write_config(tmp_path / "bad.yaml", hyperparameters=bad))
    with pytest.raises(TrainingConfigError):
        load_training_config(write_config(tmp_path / "x.yaml", contract={"level_replay": "plr"}))


def test_plr_hyperparameters_are_not_hashed_and_recorded_only_under_plr(tmp_path):
    base = load_training_config(
        write_config(tmp_path / "a.yaml", contract={"level_replay": "plr_v1"})
    )
    tuned = load_training_config(
        write_config(
            tmp_path / "b.yaml",
            contract={"level_replay": "plr_v1"},
            hyperparameters={"plr_replay_probability": 0.25, "plr_bank_size": 50},
        )
    )
    assert base[1] == tuned[1]
    out = tmp_path / "none"
    run(write_config(tmp_path / "none.yaml"), out, 32)
    manifest = read_manifest(latest_checkpoint_dir(out / "checkpoints"))
    assert manifest.hyperparameters is not None
    assert not any(name.startswith("plr_") for name in manifest.hyperparameters)
    assert manifest.level_replay_file is None


# --- learner and checkpoints -------------------------------------------------------------------


class SeededSyntheticBackend(SyntheticRoomBackend):
    """Synthetic rooms that report a run seed per episode, as the live backend does."""

    def __init__(self, seeds: SeedBank) -> None:
        super().__init__()
        self.seeds = seeds
        self.episodes = 0

    def start_episode(self, scenario: Scenario, seed: int | None) -> Any:
        result = super().start_episode(scenario, seed)
        self.episodes += 1
        self.seeds.begin_run(SEEDS[self.episodes % 3], self.episodes)
        return result

    @property
    def level_replay_run(self) -> int | None:
        return self.seeds.current_run

    def level_replay_facts(self) -> dict[str, Any]:
        return self.seeds.facts()


def plr_run(tmp_path: Path, seeds: SeedBank, steps: int, **kwargs: Any) -> Any:
    path = write_config(tmp_path / "plr.yaml", contract={"level_replay": "plr_v1"})

    def factory(_: int = 0) -> IsaacCombatEnv:
        return IsaacCombatEnv(SeededSyntheticBackend(seeds), [TOY])

    return _train(path, tmp_path / "run", steps, factory, seeds, **kwargs)


def _train(path: Path, out: Path, steps: int, factory: Any, seeds: SeedBank, **kwargs: Any) -> Any:
    from isaac_threrisaifuture.training import train

    config, digest = load_training_config(path)
    return train(
        config, digest, seed=1, env_factory=factory, out_dir=out, max_timesteps=steps,
        reward_contract="pure-v11", level_replay=seeds, **kwargs,
    )  # fmt: skip


def test_the_learner_scores_the_seeds_and_checkpoints_save_and_restore_the_bank(tmp_path):
    seeds = SeedBank(capacity=10, seed=1)
    plr_run(tmp_path, seeds, 64)
    assert seeds.runs >= 2 and len(seeds) >= 1
    assert all(entry.score is not None and entry.score > 0 for entry in seeds.entries.values())
    directory = latest_checkpoint_dir(tmp_path / "run" / "checkpoints")
    manifest = read_manifest(directory)
    assert manifest.level_replay_file == LEVEL_REPLAY_FILE and manifest.level_replay_sha256
    assert manifest.hyperparameters is not None
    assert manifest.hyperparameters["plr_bank_size"] == 500  # recorded under plr_v1
    saved = json.loads((directory / LEVEL_REPLAY_FILE).read_text("utf-8"))
    assert saved["runs"] == seeds.runs
    # Resume restores the saved bank before the first new rollout.
    resumed = SeedBank(capacity=10, seed=1)
    plr_run(tmp_path, resumed, 96, resume=True)
    assert resumed.runs > saved["runs"]
    assert set(saved_seed for saved_seed, *_ in saved["entries"]) <= set(resumed.entries)


def test_resume_refuses_a_checkpoint_without_the_seed_bank_and_a_bank_needs_plr(tmp_path):
    seeds = SeedBank(capacity=10, seed=1)
    plr_run(tmp_path, seeds, 32)
    directory = latest_checkpoint_dir(tmp_path / "run" / "checkpoints")
    (directory / LEVEL_REPLAY_FILE).unlink()
    with pytest.raises(CheckpointError, match="missing"):
        plr_run(tmp_path, SeedBank(), 64, resume=True)
    with pytest.raises(TrainingConfigError, match="seed bank"):
        run(write_config(tmp_path / "none.yaml"), tmp_path / "other", 32, level_replay=SeedBank())
    with pytest.raises(TrainingConfigError, match="seed bank"):
        run(
            write_config(tmp_path / "p.yaml", contract={"level_replay": "plr_v1"}),
            tmp_path / "o",
            32,
        )


def test_a_manifest_without_the_bank_file_is_refused_on_plr_resume(tmp_path):
    seeds = SeedBank(capacity=10, seed=1)
    plr_run(tmp_path, seeds, 32)
    directory = latest_checkpoint_dir(tmp_path / "run" / "checkpoints")
    manifest = json.loads((directory / "manifest.json").read_text("utf-8"))
    manifest.update(level_replay_file=None, level_replay_sha256=None)
    (directory / "manifest.json").write_text(json.dumps(manifest), "utf-8")
    with pytest.raises(CheckpointError, match="no seed bank"):
        plr_run(tmp_path, SeedBank(), 64, resume=True)


# --- live backend ------------------------------------------------------------------------------


class SeedClient(FakeClient):
    """FakeClient whose snapshots carry a run seed and whose commands record their seed."""

    def __init__(self, clock: Clock, seed: str | None) -> None:
        super().__init__(clock)
        self.seed = seed
        self.seeds: list[tuple[str, str | None]] = []

    def _snapshot(self) -> Any:
        snap = super()._snapshot()
        oracle = snap.oracle.model_copy(update={"run_seed": self.seed})
        return snap.model_copy(update={"oracle": oracle})

    def command(self, kind: str, reference: Any, **kwargs: Any) -> Any:
        self.seeds.append((kind, kwargs.get("seed")))
        return super().command(kind, reference, **kwargs)


def test_the_live_backend_arms_the_planned_seed_and_seeds_the_stall_restart():
    seeds = scored({"CCCC DDDD": 1.0})
    client = SeedClient(Clock(), "AAAA BBBB")
    backend = LiveBackend(client, level_replay=seeds)  # type: ignore[arg-type]
    backend.start_episode(LIVE_SCENARIO, None)
    assert backend.level_replay_facts() == {"run_seed": "AAAA BBBB", "seed_replayed": 0}
    assert seeds.planned_seed == "CCCC DDDD" and backend.level_replay_run == seeds.runs
    backend.step(_still(), 6)
    backend.step(_still(), 6)
    assert client.seeds[0] == ("next_seed", "CCCC DDDD")  # armed once, before the first action
    assert [kind for kind, _ in client.seeds].count("next_seed") == 1
    assert backend.request_restart()
    assert client.seeds[-1] == ("restart", "CCCC DDDD")


def test_refused_arming_is_retried_a_bounded_number_of_times():
    seeds = scored({"CCCC DDDD": 1.0})
    client = SeedClient(Clock(), "AAAA BBBB")
    client.status = "rejected"
    backend = LiveBackend(client, level_replay=seeds)  # type: ignore[arg-type]
    backend.start_episode(LIVE_SCENARIO, None)
    for _ in range(30):
        backend.step(_still(), 6)
    from isaac_threrisaifuture.live import ARM_ATTEMPTS

    assert [kind for kind, _ in client.seeds].count("next_seed") == ARM_ATTEMPTS


def test_without_level_replay_no_seed_is_ever_sent():
    client = SeedClient(Clock(), None)
    backend = LiveBackend(client)  # type: ignore[arg-type]
    backend.start_episode(LIVE_SCENARIO, None)
    backend.step(_still(), 6)
    assert backend.request_restart()
    assert all(seed is None for _, seed in client.seeds) and "next_seed" not in client.sent
    assert backend.level_replay_facts() == {} and backend.level_replay_run is None


def _still() -> Any:
    from isaac_threrisaifuture.episodes import Action

    return Action(0, 0, 0)


def test_the_run_seed_is_metadata_and_never_reaches_the_observation():
    from isaac_threrisaifuture.encoding import encode

    plain = live(3)
    seeded = plain.model_copy(
        update={"oracle": plain.oracle.model_copy(update={"run_seed": "T1MM AY48"})}
    )
    assert plain.entity_frame is not None and seeded.entity_frame is not None
    assert np.array_equal(encode(plain.entity_frame).vector, encode(seeded.entity_frame).vector)


# --- episode metrics ---------------------------------------------------------------------------


def test_episodes_csv_gains_the_level_replay_columns_and_upgrades_once(tmp_path):
    assert FIELDS[-3:] == (*LEVEL_REPLAY_FIELDS, "wall_time")
    path = tmp_path / "episodes.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(PRE_LEVEL_REPLAY_HEADER)
        writer.writerow(["7" if name == "episode_id" else "x" for name in PRE_LEVEL_REPLAY_HEADER])
    metrics = EpisodeMetricsWriter(path)
    EpisodeMetricsWriter(path)
    metrics.write({"episode_id": 8, "run_seed": "T1MM AY48", "seed_replayed": 1})
    metrics.write({"episode_id": 9})  # level replay off
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert [row["episode_id"] for row in rows] == ["7", "8", "9"]
    assert (rows[0]["run_seed"], rows[0]["seed_replayed"]) == ("", "")
    assert (rows[1]["run_seed"], rows[1]["seed_replayed"]) == ("T1MM AY48", "1")
    assert (rows[2]["run_seed"], rows[2]["seed_replayed"]) == ("", "")


def test_episode_summaries_carry_the_run_seed_only_under_level_replay():
    seeds = bank()
    env = IsaacCombatEnv(SeededSyntheticBackend(seeds), [TOY])
    env.reset(seed=1)
    for _ in range(500):
        _, _, terminated, truncated, info = env.step(np.array([0, 0, 0]))
        assert info["level_replay_run"] == seeds.current_run
        if terminated or truncated:
            break
    summary = info["episode_summary"]
    assert summary["run_seed"] in SEEDS and summary["seed_replayed"] == 0
    plain = IsaacCombatEnv(SyntheticRoomBackend(), [TOY])
    plain.reset(seed=1)
    _, _, _, _, info = plain.step(np.array([0, 0, 0]))
    assert "level_replay_run" not in info
