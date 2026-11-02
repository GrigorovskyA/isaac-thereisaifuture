"""Behaviour cloning from human demos (contract `pretraining: demo_bc_v1`).

A fresh lineage first learns to imitate human demo sequences (`demo_dataset.DemoSequence`): the
policy is trained on the masked mean negative log-likelihood of the demo actions, summed over the
move, shoot and use heads, through the same features extractor and actor LSTM that PPO trains.
During RL the same loss then runs as a regulariser after each PPO update, with a weight that
decays linearly to 0 (`coef_at`), so PPO does not wash the demo skill out before the critic has
learned values for it.

Sequences are cut into windows of `seq_len` steps; the last partial window of a sequence is
padded and masked. A batch is `batch_sequences` random windows, flattened window-major (all steps
of window 0, then window 1, ...) as sb3-contrib's `_process_sequence` expects, with zero LSTM
states and an episode start at each window's first step. Demo observations are raw encoder
vectors and are normalized at sampling time with the model's VecNormalize statistics, on the
policy's device, so they match what the policy sees in RL. Whole sequences are held out (seeded)
to measure the imitation; pretraining keeps the weights with the best holdout NLL and stops early
when it no longer improves.

The Adam of this module is its own and covers all policy parameters; the value head gets no
gradient. It is not saved: a resumed session starts it fresh (Adam's bias correction keeps the
first steps at the configured step size). Torch is imported at module load.
"""

import copy
import time
from collections.abc import Callable, Sequence
from typing import Any, Literal

import numpy as np
import torch
from numpy.typing import NDArray
from sb3_contrib.common.recurrent.type_aliases import RNNStates

from .demo_dataset import DemoSequence
from .normalization import VARIANCE_FLOOR, ContinuousVecNormalize

Pretraining = Literal["none", "demo_bc_v1"]
NONE: Pretraining = "none"  # contract value `pretraining`: learn from scratch (earlier lineages)
DEMO_BC: Pretraining = "demo_bc_v1"
PRETRAININGS: tuple[Pretraining, ...] = (NONE, DEMO_BC)
HEADS = ("move", "shoot", "use")  # the MultiDiscrete action heads, in order
FIT_CHUNK = 4096  # rows per normalizer update, to bound the float32 copy
FINAL_WINDOW = 100  # the summary's train NLL is the mean over the last steps of pretraining


def linear_coef(coef: float, decay_timesteps: int, timesteps: int) -> float:
    """`coef` at timestep 0, falling linearly to 0 at `decay_timesteps` and staying there."""
    if decay_timesteps <= 0:
        return 0.0
    return coef * max(0.0, 1.0 - timesteps / decay_timesteps)


def holdout_split(count: int, fraction: float, seed: int) -> tuple[list[int], list[int]]:
    """Indices of the train and holdout sequences; at least one sequence stays for training.

    With two or more sequences and a positive fraction, at least one is held out.
    """
    held = round(count * fraction)
    if fraction > 0 and count >= 2:
        held = max(held, 1)
    held = min(held, count - 1) if count > 0 else 0
    order = np.random.default_rng(seed).permutation(count)
    holdout = sorted(int(i) for i in order[:held])
    train = sorted(int(i) for i in order[held:])
    return train, holdout


def _windows(
    sequences: Sequence[DemoSequence], indices: Sequence[int], seq_len: int
) -> NDArray[Any]:
    """(sequence index, start step) of each window of the given sequences."""
    rows = [
        (index, start)
        for index in indices
        for start in range(0, len(sequences[index].actions), seq_len)
    ]
    return np.asarray(rows, dtype=np.int64).reshape(-1, 2)


