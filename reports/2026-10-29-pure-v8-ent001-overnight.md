# Evidence: pure-v8 entropy-coefficient continuation, 2026-10-28/29

- Revision: `fb393624a55056a30599bee576237da08ff44a52`; resumed `fb22b342-s1-t510976` without initialization.
- The first leg ran 09:46:35-12:02:56 CET on October 28. After the user paused it for a [menu-only parallel-instance probe](2026-10-28-isaac-parallel-instance-probe.md), the user explicitly resumed from t539648 at 12:09:50 CET, revision `abb848b`. Documentation-only commit `ca47e69` followed; runtime inputs stayed frozen.
- Native Windows/Steam, file 2; pure-v8 contract `fb22b3429127c22b325c20594d1ab6d2931fae684ceab6eef9af4731136eb938`; observation 5/action 2, seed 1.
- Only ent_coef changed: 0.005 to 0.01. Reward/stall 40 s and runtime code remained unchanged; no evaluation was run.
- Parent t510976 is pinned in seed-1/checkpoints/pinned.txt.
- UTC start: 2026-10-28T08:46:35.349844+00:00; end: 2026-10-28T14:51:24.314967+00:00. Authorized deadline: 2026-10-29 09:00 CET (08:00 UTC).
- Caps: five consecutive faults, 20,480,000,000 bytes, bounded 8-hour leases; stop.forever on deadline or mean use_none below 0.40 across 40 new completed rollouts.
- Stop reason: `user cancelled`; launcher exit 0; stop marker present: True.
- The user explicitly stopped the resumed leg on October 28 at 15:51 CET; final owner cleanup ended at 15:51:24 CET. This supersedes the original October 29 deadline. Training remains stopped and the recurring monitor was deleted, not rescheduled. The report filename retains the originally requested date.
- Last checkpoint: `fb22b342-s1-t588288`, 588288 steps; +77312 since tuning. Last checkpoint UTC epoch: 1793199002.6686792.
- Last saved progress: October 28 at 15:50:02 CET. Both legs ended with learner_exit=0, fault null and cleanup_errors empty; no lease rollover or infrastructure fault occurred during this trial.
- Preflight Windows gate: 1271 tests passed including Lua, no skips, one existing synthetic All-NaN warning; lint/format/mypy/pip passed; strict OpenSpec 21/21.

## Sessions and faults

| Session | Parent | Final checkpoint | State | Learner exit | Fault | Cleanup errors |
|---|---|---|---|---:|---|---|
| session-20261028-094637-0001 | fb22b342-s1-t510976 | fb22b342-s1-t539648 | user_cancelled | 0 | None | [] |
| session-20261028-120950-0001 | fb22b342-s1-t539648 | fb22b342-s1-t588288 | user_cancelled | 0 | None | [] |

## Gameplay by approximately 30,000 optimizer steps

Completed episodes are assigned whole to a window by their end time, interpolated between train.csv wall-time/step anchors. Boundary episodes are not split. Rates use completed-episode steps, which can differ from optimizer steps and exclude unfinished episodes at stop or fault. Exit start means rooms_visited > 1. New item means pickups_collectible > 0. These are training outcomes, not frozen evaluation or acceptance evidence.

| Step window | Episodes | Episode steps | Stall episodes | Steps in stalled episodes | Exit start | Rooms visited mean | Kills/1k | Clears/1k | Episodes with new item |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 510976-540976 | 177 | 29939 | 122/177 (68.9%) | 26105/29939 (87.2%) | 133/177 (75.1%) | 1.8136 | 6.079 | 0.735 | 13/177 (7.3%) |
| 540976-570976 | 183 | 29805 | 128/183 (69.9%) | 26403/29805 (88.6%) | 134/183 (73.2%) | 1.7978 | 4.932 | 0.805 | 10/183 (5.5%) |
| 570976-588288 | 101 | 17373 | 72/101 (71.3%) | 14548/17373 (83.7%) | 71/101 (70.3%) | 1.7426 | 4.144 | 0.633 | 8/101 (7.9%) |

## Optimizer and use head by the same windows

Arithmetic means of completed rollout rows; policy entropy is -entropy_loss. Use fractions describe requested actions, not verified item effects. The guard uses each consecutive trailing group of 40 new rollout rows, not these wider windows.

| Step window | Rollouts | Entropy | Approx KL | Clip fraction | Use none | Use bomb |
|---|---:|---:|---:|---:|---:|---:|
| 510976-540976 | 58 | 2.7324 | 0.0333 | 0.1718 | 0.6569 | 0.1207 |
| 540976-570976 | 59 | 2.7477 | 0.0288 | 0.1629 | 0.5965 | 0.1281 |
| 570976-588288 | 34 | 2.5839 | 0.0285 | 0.1574 | 0.6202 | 0.1045 |

Last guard observation: `{"checked_at_utc": "2026-10-28T14:51:13.314834+00:00", "rollouts": 151, "window": 40, "mean_use_none": 0.64189453125, "latest_timesteps": 588288, "threshold": 0.4}`.

Across all complete 40-rollout windows since tuning, the minimum use_none mean was 0.5313 and the final mean was 0.6419. The 0.40 stop condition never fired. The pause did not reset the window.

## Evidence and limits

- First-leg receipts: reports/local/pure-v8-ent001-20261028/{launch.json,continuation-result.json,use-head-guard.json,check-full.log}. Resumed-leg receipts and combined report inputs: reports/local/pure-v8-ent001-resume-20261028/. Full session events/results remain under runs/pure-v4/supervisor/.
- Live shutdown verified after the final user stop: no Isaac, worker, forever supervisor or local timer-owner process remained; port 9528 had no listener, and stop.forever was present. The recurring automation was deleted. No source/config/mod/save changes or new evaluations accompanied the stop.
- Self-review only. No frozen evaluation, baseline comparison, Dead God claim or new OpenSpec gameplay acceptance. Raw logs and models remain outside Git.
