"""Self-supervised auxiliary losses of the pure profile (contract `auxiliary: spr_reward_done_v1`).

PPO uses each step for about ten gradient steps and then drops it. Here the shared features
extractor (the input of both LSTMs) also learns to predict what the agent itself sees next, the
reward it gets and whether the episode ends, from a replay of the last rollouts (SPR, Schwarzer et
al. 2020, arXiv 2007.05929, cut to one step; sample reuse as in PPG, Cobbe et al. 2020). These are
the agent's own observations and rewards, not hints, and they add no reward. The heads are
feed-forward over single transitions, so no LSTM state or sequence is needed:

- latent: a transition MLP maps features(s_t) and the one-hot action to a predicted projection
  of features(s_t+1) from an EMA target copy of the extractor and projection (stop-gradient),
  loss 2 - 2 cos; pairs whose episode ended at t are skipped;
- reward: the VecNormalize-scaled reward r_t, as the learner sees it, Huber loss;
- done: the terminal outcome at t (death or stall restart, not a time limit), BCE.

The replay keeps raw observations (continuous features float32, binary and one-hot features
float16, which holds 0 and 1 exactly) and raw rewards, normalized with the current statistics at
sampling time. It lives in memory only and starts empty after a resume. Heads, EMA target and
optimizer state are saved per checkpoint as `auxiliary.pt`; frozen evaluation never reads it.
Torch is imported at module load.
"""

import copy
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import torch
from numpy.typing import NDArray
from torch import nn
from torch.nn import functional

from .encoding import continuous_mask

Auxiliary = Literal["none", "spr_reward_done_v1"]
NONE: Auxiliary = "none"  # contract value `auxiliary`: no auxiliary losses (earlier lineages)
SPR_REWARD_DONE: Auxiliary = "spr_reward_done_v1"
AUXILIARIES: tuple[Auxiliary, ...] = (NONE, SPR_REWARD_DONE)
PROJECTION_DIM = 128  # SPR projects the 512 features before the cosine
HEAD_HIDDEN = 128
STATE_FORMAT = 1  # layout of auxiliary.pt
LOSSES = ("latent", "reward", "done")


def one_hot_actions(actions: torch.Tensor, nvec: Sequence[int]) -> torch.Tensor:
    """Concatenated one-hot of each head of a MultiDiscrete action batch (batch, heads)."""
    parts = [functional.one_hot(actions[:, i].long(), n) for i, n in enumerate(nvec)]
    return torch.cat(parts, dim=1).float()


def _mlp(width_in: int, hidden: int, width_out: int) -> nn.Sequential:
    return nn.Sequential(nn.Linear(width_in, hidden), nn.ReLU(), nn.Linear(hidden, width_out))


class AuxiliaryHeads(nn.Module):
    """Online heads over features(s_t) plus the one-hot action; trained by the auxiliary phase."""

    def __init__(self, features_dim: int, nvec: Sequence[int]) -> None:
        super().__init__()
        width = features_dim + sum(nvec)
        self.transition = _mlp(width, features_dim, features_dim)
        self.projection = nn.Linear(features_dim, PROJECTION_DIM)
        self.predictor = nn.Linear(PROJECTION_DIM, PROJECTION_DIM)
        self.reward = _mlp(width, HEAD_HIDDEN, 1)
        self.done = _mlp(width, HEAD_HIDDEN, 1)


class AuxiliaryModel(nn.Module):
    """Online heads and the EMA target (copies of the extractor and the projection)."""

    def __init__(self, extractor: nn.Module, features_dim: int, nvec: Sequence[int]) -> None:
        super().__init__()
        self.heads = AuxiliaryHeads(features_dim, nvec)
        self.target_extractor = copy.deepcopy(extractor)
        self.target_projection = copy.deepcopy(self.heads.projection)
        for parameter in self.target_parameters():
            parameter.requires_grad_(False)

    def target_parameters(self) -> list[nn.Parameter]:
        return [*self.target_extractor.parameters(), *self.target_projection.parameters()]


@torch.no_grad()
def ema_update(target: nn.Module, online: nn.Module, tau: float) -> None:
    """target <- tau * target + (1 - tau) * online, parameter by parameter."""
    for kept, fresh in zip(target.parameters(), online.parameters(), strict=True):
        kept.mul_(tau).add_(fresh.detach(), alpha=1.0 - tau)


# --- replay ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class RolloutRecord:
    """One rollout of one env: n steps and the n + 1 observations around them, all raw."""

    continuous: NDArray[np.float32]  # (n + 1, continuous features)
    discrete: NDArray[np.float16]  # (n + 1, binary and one-hot features)
    actions: NDArray[np.int64]  # (n, heads)
    rewards: NDArray[np.float32]  # (n,) raw env rewards
    dones: NDArray[np.bool_]  # (n,) the episode ended at t; obs t + 1 is the next episode's
    terminated: NDArray[np.bool_]  # (n,) ended by an outcome (death, stall), not a time limit

    @property
    def steps(self) -> int:
        return len(self.rewards)

    @property
    def nbytes(self) -> int:
        arrays = (self.continuous, self.discrete, self.actions, self.rewards, self.dones)
        return sum(array.nbytes for array in arrays) + self.terminated.nbytes


