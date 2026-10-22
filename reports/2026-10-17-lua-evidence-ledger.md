# Evidence: lua-evidence-ledger-01

- Date/time and timezone: 2026-10-17, Mac executor (offline authoring only)
- Git revision and dirty status: on top of ef4f77a; three new files, uncommitted
- Change scope and acceptance criteria: standalone passive Lua timing ledger per the
  frozen design section "passive Lua timing ledger (unshipped)". Facts only: no engine,
  clock, socket, logger or filesystem calls, no wire messages, no completed/applied
  status, no input authority, no production import, not a GameBackend. This is not
  completion of tasks 3.6/3.8.
- Game/mod/bridge versions: not applicable; observer artifacts and hashes untouched.
- Python/package versions and configuration hash: not applicable on the Mac.
- Scenario, split, seeds, budget, and stop conditions: not applicable (no run).

## Files

- `mod/experimental/native_step_ledger.lua` (new, standalone).
- `tests/test_lua_native_step_ledger.py` (new, only this module is loaded into
  `lupa.lua53`; skipped when lupa is absent, no Isaac globals or harness).
- This report.

## Behavior implemented

- API: `Ledger.new(sequence, accepted_frame, requested_frames)`, and methods
  `observe_query`, `observe_post_update`, `close`, `snapshot` (called with `:`).
- Counters are finite integer-valued Lua numbers in 0..2^53-1 (sequence >= 1, repeat
  1..15); booleans, strings, fractions, nan and inf fail; a constructor whose end frame
  exceeds the bound fails. Hooks are exactly the three known names; button is an
  integer 0..7; GET_ACTION_VALUE takes a finite number 0..1, the others a boolean.
  Invalid arguments error before any mutation and never spend the budget.
- Query window `[accepted, accepted + repeat)`: at most 15 slots, each with a fixed
  3x8 cell grid (count, first/last update, first/last value); duplicates only raise
  counts. Out-of-window queries and queries after close increment separate dropped
  counters and return false (the closed state takes precedence).
- Post-update window includes the endpoint: at most 16 slots with count, first/last
  update and after-release count; out-of-window updates increment a dropped counter.
- `close` requires a nonblank reason of at most 64 bytes without control characters,
  keeps the first release (reason, frame, update) and returns true once, false after.
  The reason is opaque; no expiry kind is inferred. Release does not seal the endpoint.
- 4096-call budget over valid query/post-update calls, dropped ones included; the 4097th
  errors without mutation. `close` and `snapshot` neither spend nor renew it.
- `snapshot` returns an independent deep copy (limits, calls, dropped, windows with only
  observed cells, release); no immutability is claimed. Instances share no state.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Lua syntax | `luac -p mod/experimental/native_step_ledger.lua` | 0 | passed | Mac luac |
| Ad hoc Lua 5.5 sanity script | window, close, endpoint, budget, invalid arguments (inline, no file written) | 0 | passed | not the pytest suite; Lua 5.5, not 5.3 |
| Python syntax / line length | `ast.parse`; scan for >100 characters | 0 | passed | none longer than 100 |
| Ledger tests | `pytest tests/test_lua_native_step_ledger.py` | - | not_run | Mac has no lupa; run on Windows |
| ruff/format/mypy/Check.ps1 | `./scripts/Check.ps1` | - | not_run | run on Windows; formatting unverified |
| Task 3.6/3.8 completion | - | - | not_run | explicitly not claimed |

## Real game

Not run. Nothing is deployed or imported by `main.lua`; installed 0.4.1-dev unchanged.

## Limitations and continuation

- Tests were never executed under lupa Lua 5.3; the Mac sanity script used Lua 5.5.
- `ruff format` may reflow the test file; line lengths were checked by hand.
- Interpretation choices to review: method-call API, sparse snapshot cells keyed
  `[hook][button]`, separate dropped counters, closed-state precedence over window.
- Next action: run the targeted pytest and `Check.ps1` on Windows, then primary review.


## Primary Windows verification and self-review

- Reviewed at 0a76c20 plus this batch, 2026-10-17 Europe/Amsterdam; Python
  3.12.14, pytest 9.1.1. Existing isolated lupa.lua53 test runtime reused.
- `.venv/Scripts/python.exe -m pytest tests/test_lua_native_step_ledger.py -q`
  with that process-local PYTHONPATH: exit 0, 68 passed. No game/json/socket
  globals or observer harness were loaded by these isolated module tests.
- `./scripts/Check.ps1`: exit 0, 814 passed, zero skips; Ruff, 78 formatted
  files, strict mypy (36 source files), pip consistency and strict OpenSpec 24/24.
  The established process-local Lua runtime/json.lua and ignored temp directory
  were reused for the full suite. No dependencies or global settings changed.
- Self-review: fixed 15-query/16-post windows, fixed hook/button cells, scalar
  4096-call budget including drops, strict finite/type/bound checks before
  mutation, detached snapshots, independent instances and first-release retention
  conform to the frozen design. Endpoint observations after release are facts;
  no query count is converted into applied updates or completed status.
- The module is under mod/experimental and is not imported/shipped by the observer.
  Observer source/installed 0.4.1-dev hashes remain unchanged. No game/runtime,
  authority/approval, save/Cloud or reset/input limit changed.
- Accepted offline ledger component only. Tasks 3.6/3.8 and full task-4 probes
  remain incomplete; no archival. Next: source-backed audit of native oracle
  callbacks/outcome facts and attach-event ordering before their implementation.
