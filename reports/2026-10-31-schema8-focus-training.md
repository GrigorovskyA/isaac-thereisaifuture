# Evidence: schema 8 pause verification and stall context training

Actual run/review: **2026-10-29**. The user stopped continuation early; the October31
filename was planned for the authorized deadline, which was not reached.

- Continuation started15:49:44.041 UTC (16:49 CET), stopped15:52:46.875 UTC
  (16:52:46.875 CET), duration about3 minutes. No initialization.
- Latest checkpoint remains **b26db425-s1-t31744**, saved15:43:53.534 UTC during
  qualification. Continuation completed3 episodes/576 episode steps, then stopped
  with an unsaved rollout; no additional optimizer update or checkpoint was saved.
- Actual stop verified: no owned Isaac/worker/session runner/continuation owner,
  no port9528 listener or active control approval. stop.forever remains. The recurring
  monitor was deleted; no further training is scheduled by this task.
- Learner exit0 and fault null; session statefault comes from the cleanup integrity
  check: frozen source training_metrics.py changed relative to launch. Thus process
  shutdown is confirmed, but overall cleanup is **not** reported as clean.
  The working-tree edits to that file and tests/test_update_pause.py, plus unrelated
  tools/, are preserved and excluded from this documentation commit.
- The t31744 manifest/model/normalizer still match the protected qualified copy.
  No retry, repair, rollback or new initialization was performed.

- Source revision fde8b1f; Check1428 including Lua/no skips; strict OpenSpec25/25; existing synthetic All-NaN warning. Mod unchanged and deployed SHA matched.
- Contract b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de; observation8=9762/action2/pure-v9; ent_coef0.005 gamma0.998 n_steps1024.
- This qualification resumes b26db425-s1-t16384 without initialization. The prior67 episode and16 train rows are retained as the pre-focus-fix baseline and excluded from this hour's telemetry acceptance. The first60 episodes lack stall context; the next7 already carry it.
- One-hour qualifier start 2026-10-29T14:45:42.118853+00:00; end 2026-10-29T15:45:45.008177+00:00. Conditional continuation only until2026-10-31T08UTC/09CET.
- Qualification review: {"state": "passed", "scope": "Full-hour native pause/stall review and user-authorized continuation", "checkpoint": "b26db425-s1-t31744", "pause_enabled": true, "pause_ok": 1, "pause_sample": 15, "update_seconds_median": 7.773499999999785, "update_paused": 15, "skipped": 0, "resume_failed": 0, "new_episodes": 68, "stall_context_errors": [], "source_revision": "fde8b1f", "deadline_utc": "2026-10-31T08:00:00Z", "cleanup_verified": true}
- Latest checkpoint {'id': 'b26db425-s1-t31744', 'steps': 31744, 'path': 'D:\\isaac\\runs\\pure-v4\\seed-1\\checkpoints\\b26db425-s1-t31744', 'completed_at': 1793288633.5344346}. Completed episode steps 33754 may exceed checkpoint steps 31744 because the final rollout can be unsaved.

## Native sessions

| Session | Parent | State | Learner exit | Fault | Cleanup |
| --- | --- | --- | ---: | --- | --- |
| session-20261029-154542-0001 | b26db425-s1-t16384 | user_cancelled | 0 | None | [] |
| session-20261029-164944-0001 | b26db425-s1-t31744 | fault | 0 | None | ['frozen: RuntimeError: Frozen source or parent changed: D:\\isaac\\src\\isaac_threrisaifuture\\training_metrics.py'] |

## One-hour pause and metric verification

```json
{
  "state": "hour_complete",
  "errors": [],
  "pause_ok": 1.0,
  "pause_sample": 15,
  "new_train_rows": 15,
  "pause_seconds_cells": 15,
  "pause_rows_missing": 0,
  "update_seconds_median": 7.773499999999785,
  "update_paused": 15,
  "skipped": [],
  "resume_failed": [],
  "focus_holders": {},
  "recommended_pause_enabled": true,
  "new_episodes": 68,
  "legacy_rows_preserved": true,
  "checkpoint": {
    "id": "b26db425-s1-t31744",
    "steps": 31744,
    "path": "D:\\isaac\\runs\\pure-v4\\seed-1\\checkpoints\\b26db425-s1-t31744",
    "completed_at": 1793288633.5344346
  }
}
```

## Overnight pause share

Post-qualification train rows: 0; measured pause rows: 0; successful: 0; share: N/A (no measured pause rows).
Pause stayed enabled. No post-qualification optimizer update completed before the user stop, so overnight pause share is unavailable (0 measured rows), not0%. The completed qualification hour remains15/15 (100%); it had no skipped pauses or named focus holders.

## Approximately 30k-step windows

Completed episodes are assigned by cumulative episode-step end from fresh zero; boundary episodes are not split. Rates use completed-episode steps. The last window is partial and includes unsaved rollout steps. These cumulative observed gameplay-step bounds are not checkpoint or optimizer-step bounds: earlier stopped rollouts left metrics beyond their resumed checkpoints. The comparison uses the same cumulative method for both schemas and does not claim exact matched model-step exposure.

