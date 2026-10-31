"""Episodic E3B bonus times the cross-run count novelty (contract `intrinsic: e3b_count_v1`).

E3B (Henaff et al., NeurIPS 2022, arXiv 2210.05805) pays b_t = phi(s_t+1)^T C_t^-1 phi(s_t+1),
the elliptical novelty of the next state's embedding against the embeddings already seen in the
episode: C_0 = lambda I, C_t+1 = C_t + phi phi^T, reset at every episode start, with C^-1 kept by
Sherman-Morrison. phi is the embedding of an inverse-dynamics model g(phi(s_t), phi(s_t+1)) -> a_t,
so it keeps what the agent's action changes and drops what it cannot control. Henaff, Jiang and
Raileanu (ICML 2023, arXiv 2306.03236) show that the episodic bonus works when it is multiplied by
a global (count) bonus and not when the two are added. Here the global factor is the cross-run
novelty count of reward v11/v12 for the (stage, room, cell) key of s_t+1, read only:

    r_int = beta * clip(b_t / std(b) * max(1 / sqrt(N), floor), 0, 1)

with std(b) a running standard deviation of the raw bonus. This is an intrinsic exploration
signal (`docs/UPDATE_DECISION.md`, principle 2): no hint, no observation, no change of the reward
v12 terms. The env adds r_int to the step reward as its own ledger column `e3b`.

The embedding is a separate small copy of the structured extractor (own weights, so the bonus does
not drift with the policy) followed by Linear to `embed_dim`. It reads the raw observation with
the stall clock and the visited-cell grid zeroed (`EXCLUDED_BLOCKS`): a clock or a run-long trace
makes every state unique (E3B paper, section 5, the MiniHack time counter). Raw observations keep
the bonus independent of the policy's running normalizer. Embedding, inverse-dynamics head, their
Adam and the running std are learner state, saved per checkpoint as `e3b.pt`; the episodic matrix
lives only in the current episode. Torch is imported at module load.
"""

import time
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import gymnasium as gym
import numpy as np
import torch
from numpy.typing import NDArray
from torch import nn
from torch.nn import functional

from .auxiliary import Replay
from .encoding import FEATURE_BLOCKS, OBSERVATION_SIZE
from .policy import StructuredFeatures

Intrinsic = Literal["none", "e3b_count_v1"]
NONE: Intrinsic = "none"  # contract value `intrinsic`: no intrinsic reward (earlier lineages)
E3B_COUNT: Intrinsic = "e3b_count_v1"
INTRINSICS: tuple[Intrinsic, ...] = (NONE, E3B_COUNT)
# Observation blocks phi never sees: the stall clock and the run's visited-cell grid of the room.
EXCLUDED_BLOCKS = ("stall", "visited_cells")
EMBED_HIDDEN = 256  # output width of the extractor copy, in front of Linear(256, embed_dim)
IDM_HIDDEN = 256
CLIP = 1.0  # r_int / beta is clipped to [0, CLIP]
STATE_FORMAT = 1  # layout of e3b.pt
STD_EPSILON = 1e-8


def keep_mask() -> NDArray[np.float32]:
    """1.0 for the indices phi reads, 0.0 for `EXCLUDED_BLOCKS` (found in FEATURE_BLOCKS)."""
    mask = np.ones(OBSERVATION_SIZE, dtype=np.float32)
    found: set[str] = set()
    for block in FEATURE_BLOCKS:
        if block.name in EXCLUDED_BLOCKS:
            mask[block.offset : block.offset + block.size] = 0.0
            found.add(block.name)
    if found != set(EXCLUDED_BLOCKS):
        raise ValueError(f"Feature blocks missing from the layout: {set(EXCLUDED_BLOCKS) - found}")
    return mask