@dataclass(frozen=True)
class ReplaySample:
    observations: NDArray[np.float32]  # raw, (batch, size)
    next_observations: NDArray[np.float32]  # raw; meaningless where next_valid is False
    actions: NDArray[np.int64]
    rewards: NDArray[np.float32]  # raw
    terminated: NDArray[np.bool_]
    next_valid: NDArray[np.bool_]  # same episode at t + 1: the latent pair counts


class RolloutRecorder:
    """Collects the raw observations and rewards of one rollout, step by step."""

    def __init__(self, first_observation: NDArray[Any]) -> None:
        self.observations: list[NDArray[np.float32]] = [_single(first_observation)]
        self.rewards: list[float] = []
        self.dones: list[bool] = []
        self.terminated: list[bool] = []

    def step(
        self, observation: NDArray[Any], reward: NDArray[Any], dones: NDArray[Any], infos: Any
    ) -> None:
        """After env.step: the raw new observation (the reset one after a done) and reward."""
        done = bool(np.asarray(dones).reshape(-1)[0])
        truncated = bool(infos[0].get("TimeLimit.truncated", False))
        self.observations.append(_single(observation))
        self.rewards.append(float(np.asarray(reward).reshape(-1)[0]))
        self.dones.append(done)
        self.terminated.append(done and not truncated)

    def finish(self, actions: NDArray[Any], mask: NDArray[np.bool_]) -> RolloutRecord:
        """Close the record with the rollout buffer's actions, shape (n, 1, heads)."""
        observations = np.stack(self.observations)
        steps = len(self.rewards)
        flat = np.asarray(actions).reshape(steps, -1).astype(np.int64)
        return RolloutRecord(
            continuous=observations[:, mask].astype(np.float32),
            discrete=observations[:, ~mask].astype(np.float16),
            actions=flat,
            rewards=np.asarray(self.rewards, dtype=np.float32),
            dones=np.asarray(self.dones, dtype=np.bool_),
            terminated=np.asarray(self.terminated, dtype=np.bool_),
        )


def _single(observation: NDArray[Any]) -> NDArray[np.float32]:
    array = np.asarray(observation, dtype=np.float32)
    return array.reshape(-1) if array.ndim == 1 else array[0].reshape(-1)


class Replay:
    """Ring buffer of the last `capacity` rollouts; uniform sampling over their transitions."""

    def __init__(self, capacity: int, mask: NDArray[np.bool_] | None = None) -> None:
        if capacity <= 0:
            raise ValueError("Replay capacity must be positive")
        self.mask = continuous_mask() if mask is None else mask
        self.records: deque[RolloutRecord] = deque(maxlen=capacity)

    def add(self, record: RolloutRecord) -> None:
        if record.steps > 0:
            self.records.append(record)  # the oldest rollout drops out

    def __len__(self) -> int:
        return sum(record.steps for record in self.records)

    @property
    def nbytes(self) -> int:
        return sum(record.nbytes for record in self.records)

    def _rows(self, record: RolloutRecord, rows: NDArray[np.int64]) -> NDArray[np.float32]:
        out = np.empty((len(rows), self.mask.size), dtype=np.float32)
        out[:, self.mask] = record.continuous[rows]
        out[:, ~self.mask] = record.discrete[rows]
        return out

    def sample(self, size: int) -> ReplaySample:
        """`size` transitions, uniform with replacement (global NumPy RNG, saved per checkpoint)."""
        total = len(self)
        if total == 0:
            raise ValueError("Replay is empty")
        picks = np.random.randint(total, size=size)
        ends = np.cumsum([record.steps for record in self.records])
        which = np.searchsorted(ends, picks, side="right")
        parts: list[ReplaySample] = []
        for index in np.unique(which):
            record = self.records[int(index)]
            start = int(ends[index]) - record.steps
            steps = (picks[which == index] - start).astype(np.int64)
            dones = record.dones[steps]
            parts.append(
                ReplaySample(
                    observations=self._rows(record, steps),
                    next_observations=self._rows(record, steps + 1),
                    actions=record.actions[steps],
                    rewards=record.rewards[steps],
                    terminated=record.terminated[steps],
                    next_valid=~dones,
                )
            )
        return ReplaySample(
            *(np.concatenate([getattr(part, name) for part in parts]) for name in _SAMPLE_FIELDS)
        )


