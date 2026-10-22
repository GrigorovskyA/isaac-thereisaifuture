# Evidence: restart-after-game-over

- Date/time and timezone: 2026-10-17, Europe/Amsterdam. Offline implementation at 17:28 CEST; real optional-mode probe 18:24:49.432–18:27:37.479 CEST.
- Git revision and dirty status: implementation b48fde9, closed-game deployment record 6db4311, initial real connection record 19e327f; final acceptance docs dirty during verification. The containing final commit identifies this report snapshot.
- Scope/acceptance: explicit optional death-restart mode, default observation unchanged. Closed-game deployment, real natural death, exactly one new run, matching character, responsive disconnect and full offline checks required. All six tracked tasks now complete.
- Game/mod/bridge: fresh native log reports Repentance+ v1.9.7.17.J460; Steam build 22878971 from audited manifest. Actual handshake: observer 0.2.0, Lua 5.3, extender absent, protocol/schema 1. Wire game version/build stay null with unavailable provenance; not fabricated detection.
- Python/packages/configuration: Python 3.12.14, pytest 9.1.1, unchanged production dependencies. Test-only isolated Lupa 2.6/lua53 and installed JSON source. Reviewed artifact SHA-256 values are in docs/DEATH_RESTART.md and matched the deployed bytes. Limits: 3 attempts, 600000 ms lease, 1500 ms delay, 5000 ms stale/confirmation deadlines.
- Scenario/budget/stop: user manually launched and selected file 2, continuing the ordinary run under narrow explicit lifecycle authorization. No deliberately caused death, character input, live-run reset, save edits, spawning, Cloud changes or RL. Probe budget 660 seconds; stop after new epoch plus 30 further snapshots, deadline or fault. Actual probe stopped after 168.046 seconds, 832 snapshots, exit 0.

## Results

Commands run from repository root. Lua tests used isolated PYTHONPATH and ISAAC_JSON_LUA; raw logs, test probe and backups remain in ignored reports/local.

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Full offline gates | .\scripts\Check.ps1 with Lua test environment | 0 | passed | 114 tests, no skips: 48 Python protocol/peer, 39 Lua stubs, 25 launcher, 2 diagnostics; Ruff, format, mypy, pip and strict OpenSpec |
| Delta validation | .\scripts\OpenSpec.ps1 validate restart-after-game-over --strict | 0 | passed | Proposal/design/two delta specs/tasks valid |
| Capability/default contract | Simulated peer and Lua tests | 0 | passed | Missing optional support rejected; absent operator slot confirmation exits 2 before binding; ordinary capabilities never authorize restart |
| Death and cancellation guards | Simulated Lua behavioral suite | 0 | passed | Delayed single fixed restart; victory, revival, co-op, missing player/API fault, exit, disconnect, unload, changed epoch, expiry/staleness cancel; death state alone does nothing |
| Limits/uncertain outcomes | Simulated Lua behavioral suite | 0 | passed | Reconnect never renews lease/count; dispatch fault, confirmation timeout/continued start disable retries; partial ack never arms |
| Native API discovery | Installed enums.lua and primary API references | 0 | passed | Native IDs 15/16; documentation supports callback/restart design, not used alone as acceptance |
| Closed-game deployment | Task 3.1; byte/hash checks; launcher --preflight-only | 0 | passed | Two process-absence checks, byte-verified private backups, both deployed hashes match; no process launched by preflight |
| Requested focus-loss setting | Closed-game options.ini single-key change/readback | 0 | passed | PauseOnFocusLost 1 -> 0, every other key/value unchanged; no save/Cloud edit |
| Background runtime | User focus-loss confirmation plus real timestamped snapshots | 0 | passed | 150 active samples over 29.869 seconds, frames 30352 -> 31248, no adjacent equal frame; user confirmed 15 seconds unfocused |
| Default 0.2.0 observation | CLI observe --samples 30 --accept-timeout 20 | 0 | passed | Session d1bebff969454ea38eccca616d7adce8, frames 27381 -> 27555; normal consumer cleanup |
| Real death-to-new-run | Finite local optional-mode probe plus native diagnostics | 0 | passed | Exactly one scheduled event, dispatch attempt 1, confirmation epoch 1 -> 2; fresh session and advancing new-run frames |
| User correlation/cleanup | User report, process response, listener/native readback | 0 | passed | Automatic new run, same character, manual movement works and no hangs after probe stopped; game Responding=True, no port-9528 listener, native Peer disconnected |
| General campaign/startup/RL | Deferred/out of scope | N/A | not_run | No automatic file selection, movement/shooting, training or Dead God claim |

