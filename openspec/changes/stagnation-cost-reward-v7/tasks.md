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
- [x] 2.2 Windows `scripts/Check.ps1`; rename `runs\pure-v4` to
  `runs\pure-v4-reward-v6`; one-hour native session with `--initialize`; episode rows
  have nonzero `col_stagnation` only in episodes that idled past 20 s, and every stall
  row has `col_stall` -5. Evidence: [one-hour native report](../../../reports/2026-10-24-pure-v7-one-hour.md).
- [ ] 2.3 Acceptance (revised 2026-10-25, see proposal): frozen evaluation of the latest
  checkpoint over two 3600 s sessions; `compare_eval.py --baseline random-prior` shows
  the 95% interval of `kills_1k` difference above zero and a positive `clears_1k`
  difference. The 2026-10-25 single-session result for t244736: kills_1k +2.65
  [+0.09, +5.82], clears_1k +0.25 [-0.17, +0.70], damage_1k +2.00 [-0.85, +5.59].
  Not passed on 2026-10-26: t477184 over two sessions against two random-prior sessions
  gave kills_1k -1.01 [-2.38, +0.28] and clears_1k -0.07
  ([report](../../../reports/2026-10-26-pure-v7-t477184-eval-and-timing.md)). The two
  random-prior sessions alone differ by 0.88 kills_1k, so one session per checkpoint is
  not enough to rank checkpoints. Training rates stayed at random level for 477k steps,
  with 82% of steps spent in stalled episodes. Follow-up: `short-stall-reward-v8`.
