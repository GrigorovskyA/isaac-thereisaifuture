# Native training statistics and schema8 final report

The run stopped early on October 29, 2026 at 20:29:25 UTC (21:29:25 CET), after a Windows access-denied error while replacing the session status file. The October 30 deadline was not reached. Training remains stopped; no manual retry or repair was performed.

The first learner exited 0 with no cleanup errors, but its session fault is retained. Before the file guard stopped the supervisor, its built-in loop automatically opened a second session from t102400. That session only reached startup/listening, produced no episodes or updates, and exited 1 after its owned worker required termination; cooperative input release was unverified. This is a shutdown limitation, not a clean-run claim. The launcher exit 0 does not override these session results.

Post-stop inspection found no game, training worker, finite owner or Start-Pure process, and no listener on port 9528. Only the existing read-only dashboard Python processes remained. The deployed action_authorization.json and its temporary file are absent, so neither session retains an owned approval. stop.forever is present. Frozen source/mod/config hashes match the launch receipt; the pause flag remains enabled. No new training is authorized by this report.

- Source revision fc80cd5d47fb843043e41f8375b63b986ca7b947; Check1428 includingLua/no skips, strictOpenSpec25/25; one existing synthetic All-NaN warning.
- Contract b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de; observation8/9762/action2/pure-v9, ent_coef0.005 gamma0.998 n_steps1024.
- Resume exact b26db425-s1-t31744 without initialization. Mod unchanged. No other PC windows opened/activated; file-only monitoring.
- Started 2026-10-29T15:58:40.333760+00:00; ended 2026-10-29T20:29:25.006629+00:00; fixed deadline2026-10-30T08UTC/09CET. Stop reason: training fault.
- Final checkpoint: `b26db425-s1-t102400` (70,656 saved model steps beyond parent t31744). Completed episode steps across schema8 history: 105,104; this finite run: 71,350 across 305 completed episodes. The prelaunch cumulative baseline was 33,754, already above parent model step 31,744; cumulative gameplay steps and checkpoint steps are different measures.

## Sessions

| Session | Parent | State | Learner exit | Fault | Cleanup |
| --- | --- | --- | ---: | --- | --- |
| session-20261029-165840-0001 | b26db425-s1-t31744 | fault | 0 | PermissionError: [WinError 5] Access denied: 'D:\\isaac\\runs\\pure-v4\\supervisor\\session-20261029-165840-0001\\status.tmp' -> 'D:\\isaac\\runs\\pure-v4\\supervisor\\session-20261029-165840-0001\\status.json' | [] |
| session-20261029-212908-0002 | b26db425-s1-t102400 | fault | 1 | None | ['worker: RuntimeError: Owned worker required termination; cooperative release unverified'] |

## Evidence and stop boundary

Local receipts: `reports/local/schema8-train-stats-20261029/result.json`, `phase-1-result.json`, `training-fault-stop.json`, `statistics-check.json` and `first-hour-pause.json`; per-session results/events remain under `runs/pure-v4/supervisor/`. The failure was `status.tmp` replacement with `status.json`; the process holding a conflicting handle is unknown. The later "User cancellation requested" reason came from the stop mechanism and does not establish a fresh human cancellation.

## Statistics capture and pause

- statistics-check.json: {"time": "2026-10-29T16:10:40.754130+00:00", "state": "passed", "rows": 3, "missing": [], "pause_ok": ["1", "1", "1"]}
- first-hour-pause.json: {"time": "2026-10-29T16:58:40.775950+00:00", "rows": 15, "sample": 15, "pause_ok": 1.0, "pause_enabled": true}

New train rows: 69. Measured pauses: 69; successes: 69; share: 100.0%. Pause was never disabled. Empty disabled-pause rows would be N/A, not failures. No pause refusal or failed measured update was recorded.
The prelaunch 31 rows are excluded from logger-repair acceptance/trends and retained without backfilling.

