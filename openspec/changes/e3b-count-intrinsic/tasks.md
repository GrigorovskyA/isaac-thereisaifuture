## 1. Implementation

- [x] 1.1 `e3b.py`: masked embedding (structured extractor copy + Linear), inverse dynamics,
  Sherman-Morrison bonus, running std, count factor, `E3BLearner` (reward, update, save/load).
- [x] 1.2 `env.py` and `rewards.py`: `IsaacCombatEnv.intrinsic` pays r_int as component `e3b`
  with a writable table only; `RewardLedgerV4.novelty_key` exposes the next cell's key.
- [x] 1.3 `learner.py`: contract `intrinsic`, the `e3b_*` hyperparameters, the shared or own
  replay, the E3B phase after the PPO epochs and the auxiliary phase, its logs.
- [x] 1.4 `training.py` and `checkpoints.py`: contract field (none left out of the hash),
  hyperparameters recorded only when on, `e3b.pt` saved and hashed, resume restores it and refuses
  a checkpoint without it, the env hook attached to the training env only.
- [x] 1.5 `training_metrics.py` and `episode_metrics.py`: `e3b_idm_loss`, `e3b_bonus_mean`,
  `e3b_seconds` and `col_e3b` with one-time header upgrades.
- [x] 1.6 `configs/training-pure-v4.yaml`: comments and unhashed defaults only; `scripts/smoke_rl.py`
  E3B leg.
- [x] 1.7 Tests: `tests/test_e3b_count_intrinsic.py`.
- [x] 1.8 Docs: RL_DESIGN, one line in STATUS and TRAINING_SESSION.

## 2. Verification

- [x] 2.1 Offline gate (two known macOS-only failures), `scripts/smoke_rl.py`, strict OpenSpec
  validation; the shipped contract hash is still `0399c37d...`; per-step and per-update cost
  measured on the Mac CPU.
- [ ] 2.2 Windows: `scripts/Check.ps1` and `scripts/Smoke-RL.ps1` with the CUDA torch; time one E3B
  phase on the RTX 4070.
- [ ] 2.3 (shipped config switched to `e3b_count_v1` on 2026-11-01, contract `db85924f...`) Plan and launch an `e3b_count_v1` lineage (new contract hash, `--initialize`); in the
  first hour check `e3b_seconds`, `e3b_idm_loss`, `e3b_bonus_mean` and `col_e3b` against
  `col_room_visit`.
- [ ] 2.4 Compare it with the `none` lineage at equal steps in frozen evaluation (rooms per
  episode, share of episodes with 3+ rooms, floor 2 rate).
- [ ] 2.5 Archive after acceptance.
