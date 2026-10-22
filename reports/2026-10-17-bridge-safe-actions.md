# Evidence: bridge-safe-actions

- Date/time and timezone: 2026-10-17, Europe/Amsterdam (CEST, UTC+02:00); offline implementation and checks during this session.
- Git revision and dirty status: started clean at 7691d9b on main, matching the requested reference. This report belongs to the containing implementation commit; only scoped project changes were dirty during verification.
- Change scope and acceptance criteria: item 03; proposal, two deltas, design, seven tasks, Lua/Python action contract, tests, protocol and prerequisite plan. Offline checks must pass; live acceptance additionally requires verified isolated profile/slot/instance authority, 50 controlled sequences and actual release evidence. Live tasks remain incomplete.
- Game/mod/bridge versions: historical accepted J460 / Steam build 22878971 / Lua 5.3, installed adapter 0.2.0. No new game handshake or version probe was performed. Source 0.3.0 is not deployed. Protocol/schema remain 1; optional safe_actions_v1 gate is nil.
- Python/package versions and configuration hash: Python 3.12.14, pytest 9.1.1, pydantic 2.14.1, unchanged production dependencies/locks. Existing isolated test-only Lupa 2.6 / lua53 and installed json.lua reused. Config embedded in main.lua: 127.0.0.1:9528, 1024-byte commands, 16384-byte output, <=4096 bytes I/O and one command per render callback, 15-frame freshness, action <=15 frames and 250 ms, heartbeat 500 ms. SHA-256 main.lua: `9c3e788833423a3bd9a77a84f86ee1ace0b17780d053c5b123bd0f00c45d9728`; metadata.xml: `4710d0f08d4c77336522f374e20542ff90851a475137b5e130542ff7df1703b2`. Both source artifacts normalized to LF before hashing.
- Scenario, split, seeds, budget, stop: offline simulated Isaac callbacks/socket objects and actual local TCP with fake Lua peers only. No game seed, RL split or experiment. Stop on check failure; no launch, save selection, reset, training, screen capture or desktop input. Conditional future live budget is 50 sequences / 120 seconds with immediate stop on fault; see SAFE_ACTIONS.md.

## Results

Commands are from repository root. For Lua checks, existing isolated Lupa is on
PYTHONPATH and ISAAC_JSON_LUA points to the installed resources/scripts/json.lua.
These environment variables are test tooling only, not game changes. No install
or dependency update was needed. They must be set when reproducing the no-skip
result; otherwise the optional Lua harness explicitly skips and does not pass.

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Starting reference | git status --short; git log -5 --oneline | 0 | passed | Clean main at 7691d9b; no unrelated changes to preserve |
| Context/prerequisite audit | Read required guides, main specs and archived/runtime evidence; inspect native enums/LuaDocs | 0 | passed | Existing ordinary-profile exception is limited; slot API/isolation not established; exact blockers below |
| Process inventory | Get-Process isaac-ng | 0 | passed | Existing process present, started 18:23 CEST; left running and never used as a test episode |
| API source shape | Installed enums.lua; primary callback/InputHook/ButtonAction documentation | 0 | passed | Native MC_INPUT_ACTION=13, button 0..7 and typed hooks; source evidence only, no native runtime claim |
| Proposal and deltas | .\scripts\OpenSpec.ps1 validate bridge-safe-actions --strict | 0 | passed | Six ADDED native requirements and one MODIFIED negotiation requirement; no removed/renamed behavior |
| Full offline gates | .\scripts\Check.ps1 with Lua environment | 0 | passed | 224 tests, no skips: 45 Python actions, 65 Lua actions and all 114 existing tests; Ruff, format, strict mypy, pip consistency, seven strict OpenSpec items |
| Native action semantics | tests/test_lua_actions.py | 0 | passed | Independent cardinal/none mapping, correct hook types, player pointer restriction, neutral/release, frame/wall expiry checked inside input callback without render/update |
| Stale commands and faults | Lua command tests and tests/test_actions.py | 0 | passed | Wrong sessions/epochs/rooms/frames, duplicate sequence, malformed/version/extra/duplicate fields, partial input, output stalls, invalid API and mismatched acknowledgements fail closed |
| Heartbeat/reconnect/cleanup | Lua and real localhost simulated peers | 0 | passed | Heartbeat cannot extend hold; expiry closes connection; reconnect starts sequence at one/new session/no hold; disconnect, silent Python, pause/death/transitions/exit/unload/fault clear inputs |
| Local gate | Missing/blank evidence, wrong slot/epoch, incompatible modes, partial hello ack | 0 | passed | No action capability or input authority without valid local opt-in; Python cannot populate Lua approval |
| Installed artifact readback | Get-FileHash on installed two adapter files | 0 | passed | Existing 0.2.0 SHA-256 values match DEATH_RESTART.md; no deployment occurred |
| Diff/privacy self-review | git diff --check; source/spec/test review; explicit staging review | 0 | passed | Only project source/docs/spec/tests; private logs, saves, backups and runtime config excluded |
| Approved isolation/slot/instance/runtime authority | Task 1.3 | N/A | blocked | No approved isolated profile/restoration/write set or active-slot attestation; no specific movement/shooting runtime authorization for such a profile |
| Closed-game 0.3.0 deployment | Task 3.2 prerequisite | N/A | blocked | Game is running; no approved action-profile artifact deployment; installed adapter untouched |
| 50 actual action sequences and real release measurements | Task 3.2 | N/A | blocked | 0/50; no movement, shot, release, failure or reconnect acceptance with real native inputs |
| RL/Smoke-RL | Outside scope | N/A | not_run | No learning, environment or production dependency change |

