# Project status

Updated 2026-10-23 (Europe/Amsterdam). Current state only; dated evidence is history.
The pre-refactor STATUS is preserved in `archive/docs/STATUS.pre-pure.md`.

## Direction

- Pure self-learning since 2026-10-22 ([decision](UPDATE_DECISION.md)). One
  RecurrentPPO lineage learns from scratch and continuously, from raw facts and
  outcome rewards only. No scripted setup, advice features or technique rewards.
  Hinted code, tests, docs and all previously open changes are in `archive/`.
- Active changes:
  - `openspec/changes/pure-v4-map-hazards-and-stall`: observation schema 5 (obstacle
    classes, room shape, minimap, stall clock; 48 KiB messages), reward v5 (stall -10), v6 (kill credit),
    kill and damage-source metrics, `train.csv` timing, lineage `pure-v4`. Tasks 1.1-1.3
    done offline on macOS; Windows gate 2.2 and mod redeploy passed.
    Native check 2.3 remains open: shape-3 perimeter walls are still exported;
    fire and nonlethal enemy-damage clock reset were not exercised
    ([evidence](../reports/2026-10-23-pure-v4-native-acceptance.md)).
  - `openspec/changes/stall-watchdog-novel-progress`: only facts new for the run reset
    the stall watchdog (revisited rooms and regained counters no longer do). 1.1 and
    2.1 done on macOS; Windows gate 2.2 passed (1123 tests with Lua, smoke passed).
    Native check 2.3 passed in the 15-hour run (no long stalls). All tasks done;
    unarchived. No contract change.
  - `openspec/changes/pure-v3-observation-and-control`: observation schema 4, 32 KiB
    messages, action repeat 6, use-head prior, reward v4 and lineage `pure-v3`.
    Tasks 1.1-2.3 passed, including the bounded native check; unarchived (superseded
    by pure-v4).
  - `openspec/changes/reward-v3-and-training-metrics` (1.1-2.2 done; native hours 2.3
    answered by the pure-v2 analysis below, kept open for pure-v3) and
    `openspec/changes/pure-self-learning-v1` (all tasks done; 4.3 closed by the
    [reward-v3 startup report](../reports/2026-10-22-pure-v3-startup.md)).
- [Refactor report](../reports/2026-10-22-pure-self-learning-refactor.md).
- [Windows checks and native acceptance](../reports/2026-10-22-pure-windows-acceptance.md).
- [Schema4 Windows gate and native plan](../reports/2026-10-22-pure-v3-schema4-acceptance.md).
- [pure-v3 15-hour report](../reports/2026-10-23-pure-v3-overnight.md).

## Contracts

- Observation schema 5: 3499 floats (schema 4's 2038 plus obstacle class one-hot 24 x 11,
  room shape 12, minimap 13 x 13 x 7 + off-grid flag, stall clock 1). Oracle `room_index`,
  hidden enemy HP and the kill/hit counters stay out of the policy vector. Messages up to
  48 KiB (Lua and Python).
- Action v2: `MultiDiscrete([5, 5, 4])` (move, shoot, use none/bomb/active/pill-card),
  held for 6 game updates (0.2 s). The use head starts at P(none)=0.85, 0.05 per press
  (fresh model only, never on resume).
- Reward v6: `configs/reward-v6.yaml` = v5 coefficients + kill credit (v5: stall restart -10, once,
  never with death). Other terms: enemy damage 5.0, first clear 10, health -1 per
  half-heart, first room visit 3, new collectible 2.0, novelty 0.02 on first cell visits.
  Exploit tests in `tests/test_reward_v4.py`, v5 term in `tests/test_reward_v5.py`,
  kill credit in `tests/test_kill_credit.py`; v4 and v5 are in `archive/configs/`.
- Episode = run. Death terminates; the stall watchdog (90 active s without
  progress new for the run) truncates and sends a `restart` command.
- Training: `configs/training-pure-v4.yaml` (contract: observation 5, action 2, reward 5,
  action repeat 6, `use_head_initial_none_probability` 0.85; must match the code);
  gamma 0.995, ent_coef 0.005; lineage hash = `contract` only; hyperparameters tunable between sessions; retention 5 newest +
  every 200th rollout.
- Dashboard: `Start-Dashboard.cmd` serves a live read-only view of `runs\pure-v4` at
  http://127.0.0.1:8765; episode CSV rows carry `wall_time`; `metrics/train.csv` has one
  row per update (SB3 statistics, action mix, `rollout_seconds`, `update_seconds`); episode
  rows add `enemies_killed` and `hits_*` by damage source (observer metrics only).
