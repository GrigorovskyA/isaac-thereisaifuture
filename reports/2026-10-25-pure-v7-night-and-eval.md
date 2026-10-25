# Evidence: pure-v7 night training and frozen evaluation

- Revision: `aeb4b9ae3f5e46059ca4d56b110f23ca9237c2ea`; unrelated tools/ excluded.
- Date/time: night of 2026-10-24/25, Europe/Amsterdam. DST ends; 09:00 CET = 08:00 UTC.
- Training start: 2026-10-24T19:15:08.454618+00:00; stop: 2026-10-25T07:05:33.617753+00:00. Absolute authorized deadline: 2026-10-25T08:00:00+00:00.
- Contract: pure-v7, observation 5/action 2, seed 1, SHA256 `d62dc21baf19941b0484e857f2124e8fbffb3d564ab9763a2e13619230c63bc4`.
- Python 3.12 project venv; RecurrentPPO; native Windows/Steam/file 2/structured bridge.
- Configuration unchanged: gamma 0.998, gae_lambda 0.98, ent_coef 0.005. No initialization.
- Training cap: 20,480,000,000 bytes, max five consecutive faults, lease <=28740 s; stop immediately if a session is unclean.
- Evaluation: latest after clean night, then random-prior, 3600 s each; historical uniform random is not rerun.

## Results

| Check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Windows gate | scripts/Check.ps1 including Lua | 0 | passed | 1242 tests, strict OpenSpec 19/19; local check.log |
| Training session-20261024-211508-0001 | resume d62dc21b-s1-t74240 | 0 | passed | state=completed; cleanup=[]; latest=d62dc21b-s1-t188928 |
| Training session-20261025-041355-0002 | resume d62dc21b-s1-t188928 | 0 | passed (requested stop) | state=user_cancelled; cleanup=[]; latest=d62dc21b-s1-t244736 |
| Lease rollover | resume latest in second session | N/A | passed | See rollover.json and training-verification.json |
| Evaluation v7-t244736 | Start-Eval.cmd, 3600 s | 0 | passed | D:\isaac\runs\pure-v4-eval\_sessions\v7-t244736 |
| Evaluation random-prior | Start-Eval.cmd, 3600 s | 0 | passed | D:\isaac\runs\pure-v4-eval\_sessions\random-prior |

## Hourly night outcomes

Bins are consecutive elapsed hours, shown in UTC to disambiguate the DST transition. Completed episodes are assigned by completion timestamp; unfinished episodes are excluded. Exit means rooms_visited >1. Damage/HP are per-episode means; kills/clears are totals.

