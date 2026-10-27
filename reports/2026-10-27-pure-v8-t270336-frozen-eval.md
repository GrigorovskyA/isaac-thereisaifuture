# Evidence: pure-v8 t270336 frozen evaluation

- Started (UTC): 2026-10-27T09:08:33.956325+00:00; Europe/Amsterdam UTC+1.
- Revision: `3861a1249d9556700d91588ec619a480b6bd4641`; pre-existing task/report changes and tools/ excluded from this commit.
- Contract: pure-v8, observation 5/action 2, seed 1, SHA256 `fb22b3429127c22b325c20594d1ab6d2931fae684ceab6eef9af4731136eb938`.
- Reward v8, stall 40 seconds. Checkpoint selected before evaluation: fb22b342-s1-t270336.
- Four successful native file-2 sessions, 3600 seconds each. The first baseline-b startup failed; the user then authorized exactly one retry. Disk cap 20,480,000,000 bytes.
- Start-Eval.cmd for checkpoint sessions; equivalent native CLI with explicit --evaluate random-prior for prefixed baseline labels (the wrapper otherwise selects uniform random).

## Results

| Session | Exit | State | Cleanup | Training tree unchanged | Status |
|---|---:|---|---|---|---|
| v8-t270336-a | 0 | completed | [] | True | passed |
| v8-t270336-b | 0 | completed | [] | True | passed |
| v8-random-prior-a | 0 | completed | [] | True | passed |
| v8-random-prior-b | 0 | completed | [] | True | passed |

## Per-session comparison

```text
label              episodes  death  stall  left_room  damage  damage_se  kills  rooms_cleared  any_clear  hp_lost  return  max_stage  stall_lo  stall_hi  damage_1k  kills_1k  clears_1k
v8-t270336-a       76        0.289  0.711  0.829      1.440   0.259      1.145  0.211          0.197      2.868    -0.403  1.000      0.600     0.800     7.140      5.678     1.044
v8-t270336-b       78        0.256  0.744  0.782      1.363   0.223      1.167  0.192          0.192      2.641    -1.302  1.000      0.637     0.827     7.193      6.156     1.015
v8-random-prior-a  73        0.247  0.753  0.534      0.738   0.165      0.562  0.068          0.068      2.342    -6.278  1.000      0.644     0.838     3.370      2.566     0.313
v8-random-prior-b  79        0.304  0.696  0.532      0.922   0.158      0.633  0.139          0.139      2.823    -4.949  1.000      0.588     0.787     4.672      3.207     0.706

minus v8-random-prior-a  damage_1k             kills_1k              clears_1k
v8-t270336-a             +3.77 [+0.85, +6.88]  +3.11 [+0.76, +5.51]  +0.73 [+0.23, +1.26]
v8-t270336-b             +3.82 [+1.15, +6.74]  +3.59 [+1.19, +6.21]  +0.70 [+0.20, +1.19]
v8-random-prior-b        +1.30 [-0.88, +3.48]  +0.64 [-1.16, +2.50]  +0.39 [-0.04, +0.81]

```

## Pooled checkpoint a+b versus random-prior a+b

Unpaired episode bootstrap: 2000 draws, seed 0, 95% percentile intervals, using scripts/compare_eval.py rate_difference unchanged.

```json
{
  "checkpoint_episodes": 154,
  "baseline_episodes": 152,
  "bootstrap_samples": 2000,
  "seed": 0,
  "checkpoint_rates": {
    "damage_1k": 7.165964138371478,
    "kills_1k": 5.912639096495599,
    "clears_1k": 1.029729280850357
  },
  "baseline_rates": {
    "damage_1k": 4.013106008734631,
    "kills_1k": 2.882574677690139,
    "clears_1k": 0.5068263169565079
  },
  "differences": {
    "damage_1k": [
      3.1528581296368463,
      1.1446814698824754,
      5.17156221523566
    ],
    "kills_1k": [
      3.0300644188054595,
      1.3371753570932068,
      4.7983259492641155
    ],
    "clears_1k": [
      0.5229029638938492,
      0.1308115524671985,
      0.9073832429275943
    ]
  }
}
```

## Real game and limitations

Native Steam/menu entry, file 2 and bridge actions are handled by session_runner. Each session retains plan.json, events.jsonl and result.json under runs/pure-v4-eval/_sessions/<label>.
Training checkpoints, latest pointer, metrics and stopped supervisor tree were SHA256 checked before and after every evaluation. Full receipts and console logs are under reports/local/pure-v8-t270336-20261027.
Only the four named v8 roots are compared. No historical v7 baseline is included. Completed-episode denominators exclude the final unfinished rollout; the failed baseline-b startup is preserved separately and excluded from episode pooling; only one explicitly authorized retry was performed.
Self-review only. Episode bootstrapping does not capture all between-session variance; game RNG is unpaired. OpenSpec acceptance 2.3 remains open: frozen outcomes alone do not establish its separate first-eight-hour stall requirement.

## Continuation

Training is stopped throughout evaluation. The user authorized resume through Start-Pure.cmd without --initialize, from fb22b342-s1-t270336, until 2026-10-28 09:00 Europe/Amsterdam (08:00 UTC). No configuration changes are included.

## Preserved failed attempt and recovery

The original v8-random-prior-b attempt failed at startup: Existing file2 game state not confirmed; no New Run fallback. Learner exit 1; worker required termination and cooperative release was unverified. It produced no evaluated episodes. Both failed trees are preserved with suffix -failed-20261027-130812. The native log reported no GameState 2. A guarded menu-only New Run on file 2 followed by normal owned-game close created Continue; no save files were edited. This preparation is excluded from evaluation outcomes. The authorized retry uses the same config, policy and hour budget.

The report is committed before continuation; runtime receipts are in reports/local/pure-v8-t270336-20261027/continuation-status.json and runs/pure-v4/supervisor/until-20261028-0900-timer.json. A planned continuation is not evidence of completed training.
