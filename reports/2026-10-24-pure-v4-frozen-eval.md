# Evidence: pure-v4 frozen checkpoint evaluation

- Date/time: 2026-10-24, Europe/Amsterdam (CEST, UTC+02:00).
- Tested implementation revision: `8a12877` on top of `2eccd69`, pushed with the
  requested implementation commit before any native evaluation.
- Scope: four sequential frozen evaluations, no training or model/config tuning.
- Stack: native Windows, project Python 3.12, Steam Repentance+ v1.9.7.17,
  first-party observer 0.5.0-dev, RecurrentPPO checkpoints / uniform RandomPolicy.
- Observation 5 (3499 floats), action 2 [5,5,4], repeat 6, reward contract pure-v6,
  stall 90 seconds. Policy sampling seed 1; checkpoint sampling is stochastic,
  with frozen saved observation normalization and recurrent reset per episode.
- Contract hash: `ed954e0a5f2b064fc11634396f612bae4497fa4d2bddda5d6e16914ca67fe792`.
- Budget: 3600 seconds per session; supervisor stop margin 15 seconds,
  20,480,000,000-byte disk cap each, unlimited death/stall New Runs within the lease,
  existing five-consecutive-fault env cap. Guard refusals stop the batch.
- Local evidence: `reports/local/pure-v4-frozen-eval-20261024/`; native successful
  sessions: `runs/pure-v4-eval/_sessions/<label>/`, episodes under each eval root.

## Results

| Requirement | Command/scenario | Exit | Status | Evidence |
|---|---|---|---|---|
| Windows gate with Lua | scripts/Check.ps1 | 0 | passed | check.log: 1215 passed, no skips; lint/format/mypy/pip clean, strict OpenSpec 17/17 |
| Four native policies | Start-Eval.cmd with 3600 seconds, sequentially | learner 0 each | passed | All four result.json files completed, fault null, cleanup_errors=[] |
| No learning | Native evaluation events / files | n/a | passed | No training or checkpoint events, no train.csv or checkpoint directory in eval roots |
| Protected training lineage | Before/after SHA256 tree snapshots, including directories | 0 | passed | All 77 files under runs/pure-v4 byte-identical after each successful run and after all runs |
| Tested source / mod unchanged | Hash readback before report edits | 0 | passed | All 825 tracked files and both deployed mod files unchanged |
| Complete episode accounting | CSV versus episode events and evaluation_result | n/a | passed | 34 / 38 / 40 / 34 rows respectively; matching events |
| Offline comparison | Exact compare_eval.py command below | 0 | passed | comparison.txt, comparison.json |
| Final cleanup | Process, port, installed mod and stop-file readback | n/a | passed | No game, learner, supervisor, batch parents or listener 9528; approval absent; training stop.forever retained |
| Two t237568 startup attempts | Foreground guard refused before evaluation | learner 1 each | failed, preserved | Focus refusal and cleanup termination warnings described below; zero episodes |

### Native session results

| Policy | Start CEST | End CEST | Elapsed s | State | Episodes | Learner exit / cleanup |
|---|---|---|---:|---|---:|---|
| t102400 | 2026-10-24 10:29:01 | 2026-10-24 11:28:48 | 3586.265 | completed | 34 | 0 / [] |
| t204800 | 2026-10-24 11:28:50 | 2026-10-24 12:28:37 | 3586.766 | completed | 38 | 0 / [] |
| t237568 | 2026-10-24 12:33:26 | 2026-10-24 13:33:12 | 3586.437 | completed | 40 | 0 / [] |
| random | 2026-10-24 13:33:15 | 2026-10-24 14:33:01 | 3586.188 | completed | 34 | 0 / [] |

Each launcher received exactly 3600 seconds. Actual elapsed time is about 3586 s
because the worker stops 15 s before the lease deadline and then cleans up. This
margin is common to every policy, not a shortened individual retry or a count cap.
The one-hour cooperative deadline stops validate the margin on this duration;
an eight-hour rollover was not performed during this evaluation.

## Real game

Each successful session started with Isaac closed, launched through Steam and
verified guarded Continue on save file 2 plus initial Isaac character identity.
Gameplay used the structured bridge. No primary gameplay input, unlocks, save edits,
training, pinning writes, retention pruning or manual mod deployment occurred.
Checkpoint policies were exact t102400, t204800 and t237568 directories; random
was launched without a checkpoint argument. Expected checkpoint hashes and the
entire training run root were checked, not merely the latest pointer or CSV size.

Commands (game directory and log were the existing native Steam paths):

```powershell
.\Start-Eval.cmd "<game>" "<log.txt>" t102400 3600 "runs\pure-v4\seed-1\checkpoints\ed954e0a-s1-t102400"
.\Start-Eval.cmd "<game>" "<log.txt>" t204800 3600 "runs\pure-v4\seed-1\checkpoints\ed954e0a-s1-t204800"
.\Start-Eval.cmd "<game>" "<log.txt>" t237568 3600 "runs\pure-v4\seed-1\checkpoints\ed954e0a-s1-t237568"
.\Start-Eval.cmd "<game>" "<log.txt>" random 3600
```

### Preserved startup failures

The first t237568 launch at 12:28:47 CEST failed after 26.125 s because Isaac was
not foreground. The user reported accidentally selecting another window. A
subsequent launch at 12:31:56 failed after 25.141 s for the same foreground guard.
Both attempts wrote zero episodes and never reached the evaluation event.
The failed results record learner_exit=1 and a cleanup warning that the owned
worker required termination, so cooperative release was unverified. These are
failed attempts, not clean successful sessions. Subsequent readback found no
remaining game/worker/listener/approval, and the training tree remained identical.

