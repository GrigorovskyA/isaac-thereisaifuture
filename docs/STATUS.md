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

- `pure-v1` does not exist yet. The first native session creates it with
  `--initialize`. Old lineages (v2-v5, `a0a93c29-s20-t26368`, `t27904` and
  ancestors) stay preserved under `runs/`; they are incompatible with schema 3.

## Verification

- macOS offline gate in a local copy: ruff/format clean, mypy (29 files) clean,
  pytest 1027 passed / 1 skipped / 2 failed, strict OpenSpec 11/11, RL smoke on
  the new spaces passed. The 2 failures are pre-existing macOS-only tests
  (Windows input struct layout, owned worker import); they failed before the
  refactor too.
- Windows `scripts/Check.ps1`: passed with Lua suites, 1030 tests, no skips;
  mypy 29 files, lint/format, pip check, strict OpenSpec 11/11. A temporary
  fixture writer needed explicit LF on Windows. Synthetic RL smoke passed.
- Not run: any pure-profile game session.
- Unverified natively: `ExecuteCommand("restart")` while alive, one-shot
  `IS_ACTION_TRIGGERED` for bomb/item/pill-card, collectible scan cost, pickup
  `Price` semantics, schema 3 snapshot size margin (worst case 15674 of 16384 bytes
  in tests).

## Next

1. Squash the verified refactor to one root commit and push as authorized.
   Old history is preserved in the verified external Git bundle.
2. Windows gate is complete (task 4.2).
3. Deploy `mod/observer`, then run one bounded native acceptance session (task 4.3).
4. Start continuous training with `Start-Pure.cmd ... --initialize`.

## Navigation

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[RL design](RL_DESIGN.md) | [Architecture](ARCHITECTURE.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Archive](../archive/README.md)
