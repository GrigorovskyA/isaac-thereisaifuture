# Project status

Updated 2026-10-22 (Europe/Amsterdam). Current state only; dated evidence is history.
The pre-refactor STATUS is preserved in `archive/docs/STATUS.pre-pure.md`.

## Direction

- Pure self-learning since 2026-10-22 ([decision](UPDATE_DECISION.md)). One
  RecurrentPPO lineage `pure-v2` learns from scratch and continuously, from raw
  facts and outcome rewards only. No scripted setup, advice features or technique
  rewards. Hinted code, tests, docs and all previously open changes are in `archive/`.
- Active change: `openspec/changes/reward-v3-and-training-metrics` (1.1-2.2 done;
  native hours 2.3 open). `pure-self-learning-v1` native task 4.3 passed on frozen
  reward-v3 sources; changes remain unarchived.
- [Refactor report](../reports/2026-10-22-pure-self-learning-refactor.md).
- [Windows checks and native acceptance](../reports/2026-10-22-pure-windows-acceptance.md).
- [Reward v3 qualification and startup](../reports/2026-10-22-pure-v3-startup.md).

## Contracts

- Observation schema 3: 1837 floats (player, inventory, room facts, entity slots,
  pickup variant classes, held-collectible multi-hot). Oracle `room_index` stays out
  of the policy vector.
- Action v2: `MultiDiscrete([5, 5, 4])` (move, shoot, use none/bomb/active/pill-card).
- Reward v3: `configs/reward-v3.yaml`: enemy damage 5.0, first clear 10, health
  -1 per half-heart, first room visit 3, stall restart -5 (once, never with death), novelty 0.02 on the
  first visit of a cell only; exploit tests in `tests/test_reward_v3.py`.
- Episode = run. Death terminates; the stall watchdog (90 active s without
  progress) truncates and sends a `restart` command.
- Training: `configs/training-pure-v2.yaml` (contract reward_version 3 must match the code); lineage hash = `contract` only;
  hyperparameters tunable between sessions; retention 5 newest + every 200th (~3 h).
- Dashboard (added after the squash, uncommitted): `Start-Dashboard.cmd` serves a
  live read-only view of `runs\pure-v2` at http://127.0.0.1:8765; episode CSV rows
  carry `wall_time`. New `metrics/train.csv`: one row per update (SB3 statistics, action mix).
- Supervisor: `Start-Pure.cmd` / `session_runner --forever`; unlimited New Run,
  consecutive-fault cap 5, disk cap, session-log retention 20.

## Lineage

- `pure-v1` (reward v2): 9 native episodes, about 7k steps; preserved under
  `runs/pure-v1`, not resumed. Superseded because reward v2 paid most for idling:
  stall-restarted episodes without a fight returned +2 to +5.6 (novelty +4 to +6.5),
  while episodes that damaged enemies and died returned -12.6 and -13.3
  ([proposal](../openspec/changes/reward-v3-and-training-metrics/proposal.md)).
- `pure-v2` (reward v3) exists: seed 1, qualification saved `d9b93984-s1-t7168`.
  Contract hash `d9b939847544687899d97490a6deff29f60ee0392d275d12cd96e4e3637a4c76`.
  Resume without --initialize. Pure-v1 checkpoints are refused. Old lineages (v2-v5,
  `a0a93c29-s20-t26368`, `t27904` and ancestors) stay preserved; incompatible with
  schema 3.

## Verification

- macOS offline gate after reward v3 + dashboard: ruff/format clean, mypy 31 files clean,
  pytest 1058 passed / 1 skipped / 2 failed, strict OpenSpec 12/12, RL smoke passed. The 2 failures are pre-existing macOS-only tests
  (Windows input struct layout, owned worker import); they failed before the
  refactor too.
- Windows `scripts/Check.ps1`: passed with Lua suites, 1030 tests, no skips;
  mypy 29 files, lint/format, pip check, strict OpenSpec 11/11. A temporary
  fixture writer needed explicit LF on Windows. Synthetic RL smoke passed.
- Current Windows gate after reward v3: 1061 tests without skips, mypy 31 files,
  lint/format/pip clean, strict specs 12/12. Synthetic RL smoke passed.
- Native `pure-v1` (reward v2): 15-minute session, 7168 saved steps, 9 episodes
  (2 deaths, 7 stalls). Death and watchdog New Run confirmed; the user observed a
  use effect; model/normalizer loaded back; a read-only probe kept 40 schema 3 frames.
  That old session failed its frozen-source check. The pure-v2 qualification
  subsequently passed: 15 minutes, 7168 saved steps, 10 episodes (3 deaths,
  7 stalls), 14 optimizer rows, 5 start-room exits, 0 clears; clean shutdown,
  checkpoint/model/normalizer readback and unchanged frozen inputs.
- Still unverified: nonzero item/coin snapshot diversity, all three use variants,
  collectible scan worst-case cost, pickup Price semantics and worst-case size.

## Next

1. `pure-v1` is stopped (stop file present); do not resume it.
2. Windows gate and bounded native qualification passed. Deployed Lua matched;
   no redeployment was needed. Old abandoned approval removal was separately authorized.
3. Continuous `pure-v2` resumed at 17:14:57 CEST without --initialize, parent
   `d9b93984-s1-t7168`; file2/Isaac and the connected pure-v3 learner verified.
   Session `runs/pure-v2/supervisor/session-20261022-171457-0001` is running.
   First resumed checkpoint `d9b93984-s1-t7680` has the expected parent and
   continued optimizer count; frozen hashes still match.
   Do not edit frozen source/config/mod during this session. Stop via
   `runs/pure-v2/supervisor/stop.forever` when maintenance is needed.
4. After hours of play, compare return by outcome, exit rate, damage dealt and taken
   with the first `pure-v1` episodes (task 2.3).

## Navigation

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[RL design](RL_DESIGN.md) | [Architecture](ARCHITECTURE.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Archive](../archive/README.md)
