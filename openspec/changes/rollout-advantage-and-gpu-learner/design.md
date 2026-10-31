## Context

`full-batch-structured-learner` (contract `ee4f6599...`) set `batch_size` = `n_steps` = 1024,
because sb3-contrib 2.9 normalizes advantages per minibatch (`ppo_recurrent.py` 355-356) and
`RecurrentRolloutBuffer.get` (`common/recurrent/buffers.py` 184-198) yields contiguous slices
after one random rotation: with one env and batch 128 every minibatch was part of one episode.
The full batch fixes the normalization but leaves one gradient step per epoch, at most 10 per
rollout. The Windows learner PC has an RTX 4070 that the CPU torch wheel cannot use.

## Decision 1: normalize the advantages once per rollout

`learner.PureRecurrentPPO` subclasses RecurrentPPO. `train` first calls
`normalize_rollout_advantages(buffer)`: `(A - mean(A)) / (std(A) + 1e-8)` over all
`n_steps x n_envs` steps, in place, then runs the upstream loop without the per-minibatch
normalization (`normalize_advantage` is forced to False). The returns were computed from the raw
advantages in `compute_returns_and_advantage`, so the value targets do not change. Mean and std
do not depend on the layout, so it does not matter whether the buffer has already flattened its
arrays; `train` runs once per rollout and the buffer is refilled before the next one.

With batch 256 a minibatch is still a contiguous slice of about 1-2 episodes, but its advantages
keep their sign and size relative to the whole rollout: a 3-room episode still pushes its actions
up against a 1-room one. Each epoch makes 4 gradient steps (up to 40 per rollout, 4x the full
batch). BPTT is again cut at minibatch borders (at most 256 steps); the full batch covered whole
episodes. That is the trade-off accepted for 4x more steps.

Alternatives: overriding `RecurrentRolloutBuffer.get` to shuffle whole sequences would also help,
but changes padding and memory and is a larger fork of library code; it stays a later option.
A wrapper that sets `normalize_advantage = False` and normalizes in `collect_rollouts` would work
for Decision 1 alone, but Decision 2 needs the loop anyway, and later auxiliary losses need it
too, so the loop lives in one subclass.

## Decision 2: target_kl on the mean KL of an epoch

Upstream breaks before the optimizer step of the first minibatch whose approximate KL exceeds
1.5 x `target_kl`. With several small minibatches one noisy minibatch ends the update (2-3.5 of
10 epochs at batch 128). `PureRecurrentPPO.train` still measures the KL of every minibatch before
its step, but checks the mean over the epoch after all its minibatches stepped, and then stops
the remaining epochs. The check is well contained: it is the same loop with the `break` moved.
`train/approx_kl` is still the mean of the last epoch, and `n_updates` still counts epochs, so
`train.csv` shows the epochs run per update as before.

## Decision 3: the contract names the learner

`advantage_normalization: Literal["rollout"]` is a required contract field and selects
`PureRecurrentPPO` for fresh models and resume (`Algo.load(..., custom_objects=hyper)`). The
saved zip does not record the class; SB3 rebuilds it from `cls`, and the saved attributes
(`advantage_normalization`, `normalize_advantage` False) are restored from the data. Frozen
evaluation (`CheckpointPolicy`) loads the same file with plain RecurrentPPO, which is correct
because inference does not use the training loop. Keep the class name and module stable.

## Decision 4: cuda without fallback

`contract.device: Literal["cpu", "cuda"]`. SB3's `get_device` silently returns the CPU when
CUDA is missing, so `training.require_device` refuses `cuda` with a `TrainingConfigError` that
names the torch version and CUDA build, before an environment or model exists. The forever
supervisor calls it after loading the config, so a missing GPU stops it as `config refused`
before any game session. Rollout inference runs on the same device (SB3 moves each observation
with `obs_as_tensor`); `ContinuousVecNormalize` stays numpy. SB3 `load` passes `map_location` to
`torch.load` and the optimizer state follows its parameters, so a checkpoint saved on cuda loads
on cpu (frozen evaluation always uses `device="cpu"`) and vice versa. The RNG state saved per
checkpoint is the CPU generator only; GPU kernels (cuDNN LSTM) are not bit-reproducible anyway.

Torch is pinned in `scripts/TorchPin.ps1`: `2.14.1+cu130` from
`https://download.pytorch.org/whl/cu130` (variants on that index for cp312 win_amd64: cu126,
cu130, cu132). CUDA 13.0 needs driver 580 or newer (the PC has 610.88) and supports Ada (RTX
4070); the Windows wheel bundles its CUDA libraries and has the same `Requires-Dist` as the CPU
wheel, so `requirements-lock.txt` does not change. `Bootstrap.ps1` installs it (`-CpuTorch` for
the CPU build), and `Check.ps1` fails unless the installed torch is the pinned build and prints
`cuda_available`. macOS keeps the PyPI CPU torch and tests on the CPU only.

## Update time (this Mac, CPU)

One update = 1024 steps, 10 epochs, LSTM 256, structured features, synthetic sparse observations
of size 11691, episodes of 170-220 steps (benchmark of the full-batch change):

| Setup | Seconds per update | Epochs run | Peak RSS |
| --- | --- | --- | --- |
| Full batch 1024, plain RecurrentPPO (current lineage) | 17.5-19.4 | 10 | 957 MB |
| Batch 256, `PureRecurrentPPO`, `target_kl` off | 30.7-32.6 | 10 | 607 MB |
| Batch 256, `PureRecurrentPPO`, `target_kl` 0.03 | 30.7-32.8 | 10 | 533 MB |

Four times the gradient steps cost about 1.7x the time on the CPU (less padding per minibatch,
less memory), still below the 60 s target with the game paused. Two updates per setup, 8 torch
threads; script `bench_update_rollout.py` (adapted from the full-batch benchmark).

The GPU time is not measured; `train.csv` `update_seconds` on Windows will show it.

## Lineage

The contract gains `advantage_normalization` and `device` changes to `cuda`, so the hash changes
to `5eb6f93af48955b55130c410fff59d109bea133d81688a023bbd6c59687c4f14`. The network shape is
unchanged, but the update rule and the device are part of the contract, and one contract binds
one lineage. The full-batch structured run is kept as
`runs/pure-v4-full-batch-structured`; `pure-v4` restarts with `--initialize`.

## Risks

- Only native Windows can verify: the CUDA wheel installs and sees the GPU, the cuDNN LSTM with
  padded sequences is numerically fine, GPU memory for the padded batch fits in 12 GiB next to the
  game, and the game frame rate does not suffer while the GPU runs rollout inference.
- Smaller minibatches make each step noisier; target_kl on the epoch mean may let an epoch move
  further than before. `approx_kl` and `clip_fraction` in `train.csv` show it.
- Rollout inference on the GPU costs a host-device copy per step (one observation of 11691
  floats); if `rollout_seconds` grows, inference could move back to the CPU in a later change.
- The superseded full-batch requirement must be dropped when both changes are archived.
