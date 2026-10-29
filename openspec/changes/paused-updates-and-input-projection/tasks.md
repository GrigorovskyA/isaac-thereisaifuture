## 1. Implementation

- [x] 1.1 `policy.py`: shared `Linear(obs, features_dim)` + ReLU extractor and one kwargs
  helper; `features_dim` in the hashed contract and used for every fresh model; checkpoints
  of another width are refused by the contract hash.
- [x] 1.2 `n_steps` 1024 and `batch_size` 256 in `configs/training-pure-v4.yaml`; retention
  comment and docs updated.
- [x] 1.3 `update_pause.py` and the backend backlog: pause at rollout end, resume at the next
  rollout start, bounded waits, failures recorded and never raised; `live` config section.
- [x] 1.4 Worker keyboard (`LazyWindowsMenu`) reusing the guarded menu input.
- [x] 1.5 `train.csv` columns `pause_seconds` and `pause_ok` with upgrade of older headers.
- [x] 1.6 Tests: policy shape and refusal, contract hash, config parsing, pause ordering,
  timeout, already paused, focus loss, failed resume, callbacks, backend backlog, metrics.

## 2. Verification

- [x] 2.1 Offline gate: `scripts/check.sh` and strict OpenSpec validation (macOS).
- [ ] 2.2 Native one hour on Windows: `update_seconds` median below 12 s, `pause_ok` share
  above 90%, no fault from pausing, steps per hour not below the schema-7 run.