Initial delta validation exposed two long-requirement warnings; requirements were
split without weakening behavior and strict validation then passed. An early Lua
run exposed an oversized partial-input boundary regression and a harness call
that raised before the tested callback. Fixed the production byte bound and
passed a stable simulated entity to the fault test; no requirement was relaxed.
Diff review also corrected Windows default-codepage corruption in existing
documentation before staging, preserving original Unicode lines.
Self-review added blank-evidence rejection, explicit heartbeat connection closure,
cardinal mapping, partial-ack, frame freshness and backpressure cases. Full gates
were rerun after these code changes.

## Real game

**No live action test took place.** No new session/epoch/frame/action IDs or
physical effects exist for this change. The existing process/run was not
interrupted. No installed mod, options, PauseOnFocusLost, save, Steam Cloud,
Steam setting or REPENTOGON was changed. Accepted observation, background and
one natural-death restart tasks were not repeated or reimplemented.

Installed readback: main.lua `c53efb0e735c191ac1b72d7ad9c93cf8e03808c858d719e3b7f88cfe98245b09`,
metadata.xml `25c4980fd19565489ba4f92b91008bafc89d4ddfe3b05f104cc5ee1aaefaa59d`.
These match the existing 0.2.0 deployment record, not the new source hashes above.
Default attach observation/restart is compatible. The launcher compares deployed
and source hashes and will refuse the 0.3.0 mismatch until authorized closed-game
deployment; the check was not bypassed.

## RL evaluation

Not applicable. No policy, reward, training, Gymnasium, campaign, save progression
or achievement eligibility claim is made.

## Separate self-review and OpenSpec verification

One implementing agent used openspec-verify-change for a separate review pass.
This is self-review, not an independent review. Reviewed all change artifacts,
Lua/Python code, tests, baseline negotiation/lifecycle requirements and diff.

| Dimension | Result |
|---|---|
| Completeness | 5/7 tasks complete; tasks 1.3 and 3.2 blocked and incomplete |
| Spec coverage / implementation mapping | All 7 added/modified requirements mapped below; no removed/renamed requirements. Native live behavior and profile/slot verification not verified because prerequisites are absent |
| Scenario coverage | Offline scenarios covered by simulated tests; required actual 50-sequence/failure cases not verified (no isolated authorized runtime) |
| Design adherence | Optional capability, local gate, native input, synchronous client, conservative identity and fixed bounds implemented; runtime migration not performed |
| Code pattern consistency | Existing strict models, socket errors, bounded callbacks and LF Lua/XML followed; no dependency, launcher or lifecycle limit change |

Requirement mapping:

- Explicit isolated authority: main.lua action_authorized/hello (lines 31/92),
  ActionApproval (actions.py:29), local gate tests; operational isolation/slot
  evidence remains unverified, so the source gate stays disabled.
- Bounded independent native actions: main.lua MC_INPUT_ACTION (line 427), command
  ack and Command/ActionClient (actions.py:40/82); native mapping tests. Actual
  movement and shooting remain unverified.
- Strict command identity: main.lua command (line 178), Command and ack validation
  (actions.py:40/113), shared snapshot ordering (observer_client.py:181); replay,
  wrong-identity and strict parsing tests.
- Expiry and cleanup: action_guard (main.lua:45), release and input guard; Lua
  frame/wall/heartbeat, neutral/release, no-render and backpressure tests.
- Lifecycle cleanup: callbacks (main.lua:378 onward), close and Python error/context
  cleanup; transition/fault/reconnect/socket tests. Physical real cleanup unverified.
- Separate offline/runtime acceptance: tasks 1.3/3.2 left unchecked, this report,
  SAFE_ACTIONS prerequisite/live plan, STATUS and ROADMAP.
- Modified negotiation: main.lua hello and ObserverConfig/accept; old observer,
  restart and launcher tests all retained/passed; old main specs remain unsynced
  until actual acceptance and archive.

Critical unresolved acceptance issues: task 1.3 needs approved isolation,
restoration/write-set evidence and actual current-instance/active-slot identity
plus specific runtime authorization. Task 3.2 then needs reviewed deployment and
50 actual sequences/failure cleanup evidence. **Do not archive.** No additional
unresolved offline code defect was identified in this self-review. Live behavior,
physical cleanup, isolation/slot validation and migration were skipped for these
reasons and are not scored as passing. No independent review was performed.

## Limitations and continuation

The local record is a manual approval gate, not a slot detector, authenticated
operator identity or automated proof of isolation. It must refer to current
instance/mod-load evidence and must not be reused across launches. No supported
slot query/profile-redirection API was established. Shared same-user loopback
peers are not authenticated. A suspended process cannot run a watchdog; the
input-time guard prevents an expired override on its next poll. Existing native
manual key state, projectile persistence and character inertia are not reset by
release. Continuous shooting hook semantics, other mods, J460 callbacks, special
characters and real-time latency all require actual evidence.

Next action: review the concrete isolation/slot plan in docs/SAFE_ACTIONS.md and
resolve task 1.3 without forbidden Cloud/save/runtime changes. If no acceptable
profile/identity method is available under those constraints, keep blocked.
Once resolved, obtain action-time authorization for reviewed hashes/destination
and the finite experiment, keep launch/selection manual and execute task 3.2.
Commit/push this offline implementation and keep bridge-safe-actions active.
