# Evidence: later-frame HP diagnostics (offline)

Review disposition: accepted for offline source only after primary Windows
review and fixes below. The executor submission remains recorded as historical
evidence. Source was not installed or tested in Isaac during review. Subsequent
closed-game deployment is recorded in [deployment evidence](2026-10-18-later-frame-hp-deployment.md);
later-frame runtime sampling remains unfinished.

- Date/time and timezone: 2026-10-18, Mac executor over SMB share (offline authoring only)
- Task ID: later-frame-hp-20261018-01
- Git revision and dirty status: baseline 3d4e203 plus the handoff exception. At start
  AGENTS.md, docs/AGENT_WORKFLOW.md and subagent.md were already modified and
  errors.txt was untracked; all were preserved untouched. Nothing was committed.
- Change scope: active change episode-lifecycle, new offline subtask 4.4. Source
  observer 0.4.5-dev samples raw HP in later distinct game frames. It claims no
  applied damage, settlement, reward, completion or barrier.
- Game/mod/bridge versions: source 0.4.5-dev. Installed 0.4.4-dev untouched and not
  redeployed; installed and source hashes now differ.
- Python/package versions and configuration hash: not applicable on the Mac.
- Scenario, split, seeds, budget, and stop conditions: none (no run).

## Changed files

- `openspec/changes/episode-lifecycle/design.md` (new "Later-frame HP diagnostic
  slice"), `specs/episode-lifecycle/spec.md` (one amended requirement wording, one new
  requirement with seven scenarios), `proposal.md`, `tasks.md` (new subtask 4.4,
  unchecked; whole-task 12/19 count untouched).
- `mod/observer/main.lua`, `mod/observer/metadata.xml` (0.4.5-dev).
- `tests/test_lua_post_update_hp.py` (one test adapted, new tests added).
- `docs/ORACLE_PROBE.md`, `docs/STATUS.md`, `ROADMAP.md`, `README.md`, this report,
  `agent-status.json`. `tests/test_lua_oracle_probe.py` and others were not edited.

## Exact bounds implemented

- At most 3 samples per entry; sample 1 at the first observer post-update callback
  (it may share the attempt frame), samples 2 and 3 only at a game frame strictly
  greater than the previous sample's frame.
- At most 4 observer post-update callbacks after staging, counting unchanged-frame ones.
- At most 16 entries in one list across first and later stages (no detached second
  list); the seventeenth distinct target stops with reason=pending, no eviction.
- Per callback and entry: age+1, then opportunity, then expiry. A fourth callback can
  still sample before expiring; the third sample or an unavailable status finishes an
  entry without an expiry record. Removal is emitted at the next callback without a read.
- Unchanged records: first `post_update_hp`. New: `post_update_hp_later` (sample,
  prior_frame, queued context) and `post_update_hp_expired` (samples, callbacks=4).
- The same 120000 ms / 1024 attempts including stop / 128 labels / 400-byte budgets;
  no renewal. Same fail-closed reentry/fault paths; references dropped on finish,
  removal, expiry, transitions, stop and faults.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Lua syntax | `luac -p mod/observer/main.lua` | 0 | passed | Mac luac 5.5 |
| Production-code simulation | ad hoc Lua 5.5 script that loaded the actual probe section of main.lua with stubs: old first HP then changed later HP, same-frame callbacks, sample-then-expiry on callback 4, three samples without expiry, weak-reference release, 16 entries then 17th stop | 0 | passed | script removed; NOT the pytest suite and not Lua 5.3 |
| Python syntax / line length | `ast.parse`; scan >100 chars on the test file | 0 | passed | none longer than 100 |
| Targeted Lua tests | `pytest tests/test_lua_post_update_hp.py` | - | not_run | no lupa on the Mac |
| Check.ps1 | `./scripts/Check.ps1` | - | not_run | no PowerShell/.venv on the Mac |
| OpenSpec strict | `node node_modules/@fission-ai/openspec/bin/openspec.js validate episode-lifecycle --strict` | 1 | blocked | EPERM opening openspec.js on the SMB share; `validate --all --strict` not run |
| Real-game checks | none | - | not_run | no game access, none claimed |

Design/spec were written before coding; strict validation could not be run before
coding because of the EPERM above, so the ordering rule was only partly met.

## Self-review (separate from independent review)

- Existing tests that depended on first-post release were adapted, not deleted:
  `test_successful_flush_drops_reference_even_without_npc_update` became
  `test_successful_flush_retains_only_inside_window_then_drops_reference`.
  Other existing tests still hold by reading; they were not executed.
- Interpretation choices for review: removal is emitted at the next callback
  regardless of frame; coalesced `attempts` in later records is the count at
  emission; `npc_init` always takes a fresh label, so it never coalesces with an
  existing label (existing behavior, unchanged); the flush is in place rather than
  detached, so entries in flight always count toward the 16.