| UTC interval | Episodes | Stall | Exit start | Damage mean | Kills total | Clears total | Half-hearts lost mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-24T19:15:08.454618+00:00 to 2026-10-24T20:15:08.454618+00:00 | 38 | 29/38 (76.3%) | 24/38 (63.2%) | 0.7897 | 24 | 7 | 1.8421 |
| 2026-10-24T20:15:08.454618+00:00 to 2026-10-24T21:15:08.454618+00:00 | 33 | 23/33 (69.7%) | 19/33 (57.6%) | 1.4114 | 31 | 5 | 2.4545 |
| 2026-10-24T21:15:08.454618+00:00 to 2026-10-24T22:15:08.454618+00:00 | 30 | 22/30 (73.3%) | 26/30 (86.7%) | 1.3825 | 35 | 9 | 2.7000 |
| 2026-10-24T22:15:08.454618+00:00 to 2026-10-24T23:15:08.454618+00:00 | 43 | 23/43 (53.5%) | 30/43 (69.8%) | 1.1881 | 36 | 4 | 3.6279 |
| 2026-10-24T23:15:08.454618+00:00 to 2026-10-25T00:15:08.454618+00:00 | 33 | 19/33 (57.6%) | 27/33 (81.8%) | 1.3032 | 36 | 11 | 3.4242 |
| 2026-10-25T00:15:08.454618+00:00 to 2026-10-25T01:15:08.454618+00:00 | 34 | 24/34 (70.6%) | 24/34 (70.6%) | 1.8453 | 55 | 7 | 2.7647 |
| 2026-10-25T01:15:08.454618+00:00 to 2026-10-25T02:15:08.454618+00:00 | 35 | 22/35 (62.9%) | 27/35 (77.1%) | 1.2374 | 38 | 5 | 2.9143 |
| 2026-10-25T02:15:08.454618+00:00 to 2026-10-25T03:15:08.454618+00:00 | 32 | 22/32 (68.8%) | 21/32 (65.6%) | 1.1727 | 35 | 6 | 2.7812 |
| 2026-10-25T03:15:08.454618+00:00 to 2026-10-25T04:15:08.454618+00:00 | 33 | 24/33 (72.7%) | 20/33 (60.6%) | 1.2731 | 35 | 4 | 2.2727 |
| 2026-10-25T04:15:08.454618+00:00 to 2026-10-25T05:15:08.454618+00:00 | 32 | 18/32 (56.2%) | 27/32 (84.4%) | 1.5266 | 38 | 6 | 3.7500 |
| 2026-10-25T05:15:08.454618+00:00 to 2026-10-25T06:15:08.454618+00:00 | 33 | 21/33 (63.6%) | 21/33 (63.6%) | 0.9001 | 21 | 4 | 3.1515 |
| 2026-10-25T06:15:08.454618+00:00 to 2026-10-25T07:05:33.617753+00:00 | 29 | 16/29 (55.2%) | 23/29 (79.3%) | 1.8026 | 48 | 10 | 3.5862 |

## Frozen evaluation

```text
label         episodes  death  stall  left_room  damage  damage_se  kills  rooms_cleared  any_clear  hp_lost  return  max_stage  stall_lo  stall_hi
random        34        0.588  0.412  0.824      1.702   0.341      1.294  0.206          0.147      4.176    0.626   1.000      0.264     0.578
random-prior  40        0.575  0.425  0.825      1.349   0.225      0.850  0.150          0.150      3.900    -1.747  1.000      0.285     0.578
v7-t244736    39        0.385  0.615  0.821      2.195   0.543      1.949  0.256          0.231      3.154    3.987   1.000      0.459     0.751
t102400       34        0.382  0.618  0.706      1.931   0.467      1.588  0.206          0.206      3.353    1.705   1.000      0.450     0.761
```

These are unpaired native samples, not matched game seeds. Historical uniform random and t102400 used reward v6; compare damage/stall/clear outcomes, not returns across reward contracts. random-prior uses P(none)=0.85, each other use=0.05. No new checkpoint is selected after seeing its evaluation result.

Per 1000 completed-episode steps, v7-t244736 vs random-prior: clears 0.63 vs 0.38, damage 5.41 vs 3.41, kills 4.80 vs 2.15 (15,833 vs 15,848 steps).

## Real game and cleanup

Training consecutive faults: 0. Whole-training-root byte preservation during evaluations: True. Frozen tracked inputs unchanged before report/task writes: True.
Guarded Steam/menu entry and bridge gameplay use the native supervisor. Per-session result.json records learner exit, cleanup and faults. Source/deployed observer hashes are checked at preflight. Raw results, snapshots and logs remain in reports/local/pure-v7-night-20261024 and runs/, outside Git.

## Acceptance and continuation

Latest frozen result: stall 61.538%, damage fraction 2.1954. Task 2.3 stays open because its stall criterion is confounded by deaths (revision pending). The existing acceptance specification is unchanged.
random-prior task 2.2: passed.
Self-review only. No gameplay improvement claim follows from training loss or reward. Training remains stopped; no further session, config change, commit or push is performed by this pipeline.

The night run was stopped at the user's request at 08:05 CET, before its original 09:00 deadline, with no infrastructure fault. The first lease session completed normally and the second resumed its final checkpoint. Frozen evaluations were separately authorized after that stop. The original blocked training-to-evaluation pipeline receipt is retained as history; the requested cancellation is not a fault.
