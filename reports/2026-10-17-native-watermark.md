# Evidence: episode-lifecycle / native-watermark-01

- Date/time and timezone: 2026-10-17, Europe (+02:00)
- Git revision and dirty status: fe308d8 base, dirty (uncommitted working tree, shared SMB copy)
- Change scope and acceptance criteria: task 3.7 only. `StepCompletion.last_event_id: Counter`
  appended, required, no default; no field on `EntityFrame`; all identity/status/frame/size
  checks unchanged. New `validate_event_barrier(result, last_event_id)` (exported): observed value
  must be an actual `int` in 0..2**53-1 and equal `result.last_event_id`, otherwise
  `ProtocolError`. It imports no cursor/client module, does not change `validate_completion`
  and does not bind a cursor to a session.
- Game/mod/bridge versions: not applicable (offline models).
- Python/package versions and configuration hash: not run on macOS.
- Scenario, split, seeds, budget, and stop conditions: not applicable.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Syntax | `ast.parse` on native_protocol.py and test_native_protocol.py | 0 | passed | macOS |
| Line length <= 100 | awk scan on both files | 0 | passed | no long lines |
| Round trip zero/positive/MAX | `test_watermark_round_trips_...` | 0 | passed | primary Windows tests |
| Missing field rejected | `test_receipt_without_watermark_is_rejected` | 0 | passed | primary Windows tests |
| Strict counter values in model | `test_watermark_must_be_a_bounded_strict_integer` | 0 | passed | primary Windows tests |
| Matching barrier zero/nonzero/MAX | `test_matching_barrier_is_accepted` | 0 | passed | primary Windows tests |
| Missing tail and cursor ahead | `test_missing_tail_or_cursor_ahead_is_rejected` | 0 | passed | primary Windows tests |
| Malformed observed counter (bool, float, str, None, range) | `test_malformed_observed_counter_is_rejected` | 0 | passed | primary Windows tests |
| Previous tests preserved | existing tests in test_native_protocol.py, test_native_negotiation.py (uses `completion()`) | 0 | passed | primary Windows tests |
| pytest, Ruff, format, strict mypy, OpenSpec strict | `./scripts/Check.ps1` | - | not_run | macOS share lacks dependencies; orchestrator records Windows results |

The shared `completion()` fixture now passes `last_event_id=0` before `**changes`, so tests
can override it. Only `test_native_negotiation.py` and `test_native_protocol.py` build
completions (searched `src` and `tests`).

## Real game

No real-game run took place; no Lua, deployment or peer was touched.

## Limitations and continuation

- The watermark does not prove physical input and cannot detect a peer that invents a
  consistent history; the helper checks one integer and nothing about session identity.
- A future transaction must validate identity, consume interval events with its bound
  `NativeEventCursor`, then pass `cursor.last_id` to the helper.
- Self-review (not independent): diff limited to the three allowed files plus agent-status.json.
- Next action: orchestrator runs the primary Windows gates and records results here.

## Primary Windows verification and self-review

- Reviewed at fe308d8 plus this batch, 2026-10-17 Europe/Amsterdam; Python
  3.12.14, pytest 9.1.1; no dependencies changed.
- `.venv/Scripts/python.exe -m pytest tests/test_native_protocol.py
  tests/test_native_negotiation.py -q`: exit 0, 90 passed (74 receipt/model cases
  including 25 new watermark cases, plus 16 negotiation cases).
- `./scripts/Check.ps1`: exit 0, 631 passed, zero skips, Ruff, 73 formatted
  files, strict mypy (35 source files), pip consistency and OpenSpec strict 24/24.
  Process-local PYTHONPATH/ISAAC_JSON_LUA used the existing Lua test runtime and
  installed json.lua; ignored reports/local/check-native-protocol held temp files.
  No global settings or installed game/mod files changed.
- Self-review: watermark is required and strictly bounded; missing fields fail,
  both missing tail and cursor ahead fail. Existing receipt matching signature,
  status/frame/provenance checks and all previous tests are preserved. No cursor
  module import or policy frame field was added. Helper claims no session binding.
- Task 3.7 accepted offline only. Next: bounded receipt assembly to enforce actual
  message ordering, interval identity and barrier consistency before any sender.
  Native transaction transport, attach baseline and real input proof are unfinished.
