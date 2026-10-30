# Project status

Updated 2026-10-30 (Europe/Amsterdam). Current state only; dated evidence is history.
The pre-refactor STATUS is preserved in `archive/docs/STATUS.pre-pure.md`.

## Direction

- Pure self-learning since 2026-10-22 ([decision](UPDATE_DECISION.md)). RecurrentPPO
  learns from raw facts and outcome rewards, plus one potential-based door term since
  reward v9: no scripted setup, advice features or technique rewards. Archive content is history, not runtime authority.
- Held live-status writes now skip a publication after the bounded Windows sharing
  retry instead of faulting training; `result.json` remains strict. The terminal
  result records `status_writes_skipped` for skipped live publications.
  October 30 Check.ps1 passed: 1075 tests, 10 Lua module skips (isolated runtime
  unavailable), strict OpenSpec 25/25; existing synthetic All-NaN warning.
  Training remains stopped. Reward v10 is being prepared as a separate fresh lineage;
  no initialization, new branch or training launch is part of this repair.
- Train-statistics logger repair `fc80cd5` passed native recording: all nine statistics
  populated in 69/69 new rows; pause_ok 69/69, first hour 15/15. Check1428/Lua/no skips;
  strict 25/25. Contract/mod/config unchanged; live pause remains enabled.
  Finite continuation from t31744 stopped early October 29 at 21:29:25 CET on a
  Windows access-denied status-file replacement fault, final `b26db425-s1-t102400`.
  First learner exit 0/cleanup empty; automatic supervisor startup of a second session
  made no progress and required worker termination (exit 1; release unverified).
  No game/worker/owner/listener remains; stop.forever present. No manual retry.
  [Final statistics, gameplay windows and stall report](../reports/2026-10-30-schema8-train-statistics.md).
  [Finite plan](../reports/2026-10-29-train-statistics-resume-plan.md).
  Prior pause qualification passed15/15; historical early-stop integrity discrepancy
  remains in its [report](../reports/2026-10-31-schema8-focus-training.md).
- Previous trained native lineage: `runs/pure-v4-reward-v9-schema7`, observation schema 7, reward contract `pure-v9`.
  One-hour qualification ended cleanly October 28 at 19:33 CET, checkpoint t13824.
  Measured geometry/door checks passed. User stopped continuation October 29 at 10:36 CET
  at `3cb9d928-s1-t204800`; stop.forever remains, all processes/listener/approval cleared.
  One recovered command timeout remains in the final fault field; learner exit 0, cleanup empty.
  [Final report](../reports/2026-10-30-pure-v9-schema7-training.md).
  [Schema 7 qualification](../reports/2026-10-28-pure-v9-schema7-qualification.md).
  The schema 6 qualification hour (`82b1b53e-s1-t13824`) found
  that its visited-cell grid cut every tile in half; schema 7 counts tiles from the room corner
  (60, 140) and that hour is not resumed.
  The reward-v8 run stopped at `fb22b342-s1-t588288` and is preserved as
  `runs/pure-v4-reward-v8`. The reward-v7 run is preserved as `runs/pure-v4-reward-v7`. The reward-v5 trial is preserved separately as
  `runs/pure-v4-pre`; it is not resumed.
