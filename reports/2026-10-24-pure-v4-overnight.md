# Evidence: pure-v4 12-hour night analysis (gamma 0.998, GAE 0.98)

- Date: 2026-10-24, Europe/Amsterdam (CEST, UTC+02:00). Offline analysis on Windows.
- Source revision: `c6e3e82`; only unrelated untracked `tools/` before analysis.
- Scope: assess the completed night run; no gameplay, restart, training/config/mod edits.
- Native game: Repentance+ v1.9.7.17, save file 2, observer 0.5.0-dev; Python 3.12,
  RecurrentPPO, observation 5 / action 2 / semantic reward contract `pure-v6`.
- Seed 1; gamma 0.998, gae_lambda 0.98, ent_coef 0.005. Contract hash unchanged:
  `ed954e0a5f2b064fc11634396f612bae4497fa4d2bddda5d6e16914ca67fe792`.
- Planned budget: 43200 seconds, disk 20,480,000,000 bytes, five consecutive faults.
- Evidence/analysis outputs: `reports/local/pure-v4-overnight-analysis-20261024/`.

## Results

| Check | Evidence | Exit | Status |
|---|---|---|---|
| Final timer stop | twelve-hour-timer-fired.json, second result.json | 0 | passed |
| Cleanup | Both learner_exit=0, cleanup_errors=[]; no owned game/learner/supervisor/timer parent or 9528 listener; installed approval absent | 0 | passed |
| Eight-hour transition | First result is fault at its lease deadline; second resumed t176128 | 0 | recovered fault |
| Lineage / hyperparameters | First startup and final manifests agree on pure-v6, gamma .998, GAE .98, entropy .005 | 0 | passed |
| Final model/normalizer load | final-checkpoint-load.json, CheckpointPolicy load and hash verification | 0 | passed |
| Frozen source | 816 tracked hashes match the preflight, before these report edits | 0 | passed |
| Metric consistency | 445 completed CSV rows match 307 + 138 supervisor episode events | 0 | passed |
| Kills with zero damage | 0 of 133 completed episodes containing kills | n/a | passed |
| Controlled improvement vs random/frozen policy | No matched native evaluation in this run | n/a | not_run |

## Real game

The night resumed `ed954e0a-s1-t55808` without initialization. It ran from
23 October 20:16:37.083 to 24 October 08:16:39.209 CEST (12 hours 2.126 seconds
including shutdown). Timer fired at 08:16:37.110; stop.forever remains in place.

| Session | Parent -> latest | Completed episodes | Outcome |
|---|---|---:|---|
| session-20261023-201637-0001 | t55808 -> t176128 | 307 | fault at 04:15:39; learner exit 0, cleanup clean |
| session-20261024-041539-0002 | t176128 -> t237568 | 138 | planned stop at 08:16:39; fault null, exit 0, cleanup clean |

At the first lease deadline, the learner recorded `Peer closed before a complete
record`, then `Live wall-time budget exhausted; unfinished rollout has no new
checkpoint`. The supervisor counted one fault and resumed the saved checkpoint.
This was a successful rollover, but the run was not fault-free. The ordering and
classification of a planned lease expiry deserve a separate engineering review;
the evidence does not identify the exact initiator of the connection closure.

Final checkpoint: `ed954e0a-s1-t237568`, parent t237056. It loaded with its saved
normalizer. Night progress: **181760 saved steps, 355 saved rollout/checkpoint rows**.
There are two uncompleted episode/rollout tails at the boundaries, excluded from
complete-episode denominators. No unbounded retries or disk cap exhaustion occurred.

## RL evaluation

**Conclusion: partial recovery of combat metrics, without a sustained progression
breakthrough.** The overall averages improved versus the preceding session, but
room clears stayed almost flat, stage 2 was never reached, and stalling grew again
after the first three hours. The last quarter recovered some combat and clears.

### Previous session versus the night

