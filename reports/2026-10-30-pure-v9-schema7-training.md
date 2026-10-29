# Evidence: pure-v9 schema 7 training stopped by user

Stopped early at the user's request on October 29 at 09:36:14 UTC / 10:36:14 CET.
The October 30 deadline was not reached; the filename retains the planned report date.
Source revision d789c5d; qualification/continuation revision f705e27.

- Native Windows/Steam/file 2; observation 7 (3863 inputs), action 2, reward pure-v9, seed 1.
- Contract: `3cb9d928e397ec26587bb72d89864ecd1dae04094404c36fb60fa282a9749310`; ent_coef=0.005, gamma=0.998, stall 40 s.
- Fresh schema7 lineage initialized once after preserving schema6 as runs/pure-v4-reward-v9-schema6, including its stop.forever and checkpoint t13824; reward v8 remains separately preserved. Any later sessions resume compatible checkpoints without initialization.
- Qualification start UTC: 2026-10-28T17:33:40.620730+00:00; ended: 2026-10-28T18:33:45.748076+00:00. Qualification duration 3600 seconds.
- Conditional continuation authorized only after native review, fixed deadline October 30 at 09:00 CET (08:00 UTC). Caps: 20,480,000,000 bytes, five consecutive infrastructure faults, bounded 8-hour leases.
- Final checkpoint: `3cb9d928-s1-t204800`, 204800 optimizer steps. Final UTC epoch: 1793266547.5950065.
- Windows gate: 1325 tests passed including Lua, no skips; one existing synthetic All-NaN warning. Lint/format/mypy/pip and strict OpenSpec 22/22 passed; synthetic CPU smoke passed (3863 inputs).

## Sessions

| Session | Parent | State | Learner exit | Fault | Cleanup | Final |
|---|---|---|---:|---|---|---|
| session-20261028-183341-0001 | fresh | user_cancelled | 0 | None | [] | 3cb9d928-s1-t13824 |
| session-20261028-193648-0001 | 3cb9d928-s1-t13824 | completed | 0 | None | [] | 3cb9d928-s1-t116736 |
| session-20261029-033536-0002 | 3cb9d928-s1-t116736 | fault | 0 | {'reason': 'Episode 317 fault: Command acknowledgement deadline expired', 'faults': 1, 'consecutive': 1} | [] | 3cb9d928-s1-t204800 |

## Native qualification audit

```json
{
  "state": "needs_review",
  "errors": [],
  "notes": [
    "Boss bonus native positive case not encountered; do not claim verified"
  ],
  "episodes": 67,
  "steps": 13824,
  "wire_snapshots": 69194,
  "max_snapshot_bytes": 12170,
  "max_doors": 6,
  "audit_errors": [],
  "shaping_episodes": 67,
  "stationary_steps": 262,
  "stationary_excess": 0,
  "boss_clear_events": 0,
  "bonus_without_boss": 0,
  "geometry": {
    "samples": 13148,
    "physical_outside": 49,
    "grid_outside_13x7": 49,
    "origin_relative_cell_disagreement": 0,
    "x_range": [
      46.596385955811,
      590.74176025391
    ],
    "y_range": [
      125.69786071777,
      434.08551025391
    ],
    "outside_near_door": 49,
    "outside_fraction": 0.0037268025555217523
  }
}
```

The independent review accepted t13824 for conditional continuation only.
[Qualification report](2026-10-28-pure-v9-schema7-qualification.md) records all checks
and coverage limits. The aggregator state needs_review above is not acceptance.
Native boss positive-case coverage remains missing; task 2.2 remains unchecked.

## Approximately 30,000-step gameplay windows

Assign whole completed episodes by interpolated completion time between train.csv wall-time/optimizer-step anchors. Boundary episodes are not split; rates use completed-episode steps. Unfinished episodes are excluded. New item means pickups_collectible > 0; exit start means rooms_visited > 1. The final window is partial.

