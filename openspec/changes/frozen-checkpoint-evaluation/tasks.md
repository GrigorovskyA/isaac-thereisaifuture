## 1. Implementation

- [x] 1.1 `LiveRunOptions` evaluate mode with validated `eval_policy` and
  `eval_checkpoint`; unit tests for every valid and refused combination.
- [x] 1.2 `live._evaluate_run` with the pure training env, `episodes.csv`, policy
  reset per episode, deadline stop and no checkpoint writes; tests with a synthetic
  room and a real tiny checkpoint (lineage files unchanged).
- [x] 1.3 `CheckpointPolicy`: `deterministic`, `sampling_seed`,
  `expected_reward_contract`.
- [x] 1.4 Supervisor: `SessionPlan.evaluation`, `--evaluate` / `--checkpoint`, root
  guard, preflight without parent, worker passes `mode="evaluate"`; tests for the
  `completed` classification and every refused flag combination.
- [x] 1.5 `scripts/compare_eval.py` with a unit test on a synthetic CSV.
- [x] 1.6 `docs/TRAINING_SESSION.md` section and `Start-Eval.cmd`.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation (macOS).
- [x] 2.2 Native Windows: `scripts/Check.ps1`, then one evaluation session per
  checkpoint (t102400, t204800, t237568) and random, each ending `completed`
  with a non-empty `episodes.csv`, `runs/pure-v4` byte-identical afterwards, and the
  comparison table printed by `scripts/compare_eval.py`.

  Windows gate: 1215 passed with Lua, no skips, strict OpenSpec 17/17. Successful
  evaluations: t102400/t204800/t237568/random = 34/38/40/34 complete episodes,
  all result states completed, learner exits 0, cleanup errors empty. All 77 files
  in runs/pure-v4 and 825 tracked source files stayed byte-identical. Two refused
  t237568 focus starts (zero episodes) are preserved and disclosed in
  reports/2026-10-24-pure-v4-frozen-eval.md. Training remains stopped.
