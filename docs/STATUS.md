# Project status

Updated 2026-10-24 (Europe/Amsterdam). Current state only; dated evidence is history.
The pre-refactor STATUS is preserved in `archive/docs/STATUS.pre-pure.md`.

## Direction

- Pure self-learning since 2026-10-22 ([decision](UPDATE_DECISION.md)). RecurrentPPO
  learns from raw facts and outcome rewards only: no scripted setup, advice features
  or technique rewards. Archive content is history, not runtime authority.
- Current native lineage: `pure-v4`, observation schema 5, reward contract `pure-v7`; one-hour native qualification passed. The reward-v5 trial is preserved separately as `runs/pure-v4-pre`; it is not resumed.
- Active changes (not archived):
  - `random-prior-eval-baseline`: Windows gate passed; native one-hour task 2.2
    pending. Move/shoot uniform, use none 0.85, other uses 0.05 each.
  - `stagnation-cost-reward-v7`: Windows gate and one-hour native task 2.2 passed;
    [qualification report](../reports/2026-10-24-pure-v7-one-hour.md). Eight-hour acceptance 2.3 remains open.
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
- Reward: `configs/reward-v7.yaml`, semantic contract `pure-v7`: v6 (v5 coefficients
  plus kill credit) with lost half-heart -0.5, stall -5 once without death and a
  stagnation cost -0.1 per idle second past 20 s (episode stagnation cap -7.0 plus stall -5).
  Enemy damage 5, first clear 10, first room 3, new collectible 2, death -10.
  The generic manifest reward_schema_version=1 is separate from reward_contract.
- Episode = run. Death terminates; 90 active seconds without run-new progress
  truncates and restarts. Revisited rooms/regained counters do not reset progress.
- `configs/training-pure-v4.yaml`: gamma 0.998, gae_lambda 0.98, ent_coef 0.005, seed 1;
  contract hash
  `d62dc21baf19941b0484e857f2124e8fbffb3d564ab9763a2e13619230c63bc4`
  (reward v6: `ed954e0a...`). Observation 5/action 2/reward contract pure-v7 must match. Earlier contracts refused.
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
  migration; old checkpoints are incompatible with pure-v7.
- Reward-v6 pure-v4 run (initialized at source 7be28a4): qualification, a 3 h 28 m
  continuation and a 12-hour night run ended cleanly at ed954e0a-s1-t237568
  (445 night episodes, 51 clears, stage 2 never reached; stall share rose 48% ->
  65%). Its directory is preserved as `runs/pure-v4-reward-v6`. Training is stopped
  and stop.forever remains. [Night analysis](../reports/2026-10-24-pure-v4-overnight.md).

## Verification

- Current Windows gate: 1242 tests passed with Lua, no skips; mypy 31 files,
  lint/format/pip clean, strict OpenSpec 19/19. Synthetic CPU smoke passed:
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

1. Reward-v7 four-hour continuation completed cleanly at d62dc21b-s1-t74240:
   158 episodes, 58.2% stalls, 80.4% start-room exits, damage fraction 1.5760,
   173 kills, 21 clears; [hourly report](../reports/2026-10-24-pure-v7-four-hour.md).
   User authorized continuation from t74240 until 2026-10-25 09:00 Europe/Amsterdam
   (08:00 UTC, after DST), unchanged configs; verify the eight-hour lease rollover.
   After clean training shutdown, evaluate latest then random-prior for one hour each,
   compare with historical random/t102400, write the night report and remain stopped.
2. Why v7: the [frozen evaluation](../reports/2026-10-24-pure-v4-frozen-eval.md)
   (t102400/t204800/t237568/random, 34/38/40/34 episodes) showed no checkpoint
   better than random: stall share 62/74/53% vs 41%, damage fraction 1.93/0.51/1.46
   vs 1.70, all on stage 1. Acceptance after 8 h: stall share below 41% and damage
   fraction at least 1.70.
3. STOP_MARGIN_SECONDS=15 produced clean one-hour deadlines; native eight-hour
   rollover is untested. Evaluation display can stay waiting after a long episode
   (record separately). Dashboard views passed the offline gate, interactive
   acceptance was not run.
4. Keep old lineages and pure-v4-pre preserved. Generic player_damaged event sources
   are hardcoded enemy; use native hits_* counters for source aggregates.

## Navigation

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[RL design](RL_DESIGN.md) | [Architecture](ARCHITECTURE.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Archive](../archive/README.md)
