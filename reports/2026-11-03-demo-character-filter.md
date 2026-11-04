# Demo character filter

Date: 2026-11-03. Author: Mac work copy `~/work/isaac-chars`, base `3f2b41e`. Not committed.
OpenSpec: `openspec/changes/demo-pretraining-v1`, task group 4 (strict validation 37/37).

## Why

A second player will record with every character. The agent plays Isaac only (`live.py` rejects
`character_type != 0`) and its observation has no character identity, so steps of characters
with other attacks or health (Azazel, Forgotten, Lilith, The Lost, tainted characters) would teach
Isaac the wrong moves. Recordings of every character are kept for a later lineage that observes
the character (goal in `docs/PROGRESSION_GOAL.md`: every floor, then every character).

## What changed

- `demo_dataset.py`: `DemoSequence.characters` (character per decision point, `-1` without a
  player), stored in the cache (`LABELER_VERSION` 5: every cache rebuilds once, about a minute
  for the current recordings). `filter_characters` keeps only listed characters; a dropped step
  splits a sequence, a switch between listed characters (Lazarus rising) does not; pieces shorter
  than `min_steps` are dropped. `load_demos(characters=...)` filters after the cache, so the list
  is not in the cache key. `describe` adds `characters` (steps per character). CLI:
  `--characters` (default `DEFAULT_CHARACTERS`, or `all`), output adds `dropped_steps` and
  `recorded_characters`.
- `training.py`: `DemoConfig.characters` (default `[0, 1, 2, 3, 4, 5, 6, 8, 11, 12, 15, 18, 21]`,
  not hashed, recorded in `pretraining.json` with the rest of `demo`); `_demo_learner` passes it.
- `configs/training-pure-v4.yaml`: `demo.characters` with the same list.
- Docs: `docs/DEMO_RECORDING.md` (section Characters), `docs/PROGRESSION_GOAL.md` (gameplay
  milestones), `docs/STATUS.md`; OpenSpec delta (requirement "Demo character filter") and tasks.

Contract hash unchanged (`c8a7486b...`): the running lineage resumes with the filter.

## Checks (macOS)

| Check | Result |
|---|---|
| `scripts/check.sh` (ruff, format, mypy win32, pytest incl. Lua) | 1789 passed, 1 skipped, 2 failed (known macOS-only `test_menu_entry` struct layout, `test_session_runner` worker module) |
| OpenSpec `validate --all --strict` | 37/37 |
| Current recordings (copy of `runs/demos`, 37 files) | 36154 steps, 19 sequences, all character 0, `dropped_steps` 0; label counts equal to the gaps report |

New tests in `tests/test_demo_dataset.py`: per-step characters from a replay, split and keep
rules, filter after the cache with the cache holding every character, CLI fields, config default
equal to `DEFAULT_CHARACTERS`.

## Windows agent task

1. Only while training is stopped (`Train-Status.cmd`, `stop.forever` present). Commit the 10
   files listed below with the message "Demo character filter".
2. `scripts\Check.ps1`; record the counts.
3. `.venv\Scripts\python.exe -m isaac_threrisaifuture.demo_dataset runs\demos`: expect 36154+
   steps (more if new recordings were added), `dropped_steps` 0 and `recorded_characters` only
   `"0"` for the user's recordings. Mark task 4.5.
4. No mod change, no redeploy. The next `Train-Start.cmd` rebuilds the demo caches once.

Files: `configs/training-pure-v4.yaml`, `docs/DEMO_RECORDING.md`, `docs/PROGRESSION_GOAL.md`,
`docs/STATUS.md`, `openspec/changes/demo-pretraining-v1/specs/live-training-loop/spec.md`,
`openspec/changes/demo-pretraining-v1/tasks.md`, `src/isaac_threrisaifuture/demo_dataset.py`,
`src/isaac_threrisaifuture/training.py`, `tests/test_demo_dataset.py`,
`reports/2026-11-03-demo-character-filter.md`.

## Rollback

Before commit: `git checkout 3f2b41e -- <the 9 modified files>` and delete this report. After
commit: `git revert <commit>`. Recordings are untouched; old `.bc-*.npz` caches stay valid for
the old code.
