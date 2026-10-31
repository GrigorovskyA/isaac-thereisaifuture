## 1. Implementation

- [x] 1.1 `rewards.py`: v12 in the version tuples, `STALL_LIMIT_VERSIONS`, `stall_seconds`
  (number > 0, greater than the grace period), loader section `stall`, `DEFAULT_CONFIG_V12`.
- [x] 1.2 `configs/reward-v12.yaml`: door coefficient 4, death -11, stall restart -4,
  stagnation -0.39, `stall.seconds: 30`.
- [x] 1.3 `live.py`: `make_live_env` accepts 12 (default 12) and rejects a `stall_seconds` that
  differs from the contract.
- [x] 1.4 `training.py`: `PURE_REWARD_VERSION = 12`; `watchdog.stall_seconds` must equal the
  reward stall limit.
- [x] 1.5 `training-pure-v4.yaml`: `reward_version: 12`, `watchdog.stall_seconds: 30`.
- [x] 1.6 Tests: `tests/test_reward_v12.py`; current-version assumptions updated in the existing
  suites.
- [x] 1.7 Docs: RL_DESIGN, UPDATE_DECISION, TRAINING_SESSION, STATUS, RUNTIME_AUTHORITY, README,
  AGENTS.

## 2. Verification

- [x] 2.1 Offline gate and strict OpenSpec validation.
- [ ] 2.2 Windows `scripts/Check.ps1`; rename `runs\pure-v4` to `runs\pure-v4-reward-v11-schema9`;
  one-hour native session with `--initialize`.
- [ ] 2.3 Native 150k steps: stall share < 50%, rooms per episode > 2.5.
- [ ] 2.4 Acceptance: compare `episodes.csv` of the reward v12 run with the reward v11 schema 9
  run at equal steps: stall share, rooms per episode, episodes reaching stage 2.
