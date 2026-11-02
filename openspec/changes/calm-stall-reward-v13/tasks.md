## 1. Implementation

- [x] 1.1 `rewards.py`: v13 in the version tuples, `CALM_STALL_VERSIONS`, `stall_calm_seconds`
  (above the grace period, at most the stall limit), loader key `stall.calm_seconds`, the
  stagnation floor sized for the calm limit, `DEFAULT_CONFIG_V13`.
- [x] 1.2 `configs/reward-v13.yaml`: `stall.calm_seconds: 15`, `stagnation.grace_seconds: 3`.
- [x] 1.3 `stall_watchdog.py`: `calm_seconds`, `limit`, `observe(calm=...)`.
- [x] 1.4 `live.py`: `make_live_env` accepts 13 (default 13) and passes the calm limit; the
  backend feeds `calm` from the oracle; the stall fraction uses the current limit.
- [x] 1.5 `learner.py`: `use_entropy_scale`, `weighted_entropy`, `_evaluate_actions`.
- [x] 1.6 `training.py`: `PURE_REWARD_VERSION = 13`, hyperparameter `use_entropy_scale`.
- [x] 1.7 `training-pure-v4.yaml`: `reward_version: 13`, `use_entropy_scale: 0.2`.
- [x] 1.8 `session_runner.py`: disk sampling skips files deleted during the walk.
- [x] 1.9 Tests: `test_reward_v13.py`, `test_use_entropy_scale.py`, calm cases in
  `test_stall_watchdog.py`, the retention race in `test_session_runner.py`; hash and version pins.
- [x] 1.10 Docs: STATUS, TRAINING_SESSION, RUNTIME_AUTHORITY.

## 2. Verification

- [x] 2.1 Offline gate and strict OpenSpec validation; `scripts/smoke_rl.py`.
- [ ] 2.2 Windows `scripts/Check.ps1`; rename `runs\pure-v4` to `runs\pure-v4-e3b`; native
  session with `Train-Start.cmd --initialize`; 20-minute audit.
- [ ] 2.3 Native 75k and 150k reports against the E3B lineage at equal steps.