- Supervisor: `Start-Pure.cmd` / `session_runner --forever` (run root `runs\pure-v4`);
  unlimited New Run, consecutive-fault cap 5, disk cap, session-log retention 20.

## Lineage

- `pure-v1` (reward v2): 9 native episodes, about 7k steps; preserved under
  `runs/pure-v1`, not resumed. Superseded because reward v2 paid most for idling:
  stall-restarted episodes without a fight returned +2 to +5.6 (novelty +4 to +6.5),
  while episodes that damaged enemies and died returned -12.6 and -13.3
  ([proposal](../openspec/changes/reward-v3-and-training-metrics/proposal.md)).
- `pure-v2` (reward v3, schema 3, repeat 3): stopped at 18:59 after 58,880 steps
  (115 updates, 32 episodes, about 2 h); latest `d9b93984-s1-t58880`, preserved under
  `runs/pure-v2`, not resumed. Its config is `archive/configs/training-pure-v2.yaml`;
  its checkpoints are refused. Findings
  ([analysis](../reports/2026-10-22-pure-v2-analysis.md)): reward aligned with progress
  (return vs rooms cleared r=0.77; left start room -0.27 vs stayed -6.45; any clear
  +9.13), policy entropy 4.57 -> 3.97 of 4.61, fewer "no move"/"no shoot" choices, but
  bomb presses stayed 0.234-0.238 per step and start-room exits stayed at 50-60%.
  The last two faults came from the game being closed manually.
- `pure-v3` (schema 4, reward v4): stopped after 15 hours plus a one-hour test with
  gamma 0.995 and ent_coef 0.005 ([report](../reports/2026-10-23-pure-v3-gamma-test.md):
  stall share 0.58 -> 0.38, deaths 0.42 -> 0.62, entropy 3.59 -> 3.43, clears flat);
  final checkpoint `03b9c5e3-s1-t257024` (661 episodes, 257k steps), preserved under
  `runs/pure-v3`, not resumed. Its config is `archive/configs/training-pure-v3.yaml`; its
  checkpoints are refused. Findings ([report](../reports/2026-10-23-pure-v3-overnight.md)):
  start-room exits 86-91%, explained variance 0.42, entropy 3.59, but clears flat
  (0.1-0.2 per episode), stage 2 never reached; stalls (-5) returned more than deaths,
  `enemies_killed` was always 0. Causes drove `pure-v4`.
- `pure-v4` (schema 5, reward v5; restarts on v6): initialized once; checkpoint `9aab0d2d-s1-t3584`,
  contract `9aab0d2d22a7f11225ea2392beaddf1b0f71add1167e1fdb83db30128db9592b`.
  Stopped after qualification (six complete episodes, seven saved rollouts, no faults).
  Checkpoint reloaded; cleanup passed. Do not initialize again. Hourly continuation
  was not launched because native geometry acceptance failed.

## Verification

- macOS offline gate for pure-v4 (task 2.1): 1172 passed, 1 skipped, strict OpenSpec
  15/15, RL smoke with 3499 inputs. The two known macOS-only failures are the Windows
  input struct layout and owned worker import.
- Pure-v3 gate facts stay valid for unchanged code: use-head prior, older configs and
  checkpoints refused, collectible 2.0.
- Current Windows gate (schema 5): 1175 tests passed with Lua and no skips, mypy 31
  files, lint/format/pip clean, strict specs 15/15; RL smoke passed with 3499 inputs.
- Native pure-v1/v2/v3 sessions confirmed death and watchdog New Run, use effect,
  checkpoint reload, frozen-source cleanup and train.csv rows.
- Episode `use_*` counts are requested uses (policy choice), not acknowledged presses.
- Native schema4 qualification passed (901 s, 3584 saved steps, clean shutdown).
- Scope limits: baseline Isaac stats/false tear flags/tears weapon only; other
  weapon types, positive tear flags and heavy-attack snapshot load not verified.

## Next

1. `pure-v1`, `pure-v2` and `pure-v3` are stopped; do not resume them.
2. Windows gate and mod deployment passed; source commit `c494aff`.
3. Fix narrow/irregular-room perimeter filtering in the Lua observer; add regression
   coverage, rerun checks and redeploy while closed. Repeat native check 2.3, including
   fire classification and the still-missing enemy-damage stall-clock reset case.
4. Resume the existing pure-v4 lineage without `--initialize` only with an agreed
   bounded native recheck; the conditional hourly run was not started. Older lineages
   remain stopped. [Qualification report](../reports/2026-10-23-pure-v4-native-acceptance.md).
5. Do not edit the working copy during a session.

## Navigation

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[RL design](RL_DESIGN.md) | [Architecture](ARCHITECTURE.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Archive](../archive/README.md)