class Embedding(nn.Module):
    """phi: masked raw observation -> structured extractor copy -> Linear(256, embed_dim)."""

    keep: torch.Tensor

    def __init__(self, embed_dim: int) -> None:
        super().__init__()
        space = gym.spaces.Box(-1.0, 1.0, (OBSERVATION_SIZE,), np.float32)
        self.extractor = StructuredFeatures(space, features_dim=EMBED_HIDDEN)
        self.out = nn.Linear(EMBED_HIDDEN, embed_dim)
        self.register_buffer("keep", torch.from_numpy(keep_mask()), persistent=False)

    def forward(self, observations: torch.Tensor) -> torch.Tensor:
        return self.out(self.extractor(observations * self.keep))  # type: ignore[no-any-return]


class InverseDynamics(nn.Module):
    """g(phi(s_t), phi(s_t+1)) -> logits of each action head (5, 5 and 4 choices)."""

    def __init__(self, embed_dim: int, nvec: Sequence[int]) -> None:
        super().__init__()
        self.nvec = [int(n) for n in nvec]
        self.net = nn.Sequential(
            nn.Linear(2 * embed_dim, IDM_HIDDEN), nn.ReLU(), nn.Linear(IDM_HIDDEN, sum(self.nvec))
        )

    def forward(self, phi: torch.Tensor, phi_next: torch.Tensor) -> list[torch.Tensor]:
        logits = self.net(torch.cat([phi, phi_next], dim=1))
        return list(torch.split(logits, self.nvec, dim=1))


class EllipticalBonus:
    """Episodic C^-1 in float64, updated by Sherman-Morrison; deterministic on the CPU."""

    def __init__(self, embed_dim: int, ridge: float) -> None:
        if ridge <= 0:
            raise ValueError("The E3B ridge lambda must be positive")
        self.embed_dim = embed_dim
        self.ridge = ridge
        self.inverse = np.eye(embed_dim) / ridge

    def reset(self) -> None:
        """C_0 = lambda I at an episode start."""
        self.inverse = np.eye(self.embed_dim) / self.ridge

    def observe(self, phi: NDArray[np.float64]) -> float:
        """Return b = phi^T C^-1 phi, then C <- C + phi phi^T (C^-1 by Sherman-Morrison)."""
        u = self.inverse @ phi
        bonus = float(phi @ u)
        self.inverse -= np.outer(u, u) / (1.0 + bonus)
        return bonus


class RunningStd:
    """Running standard deviation of the raw bonus (Welford), learner state."""

    def __init__(self) -> None:
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.m2 += delta * (value - self.mean)

    @property
    def std(self) -> float:
        """1.0 until two values are seen, so the first bonus is neither zero nor infinite."""
        if self.count < 2:
            return 1.0
        return max(float(np.sqrt(self.m2 / (self.count - 1))), STD_EPSILON)

    def state(self) -> dict[str, float]:
        return {"count": float(self.count), "mean": self.mean, "m2": self.m2}

    def load(self, state: dict[str, float]) -> None:
        self.count, self.mean, self.m2 = int(state["count"]), float(state["mean"]), state["m2"]


def count_factor(count: int | None, floor: float) -> float:
    """max(1 / sqrt(N), floor) for the cross-run count N of s_t+1's key; floor without a key."""
    if count is None:
        return floor
    return max(1.0 / float(np.sqrt(max(count, 1))), floor)


