# Evidence: ordinary-profile action authorization

- Date/time and timezone: 2026-10-17, Europe/Amsterdam (CEST).
- Git revision and dirty status: started clean at 90dc71b; scoped implementation/docs/tests dirty during verification. The containing commit identifies this follow-up.
- Change scope and acceptance criteria: direct user permission to enable movement/shooting on the ordinary profile and retain that permission for future bounded tests. Amend OpenSpec explicitly, add finite local authority and native evidence, install reviewed 0.3.1 while closed, preserve default observation and existing reset limits. Live acceptance remains 50 actual sequences plus failure cleanup.
- Game/mod/bridge versions: game historically J460/build 22878971; source/installed adapter 0.3.1, protocol/schema 1. No actual 0.3.1 game handshake occurred.
- Python/package versions and configuration hash: Python 3.12.14, unchanged production dependencies. Isolated Lupa 2.6/lua53 and installed JSON source reused. SHA-256 main.lua `43d2bc10e63b96d86cefa57630528040e0017674a08d4b57b23a683628879efc`, metadata.xml `11d0659831cd4ffec75453f6db13261a02a05f75160501ee27133a973ecffda9`. Source authority nil; fixed private approval path, <=2048-byte record, <=30-minute expiry, 120000-ms per-mod-load lease. Existing 250-ms/15-frame hold and 500-ms heartbeat limits unchanged.
- Scenario, split, seeds, budget and stop conditions: offline simulated callbacks and peers, closed-game two-file deployment. User must manually launch/select and confirm file 2/active safe room before any input. Finite probe <=50 sequences / 120 seconds; stop on pause, changed room/epoch/health, boundary proximity, protocol/transport errors or interruption. No RL/seeds/splits.

## Authorization and changed prerequisite

The user explicitly approved movement and shooting directly in their ordinary
profile and asked to remember that for future checks. This is a new direct
instruction superseding the previous observation/restart-only exception and the
isolation-only action-test prerequisite. It is recorded as ordinary_profile_exception,
not verified isolation. Do not ask for that same ordinary-profile permission again.
A small requested memory-update note was saved through the permitted memory
extension mechanism; no existing memory registry was edited.

The permission does not authorize training, save editing/restoration, Steam Cloud
changes, REPENTOGON, forced run resets, reset-budget changes, automatic launch or
selection, unbounded supervision or achievement claims. Current instance, game
epoch and manual active-slot confirmation remain required. No answer to the
pending current-slot/room question has arrived; the game is closed. No private
approval file was activated and no gameplay input was sent.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Scope and permission | Direct user instruction; amended proposal/design/native and game-environment deltas | N/A | passed | Explicit exception recorded without claiming isolation; training gate retained |
| Full offline gates | .\scripts\Check.ps1 with isolated Lua PYTHONPATH and ISAAC_JSON_LUA | 0 | passed | 241 tests, no skips; Ruff/format/mypy/pip consistency and seven strict OpenSpec items |
| Authority modes and expiry | Lua ordinary/isolated, invalid mode, expired/future/bool approval tests; Python expired approval tests | 0 | passed | Missing/invalid authority cannot enable input; client closes on local expiry |
| Lease and reconnect | Simulated Lua per-mod-load lease test | 0 | passed | Reconnect at 100 seconds does not extend initial 120-second authority |
| Private approval loading | Simulated bounded read-only io.open, absence then creation, cached successful record | 0 | passed | Exact fixed path and bounded read; no save writes; negative cache does not prevent post-confirmation activation |
| Native physical evidence plumbing | Installed MC_POST_FIRE_TEAR=61 enum and primary callback docs; simulated player-tear callback | 0 | passed | Logs correlate actual callback tear velocity with session/epoch/command/frame/time; <=4 inspected tears per action, duplicate log deduplication |
| Finite probe | action_probe tests and source self-review | 0 | passed | Invalid budgets/expired approval fail before connecting; ten declared cases repeated <=5 times; no launch/reset and unconditional context cleanup |
| Deployment | Process absence checks, verified backup/copy/hash of main.lua/metadata.xml | 0 | passed | 0.3.0 prior files kept under ignored reports/local; installed 0.3.1 hashes match above; game remains closed |
| Launch preflight | python -m isaac_threrisaifuture.launcher --preflight-only | 0 | passed | No process launched or configuration changed |
| Strict OpenSpec and diff | OpenSpec.ps1 validate bridge-safe-actions --strict; validate --all --strict; git diff --check | 0 | passed | New game-environment delta explicitly documents exception; no silent isolation claim |
| Current process/slot/room confirmation | Task 1.3 | N/A | blocked | Await manual launch, current slot-2/room confirmation and real handshake/epoch; profile permission itself is already granted |
| Real movement/shooting/release | Task 3.2 | N/A | not_run | 0/50; no live commands, tear, displacement or failure-release acceptance yet |

Initial offline checks found formatting/line-length issues and a nullable-player
mypy error in the new probe; corrected before passing full gates. Self-review
also removed an extra consecutive snapshot wait that could unnecessarily approach
the heartbeat deadline and allowed missing local approval to be supplied after
read-only confirmation without reloading the mod. No safety limit was relaxed.

## Real game

No real-game action test took place. Isaac process absence was checked before
and during deployment. Only the two existing observer artifacts were backed up
and replaced. No ordinary save, options, mod-data, Cloud setting or Steam setting
was edited. No private action authority file exists yet. This is installation and
offline plumbing evidence only, not J460 input/effects/cleanup acceptance.

## RL evaluation

Not applicable. No policy, training, reward, Gymnasium or campaign change.

## Separate self-review / OpenSpec verification

One agent reviewed deltas/tasks against Lua/Python/tests and deployment; no
independent reviewer or subagent. Explicit profile authority maps to local
approval validation and unchanged read-only negotiation; identity/expiry/cleanup
map to existing command tests plus lease/expiry tests; native evidence maps to
MC_POST_FIRE_TEAR and bounded release diagnostics. Probe semantics retain manual
startup/selection and distinguish command completion from physical acceptance.

Task completeness: 6/8 complete. Task 1.3 still needs the actual current instance/
operator-confirmed slot/room and action approval; task 3.2 still needs all actual
movement/shooting/failure-cleanup evidence. These are critical acceptance gaps,
not offline test failures. Physical scenario coverage, native API behavior in
J460, local approval file access in the actual game and real release timing are
not verified because no game session occurred. Do not archive.

## Limitations and continuation

Slot identity will be operator-confirmed for this supervised check, not native
automatic attestation. Ordinary-profile permission is not isolation. Local same-user
loopback peers remain unauthenticated. A record is cached once per mod load and
its lease cannot be renewed by reconnect; expired authority needs a new manually
started instance, without an automatic supervisor. Special weapons cannot be
counted as tear evidence. Default observation/restart behavior and limits remain.

Next: user manually launches/selects file 2 and confirms an active safe room.
Read actual process/handshake/epoch, create the private ordinary-profile approval,
run the finite probe, review native tear/position effects, then perform controlled
disconnect/Python-failure/stall cleanup. Delete the private approval afterward.
Do not request ordinary-profile movement/shooting permission again.