- Active changes (not archived):
  - `rich-room-observation-v8`: door facts per slot (exists, open, locked, target room class,
    target visited), 11 room classes on doors and minimap, trapdoor/crawlspace/pressure
    plate/lock block/teleporter grid classes, `interactable` kind (slot machines, beggars,
    blood donation, fortune teller, restock box, crane, heaven door), enemy identity (64-bucket
    type/variant one-hot, boss, champion, flying, invulnerable, max HP), caps enemy 32,
    projectile 64, obstacle 64, pickup 24, own attack 48, bomb 8, interactable 16, transport
    cap 128 KiB, per-kind `max_*`/`overflow_*` and `enemy_kinds` episode metrics. 9762 floats.
    Offline gate passed; several Isaac API names are unverified natively (task 2.2).
  - `paused-updates-and-input-projection`: shared Linear(obs, 512) + ReLU before the LSTMs
    (one update 55 s -> 7 s at 9762 inputs and 1024 steps, local benchmark), n_steps 1024,
    batch 256, Esc pause around each update (`live.pause_during_updates`), `pause_seconds`
    and `pause_ok` in train.csv. Offline gate passed; native hour open.
  - `dense-exploration-reward-v9`: denser exploration and run-goal rewards (novelty 0.1,
    new room 5, new floor 30, boss clear +20, pickups up), potential-based door shaping
    (coefficient 2, clear rooms only) from new oracle `doors`, and a 26x14 visited-cell map
    in observation schema 7. Schema 6 passed the Windows gate, door reward and snapshot size
    natively, but its grid check failed; schema 7 now passes geometry (49/13148 doorway samples outside).
    Task 2.2 remains open for the native boss positive case; 2.3 remains open. [Qualification report](../reports/2026-10-29-pure-v9-training.md).
  - `short-stall-reward-v8`: stall limit 40 s (was 90), stagnation -0.25 per idle second
    past 12 s, cap still -7.0. Windows task 2.2 passed; t270336 passed the kills/clears
    conditions, the stalled-step condition did not; superseded by reward v9.
  - `observer-frame-timing`: the observer logs an `Observer perf` line every ~10 s
    (callback, capture and encode time); `scripts/lua_perf.py` summarizes log.txt.
    Deployed; native task 2.2 passed ([report](../reports/2026-10-26-pure-v8-one-hour-and-frame-timing.md)).
  - `random-prior-eval-baseline`: Windows gate and native one-hour task 2.2 passed. Move/shoot uniform, use none 0.85, other uses 0.05 each.
  - `stagnation-cost-reward-v7`: Windows gate and one-hour native task 2.2 passed;
    [qualification report](../reports/2026-10-24-pure-v7-one-hour.md). Acceptance 2.3 not
    passed ([t477184 report](../reports/2026-10-26-pure-v7-t477184-eval-and-timing.md));
    superseded by reward v8.
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
- Reward: `configs/reward-v9.yaml`, semantic contract `pure-v9`: lost half-heart -0.5,
  stall -5 once without death, stagnation -0.25 per idle second past 12 s (cap -7.0),
  death -10; enemy damage 5, first clear 10 (+20 for a boss room), first room 5, first
  floor 30, novelty 0.1 per new 40 px cell, coin 0.3, bomb/key 0.5 (run cap 10), new
  collectible 5; door shaping gamma * Phi(s') - Phi(s), Phi = -2 * distance to the nearest
  open door into an unexplored room / room diagonal, in clear rooms only.
  The generic manifest reward_schema_version=1 is separate from reward_contract.
- Episode = run. Death terminates; 40 active seconds without run-new progress
  truncates and restarts. Revisited rooms/regained counters do not reset progress.
- Observation 7: schema 5 plus a 26x14 map of the 40 px floor tiles visited in the current
  room this run, counted from the room corner (60, 140) (3863 floats). Oracle `doors` (slot, position, open, unexplored) is reward-only.
- `configs/training-pure-v4.yaml`: gamma 0.998, gae_lambda 0.98, ent_coef 0.005, seed 1;
  contract hash
  `b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de`
  (archived schema 7: `3cb9d928...`, schema 6 hour: `82b1b53e...`, reward v8: `fb22b342...`, reward v7: `d62dc21b...`, reward v6: `ed954e0a...`).
  Observation 8 (9762 floats)/action 2/reward contract pure-v9 must match; features_dim 512,
  n_steps 1024, batch_size 256. Earlier contracts refused.
- Supervisor: `Start-Pure.cmd`, `runs/pure-v4`, unlimited death/stall New Runs,
  five consecutive faults maximum, disk cap 20,480,000,000 bytes; session lease
  28740 seconds. A timer-owned stop.forever bounds the authorized continuation.
- `Start-Dashboard.cmd`: read-only runs/pure-v4 at http://127.0.0.1:8765.
  Episodes include enemies_killed/hits_*; train.csv includes rollout/update seconds and
  bridge timing (game wait, commands, snapshots per step).

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
- Reward-v7 pure-v4 run: about 33 h to d62dc21b-s1-t492032. Training rates stayed at
  random level; 69% of episodes stalled and 82% of steps were in stalled episodes.
  t477184 over two frozen sessions: kills_1k -1.01 [-2.38, +0.28] against random-prior.
  Two random-prior sessions differ by 0.88 kills_1k. Bridge timing: 92% of rollout time
  is waiting for game snapshots (the game runs ~32 updates/s), 5% commands, 3% Python.
  [Report](../reports/2026-10-26-pure-v7-t477184-eval-and-timing.md). To be preserved as
  `runs/pure-v4-reward-v7`.

## Verification

- Previous Windows gate: 1428 tests passed with Lua, no skips; mypy passed,
  lint/format/pip clean, strict OpenSpec 25/25. Synthetic CPU smoke passed:
  16 steps, 9762 inputs, [5,5,4] actions. Synthetic smoke is not gameplay evidence.
- Closed-game deployment hashes matched source:
  Lua 41b78262d4e8a80634a6d9ce0a04e343195601b2dbcf061fdeca46aac4e58985,
  metadata 00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997.
- Native narrow shape 3 and L shape 12 exported no wall; rocks/bomb rocks retained.
  Fire observed; both nonlethal damage and kills reset stall clock. Full-HP kill
  credited 10 HP once; all five complete episodes with kills have positive damage.
  No overpaid identity in the recorded sample. Death and stall New Runs verified.
- Scope limits: unencountered hazard variants, arbitrary weapons/tear flags and
  heavy snapshot load were not revalidated. This is self-review, not independent
  review, and the sample does not establish improved play against a baseline.

## Next

1. Training is stopped after the status-file access fault. Preserve t102400 and all
   evidence; no retry or source fix is part of this task. A separate authorized change
   is needed to investigate status-file contention and the automatic restart/stop race.
2. Schema 7 training is complete and archived with stop.forever and verified checkpoint hashes.
   Schema 6 remains separately stopped in `runs/pure-v4-reward-v9-schema6`.
3. The ent_coef=0.01 trial ended at t588288 on October 28 at the user's request.
   Both legs exited 0 with empty cleanup errors and no fault. stop.forever remains;
   recurring monitoring was deleted and the October 29 deadline is superseded.
   Minimum 40-rollout use_none mean was 0.5313; its 0.40 guard never fired.
   [Combined final report](../reports/2026-10-29-pure-v8-ent001-overnight.md).
4. A bounded two-instance launch probe observed only one persistent game; direct second
   launch exited 53. Four-instance gameplay and shared-learner training remain untested.
   [Probe evidence and current architectural limits](../reports/2026-10-28-isaac-parallel-instance-probe.md).
5. Frozen t270336 evaluation passed kills/clears conditions, but stalled-step share failed;
   task 2.3 remains open. [Evaluation](../reports/2026-10-27-pure-v8-t270336-frozen-eval.md).
6. Before parallel training, establish independent game launch, save/profile handling,
   per-instance bridge ports and process ownership, then a vectorized single learner.
7. STOP_MARGIN_SECONDS=15 produced clean one-hour deadlines; native eight-hour
   rollover succeeded on 2026-10-25; a later recovered fault blocked the following one. Evaluation display can stay waiting after a long episode
   (record separately). Dashboard views passed the offline gate, interactive
   acceptance was not run.
8. Keep old lineages and pure-v4-pre preserved. Generic player_damaged event sources
   are hardcoded enemy; use native hits_* counters for source aggregates.

## Navigation

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[RL design](RL_DESIGN.md) | [Architecture](ARCHITECTURE.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Archive](../archive/README.md)
