# Evidence: schema 8 qualification failed; training stopped

Actual run and review date: **2026-10-29**. The October 31 filename was planned for
the conditional continuation, which was not launched. **Qualification failed** because
all required pause metrics are missing. No fix or further retry was performed.

- Native Windows/Steam/file 2; observation 8 (9762 inputs), action 2, reward pure-v9, seed 1.
- Contract: `b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de`; ent_coef=0.005, gamma=0.998, stall 40 s.
- Source revision `384b1cc`; launch receipt committed as `0269fb0`. Schema 7 t204800 is preserved in runs/pure-v4-reward-v9-schema7 with stop.forever. Two earlier failed startups produced no checkpoint and remain in runs/pure-v4-schema8-startup-failed-20261029. The user explicitly authorized a guarded file-2 New Run and one repeated hour; it initialized the model once. No continuation was started.
- Qualification start UTC: 2026-10-29T10:39:41.881063+00:00; ended: 2026-10-29T11:39:45.764251+00:00. Qualification duration 3600 seconds.
- Conditional continuation authorized only after native review, fixed deadline October 31 at 09:00 CET (08:00 UTC). Caps: 20,480,000,000 bytes, five consecutive infrastructure faults, bounded 8-hour leases.
- Final checkpoint: `b26db425-s1-t15360`, 15360 checkpoint environment steps. Final UTC epoch: 1793273807.939452.
- Windows gate: 1422 tests passed including Lua, no skips; one existing synthetic All-NaN warning. Lint/format/mypy/pip and strict OpenSpec 24/24 passed; synthetic CPU smoke passed (9762 inputs).

## Sessions

| Session | Parent | State | Learner exit | Fault | Cleanup | Final |
|---|---|---|---:|---|---|---|
| session-20261029-113942-0001 | fresh | user_cancelled | 0 | None | [] | b26db425-s1-t15360 |

## Native qualification audit

| Check | Result | Evidence |
| --- | --- | --- |
| Snapshot validation and maximum | passed in audited sample | 69,500 snapshots; 24,605 bytes maximum <131,072; zero decode errors |
| Throughput | passed | 16,158 audited successful native steps during the hour versus schema 7's 13,824, +16.9% |
| Command rejection | comparison unresolved | 16/16,234 acknowledgements =0.09856%; schema 7's exact acknowledgement denominator was not retained |
| Update duration | passed | 14 populated update_seconds cells; median 7.617 s <12 s; first row empty as expected |
| Pause metrics | failed qualification | pause_ok and pause_seconds empty in all 15 rows; zero usable success measurements, not a measured 0% success rate |
| Pause/resume failures | limited evidence | one update_pause_skipped: foreground refusal; zero update_resume_failed; absence of errors does not prove successful pauses |
| Door API | positive values observed | locked=true and target room types 4 (treasure), 5 (boss), plus 1,2,6,7,10,12,13 |
| Minimap API | positive values observed | room types 1,2,4,5,7,10,12,13 |
| Enemy API | positive values observed | 24 observed type/variant pairs, including (10,1), (11,1), (14,1); enemy_kinds maximum 4 |
| Interactables/grid | limited positive coverage | restock_box and pressure_plate observed; trapdoor not encountered |

The required pause success share >=90% cannot be calculated, and its duration
columns are unpopulated. Thus the continuation prerequisite failed even though
optimizer latency is below the threshold. The local assessor's blocked result was
independently checked against train.csv, events.jsonl, the passive audit summary
and native session result. No assertion is made that the actual pause success rate
was zero. The foreground refusal was recorded at 10:43:46 UTC. No pause repair was
attempted, and no passed qualification receipt was written.

### Capacity metrics

All seven max_* and overflow_* columns are populated for all 60 completed episodes.
Maximum counts are pre-cap observed entity totals; they can exceed the encoding cap.
Overflow share below is the arithmetic mean of episode fractions of steps with overflow, with the
number of affected episodes reported separately; it is not a pooled frame-weighted rate.

