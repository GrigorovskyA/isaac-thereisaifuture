"""`use_entropy_scale`: the use head gets a share of the entropy bonus; move and shoot keep it."""

from typing import Any

import numpy as np
import pytest
import torch
from test_pure_training import load_latest, run, write_config
from test_rollout_advantage_and_gpu_learner import model

from isaac_threrisaifuture.learner import PureRecurrentPPO, weighted_entropy
from isaac_threrisaifuture.training import PURE_CONFIG, load_training_config


def minibatch(ppo: PureRecurrentPPO) -> Any:
    ppo.learn(64)  # fills the rollout buffer
    return next(iter(ppo.rollout_buffer.get(16)))


@pytest.mark.parametrize("scale", [0.0, 0.2, 1.0])
def test_the_forward_pass_matches_the_policy_and_only_the_use_entropy_is_scaled(scale):
    ppo = model(use_entropy_scale=scale)
    data = minibatch(ppo)
    args = (data.observations, data.actions, data.lstm_states, data.episode_starts)
    with torch.no_grad():
        values, log_prob, entropy = ppo._evaluate_actions(*args)
        ref_values, ref_log_prob, ref_entropy = ppo.policy.evaluate_actions(*args)
    assert torch.allclose(values, ref_values, atol=1e-6)
    assert torch.allclose(log_prob, ref_log_prob, atol=1e-6)
    assert entropy.shape == ref_entropy.shape
    if scale == 1.0:
        assert torch.allclose(entropy, ref_entropy, atol=1e-6)
    else:
        assert bool(torch.all(entropy < ref_entropy))


def test_weighted_entropy_scales_only_the_last_head():
    logits = [torch.zeros(3, 5), torch.zeros(3, 5), torch.zeros(3, 4)]

    class Dist:
        distribution = [torch.distributions.Categorical(logits=x) for x in logits]

    full = 2 * np.log(5) + np.log(4)
    assert torch.allclose(weighted_entropy(Dist, 1.0), torch.full((3,), full, dtype=torch.float32))
    assert torch.allclose(
        weighted_entropy(Dist, 0.25),
        torch.full((3,), 2 * np.log(5) + 0.25 * np.log(4), dtype=torch.float32),
    )


def test_a_negative_scale_is_refused():
    with pytest.raises(ValueError, match="use_entropy_scale"):
        model(use_entropy_scale=-0.1)


def test_the_shipped_config_sets_a_fifth_and_training_passes_it_to_the_learner(tmp_path):
    config, _ = load_training_config(PURE_CONFIG)
    assert config.hyperparameters.use_entropy_scale == 0.2
    out = tmp_path / "run"
    run(write_config(tmp_path / "c.yaml"), out, 32)
    ppo, manifest, _ = load_latest(out)
    assert ppo.use_entropy_scale == 0.2
    assert manifest.hyperparameters["use_entropy_scale"] == 0.2
