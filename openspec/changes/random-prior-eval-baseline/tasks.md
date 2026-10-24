## 1. Implementation

- [x] 1.1 `RandomPriorPolicy` with sampling-frequency, uniformity, per-seed
  determinism and invalid-probability tests.
- [x] 1.2 `LiveRunOptions` and `EvaluationSpec` accept `random-prior` and refuse a
  checkpoint with it; `_evaluate_run` reads the probability from the config and
  records the policy name; tests.
- [x] 1.3 `session_runner --evaluate random-prior`; CLI tests for acceptance and the
  refused `--checkpoint`, `--forever` and training-root combinations.
- [x] 1.4 `Start-Eval.cmd` label `random-prior` and the `docs/TRAINING_SESSION.md` text.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation (macOS); training contract
  hash unchanged. Windows gate: 1242 passed with Lua, strict OpenSpec 19/19 (2026-10-24).
- [ ] 2.2 Native Windows: `scripts/Check.ps1`, then one 3600 s `random-prior`
  evaluation session ending `completed` with a non-empty `episodes.csv`,
  `runs/pure-v4` byte-identical afterwards, and the `scripts/compare_eval.py` table
  next to `random` and the checkpoints.
