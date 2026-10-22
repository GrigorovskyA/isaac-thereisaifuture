# Evidence: lua-step-evidence-20261018-01 (episode-lifecycle subtask 3.10)

- Date/time and timezone: 2026-10-18, Mac executor (offline).
- Git revision and dirty status: baseline 51fb5cc (HEAD 9a92e54); working tree modified, nothing committed; `errors.txt` untracked and untouched.
- Change scope: bounded producer-side Lua evidence hooks in the default-off `callback_trace`. Acceptance: criteria in `openspec/changes/episode-lifecycle` design/spec 3.10 ("Bounded Lua step evidence").
- Game/mod versions: source 0.4.6-dev (`main.lua`, `metadata.xml`); installed stays 0.4.5-dev (untouched, source/installed mismatch is deliberate). No game ran.
- Python/Lua: Python 3.11 + test-only lupa (Lua 5.3) in /tmp; a /tmp JSON shim stood in for the game json.lua.

## Changed files

`mod/observer/main.lua`, `mod/observer/metadata.xml`, `tests/test_lua_step_evidence.py` (new, 24 cases), `tests/test_lua_callback_trace.py` (one compatibility assertion: update records now include `hold_update`), `docs/NATIVE_STEP_EVIDENCE.md` (new), `docs/NATIVE_EPISODE_PROTOCOL.md`, `docs/STATUS.md`, `ROADMAP.md`, `README.md`, episode-lifecycle `proposal/design/tasks/spec`, `subagent_report.md`, `agent-status.json`.

## Fields, hooks and bounds

See `docs/NATIVE_STEP_EVIDENCE.md`. `action_accepted` (+`until`, `deadline_ms`), `hold_update` (once per frame: `hold_seq`, `left`, `upd_since`), `release` (+`hold_seq` from the cleared hold, `frame_due`, `wall_due`, `left`, reason cap 40), `release_update` and `release_input` (one pending release, next post-update and next nil-override player movement/shoot query). Trace limits unchanged (10 s, 512 attempts incl. stop, 300 bytes, one window). A line over 300 bytes now stops with `reason=line_limit` instead of truncating (measured valid maximum 263 bytes). Cleanup of scalars on stop/fault, accepted action, room, level, game start/end, disconnect, exit/unload. Wire, validation, acks, input returns, release/watchdog untouched. Task 3.10 added unchecked (14/22); 3.6, 3.8, 4.1-4.3, 5.1, 5.2 not marked.

## Results

| Check | Command | Exit | Status | Evidence |
|---|---|---|---|---|
| Lua syntax | `luac -p mod/observer/main.lua` | 0 | passed | clean |
| Lua suites on /tmp copy (step evidence, callback trace, actions, observer) | `PYTHONPATH=src:tests:<lupa> ISAAC_JSON_LUA=<shim> python -m pytest -p no:cacheprovider -q ...` | 0 | passed | 155 passed, 0 skipped |
| Wider suite on /tmp copy | same, `tests --continue-on-collection-errors` | 1 | not accepted | 1092 passed; 16 failures and 6 collection errors are environmental (no gymnasium, missing data dirs, JSON-shim empty-array encoding); `test_lua_entities` 2 failures reproduce on baseline main.lua |
| Pinned Windows pytest, `./scripts/Check.ps1`, ruff, mypy | not available on Mac | - | not_run | primary must run |
| `./scripts/OpenSpec.ps1 validate --all --strict` | node package unreadable on SMB (EPERM) | - | blocked | primary must run; spec/design written before code |
| Real-game probe, deployment, preflight | - | - | not_run | no game, approval or install touched |

## Spec mapping

Acceptance/endpoint fields, once-per-frame post-update, original hold identity, wall vs frame due flags: step-evidence tests. Pending release (one, eviction by new action, context discard, no false confirmation, non-movement/foreign input ignored): pending/context tests. Off mode, logger/DebugString failure, re-entrant logger, budget stop, line limit, disconnect: bounds and failure tests. Existing trace/action/observer assertions kept.

## Limitations and continuation

- Bridge-side clearing is not physical neutrality; `override=nil` is not neutral engine input.
- Post-update and input-query records are not consumed updates; no READY/seal/watermark exists.
- Wall vs frame expiry is reported as two observed conditions; both true is unattributable.
- Mac ran Python 3.11 with a patched copy and a shim JSON (not the pinned 3.12 / game json.lua); Windows rerun required.
- Live acceptance needs a reviewed closed-game deploy of 0.4.6-dev plus a separate preflight; a future probe is one short action, release, cleanup and must not force death/reset/restart.
- Diff self-review done against the spec; no independent review claimed. Next action: primary review and Windows gates.
- Process note: some docs/appends were written via shell instead of the edit tools.

## Primary review (macOS, 2026-10-18)

- Diff reviewed against the 3.10 design/spec. Fix: `release_superseded` now formats `hold_seq`/`by_seq` through `trace_num` and fails closed on invalid scalars.
- Note: the `trace_release` epoch/visit mismatch branch is defensive; every `release()` call precedes epoch/visit changes in current callbacks.
- Mixed CRLF/LF lines from shell appends were normalized in the working tree; Git stores LF per `.gitattributes`.
- `./scripts/check.sh` (Python 3.12 venv outside the share, lupa, test-only JSON shim): exit 0; ruff, format, mypy `--platform win32`, 1167 passed / 0 skipped, `uv pip check`, OpenSpec strict 24/24. Status: passed (pre-check).
- Windows `./scripts/Check.ps1` with the game json.lua: not_run. Real-game probe: not_run.


## Subsequent primary Windows review

The Windows review corrected reentry/context handling, proved logger failures at
all five record types, added explicit supersession and monotonic frame coverage,
and preserved the Mac trace_num correction. Original targeted Lua suites passed
165 cases and the pre-live-loop source gate passed 1167 cases. Subsequent 0.5.0-dev
additions were reviewed separately; final Windows gate passed 1224 cases and strict
25/25. See reports/2026-10-18-windows-live-review.md. No installed file, approval or
real game was changed and the new diagnostic runtime probe remains not_run.
