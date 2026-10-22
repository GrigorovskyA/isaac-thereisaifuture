# Evidence: pure self-learning refactor

- Date: 2026-10-22, Europe/Amsterdam. Host: macOS (Darwin arm64), offline only.
  No game, Steam, approval, save, deployment, training run or model write.
- Decision: `docs/UPDATE_DECISION.md` (user, 2026-10-22). OpenSpec change:
  `openspec/changes/pure-self-learning-v1` (tasks 1.1-4.1 done; 4.2, 4.3 open).
- Base: working tree of `ace33dd` plus the uncommitted wall-stagnation work of
  another agent (preserved; see Archive). Content is identical to `026eeab`
  (author-fixed history on `origin/main` and branch `codex/fix-personal-author-20261022`).
- Work was done in a local copy (`~/work/isaac`) and synced back to the SMB checkout
  without `.git`. **Nothing was committed or staged.** The user commits from Windows.

## Outcome

The project now trains one RecurrentPPO model from scratch and continuously, on raw
game facts and outcome rewards only. Hint, diagnostic, native-episode and roadmap
code is in `archive/`. The Python package went from 70 modules / ~16.3k lines to
29 modules / ~7.4k lines; the Lua observer from 1858 to 823 lines.

| Area | Result |
| --- | --- |
| Archive | 41 source modules, 54 test files, 6 configs, ~25 docs, all 46 open OpenSpec changes and the `combat-experience-gate` spec moved to `archive/` (`archive/README.md`) |
| Lua trim | Callback trace, oracle probe, lifecycle diagnostics, navigation grid/doors, target-phase, tear audit, firing/boundary/policy geometry and their capabilities removed; pre-trim copy `archive/mod/main.pre-pure.lua` |
| Observation schema 3 | 1837 floats: player 9, inventory 9, room facts 43, enemy/projectile/obstacle slots, pickup slots with variant class/subtype/shop flag, held-collectible multi-hot 1..1024; oracle `room_index` never in the policy vector |
| Action v2 | `MultiDiscrete([5, 5, 4])`; `use` none/bomb/active/pill-card as a one-shot press in Lua |
| Reward v2 | `configs/reward-v2.yaml`: damage, first clear/visit per (stage, room), first floor, health lost, death, time, pickups above run peak with shared cap, new collectible per ID, heal capped by loss, novelty 0.02/sqrt(n) |
| Episodes | One episode = one run; death terminates; room clear no longer ends an episode; 60 s segments removed |
| Restart and watchdog | `restart` command through the death-restart path; approval `max_restarts` 0 = unlimited; `StallWatchdog` truncates after 90 active s without progress and sends one restart; faults are never stalls |
| Continuous training | `configs/training-pure-v1.yaml`: lineage hash = `contract` only; hyperparameters (incl. n_steps) applied on resume and recorded per checkpoint; retention 5 newest + every 50th; `metrics/episodes.csv`; consecutive-fault cap |
| Supervisor | `session_runner --forever` / `Start-Pure.cmd`; sessions back to back resuming `latest`; stops on stop file, Ctrl+C, disk cap, refused lineage/config, 5 consecutive faulted sessions; keeps 20 newest session log folders |
| Docs | README, ROADMAP, STATUS, ARCHITECTURE (module map), RL_DESIGN, RUNTIME_AUTHORITY (pure standing authority), TRAINING_SESSION, AGENTS (6.5 KB), `openspec/config.yaml`; old versions in `archive/docs/*.pre-pure.md` |

## Checks

| Check | Status | Detail |
| --- | --- | --- |
| ruff check / format | passed | `src tests scripts/smoke_rl.py`, 67 files |
| mypy `--platform win32` strict | passed | 29 source files |
| pytest `-m "not game"` with Lua suites (lupa, json.lua) | passed with 2 known failures | 1027 passed, 1 skipped (native Windows sharing), 2 failed |
| Known failures | pre-existing | `test_menu_entry.py::test_windows_input_struct_matches_native_64bit_layout` and `test_session_runner.py::test_owned_worker_command_is_importable_module` fail on macOS before and after the refactor (baseline: 2428 passed, same 2 failed) |
| OpenSpec `validate --all --strict` | passed | 11/11 |
| RL smoke (`scripts/smoke_rl.py`) | passed | new 1837/`[5,5,4]` spaces |
| `uv pip check` | passed | |
| Archived names in `src/ tests/ scripts/ mod/` | passed | no matches |
| Windows `scripts/Check.ps1` | not_run | needs the Windows PC (task 4.2) |
| Native game session | not_run | task 4.3 |

Test count fell from 2428 to 1027 because hint/diagnostic tests moved to
`archive/tests/`. About 210 new tests cover schema 3, action v2, reward v2
exploits, restart/watchdog and continuous training.

Known weaker coverage: the Lua trim removed lifecycle diagnostics, so the
async-restart tests no longer check exact lease deadlines and attempt counters.
The 5 s restart-confirmation timeout is checked again through kept log lines
(`tests/test_lua_restart_command.py`).

## Unverified in the real game

- `Isaac.ExecuteCommand("restart")` while the player is alive (stall restart).
- One-shot `IS_ACTION_TRIGGERED` for `ACTION_BOMB`, `ACTION_ITEM`, `ACTION_PILLCARD`.
- Cost of `HasCollectible` over IDs 1..1024 every 30 frames.
- Pickup `Price` semantics (devil deals negative, free -1000), card/pill/trinket
  ID ranges, `GetActiveCharge` overcharge, door `IsOpen` per slot.
