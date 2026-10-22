## 1. Specification

- [x] 1.1 Proposal, design, delta spec and tasks for `frozen-policy-evaluation-v1`.
- [x] 1.2 Strict validation of this change (macOS pinned OpenSpec CLI; Windows wrapper pending).

## 2. Frozen policy adapter (offline)

- [x] 2.1 Add `checkpoint_policy.py`: explicit directory, reused compatibility checks,
      RecurrentPPO only, identity hashes, frozen VecNormalize, recurrent carry/reset,
      deterministic inference, input/output validation, `verify_unchanged()`, lazy imports.
- [x] 2.2 Add `tests/test_checkpoint_policy.py` with a real synthetic RecurrentPPO round trip
      and lightweight fakes for invalid outputs; mutation sanity checks caught each mutation.
- [x] 2.3 Fix `training.train` SB3 `KeyError: 'r'` with a `Monitor` wrapper; regression test in
      `tests/test_training_manifest.py` fails without the fix.

- [x] 2.4 Review feedback 1: validate saved normalizer statistics/scalars at construction and
      finite normalized input before `predict`; regressions for each corrupt state, zero variance
      and predict-not-called (19 of them fail on the pre-feedback code).

## 3. Plan

- [x] 3.1 Write `docs/LIVE_EVALUATION_PLAN.md` (exploratory pilot vs blocked confirmatory
      comparison; denominators, stop conditions, operator intervention).

## 4. Checks and evidence

- [x] 4.1 Targeted tests, ruff, format and mypy on macOS; full `scripts/check.sh` gate.
- [x] 4.2 Evidence report `reports/2026-10-18-frozen-policy-evaluation-offline.md`.
- [x] 4.3 `./scripts/Check.ps1` and `./scripts/OpenSpec.ps1 validate --all --strict` on Windows
      (primary agent).

## 5. Real evaluation (blocked, not part of acceptance)

- [ ] 5.1 Exploratory live pilot per the plan, after separate runtime approval and a live
      runner change.
- [ ] 5.2 Confirmatory comparison, blocked until comparable seeded scenarios and
      train/validation/test separation exist for the live backend.
