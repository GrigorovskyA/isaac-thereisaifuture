"""Explicit offline 649->723 warm-start primitives; never automatic resume."""

from copy import deepcopy
from typing import Any

import numpy as np

INPUT_WEIGHTS = {"lstm_actor.weight_ih_l0", "lstm_critic.weight_ih_l0"}


def expand_recurrent_parameters(source: Any, target: Any) -> None:
    """Copy one matching recurrent architecture and Adam state, zero new columns."""
    import torch

    if source.observation_space.shape != (649,) or target.observation_space.shape != (723,):
        raise ValueError("Migration requires exactly649->723 inputs")
    if not np.array_equal(source.action_space.nvec, target.action_space.nvec):
        raise ValueError("Migration action spaces differ")
    old, new = source.policy.state_dict(), target.policy.state_dict()
    if old.keys() != new.keys():
        raise ValueError("Migration policy layouts differ")
    expanded = set()
    for name, value in old.items():
        if value.shape == new[name].shape:
            new[name] = value.clone()
        elif (
            name in INPUT_WEIGHTS
            and value.ndim == 2
            and (value.shape[1] == 649 and new[name].shape == (value.shape[0], 723))
        ):
            new[name] = torch.cat((value, value.new_zeros((value.shape[0], 74))), dim=1)
            expanded.add(name)
        else:
            raise ValueError(f"Unsupported migration shape: {name}")
    if expanded != INPUT_WEIGHTS:
        raise ValueError("Migration requires separate actor/critic input LSTMs")
    old_names = {id(p): name for name, p in source.policy.named_parameters()}
    new_names = {id(p): name for name, p in target.policy.named_parameters()}
    old_opt, new_opt = source.policy.optimizer, target.policy.optimizer
    state = deepcopy(old_opt.state_dict())
    target_state = new_opt.state_dict()
    if len(old_opt.param_groups) != len(new_opt.param_groups):
        raise ValueError("Optimizer groups differ")
    copied: dict[Any, Any] = {}
    for index, (a, b) in enumerate(zip(old_opt.param_groups, new_opt.param_groups, strict=True)):
        names_a = [old_names[id(p)] for p in a["params"]]
        names_b = [new_names[id(p)] for p in b["params"]]
        if names_a != names_b:
            raise ValueError("Optimizer parameter order differs")
        old_ids = state["param_groups"][index]["params"]
        new_ids = target_state["param_groups"][index]["params"]
        for name, old_id, new_id in zip(names_a, old_ids, new_ids, strict=True):
            moments = deepcopy(state["state"].get(old_id, {}))
            for key, value in moments.items():
                if torch.is_tensor(value) and value.ndim:
                    if value.shape != old[name].shape:
                        raise ValueError("Unsupported optimizer tensor")
                    if name in expanded:
                        moments[key] = torch.cat(
                            (value, value.new_zeros((value.shape[0], 74))), dim=1
                        )
            copied[new_id] = moments
        state["param_groups"][index]["params"] = new_ids
    state["state"] = copied
    target.policy.load_state_dict(new, strict=True)
    target.policy.optimizer.load_state_dict(state)
    target.num_timesteps = source.num_timesteps
    target._n_updates = source._n_updates


def expand_normalizer(source: Any, vector_env: Any) -> Any:
    """Preserve prefix statistics; append an explicit neutral prior, not measured data."""
    if source.observation_space.shape != (649,) or vector_env.observation_space.shape != (723,):
        raise ValueError("Normalizer migration requires exactly649->723 inputs")
    target = deepcopy(source)  # VecNormalize deliberately omits its live environment
    target.observation_space = vector_env.observation_space
    target.obs_rms.mean = np.concatenate((source.obs_rms.mean, np.zeros(74)))
    target.obs_rms.var = np.concatenate((source.obs_rms.var, np.ones(74)))
    target.old_obs = np.zeros((vector_env.num_envs, 723), dtype=np.float32)
    target.set_venv(vector_env)
    return target
