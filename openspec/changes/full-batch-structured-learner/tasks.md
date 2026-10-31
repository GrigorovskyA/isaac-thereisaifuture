## 1. Implementation

- [x] 1.1 `encoding.py`: `FEATURE_BLOCKS` per-index kind table with layout anchors,
  `feature_kinds()`, `continuous_mask()`, `ENTITY_OFFSETS`.
- [x] 1.2 `normalization.py`: `ContinuousVecNormalize` and `check_continuous_only`.
- [x] 1.3 `policy.py`: `StructuredFeatures`; `policy_kwargs(features=...)`; `InputProjection` kept.
- [x] 1.4 `training.py`: contract `policy_features` and `observation_normalization`; fresh pure
  models use the continuous-only normalizer and the structured extractor; resume checks the
  normalizer.
- [x] 1.5 `checkpoint_policy.py` / `live.py`: frozen evaluation requires and checks the
  continuous-only normalizer.
- [x] 1.6 `training-pure-v4.yaml`: `batch_size` 1024, both contract fields, comment block.
- [x] 1.7 `scripts/smoke_rl.py`: the same normalizer, extractor and full batch, with a save/load.
- [x] 1.8 Tests: `tests/test_full_batch_structured_learner.py`, frozen-policy normalizer checks,
  pinned contract hash and shipped config updated.
- [x] 1.9 Docs: RL_DESIGN, UPDATE_DECISION, TRAINING_SESSION, STATUS, RUNTIME_AUTHORITY,
  ARCHITECTURE.

## 2. Verification

- [x] 2.1 Offline gate (two known macOS-only failures), `scripts/smoke_rl.py` and strict OpenSpec
  validation; update time measured on the development Mac.
- [ ] 2.2 Windows `scripts/Check.ps1` and `scripts/Smoke-RL.ps1`; rename `runs\pure-v4` to
  `runs\pure-v4-reward-v12-schema9`; one-hour native session with `--initialize`; check
  `update_seconds` in `train.csv`.
- [ ] 2.3 Native 150k steps: explained variance above 0.6, rooms per episode above 2.3.
- [ ] 2.4 Acceptance: compare `episodes.csv` and `train.csv` with the reward v12 schema 9 run at
  equal steps: rooms per episode, share of episodes with 3+ rooms, stall share, explained
  variance, epochs run per update.
