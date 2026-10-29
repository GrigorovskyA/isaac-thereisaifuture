# Evidence: pause qualification failed; resumed training stopped

Actual run/review: **2026-10-29**. Stopped early at **15:25:52 CET** after the
first completed pause measurement failed (0/1 successes). The October31 filename
was planned for the conditional continuation, which was not launched.

- Owner start 14:18:11.615 UTC; planned hour stop15:18:11.615 UTC; actual end14:25:52.038 UTC.
- Active training attempt: 14:18:39.913 to14:25:51.065 UTC. Final checkpoint saved
  at14:22:54.123 UTC, t16384; the last completed episode was recorded14:24:36.286 UTC.
- Live cleanup verified: no Isaac, worker/session runner, hour owner, listener9528
  or active owned control approval; stop.forever retained. Frozen inputs match launch.
- The first automatic startup attempt failed its foreground guard, learner exit1,
  worker termination required/cooperative release unverified. The supervisor then
  automatically launched a second attempt; this was not a manual retry. The hour
  foreground helper subsequently recorded Owned Isaac window/PID changed.
  The second attempt ended by stop file, learner exit0, fault null, cleanup_errors[].
  Aggregate run cleanup is therefore not described as uniformly clean.
- No repair, source/config/mod/save/Cloud change, reinitialization or continuation
  was performed after failure. The finite monitor is deleted after this report.

- Source revision bc5e985; Check1427 including Lua/no skips; strict OpenSpec25/25; existing synthetic All-NaN warning. Mod unchanged and deployed SHA matched.
- Contract b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de; observation8=9762/action2/pure-v9; ent_coef0.005 gamma0.998 n_steps1024.
- This qualification resumes b26db425-s1-t15360 without initialization. Prior 60 episode rows and 15 train rows predate the pause fix/stall columns; those rows are retained and excluded from new telemetry acceptance.
- One-hour qualifier start 2026-10-29T14:18:11.614818+00:00; end 2026-10-29T14:25:52.037776+00:00. Conditional continuation only until2026-10-31T08UTC/09CET.
- Qualification review: {"state": "failed", "checkpoint": "b26db425-s1-t16384", "reason": "pause_ok0/1 below90%; foreground refusal; initial supervisor startup also faulted", "continuation_authorized": false, "source_revision": "bc5e985", "no_fix_or_retry": true}
- Latest checkpoint {'id': 'b26db425-s1-t16384', 'steps': 16384, 'path': 'D:\\isaac\\runs\\pure-v4\\seed-1\\checkpoints\\b26db425-s1-t16384', 'completed_at': 1793283774.1229403}. Completed episode steps 17595 may exceed checkpoint steps 16384 because the final rollout can be unsaved.

## Native sessions

| Session | Parent | State | Learner exit | Fault | Cleanup |
| --- | --- | --- | ---: | --- | --- |
| session-20261029-151812-0001 | b26db425-s1-t15360 | fault | 1 | MenuEntryError: Isaac is not foreground; no input sent | ['worker: RuntimeError: Owned worker required termination; cooperative release unverified'] |
| session-20261029-151839-0002 | b26db425-s1-t15360 | user_cancelled | 0 | None | [] |

## Early qualification review

| Check | Outcome | Evidence |
| --- | --- | --- |
| Pause recording | populated, failure observed | new row t16384: pause_ok0, pause_seconds0.0 |
| Required pause share >=90% | failed | 0/1 successful pauses, 0%; stopped at this observation |
| Pause event coverage | failed pause explained | update_paused0, update_pause_skipped1, update_resume_failed0; reason: MenuEntryError: Isaac is not foreground; no input sent |
| Update median <12s | not measurable | only one new row; its first-update timing cell is empty as expected; this is not a measured slow update |
| Old episode rows | passed | all60 retained under every old column; added columns empty |
| Old train rows | passed | all15 retained exactly; prior empty pause cells excluded from this qualification |
| New stall context | passed in available sample | 6 new stalls, last_room_clear populated and consistent with stall_room_clear |
| New nonstall context | passed in available sample | 1 death row: last_room_clear populated, all stall_* empty |
| Empty enemy fields on clear stalls | expected semantic absence | all6 stalls have zero observed enemies; stall_enemy_kinds and stall_nearest_enemy empty by design; numeric/context fields populated |

