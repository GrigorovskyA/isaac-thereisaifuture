# Evidence: pure-v7 t477184 frozen evaluations and bridge timing

- Revision: `4fc1ab5ae107e462ab6f7eca0d03eda24a2aa8b2`; unrelated tools/ excluded.
- Start: 2026-10-26T07:00:11.754377+00:00; timezone Europe/Amsterdam (UTC+1).
- Config SHA256: `d62dc21baf19941b0484e857f2124e8fbffb3d564ab9763a2e13619230c63bc4`, pure-v7, observation 5/action 2, seed 1.
- Python 3.12 project venv, RecurrentPPO, native Windows/Steam/file 2/structured bridge.
- Evaluation: checkpoint d62dc21b-s1-t477184 twice, then random-prior once, 3600 s each, no retries.
- Training: separate authorized one-hour continuation after all evaluations and comparison, no initialization/config edits.
- Caps: 20,480,000,000-byte disk cap; pure restart authority; normal supervisor max five consecutive faults.

## Results

| Check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Windows gate | scripts/Check.ps1 with Lua | 0 | passed | 1247 tests, one All-NaN warning on synthetic missing columns; lint/format/mypy/pip clean; strict OpenSpec 19/19 |
| t477184-a | Start-Eval.cmd, 3600 s | 0 | passed | state=completed, cleanup=[], training byte-identical=True |
| t477184-b | Start-Eval.cmd, 3600 s | 0 | passed | state=completed, cleanup=[], training byte-identical=True |
| random-prior-b | Start-Eval.cmd, 3600 s | 0 | passed | state=completed, cleanup=[], training byte-identical=True |

## Comparison

```text
label           episodes  death  stall  left_room  damage  damage_se  kills  rooms_cleared  any_clear  hp_lost  return  max_stage  stall_lo  stall_hi  damage_1k  kills_1k  clears_1k
random          34        0.588  0.412  0.824      1.702   0.341      1.294  0.206          0.147      4.176    0.626   1.000      0.264     0.578     3.759      2.858     0.455
random-prior    40        0.575  0.425  0.825      1.349   0.225      0.850  0.150          0.150      3.900    -1.747  1.000      0.285     0.578     3.405      2.145     0.379
random-prior-b  37        0.486  0.514  0.784      1.731   0.370      1.270  0.162          0.162      3.865    0.393   1.000      0.359     0.666     4.123      3.026     0.386
t102400         34        0.382  0.618  0.706      1.931   0.467      1.588  0.206          0.206      3.353    1.705   1.000      0.450     0.761     4.317      3.550     0.460
t204800         38        0.263  0.737  0.447      0.511   0.137      0.263  0.053          0.053      2.316    -7.388  1.000      0.580     0.850     1.211      0.624     0.125
t237568         40        0.475  0.525  0.700      1.464   0.298      1.150  0.225          0.225      3.300    -0.314  1.000      0.375     0.671     3.686      2.895     0.567
t477184-a       36        0.167  0.833  0.528      0.861   0.281      0.639  0.111          0.111      1.694    -4.957  1.000      0.681     0.921     1.904      1.413     0.246
t477184-b       37        0.243  0.757  0.595      0.847   0.338      0.757  0.162          0.162      2.270    -4.997  1.000      0.599     0.866     1.932      1.725     0.370
v7-t244736      39        0.385  0.615  0.821      2.195   0.543      1.949  0.256          0.231      3.154    3.987   1.000      0.459     0.751     5.408      4.800     0.632

minus random-prior  damage_1k             kills_1k              clears_1k
random              +0.35 [-1.89, +2.77]  +0.71 [-1.14, +3.04]  +0.08 [-0.37, +0.60]
random-prior-b      +0.72 [-1.73, +3.38]  +0.88 [-1.08, +3.14]  +0.01 [-0.35, +0.39]
t102400             +0.91 [-1.55, +3.18]  +1.40 [-0.57, +3.29]  +0.08 [-0.28, +0.44]
t204800             -2.19 [-3.90, -0.74]  -1.52 [-2.67, -0.58]  -0.25 [-0.54, +0.06]
t237568             +0.28 [-1.83, +2.75]  +0.75 [-0.96, +2.71]  +0.19 [-0.20, +0.61]
t477184-a           -1.50 [-3.45, +0.40]  -0.73 [-2.09, +0.71]  -0.13 [-0.45, +0.18]
t477184-b           -1.47 [-3.60, +0.44]  -0.42 [-2.14, +1.33]  -0.01 [-0.36, +0.36]
v7-t244736          +2.00 [-0.85, +5.59]  +2.65 [+0.09, +5.82]  +0.25 [-0.17, +0.70]
```