- New tests were never executed under lupa. Expect possible failures from harness
  details (for example record counts around the budget tests); fix before accepting.
- `sed -i` was used once for the version bump of main.lua/metadata.xml (the other
  edits used the edit tool).
- `ruff format` may reflow the test file.

## Remaining runtime work

All runtime checks: install 0.4.5-dev while the game is closed (separately
authorized), a later-frame combat scenario, and death/revival/floor coverage.
Windows next action: set the documented environment, run the targeted pytest,
`./scripts/Check.ps1` and `./scripts/OpenSpec.ps1 validate --all --strict`.

## Primary Windows review and corrections

Reviewed against task later-frame-hp-20261018-01 and baseline 3d4e203 on
2026-10-18. This is primary-agent review and regression testing, not independent
review or real-game acceptance. Executor code initially passed 88 targeted Lua
cases and 979 total cases, but the full gate failed strict OpenSpec validation:
the new requirement exceeded 500 characters. It was split into sampling and
shared-capacity/cleanup requirements without weakening behavior. The earlier
requirement now explicitly covers the entire bounded sampling window.

A new regression reproduced a correctness bug twice: if the flush-frame getter
reentered a room transition, the old local entry list survived, and a first/later
identity_changed record was emitted with the NEW room number. The frame getter
is now protected by the diagnostic busy guard and pcall; reentry invalidates the
window before old-target output. Six parameterized cases cover room/diagnostic
reentry and frame-read failure both before and after the first sample. The two
literal source-version string tests were replaced by these behavioral cases.
Ruff formatted the updated Python test file.

One intermediate targeted run omitted the documented private TMP/TEMP and failed
at pytest session cleanup with WinError 5 on the pre-existing global pytest-current
junction. This is not counted as a pass. The junction was not modified; rerunning
with the existing private temp directory completed successfully.

| Final check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Targeted production Lua | .venv/Scripts/python.exe -m pytest tests/test_lua_post_update_hp.py tests/test_lua_oracle_probe.py -q | 0 | passed | 92 tests, zero skips, Lua 5.3 harness |
| Full Windows gate | ./scripts/Check.ps1 with environment from subagent.md | 0 | passed | 983 tests, zero skips; Ruff, 84 formatted files, mypy 37 sources, pip consistency, OpenSpec 24/24 |
| Final strict validation | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 24/24 after review documentation |
| Whitespace review | git diff --check | 0 | passed | No whitespace errors |
| Installed files readback | SHA256 of installed main.lua and metadata.xml | 0 | passed | Historical 0.4.4-dev hashes unchanged; no deployment |
| New source runtime | No launch, attach, actions or installation | N/A | not_run | All new game acceptance remains unfinished |

### Verification scope and specification mapping

| Dimension | Reviewed result |
|---|---|
| Completeness | Original tasks remain 12/19; offline 4.4 accepted separately, so actual checklist is 13/20. Whole change incomplete; no archive. |
| Correctness | Two added later-frame requirements and eight scenarios plus the amended deferred-window requirement map to production Lua tests. Broader native-step/lifecycle runtime scenarios remain not verified. |
| Coherence | Three opportunities, four callbacks, one 16-entry list, shared budgets, no wire/outcome/control additions; frame-read invalidation correction now matches cleanup design. |

Scenario evidence: old-first/later-changed, same-frame/expiry and three-sample
completion tests cover sampling; removal/missing/identity tests cover unavailable
facts; combined-capacity tests cover 16/17; cleanup/failure tests cover lifecycle
and fault behavior; the new flush-frame regression covers context invalidation.
All are fabricated callback schedules, not engine ordering proof.

Installed hashes remain:

- main.lua: 9e720026da0bea6ddc7e2f51c1d11683e6807c85568ed31fa859f81932ecac45.
- metadata.xml: 085c10c2a14de0ef7600dcd8195621079e9843dcca3572df1902b66ee98e78b1.

Reviewed source hashes:

- main.lua: 10596bb33a8a98c6d0e616700b931b35ec7aca44bb7c5b5cae094ec43ebb7323.
- metadata.xml: cfd4aa96a12d77d1104b69a2fef273f4b8f9a4b0f26b7a6823a0adf274016e65.

The extra subagent_report.md is retained as the executor's user-requested summary;
agent-status.json remains ignored and executor-owned, not an acceptance verdict.
No raw logs, saves, backups, approval, dependency/lock changes or errors.txt are
included. Next action: confirm the game is closed before any deployment, then
prepare one bounded manual-combat check. No additional executor assignment or
heartbeat activation is authorized by accepting this task.
