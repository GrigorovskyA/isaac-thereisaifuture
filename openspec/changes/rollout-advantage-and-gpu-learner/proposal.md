## Why

Rewards v9 to v12 all plateaued at about 2 rooms per episode (7-12% of the episodes reached 3+
rooms, slope about 0 after 75k steps). `full-batch-structured-learner` found the learner faults
and set `batch_size` = `n_steps` = 1024 as the fix for one of them: sb3-contrib normalizes the
advantages per minibatch (`ppo_recurrent.py` 355) and slices recurrent minibatches contiguously
after one random rotation (`common/recurrent/buffers.py` 184-198), so a small minibatch was a
piece of one episode and its normalization erased the difference between episodes. One
minibatch per epoch repairs that, but leaves at most 10 gradient steps per 1024-step rollout
(16-28 before, 80 nominal), about 10 per 4 minutes of play.

The CPU learner also limits what the next changes can afford: one structured full-batch update
takes 18-39 s on the development Mac with the game paused. The Windows learner machine has an
RTX 4070 (12 GiB, driver 610.88), but the project installs the CPU torch wheel (`2.14.1+cpu`).

## What Changes

- `learner.py`: `PureRecurrentPPO`, a RecurrentPPO subclass whose `train` normalizes the
  advantages once over the whole rollout buffer (mean and std over all steps) and never per
  minibatch, and stops the epochs when the mean approximate KL over an epoch's minibatches
  exceeds 1.5 x `target_kl` (upstream stops at the first minibatch over it). It is the place for
  later auxiliary losses.
- Contract field `advantage_normalization: rollout` (required); `contract.device` accepts `cpu`
  or `cuda`. Training and resume build `PureRecurrentPPO`; frozen evaluation still loads the
  same model file with RecurrentPPO on the CPU.
- `training.require_device`: a `cuda` contract without a usable CUDA torch is refused with a
  clear error before any environment or model exists (SB3 would silently use the CPU); the
  forever supervisor refuses it before any session.
- `configs/training-pure-v4.yaml`: `device: cuda`, `advantage_normalization: rollout`,
  `batch_size` 256 (4 minibatches per epoch), `n_steps` 1024, `n_epochs` 10, `target_kl` 0.03,
  other hyperparameters unchanged. New contract hash
  `5eb6f93af48955b55130c410fff59d109bea133d81688a023bbd6c59687c4f14`.
- Windows dependencies: `scripts/TorchPin.ps1` pins torch `2.14.1+cu130` from
  `https://download.pytorch.org/whl/cu130`; `Bootstrap.ps1` installs it (`-CpuTorch` keeps the
  CPU wheel), `Check.ps1` refuses another torch build. macOS stays on the CPU.
- `scripts/smoke_rl.py` runs on an explicit CPU device with `PureRecurrentPPO`; when CUDA is
  available it also trains on the GPU and loads that model on the CPU.
- The full-batch structured run is kept as `runs/pure-v4-full-batch-structured`; its
  checkpoints are refused. `pure-v4` restarts with `--initialize`.

## Non-goals

- No reward, observation, action, hint or Lua change; reward v12 and schema 9 stay.
- No auxiliary losses yet (a later change adds them to `PureRecurrentPPO.train`).
- No change of learning rate, entropy coefficient, gamma, lambda, clip range, `n_steps`,
  `n_epochs` or `target_kl`.
- No shuffling of recurrent sequences across the rollout and no multi-env collection.
- VecNormalize stays numpy on the CPU; no mixed precision.

## Acceptance

- Offline gate (`scripts/check.sh` with the two known macOS-only failures / `Check.ps1`),
  `scripts/smoke_rl.py` and strict OpenSpec validation pass.
- Tests show: one normalization per rollout and none per minibatch; the epoch-mean KL stop;
  training and resume use `PureRecurrentPPO`; a `cuda` contract without CUDA is refused by
  `train` and the forever supervisor; the contract refuses the earlier lineage.
- Windows: `Check.ps1` passes with torch `2.14.1+cu130` and `cuda_available True`;
  `Smoke-RL.ps1` reports `cuda_to_cpu_checkpoint: passed`; `update_seconds` in `train.csv` of the
  first native hour is below the full-batch CPU run's.
- Native 150k steps against the full-batch structured and reward v12 schema 9 runs at equal
  steps: explained variance above 0.6, rooms per episode above 2.3 and a rising share of
  episodes with 3+ rooms.

## Impact

- `src/isaac_threrisaifuture/{learner,training,session_runner}.py`,
  `configs/training-pure-v4.yaml`, `scripts/{smoke_rl.py,Bootstrap.ps1,Check.ps1,TorchPin.ps1}`,
  tests, docs.
- Lineage `pure-v4` restarts with `--initialize`; the Windows venv needs the CUDA torch wheel
  first.
