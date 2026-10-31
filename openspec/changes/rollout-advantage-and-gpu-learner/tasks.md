## 1. Implementation

- [x] 1.1 `learner.py`: `PureRecurrentPPO` (rollout-level advantage normalization, epoch-mean KL
  stop) and `normalize_rollout_advantages`.
- [x] 1.2 `training.py`: contract `advantage_normalization: rollout` and `device: cpu | cuda`;
  `require_device`; fresh and resumed pure models use `PureRecurrentPPO` on the contract device.
- [x] 1.3 `session_runner.py`: the forever supervisor refuses a `cuda` contract without CUDA.
- [x] 1.4 `training-pure-v4.yaml`: `device: cuda`, `advantage_normalization: rollout`,
  `batch_size` 256, comment block.
- [x] 1.5 `scripts/TorchPin.ps1`, `Bootstrap.ps1` (CUDA wheel, `-CpuTorch`), `Check.ps1` (pinned
  build check).
- [x] 1.6 `scripts/smoke_rl.py`: explicit CPU, `PureRecurrentPPO` with two minibatches, GPU-to-CPU
  checkpoint leg when CUDA is available.
- [x] 1.7 Tests: `tests/test_rollout_advantage_and_gpu_learner.py`; pinned contract hash, shipped
  config and the CPU device of the test configs updated.
- [x] 1.8 Docs: RL_DESIGN, SETUP_REPORT, TRAINING_SESSION, STATUS, RUNTIME_AUTHORITY.

## 2. Verification

- [x] 2.1 Offline gate (two known macOS-only failures), `scripts/smoke_rl.py` and strict OpenSpec
  validation; update time measured on the development Mac CPU.
- [ ] 2.2 Windows: `scripts/Bootstrap.ps1` installs torch `2.14.1+cu130`; `scripts/Check.ps1`
  passes and prints `cuda_available True`; `scripts/Smoke-RL.ps1` reports
  `cuda_to_cpu_checkpoint: passed`.
- [ ] 2.3 Stop the full-batch structured run, rename `runs\pure-v4` to
  `runs\pure-v4-full-batch-structured`; one-hour native session with `--initialize`; check
  `update_seconds`, `n_updates` per rollout and GPU memory.
- [ ] 2.4 Native 150k steps: explained variance above 0.6, rooms per episode above 2.3.
- [ ] 2.5 Acceptance: compare `episodes.csv` and `train.csv` with the full-batch structured and
  reward v12 schema 9 runs at equal steps: rooms per episode, share of episodes with 3+ rooms,
  stall share, explained variance, epochs run per update.
- [ ] 2.6 Archive after `full-batch-structured-learner`; its requirement "One full-rollout
  minibatch per epoch" is superseded by "Several minibatches per epoch" and is dropped then.