| Statistic | Filled / new rows | First | Last | Mean |
| --- | ---: | ---: | ---: | ---: |
| learning_rate | 69/69 | 0.0003 | 0.0003 | 0.0003 (n=69) |
| entropy_loss | 69/69 | -3.7643940448760986 | -3.772407978773117 | -3.6970 (n=69) |
| policy_gradient_loss | 69/69 | -0.008834134903736413 | -0.0108142653334653 | -0.0079 (n=69) |
| value_loss | 69/69 | 0.076319323212374 | 0.09187892510090023 | 0.1027 (n=69) |
| loss | 69/69 | -0.005835225805640221 | 0.039349623024463654 | -0.0023 (n=69) |
| approx_kl | 69/69 | 0.009885539300739765 | 0.013141854666173458 | 0.0115 (n=69) |
| clip_fraction | 69/69 | 0.06298828125 | 0.11376953125 | 0.0834 (n=69) |
| explained_variance | 69/69 | 0.784746527671814 | 0.9372879266738892 | 0.8380 (n=69) |
| n_updates | 69/69 | 128.0 | 400.0 | 264.0000 (n=69) |

## Approximately 30k observed-gameplay-step windows

Completed episodes are assigned by cumulative episode-step endpoint from fresh zero. Boundary episodes are not split. Rates use complete-episode steps. Cumulative observed steps include earlier unsaved tails and do not equal model/checkpoint steps. The last window is partial.

| Steps | Episodes | Episode steps | Exit start | Rooms mean | Kills/1k | Clears/1k | Stage>=2 episodes | Stalls | Deaths | Stalled-step share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-30000 | 119 | 29940 | 77/119 (64.7%) | 1.7983 (n=119) | 3.407 | 0.668 | 0/119 (0.0%) | 88/119 (73.9%) | 31/119 (26.1%) | 24995/29940 (83.5%) |
| 30000-60000 | 133 | 29951 | 105/133 (78.9%) | 1.8797 (n=133) | 4.407 | 0.467 | 0/133 (0.0%) | 87/133 (65.4%) | 46/133 (34.6%) | 23064/29951 (77.0%) |
| 60000-90000 | 124 | 29784 | 84/124 (67.7%) | 1.8065 (n=124) | 2.619 | 0.638 | 0/124 (0.0%) | 92/124 (74.2%) | 32/124 (25.8%) | 23789/29784 (79.9%) |
| 90000-105104 | 67 | 15429 | 52/67 (77.6%) | 1.8358 (n=67) | 2.722 | 0.648 | 0/67 (0.0%) | 47/67 (70.1%) | 20/67 (29.9%) | 12521/15429 (81.2%) |

## Schema7 at equal cumulative episode-step bounds

Schema7 reference ends at t204800. No extrapolation or claim of exact matched model-step exposure; separate uncontrolled game trajectories, descriptive comparison only. Both configurations use seed 1; native room/episode sequences are not paired.

| Steps | Schema | Episodes | Episode steps | Exit start | Rooms mean | Kills/1k | Clears/1k | Stage>=2 episodes | Stalls | Deaths | Stalled-step share |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-30000 | 8 | 119 | 29940 | 77/119 (64.7%) | 1.7983 (n=119) | 3.407 | 0.668 | 0/119 (0.0%) | 88/119 (73.9%) | 31/119 (26.1%) | 24995/29940 (83.5%) |
| 0-30000 | 7 | 146 | 29966 | 66/146 (45.2%) | 1.4795 (n=146) | 2.136 | 0.467 | 0/146 (0.0%) | 122/146 (83.6%) | 24/146 (16.4%) | 27002/29966 (90.1%) |
| 30000-60000 | 8 | 133 | 29951 | 105/133 (78.9%) | 1.8797 (n=133) | 4.407 | 0.467 | 0/133 (0.0%) | 87/133 (65.4%) | 46/133 (34.6%) | 23064/29951 (77.0%) |
| 30000-60000 | 7 | 150 | 30015 | 86/150 (57.3%) | 1.6667 (n=150) | 3.365 | 0.433 | 0/150 (0.0%) | 101/150 (67.3%) | 49/150 (32.7%) | 23154/30015 (77.1%) |
| 60000-90000 | 8 | 124 | 29784 | 84/124 (67.7%) | 1.8065 (n=124) | 2.619 | 0.638 | 0/124 (0.0%) | 92/124 (74.2%) | 32/124 (25.8%) | 23789/29784 (79.9%) |
| 60000-90000 | 7 | 166 | 29933 | 105/166 (63.3%) | 1.7530 (n=166) | 4.610 | 0.935 | 0/166 (0.0%) | 113/166 (68.1%) | 53/166 (31.9%) | 24549/29933 (82.0%) |
| 90000-105104 | 8 | 67 | 15429 | 52/67 (77.6%) | 1.8358 (n=67) | 2.722 | 0.648 | 0/67 (0.0%) | 47/67 (70.1%) | 20/67 (29.9%) | 12521/15429 (81.2%) |
| 90000-105104 | 7 | 83 | 15046 | 62/83 (74.7%) | 1.7952 (n=83) | 7.045 | 1.063 | 0/83 (0.0%) | 63/83 (75.9%) | 20/83 (24.1%) | 13524/15046 (89.9%) |

