# Evidence: pure-v7 four-hour continuation

- Date/time: 2026-10-24 16:25:54.108-20:25:39.900 Europe/Amsterdam (14:25:54.108-18:25:39.900 UTC).
- Revision: `f6db4c58b159e68e42846e16580a27f330192cb2`; unrelated `tools/` untracked. Frozen tracked files unchanged at shutdown.
- Scope: authorized four-hour continuation, no initialization or configuration changes; not a frozen policy evaluation.
- Runtime: native Windows, Steam Repentance+, save file 2, structured observer bridge; unchanged observer Lua/mod contract.
- Python/config: project Python 3.12, RecurrentPPO, seed 1; observation 5/action 2/reward contract `pure-v7`.
- Contract hash: `d62dc21baf19941b0484e857f2124e8fbffb3d564ab9763a2e13619230c63bc4`.
- Hyperparameters: gamma 0.998, gae_lambda 0.98, ent_coef 0.005, unchanged.
- Budget: 14,400 inclusive seconds, 20,480,000,000 bytes, five consecutive faults maximum; pure unlimited death/stall restarts. Latest parent `d62dc21b-s1-t14848`.

## Results

| Check | Scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Current Windows gate | `scripts/Check.ps1` including Lua | 0 | passed | 1242 tests, no skips; mypy/lint/format/pip clean; OpenSpec 19/19; local night check.log |
| Native continuation | session-20261024-162554-0001 | 0 | passed | state completed, learner_exit 0, fault null |
| Clean shutdown | cooperative deadline, 15-second margin | 0 | passed | cleanup_errors [], elapsed 14385.625 s |
| Model lineage | parent t14848 to latest t74240 | 0 | passed | 59,392 new saved steps, 116 rollout publications |
| Contract | final checkpoint manifest and configuration | 0 | passed | pure-v7, hash d62dc21b..., unchanged hyperparameters |
| Forever supervisor | one bounded session, stop file after completion | 0 | passed | consecutive_faults 0; no follow-up session |
| Frozen inputs / cleanup | post-run readback | 0 | passed | tracked_files_changed [], no Isaac process or bridge listener |
| Eight-hour frozen acceptance | change task 2.3 | N/A | not_run | Remains open; training statistics do not meet the frozen-evaluation requirement |

Raw evidence: `runs/pure-v4/supervisor/session-20261024-162554-0001/{plan,status,result,events}.json*`, `runs/pure-v4/supervisor/four-hour-verification.json`, `runs/pure-v4/metrics/{episodes,train}.csv`. Prepared launcher and logs: `reports/local/pure-v7-four-hour-20261024/`. Aggregation receipt: `reports/local/pure-v7-night-20261024/four-hour-summary.json`. Raw logs/models are excluded from Git.

## Hourly gameplay outcomes

Completed episodes are assigned by their CSV completion timestamp to four consecutive elapsed-hour bins beginning 14:25:54.108 UTC; the fourth ends at 18:25:39.900 UTC. Local bins are approximately 16:26-17:26, 17:26-18:26, 18:26-19:26, 19:26-20:26 CEST. Crossing episodes belong to the hour they finish; the unfinished final episode is excluded. Exit means rooms_visited > 1, matching compare_eval.py. Damage and HP lost are per-episode means; kills and clears are totals.

| Elapsed hour | Episodes | Stall | Exit start | Damage fraction mean | Kills total | Clears total | Half-hearts lost mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 37 | 19/37 (51.4%) | 29/37 (78.4%) | 1.3586 | 36 | 4 | 3.5135 |
| 2 | 36 | 25/36 (69.4%) | 26/36 (72.2%) | 1.3051 | 40 | 5 | 3.1667 |
| 3 | 40 | 23/40 (57.5%) | 30/40 (75.0%) | 1.5855 | 46 | 4 | 3.1500 |
| 4 | 45 | 25/45 (55.6%) | 42/45 (93.3%) | 1.9631 | 51 | 8 | 2.8889 |
| Total | 158 | 92/158 (58.2%) | 127/158 (80.4%) | 1.5760 | 173 | 21 | 3.1646 |

## Real game and interpretation

There were 66 deaths and 92 stall restarts among 158 complete episodes. The maximum stage remained 1. In the last hour, damage was 1.9631 versus 1.3586 in the first, start-room exits were 93.3% versus 78.4%, and mean half-hearts lost decreased from 3.5135 to 2.8889. Stall share fluctuated (51.4%, 69.4%, 57.5%, 55.6%). These are descriptive within-training observations; changing policy, unequal episode lengths and unpaired game randomness prevent a causal improvement claim.

The worker stopped for its wall-time budget; the final unfinished rollout had no new checkpoint. The final saved model was t74240. The forever summary and independent launch verification both confirm clean completion, no fault, stop.forever retained, and no automatic next session. The old reward-v6 directory remains separate.

## Limitations and continuation

This is self-review, not independent review. It does not close stagnation-cost-reward-v7 task 2.3: acceptance requires a frozen evaluation after at least eight hours, stall <41% and damage fraction >=1.70. The user separately authorized overnight continuation from t74240 until 09:00 Europe/Amsterdam on 2026-10-25, followed by one-hour latest-checkpoint and random-prior evaluations in that order. No hyperparameter or contract change is authorized. The night crosses the DST transition: 09:00 CET is 08:00 UTC. Uniform random and t102400 are historical reward-v6 evaluations; compare outcome metrics, not cross-contract returns.
