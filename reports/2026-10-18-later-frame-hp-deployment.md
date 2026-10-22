# Evidence: closed-game observer 0.4.5-dev deployment

- Date/time and timezone: 2026-10-18 12:20, Europe/Amsterdam (10:20 UTC).
- Git revision and dirty status: 239146a; only unrelated untracked errors.txt before deployment, preserved.
- Scope: install reviewed later-frame diagnostic source with backup/readback and normal launcher preflight. Runtime acceptance is separate.
- Game/mod/bridge: existing Repentance+ installation, observer updated from 0.4.4-dev to 0.4.5-dev; no live handshake in this operation.
- Python/packages: existing CPython 3.12 environment; no package/lock changes.
- Scenario/budget: operator reported game closed; process absence checked before backup, before each of two writes and afterward. No launch, attach, controls or restart.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Closed-game guard | tasklist /FI "IMAGENAME eq isaac-ng.exe" /FO CSV /NH, parsed by Python | 0 | passed | No matching process at each guarded stage |
| Reviewed artifacts | SHA256 source and installed files against fixed expected values | 0 | passed | Reviewed source matches 239146a; old installed copy matches prior runtime evidence |
| Private backup | Copy old bytes into exclusive directory, compare readback | 0 | passed | Backup path below; no existing backup overwritten |
| Two-file deployment | Write only main.lua/metadata.xml, compare SHA256 readback | 0 | passed | Source/installed hashes below |
| No action authority | action_authorization.json absence guard | 0 | passed | No approval created or copied |
| Launcher preflight | ./Start-Isaac.cmd --preflight-only | 0 | passed | No process launched; ordinary observation configuration passed |
| Final specification check | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 24/24 after deployment documentation |
| Later-frame combat | New live handshake and bounded raw samples | N/A | not_run | Awaiting manual file-2 selection and combat readiness |

## Real game and cleanup

The user explicitly confirmed normal game closure after the proposed deployment
step. The agent did not terminate a run. The deployed files are under the existing
observer directory in the Steam game installation. All other files, saves, Steam
Cloud/options and third-party mods were left untouched. Diagnostics remain off
unless an explicit read-only oracle_probe_v1 attach requests them. Installed
source retains callback_trace=false and no action approval. No diagnostic budget
was consumed and no reconnect or restart was attempted.

Exclusive ignored backup and manifest:
reports/local/later-frame-hp-deployment-f34bebfef42949ac9366d6aefc63e3d0/.
The manifest records UTC time, old/new hashes, process guards and changed files.

Installed/source SHA256:

- main.lua: 10596bb33a8a98c6d0e616700b931b35ec7aca44bb7c5b5cae094ec43ebb7323.
- metadata.xml: cfd4aa96a12d77d1104b69a2fef273f4b8f9a4b0f26b7a6823a0adf274016e65.

Previous hashes retained in private backup:

- main.lua: 9e720026da0bea6ddc7e2f51c1d11683e6807c85568ed31fa859f81932ecac45.
- metadata.xml: 085c10c2a14de0ef7600dcd8195621079e9843dcca3572df1902b66ee98e78b1.

## RL evaluation

Not applicable. No game input, training, reward, progression or achievement claim.

## Limitations and continuation

Self-review checked revision, exact file allowlist, old/new hashes, approval
absence, backup exclusion, process guards and preflight result. Existing offline
983-test / strict 24/24 acceptance is in the preceding review report; no source
changed here, so the full gate was not repeated. Runtime checklist remains
unfinished (13/20 including offline subtask 4.4); no archive.

Next: operator launches normally with --luadebug, confirms file 2 and manual combat
readiness, then one read-only capture with at most 600 snapshots / 120 seconds,
zero reconnects and existing nonrenewable Lua budgets. Do not infer damage or
completion from later-frame HP alone. No forced scenarios or automatic recovery.