| Step window | Episodes | Episode steps | Stalls | Steps in stalled episodes | Exit start | Rooms visited mean | Kills/1k | Clears/1k | New-item episodes | Max stage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0-30000 | 145 | 29767 | 121/145 (83.4%) | 26803/29767 (90.0%) | 66/145 (45.5%) | 1.483 | 2.150 | 0.470 | 5/145 (3.4%) | 1 |
| 30000-60000 | 150 | 29978 | 101/150 (67.3%) | 23117/29978 (77.1%) | 85/150 (56.7%) | 1.653 | 3.369 | 0.434 | 11/150 (7.3%) | 1 |
| 60000-90000 | 166 | 29956 | 113/166 (68.1%) | 24572/29956 (82.0%) | 105/166 (63.3%) | 1.759 | 4.607 | 0.935 | 11/166 (6.6%) | 1 |
| 90000-120000 | 165 | 29969 | 118/165 (71.5%) | 25323/29969 (84.5%) | 119/165 (72.1%) | 1.806 | 6.607 | 0.934 | 20/165 (12.1%) | 1 |
| 120000-150000 | 165 | 30229 | 109/165 (66.1%) | 25700/30229 (85.0%) | 139/165 (84.2%) | 1.976 | 6.782 | 1.257 | 13/165 (7.9%) | 1 |
| 150000-180000 | 158 | 29939 | 102/158 (64.6%) | 24789/29939 (82.8%) | 138/158 (87.3%) | 2.051 | 6.814 | 1.336 | 11/158 (7.0%) | 1 |
| 180000-204800 | 146 | 24927 | 82/146 (56.2%) | 19175/24927 (76.9%) | 137/146 (93.8%) | 2.171 | 10.190 | 1.364 | 7/146 (4.8%) | 1 |

## Mean reward components per completed episode

| Component | 0-30000 | 30000-60000 | 60000-90000 | 90000-120000 | 120000-150000 | 150000-180000 | 180000-204800 |
|---|---:|---:|---:|---:|---:|---:|---:|
| col_enemy_damage | 2.8294 | 4.6648 | 5.2078 | 7.1395 | 7.6821 | 7.7601 | 10.3758 |
| col_room_clear | 0.9655 | 0.8667 | 1.6867 | 1.6970 | 2.3030 | 2.5316 | 2.3288 |
| col_room_visit | 2.4138 | 3.2667 | 3.7952 | 4.0303 | 4.8788 | 5.2532 | 5.8562 |
| col_floor_entered | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| col_damage_taken | -1.1207 | -1.5167 | -1.3946 | -1.3697 | -1.5818 | -1.6835 | -1.9623 |
| col_death | -1.6552 | -3.2667 | -3.1928 | -2.8485 | -3.3939 | -3.5443 | -4.3836 |
| col_time | -0.2501 | -0.2578 | -0.2435 | -0.2474 | -0.2491 | -0.2537 | -0.2186 |
| col_pickup_coin | 0.0083 | 0.0160 | 0.0199 | 0.0200 | 0.0145 | 0.0133 | 0.0164 |
| col_pickup_bomb | 0.0000 | 0.0133 | 0.0151 | 0.0000 | 0.0182 | 0.0000 | 0.0171 |
| col_pickup_key | 0.0000 | 0.0067 | 0.0000 | 0.0121 | 0.0061 | 0.0032 | 0.0103 |
| col_collectible_new | 0.1724 | 0.3667 | 0.3313 | 0.6061 | 0.3939 | 0.3481 | 0.2397 |
| col_heal | 0.0103 | 0.0400 | 0.0241 | 0.0061 | 0.0152 | 0.0190 | 0.0205 |
| col_novelty | 3.6766 | 2.9793 | 2.2295 | 2.1576 | 2.2964 | 2.1791 | 1.9781 |
| col_stall | -4.1724 | -3.3667 | -3.4036 | -3.5758 | -3.3030 | -3.2278 | -2.8082 |
| col_stagnation | -6.1069 | -5.4674 | -5.0987 | -5.2037 | -4.8244 | -4.8398 | -4.2292 |
| col_door_shaping | 0.6415 | 0.5754 | 0.6038 | 0.5530 | 0.5483 | 0.5291 | 0.5544 |

## Evidence and limits

- Full gate, deployment/archive receipts, passive native audit, qualification review and session results: reports/local/pure-v9-schema7-20261028/ and runs/pure-v4/. Raw logs/models remain outside Git.
- Live shutdown verified October 29 at 09:36 UTC / 10:36 CET: no Isaac, learner,
  forever supervisor or continuation owner; no port 9528 listener; owned approval absent;
  stop.forever present. Every learner exited 0 and every cleanup_errors list is empty.
- The last session retains state fault despite reason User cancellation requested.
  This is the stored episode-317 command acknowledgement timeout at 07:18:36 UTC,
  recovered with subsequent episodes and checkpoint advancement to t204800. It is not
  a clean fault-null result; no retry or restart was initiated by this monitor.
- The first continuation lease completed normally at t116736 and resumed with that
  exact compatible parent. Its unfinished rollout was not checkpointed.
- Final checkpoint saved October 29 at 09:35:47 UTC / 10:35:47 CET.
  Completed-episode steps and final unsaved rollout metrics can exceed checkpoint steps.
- Automation isaac-pure-v9-schema-7 is being deleted after this user-requested stop.
- Geometry discrepancies are reported without changing the encoder. Boss positive-case coverage is separate from absence of an invalid bonus.
- Self-review only. No new frozen evaluation or native gameplay acceptance claim; OpenSpec task 2.3 remains open.
