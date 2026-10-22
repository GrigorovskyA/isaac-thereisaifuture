## Why

Roadmap item 09: extending the combat task set must not erase earlier skills, and
negative results must stay visible. Thresholds and tolerances must be fixed before training.

## What Changes

- Add `curriculum.py`: `Stage`, `Curriculum` (frozen, hashed), `should_advance`,
  `RegressionTolerance`, `regression_gate`, `compare_to_baselines`, `ResultsLog`,
  `LeakageCheckedPolicy`, `check_policy_input`.
- Add `tests/test_curriculum.py`.

## Scope and non-goals

- In scope: offline contract over synthetic scenarios; policies and evaluation callables are parameters.
- Out of scope: training, checkpoints, real-game scenarios, boss support.
- This is an offline contract. It MUST NOT be archived until real-game evidence exists.

## Dependencies and risks

- Depends on scenarios, baselines and evaluation (item 07).
- Risk: thresholds in `DEFAULT_CURRICULUM` are untuned hypotheses; the synthetic room is not Isaac.

## Acceptance criteria

- Advancement uses validation metrics only; the CI lower bound must reach the predeclared threshold.
- The regression gate fails on clear-rate or damage regression beyond the frozen tolerance.
- Every stage outcome, including failures, is appended; tampering or truncation is detected.
- Policy input is verified to be exactly the encoded observation size.
- Pending real game: beat random on held-out test scenarios with the real backend.

## Impact

New module `curriculum.py`; no change to existing modules.