The primary table includes every direct eval root containing metrics/episodes.csv. The baseline label is random-prior, as requested. Historical reward-v6 returns are not comparable with v7 returns; outcome columns remain descriptive.

## Revised task 2.3

Two-session pools: 73 checkpoint episodes vs 77 random-prior episodes. {"damage_1k": [-1.8426558438933738, -3.4427425458836467, -0.3495941242536054], "kills_1k": [-1.0127749023464458, -2.3774465846278083, 0.2778182304434761], "clears_1k": [-0.07485481201283006, -0.3263618144449326, 0.17884530317690167]}; task 2.3 remains open: both specified conditions did not pass.

Acceptance pools t477184-a+b and compares with random-prior plus random-prior-b, using the same deterministic unpaired episode bootstrap (2000 draws, seed 0). Thresholds: kills_1k interval lower bound >0 and clears_1k point difference >0. Full per-run tables are retained separately. This is self-review; episode bootstrapping does not capture all between-session variance, and game RNG is not paired.

## One-hour native timing verification

{
  "status": "passed",
  "new_rows": 29,
  "legacy_rows_preserved": 932,
  "first_new_row": {
    "timesteps": "477696",
    "rollout_seconds": "121.70300000000861",
    "game_wait_seconds": "111.00200000032783",
    "command_seconds": "5.6519999996817205",
    "snapshots_per_step": "4.54296875"
  },
  "last_checkpoint": "d62dc21b-s1-t492032",
  "result": {
    "state": "user_cancelled",
    "updated_at": 1793012395.2003987,
    "observed_monotonic": 188778.171,
    "started_at": 1793008817.6222765,
    "deadline_monotonic": 213940.00272345543,
    "elapsed_seconds": 3577.546000000002,
    "last_activity_monotonic": 188776.281,
    "phase_seconds": {
      "startup": 20.76500000001397,
      "waiting": 0.10999999998603016,
      "training": 3539.027999999962,
      "checkpointing": 17.643000000040047
    },
    "latest_checkpoint": {
      "id": "d62dc21b-s1-t492032",
      "steps": 492032,
      "path": "D:\\isaac\\runs\\pure-v4\\seed-1\\checkpoints\\d62dc21b-s1-t492032",
      "completed_at": 1793012393.0644677
    },
    "last_checkpoint_update_at": 1793012393.2615378,
    "checkpoint_note": null,
    "reason": "User cancellation requested",
    "stop_observed_monotonic": 188776.281,
    "fault": null,
    "learner_exit": 0,
    "cleanup_errors": [],
    "sampled_peak_bytes": 1406644839,
    "ended_at": 1793012395.2003987
  },
  "attempts": [
    {
      "session": {
        "output": "D:\\isaac\\runs\\pure-v4\\supervisor\\session-20261026-105952-0001",
        "resumed": true,
        "parent": "d62dc21b-s1-t477184",
        "latest": "d62dc21b-s1-t477184",
        "state": "fault",
        "reason": "Worker exited without a completion reason"
      },
      "result": {
        "state": "fault",
        "updated_at": 1793008817.4677942,
        "observed_monotonic": 185200.468,
        "started_at": 1793008792.588146,
        "deadline_monotonic": 213915.0048540287,
        "elapsed_seconds": 24.875,
        "last_activity_monotonic": 185176.359,
        "phase_seconds": {
          "startup": 24.875
        },
        "latest_checkpoint": {
          "id": "d62dc21b-s1-t477184",
          "steps": 477184,
          "path": "D:\\isaac\\runs\\pure-v4\\seed-1\\checkpoints\\d62dc21b-s1-t477184",
          "completed_at": 1792985949.906387
        },
        "last_checkpoint_update_at": null,
        "checkpoint_note": null,
        "reason": "Worker exited without a completion reason",
        "stop_observed_monotonic": null,
        "fault": "MenuEntryError: Isaac lost focus during menu input",
        "learner_exit": 1,
        "cleanup_errors": [
          "worker: RuntimeError: Owned worker required termination; cooperative release unverified"
        ],
        "sampled_peak_bytes": 1313428238,
        "ended_at": 1793008817.4677942
      }
    },
    {
      "session": {
        "output": "D:\\isaac\\runs\\pure-v4\\supervisor\\session-20261026-110017-0002",
        "resumed": true,
        "parent": "d62dc21b-s1-t477184",
        "latest": "d62dc21b-s1-t492032",
        "state": "user_cancelled",
        "reason": "User cancellation requested"
      },
      "result": {
        "state": "user_cancelled",
        "updated_at": 1793012395.2003987,
        "observed_monotonic": 188778.171,
        "started_at": 1793008817.6222765,
        "deadline_monotonic": 213940.00272345543,
        "elapsed_seconds": 3577.546000000002,
        "last_activity_monotonic": 188776.281,
        "phase_seconds": {
          "startup": 20.76500000001397,
          "waiting": 0.10999999998603016,
          "training": 3539.027999999962,
          "checkpointing": 17.643000000040047
        },
        "latest_checkpoint": {
          "id": "d62dc21b-s1-t492032",
          "steps": 492032,
          "path": "D:\\isaac\\runs\\pure-v4\\seed-1\\checkpoints\\d62dc21b-s1-t492032",
          "completed_at": 1793012393.0644677
        },
        "last_checkpoint_update_at": 1793012393.2615378,
        "checkpoint_note": null,
        "reason": "User cancellation requested",
        "stop_observed_monotonic": 188776.281,
        "fault": null,
        "learner_exit": 0,
        "cleanup_errors": [],
        "sampled_peak_bytes": 1406644839,
        "ended_at": 1793012395.2003987
      }
    }
  ],
  "supervisor": {
    "stop_reason": "user cancelled",
    "consecutive_faults": 1,
    "sessions": [
      {
        "output": "D:\\isaac\\runs\\pure-v4\\supervisor\\session-20261026-105952-0001",
        "resumed": true,
        "parent": "d62dc21b-s1-t477184",
        "latest": "d62dc21b-s1-t477184",
        "state": "fault",
        "reason": "Worker exited without a completion reason"
      },
      {
        "output": "D:\\isaac\\runs\\pure-v4\\supervisor\\session-20261026-110017-0002",
        "resumed": true,
        "parent": "d62dc21b-s1-t477184",
        "latest": "d62dc21b-s1-t492032",
        "state": "user_cancelled",
        "reason": "User cancellation requested"
      }
    ]
  },
  "note": "Automatic report guard expected one attempt; two occurred. Readback manually verified both attempts without changing native results. First attempt failed focus guard; second ran until the original one-hour timer.",
  "dashboard_fields_present": true
}

