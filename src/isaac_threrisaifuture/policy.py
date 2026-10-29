"""Policy architecture shared by training, resume, frozen evaluation and the smoke test.

A linear projection of the observation feeds both LSTMs. Without it each LSTM applies its
input matrix to the full observation for every padded step of every sequence, which made one
optimizer update about 4x slower at observation size 7522. Saved models pickle this class by
its module path, so keep the name and module stable.
"""

from typing import Any

import gymnasium as gym
import torch
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from torch import nn


class InputProjection(BaseFeaturesExtractor):
    """Linear(obs, features_dim) + ReLU, shared by the actor and the critic."""

    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 512) -> None:
        super().__init__(observation_space, features_dim)
        (size,) = observation_space.shape
        self.net = nn.Sequential(nn.Linear(size, features_dim), nn.ReLU())

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.net(observations)  # type: ignore[no-any-return]


def policy_kwargs(lstm_hidden_size: int, features_dim: int | None, **extra: Any) -> dict[str, Any]:
    """Keyword arguments of the one RecurrentPPO policy; no features_dim keeps SB3's default."""
    kwargs: dict[str, Any] = {"lstm_hidden_size": lstm_hidden_size, **extra}
    if features_dim is not None:
        kwargs["features_extractor_class"] = InputProjection
        kwargs["features_extractor_kwargs"] = {"features_dim": features_dim}
    return kwargs