class DemoBatch:
    """Raw window-major rows of a batch of windows; padded rows have mask False."""

    def __init__(self, sequences: Sequence[DemoSequence], windows: NDArray[Any], seq_len: int):
        count = len(windows)
        width = sequences[0].observations.shape[1]
        heads = sequences[0].actions.shape[1]
        self.windows = count
        dtype = sequences[0].observations.dtype  # float16 demos stay float16 until the device
        self.observations = np.zeros((count * seq_len, width), dtype=dtype)
        self.actions = np.zeros((count * seq_len, heads), dtype=np.int64)
        self.mask = np.zeros(count * seq_len, dtype=bool)
        for row, (index, start) in enumerate(windows):
            sequence = sequences[int(index)]
            stop = min(int(start) + seq_len, len(sequence.actions))
            length = stop - int(start)
            at = row * seq_len
            self.observations[at : at + length] = sequence.observations[start:stop]
            self.actions[at : at + length] = sequence.actions[start:stop]
            self.mask[at : at + length] = True
        self.episode_starts = np.zeros(count * seq_len, dtype=np.float32)
        self.episode_starts[::seq_len] = 1.0


def zero_lstm_states(policy: Any, count: int, device: torch.device) -> RNNStates:
    """Zero (h, c) of the actor and critic LSTMs for `count` sequences."""

    def zeros(lstm: Any) -> tuple[torch.Tensor, torch.Tensor]:
        shape = (lstm.num_layers, count, lstm.hidden_size)
        return torch.zeros(shape, device=device), torch.zeros(shape, device=device)

    pi = zeros(policy.lstm_actor)
    vf = zeros(policy.lstm_critic) if policy.lstm_critic is not None else pi
    return RNNStates(pi=pi, vf=vf)


def normalize_on_device(normalizer: Any, raw: NDArray[Any], device: torch.device) -> torch.Tensor:
    """`normalizer.normalize_obs(raw)` as a float32 tensor on `device`.

    The continuous-only normalizer is applied on the device (the numpy path costs about 0.15 s
    per batch of 1024 rows); any other normalizer goes through its own numpy method.
    """
    if normalizer is None or not normalizer.norm_obs:
        return torch.as_tensor(raw, device=device).float()
    if not isinstance(normalizer, ContinuousVecNormalize):
        normalized = normalizer.normalize_obs(raw.astype(np.float32))
        return torch.as_tensor(np.asarray(normalized, dtype=np.float32), device=device)
    obs = torch.as_tensor(raw, device=device).float()
    rms: Any = normalizer.obs_rms  # one RunningMeanStd: the observation space is a Box
    mean = torch.as_tensor(rms.mean, dtype=torch.float32, device=device)
    var = torch.as_tensor(rms.var, dtype=torch.float32, device=device)
    std = torch.sqrt(torch.clamp(var, min=VARIANCE_FLOOR) + normalizer.epsilon)
    clip = float(normalizer.clip_obs)
    scaled = torch.clamp((obs - mean) / std, -clip, clip)
    continuous = torch.as_tensor(normalizer.continuous, device=device)
    return torch.where(continuous, scaled, obs)


def action_distribution(
    policy: Any, obs: torch.Tensor, lstm_states: RNNStates, episode_starts: torch.Tensor
) -> Any:
    """The actor half of `PureRecurrentPPO._evaluate_actions`: the action distribution only."""
    features = policy.extract_features(obs)
    pi_features = features if policy.share_features_extractor else features[0]
    latent_pi, _ = policy._process_sequence(
        pi_features, lstm_states.pi, episode_starts, policy.lstm_actor
    )
    latent_pi = policy.mlp_extractor.forward_actor(latent_pi)
    return policy._get_action_dist_from_latent(latent_pi)


