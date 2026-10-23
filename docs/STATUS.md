# Project status

Updated 2026-10-23 (Europe/Amsterdam). Current state only; dated evidence is history.
The pre-refactor STATUS is preserved in `archive/docs/STATUS.pre-pure.md`.

## Direction

- Pure self-learning since 2026-10-22 ([decision](UPDATE_DECISION.md)). One
  RecurrentPPO lineage learns from scratch and continuously, from raw facts and
  outcome rewards only. No scripted setup, advice features or technique rewards.
  Hinted code, tests, docs and all previously open changes are in `archive/`.
- Active changes:
  - `openspec/changes/stall-watchdog-novel-progress`: only facts new for the run reset
    the stall watchdog (revisited rooms and regained counters no longer do). 1.1 and
    2.1 done on macOS; Windows gate 2.2 passed (1123 tests with Lua, smoke passed).
    Native check 2.3 passed in the 15-hour run (no long stalls). All tasks done;
    unarchived. No contract change.
  - `openspec/changes/pure-v3-observation-and-control`: observation schema 4, 32 KiB
    messages, action repeat 6, use-head prior, reward v4 and lineage `pure-v3`.
    Tasks 1.1-2.3 passed, including the bounded native check; unarchived.
  - `openspec/changes/reward-v3-and-training-metrics` (1.1-2.2 done; native hours 2.3
    answered by the pure-v2 analysis below, kept open for pure-v3) and
    `openspec/changes/pure-self-learning-v1` (all tasks done; 4.3 closed by the
    [reward-v3 startup report](../reports/2026-10-22-pure-v3-startup.md)).
- [Refactor report](../reports/2026-10-22-pure-self-learning-refactor.md).
- [Windows checks and native acceptance](../reports/2026-10-22-pure-windows-acceptance.md).
- [Schema4 Windows gate and native plan](../reports/2026-10-22-pure-v3-schema4-acceptance.md).

## Contracts

- Observation schema 4: 2038 floats (schema 3's 1837 plus stats 6, tear flags 16,
  weapons 15, own attacks 16 x 8, bombs 4 x 9). Oracle `room_index` and hidden enemy
  HP stay out of the policy vector. Messages up to 32 KiB (Lua and Python).
- Action v2: `MultiDiscrete([5, 5, 4])` (move, shoot, use none/bomb/active/pill-card),
  held for 6 game updates (0.2 s). The use head starts at P(none)=0.85, 0.05 per press
  (fresh model only, never on resume).
- Reward v4: `configs/reward-v4.yaml` = reward v3 with new collectible 2.0 (was 1.0);
  enemy damage 5.0, first clear 10, health -1 per half-heart, first room visit 3, stall
  restart -5 (once, never with death), novelty 0.02 on the first visit of a cell only.
  Exploit tests in `tests/test_reward_v4.py`.
- Episode = run. Death terminates; the stall watchdog (90 active s without
  progress new for the run) truncates and sends a `restart` command.
- Training: `configs/training-pure-v3.yaml` (contract: observation 4, action 2, reward 4,
  action repeat 6, `use_head_initial_none_probability` 0.85; must match the code); lineage
  hash = `contract` only; hyperparameters tunable between sessions; retention 5 newest +
  every 200th rollout.
- Dashboard: `Start-Dashboard.cmd` serves a live read-only view of `runs\pure-v3` at
  http://127.0.0.1:8765; episode CSV rows carry `wall_time`; `metrics/train.csv` has one
  row per update (SB3 statistics, action mix).
- Supervisor: `Start-Pure.cmd` / `session_runner --forever` (run root `runs\pure-v3`);
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
- `pure-v3` (schema 4, reward v4) exists: seed 1, qualification checkpoint
  `03b9c5e3-s1-t3584`, contract hash
  `03b9c5e3c782d6b3d59c0e6b30cc4aa7ea8818f3d68e7180f4a32c269fdc8429`.
  Resume without --initialize. Older checkpoints are refused. First hour
  ([report](../reports/2026-10-22-pure-v3-first-hour.md)): bomb requests 0.05-0.07 per
  step (pure-v2 0.24), start-room exits 69-77%, explained variance positive; one
  16-minute stall episode (watchdog hole, fixed). After 15 hours (latest
  `03b9c5e3-s1-t243200`, 622 episodes, 243k steps, zero faults;
  [report](../reports/2026-10-23-pure-v3-overnight.md)): start-room exits 86-91%, idle
  moves halved, explained variance 0.42, entropy 3.59; clears flat (0.1-0.2 per
  episode), stage 2 never reached. Fast deaths are mostly real combat, self-bombs and
  hazards. `enemies_killed` is always 0. `ent_coef` lowered 0.01 -> 0.005 for the next
  session (the use head drifted back toward uniform). Even older
  lineages (v2-v5, `a0a93c29-s20-t26368`, `t27904` and ancestors) stay preserved.

## Verification

- macOS offline gate for the pure-v3 change (tasks 1.1 and 1.2): ruff and format clean,
  mypy 31 files clean, pytest 1116 passed / 1 skipped / 2 failed, strict OpenSpec 13/13,
  RL smoke passed. The 2 failures are the known macOS-only tests (Windows input struct
  layout, owned worker import).
- Added in 1.2: use-head probabilities 0.85/0.05/0.05/0.05 on random observations at
  creation, move/shoot heads untouched, no prior on resume, `pure-v1`/`pure-v2` configs and
  checkpoints refused, live env sends frames=6 from the contract, collectible 2.0.
- Current Windows gate with Lua suites: 1123 tests passed without skips, mypy 31
  files, lint/format/pip clean, strict specs 14/14. RL smoke passed with 2038 inputs.
  Oversized-message test IDs were shortened to fit Windows environment limits;
  protocol tests and message limits were not relaxed.
- Native `pure-v1` (reward v2) and `pure-v2` (reward v3) sessions confirmed death and
  watchdog New Run, a user-observed use effect, checkpoint reload, frozen-source
  cleanup and train.csv rows. Windows `Check.ps1` for reward v3: 1061 tests, no skips.
- Episode `use_*` counts are requested uses (policy choice), not acknowledged presses.
- Native schema4 qualification passed after 901.782 s: 1100 retained frames,
  863 with own_attack; six bomb identities, accepted use acknowledgements and
  increasing bomb age; watchdog and death New Run confirmed. Six episodes
  (one death, five stalls), seven updates, 3584 saved steps. Actual model and
  normalizer loaded back; 791 frozen files unchanged; clean owned shutdown.
- Scope limits: baseline Isaac stats/false tear flags/tears weapon only; other
  weapon types, positive tear flags and heavy-attack snapshot load not verified.

## Next

1. `pure-v1` and `pure-v2` are stopped; do not resume them.
2. Continue `pure-v3` from `03b9c5e3-s1-t243200` without --initialize for the authorized
   one-hour test (`ent_coef` 0.005, `gamma` 0.995; rollback: 0.01 and 0.99).
   Timer receipt: `runs/pure-v3/supervisor/one-hour-timer.json`. After normal shutdown,
   record counts/checkpoint/cleanup in `reports/2026-10-23-pure-v3-gamma-test.md`.
   Mac-agent analysis compares metrics with the [15-hour report](../reports/2026-10-23-pure-v3-overnight.md).
3. Candidate next lineage (needs an OpenSpec change and a plan): obstacle type in the
   observation (rock, pit, spikes, TNT; bombable or not), damage source in metrics,
   a working `enemies_killed` counter.
4. Do not edit the working copy during a session.

## Navigation

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[RL design](RL_DESIGN.md) | [Architecture](ARCHITECTURE.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Archive](../archive/README.md)
