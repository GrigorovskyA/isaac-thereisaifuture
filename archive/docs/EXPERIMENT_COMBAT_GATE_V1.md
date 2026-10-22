# Experiment: first real combat-gated training continuation

Predeclared: 2026-10-18, Europe/Amsterdam.
Experiment ID: combat-gated-continuation-v1. This is an exploratory pipeline
experiment, not a confirmatory evaluation of policy quality.

## Parent and fixed configuration

Resume the existing final checkpoint 1f4a187e-s20-t4096, training seed 20,
config hash 1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5.
Use configs/training-live-v1.yaml without changing hyperparameters, reward
coefficients, schemas, action repeat or normalizer settings. Observer remains
0.5.0-dev. Original parent artifacts must remain unchanged.

## Budget

- Target 6144 TOTAL timesteps: at most 2048 new samples from t4096, not 6144 new
  samples. Explicit resume only; no fallback to a new model.
- Ten minutes maximum for training including combat-gate/operator waits, pauses
  and reconnects. Each handoff waits at most two minutes. Zero tolerated faults.
- One local 20-minute approval, at most three natural-death restart attempts for
  the game launch. No renewal on handoff/reconnect or extension to finish a rollout.
- Existing disk cap 512 MB; at most eight new completed 256-step checkpoints are
  expected. Keep all completed checkpoints, including unfavorable outcomes.
- After training, validate final checkpoint/model/normalizer and parent lineage
  offline. A separate optional frozen live check (256 decisions/two minutes)
  requires fresh operator readiness and sufficient original approval time.

## Operator interaction

Initial launch, file-2 selection/Continue and normal exit are manual. Prepare a
small ordinary enemy room on pause before connecting. Primary prepares a single
acknowledgment for the exact current paused request/session/epoch/room, then
instructs the operator to unpause and release keys. No long blocking poll during
the exposed readiness exchange. A prepared acknowledgment expires without retry
if provenance changes or the unpause deadline passes.

During combat the operator does not press game keys. After clear/empty/death/
timeout, the gate releases input and waits; it never acknowledges itself. Only
then may the operator navigate manually, pause in the next fight and confirm
readiness. Every new handoff needs fresh readiness; manual damage/clear during
waiting must not be credited to the subsequent policy segment.

Waiting contributes no policy observations, recurrent updates, normalization
samples or reward. Legitimate combat terminal/truncated transitions are retained;
queued action-veto transitions can be counted as withheld rather than executed.
Record that distinction. A deadline can lose the unfinished rollout; report
unsaved samples, not a fabricated new checkpoint.

## Evidence and decision rule

Use reports/EVIDENCE_TEMPLATE.md. Retain initial/final checkpoint identity,
every new parent link, elapsed/active/wait time, handoff requests and accepted/
rejected readiness, combat decisions, withheld commands, samples covered by
completed updates and unsaved partial samples. Keep oracle labels separate.
Record clears/empty exits, deaths, damage, timeouts, faults, manual interventions,
native movement/tears/releases, and operator cleanup confirmation.

Pipeline success requires at least one real completed PPO update and reloadable
checkpoint using combat-gated experience, no actions/normalizer sampling during
waits, valid handoff boundaries, bounded stop and preserved parent. Reaching
6144 is a target, not a reason to extend the budget. If no checkpoint is saved,
report that outcome and the unsaved rollout honestly.

Combat performance remains inconclusive: one seed, operator-prepared unmatched
rooms, no independent baseline or held-out comparison. Reward growth or a clear
alone does not prove improvement. Do not alter rewards, tune after observing
the run, pick only a favorable model or claim autonomous navigation. The larger
multi-seed/100-episode/+20-point criteria remain unchanged.

No forced resets/deaths, enemy spawning, save/Cloud/settings edits, screen
capture, desktop inputs, unattended startup or automatic successor experiment.
