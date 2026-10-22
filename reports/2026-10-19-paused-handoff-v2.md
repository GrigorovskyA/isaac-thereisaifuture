# Evidence: paused training handoff v2

- User requested continuation after the runtime-selection correction. New finite attempt, no automatic budget renewal.
- One Steam launch, file 2 selected visually. Continue when available; no forced reset. If it resumes already in combat, pause there without navigation. Otherwise at most 14 structured down/no-shoot commands, 30 seconds after connection, first room transition only, final release; no more navigation after that budget.
- Pause/unpause: existing pinned PowerShell 7.6.5 runtime, no ExecutionPolicy changes; foreground guard, scan-code Escape held 100 ms, finally key-up, 100 ms post-input observation delay. Verify paused/alive bridge state before learner setup, then same-context fresh combat before readiness.
- One learner invocation: resume seed-20 t4864 to target t5120, at most 256 new steps, five minutes, one-minute gate waits, zero tolerated infrastructure faults, one natural-death restart, 512 MiB disk cap. At most three distinct same-session/epoch/room combat readiness acknowledgments; no extra run.
- Private helpers are experimental management assistance outside learner observations/rewards/normalizer. No production behavior/schema/reward/dependency changes or autonomous gameplay-quality claims.
- Preflight, parent readback, pinned runtime invocation (7.6.5/RemoteSigned), PowerShell parse and Python syntax checks passed. No ExecutionPolicy setting or bypass flag changed. The experiment used Continue, not New Run.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Steam/file 2 | passed | One PID 2136, source-matching observer 0.5.0-dev, existing --luadebug; FILE 2 highlight/selection and Continue visually confirmed |
| Initial state | passed | Continue resumed an existing combat room; no navigation movement was required. Session `90a73eb24b6e4491bef1a4a15b66a1a1`, epoch 1/room visit 0/frame 2373 classified combat |
| Pause before learner setup | passed | Pinned helper runtime successfully sent menu Escape; bridge verified paused/alive same epoch/room at frame 2394 and screenshot showed pause menu with full three hearts. Zero navigation commands; final release rejected while paused, so no neutral acknowledgment is claimed |
| Learner connection/resume | passed | Seed 20/config unchanged, resume parent t4864; training session `4669f260b8444e538afda8f2b02fc9e9` in `runs/live/sessions/20261019-232142-dabbcf` |
| Coordinated unpause/readiness | passed | Learner first observed paused; local manager unpaused at 1792444907.461, fresh request reported combat at 1792444907.530, manager acknowledged at 1792444907.571, gate accepted at 1792444907.585, combat resumed at 1792444907.640. One request, same session/epoch/room; no foreign or paused readiness |
| Combat collection | passed, partial target | 104 decisions over 11.477 seconds; gate ended segment as `empty`, then separately observed `cleared` 0.269 seconds later. Approximate reward 9.8853 is not a gameplay-quality metric |
| New PPO update/checkpoint | not_run | Target 256 new samples was not reached; one incomplete 104-sample rollout was discarded, 0 checkpointed samples, 104 unsaved samples, latest remains t4864 |
| Next-room wait and stop | passed | Second handoff stayed empty/cleared, no readiness ack. Original 60-second wait cap expired; manager and learner both exited 0. Two handoffs, one accepted; no rejected readiness, resume races, observation gaps, withheld actions or cleanup errors |
| Death/restart | not_run | No death or restart observed in this attempt; no second invocation or renewed budget |
| Input recovery | passed, agent check only | Final held Escape opened pause menu; final screen showed three hearts and a reward chest. No human manual-control recovery or human non-intervention assertion obtained |
| Cleanup/parent | passed | Normal window close, successful unload/shutdown log, process absent after two seconds; removed only exact matching temporary approval. No port listener (TIME_WAIT only). Model/normalizer/manifest identity and latest pointer unchanged; full parent reload and post-close preflight passed |

## Interpretation

This verifies the previously missing **pause -> learner setup -> unpause -> fresh
combat acknowledgment -> policy actions** route in one real game session. It does
not deliver a general unattended runner or prove improved gameplay. The end label
remains the existing gate's `empty`; do not fabricate a resolved cleared episode
or native exact-event/step evidence from the later room-clear flag or screenshot.

There is still a learning throughput gap: this encounter provided only 104 of
the required 256 rollout samples, and the local manager cannot navigate to a
different room through the learner's existing connection. The first readiness
worked; the second correctly stayed unacknowledged in a clear room. Further
progress requires bounded navigation within the same learner handoff loop so
one rollout can span several encounters. Do not lower n_steps, alter the config
hash or restart from scratch to disguise this incomplete target.

Private artifacts: `reports/local/paused-handoff-v2-20261019-232022/` holds the
navigation/pause/readiness records, destination assertion, local console and
window captures. The production live session directory above retains bounded
learner/oracle logs. Raw captures, approvals and checkpoint files remain ignored.

Self-review: no gameplay keyboard control, no navigation samples in learner input,
no acknowledgment without the existing gate's combat/context validation, no
second training run. Policy collection happened, but no optimizer update or new
checkpoint is claimed. Parent lineage and existing schemas are preserved. Only
private experimental helpers and evidence/status/roadmap documentation changed;
the full offline suite was not rerun for these changes. Syntax/parse checks,
runtime checks, parent reload, preflight and diff whitespace checks passed.
