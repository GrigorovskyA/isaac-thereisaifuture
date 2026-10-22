# Tasks

## 1. Unscored setup and collector boundary

- [x] 1.1 Implement the bounded opt-in setup controller using the qualified one-frame movement/braking branch; add closed-loop and stale/grid/target/deadline failure tests, retaining the measured three-frame non-convergence regression, and document its guards. Native entry capture additionally motivates a command-free 5-second/100-snapshot visibility wait inside setup; offline regression/replay required, native handoff still belongs to 4.3.
- [x] 1.2 Add the pre-collector setup seam with release and fresh handoff; verify zero setup rollout entries, reward credit, normalization updates or recurrent carryover, including wounded-target baselines, changed first-action state and unchanged default modes.

## 2. Preserved branch and bounded orchestration

- [x] 2.1 Implement transactional copying of the exact t26368 parent into an absent child run; verify loaded model/Adam/normalizer/RNG identities, protected parent pointers, incompatible/missing-state refusal and interrupted-copy behavior, with a branch receipt.
- [x] 2.2 Implement the 300-second shared phase runner and explicit cap manifest; test stop-before-reset on death, health/disk/trace/count limits, shared-reader phase transfer and refusal of unverified reconnect, one-reader ownership and no lease renewal, and document the runnable plan.

## 3. Frozen observations and evidence

- [x] 3.1 Implement named parent/learned-child frozen phases with bounded eligibility/setup; test immutable model/statistics, fresh recurrent starts, missing-checkpoint/state not_run handling and no initial-child substitution.
- [x] 3.2 Produce per-phase metrics and start fingerprints; test observed damage/health/clear/death coverage, 10-second stagnation windows, setup exclusion, phase exposure denominators, unfinished-rollout accounting and observational-only comparison labels, with a report example.

## 4. Integration and native qualification

- [x] 4.1 Run focused checks then scripts/Check.ps1 and strict OpenSpec validation on final source; save complete results and verify tested input hashes before freezing the exact native assignment.
- [x] 4.2 Execute only the declared one-shot Continue/file-2 pilot after implementation and applicable authorization; record all phase attempts, caps, actual native accepts, saved/unsaved work and release/game/listener/approval cleanup without retries or New Run. Attempt closed: setup refused before action; learning and frozen phases not_run. See reports/2026-10-22-exposed-start-windows-review.md.
- [x] 4.3 Independently reload the child and verify preserved parent lineage, at least one real optimizer update and learner-attributed native damage; publish phase metrics, comparison limitations and OpenSpec verification, keeping qualification unfinished if required native evidence is absent. Ready-pilot evidence passed: native HP-loss lower bound7, six saved optimization cycles and independently reloaded t27904; no improved-play claim. See reports/2026-10-22-ready-curriculum-pilot-results.md.

## Workflow follow-up

- Archive only after the scoped tasks and native qualification pass; paired multi-seed model promotion remains a later milestone.