Baseline: preceding continuation, 118 complete episodes over 3 h 28 m 44 s,
gamma .995 / GAE .95. Qualification episodes are excluded. Night: 445 episodes,
gamma .998 / GAE .98. Both retain the same reward/model lineage.

| Per completed episode unless stated | Previous session | Night |
|---|---:|---:|
| Stall share | 67.8% | 60.7% |
| Death share | 32.2% | 39.3% |
| Left start room | 65.3% | 69.4% |
| Enemy damage fraction | 0.834 | 1.032 |
| Kills | 0.551 | 0.753 |
| Rooms cleared | 0.110 | 0.115 |
| Episodes with any clear | 10.2% | 10.6% |
| Half-hearts lost | 2.99 | 3.23 |
| Bomb requests / selected actions | 4.3% | 5.3% |
| Mean return | -4.95 | -3.91 |
| Highest stage | 1 | 1 |

Damage fraction is the sum of credited HP / enemy maximum HP, not DPS or raw HP.
Request shares describe selected actions, not successful presses or explosions.
Night totals: **175 deaths, 270 stalls, 335 kills, 51 room clears**. 57.1% of episodes still deal no damage (median damage is zero; 42.9% deal any damage).

### Trend in three-hour blocks

| Hours since start | N | Stall | Exit start | Damage | Kills | Clears | Bomb requests |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0-3 | 120 | 48.3% | 80.8% | 1.348 | 0.975 | 0.108 | 5.5% |
| 3-6 | 116 | 60.3% | 69.0% | 0.887 | 0.578 | 0.086 | 4.3% |
| 6-9 | 105 | 70.5% | 60.0% | 0.717 | 0.495 | 0.105 | 6.2% |
| 9-12 | 104 | 65.4% | 66.3% | 1.148 | 0.952 | 0.163 | 5.0% |

First-to-last block: stalls 48.3% -> 65.4%, start exits 80.8% -> 66.3%, damage
1.348 -> 1.148. Clears rise 0.108 -> 0.163 in the final block, but with only
17 clears / 104 episodes this is not a demonstrated stable improvement.

### Hourly detail

Hours are anchored to 20:16:36 CEST, rather than UTC calendar-hour boundaries.

| Hour | N | Stall | Damage | Kills | Clears | Exit start |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 38 | 52.6% | 1.259 | 0.947 | 0.132 | 78.9% |
| 2 | 42 | 45.2% | 1.143 | 0.762 | 0.071 | 83.3% |
| 3 | 40 | 47.5% | 1.648 | 1.225 | 0.125 | 80.0% |
| 4 | 40 | 50.0% | 1.270 | 0.800 | 0.050 | 80.0% |
| 5 | 38 | 60.5% | 0.557 | 0.342 | 0.079 | 68.4% |
| 6 | 38 | 71.1% | 0.814 | 0.579 | 0.132 | 57.9% |
| 7 | 36 | 72.2% | 0.756 | 0.444 | 0.083 | 63.9% |
| 8 | 35 | 74.3% | 0.426 | 0.257 | 0.086 | 51.4% |
| 9 | 34 | 64.7% | 0.976 | 0.794 | 0.147 | 64.7% |
| 10 | 39 | 56.4% | 0.867 | 0.538 | 0.103 | 66.7% |
| 11 | 29 | 75.9% | 1.642 | 1.586 | 0.276 | 55.2% |
| 12 | 36 | 66.7% | 1.055 | 0.889 | 0.139 | 75.0% |

### Stall watchdog and long runs

Median episode duration: 96.1 game-update seconds. Eighteen episodes exceed
180 game-update seconds; maximum 350.5 s. A long *run* is not proof of long
*progress-free* time: new rooms, HP damage, clears and new items reset the clock.

Replaying RunProgress over logged oracle events for 443 fresh-run episodes
(initial Continue episodes excluded), using room 84, counters 0/1/0 and frame 6
as initial assumptions, gives a maximum gap of about **107.5 game-update seconds**
between novel-progress events or episode end; none exceed 120 or 180 seconds.
These frame-based gaps do not reconstruct the watchdog active wall clock, pauses
or transport gaps, so this is supporting evidence rather than an exact idle trace.

