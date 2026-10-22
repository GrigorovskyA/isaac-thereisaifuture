## Why

`CheckpointPolicy` can run a saved RecurrentPPO checkpoint as a frozen policy, but nothing can
drive it through the live loop. A future descriptive pilot needs an attach-only, inference-only
runner that reuses the accepted live transport, records an immutable policy identity and never
learns, saves, launches, restarts the game or writes approvals.

## What Changes

- Add `live_evaluation.py`: `run_frozen_live(options)` runs exactly one explicitly chosen policy
  (`checkpoint` via `CheckpointPolicy`, or `random` via `RandomPolicy`) over
  `LiveClient`/`make_live_env` within one absolute monotonic deadline and a decision cap.
- Add CLI subcommand `eval-live` (default pilot cap 2000 decisions / 6 minutes, zero tolerated
  infrastructure faults, required `--confirmed-save-slot 2`, operator-assistance label
  `assisted|unassisted|unknown`, default `unknown`). Existing commands are unchanged.
- Private session logs: `live.jsonl` (identity, versions, hellos, segments including the final
  partial one, faults, final summary on every exit path) and a separate `oracle.jsonl`.
- Add `docs/FROZEN_LIVE_PILOT.md` (operator guide) and align `docs/LIVE_EVALUATION_PLAN.md` with
  the workflow this runner actually supports.

## Scope and non-goals

- Acceptance is offline: unit tests with fake clock/peer/env and one synthetic Lua+socket run.
  The real pilot is pending runtime evidence owned by the primary agent and is `not_run` here.
- No `--launch`, training, resume, implicit latest model, approval writing, forced restart,
  unattended recovery, supervisor, Lua/mod change or authorization-schema change. The Lua
  `live_loop_v1` approval remains required.
- No automatic detection of physical operator input; no within-session policy alternation.
- No ranking, winner or improvement claim from unmatched live rooms. The
  `combat-baselines-and-reward-v1`, `combat-ppo-training` and `rl-evaluation` multi-seed,
  held-out, 100-episode and +20 percentage-point criteria are unchanged.

## Dependencies and risks

- Depends on accepted `live-training-loop` (`LiveClient`, `LiveBackend`, `FaultTolerantEnv`,
  `make_live_env`) and `frozen-policy-evaluation-v1` (`CheckpointPolicy`).
- In-flight I/O may overrun the deadline by the bounds already in `LiveBackend` (ack 1 s,
  step wait 5 s); a paused wait is capped by the run deadline.
- The checkpoint manifest does not record the training action repeat; the runner uses the live
  default (3 game updates, same as `configs/training-live-v1.yaml`) and logs it.
- Operator navigation cannot be detected; the whole session carries the declared label.

## Acceptance

- Offline: `tests/test_live_evaluation.py` passes; the full gate passes; strict OpenSpec passes.
- Runtime (pending, not part of this offline acceptance): one primary-owned bounded pilot with a
  valid approval, recorded with `reports/EVIDENCE_TEMPLATE.md`.
