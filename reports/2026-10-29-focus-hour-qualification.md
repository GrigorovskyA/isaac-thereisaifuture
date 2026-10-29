# Native full-hour focus and pause qualification

Date: 2026-10-29, Europe/Amsterdam. Outcome: **passed for the authorized continuation**.
Self-review against native files, not independent review or gameplay acceptance.

## Identity and interval

- Software revision `fde8b1f`; launch-plan documentation `1c0e7da`, both pushed.
  Windows Check1428 including Lua/no skips, lint/format/mypy/pip passed; strict
  OpenSpec25/25; one existing synthetic All-NaN warning. No new synthetic smoke claim.
- Same contract `b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de`:
  observation8/9762, action2, pure-v9, projection512, n_steps1024, ent_coef0.005,
  gamma0.998, stall40. Source/config/mod hashes still match the launch receipt.
- Mod unchanged and deployed hashes matched before launch. No save/Cloud changes.
- Start-Pure resumed exact `b26db425-s1-t16384`, no initialization. Session
  `session-20261029-154542-0001` verified file2 Continue. No failed startup or retry.
- Owner start14:45:42.119 UTC, scheduled hour stop15:45:42.119 UTC, owner ended
  15:45:45.008 UTC (15:45 to16:45 CET). The small overrun is stop observation/cleanup.
  Native session elapsed3601.437 s; its recorded state user_cancelled is the timer
  stop-file path, not a new human cancellation.

## Whole-hour evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Successful pauses | passed | 15/15 new update rows, 100%; exceeds user70% and original90% requirement |
| Pause durations | passed | all15 filled, range6.469-10.593 s |
| Update latency | passed | median7.7735 s across14 populated update_seconds cells; first update has no preceding gap |
| Successful-pause events | passed | 15 update_paused, matching the successful rows |
| Pause/resume failure events | passed in sample | no update_pause_skipped or update_resume_failed |
| Named focus holders | none to report | no foreground refusal occurred during this hour |
| Progress | passed | t16384->t31744:15360 checkpoint steps; 68 completed episodes containing15583 gameplay steps |
| Legacy metrics | passed | all67 prior episode rows and16 prior train rows preserved exactly |
| New stall/nonstall fields | passed in sample | 48 stall rows,20 nonstall rows; last_room_clear filled and stall context consistent; nonstall stall_* fields empty |
| Exit and cleanup | passed | learner exit0, fault null, cleanup_errors[] |

All48 new stalls had the required numeric/context values. For stalls with zero
observed enemies, stall_enemy_kinds and stall_nearest_enemy are correctly empty;
no fictitious identity/distance was substituted. Two stalls were in uncleared rooms
and46 in clear rooms. Historical rows without stall context remain excluded from
context aggregates. Their preservation was checked against the prelaunch copies.

The prepared assessment was checked against actual CSV rows, events, manifest,
frozen hashes and native result. Fifteen updates were measured over the complete
hour; no early decision was made from the first pause. Steps per hour exceed the
schema7 qualification reference13824 even using only the15360 saved-step advance.
The unsaved rollout explains why completed-episode steps can exceed that advance.

## Stop verification and decision

After the hour, live inspection found no owned Isaac/worker/session runner/hour
owner, no port9528 listener and no active control-approval.json. stop.forever was
present. Parentt16384 and qualifiedt31744 copies are protected in local evidence.

Keep live.pause_during_updates:true; the configuration was not changed. Resume
qualifiedt31744 without initialization to the user deadline **2026-10-31 09:00 CET
(08:00 UTC)**, using the prepared timer and file-only fault guard. During training,
no other windows are opened/activated and no external focus helper runs. Pause
failures alone do not stop this finite continuation; training faults do.

OpenSpec paused-updates-and-input-projection task2.2 and stall-context-metrics
task2.2 are satisfied in this measured native scope. No change is archived here.
No frozen evaluation, gameplay-improvement or task2.3 acceptance is claimed.

Raw evidence: `reports/local/schema8-focus-hour-20261029/` contains launch/result,
assessment, qualification-review, prelaunch metrics/config, parent/qualified
checkpoint copies and game log. Session events and CSV files remain under
`runs/pure-v4/`. Raw logs/models/local helpers are excluded from Git.
The final committed report will include approximately30k-step windows, schema7
comparison with explicit step-method limits, stall breakdown and overnight pause share.