## Logger trend by checkpoint-step windows (new statistics only)

Logger rows use their saved model timesteps, distinct from the cumulative gameplay windows above. entropy_loss is the raw SB3 negative-entropy estimate. A trend in optimizer statistics is not native gameplay acceptance.

| Model steps | Rows | entropy_loss mean | explained_variance mean |
| --- | ---: | ---: | ---: |
| 30000-60000 | 27 | -3.7156 (n=27) | 0.8180 (n=27) |
| 60000-90000 | 29 | -3.6574 (n=29) | 0.8359 (n=29) |
| 90000-120000 | 13 | -3.7466 (n=13) | 0.8845 (n=13) |

The mean explained variance rose from 0.8180 in the first partial model-step bin to 0.8845 in the last partial bin. Negative entropy estimates were non-monotonic (-3.7156, -3.6574, -3.7466); these optimizer statistics do not establish improved gameplay.

## Mean reward components per complete episode

| Component | 0-30000 | 30000-60000 | 60000-90000 | 90000-105104 |
| --- | ---: | ---: | ---: | ---: |
| col_enemy_damage | 5.7827 (n=119) | 6.6250 (n=133) | 4.1468 (n=124) | 4.2901 (n=67) |
| col_room_clear | 1.6807 (n=119) | 1.0526 (n=133) | 1.5323 (n=124) | 1.4925 (n=67) |
| col_room_visit | 3.9916 (n=119) | 4.3985 (n=133) | 4.0323 (n=124) | 4.1791 (n=67) |
| col_floor_entered | 0.0000 (n=119) | 0.0000 (n=133) | 0.0000 (n=124) | 0.0000 (n=67) |
| col_damage_taken | -1.3193 (n=119) | -1.4887 (n=133) | -1.1371 (n=124) | -1.2537 (n=67) |
| col_death | -2.6050 (n=119) | -3.4586 (n=133) | -2.5806 (n=124) | -2.9851 (n=67) |
| col_time | -0.2603 (n=119) | -0.2346 (n=133) | -0.2488 (n=124) | -0.2379 (n=67) |
| col_pickup_coin | 0.0126 (n=119) | 0.0023 (n=133) | 0.0097 (n=124) | 0.0045 (n=67) |
| col_pickup_bomb | 0.0000 (n=119) | 0.0752 (n=133) | 0.0000 (n=124) | 0.0000 (n=67) |
| col_pickup_key | 0.0042 (n=119) | 0.0075 (n=133) | 0.0040 (n=124) | 0.0075 (n=67) |
| col_collectible_new | 0.0840 (n=119) | 0.3759 (n=133) | 0.2016 (n=124) | 0.0000 (n=67) |
| col_heal | 0.0252 (n=119) | 0.0150 (n=133) | 0.0202 (n=124) | 0.0000 (n=67) |
| col_novelty | 4.7647 (n=119) | 4.1556 (n=133) | 3.9185 (n=124) | 3.1045 (n=67) |
| col_stall | -3.6975 (n=119) | -3.2707 (n=133) | -3.7097 (n=124) | -3.5075 (n=67) |
| col_stagnation | -5.8302 (n=119) | -5.0030 (n=133) | -5.8222 (n=124) | -5.3185 (n=67) |
| col_door_shaping | 0.6166 (n=119) | 0.5468 (n=133) | 0.5916 (n=124) | 0.5891 (n=67) |