The first attempt's startup fault is an additional qualification blocker. The
subsequent training attempt produced one completed update before the check and
stop; no full-hour success or reliable throughput/update-median result is claimed.
The prepared assessor was reviewed against the actual rows/events/results. Its
message Update median not below12seconds means **no available measurement**, not
an observed latency above12s. A failed review receipt was retained locally.
Native tasks2.2 remain unchecked because the authorized full-hour verification
was stopped early. No further attempt or fix is authorized by this report.

## Approximately 30k-step windows

Completed episodes are assigned by cumulative episode-step end from fresh zero; boundary episodes are not split. Rates use completed-episode steps. The last window is partial and includes unsaved rollout steps. Old completed-episode steps16106 already exceeded the resumed parent checkpoint15360, so cumulative gameplay-step windows are descriptive and do not equal policy checkpoint/optimizer-step bounds. This mismatch is retained explicitly rather than discarding old rows.

| Steps | Episodes | Episode steps | Stalls | Stalled-step share | Exit start | Rooms mean | Kills/1k | Clears/1k | New-item episodes | Max stage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-17595 | 67 | 17595 | 50/67 (74.6%) | 14740/17595 (83.8%) | 42/67 (62.7%) | 1.806 (n=67) | 3.581 | 0.682 | 1/67 (1.5%) | 1 |

## Mean reward components per completed episode

| Component | 0-17595 |
| --- | ---: |
| col_enemy_damage | 6.663 (n=67) |
| col_room_clear | 1.791 (n=67) |
| col_room_visit | 4.030 (n=67) |
| col_floor_entered | 0.000 (n=67) |
| col_damage_taken | -1.276 (n=67) |
| col_death | -2.537 (n=67) |
| col_time | -0.271 (n=67) |
| col_pickup_coin | 0.022 (n=67) |
| col_pickup_bomb | 0.000 (n=67) |
| col_pickup_key | 0.007 (n=67) |
| col_collectible_new | 0.075 (n=67) |
| col_heal | 0.015 (n=67) |
| col_novelty | 4.910 (n=67) |
| col_stall | -3.731 (n=67) |
| col_stagnation | -5.935 (n=67) |
| col_door_shaping | 0.615 (n=67) |

## Matched-step schema7 comparison

Same cumulative complete-episode endpoint method, uncontrolled training seeds. These are equal cumulative completed-episode step bounds, not exact matched model/checkpoint steps: schema8 includes its pre-resume unsaved tail. Compare only up to schema7 t204800; no extrapolation or frozen acceptance.

| Steps | Schema | Episodes | Episode steps | Stalls | Stalled-step share | Exit start | Rooms mean | Kills/1k | Clears/1k | New-item episodes | Max stage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-17595 | 8 | 67 | 17595 | 50/67 (74.6%) | 14740/17595 (83.8%) | 42/67 (62.7%) | 1.806 (n=67) | 3.581 | 0.682 | 1/67 (1.5%) | 1 |
| 0-17595 | 7 | 85 | 17434 | 69/85 (81.2%) | 15098/17434 (86.6%) | 41/85 (48.2%) | 1.494 (n=85) | 2.466 | 0.516 | 3/85 (3.5%) | 1 |

## Stall context summary

Context coverage: 6/50 stalls. Legacy rows without context are excluded, never imputed. Uncleared: 0/6; clear: 6/6. Shares: 0.0% / 100.0%.

| Uncleared-room mean | Value and available denominator |
| --- | ---: |
| stall_enemies | N/A (n=0) |
| stall_oracle_enemies | N/A (n=0) |
| stall_enemies_invulnerable | N/A (n=0) |
| stall_enemies_flying | N/A (n=0) |
| stall_enemies_boss | N/A (n=0) |
| stall_nearest_enemy | N/A (n=0) |

Top10 enemy kinds among uncleared stalls, counted once per episode containing the type.variant (not number of enemies).

| Kind | Stall episodes |
| --- | ---: |
| Not observed in uncleared stalls | 0 |

Clear-room stalls with no open unexplored door: 2/6 (33.3%). This is the requested dead-end proxy, not proof that no gameplay route exists.

## Limits

No source/config/mod/save/Cloud changes during the run. Raw logs, models and local evidence are excluded from Git. Self-review only; no new frozen evaluation, gameplay-improvement or task2.3 acceptance claim. Actual stopped process/listener/approval and retained stop.forever were checked as recorded above.
