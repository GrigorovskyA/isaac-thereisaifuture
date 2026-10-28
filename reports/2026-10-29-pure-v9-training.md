# Evidence: pure-v9 qualification and training

The one-hour qualification ended cleanly, but **continuation is blocked by the native visited-cell geometry check**. No continuation, retry, reinitialization or geometry fix was performed. Tasks 2.2 and 2.3 remain open. The report keeps the originally requested morning date; this run ended on October 28.

- Native Windows/Steam/file 2; observation 6 (3904 inputs), action 2, reward pure-v9, seed 1.
- Contract: `82b1b53e4703d8527eb38605363cc0f5f794ad95c51273433289f5e24c6ffe1b`; ent_coef=0.005, gamma=0.998, stall 40 s.
- Fresh lineage initialized once after preserving reward v8 as runs/pure-v4-reward-v8, including its stop.forever and checkpoint t588288. Any later sessions resume compatible checkpoints without initialization.
- Qualification start UTC: 2026-10-28T15:23:33.091547+00:00; ended: 2026-10-28T16:23:37.309391+00:00. Qualification duration 3600 seconds.
- Conditional continuation authorized only after native review, fixed deadline October 29 at 09:00 CET (08:00 UTC). Caps: 20,480,000,000 bytes, five consecutive infrastructure faults, bounded 8-hour leases.
- Final checkpoint: `82b1b53e-s1-t13824`, 13824 optimizer steps. Final UTC epoch: 1793204526.5153751.
- Last saved progress: October 28, 17:22:06 CET. Timer stop and cleanup completed at 17:23:37 CET. Completed episodes include 14,173 environment steps; 349 of those are beyond the last published checkpoint, in the unsaved final rollout. They are counted in gameplay metrics, not claimed as checkpoint training steps.
- Windows gate: 1324 tests passed including Lua, no skips; one existing synthetic All-NaN warning. Lint/format/mypy/pip and strict OpenSpec 22/22 passed; synthetic CPU smoke passed (3904 inputs).

## Sessions

| Session | Parent | State | Learner exit | Fault | Cleanup | Final |
|---|---|---|---:|---|---|---|
| session-20261028-162333-0001 | fresh | user_cancelled | 0 | None | [] | 82b1b53e-s1-t13824 |

## Native qualification audit

| Check | Result | Native evidence |
|---|---|---|
| Door potential and per-step formula | passed | All 14,173 audited steps match the recomputed eligible-room potential and gamma * Phi_after - Phi_before; completed-episode sums match CSV. |
| Per-episode door sums | passed within observed scope | 0.2035 to 1.3989; maximum absolute sum per distinct eligible clear room 1.3038, below 2. |
| Standing reward | passed within observed scope | 255 near-stationary steps; no excess beyond the discount residual plus the geometric bound for less than 0.01 px jitter. The discount residual is intentionally nonzero. |
| Clear-room eligibility | passed for oracle state; metric distinction below | Potential is nonzero only for clear rooms without enemies and an open unexplored door; transitions and terminals can telescope the previous clear-room potential. |
| Boss clear bonus | not encountered | No boss room clear and no bonus outside a boss room; positive native boss-bonus coverage is not claimed. |
| Doors and snapshot validation | passed | 69,178 valid snapshots, up to four doors, maximum 11,629 bytes < 49,152; no decode/audit errors. |
| 1x1 visited-cell geometry | blocked | 3,790/13,568 positions (27.9%) map beyond the requested 13 columns x 7 rows. |

All 71 episodes have a nonzero door sum, including 64 with no explicit room-clear event in metrics: their starting room is already clear. An already-clear oracle room is different from an episode that earns col_room_clear. This distinction must not be hidden by calling all those episodes combat clears.

The encoder calculates floor(x/40)-floor(60/40), floor(y/40)-floor(140/40). Native 1x1 indices span columns 0..13 and rows 0..7, rather than 0..12 and 0..6. For example, player (320, 400.746) sets cell (7,7); an origin-relative 40 px grid would set (6,6). There are 10,722/13,568 origin-relative cell disagreements. All actual encoded current-cell bits were present, so this is a quantization/origin disagreement, not missing visitation bits or saturation of the full 27x15 array. The player also briefly crossed nominal interior bounds in 81/13,568 samples, consistent with door passage; that alone is not evidence of a coordinate fault. No encoder change was made, as requested.

