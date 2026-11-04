# Demo lineage v2: stop the first demo lineage, start a new one on all recordings

Date: 2026-11-04. Author: Mac work copy `~/work/isaac-chars`, base `3f2b41e` plus the demo
character filter ([report](2026-11-03-demo-character-filter.md)). Not committed.

## Why

The first demo lineage (contract `c8a7486b...`, `runs/pure-v4`) ran 440k steps. Per 20k steps
it rose until about 60-80k and then stayed flat:

| Steps | Rooms | Kills | Clears | Deaths | Stalls | Half hearts lost |
|---|---|---|---|---|---|---|
| 0-20k | 1.69 | 1.20 | 0.18 | 32% | 68% | 2.46 |
| 60-80k | 1.97 | 2.40 | 0.42 | 33% | 67% | 3.12 |
| 200-220k | 2.00 | 2.69 | 0.37 | 33% | 67% | 3.01 |
| 320-340k | 2.16 | 3.03 | 0.41 | 40% | 60% | 3.51 |
| 420-440k | 2.10 | 2.95 | 0.41 | 36% | 64% | 3.24 |

Stage 2 was reached in 1 of 4076 episodes. The use head never pressed (`use_none` 1.0). Entropy
fell from 0.48 after the 2026-11-03 restart to 0.22.

`seed-1/pretraining.json` shows the pretraining used 19073 demo steps (16 sequences, 2 held
out): only the 2026-11-02 recordings. The 2026-11-03 recordings, which hold full floors
(one file goes from floor 1 to floor 6, another from 4 to 6), reached the lineage only through
the regulariser, whose weight was already falling. Train NLL 0.28 against holdout NLL 1.98 and
the best holdout at step 750 of 2250 show the small set was memorised.

## What changed

- Training stopped from the Mac by creating `runs/pure-v4/supervisor/stop.forever` (what
  `Train-Stop.cmd` does). Final checkpoint `c8a7486b-s1-t440320`, stop reason "stop file".
- `runs/pure-v4` renamed on SMB to `runs/pure-v4-demo-bc-v1`. Sizes of all files outside
  `supervisor/` were compared before and after: identical.
- The 10 files of the character filter synced to SMB (they were unchanged on SMB since
  `3f2b41e`; previous versions in `~/work/smb-backup-20261104-chars` on the Mac).
- `configs/training-pure-v4.yaml` `demo:` (not hashed, so the contract hash stays `c8a7486b...`):
  `bc_coef` 1.0 -> 2.0, `bc_decay_timesteps` 1M -> 3M, `min_steps` 20000 -> 30000.
- `tests/test_demo_learning.py`: the shipped-config test checks the new values.
- `docs/STATUS.md`, `docs/DEMO_RECORDING.md`: the stop, the archive and the new values.

The demo set with the default character filter: 36154 steps in 19 sequences, all Isaac; use
presses in the demos: 39 bomb, 16 active, 43 pill/card of 36154 steps.

## Checks (macOS)

| Check | Result |
|---|---|
| `test_demo_dataset`, `test_demo_learning`, `test_training_manifest`, `test_pure_training` | 116 passed |
| ruff check and format on the changed test | clean |
| `scripts/check.sh` before this config change (character filter) | 1789 passed, 1 skipped, 2 failed (known macOS-only `test_menu_entry`, `test_session_runner`) |
| Native game | not run |

## Windows agent task

1. Commit the character filter files (see its report) and these 5 files:
   `configs/training-pure-v4.yaml`, `tests/test_demo_learning.py`, `docs/STATUS.md`,
   `docs/DEMO_RECORDING.md`, `reports/2026-11-04-demo-lineage-v2.md`, message
   "Demo lineage v2: stronger and longer BC regulariser, min 30000 demo steps".
2. Run `scripts\Check.ps1` and record the counts.
3. Check that `runs\pure-v4` does not exist and `runs\pure-v4-demo-bc-v1\seed-1\checkpoints`
   ends at `c8a7486b-s1-t440320`.
4. `Train-Start.cmd --initialize`. Report `runs\pure-v4\seed-1\pretraining.json`: `demo_steps`
   (expect 36154 minus the holdout), holdout accuracy before and after per head against
   `majority_accuracy`, `best_step`.
5. After 100k steps compare against `runs\pure-v4-demo-bc-v1` at equal steps (rooms, kills,
   clears, stage 2+, stall share, entropy).

## Rollback

- Config: restore `bc_coef: 1.0`, `bc_decay_timesteps: 1000000`, `min_steps: 20000` and the test
  line `(64, 16, 20000)`; or `git checkout 3f2b41e -- configs/training-pure-v4.yaml
  tests/test_demo_learning.py` before commit.
- Resume the old lineage: rename `runs\pure-v4-demo-bc-v1` back to `runs\pure-v4` (only while no
  new `runs\pure-v4` exists, or move that one aside first) and run `Train-Start.cmd` without
  `--initialize`.
