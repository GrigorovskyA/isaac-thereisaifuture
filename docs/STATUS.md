# Project status

Updated 2026-10-24 (Europe/Amsterdam). Current state only; dated evidence is history.
The pre-refactor STATUS is preserved in `archive/docs/STATUS.pre-pure.md`.

## Direction

- Pure self-learning since 2026-10-22 ([decision](UPDATE_DECISION.md)). RecurrentPPO
  learns from raw facts and outcome rewards only: no scripted setup, advice features
  or technique rewards. Archive content is history, not runtime authority.
- Current native lineage: `pure-v4`, observation schema 5, reward contract `pure-v6`.
  The reward-v5 trial is preserved separately as `runs/pure-v4-pre`; it is not resumed.
- Active changes, complete but unarchived:
  - `frozen-checkpoint-evaluation`: Windows gate and native task 2.2 passed, four
    hourly comparisons completed; [results](../reports/2026-10-24-pure-v4-frozen-eval.md).
  - `pure-v4-map-hazards-and-stall`: all GRID_WALL excluded, typed obstacles,
    room shape/minimap/stall clock, kill/hit metrics and training timings.
    Windows gate, deployment and bounded native task 2.3 passed after the wall fix.
  - `kill-credit-reward-v6`: last-16 oracle kill ids pay remaining enemy HP once;
    full-HP native kill paid, with no killed-but-zero-damage completed rows.
    Windows task 2.2 and native task 2.3 passed.
  - `stall-watchdog-novel-progress`: run-new facts reset the watchdog; native
    acceptance passed in the [15-hour run](../reports/2026-10-23-pure-v3-overnight.md).
  - `pure-v3-observation-and-control`: bounded native task 2.3 passed; superseded.
- Current [Windows and native evidence](../reports/2026-10-23-pure-v6-native-acceptance.md).
  Earlier [wall-failure report](../reports/2026-10-23-pure-v4-native-acceptance.md)
  and [reward-v5 one-hour analysis](../reports/2026-10-23-pure-v4-one-hour.md)
  explain the fixes; their old runtime state is historical.

## Contracts

- Observation 5: 3499 floats, room shape, 24 typed obstacles, 13x13 minimap and
  stall fraction. All GRID_WALL cells excluded, including narrow/irregular rooms;
  fireplaces are fire. Transport cap 48 KiB. Hidden HP, kill ids/counters and hit
  sources stay in the oracle, outside the policy/normalizer/recurrent state.
- Action 2: MultiDiscrete([5,5,4]), held for six updates (0.2 s). Use none/bomb/
  active/pill-card; fresh use-head prior P(none)=0.85. Requested use is not proof
  of a visible effect.
- Reward: `configs/reward-v6.yaml`, semantic contract `pure-v6`, v5 coefficients
  plus remaining-HP kill credit. Enemy damage 5, first clear 10, first room 3,
  new collectible 2, lost half-heart -1, death -10, stall -10 once without death.
  The generic manifest reward_schema_version=1 is separate from reward_contract.
- Episode = run. Death terminates; 90 active seconds without run-new progress
  truncates and restarts. Revisited rooms/regained counters do not reset progress.
- `configs/training-pure-v4.yaml`: gamma 0.998, gae_lambda 0.98, ent_coef 0.005, seed 1;
  contract hash
  `ed954e0a5f2b064fc11634396f612bae4497fa4d2bddda5d6e16914ca67fe792`.
  Observation 5/action 2/reward contract pure-v6 must match. Earlier contracts refused.
- Supervisor: `Start-Pure.cmd`, `runs/pure-v4`, unlimited death/stall New Runs,
  five consecutive faults maximum, disk cap 20,480,000,000 bytes; session lease
  28740 seconds. A timer-owned stop.forever bounds the authorized continuation.
- `Start-Dashboard.cmd`: read-only runs/pure-v4 at http://127.0.0.1:8765.
  Episodes include enemies_killed/hits_*; train.csv includes rollout/update seconds.

## Lineage

- pure-v1 (reward v2), pure-v2 (reward v3), pure-v3 (reward v4) remain preserved and
  stopped. Do not resume them. Pure-v3 final checkpoint: 03b9c5e3-s1-t257024;
  [gamma-test report](../reports/2026-10-23-pure-v3-gamma-test.md).
- Reward-v5 pure-v4 trial: final 9aab0d2d-s1-t18432, preserved in runs/pure-v4-pre.
  It showed uncredited one-shot kills and narrow-room walls. No deletion or model
  migration; old checkpoints are incompatible with pure-v6.
- Fresh reward-v6 pure-v4 initialized once at source 7be28a4 after preserving the
  trial. Qualification ended at ed954e0a-s1-t3072: six saved rollout checkpoints,
  nine complete episodes (six deaths, three stalls), nine kills, two clears.
  A tenth episode was interrupted; partial rollout work is not in the saved model.
  Model and normalizer loaded successfully and produced a valid recorded-frame action.
