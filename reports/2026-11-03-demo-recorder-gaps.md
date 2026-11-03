# Evidence: demo recording gaps and continuation

- Date: 2026-11-03, Europe/Amsterdam. Base revision: `ed5c729`; changes uncommitted.
- Scope: demo recording timeouts and offline continuation stitching; no training or save changes.
- Training preflight: `Train-Status.cmd` reported not running, with `stop.forever` present.
  The previous session had a command-acknowledgement fault; no training was resumed.
- Runtime: Windows, Python 3.12.14; Torch 2.14.1+cu130 reported CUDA available.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Recorder timeout and socket buffer | passed | Real socket test inserts a five-second silent gap in a partial message; one file and one waiting notice. Idle limit is 30 minutes. |
| Replay continuation and fidelity | passed | Synthetic split/unsplit vectors and labels, optional seed mismatch, rewind and boundary fixtures; existing live-env fidelity test unchanged. |
| Windows quality gate | passed | `scripts/Check.ps1`: 1,787 passed, two warnings; lint, formatting, mypy and dependency check passed. |
| Strict specifications | passed | `scripts/OpenSpec.ps1 validate --all --strict`: 37/37. |
| Historical recordings | passed | 36 existing files, 14 requested merge boundaries; 35,437 steps before and after, 32 sequences before and 18 after. All move/shoot/use label counts unchanged. Derived active seconds changed from 7,272.533 to 7,284.1; this is not a claim of extra recorded steps. |
| Floor transition and alt-tab | passed | One new file, `20261103-124112-f102887d.jsonl.gz`, includes stage 1 to stage 2, a 120.579 s paused interval and a 6.14 s receipt gap followed by resumed snapshots. The user confirmed the requested alt-tab scenario. |
| Dataset after native check | passed | `python -m isaac_threrisaifuture.demo_dataset runs/demos`: 36,154 steps in 19 sequences; the new recording adds 717 steps and one sequence. |

The group cache key covers all member recordings and the revised derivation version; old
recordings are not deleted or rewritten. The files affected are the recorder, observer client,
dataset replay, demo oracle metadata, related tests and fixture, OpenSpec deltas, and recording
documentation. No training timeout was changed.

## Real game and deployment

Before the native check, the closed-game deployed observer was replaced with the source file.
Both SHA-256 values were `449f9e765a643a9c9c24724a2649a2407db560890093851677d831f0db711bac`.
The previous deployed file was backed up under
`reports/local/demo-recorder-gaps-20261103/observer-before-main.lua`, SHA-256
`ea4303ae80b4d86c87aee81dbf54386b9adf31556e69e89b340f45a242cfcbf5`.
The user played the native scenario and stopped the recorder with Ctrl+C. The file contains
5,491 snapshots (2,907 active, 2,584 paused), over 287.641 receipt seconds; the demo oracle
reported a run seed. The file remained one session across the floor transition and pause.
Afterwards the recorder listener, game, training supervisor and worker were absent. This is
evidence for this recorded scenario, not a gameplay-quality or training result.

## Limitations and rollback

Continuation for old recordings with no seed is heuristic under the agreed boundary rule;
it is not proof of identity. Unrelated pre-existing OpenSpec tasks 2.2 and 2.3 remain open.
To roll back, stop the recorder, close Isaac, restore the saved deployed `main.lua`, and revert
the code change; existing recordings remain intact and old cache keys can be rebuilt.
