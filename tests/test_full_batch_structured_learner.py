"""OFFLINE tests for the full-batch structured learner: feature kind table, continuous-only
normalization, structured features and the hashed contract. Synthetic frames and the synthetic
room prove plumbing only, never Isaac play."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest
import torch
import yaml
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from synthetic import door, enemy, frame, inventory, pedestal, pickup, room_facts

from isaac_threrisaifuture.checkpoints import CheckpointError, config_hash
from isaac_threrisaifuture.encoding import (
    CAPACITY,
    COLLECTIBLE_OFFSET,
    ENTITY_OFFSETS,
    FEATURE_BLOCKS,
    MAP_OFFSET,
    OBSERVATION_SIZE,
    SLOT_WIDTH,
    STALL_OFFSET,
    VISITED_OFFSET,
    VisitedCells,
    continuous_mask,
    encode,
    feature_kinds,
)
from isaac_threrisaifuture.entities import (
    ENTITY_KINDS,
    INTERACTABLE_CLASSES,
    OBSTACLE_CLASSES,
    Entity,
    MapRoom,
    Vec,
)
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episodes import Scenario
from isaac_threrisaifuture.normalization import (
    VARIANCE_FLOOR,
    ContinuousVecNormalize,
    check_continuous_only,
)
from isaac_threrisaifuture.policy import StructuredFeatures, policy_kwargs, scalar_indices
from isaac_threrisaifuture.sim import SyntheticRoomBackend
from isaac_threrisaifuture.training import (
    PURE_CONFIG,
    TrainingConfigError,
    apply_use_head_prior,
    load_training_config,
)

TOY = Scenario("toy", "validation", 1, 90, enemy_count=2, enemy_hp=7.0)
RAW: dict[str, Any] = yaml.safe_load(PURE_CONFIG.read_text("utf-8"))
# Contract hash of the reward v12 schema 9 run (runs/pure-v4-reward-v12-schema9).
REWARD_V12_SCHEMA9_HASH = "1a6d8146f5e89b7bdad14fe21d3afa9cc1f5c4192b8e5f24cefb6bbab0e0c8d8"


def synthetic_env(_: int = 0) -> IsaacCombatEnv:
    return IsaacCombatEnv(SyntheticRoomBackend(), [TOY])


def rich_entities() -> list[Entity]:
    """At least one entity of every kind, with all optional facts set."""
    npc = enemy(1, 40, -30).model_copy(
        update={
            "velocity": Vec(x=3, y=-2), "npc_type": 10, "npc_variant": 1, "npc_max_hp": 25.0,
            "boss": True, "champion": False, "flying": True, "invulnerable": False,
        }
    )  # fmt: skip
    base = {"spawn_generation": 0, "position": Vec(x=-80, y=60)}
    return [
        npc,
        enemy(2, 200, 100, hp=3.0),
        Entity(kind="projectile", entity_id=3, velocity=Vec(x=-5, y=1), **base),
        Entity(kind="obstacle", entity_id=4, obstacle_class=OBSTACLE_CLASSES[2], **base),
        pickup(5, 10, 20, variant=20, subtype=2, price=5),
        pedestal(6, -30, 40, 118, quality=3, item_type="active", max_charges=6, tags=5),
        Entity(kind="own_attack", entity_id=7, velocity=Vec(x=8, y=0), **base),
        Entity(kind="bomb", entity_id=8, age_frames=45, **base),
        Entity(
            kind="interactable", entity_id=9, interactable_class=INTERACTABLE_CLASSES[1], **base
        ),
    ]


def rich_frame() -> Any:
    rooms = [
        MapRoom(grid_index=84, shape=1, visited=True, current=True, room_type=1),
        MapRoom(grid_index=85, shape=8, visited=False, current=False, room_type=4),
        MapRoom(grid_index=60, shape=1, visited=False, current=False, room_type=None),
    ]
    inv = inventory(coins=7, bombs=2, keys=1, active_item=105, active_charge=2,
                    active_max_charge=6, card=3)  # fmt: skip
    inv = inv.model_copy(update={"active_quality": 2, "active_tags": 9})
    return frame(
        rich_entities(),
        inventory=inv,
        room=room_facts(type=4, clear=True, shape=6,
                        doors=[door(), None, door(locked=True, target_type=5), *[None] * 5]),
        map=rooms,
        collectibles=[1, 118, 1024],
    )  # fmt: skip


def encoded(item: Any, stall: float = 0.4) -> np.ndarray:
    visited = VisitedCells().update(item)
    return encode(item, stall_fraction=stall, visited_cells=visited).vector


# --- feature kind table -----------------------------------------------------------------------


def test_feature_blocks_cover_every_index_exactly_once():
    covered = np.zeros(OBSERVATION_SIZE, dtype=int)
    end = 0
    for block in FEATURE_BLOCKS:
        assert block.offset == end and block.size > 0
        covered[block.offset : block.offset + block.size] += 1
        end = block.offset + block.size
    assert end == OBSERVATION_SIZE and (covered == 1).all()
    assert len(feature_kinds()) == OBSERVATION_SIZE == len(continuous_mask())
    assert {block.kind for block in FEATURE_BLOCKS} == {"continuous", "binary", "one_hot"}
    assert len({block.name for block in FEATURE_BLOCKS}) == len(FEATURE_BLOCKS)


def test_feature_blocks_follow_the_encoder_layout():
    by_offset = {block.offset: block for block in FEATURE_BLOCKS}
    for kind in ENTITY_KINDS:
        for slot in (0, CAPACITY[kind] - 1):
            start = ENTITY_OFFSETS[kind] + slot * SLOT_WIDTH[kind]
            assert by_offset[start].name == f"{kind}[{slot}].present"
            assert by_offset[start].kind == "binary"
    assert by_offset[COLLECTIBLE_OFFSET].name == "collectibles"
    assert by_offset[MAP_OFFSET].name == "map[0].flags"
    assert by_offset[STALL_OFFSET].name == "stall" and by_offset[STALL_OFFSET].kind == "continuous"
    assert by_offset[VISITED_OFFSET].name == "visited_cells"
    assert by_offset[VISITED_OFFSET].kind == "binary"


def test_encoded_binary_and_one_hot_features_hold_only_zero_or_one():
    vectors = [encoded(rich_frame()), encoded(frame(), stall=0.0), encoded(frame([enemy(1, 5, 5)]))]
    set_ones = 0
    for vector in vectors:
        for block in FEATURE_BLOCKS:
            values = vector[block.offset : block.offset + block.size]
            if block.kind == "continuous":
                continue
            assert set(np.unique(values)) <= {0.0, 1.0}, block.name
            if block.kind == "one_hot":
                assert values.sum() <= 1.0, block.name
            set_ones += int(values.sum())
    assert set_ones > 50  # the rich frame sets bits in many blocks
    rich = encoded(rich_frame())
    fractional = (rich != 0) & (rich != 1)
    assert fractional.any() and continuous_mask()[fractional].all()


# --- continuous-only normalization ------------------------------------------------------------


def fitted(cls: type[VecNormalize]) -> VecNormalize:
    """A normalizer whose statistics saw 200 empty frames and one rich frame."""
    normalizer = cls(DummyVecEnv([synthetic_env]), gamma=0.998)
    empty = encoded(frame(), stall=0.0)
    normalizer.obs_rms.update(np.stack([empty] * 200 + [encoded(rich_frame())]))
    return normalizer


def test_binary_features_pass_through_and_continuous_features_are_normalized():
    masked, plain = fitted(ContinuousVecNormalize), fitted(VecNormalize)
    rare = encoded(rich_frame())[None, :]
    out, reference = masked.normalize_obs(rare)[0], plain.normalize_obs(rare)[0]
    mask = continuous_mask()
    assert out.dtype == np.float32
    assert np.array_equal(out[~mask], rare[0][~mask])  # no centring, scaling or clip
    wide = mask & (masked.obs_rms.var >= VARIANCE_FLOOR)
    assert np.allclose(out[wide], reference[wide])  # spread above the floor: plain scaling
    assert np.abs(reference[~mask]).max() > 5  # what plain VecNormalize did to a rare bit
    assert not np.allclose(out[mask], rare[0][mask])  # continuous features were normalized
    back = masked.unnormalize_obs(out[None, :])[0]
    assert np.array_equal(back[~mask], rare[0][~mask])


def test_a_rare_continuous_value_stays_within_the_variance_floor():
    masked, plain = fitted(ContinuousVecNormalize), fitted(VecNormalize)
    rare = encoded(rich_frame())[None, :]
    out, reference = masked.normalize_obs(rare)[0], plain.normalize_obs(rare)[0]
    mask = continuous_mask()
    narrow = mask & (masked.obs_rms.var < VARIANCE_FLOOR) & (rare[0] != masked.obs_rms.mean)
    assert narrow.any() and np.abs(reference[narrow]).max() > 5  # plain scaling spikes
    bound = (np.abs(rare[0] - masked.obs_rms.mean) / np.sqrt(VARIANCE_FLOOR))[narrow]
    assert np.all(np.abs(out[narrow]) <= bound + 1e-5)
    back = masked.unnormalize_obs(out[None, :])[0]
    assert np.allclose(back[mask], rare[0][mask], atol=1e-5)


def test_save_load_round_trip_keeps_the_class_mask_and_output(tmp_path):
    normalizer = fitted(ContinuousVecNormalize)
    normalizer.save(str(tmp_path / "vecnormalize.pkl"))
    loaded = VecNormalize.load(str(tmp_path / "vecnormalize.pkl"), DummyVecEnv([synthetic_env]))
    assert isinstance(loaded, ContinuousVecNormalize)
    check_continuous_only(loaded)
    rare = encoded(rich_frame())[None, :]
    assert np.array_equal(loaded.normalize_obs(rare), normalizer.normalize_obs(rare))


def test_a_plain_or_stale_normalizer_is_refused():
    with pytest.raises(CheckpointError, match="not the continuous-only"):
        check_continuous_only(fitted(VecNormalize))
    stale = fitted(ContinuousVecNormalize)
    stale.continuous = ~stale.continuous
    with pytest.raises(CheckpointError, match="mask"):
        check_continuous_only(stale)


# --- contract ---------------------------------------------------------------------------------


def write(path: Path, **contract: Any) -> Path:
    raw = yaml.safe_load(yaml.safe_dump(RAW))
    raw["contract"].update(contract)
    for name in [key for key, value in contract.items() if value is None]:
        del raw["contract"][name]
    path.write_text(yaml.safe_dump(raw), "utf-8")
    return path


def test_the_contract_binds_normalization_and_features_and_refuses_the_old_lineage(tmp_path):
    config, digest = load_training_config(PURE_CONFIG)
    assert config.contract.observation_normalization == "continuous_only"
    assert config.contract.policy_features == "structured_v1"
    assert digest != REWARD_V12_SCHEMA9_HASH
    old = {k: v for k, v in RAW["contract"].items()
           if k not in ("observation_normalization", "policy_features")}  # fmt: skip
    assert config_hash(old) != digest
    for change in (
        {"observation_normalization": None},
        {"policy_features": None},
        {"observation_normalization": "all"},
        {"policy_features": "input_projection"},
    ):
        with pytest.raises(TrainingConfigError):
            load_training_config(write(tmp_path / "x.yaml", **change))


# --- structured features ----------------------------------------------------------------------


def extractor(features_dim: int = 32) -> StructuredFeatures:
    torch.manual_seed(0)
    space = synthetic_env().observation_space
    return StructuredFeatures(space, features_dim).eval()


def test_the_extractor_partitions_the_observation():
    ranges = [set(range(ENTITY_OFFSETS[k], ENTITY_OFFSETS[k] + CAPACITY[k] * SLOT_WIDTH[k]))
              for k in ENTITY_KINDS]  # fmt: skip
    grids = set(range(MAP_OFFSET, MAP_OFFSET + 169 * 14)) | set(
        range(VISITED_OFFSET, OBSERVATION_SIZE)
    )
    parts = [*ranges, grids, set(scalar_indices())]
    assert sum(len(part) for part in parts) == OBSERVATION_SIZE
    assert set().union(*parts) == set(range(OBSERVATION_SIZE))


def test_extractor_output_shape_and_finite_for_empty_groups():
    net = extractor()
    batch = torch.as_tensor(np.stack([encoded(rich_frame()), np.zeros(OBSERVATION_SIZE)]))
    out = net(batch.float())
    assert out.shape == (2, 32) and torch.isfinite(out).all()
    empty = torch.zeros(3, OBSERVATION_SIZE, requires_grad=True)
    loss = net(empty).sum()
    loss.backward()
    assert torch.isfinite(loss) and torch.isfinite(empty.grad).all()


def test_extractor_is_invariant_to_the_order_of_entity_slots():
    net = extractor()
    vector = encoded(frame([enemy(i, 20 * i, -10 * i, hp=float(i)) for i in range(1, 6)]))
    start, width = ENTITY_OFFSETS["enemy"], SLOT_WIDTH["enemy"]
    slots = vector[start : start + CAPACITY["enemy"] * width].reshape(CAPACITY["enemy"], width)
    order = np.random.default_rng(3).permutation(CAPACITY["enemy"])  # present slots move too
    permuted = vector.copy()
    permuted[start : start + CAPACITY["enemy"] * width] = slots[order].ravel()
    assert not np.array_equal(permuted, vector)
    both = net(torch.as_tensor(np.stack([vector, permuted])))
    assert torch.allclose(both[0], both[1], atol=1e-5)
    fewer = vector.copy()
    fewer[start + width : start + 2 * width] = 0.0  # one enemy gone changes the output
    assert not torch.allclose(net(torch.as_tensor(fewer[None])), both[:1])


def test_full_batch_recurrent_ppo_learns_with_structured_features(monkeypatch):
    from sb3_contrib import RecurrentPPO
    from sb3_contrib.common.recurrent.buffers import RecurrentRolloutBuffer

    calls: list[int] = []
    original = RecurrentRolloutBuffer._get_samples

    def counted(self: Any, batch_inds: np.ndarray, *args: Any, **kwargs: Any) -> Any:
        calls.append(len(batch_inds))
        return original(self, batch_inds, *args, **kwargs)

    monkeypatch.setattr(RecurrentRolloutBuffer, "_get_samples", counted)
    from stable_baselines3.common.monitor import Monitor

    # Monitor owns info["episode"], as in training.
    venv = ContinuousVecNormalize(DummyVecEnv([lambda: Monitor(synthetic_env())]), gamma=0.998)
    model = RecurrentPPO("MlpLstmPolicy", venv, n_steps=64, batch_size=64, n_epochs=2,
                         policy_kwargs=policy_kwargs(16, 24), seed=3, device="cpu")  # fmt: skip
    apply_use_head_prior(model, 0.85)
    assert isinstance(model.policy.features_extractor, StructuredFeatures)
    model.learn(64)
    assert calls == [64, 64]  # one minibatch of the whole rollout per epoch
    assert model.num_timesteps == 64
    assert all(torch.isfinite(p).all() for p in model.policy.parameters())
