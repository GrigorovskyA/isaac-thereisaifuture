"""Conservative live reward continuity, tested without the game or model training."""

from pathlib import Path

import numpy as np
import pytest
from test_live import kinds, live
from test_training_manifest import write_checkpoint

from isaac_threrisaifuture.checkpoints import CheckpointError, load_checkpoint, save_checkpoint
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episodes import EpisodeFault, Scenario, StepResult
from isaac_threrisaifuture.live import EventDeriver
from isaac_threrisaifuture.rewards import CombatCoefficients, RewardLedger
from isaac_threrisaifuture.training import load_training_config, train


def test_absence_and_reappearance_never_pay_remaining_hp_or_kill():
    deriver = EventDeriver()
    deriver.begin(live(1, enemies=[(45, 10.0)]))
    assert kinds(deriver.update(live(2, enemies=[(45, 6.5)]))) == [("enemy_damaged", 45, 3.5)]
    assert deriver.update(live(3)) == []
    assert kinds(deriver.update(live(4, enemies=[(45, 6.5)]))) == [("enemy_spawned", 45, 10.0)]
    assert deriver.update(live(5)) == []  # permanent absence has no kill evidence either


class SegmentedBackend:
    """A continuing live encounter using production derivation and Gym reset accounting."""

    supports_seed = False

    def __init__(self):
        self.deriver = EventDeriver()
        self.frame = 0

    def start_episode(self, scenario, seed):
        self.frame += 1
        snap = live(self.frame, enemies=[(1, 10.0)])
        return StepResult(snap.entity_frame, tuple(self.deriver.begin(snap)))

    def step(self, action, repeat):
        self.frame += 1
        snap = live(self.frame, enemies=[(1, 6.5)])
        return StepResult(snap.entity_frame, tuple(self.deriver.update(snap)))

    def release(self):
        pass

    def close(self):
        pass


def test_real_env_resets_do_not_renew_healed_hp_credit():
    env = IsaacCombatEnv(
        SegmentedBackend(),
        [Scenario("continuing", "train", 1, 1, 1, 10.0)],
        accountant=RewardLedger(CombatCoefficients.load()),
    )
    credits = []
    for segment in range(8):
        env.reset(seed=segment)
        _, _, terminated, truncated, info = env.step(np.array([0, 0, 0]))
        assert truncated and not terminated and info["outcome"] == "unknown"
        credits.append(info["reward_components"]["enemy_damage"])
    assert credits == pytest.approx([0.7] + [0.0] * 7)
    env.close()


@pytest.mark.parametrize("gap", ["absence", "reset", "overflow"])
def test_gap_loss_is_not_paid_and_only_new_continuous_lows_pay(gap):
    d = EventDeriver()
    d.begin(live(1, enemies=[(1, 10.0)]))
    d.update(live(2, enemies=[(1, 8.0)]))
    if gap == "absence":
        assert d.update(live(3)) == []
        baseline = d.update(live(4, enemies=[(1, 5.0)]))
    elif gap == "reset":
        baseline = d.begin(live(4, enemies=[(1, 5.0)]))
    else:
        baseline = d.update(live(3, enemies=[(1, 5.0)], overflow=1))
        assert not any(e.kind == "enemy_damaged" for e in baseline)
        baseline = d.update(live(4, enemies=[(1, 5.0)]))
    assert not any(e.kind in ("enemy_damaged", "enemy_killed") for e in baseline)
    assert kinds(d.update(live(5, enemies=[(1, 4.0)]))) == [("enemy_damaged", 1, 1.0)]
    assert d.update(live(6, enemies=[(1, 9.0)])) == []
    assert d.update(live(7, enemies=[(1, 5.0)])) == []


@pytest.mark.parametrize("boundary", ["session", "epoch", "visit"])
def test_context_boundary_rebaselines_without_comparing_old_membership(boundary):
    d = EventDeriver()
    d.begin(live(1, enemies=[(1, 10.0)]))
    d.update(live(2, enemies=[(1, 8.0)]))
    snap = live(3, enemies=[(1, 5.0)], visit=2 if boundary == "visit" else None)
    raw = snap.model_dump()
    if boundary == "session":
        raw["session_id"] = raw["entity_frame"]["session_id"] = "b" * 32
    elif boundary == "epoch":
        raw["game_epoch"] = raw["entity_frame"]["game_epoch"] = 2
    snap = type(snap).model_validate(raw)
    assert kinds(d.update(snap)) == [("enemy_spawned", 1, 10.0)]