| Kind | Encoding cap | Maximum observed count | Mean episode overflow share | Episodes with overflow |
| --- | ---: | ---: | ---: | ---: |
| enemy | 32 | 12 | 0.00000% | 0/60 |
| projectile | 64 | 4 | 0.00000% | 0/60 |
| obstacle | 64 | 144 | 0.85784% | 1/60 |
| pickup | 24 | 5 | 0.00000% | 0/60 |
| own_attack | 48 | 3 | 0.00000% | 0/60 |
| bomb | 8 | 1 | 0.00000% | 0/60 |
| interactable | 16 | 1 | 0.00000% | 0/60 |

Obstacle overflow affected one episode. Other kinds had no measured overflow.

## Approximately 30,000-step gameplay windows

Only one partial 30k-step window exists. The passive audit records 16,158 successful native steps, including the final unsaved rollout. All 60 completed episodes contain 16,106 steps; 52 additional audited steps belong to the unfinished episode. The audit summary was last flushed about three seconds before stop, so a short later tail may be unrecorded. Rates use completed-episode steps. New item means pickups_collectible >0; exit start means rooms_visited >1. The last checkpoint contains 15,360 environment steps; these are not optimizer-update counts.

| Step window | Episodes | Episode steps | Stalls | Steps in stalled episodes | Exit start | Rooms visited mean | Kills/1k | Clears/1k | New-item episodes | Max stage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0-16158 | 60 | 16106 | 44/60 (73.3%) | 13351/16106 (82.9%) | 39/60 (65.0%) | 1.850 | 3.415 | 0.683 | 1/60 (1.7%) | 1 |

## Mean reward components per completed episode

| Component | 0-16158 |
|---|---:|
| col_enemy_damage | 6.4240 |
| col_room_clear | 1.8333 |
| col_room_visit | 4.2500 |
| col_floor_entered | 0.0000 |
| col_damage_taken | -1.3250 |
| col_death | -2.6667 |
| col_time | -0.2759 |
| col_pickup_coin | 0.0250 |
| col_pickup_bomb | 0.0000 |
| col_pickup_key | 0.0083 |
| col_collectible_new | 0.0833 |
| col_heal | 0.0167 |
| col_novelty | 5.0500 |
| col_stall | -3.6667 |
| col_stagnation | -5.9227 |
| col_door_shaping | 0.6336 |

## Evidence and limits

- Full gate, deployment/archive receipts, passive native audit, qualification review and session results: reports/local/pure-v9-schema8-retry-20261029/ and runs/pure-v4/. Raw logs/models remain outside Git.
- Live cleanup verified after stop: no Isaac, worker/session runner, hour owner, listener on port 9528 or active owned control approval; stop.forever retained. Native learner exit 0, fault null, cleanup_errors empty. Session state user_cancelled is the timer-owned stop-file path, not a separate human cancellation. Last checkpoint was saved at 11:36:47.939 UTC; last audited progress was 11:39:38.850 UTC, stop observed at 11:39:42 UTC, owner finished 11:39:45.764 UTC.
- Frozen source/configuration/mod hashes still match launch. No save/Cloud edits, source/config changes, additional initialization or continuation occurred. Door/boss entity observations do not establish reward acceptance or improved play.
- Self-review only. No new frozen evaluation or native gameplay acceptance claim; OpenSpec task 2.3 remains open.


## Schema 7 comparison at matched environment-step bounds

Schema 7 checkpoints end at t204800. Compare completed episodes whose cumulative
completed-episode step count is <=15,360, from fresh step zero in each lineage.
Boundary episodes are excluded, so denominators differ. This method uses episode
step counts directly and excludes the schema 8 unsaved tail. It is a descriptive
training comparison with uncontrolled seeds, not frozen evaluation or acceptance.

| Bound | Schema | Episodes | Episode steps | Stall share | Stalled-step share | Exit start | Rooms mean | Kills/1k | Clears/1k | New-item share | Max stage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-15360 | 8 | 57 | 15270 | 73.7% | 83.1% | 64.9% | 1.842 | 3.602 | 0.720 | 0.0% | 1 |
| 0-15360 | 7 | 75 | 15322 | 81.3% | 87.0% | 46.7% | 1.467 | 2.350 | 0.392 | 1.3% | 1 |

Training remains stopped. Both schema 8 native tasks 2.2 remain unchecked; no task
2.3 or frozen-evaluation acceptance is claimed. The finite monitor is removed after
this committed report because no authorized continuation can proceed.
