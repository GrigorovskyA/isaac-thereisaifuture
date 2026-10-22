"""Explicit migration checks on actual trained synthetic artifacts, never Isaac."""

from copy import deepcopy

import numpy as np
import pytest
from test_checkpoint_policy import RAW_CONFIG, synthetic_env
from test_coherent_geometry import ShapeWorld

from isaac_threrisaifuture import checkpoints as cp
from isaac_threrisaifuture.geometry_migration import (
    INPUT_WEIGHTS,
    expand_normalizer,
    expand_recurrent_parameters,
)
from isaac_threrisaifuture.training import TrainingConfig, train


def test_trained_migration_equivalence_moments_and_resume(tmp_path):
    import torch
    from sb3_contrib import RecurrentPPO
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    cfg = TrainingConfig.model_validate(RAW_CONFIG)
    old_result = train(
        cfg, cp.config_hash(RAW_CONFIG), seed=7, env_factory=synthetic_env, out_dir=tmp_path / "old"
    )
    old_dir = tmp_path / "old/checkpoints" / old_result.checkpoint_id
    original = {p.name: p.read_bytes() for p in old_dir.iterdir()}
    parent = cp.read_manifest(old_dir)
    source = RecurrentPPO.load(old_dir / "model.zip", device="cpu")
    old_norm = VecNormalize.load(
        str(old_dir / "vecnormalize.pkl"), DummyVecEnv([lambda: synthetic_env(7)])
    )
    norm = expand_normalizer(old_norm, DummyVecEnv([ShapeWorld]))
    target = RecurrentPPO(
        "MlpLstmPolicy",
        norm,
        n_steps=32,
        batch_size=32,
        n_epochs=1,
        policy_kwargs={"lstm_hidden_size": 16},
        seed=7,
        device="cpu",
    )
    expand_recurrent_parameters(source, target)
    assert target.num_timesteps == source.num_timesteps == 32
    assert target._n_updates == source._n_updates
    for name, value in source.policy.state_dict().items():
        other = target.policy.state_dict()[name]
        if name in INPUT_WEIGHTS:
            torch.testing.assert_close(value, other[:, :649], rtol=0, atol=0)
            assert torch.count_nonzero(other[:, 649:]) == 0
        else:
            torch.testing.assert_close(value, other, rtol=0, atol=0)
    old_state, new_state = (
        source.policy.optimizer.state_dict(),
        target.policy.optimizer.state_dict(),
    )
    for key, state in old_state["state"].items():
        for field, value in state.items():
            other = new_state["state"][key][field]
            if value.ndim == 2 and value.shape[1] == 649:
                torch.testing.assert_close(value, other[:, :649], rtol=0, atol=0)
                assert torch.count_nonzero(other[:, 649:]) == 0
            else:
                torch.testing.assert_close(value, other, rtol=0, atol=0)
    assert norm.obs_rms.count == old_norm.obs_rms.count
    np.testing.assert_array_equal(norm.obs_rms.mean[:649], old_norm.obs_rms.mean)
    np.testing.assert_array_equal(norm.obs_rms.var[:649], old_norm.obs_rms.var)
    np.testing.assert_array_equal(norm.obs_rms.mean[649:], 0)
    np.testing.assert_array_equal(norm.obs_rms.var[649:], 1)
    rng = np.random.default_rng(12)
    a, b = deepcopy(source._last_lstm_states), deepcopy(target._last_lstm_states)
    for index in range(16):
        old = rng.uniform(-1, 1, (1, 649)).astype(np.float32)
        new = np.concatenate((old, rng.uniform(-1, 1, (1, 74)).astype(np.float32)), axis=1)
        old, new = old_norm.normalize_obs(old), norm.normalize_obs(new)
        np.testing.assert_array_equal(old, new[:, :649])
        starts = torch.tensor([index == 0], dtype=torch.float32)
        with torch.no_grad():
            oa, ov, op, a = source.policy.forward(torch.tensor(old), a, starts, deterministic=True)
            na, nv, np_, b = target.policy.forward(torch.tensor(new), b, starts, deterministic=True)
        torch.testing.assert_close(oa, na)
        torch.testing.assert_close(ov, nv, atol=2e-6, rtol=2e-6)
        torch.testing.assert_close(op, np_, atol=2e-6, rtol=2e-6)
    raw = deepcopy(RAW_CONFIG)
    raw["budget"]["total_timesteps"] = 64
    hashed = cp.config_hash(raw)
    migrated = cp.save_checkpoint(
        tmp_path / "new/checkpoints",
        model=target,
        vec_normalize=norm,
        algorithm="RecurrentPPO",
        cfg_hash=hashed,
        seed=7,
        timesteps=32,
        parent_checkpoint_id=parent.checkpoint_id,
        rng_state=parent.rng_state,
        reward_contract="live-firing-v4",
        observation_schema=2,
    )
    assert migrated.rng_state == parent.rng_state
    with pytest.raises(cp.CheckpointError, match="observation_schema"):
        cp.load_checkpoint(
            tmp_path / "new/checkpoints" / migrated.checkpoint_id,
            expected_config_hash=hashed,
            expected_seed=7,
        )
    resumed = train(
        TrainingConfig.model_validate(raw),
        hashed,
        seed=7,
        env_factory=lambda _: ShapeWorld(),
        out_dir=tmp_path / "new",
        resume=True,
        observation_schema=2,
        reward_contract="live-firing-v4",
    )
    assert resumed.timesteps == 64
    assert {p.name: p.read_bytes() for p in old_dir.iterdir()} == original
    old_norm.close()
    norm.close()


def test_unknown_architecture_fails_without_parameter_mutation():
    from sb3_contrib import RecurrentPPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    source = RecurrentPPO(
        "MlpLstmPolicy",
        DummyVecEnv([lambda: synthetic_env(7)]),
        n_steps=32,
        batch_size=32,
        policy_kwargs={"lstm_hidden_size": 16},
    )
    target = RecurrentPPO(
        "MlpLstmPolicy",
        DummyVecEnv([ShapeWorld]),
        n_steps=32,
        batch_size=32,
        policy_kwargs={"lstm_hidden_size": 32},
    )
    before = deepcopy(target.policy.state_dict())
    with pytest.raises(ValueError, match="Unsupported migration shape"):
        expand_recurrent_parameters(source, target)
    assert all(
        np.array_equal(v.numpy(), target.policy.state_dict()[k].numpy()) for k, v in before.items()
    )
    source.get_env().close()
    target.get_env().close()
