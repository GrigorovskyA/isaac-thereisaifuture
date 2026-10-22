# Evidence: safe-actions passive deployment

- Date/time and timezone: 2026-10-17, Europe/Amsterdam (CEST).
- Git revision and dirty status: started clean at 0b57e2a; documentation updates belong to the containing follow-up commit.
- Change scope and acceptance criteria: user requested installation after confirming game exit. Back up only the two existing observer files, verify backups, deploy 0.3.0 with action_authorization nil, compare source/installed hashes and run launch preflight without launching. No control acceptance claimed.
- Game/mod/bridge versions: historical game J460/build 22878971; adapter 0.2.0 -> 0.3.0; protocol/schema 1. No new game process or handshake.
- Python/package versions and configuration hash: unchanged Python 3.12.14 environment. Installed main.lua SHA-256 9c3e788833423a3bd9a77a84f86ee1ace0b17780d053c5b123bd0f00c45d9728; metadata.xml 4710d0f08d4c77336522f374e20542ff90851a475137b5e130542ff7df1703b2. Action gate remains nil.
- Scenario, split, seeds, budget and stop: closed-game two-file deployment only, refuse if Isaac is running or appears before a copy; fail on hash/preflight mismatch. No seed, split, RL or runtime action budget exercised.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Normal exit | Get-Process isaac-ng before deployment, before each copy and after preflight | 0 | passed | No Isaac process; no game termination or launch performed |
| Verified backup | Copy-Item for existing main.lua/metadata.xml; Get-FileHash before/after backup | 0 | passed | Both byte hashes match original 0.2.0; backup and private manifest under ignored reports/local |
| Disabled action gate | Read source Config and installed/source byte equality | 0 | passed | action_authorization = nil; Python cannot enable it |
| Source/installed identity | Copy-Item two source files; Get-FileHash each installed file | 0 | passed | Both match hashes above |
| Launcher preflight | .\.venv\Scripts\python.exe -m isaac_threrisaifuture.launcher --preflight-only | 0 | passed | Preflight passed; no processes launched or settings changed |
| OpenSpec and diff | OpenSpec.ps1 validate --all --strict; git diff --check | 0 | passed | Follow-up changes documentation only; seven strict items valid |
| Offline code tests | Previous Check.ps1 at 0b57e2a | 0 | passed | 224 tests, no skips; not rerun because source bytes/dependencies unchanged |
| Actual 0.3.0 loading | Manual launch/read-only handshake | N/A | not_run | Launch and save selection deliberately remain manual |
| Isolated action prerequisites and 50 controlled sequences | Tasks 1.3 / 3.2 | N/A | blocked | Isolation/restoration/write set, actual active-slot/instance identity and specific runtime action authorization unresolved; 0/50 |

## Real game

No live test occurred. The user closed Isaac normally. Only the existing
<Game>/mods/isaac_threrisaifuture_observer/main.lua and metadata.xml were replaced.
No save, mod-data, options, Steam/Cloud setting, launch option or mod marker was
edited. No REPENTOGON, screen capture, keyboard injection or reset was used.
Backups remain local and excluded from Git. Rollback requires normal game exit
and restoration of these two prior files only; never overwrite saves/options.

## RL evaluation

Not applicable.

## Limitations and continuation

Self-review checked actual process absence, preserved prior hashes, disabled gate,
matching deployment and unchanged code. This is a passive installation check,
not runtime API/effects/cleanup acceptance. Tasks 1.3/3.2 remain incomplete and the
OpenSpec change remains active/unarchived. The user's request authorizes this
closed-game installation; it does not supply the missing profile/slot evidence.
Next: manually launch/select and perform a bounded read-only 0.3.0 handshake.
Movement/shooting remain blocked until prerequisites and specific runtime action
authorization are satisfied.