Failed runtime roots and complete result files were preserved without deletion:

- `runs/pure-v4-eval/_failed/t237568-focus-20261024-122847/{run,session}`.
- `runs/pure-v4-eval/_failed/t237568-focus-20261024-123156/{run,session}`.

After the user explicitly answered ready to keep Isaac foreground, the complete
3600-second t237568 session was restarted through the same guard and passed.
Random started only after that successful session and its immutability checks.
The two startup failures are excluded from episode denominators, not concealed
as successful eval runs. First/second batch-state receipts and failed console
logs remain in the local evidence folder. Total calendar span includes these
startup interruptions; each successful policy still received the same budget.

## RL evaluation

### Comparison produced by the requested command

```powershell
.venv\Scripts\python.exe scripts\compare_eval.py runs\pure-v4-eval\t102400 runs\pure-v4-eval\t204800 runs\pure-v4-eval\t237568 runs\pure-v4-eval\random
```

```text
label    episodes  death  stall  left_room  damage  damage_se  kills  rooms_cleared  any_clear  hp_lost  return  max_stage  stall_lo  stall_hi
t102400  34        0.382  0.618  0.706      1.931   0.467      1.588  0.206          0.206      3.353    1.705   1.000      0.450     0.761
t204800  38        0.263  0.737  0.447      0.511   0.137      0.263  0.053          0.053      2.316    -7.388  1.000      0.580     0.850
t237568  40        0.475  0.525  0.700      1.464   0.298      1.150  0.225          0.225      3.300    -0.314  1.000      0.375     0.671
random   34        0.588  0.412  0.824      1.702   0.341      1.294  0.206          0.147      4.176    0.626   1.000      0.264     0.578
```

Damage is credited enemy HP / enemy maximum HP, summed per completed episode.
damage_se is sample SD / sqrt(N); stall_lo/hi are the 95% Wilson interval. All
shares use completed episodes. A deadline-interrupted final episode is excluded.
Lower death share alone is not evidence of better play if the alternative is stall.

### Decision-facing summary

| Policy | Kills total | Clears total | Damage/episode | Kills/episode | Clears/episode | Stall | Left start |
|---|---:|---:|---:|---:|---:|---:|---:|
| t102400 | 54 | 7 | 1.931 | 1.588 | 0.206 | 61.8% | 70.6% |
| t204800 | 10 | 2 | 0.511 | 0.263 | 0.053 | 73.7% | 44.7% |
| t237568 | 46 | 9 | 1.464 | 1.150 | 0.225 | 52.5% | 70.0% |
| random | 44 | 7 | 1.702 | 1.294 | 0.206 | 41.2% | 82.4% |

**The requested condition is not demonstrated: later checkpoints are not
consistently better than the early checkpoint and random.**

- t204800 is worse on the main point estimates: damage 0.511 vs 1.931 (early)
  and 1.702 (random), only two clears, 73.7% stall and 44.7% start-room exits.
- t237568 recovers relative to t204800, but damage 1.464 and kills 1.150 are below
  both early (1.931 / 1.588) and random (1.702 / 1.294). Its nine clears versus seven
  each for early/random are a small positive counterpoint, not a broad advantage.
- All policies remain on stage 1. No stage-2 or win/progression evidence appeared.
- The late-minus-random damage difference is -0.238; its exploratory normal
  95% interval using sqrt(SE_late^2 + SE_random^2) is about [-1.126, 0.649].
  This does not establish superiority or equivalence. The same exploratory interval
  for early minus random is [-0.904, 1.362]; early is not proven superior either.
- Excluding each initial Continue episode preserves this picture: damage means
  1.896 / 0.524 / 1.501 / 1.697, kills 1.606 / 0.270 / 1.179 / 1.303.

Under the user's proposed branching rule, these results do not justify the
"continue training with stall 60 s" branch. Reward v7 is a candidate for the next
discussion, not a change implemented here. Training remains stopped pending the
user's decision; stall_seconds remains 90, and reward/contract stay pure-v6.

## Limitations and continuation

- One fixed policy-sampling seed per variant, roughly one hour each, unpaired
  procedurally generated game runs. No causal or monotonic-learning conclusion
  follows from checkpoint age alone. The two damaged startup attempts had no
  measured policy episodes; first-episode Continue state is a remaining comparison
  limitation, addressed only by the descriptive exclusion check above.
- Wilson/SE estimates are descriptive small-sample summaries. No formal
  preregistered ranking, multi-seed test or multiple-comparison correction was run.
  The data do not satisfy ROADMAP P2 evidence of a clear learned-policy advantage.
- Status-display finding: after a long episode, progress can remain `waiting`
  while new evaluation episodes arrive. Progress.event refreshes last_activity
  for episode events but does not transition waiting back to evaluating. This
  display limitation did not stop any policy or alter completed-state classification.
  Runtime source was left frozen; the issue is recorded for a separate correction.
- Retention pinning and dashboard learning views passed the offline gate; no
  training saves/pruning or interactive dashboard acceptance was performed here.
- Self-review checked requirement coverage against tests, eval identities, episode
  accounting, checkpoint/source hashes, deadlines and cleanup. This is not an
  independent review. OpenSpec task 2.2 is complete for the requested retained
  checkpoints and random; no change was archived.

Next action is a user decision. No training, reward-v7 implementation, 60-second
watchdog change or additional evaluation has been started.