@pytest.mark.parametrize("boundary", ["session", "epoch", "visit"])
def test_new_namespace_resets_allowance_but_new_visit_does_not(boundary):
    d = EventDeriver()
    d.begin(live(1, enemies=[(1, 10.0)]))
    d.update(live(2, enemies=[(1, 5.0)]))
    for frame, hp in [(3, 10.0), (4, 8.0)]:
        snap = live(frame, enemies=[(1, hp)], visit=2)
        raw = snap.model_dump()
        if boundary == "session":
            raw["session_id"] = raw["entity_frame"]["session_id"] = "b" * 32
        elif boundary == "epoch":
            raw["game_epoch"] = raw["entity_frame"]["game_epoch"] = 2
        events = d.update(type(snap).model_validate(raw))
    damage = [e.amount for e in events if e.kind == "enemy_damaged"]
    assert damage == ([] if boundary == "visit" else [2.0])


def test_changed_max_hp_disables_future_credit_for_that_identity():
    d = EventDeriver()
    d.begin(live(1, enemies=[(1, 10.0)]))
    snap = live(2, enemies=[(1, 5.0)])
    raw = snap.model_dump()
    raw["oracle"]["enemies"][0]["max_hp"] = 20.0
    snap = type(snap).model_validate(raw)
    assert d.update(snap) == []
    assert d.update(live(3, enemies=[(1, 1.0)])) == []


def test_history_exhaustion_fails_without_forgetting_old_floor():
    d = EventDeriver()
    for batch in range(64):
        d.begin(live(batch + 1, enemies=[(batch * 64 + n, 10.0) for n in range(64)]))
    assert len(d._hp_floor) == 4096 and d._hp_floor[0] == (10.0, 10.0)
    with pytest.raises(EpisodeFault, match="history exhausted"):
        d.begin(live(100, enemies=[(4096, 10.0)]))
    assert len(d._hp_floor) == 4096 and 0 in d._hp_floor


def test_legacy_manifest_stays_readable_but_mismatched_resume_has_no_env(tmp_path):
    cfg, digest = load_training_config(Path("configs/training-live-v1.yaml"))
    root = tmp_path / "checkpoints"
    saved = write_checkpoint(root / "legacy", config_hash=digest, seed=20)
    # Actual pre-contract manifests omitted the new field.
    import json

    path = root / "legacy/manifest.json"
    raw = json.loads(path.read_text())
    raw.pop("reward_contract")
    path.write_text(json.dumps(raw))
    (root / "latest.txt").write_text("legacy")
    original = path.read_bytes()
    assert (
        load_checkpoint(
            root / "legacy", expected_config_hash=digest, expected_seed=20
        ).reward_contract
        == "combat-v1"
    )
    calls = []
    with pytest.raises(CheckpointError, match="combat-v1 != pure-v6"):
        train(
            cfg,
            digest,
            seed=20,
            env_factory=lambda _: calls.append("created"),
            out_dir=tmp_path,
            resume=True,
            reward_contract="pure-v6",
        )
    assert not calls and path.read_bytes() == original
    assert (root / "latest.txt").read_text() == "legacy"
    assert saved.reward_contract == "combat-v1"


def test_matching_reward_contract_loads_and_wrong_contract_rejects(tmp_path):
    saved = write_checkpoint(tmp_path / "new", reward_contract="pure-v6")
    assert (
        load_checkpoint(
            tmp_path / "new",
            expected_config_hash=saved.config_hash,
            expected_seed=7,
            expected_reward_contract="pure-v6",
        )
        == saved
    )
    with pytest.raises(CheckpointError, match="reward contract"):
        load_checkpoint(
            tmp_path / "new",
            expected_config_hash=saved.config_hash,
            expected_seed=7,
            expected_reward_contract="combat-v1",
        )


@pytest.mark.parametrize("contract", ["combat-v1", "pure-v6"])
def test_checkpoint_save_persists_reward_contract_and_parent(tmp_path, contract):
    class Artifact:
        def save(self, path):
            Path(path).write_bytes(b"fixture artifact")

    saved = save_checkpoint(
        tmp_path,
        model=Artifact(),
        vec_normalize=Artifact(),
        algorithm="RecurrentPPO",
        cfg_hash="a" * 64,
        seed=20,
        timesteps=256,
        parent_checkpoint_id="parent",
        rng_state={},
        reward_contract=contract,
    )
    loaded = load_checkpoint(
        tmp_path / saved.checkpoint_id,
        expected_config_hash="a" * 64,
        expected_seed=20,
        expected_reward_contract=contract,
    )
    assert loaded.reward_contract == contract and loaded.parent_checkpoint_id == "parent"
    assert (tmp_path / "latest.txt").read_text() == saved.checkpoint_id