class E3BLearner:
    """Embedding, inverse dynamics, their Adam, the running std and the episodic bonus.

    The env calls `start_episode` with the first observation (it enters C without pay) and
    `reward` with each next observation and its cross-run count; the learner calls `update` after
    the PPO epochs on transitions sampled from `replay` (the auxiliary replay when there is one).
    """

    def __init__(
        self,
        nvec: Sequence[int],
        *,
        embed_dim: int,
        ridge: float,
        beta: float,
        floor: float,
        replay: Replay,
        device: torch.device | str,
    ) -> None:
        if beta < 0 or not 0 <= floor <= 1:
            raise ValueError("E3B needs beta >= 0 and a floor in [0, 1]")
        self.nvec = [int(n) for n in nvec]
        self.beta = beta
        self.floor = floor
        self.device = torch.device(device)
        self.embedding = Embedding(embed_dim).to(self.device)
        self.idm = InverseDynamics(embed_dim, self.nvec).to(self.device)
        trained = [*self.embedding.parameters(), *self.idm.parameters()]
        self.optimizer = torch.optim.Adam(trained, eps=1e-5)
        self.replay = replay
        self.bonus = EllipticalBonus(embed_dim, ridge)
        self.std = RunningStd()
        self._paid = 0.0  # sum and count of r_int since the last update, for train.csv
        self._steps = 0
        self.step_seconds = 0.0  # wall clock spent in `reward`, for the per-step cost

    @torch.no_grad()
    def embed(self, observation: NDArray[np.float32]) -> NDArray[np.float64]:
        """phi of one raw observation, as float64 on the CPU."""
        tensor = torch.as_tensor(np.asarray(observation, dtype=np.float32), device=self.device)
        phi = self.embedding(tensor.reshape(1, -1))[0]
        out: NDArray[np.float64] = phi.cpu().numpy().astype(np.float64)
        return out

    def start_episode(self, observation: NDArray[np.float32]) -> None:
        self.bonus.reset()
        self.bonus.observe(self.embed(observation))

    def reward(self, observation: NDArray[np.float32], count: int | None) -> float:
        """r_int of a step whose next observation is `observation`; updates C and the std."""
        started = time.perf_counter()
        raw = self.bonus.observe(self.embed(observation))
        self.std.update(raw)
        scaled = raw / self.std.std * count_factor(count, self.floor)
        paid = self.beta * min(max(scaled, 0.0), CLIP)
        self._paid += paid
        self._steps += 1
        self.step_seconds += time.perf_counter() - started
        return paid

    def paid_mean(self) -> float | None:
        """Mean r_int per step since the last call, or None without steps; resets the sum."""
        mean = self._paid / self._steps if self._steps else None
        self._paid, self._steps = 0.0, 0
        return mean

    def idm_loss(
        self,
        observations: NDArray[np.float32],
        next_observations: NDArray[np.float32],
        actions: NDArray[np.int64],
        valid: NDArray[np.bool_],
    ) -> torch.Tensor:
        """Sum over the heads of the cross-entropy, mean over the pairs of one episode."""
        device = self.device
        phi = self.embedding(torch.as_tensor(observations, dtype=torch.float32, device=device))
        nxt = self.embedding(torch.as_tensor(next_observations, dtype=torch.float32, device=device))
        target = torch.as_tensor(actions, dtype=torch.long, device=device)
        weight = torch.as_tensor(valid, dtype=torch.float32, device=device)
        loss = torch.zeros(len(weight), device=device)
        for head, logits in enumerate(self.idm(phi, nxt)):
            loss = loss + functional.cross_entropy(logits, target[:, head], reduction="none")
        return (loss * weight).sum() / weight.sum().clamp(min=1.0)

    def update(
        self, *, steps: int, batch: int, learning_rate: float, max_grad_norm: float
    ) -> float:
        """`steps` Adam steps on replayed pairs; mean inverse-dynamics loss over the steps."""
        for group in self.optimizer.param_groups:
            group["lr"] = learning_rate
        trained = [p for group in self.optimizer.param_groups for p in group["params"]]
        total = 0.0
        for _ in range(steps):
            sample = self.replay.sample(batch)
            loss = self.idm_loss(
                sample.observations, sample.next_observations, sample.actions, sample.next_valid
            )
            self.optimizer.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(trained, max_grad_norm)
            self.optimizer.step()
            total += float(loss.detach().cpu())
        return total / max(steps, 1)

    def save(self, path: Path) -> None:
        """Embedding, inverse dynamics, optimizer and running std; never C^-1 or the replay."""
        state = {
            "format": STATE_FORMAT,
            "embedding": self.embedding.state_dict(),
            "idm": self.idm.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "std": self.std.state(),
        }
        torch.save(state, path)

    def load(self, path: Path) -> None:
        state = torch.load(path, map_location=self.device, weights_only=True)
        if not isinstance(state, dict) or state.get("format") != STATE_FORMAT:
            raise ValueError(f"Unsupported E3B state in {path}")
        self.embedding.load_state_dict(state["embedding"])
        self.idm.load_state_dict(state["idm"])
        self.optimizer.load_state_dict(state["optimizer"])
        self.std.load(state["std"])