Recovery requires an explicit geometry decision and the corresponding offline specification/test review before another authorized native check or continuation. This report does not choose between changing quantization and accepting a different grid definition. No new lineage or initialization is authorized by the report.

```json
{
  "state": "blocked",
  "errors": [
    "Native 1x1 coordinates do not fit expected 13x7 region; report only, do not fix"
  ],
  "notes": [
    "Encoder uses floor(world/40)-floor(origin/40), not floor((world-origin)/40); inspect geometry before authorizing continuation",
    "Boss bonus native positive case not encountered; do not claim verified"
  ],
  "episodes": 71,
  "steps": 14173,
  "wire_snapshots": 69178,
  "max_snapshot_bytes": 11629,
  "max_doors": 4,
  "audit_errors": [],
  "shaping_episodes": 71,
  "stationary_steps": 255,
  "stationary_excess": 0,
  "boss_clear_events": 0,
  "bonus_without_boss": 0,
  "geometry": {
    "samples": 13568,
    "physical_outside": 81,
    "grid_outside_13x7": 3790,
    "origin_relative_cell_disagreement": 10722,
    "x_range": [
      45.69787979126,
      594.30218505859
    ],
    "y_range": [
      125.41035461426,
      433.86090087891
    ]
  }
}
```

Review: `{   "state": "blocked",   "checkpoint": "82b1b53e-s1-t13824",   "reason": "Native 1x1 visited-cell indices do not fit requested origin-relative 13x7 grid; user requested report without fix",   "clean_stop": true,   "source_frozen": true,   "archive_preserved": true,   "assessment": "assessment.json",   "extra": "review-extra.json" }`.

## Approximately 30,000-step gameplay windows

Assign whole completed episodes by interpolated completion time between train.csv wall-time/optimizer-step anchors. Boundary episodes are not split; rates use completed-episode steps. Unfinished episodes are excluded. New item means pickups_collectible > 0; exit start means rooms_visited > 1. The final window is partial.

| Step window | Episodes | Episode steps | Stalls | Steps in stalled episodes | Exit start | Rooms visited mean | Kills/1k | Clears/1k | New-item episodes | Max stage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0-13824 | 71 | 14173 | 53/71 (74.6%) | 11685/14173 (82.4%) | 37/71 (52.1%) | 1.606 | 3.457 | 0.494 | 1/71 (1.4%) | 1 |

## Mean reward components per completed episode

| Component | 0-13824 |
|---|---:|
| col_enemy_damage | 4.2618 |
| col_room_clear | 0.9859 |
| col_room_visit | 3.0282 |
| col_floor_entered | 0.0000 |
| col_damage_taken | -1.3239 |
| col_death | -2.5352 |
| col_time | -0.2403 |
| col_pickup_coin | 0.0042 |
| col_pickup_bomb | 0.0000 |
| col_pickup_key | 0.0000 |
| col_collectible_new | 0.0704 |
| col_heal | 0.0000 |
| col_novelty | 4.3986 |
| col_stall | -3.7324 |
| col_stagnation | -5.6897 |
| col_door_shaping | 0.6293 |

## Evidence and limits

- Full gate, deployment/archive receipts, passive native audit, qualification review and session results: reports/local/pure-v9-qualification-20261028/ and runs/pure-v4/. Raw logs/models remain outside Git.
- Live cleanup verified: no Isaac, worker, forever supervisor or first-hour owner process remains; no listener on port 9528; owned action_authorization.json absent; stop.forever present. Runtime source/config hashes still match the frozen launch, and archived v8 checkpoint hashes/stop.forever remain intact. The follow-up automation is removed because continuation is blocked and no further run is authorized.
- Geometry discrepancies are reported without changing the encoder. Boss positive-case coverage is separate from absence of an invalid bonus.
- Self-review only. No new frozen evaluation or native gameplay acceptance claim; OpenSpec task 2.3 remains open.
