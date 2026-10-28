# Evidence: pure-v8 entropy-coefficient continuation, 2026-10-28/29

- Revision: `fb393624a55056a30599bee576237da08ff44a52`; resumed `fb22b342-s1-t510976` without initialization.
- Native Windows/Steam, file 2; pure-v8 contract `fb22b3429127c22b325c20594d1ab6d2931fae684ceab6eef9af4731136eb938`; observation 5/action 2, seed 1.
- Only ent_coef changed: 0.005 to 0.01. Reward/stall 40 s and runtime code remained unchanged; no evaluation was run.
- Parent t510976 is pinned in seed-1/checkpoints/pinned.txt.
- UTC start: 2026-10-28T08:46:35.349844+00:00; end: 2026-10-28T11:02:56.375440+00:00. Authorized deadline: 2026-10-29 09:00 CET (08:00 UTC).
- Caps: five consecutive faults, 20,480,000,000 bytes, bounded 8-hour leases; stop.forever on deadline or mean use_none below 0.40 across 40 new completed rollouts.
- Stop reason: `user cancelled`; launcher exit 0; stop marker present: True.
- The user paused training on October 28 at 12:02 CET to investigate parallel instances. The October 29 deadline was superseded by this early stop; training was not resumed. The filename retains the originally requested report date.
- Last checkpoint: `fb22b342-s1-t539648`, 539648 steps; +28672 since tuning. Last checkpoint UTC epoch: 1793185359.7438047.
- Preflight Windows gate: 1271 tests passed including Lua, no skips, one existing synthetic All-NaN warning; lint/format/mypy/pip passed; strict OpenSpec 21/21.

## Sessions and faults

| Session | Parent | Final checkpoint | State | Learner exit | Fault | Cleanup errors |
|---|---|---|---|---:|---|---|
| session-20261028-094637-0001 | fb22b342-s1-t510976 | fb22b342-s1-t539648 | user_cancelled | 0 | None | [] |

## Gameplay by approximately 30,000 optimizer steps

Completed episodes are assigned whole to a window by their end time, interpolated between train.csv wall-time/step anchors. Boundary episodes are not split. Rates use completed-episode steps, which can differ from optimizer steps and exclude unfinished episodes at stop or fault. Exit start means rooms_visited > 1. New item means pickups_collectible > 0. These are training outcomes, not frozen evaluation or acceptance evidence.

| Step window | Episodes | Episode steps | Stall episodes | Steps in stalled episodes | Exit start | Rooms visited mean | Kills/1k | Clears/1k | Episodes with new item |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 510976–539648 | 168 | 28616 | 116/168 (69.0%) | 24966/28616 (87.2%) | 126/168 (75.0%) | 1.8155 | 5.976 | 0.699 | 13/168 (7.7%) |

## Optimizer and use head by the same windows

Arithmetic means of completed rollout rows; policy entropy is -entropy_loss. Use fractions describe requested actions, not verified item effects. The guard uses each consecutive trailing group of 40 new rollout rows, not these wider windows.

| Step window | Rollouts | Entropy | Approx KL | Clip fraction | Use none | Use bomb |
|---|---:|---:|---:|---:|---:|---:|
| 510976–539648 | 56 | 2.7197 | 0.0325 | 0.1693 | 0.6583 | 0.1216 |

Last guard observation: `{"checked_at_utc": "2026-10-28T11:02:45.420724+00:00", "rollouts": 56, "window": 40, "mean_use_none": 0.642724609375, "latest_timesteps": 539648, "threshold": 0.4}`.

## Evidence and limits

- Local receipts: reports/local/pure-v8-ent001-20261028/{launch.json,continuation-result.json,use-head-guard.json,check-full.log}; full session events/results under runs/pure-v4/supervisor/.
- Live shutdown verified: no Isaac, learner, forever supervisor or local timer-owner processes remained; port 9528 had no listener, and stop.forever remained present. The recurring monitor was paused. A subsequent menu-only multi-instance probe also ended with its owned game closed normally; see [probe report](2026-10-28-isaac-parallel-instance-probe.md).
- Self-review only. No frozen evaluation, baseline comparison, Dead God claim or new OpenSpec gameplay acceptance. Raw logs and models remain outside Git.