The three longest runs have the following final progress-to-stop gaps:

| Second-session episode | Total game seconds | Last new progress | Tail game seconds, approximate |
|---|---:|---|---:|
| 93 | 350.5 | Room clear, frame 7816; nine kills in the run | 89.9 |
| 99 | 344.4 | New collectible, frame 7637; two clears | 89.8 |
| 66 | 291.7 | New collectible, frame 6053; zero enemies | 89.9 |

Episode 66 later revisits known rooms at frames 8487/8504; these do not reset
RunProgress. This directly addresses the former known-room cycling concern.

### Bombs and fast deaths

- Bomb request share increased overall: 4.34% -> **5.26%**; three-hour shares
  5.51%, 4.31%, 6.15%, 5.04%. There is no monotonic disappearance of bomb requests.
- Own-bomb hit counter: **198 / 1165 total recorded hit events (17.0%)**.
  80 / 175 death episodes include an own-bomb hit; inclusion does not establish
  the fatal blow or intentional use. Baseline: 54 hits, 19 / 38 death episodes.
- **23 / 175 deaths (13.1%)** occur within 70 steps, range 9-70, median 57.
  Thirteen are in hours 1-3, six in 4-6, four in 7-9, none in 10-12.
  All have positive spawned-enemy counts. Six include an own-bomb hit, twenty
  enemy hits, five spike hits and two fire hits; categories overlap.
- For those 23 episodes, oracle health-loss amounts total six half-hearts each
  in their own game epoch, followed by a death event. This is consistent with
  fresh-run health being lost, rather than a zero-health old run being counted
  immediately as another death. It is not a substitute for a continuous video.
- Important instrumentation limit: `live.py` EventDeriver emits every health-loss
  oracle_event with `damage_source="enemy"` regardless of actual source. Native
  CSV `hits_*` counters are more specific. Therefore the event label cannot be
  used to identify what caused a fast death; per-step native source timing is absent.

### Optimizer / policy

- Entropy estimate from `-entropy_loss`, first/last 10 rollout rows: **3.35 -> 3.70**
  (maximum for [5,5,4] is ln(100), about 4.61). No late entropy collapse is evident.
- Explained variance first/last 10: **0.21 -> 0.71**. Better value fit is not
  evidence of better room completion.
- Mean update time 8.50 s, rollout 112.63 s. Recorded update time totals about
  3001 s (6.95% of the 12-hour budget); the first row after each resume has an
  empty previous-update timing, so this total is slightly incomplete.
- Mean return: stall -5.07, death -2.12. Undiscounted episode return alone does
  not reveal the policy advantage targets; changing gamma/GAE did not remove
  the observed tendency to stall. Both hyperparameters changed together.

## Limitations and continuation

One learner seed, procedurally different native runs and a continually changing
policy: this is an observational before/after comparison, not a controlled causal
test of gamma or GAE. The UTC 14-17 numbers from the previous handoff are not
reused as the baseline denominator; only its actual continuation rows are used.
Unfinished boundary episodes are excluded, not counted as deaths or stalls.

The final model is preserved and training remains stopped. No hyperparameters
were changed by this analysis. A useful next measurement is a bounded frozen-policy
comparison of the retained t102400, t204800 and t237568 checkpoints under the same
evaluation protocol, including a random-policy baseline; the ROADMAP P2 comparison
has not been performed here. This is a proposed experiment, not an authorized launch.
Keep the rollover fault-classification issue separate from gameplay tuning.

Analysis was self-reviewed against episode CSV, supervisor events, native oracle
events and manifests; it is not independent review. Docs-only checks are used;
the full RL suite is not rerun for an analysis report. Historical gate evidence
for unchanged runtime source remains 1185 tests with Lua and strict specs 16/16.
