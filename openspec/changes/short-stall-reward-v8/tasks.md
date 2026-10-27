## 1. Implementation

- [x] 1.1 `configs/reward-v8.yaml` (v7 with stagnation -0.25 per second, grace 12 s);
  `configs/reward-v7.yaml` moved to `archive/configs/`; `DEFAULT_CONFIG_V8`; the loader
  requires the stagnation section for v7 and v8; the ledger rejects a grace period not
  shorter than the stall limit.
- [x] 1.2 Contract: `training-pure-v4.yaml` `reward_version: 8`, `stall_seconds: 40`;
  `PURE_REWARD_VERSION = 8`; reward contract `pure-v8`; `make_live_env` pays reward 8; the
  ledger takes the configured stall limit (live training and evaluation already pass it).
- [x] 1.3 Tests: `tests/test_reward_v8.py` (v8 equals v7 except three fields, full stall at
  40 s sums to -7.0 plus -5, charging starts at 12 s, invariant with the real stall limit,
  grace validation); pure-v7 checkpoints refused; existing tests updated to v8.
- [x] 1.4 Docs: RL_DESIGN reward section, RUNTIME_AUTHORITY lineage line, README.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [x] 2.2 Windows `scripts/Check.ps1`; rename `runs\pure-v4` to `runs\pure-v4-reward-v7`;
  one-hour native session with `--initialize`; stall rows have `col_stall` -5 and
  `col_stagnation` is nonzero only in episodes that idled past 12 s and at least -7.0.
- [ ] 2.3 Acceptance: frozen evaluation of the latest checkpoint and of `random-prior`
  (both under this config) over two 3600 s sessions each;
  `compare_eval.py --baseline random-prior` shows the 95% interval of the `kills_1k`
  difference above zero and a positive `clears_1k` difference; the share of steps in stalled
  episodes over the first 8 h session is below 50%.

  2026-10-27 t270336, two checkpoint + two random-prior sessions: kills_1k
  +3.03 [+1.34, +4.80], clears_1k +0.52 [+0.13, +0.91]. These two conditions
  passed; the share of steps in stalled episodes (<50%) did not pass (~80%),
  so task 2.3 remains open. See the
  [frozen evaluation report](../../../reports/2026-10-27-pure-v8-t270336-frozen-eval.md).
