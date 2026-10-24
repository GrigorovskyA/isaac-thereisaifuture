## 1. Implementation

- [x] 1.1 `RewardV4Coefficients`: optional `stagnation` section (required for v7, absent
  for v4-v6); `RewardLedgerV4.stagnation(before, after)`; `stagnation` reward column;
  tests for stagnation scenarios, dead player, v6 paying nothing, snapshot overshoot,
  repeated idle intervals and run-bound allowance reset.
- [x] 1.2 Live backend `stall_idle_seconds`; `IsaacEnv` charges stagnation per step and
  adds the column; tests with a fake backend (grace, past grace, reset, full stall sums
  to -7.0 plus stall -5, sim backend pays nothing).
- [x] 1.3 `configs/reward-v7.yaml`, contract `pure-v7`, `training-pure-v4.yaml`
  `reward_version: 7`, reward v6 config to `archive/configs/`; `episodes.csv`
  `col_stagnation`; dashboard and compare script read the new column; test that the
  suicide-never-pays-better-than-a-stall invariant holds for the loaded configs; test that
  pure-v6 checkpoints are refused.
- [x] 1.4 Docs: STATUS, TRAINING_SESSION, RUNTIME_AUTHORITY lineage line.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [ ] 2.2 Windows `scripts/Check.ps1`; rename `runs\pure-v4` to
  `runs\pure-v4-reward-v6`; one-hour native session with `--initialize`; episode rows
  have nonzero `col_stagnation` only in episodes that idled past 20 s, and every stall
  row has `col_stall` -5.
- [ ] 2.3 Acceptance: after 8 hours, frozen evaluation of the latest checkpoint has a
  stall share below 41% and an enemy damage fraction of at least 1.70.
