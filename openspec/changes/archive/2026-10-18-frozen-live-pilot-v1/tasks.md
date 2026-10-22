## 1. Specification

- [x] 1.1 Proposal, design, delta spec and tasks for `frozen-live-pilot-v1`.
- [x] 1.2 Strict validation (macOS pinned OpenSpec CLI; Windows wrapper pending primary rerun).

## 2. Runner (offline)

- [x] 2.1 Add `live_evaluation.py`: options validation, policy load and identity check before
      listening, one absolute deadline, decision cap, per-segment policy reset, attempted vs
      completed counts, segment and final summaries, cleanup and `verify_unchanged` in `finally`.
- [x] 2.2 Add CLI subcommand `eval-live`; existing commands unchanged.
- [x] 2.3 Add `tests/test_live_evaluation.py`: fake clock/peer/env cleanup and deadline paths,
      reset per segment, frozen normalizer and no learn/save, compatibility before listen,
      identity mutation, partial summaries, return codes, CLI validation, one synthetic Lua run.

## 3. Documentation

- [x] 3.1 Add `docs/FROZEN_LIVE_PILOT.md` operator guide.
- [x] 3.2 Align `docs/LIVE_EVALUATION_PLAN.md` with the supported workflow.

## 4. Evidence

- [x] 4.1 Offline report `reports/2026-10-18-frozen-live-runner-offline.md`.
- [x] 4.2 Windows `scripts/Check.ps1` rerun by the primary agent (1329 tests, zero skips; strict 27/27).
- [x] 4.3 Runtime pilot with a valid approval (primary-owned 256-decision frozen inference; runtime evidence, no comparative-performance claim).
