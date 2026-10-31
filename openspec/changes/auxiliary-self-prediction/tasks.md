## 1. Implementation

- [x] 1.1 `auxiliary.py`: action one-hot, heads (transition, projection, predictor, reward,
  done), EMA target, `RolloutRecorder`, `Replay` (raw observations, float16 binary block) and
  `AuxiliaryLearner` (losses, update, save/load).
- [x] 1.2 `learner.py`: `PureRecurrentPPO` takes `auxiliary` and the auxiliary hyperparameters,
  records complete rollouts, runs the auxiliary phase after the PPO epochs and logs the losses,
  `aux_approx_kl` and `aux_seconds`; the auxiliary state stays out of the model file.
- [x] 1.3 `checkpoints.py`: `auxiliary.pt` saved and hashed per checkpoint (`auxiliary_file`).
- [x] 1.4 `training.py`: contract `auxiliary` (absent = `none`), the five hyperparameters, resume
  restores the auxiliary state and refuses a checkpoint without it.
- [x] 1.5 `training_metrics.py`: five `train.csv` columns and the one-time header upgrade.
- [x] 1.6 `training-pure-v4.yaml`: `auxiliary: spr_reward_done_v1`, hyperparameters and comment
  block.
- [x] 1.7 `scripts/smoke_rl.py`: the auxiliary phase on the CPU and its state round trip.
- [x] 1.8 Tests: `tests/test_auxiliary_self_prediction.py`; pinned contract hash and the test
  config's short phase updated.
- [x] 1.9 Docs: RL_DESIGN, RUNTIME_AUTHORITY, STATUS, TRAINING_SESSION.

## 2. Verification

- [x] 2.1 Offline gate (two known macOS-only failures), `scripts/smoke_rl.py` and strict OpenSpec
  validation; one train call timed on the development Mac CPU.
- [ ] 2.2 Windows: `scripts/Check.ps1` and `scripts/Smoke-RL.ps1` pass with the CUDA torch
  (the smoke's GPU leg also runs the auxiliary phase).
- [ ] 2.3 Keep the current `runs\pure-v4` under its lineage name; one-hour native session with
  `--initialize`; check `update_seconds` (well under 60 s), `aux_seconds`, `aux_approx_kl`
  against `approx_kl`, the three auxiliary losses, learner RAM and GPU memory.
- [ ] 2.4 Native 150k steps: rooms per episode and the share of episodes with 3+ rooms against
  the earlier runs at equal steps; explained variance above 0.6.
- [ ] 2.5 Archive after `rollout-advantage-and-gpu-learner`.