An early simulated transition assertion incorrectly expected new snapshots before the restart-closed socket reconnected. It was corrected to require fresh negotiation first; no production guard was weakened. Initial Ruff formatting findings were fixed before passing full checks. One combined installed-source search included a nonexistent lowercase luadocs directory and returned 2, while enums.lua matched; no compatibility conclusion relied on the missing directory.

## Real game

The user confirmed normal exit before deployment; prior observer files and options.ini were backed up locally with byte/hash checks. 0.2.0 replaced only the two approved mod files. At separate user request, only the focus-loss option changed. User then manually launched, selected file 2 and reported being in the room. Slot identity is operator-confirmed, not attested by the wire. This is a narrow ordinary-profile exception for after-death lifecycle; it does not establish isolated training state or permit general actions.

Default observation passed first. Optional-mode session cb0a114400484f12847ba4d2cd23ee7a then armed in the actual native log. The trace contains exactly one scheduled event and exactly one dispatch for epoch 1, attempt 1, followed by `Death restart confirmed old_epoch=1 new_epoch=2`; no death-restart fault diagnostic occurred. The expected restart-related peer close caused one bounded reconnect into session c4aa06bb70494291885b94db32a16b91. Transport failure alone was never classified as death.

| Epoch | Samples | First/last engine frame | Character type | First raw red health |
|---|---|---|---|---|
| 1 | 801 | 28581 / 33318 | 0 | 4 half-hearts, maximum 8 |
| 2 | 31 | 6 / 187 | 0 | 6 half-hearts, maximum 6 |

First epoch-2 snapshot: 18:27:31.444 CEST. Probe ended at 18:27:37.479 CEST with sockets closed, no listener left and game still open/responding. User confirmed the natural death led to an automatic new run, same character, working manual control and no visible hangs after shutdown. No screenshots or desktop inputs were used. Some samples around death were paused; the background assertion is limited to its explicitly corroborated active interval, not the entire probe.

Private evidence consists of timestamped restart.jsonl, summary.json, default read-only snapshots/errors and filtered observer-native-diagnostics.txt. No raw game log, save, credentials or personal installation path is committed.

## RL evaluation

Not applicable: no policy, rewards, learning inputs, training or campaign experiment.

## Separate self-review and OpenSpec verification

Used openspec-verify-change as the same single agent, reviewing proposal/design/deltas/tasks against code, tests, real trace and user correlation. This is a self-review, not independent review.

| Dimension | Result |
|---|---|
| Completeness | All 6/6 tasks complete, including closed-game deployment and natural-death acceptance |
| Correctness | Three added requirements map to opt-in CLI/handshake and guarded lifecycle; modified negotiation preserves prior scenarios; 114 offline tests plus declared real case passed |
| Coherence | Default remains read-only, no post-hello arbitrary command endpoint, no new dependency, no application automation or player controls; fixed limits and diagnostics follow design |

No critical issues or warnings within the declared acceptance scope. Offline scenario coverage is complete; the required real natural-death case passed. Additional live edge cases below remain outside this first acceptance scope, not simulated successes promoted to integration evidence. Main-spec sync/archive and post-archive strict validation are recorded in the final completion section.

## Limitations and continuation

Accepted runtime case: one normal solo character-type-0 natural death on J460, operator-selected file 2. Special characters, actual revival/ending edge cases, challenge/daily/co-op behavior, automated slot attestation, achievement eligibility, profile isolation and long-session reliability remain unverified. A single successful restart is not a universal compatibility or learning claim.

The probe is stopped. Another session requires an explicitly opted-in connected consumer, with file 2 still manually selected; reconnecting does not renew the per-mod-load lease or attempt count. Start-Death-Restart.cmd is the attach entry point. Initial application launch/file selection stay manual. General safe actions and training remain gated on separate isolation and eligibility work. Raw evidence and backups remain excluded from Git.

## Final completion

OpenSpec reported 6/6 complete tasks, all four planning artifacts done. Archive
command `.\scripts\OpenSpec.ps1 archive restart-after-game-over --yes` exited 0,
adding three post-death-restart requirements and modifying one game-observation
negotiation requirement. Archive:
`openspec/changes/archive/2026-10-17-restart-after-game-over`.
A post-sync content comparison verified the new purpose/requirements match the
delta, the existing purpose and all unrelated requirements are unchanged, and no
delta headers leaked into main specs. Post-archive `validate --all --strict`
passed all six main specs, exit 0. No active changes remain. Final project commit
and push exclude local probe code, raw logs, backups, user options and saves.