class DemoLearner:
    """Demo windows, holdout split, own Adam and the decaying regulariser weight of one lineage."""

    def __init__(
        self,
        sequences: Sequence[DemoSequence],
        *,
        seq_len: int = 64,
        batch_sequences: int = 16,
        holdout_fraction: float = 0.1,
        seed: int = 0,
        bc_coef: float = 1.0,
        bc_steps: int = 32,
        bc_decay_timesteps: int = 1_000_000,
        device: torch.device | str | None = None,
    ) -> None:
        if not sequences:
            raise ValueError("Behaviour cloning needs at least one demo sequence")
        if seq_len <= 0 or batch_sequences <= 0:
            raise ValueError("seq_len and batch_sequences must be positive")
        if not 0 <= holdout_fraction < 1:
            raise ValueError("holdout_fraction must be in [0, 1)")
        self.sequences = list(sequences)
        self.seq_len = seq_len
        self.batch_sequences = batch_sequences
        self.bc_coef = bc_coef
        self.bc_steps = bc_steps
        self.bc_decay_timesteps = bc_decay_timesteps
        self.device = torch.device(device) if device is not None else None
        self.train_indices, self.holdout_indices = holdout_split(
            len(self.sequences), holdout_fraction, seed
        )
        self.train_windows = _windows(self.sequences, self.train_indices, seq_len)
        self.holdout_windows = _windows(self.sequences, self.holdout_indices, seq_len)
        self.rng = np.random.default_rng(seed + 1)
        self._optimizer: torch.optim.Adam | None = None
        self._optimized: Any = None  # the policy the optimizer was built for

    @property
    def steps(self) -> int:
        """Demo steps over all sequences."""
        return sum(len(sequence.actions) for sequence in self.sequences)

    def _split_steps(self, indices: Sequence[int]) -> int:
        return sum(len(self.sequences[i].actions) for i in indices)

    def coef_at(self, num_timesteps: int) -> float:
        """Regulariser weight at this RL timestep: `bc_coef` falling linearly to 0."""
        return linear_coef(self.bc_coef, self.bc_decay_timesteps, num_timesteps)

    def fit_normalizer(self, venv: Any) -> None:
        """Update the normalizer's observation statistics with every demo observation."""
        for sequence in self.sequences:
            for start in range(0, len(sequence.observations), FIT_CHUNK):
                chunk = sequence.observations[start : start + FIT_CHUNK]
                venv.obs_rms.update(chunk.astype(np.float32))

    def sample(self) -> DemoBatch:
        """`batch_sequences` train windows drawn uniformly with replacement."""
        picks = self.rng.integers(0, len(self.train_windows), size=self.batch_sequences)
        return DemoBatch(self.sequences, self.train_windows[picks], self.seq_len)

    def _forward(self, model: Any, batch: DemoBatch) -> tuple[Any, torch.Tensor, torch.Tensor]:
        """Action distribution, actions and mask of a batch, observations normalized."""
        policy = model.policy
        device = self.device or policy.device
        obs = normalize_on_device(model.get_vec_normalize_env(), batch.observations, device)
        starts = torch.as_tensor(batch.episode_starts, device=device)
        states = zero_lstm_states(policy, batch.windows, device)
        distribution = action_distribution(policy, obs, states, starts)
        actions = torch.as_tensor(batch.actions, device=device)
        mask = torch.as_tensor(batch.mask, device=device)
        return distribution, actions, mask

    def loss(self, model: Any, batch: DemoBatch) -> torch.Tensor:
        """Masked mean NLL of the demo actions (log-probabilities summed over the heads)."""
        distribution, actions, mask = self._forward(model, batch)
        log_prob: torch.Tensor = distribution.log_prob(actions)
        return -log_prob[mask].mean()

    def _adam(self, policy: Any, learning_rate: float) -> torch.optim.Adam:
        if self._optimizer is None or self._optimized is not policy:
            self._optimizer = torch.optim.Adam(policy.parameters(), lr=learning_rate, eps=1e-5)
            self._optimized = policy
        for group in self._optimizer.param_groups:
            group["lr"] = learning_rate
        return self._optimizer

    def _fit(
        self, model: Any, steps: int, learning_rate: float, max_grad_norm: float
    ) -> list[float]:
        """`steps` Adam steps on sampled train windows; the loss of each step."""
        policy = model.policy
        policy.set_training_mode(True)
        optimizer = self._adam(policy, learning_rate)
        losses: list[float] = []
        for _ in range(steps):
            loss = self.loss(model, self.sample())
            optimizer.zero_grad()
            loss.backward()  # type: ignore[no-untyped-call]
            torch.nn.utils.clip_grad_norm_(policy.parameters(), max_grad_norm)
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        return losses

    def regularize(
        self, model: Any, *, steps: int, learning_rate: float, max_grad_norm: float
    ) -> float:
        """The RL-phase regulariser: `steps` BC steps; mean loss over them."""
        losses = self._fit(model, steps, learning_rate, max_grad_norm)
        return float(np.mean(losses)) if losses else 0.0

    @torch.no_grad()
    def evaluate(self, model: Any) -> dict[str, Any] | None:
        """Holdout NLL and per-head argmax accuracy over every holdout window; None without one."""
        if len(self.holdout_windows) == 0:
            return None
        policy = model.policy
        training = policy.training
        policy.set_training_mode(False)
        nll = 0.0
        correct = np.zeros(len(HEADS))
        total = 0
        try:
            for start in range(0, len(self.holdout_windows), self.batch_sequences):
                windows = self.holdout_windows[start : start + self.batch_sequences]
                batch = DemoBatch(self.sequences, windows, self.seq_len)
                distribution, actions, mask = self._forward(model, batch)
                nll -= float(distribution.log_prob(actions)[mask].sum().cpu())
                for head, categorical in enumerate(distribution.distribution):
                    guess = categorical.probs.argmax(dim=1)
                    correct[head] += float((guess == actions[:, head])[mask].sum().cpu())
                total += int(mask.sum().cpu())
        finally:
            policy.set_training_mode(training)
        return {
            "nll": nll / total,
            "accuracy": {name: correct[i] / total for i, name in enumerate(HEADS)},
        }

    def majority_accuracy(self) -> dict[str, float] | None:
        """Holdout accuracy of always choosing the most common train action of each head."""
        if not self.holdout_indices:
            return None
        train = np.concatenate([self.sequences[i].actions for i in self.train_indices])
        held = np.concatenate([self.sequences[i].actions for i in self.holdout_indices])
        return {
            name: float(np.mean(held[:, i] == np.bincount(train[:, i]).argmax()))
            for i, name in enumerate(HEADS)
        }

    def pretrain(
        self,
        model: Any,
        *,
        steps: int,
        learning_rate: float,
        max_grad_norm: float,
        log_every: int = 1000,
        patience: int = 0,
        log: Callable[[dict[str, Any]], None] | None = None,
    ) -> dict[str, Any]:
        """Behaviour cloning of a fresh model; a summary with the holdout before and after.

        Every `log_every` steps the holdout is evaluated and `log` gets the step, the mean train
        NLL since the last call and the holdout NLL. The policy weights with the best holdout NLL
        are restored at the end; with `patience` > 0, pretraining stops after that many
        evaluations without a better one. Fit the normalizer first, so the observations are
        scaled as in RL.
        """
        started = time.perf_counter()
        before = self.evaluate(model)
        best_nll = before["nll"] if before is not None else None
        best_state: dict[str, Any] | None = None
        best_step = 0
        stale = 0
        recent: list[float] = []
        done = 0
        while done < steps:
            chunk = min(log_every, steps - done) if log_every > 0 else steps - done
            losses = self._fit(model, chunk, learning_rate, max_grad_norm)
            done += chunk
            recent = [*recent, *losses][-FINAL_WINDOW:]
            holdout = self.evaluate(model)
            if log is not None:
                log(
                    {
                        "step": done,
                        "train_nll": float(np.mean(losses)),
                        "holdout_nll": holdout["nll"] if holdout is not None else None,
                    }
                )
            if holdout is None:
                continue
            if best_nll is None or holdout["nll"] < best_nll:
                best_nll, best_step, stale = holdout["nll"], done, 0
                best_state = copy.deepcopy(model.policy.state_dict())
            else:
                stale += 1
                if patience > 0 and stale >= patience:
                    break
        if best_state is not None and best_step != done:
            model.policy.load_state_dict(best_state)
        return {
            "steps": done,
            "best_step": best_step if best_state is not None else done,
            "sequences": len(self.train_indices),
            "holdout_sequences": len(self.holdout_indices),
            "demo_steps": self._split_steps(self.train_indices),
            "holdout_demo_steps": self._split_steps(self.holdout_indices),
            "seq_len": self.seq_len,
            "batch_sequences": self.batch_sequences,
            "train_nll": float(np.mean(recent)) if recent else None,
            "holdout_before": before,
            "holdout_after": self.evaluate(model),
            "majority_accuracy": self.majority_accuracy(),
            "seconds": time.perf_counter() - started,
        }