The training CSV legacy header is upgraded only after the frozen evaluations. Old metric values must remain unchanged, and new timing cells must be finite, nonnegative, with positive snapshots_per_step. These diagnostics never enter policy inputs or rewards.

## Real game, cleanup and limitations

Frozen tracked files unchanged before report/task writes: True. Training-root byte preservation during evaluations: True.
Exact commands/results, model hashes, complete training-tree hashes, saved old training CSV and comparison tables are in reports/local/pure-v7-t477184-20261026. Native result.json/plan.json/events.jsonl remain under runs/. No raw logs, model files or approvals are committed.
The existing sticky-fault handling and floor-transition message timeout were not modified. A recovered runtime fault may still mark a session as fault. A timed one-hour Start-Pure.cmd stop uses stop.forever and normally reports user_cancelled, which is expected for this requested timer stop, rather than a completed eight-hour lease.
No additional training or evaluation is scheduled after the one-hour stop. No post-run commit or push is performed by this pipeline.

## Startup failure and postprocessing correction

The first training attempt failed with MenuEntryError: Isaac lost focus during menu input; its worker required termination, so cooperative release was unverified for that failed attempt. The normal forever supervisor retried once within the same absolute one-hour budget. The second attempt resumed the same parent, saved t492032 and stopped cleanly on the timer. Overall execution includes one startup fault; it is not a wholly fault-free run. Automatic postprocessing then rejected the unexpected two-attempt count. Manual readback verified the native results, old CSV preservation and all new timing values; no native result was rewritten and no additional game session was launched.
