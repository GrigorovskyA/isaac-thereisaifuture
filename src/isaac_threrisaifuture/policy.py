"""Policy architecture shared by training, resume, frozen evaluation and the smoke test.

The structured extractor (contract `policy_features: structured_v1`) feeds both LSTMs. Each
entity kind goes through one MLP shared by all its slots, pooled over the present slots, so what
is learned about an enemy holds in every slot. Small CNNs read the minimap and the visited-cell
grid, so a pattern means the same in every cell. An MLP reads the rest (player, inventory, room
and doors, collectibles, stats). `InputProjection` is the earlier Linear(obs, 512) and is kept so
older saved models still load. Saved models pickle these classes by their module path, so keep
the names and module stable.
"""

from typing import Any, Literal

import gymnasium as gym
import torch
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from torch import nn

from .encoding import (
    CAPACITY,
    ENTITY_OFFSETS,
    GRID_WIDTH,
    MAP_CHANNELS,
    MAP_OFFSET,
    OBSERVATION_SIZE,
    OFF_GRID_OFFSET,
    SLOT_WIDTH,
    VISITED_COLS,
    VISITED_OFFSET,
    VISITED_ROWS,
)
from .entities import ENTITY_KINDS, LEVEL_GRID_CELLS, EntityKind

PolicyFeatures = Literal["input_projection", "structured_v1"]
SLOT_HIDDEN = 64  # per-slot MLP width of every entity kind
MAP_OUT = 128
VISITED_OUT = 64
SCALAR_OUT = 256


class InputProjection(BaseFeaturesExtractor):
    """Linear(obs, features_dim) + ReLU, shared by the actor and the critic."""

    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 512) -> None:
        super().__init__(observation_space, features_dim)
        (size,) = observation_space.shape
        self.net = nn.Sequential(nn.Linear(size, features_dim), nn.ReLU())

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.net(observations)  # type: ignore[no-any-return]


def _entity_ranges() -> dict[EntityKind, tuple[int, int]]:
    return {
        kind: (ENTITY_OFFSETS[kind], ENTITY_OFFSETS[kind] + CAPACITY[kind] * SLOT_WIDTH[kind])
        for kind in ENTITY_KINDS
    }


def scalar_indices() -> list[int]:
    """Observation indices outside the entity slots, the minimap and the visited grid."""
    taken = set(range(MAP_OFFSET, OFF_GRID_OFFSET)) | set(range(VISITED_OFFSET, OBSERVATION_SIZE))
    for start, end in _entity_ranges().values():
        taken |= set(range(start, end))
    return [index for index in range(OBSERVATION_SIZE) if index not in taken]


class StructuredFeatures(BaseFeaturesExtractor):
    """Shared slot MLPs with masked mean and max pooling, two grid CNNs and a scalar MLP.

    Expects the observation after continuous-only normalization: a slot's first feature, its
    present bit, is still exactly 0 or 1. Per kind the output is mean and max of the present
    slots (zero for an empty kind) and the present fraction, so it does not depend on the slot
    order. Shared by the actor and the critic.
    """

    scalar_index: torch.Tensor

    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 512) -> None:
        super().__init__(observation_space, features_dim)
        if observation_space.shape != (OBSERVATION_SIZE,):
            raise ValueError("Structured features need the project observation size")
        self.slots = nn.ModuleDict(
            {
                kind: nn.Sequential(
                    nn.Linear(SLOT_WIDTH[kind], SLOT_HIDDEN),
                    nn.ReLU(),
                    nn.Linear(SLOT_HIDDEN, SLOT_HIDDEN),
                    nn.ReLU(),
                )
                for kind in ENTITY_KINDS
            }
        )
        # 13 x 13 cells x 14 channels -> 7 x 7 x 32; 14 x 26 visited cells -> 7 x 13 x 16.
        self.map = nn.Sequential(
            nn.Conv2d(MAP_CHANNELS, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 32, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(32 * 7 * 7, MAP_OUT),
            nn.ReLU(),
        )
        self.visited = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 16, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(16 * 7 * 13, VISITED_OUT),
            nn.ReLU(),
        )
        scalars = scalar_indices()
        self.register_buffer("scalar_index", torch.tensor(scalars), persistent=False)
        self.scalar = nn.Sequential(nn.Linear(len(scalars), SCALAR_OUT), nn.ReLU())
        width = len(ENTITY_KINDS) * (2 * SLOT_HIDDEN + 1) + MAP_OUT + VISITED_OUT + SCALAR_OUT
        self.head = nn.Sequential(nn.Linear(width, features_dim), nn.ReLU())
        self._ranges = _entity_ranges()

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        batch = observations.shape[0]
        parts: list[torch.Tensor] = []
        for kind, (start, end) in self._ranges.items():
            slots = observations[:, start:end].reshape(batch, CAPACITY[kind], SLOT_WIDTH[kind])
            present = (slots[:, :, :1] > 0.5).to(observations.dtype)
            hidden = self.slots[kind](slots) * present  # absent slots add nothing
            count = present.sum(dim=1)
            parts += [hidden.sum(dim=1) / count.clamp(min=1.0), hidden.amax(dim=1)]
            parts.append(count / CAPACITY[kind])
        grid = observations[:, MAP_OFFSET : MAP_OFFSET + LEVEL_GRID_CELLS * MAP_CHANNELS]
        grid = grid.reshape(batch, GRID_WIDTH, GRID_WIDTH, MAP_CHANNELS).permute(0, 3, 1, 2)
        parts.append(self.map(grid))
        visited = observations[:, VISITED_OFFSET:].reshape(batch, 1, VISITED_ROWS, VISITED_COLS)
        parts.append(self.visited(visited))
        parts.append(self.scalar(observations.index_select(1, self.scalar_index)))
        return self.head(torch.cat(parts, dim=1))  # type: ignore[no-any-return]


EXTRACTORS: dict[PolicyFeatures, type[BaseFeaturesExtractor]] = {
    "input_projection": InputProjection,
    "structured_v1": StructuredFeatures,
}


def policy_kwargs(
    lstm_hidden_size: int,
    features_dim: int | None,
    *,
    features: PolicyFeatures = "structured_v1",
    **extra: Any,
) -> dict[str, Any]:
    """Keyword arguments of the one RecurrentPPO policy; no features_dim keeps SB3's default."""
    kwargs: dict[str, Any] = {"lstm_hidden_size": lstm_hidden_size, **extra}
    if features_dim is not None:
        kwargs["features_extractor_class"] = EXTRACTORS[features]
        kwargs["features_extractor_kwargs"] = {"features_dim": features_dim}
    return kwargs