_SAMPLE_FIELDS = tuple(ReplaySample.__dataclass_fields__)


def _tensor(array: NDArray[Any], device: torch.device) -> torch.Tensor:
    """float32 on the learner device; the normalizer returns float64."""
    return torch.as_tensor(np.asarray(array, dtype=np.float32), device=device)


# --- learner -----------------------------------------------------------------------------------


class AuxiliaryLearner:
    """Heads, EMA target, own Adam and replay of one learner; the extractor is the policy's.

    The Adam covers the extractor and the online heads. It is separate from the policy's, so the
    PPO moment estimates never see auxiliary gradients and the policy optimizer keeps the layout
    that frozen evaluation loads. With its own Adam a constant loss weight would cancel out, so
    the phase weight scales its step size instead (see `update`).
    """

    def __init__(
        self,
        extractor: nn.Module,
        features_dim: int,
        nvec: Sequence[int],
        *,
        replay_rollouts: int,
        target_ema: float,
        device: torch.device | str,
    ) -> None:
        self.extractor = extractor
        self.nvec = [int(n) for n in nvec]
        self.target_ema = target_ema
        self.device = torch.device(device)
        self.model = AuxiliaryModel(extractor, features_dim, self.nvec).to(self.device)
        trained = [*extractor.parameters(), *self.model.heads.parameters()]
        self.optimizer = torch.optim.Adam(trained, eps=1e-5)  # SB3's policy Adam epsilon
        self.replay = Replay(replay_rollouts)

    def losses(self, sample: ReplaySample, normalizer: Any) -> dict[str, torch.Tensor]:
        """The three losses of one sampled batch; observations normalized with current stats."""
        device = self.device
        obs = _tensor(normalizer.normalize_obs(sample.observations), device)
        nxt = _tensor(normalizer.normalize_obs(sample.next_observations), device)
        scaled = np.asarray(normalizer.normalize_reward(sample.rewards), dtype=np.float32)
        reward = torch.as_tensor(scaled, device=device)
        terminated = torch.as_tensor(sample.terminated, dtype=torch.float32, device=device)
        valid = torch.as_tensor(sample.next_valid, dtype=torch.float32, device=device)
        actions = one_hot_actions(torch.as_tensor(sample.actions, device=device), self.nvec)
        heads = self.model.heads
        joint = torch.cat([self.extractor(obs), actions], dim=1)
        predicted = heads.predictor(heads.projection(heads.transition(joint)))
        with torch.no_grad():
            target = self.model.target_projection(self.model.target_extractor(nxt))
        cosine = functional.cosine_similarity(predicted, target, dim=1)
        latent = ((2.0 - 2.0 * cosine) * valid).sum() / valid.sum().clamp(min=1.0)
        return {
            "latent": latent,
            "reward": functional.smooth_l1_loss(heads.reward(joint).squeeze(1), reward),
            "done": functional.binary_cross_entropy_with_logits(
                heads.done(joint).squeeze(1), terminated
            ),
        }

    def update(
        self,
        normalizer: Any,
        *,
        steps: int,
        batch: int,
        learning_rate: float,
        max_grad_norm: float,
    ) -> dict[str, float]:
        """`steps` Adam steps on the sum of the losses; mean of each loss over the steps.

        `learning_rate` is the phase step size (learner: `aux_coef` x the current PPO rate).
        After each step the EMA target follows the online extractor and projection.
        """
        for group in self.optimizer.param_groups:
            group["lr"] = learning_rate
        sums = dict.fromkeys(LOSSES, 0.0)
        trained = [p for group in self.optimizer.param_groups for p in group["params"]]
        for _ in range(steps):
            losses = self.losses(self.replay.sample(batch), normalizer)
            total = losses["latent"] + losses["reward"] + losses["done"]
            self.optimizer.zero_grad()
            total.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(trained, max_grad_norm)
            self.optimizer.step()
            ema_update(self.model.target_extractor, self.extractor, self.target_ema)
            ema_update(self.model.target_projection, self.model.heads.projection, self.target_ema)
            for name in LOSSES:
                sums[name] += float(losses[name].detach().cpu())
        return {name: value / max(steps, 1) for name, value in sums.items()}

    def save(self, path: Path) -> None:
        """Heads, EMA target and optimizer state; the replay is never saved."""
        state = {
            "format": STATE_FORMAT,
            "model": self.model.state_dict(),
            "optimizer": self.optimizer.state_dict(),
        }
        torch.save(state, path)

    def load(self, path: Path) -> None:
        state = torch.load(path, map_location=self.device, weights_only=True)
        if not isinstance(state, dict) or state.get("format") != STATE_FORMAT:
            raise ValueError(f"Unsupported auxiliary state in {path}")
        self.model.load_state_dict(state["model"])
        self.optimizer.load_state_dict(state["optimizer"])