- Snapshot size: worst case 15674 of 16384 bytes with the test JSON shim.
- Whether paused snapshots keep arriving while paused (the watchdog relies on it).

## Judgement calls to review

- Consumable pickups pay only above the run's peak count, so drop/re-pickup and
  spend/re-collect pay nothing until the peak is passed.
- A rejected restart still truncates the episode and is counted, not a fault.
- The watchdog adds at most 2 s per snapshot gap, so learner pauses are not stalls.
- `combat-v1` reward and config v1 remain for offline synthetic tests only.
- Session log folders older than the newest 20 are deleted by the forever supervisor.

## Archive

`archive/` keeps the hinted code, tests, docs, configs and OpenSpec changes
unchanged, including the other agent's uncommitted `wall_stagnation.py`,
`tests/test_wall_stagnation.py`, `tests/fixtures/wall_stagnation/` and
`openspec/changes/wall-stagnation-replay/`. Its diagnosis report stays in
`reports/2026-10-22-wall-stagnation-diagnosis.md`. Removed junk: `errors.txt`,
`agent-status.json` (ignored). `tools/offline-replay-viewer` untouched.

## Identities

- `mod/observer/main.lua` SHA256 `edf4eff22eb785c6b9a24cc511f65b075af23da67c3b5aa7df19d1340ee7c1c8`
- `configs/training-pure-v1.yaml` SHA256 `f3fd14b993fc4c37b1b4d971fe1575c5ae2c46010fe9e79add0d99b3b13319d3`
- `configs/reward-v2.yaml` SHA256 `35f7e895e0d5fa096c0014ce88a3fc9b64df6d00cbe46b61f7e50852c62d386e`

## Handoff for the Windows agent

Run from `D:\isaac` in PowerShell. The user authorized a one-time history squash
(2026-10-22): the repository becomes a single commit without history. This
overrides the usual "never force-push" rule for this step only.

1. Delete the two files the SMB share could not delete. Close any editor, IDE or
   Python process that holds them first:

   ```powershell
   Remove-Item -Force src\isaac_threrisaifuture\campaign.py
   Remove-Item -Force src\isaac_threrisaifuture\.smbdeleteAAA100000000d98c
   Test-Path src\isaac_threrisaifuture\campaign.py   # must print False
   ```

   `campaign.py` is already in `archive/src/isaac_threrisaifuture/`. Left in `src/`,
   it breaks lint and mypy because its imports were archived.
2. Review the tree: `git status`, `git diff --stat`. Expect ~358 deletions (moves to
   `archive/` show as delete + add), ~55 modified files and new files including
   `archive/`, `src/isaac_threrisaifuture/{live_wire,stall_watchdog,episode_metrics}.py`,
   new tests, configs, `Start-Pure.cmd`, this report and `docs/UPDATE_DECISION.md`.
   Make sure no `runs/`, models, approvals, saves or raw logs are untracked-but-not-ignored.
3. Gate: `.\scripts\Check.ps1` (expect all pass on Windows, including the two
   macOS-only tests), then `.\scripts\Smoke-RL.ps1`. Fix failures before step 4.
4. Back up the full old history outside the repository, then squash to one commit:

   ```powershell
   git bundle create ..\isaac-history-backup-20261022.bundle --all
   git config user.name    # check: personal identity, not a work account
   git config user.email
   git checkout --orphan squashed
   git add -A
   git status              # review once more
   git commit -m "IPI-000: pure self-learning Isaac RL agent"
   git branch -D main
   git branch -m main
   git branch -D codex/backup-before-author-fix-20261022 codex/fix-personal-author-20261022
   git for-each-ref refs/codex --format="%(refname)" | ForEach-Object { git update-ref -d $_ }
   git push --force origin main
   git ls-remote origin    # delete any other remote branches/tags with: git push origin --delete <name>
   git reflog expire --expire=now --all
   git gc --prune=now
   git log --oneline       # must show exactly one commit
   ```

   Notes: old reports mention commit hashes that no longer exist after the squash;
   they are historical text. GitHub may keep old commits reachable for a while
   (cached views, forks, pull-request refs); deleting and recreating the remote
   repository is the only complete purge.
5. Native acceptance (task 4.3): deploy `mod/observer` with Isaac closed, run one
   bounded session (`live --mode train --launch --confirmed-save-slot 2 --out-dir
   runs\pure-v1` after `approve-training --confirmed-save-slot 2 --unlimited-restarts`,
   or `Start-Pure.cmd ... --initialize` and stop it after the checks), and record:
   schema 3 frames with plausible values, an accepted use press with a visible effect,
   a stall restart, a death restart and a reloadable checkpoint.
6. Then run `Start-Pure.cmd "<Isaac dir>" "<log.txt>"` for continuous training.

## Rollback

The exact pre-refactor SMB tree (including the uncommitted wall-stagnation work) is
in `~/work/isaac-smb-backup-20261022/` on the Mac:
`rsync -a --delete --exclude-from=$HOME/work/rsync-excludes.txt --exclude .git/ ~/work/isaac-smb-backup-20261022/ <SMB checkout>/`.

## Sync note

The SMB sync completed except two files the share reported as busy (held open on
the Windows side): `src/isaac_threrisaifuture/campaign.py` (archived copy is in
`archive/src/isaac_threrisaifuture/`) and `src/isaac_threrisaifuture/.smbdeleteAAA100000000d98c`
(an SMB pending-delete stub). Delete both on Windows before running the gate (handoff step 1).