## Stall diagnostics

### This finite run only

Known context: 213/213 stalls; missing historical context is excluded, never imputed.
Uncleared: 20/213 (9.4%); clear: 193/213 (90.6%).

| Stall room type | Episodes / known stalls |
| --- | ---: |
| 1 | 139/213 (65.3%) |
| 4 | 32/213 (15.0%) |
| 13 | 17/213 (8.0%) |
| 10 | 16/213 (7.5%) |
| 2 | 8/213 (3.8%) |
| 6 | 1/213 (0.5%) |

Dead-end proxy (clear and no open unexplored doors): 75/213 (35.2%) of all known stalls; 75/193 (38.9%) of clear stalls.

| Uncleared-room metric | Mean / available denominator |
| --- | ---: |
| stall_enemies | 1.9500 (n=20) |
| stall_oracle_enemies | 1.9500 (n=20) |
| stall_nearest_enemy | 337.5556 (n=18) |
| stall_enemies_invulnerable | 0.0500 (n=20) |
| stall_enemies_flying | 0.0500 (n=20) |
| stall_enemies_boss | 0.0500 (n=20) |

Top 10 enemy kinds, counted once per uncleared stalled episode containing type.variant.

| Kind | Episodes |
| --- | ---: |
| 12.0 | 4 |
| 217.0 | 3 |
| 29.0 | 2 |
| 77.0 | 2 |
| 16.0 | 1 |
| 11.1 | 1 |
| 96.0 | 1 |
| 15.1 | 1 |
| 51.0 | 1 |
| 16.1 | 1 |

### All available schema8 history with context

Known context: 270/314 stalls; missing historical context is excluded, never imputed.
Uncleared: 22/270 (8.1%); clear: 248/270 (91.9%).

| Stall room type | Episodes / known stalls |
| --- | ---: |
| 1 | 173/270 (64.1%) |
| 4 | 42/270 (15.6%) |
| 13 | 24/270 (8.9%) |
| 10 | 20/270 (7.4%) |
| 2 | 9/270 (3.3%) |
| 7 | 1/270 (0.4%) |
| 6 | 1/270 (0.4%) |

Dead-end proxy (clear and no open unexplored doors): 99/270 (36.7%) of all known stalls; 99/248 (39.9%) of clear stalls.

| Uncleared-room metric | Mean / available denominator |
| --- | ---: |
| stall_enemies | 2.0000 (n=22) |
| stall_oracle_enemies | 2.0000 (n=22) |
| stall_nearest_enemy | 357.6700 (n=20) |
| stall_enemies_invulnerable | 0.0455 (n=22) |
| stall_enemies_flying | 0.0455 (n=22) |
| stall_enemies_boss | 0.0455 (n=22) |

Top 10 enemy kinds, counted once per uncleared stalled episode containing type.variant.

| Kind | Episodes |
| --- | ---: |
| 217.0 | 4 |
| 12.0 | 4 |
| 11.0 | 2 |
| 29.0 | 2 |
| 77.0 | 2 |
| 16.0 | 1 |
| 11.1 | 1 |
| 96.0 | 1 |
| 15.1 | 1 |
| 51.0 | 1 |

## Verification

Final documentation whitespace and local-link checks passed; strict OpenSpec validation passed 25/25. No source or config changes were made after the frozen launch. The earlier full Windows gate is retained as source verification, not rerun for this documentation-only report.

## Limits

The later 60k-90k cumulative window has fewer kills and clears per 1,000 steps than schema7, while the earliest window has more; outcomes are mixed. Stage 2 was never observed. No new frozen evaluation or task 2.3/gameplay-improvement claim. Save/Cloud untouched. Any authorized pause-flag change and integrity discrepancy must be described above. Raw logs, models, local helpers and unrelated tools/ are excluded from Git. Self-review only.
