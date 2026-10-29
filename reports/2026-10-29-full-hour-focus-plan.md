# Full-hour focus review and finite continuation

Date: 2026-10-29, Europe/Amsterdam. Full-hour measurement pending.

The latest user instruction supersedes earlier pause90%/first-failure stops for
this finite run. Resume `b26db425-s1-t16384` without initialization for one complete
hour. Report pause_ok over the whole hour, median update_seconds and skipped-pause
reasons naming the executable holding focus. Pause failure never stops training.
At >=70% keep pause; below70% set only live.pause_during_updates:false after the
hour stops, then continue anyway without initialization until October31 at09:00
CET (08:00 UTC). Stop for training faults/crashes, deadline or explicit user stop.

## Verified preparation

- Source `fde8b1f` committed/pushed to existing origin/main: bounded three-attempt
  foreground acquisition, Alt between attempts, executable-name diagnostics, tests
  and TRAINING_SESSION documentation. Tests cover focus recovery after Alt and
  refusal without sending the requested menu key.
- Windows Check passed: 1428 tests including Lua, no skips; lint/format/mypy/pip
  clean; strict OpenSpec25/25. One existing synthetic All-NaN warning remains.
  No new smoke or native acceptance claim follows from this gate.
- Contract unchanged:
  `b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de`.
  Observation8/9762, action2, rewardpure-v9, projection512, n_steps1024,
  ent_coef0.005, gamma0.998, stall40. Mod unchanged, no redeployment.
- Source/deployed main.lua SHA256 matched
  `41b78262d4e8a80634a6d9ce0a04e343195601b2dbcf061fdeca46aac4e58985`;
  metadata matched `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.
- Exact compatible latest t16384 was loaded before launch. The parent checkpoint,
  67 episode rows, 16 train rows and original configuration were copied under
  `reports/local/schema8-focus-hour-20261029/` before launch. All older lineages
  and failed attempts remain preserved.

## Launch and monitoring

- Owner started 14:45:42.119 UTC (15:45:42.119 CET), October29. Fixed hour stop:
  15:45:42.119 UTC (16:45:42.119 CET), through timer-owned stop.forever.
- Hidden Start-Pure runs without --initialize. Session
  `session-20261029-154542-0001` verified Continue on file2 and entered training
  without a startup fault. The original protected parent remains t16384.
- Disk cap20,480,000,000 bytes; normal supervisor fault cap5. A file-only guard
  requests stop on a new faulted session. All automatic attempts are reportable;
  no hidden fresh-model/New Run fallback or extra manual attempt is authorized.
- No console/browser/Codex panel or other window is opened/activated during training.
  Monitoring reads saved files only. No external foreground helper operates; the
  tested game keyboard itself owns its bounded focus acquisition when needed.
- Frozen runtime inputs remain unchanged during the hour. No early stop for a bad
  pause row or slow update; evaluate all new rows after the full hour.

## Hour decision and final report

After the hour stops, verify all session exits/faults/cleanup and actual absence
of owned game/worker/owner/listener/approval, retaining stop.forever. Aggregate
only new train rows after the 16-row baseline. Report successes/denominator,
pause durations, update median, update_paused/skipped/resume failures and focus
holders. Missing telemetry is not a measured0%; original90% OpenSpec acceptance
remains separate from the user's70% continuation decision.

If pause is disabled, change only the explicit live flag while fully stopped,
confirm unchanged contract hash and a flag-only configuration diff, record it,
then launch the prepared compatible continuation without initialization. No other
source/config/mod/save/Cloud changes are authorized. Continuation has an absolute
October31 08:00 UTC timer and file-only fault supervision.

The final committed report will include approximately30k-step windows, schema7
comparison up to its t204800, stall_room_clear shares, requested uncleared enemy
means/top10 kinds and clear-room dead-end proxy, plus overnight pause share.
Preserve legacy rows without inventing missing context. Cumulative episode steps
include unsaved tails and differ from resumed checkpoint steps; state the method
and denominators honestly. Disabled-pause empty cells are N/A, not failed pauses.
No frozen-evaluation/gameplay-improvement/task2.3 acceptance claim is authorized.
The finite follow-up remains quiet while healthy/pending and is removed when work ends.