- Qualification ended cleanly at 16:38:10 CEST: learner_exit=0, fault=null,
  cleanup_errors=[], no owned game/learner/supervisor/listener/approval remained.
  All 815 tracked files stayed unchanged throughout the native session.
- The planned four-hour continuation was stopped early by the user after 3 h 28 m
  44 s, at ed954e0a-s1-t55808 (20:11:46 CEST). Result: user_cancelled,
  learner_exit=0, fault=null, cleanup_errors=[]; Isaac/supervisor/learner stopped.
  Completed episode rows in UTC hours 14-17 confirm: stall share 0.39/0.58/0.70/0.81,
  death share 0.61 -> 0.19, damage fraction about 1.0-1.3 -> 0.57. One-shot kills
  are credited; no completed episodes with kills > 0 and zero damage.
  The rising stall share motivates the night-run hyperparameter change, not a
  contract/reward/model reset: gamma 0.995 -> 0.998, gae_lambda 0.95 -> 0.98.

- The 12-hour night run ended by timer at 08:16:39 CEST on 24 October:
  t55808 -> t237568 (+181760 saved steps, 355 rollout/checkpoint rows), 445 complete
  episodes, 335 kills, 51 clears. Final model/normalizer load passed. Both learner
  exits were 0 and cleanup_errors empty; all 816 tracked files stayed frozen.
  Eight-hour rollover recorded one transport/budget fault, then resumed t176128;
  final session fault=null. Training is stopped and stop.forever remains.
- [Night analysis](../reports/2026-10-24-pure-v4-overnight.md): versus the preceding
  118-episode continuation, stalls 67.8% -> 60.7%, damage 0.834 -> 1.032, kills
  0.551 -> 0.753 per episode; clears nearly flat (0.110 -> 0.115), stage 2 never
  reached. First/last three-hour blocks: stalls 48.3% -> 65.4%, exits 80.8% -> 66.3%.
  Partial combat recovery, no sustained progression breakthrough. No kills/zero-damage
  completed rows; bomb requests 5.26%, 23 fast deaths within 70 steps. Approximate
  oracle-progress replay found no gap over two minutes in 443 fresh-run episodes.

## Verification

- Current Windows gate: 1215 tests passed with Lua, no skips; mypy 31 files,
  lint/format/pip clean, strict OpenSpec 17/17. Synthetic CPU smoke passed:
  16 steps, 3499 inputs, [5,5,4] actions. Synthetic smoke is not gameplay evidence.
- Closed-game deployment hashes matched source and user-provided values:
  Lua 5e9352154a38ea4ad6b6d219d463993493cb676ba432f04fd2f3372853470315,
  metadata 00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997.
- Native narrow shape 3 and L shape 12 exported no wall; rocks/bomb rocks retained.
  Fire observed; both nonlethal damage and kills reset stall clock. Full-HP kill
  credited 10 HP once; all five complete episodes with kills have positive damage.
  No overpaid identity in the recorded sample. Death and stall New Runs verified.
- Scope limits: unencountered hazard variants, arbitrary weapons/tear flags and
  heavy snapshot load were not revalidated. This is self-review, not independent
  review, and the sample does not establish improved play against a baseline.

## Next

1. Training remains stopped at ed954e0a-s1-t237568; stop.forever is retained.
   Do not resume or initialize. Reward pure-v6 and stall 90 s remain unchanged.
2. [Frozen evaluation](../reports/2026-10-24-pure-v4-frozen-eval.md) passed:
   t102400/t204800/t237568/random have 34/38/40/34 complete episodes, all completed,
   exits 0, no faults/cleanup errors in those sessions; training root byte-identical.
   Two earlier t237568 focus refusals with zero episodes are preserved separately.
3. Comparison damage/episode: 1.931/0.511/1.464/1.702; clears total: 7/2/9/7.
   All remain on stage 1. Later checkpoints are not consistently better than early
   or random. The condition for continuing with stall 60 s is not demonstrated;
   wait for the user decision about reward v7 or a further controlled experiment.
4. STOP_MARGIN_SECONDS=15 produced clean completed one-hour deadlines; native
   eight-hour rollover remains untested. Retention keep_every=100 and pre-tuning
   checkpoint pinning passed offline tests, with no training save/prune during eval.
5. Evaluation display can remain waiting after a long episode despite new rows;
   record this status-transition issue separately, without altering tested runtime.
   Dashboard views passed the offline gate; interactive acceptance was not run.
6. Keep old lineages/pure-v4-pre preserved. Generic player_damaged event sources
   are hardcoded enemy; use native hits_* counters for source aggregates.

## Navigation

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[RL design](RL_DESIGN.md) | [Architecture](ARCHITECTURE.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Archive](../archive/README.md)