| Steps | Episodes | Episode steps | Stalls | Stalled-step share | Exit start | Rooms mean | Kills/1k | Clears/1k | New-item episodes | Max stage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-30000 | 119 | 29940 | 88/119 (73.9%) | 24995/29940 (83.5%) | 77/119 (64.7%) | 1.798 (n=119) | 3.407 | 0.668 | 2/119 (1.7%) | 1 |
| 30000-33754 | 19 | 3814 | 13/19 (68.4%) | 2822/3814 (74.0%) | 13/19 (68.4%) | 1.684 (n=19) | 2.622 | 0.262 | 0/19 (0.0%) | 1 |

## Mean reward components per completed episode

| Component | 0-30000 | 30000-33754 |
| --- | ---: | ---: |
| col_enemy_damage | 5.783 (n=119) | 3.981 (n=19) |
| col_room_clear | 1.681 (n=119) | 0.526 (n=19) |
| col_room_visit | 3.992 (n=119) | 3.421 (n=19) |
| col_floor_entered | 0.000 (n=119) | 0.000 (n=19) |
| col_damage_taken | -1.319 (n=119) | -1.500 (n=19) |
| col_death | -2.605 (n=119) | -3.158 (n=19) |
| col_time | -0.260 (n=119) | -0.209 (n=19) |
| col_pickup_coin | 0.013 (n=119) | 0.000 (n=19) |
| col_pickup_bomb | 0.000 (n=119) | 0.000 (n=19) |
| col_pickup_key | 0.004 (n=119) | 0.000 (n=19) |
| col_collectible_new | 0.084 (n=119) | 0.000 (n=19) |
| col_heal | 0.025 (n=119) | 0.000 (n=19) |
| col_novelty | 4.765 (n=119) | 3.263 (n=19) |
| col_stall | -3.697 (n=119) | -3.421 (n=19) |
| col_stagnation | -5.830 (n=119) | -5.180 (n=19) |
| col_door_shaping | 0.617 (n=119) | 0.483 (n=19) |

## Matched-step schema7 comparison

Same cumulative completed-episode endpoint method, uncontrolled training seeds. These are equal observed episode-step bounds, not exact matched checkpoint/model steps. Compare only up to the available schema7 reference t204800; no extrapolation, frozen acceptance or gameplay-improvement claim.

| Steps | Schema | Episodes | Episode steps | Stalls | Stalled-step share | Exit start | Rooms mean | Kills/1k | Clears/1k | New-item episodes | Max stage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-30000 | 8 | 119 | 29940 | 88/119 (73.9%) | 24995/29940 (83.5%) | 77/119 (64.7%) | 1.798 (n=119) | 3.407 | 0.668 | 2/119 (1.7%) | 1 |
| 0-30000 | 7 | 146 | 29966 | 122/146 (83.6%) | 27002/29966 (90.1%) | 66/146 (45.2%) | 1.479 (n=146) | 2.136 | 0.467 | 5/146 (3.4%) | 1 |
| 30000-33754 | 8 | 19 | 3814 | 13/19 (68.4%) | 2822/3814 (74.0%) | 13/19 (68.4%) | 1.684 (n=19) | 2.622 | 0.262 | 0/19 (0.0%) | 1 |
| 30000-33754 | 7 | 20 | 3707 | 15/20 (75.0%) | 3138/3707 (84.7%) | 8/20 (40.0%) | 1.450 (n=20) | 3.777 | 0.809 | 0/20 (0.0%) | 1 |

## Stall context summary

Context coverage: 57/101 stalls. Legacy rows without context are excluded, never imputed. Uncleared: 2/57; clear: 55/57. Shares: 3.5% / 96.5%.

| Uncleared-room mean | Value and available denominator |
| --- | ---: |
| stall_enemies | 2.500 (n=2) |
| stall_oracle_enemies | 2.500 (n=2) |
| stall_enemies_invulnerable | 0.000 (n=2) |
| stall_enemies_flying | 0.000 (n=2) |
| stall_enemies_boss | 0.000 (n=2) |
| stall_nearest_enemy | 538.700 (n=2) |

Top10 enemy kinds among uncleared stalls, counted once per episode containing the type.variant (not number of enemies).

| Kind | Stall episodes |
| --- | ---: |
| 217.0 | 1 |
| 11.0 | 1 |

Clear-room stalls with no open unexplored door: 24/55 (43.6%). This is the requested dead-end proxy, not proof that no gameplay route exists.

## Limits

A source working-tree change in training_metrics.py was detected by the frozen-input cleanup check; it is not part of the launched revision or this report commit. Configuration/mod and protected checkpoint remained unchanged. No save/Cloud change was performed by this task. Raw logs, models and local evidence are excluded from Git. Self-review only; no new frozen evaluation, gameplay-improvement or task2.3 acceptance claim. Actual stopped processes/listener/approval and retained stop.forever were verified above.
