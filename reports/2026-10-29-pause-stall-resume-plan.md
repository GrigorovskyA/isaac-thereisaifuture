# Pause telemetry and stall context: bounded resume plan

Date: 2026-10-29, Europe/Amsterdam. Native qualification is pending.

The user authorized checking and publishing the prepared pause-metric fix and
stall-context-metrics, then resuming `b26db425-s1-t15360` for one hour without
initialization. Only successful native review permits continuation until
2026-10-31 09:00 CET (08:00 UTC). If pause_ok <90%, stop/report reasons without fixes.

## Offline verification

Revision `bc5e985` was committed and pushed to existing origin/main. Windows
Check passed: 1427 tests including Lua, no skips; lint/format/mypy/dependencies
passed; strict OpenSpec 25/25. One existing synthetic All-NaN warning remains.
No dependency or model architecture change was made; the previous CPU smoke is
historical evidence, not a new native or smoke result.

OpenSpec Verify self-review of the two changes:

| Dimension | Evidence and limits |
| --- | --- |
| Completeness | Pause fix, successful-pause event, stall facts/writer/header migration and tests are present. Both native task 2.2 checks remain pending. |
| Correctness | Regression test exercises one learn() per rollout and final resume/flush; stall test covers invulnerable/flying enemies, death rows, old headers and unchanged contract hash. All pass in Windows Check. Native scenarios remain unverified. |
| Coherence | Existing guarded pause input, metric-only oracle access and writer migration patterns are retained. Neither change provides design.md, so design-artifact adherence is not verified. |

Contract remains `b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de`:
observation8/9762, action2, pure-v9, projection512, n_steps1024, ent_coef0.005,
gamma0.998, stall40. No policy/reward/save/Cloud changes. The mod was not redeployed:
source/deployed main.lua matched SHA256
`41b78262d4e8a80634a6d9ce0a04e343195601b2dbcf061fdeca46aac4e58985`,
metadata matched `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.

## Native hour

- Owner start 2026-10-29 14:18:11.615 UTC (15:18:11.615 CET); fixed stop
  15:18:11.615 UTC (16:18:11.615 CET). Local timer writes stop.forever.
- Start-Pure runs without --initialize. Fresh menu evidence verifies file-2 Continue.
  Session `session-20261029-151839-0002` resumes exact compatible t15360.
- Foreground maintenance targets only the owned game. Runtime inputs are frozen.
  Disk cap 20,480,000,000 bytes; supervisor fault cap5; no further manual retry.
- Before launch, 60 old episode rows, 15 old train rows and a protected parent
  checkpoint copy were retained under `reports/local/schema8-pause-stall-20261029/`.
  Parent model hash `d5b25e490bdb649deae8d82ee29b8da4ae7cc4c6e116cd9099d7c83c01e9b6f7`.
- Initial live readback: training state, no fault; first new episode has stall
  context. The one-time header upgrade preserved all 60 rows under every old column.
  Successful pause telemetry is not yet available at this initial readback.

At the hour stop, verify native learner exit0, fault null, cleanup_errors empty,
actual stopped game/worker/owner/listener/owned approval and stop.forever. Assess
only newly added train rows: pause_ok >=90%, pause_seconds filled, median update
<12 s, update_paused events for successful updates and explicit reasons for skips.
New stall rows require context, new nonstall rows empty stall fields, every new row
last_room_clear; legacy added cells remain empty. When zero enemies are present,
stall_enemy_kinds and stall_nearest_enemy may be empty by design; disclose that
conditional absence rather than inventing an enemy identity or distance.

Only accepted review permits the prepared continuation without initialization to
the absolute October31 deadline. The final report will include roughly30k-step
windows, same-step schema7 comparisons, all col_* means and requested stall
breakdown with denominators. Legacy stalls lacking context are excluded from that
breakdown. Unsaved rollout metrics can exceed checkpoint steps; report the window
method and coverage. No frozen-evaluation, gameplay-improvement or task2.3 claim.

Local finite follow-up stays quiet while healthy/pending and is removed when the
authorized work ends. Source/config/mod/models/raw logs/local helpers are not
changed or staged as part of the later documentation report.
