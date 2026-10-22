# Project status

Updated 2026-10-22 (Europe/Amsterdam). Current state only; dated evidence is history.
The pre-refactor STATUS is preserved in `archive/docs/STATUS.pre-pure.md`.

## Direction

- Pure self-learning since 2026-10-22 ([decision](UPDATE_DECISION.md)). One
  RecurrentPPO lineage `pure-v1` learns from scratch and continuously, from raw
  facts and outcome rewards only. No scripted setup, advice features or technique
  rewards. Hinted code, tests, docs and all previously open changes are in `archive/`.
- Active change: `openspec/changes/pure-self-learning-v1` (tasks 1.1-3.3 implemented
  offline; 4.1 docs and 4.2 Windows gate done; 4.3 native acceptance open).
- [Refactor report](../reports/2026-10-22-pure-self-learning-refactor.md).
- [Windows checks and native acceptance](../reports/2026-10-22-pure-windows-acceptance.md).

## Contracts

- Observation schema 3: 1837 floats (player, inventory, room facts, entity slots,
  pickup variant classes, held-collectible multi-hot). Oracle `room_index` stays out
  of the policy vector.
- Action v2: `MultiDiscrete([5, 5, 4])` (move, shoot, use none/bomb/active/pill-card).
- Reward v2: `configs/reward-v2.yaml`, outcome terms plus bounded pickups and
  novelty; exploit tests in `tests/test_reward_v2.py`.
- Episode = run. Death terminates; the stall watchdog (90 active s without
  progress) truncates and sends a `restart` command.
- Training: `configs/training-pure-v1.yaml`; lineage hash = `contract` only;
  hyperparameters tunable between sessions; retention 5 newest + every 50th.
- Supervisor: `Start-Pure.cmd` / `session_runner --forever`; unlimited New Run,
  consecutive-fault cap 5, disk cap, session-log retention 20.

## Lineage

- `pure-v1` exists: seed 1, latest `c5532096-s1-t7168`, contract hash
  `c55320966c51d7c51069352659c916111a9c2f55d319d66817789791222c6ada`.
  Resume this lineage without `--initialize`. Old lineages remain preserved.

## Verification

- macOS offline gate in a local copy: ruff/format clean, mypy (29 files) clean,
  pytest 1027 passed / 1 skipped / 2 failed, strict OpenSpec 11/11, RL smoke on
  the new spaces passed. The 2 failures are pre-existing macOS-only tests
  (Windows input struct layout, owned worker import); they failed before the
  refactor too.
- Windows `scripts/Check.ps1`: passed with Lua suites, 1030 tests, no skips;
  mypy 29 files, lint/format, pip check, strict OpenSpec 11/11. A temporary
  fixture writer needed explicit LF on Windows. Synthetic RL smoke passed.
- Current workspace recheck after the user's dashboard/metrics edits: Windows
  gate passed, 1043 tests without skips, mypy 30 files, strict specs 11/11.
- Native: 15-minute session, 7168 saved steps, 9 completed episodes (2 deaths,
  7 stalls). Death and watchdog New Run confirmed; user observed a use effect;
  model/normalizer loaded back; separate read-only probe retained 40 schema3 frames.
- Task 4.3 stays open: concurrent user edits changed the frozen episode_metrics.py
  during training, so final state is fault despite learner exit 0 and normal game/
  approval cleanup. All five feature observations are recorded; clean resume and
  frozen-source cleanup on the final integrated code are pending.
- CSV migrated additively for the user's wall_time field: all 9 rows preserved,
  historical timestamps blank; exact backup is beside episodes.csv.
- Still unverified: nonzero item/coin snapshot diversity, all three use variants,
  collectible scan worst-case cost, pickup Price semantics and worst-case size.

## Next

1. Stopped at the user's requested handoff point; no game/learner/listener or
   approval remains. stop.forever is intentionally present. No long run started.
2. Squash/push completed at root bd44fe6; external old-history bundle verified.
3. Preserve the user's concurrent dashboard work. When it is stable, run a clean
   bounded resume from latest, without --initialize, and verify final cleanup.
4. Only after task 4.3 acceptance, start continuous training. Compare frozen
   gameplay against random policy after approximately 24 hours; P2 is not accepted.

## Navigation

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[RL design](RL_DESIGN.md) | [Architecture](ARCHITECTURE.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Archive](../archive/README.md)
