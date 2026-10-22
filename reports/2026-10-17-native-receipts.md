# Evidence: episode-lifecycle / native-receipts-02 (task 3.8, offline assembler only)

- Date/time and timezone: 2026-10-17, Europe/Berlin (CEST, UTC+2); Mac executor edits.
- Git revision and dirty status: base 613e30d plus uncommitted working-tree changes (no Git writes by the executor).
- Change scope and acceptance criteria: offline `NativeReceiptAssembler`/`NativeStepReceipt`
  in `src/isaac_threrisaifuture/native_receipts.py`; two read-only properties
  (`session_id`, `game_epoch`) on `NativeEventCursor`; tests in `tests/test_native_receipts.py`.
  Task 3.8 is NOT complete: no `NativeStepClient` wiring, sender or Lua emission.
- Game/mod/bridge versions: not applicable (offline, simulated records only).
- Python/package versions and configuration hash: not run on the Mac executor (no dependencies).
- Scenario, split, seeds, budget, stop conditions: not applicable.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| First Windows targeted run (revision 01) | primary-run pytest on receipt tests | n/a | failed | 57 passed, 1 failed (`baseline(frame_id=99)` raised TypeError); ruff lint and strict mypy passed; `ruff format --check` found two layout issues |
| Revision 02 fixes | see list below | n/a | pending primary | not re-run by the executor |
| Syntax of changed files | `python3 -c "import ast; ast.parse(...)"` on the two new files | 0 | passed | Mac |
| Line length <= 100 | `awk 'length>100'` on the two new files | 0 | passed | no output |
| `./scripts/Check.ps1`, pytest, ruff, mypy, OpenSpec strict | Windows primary | n/a | not_run | executor has no runtime |
| Per-record, aggregate and CR/LF checks run before JSON parsing | `test_oversized_record_is_rejected_before_any_json_parse`, `test_budget_is_enforced_before_any_json_parse` (spy on `json.loads`) | n/a | not_run | written, pending primary |
| Real 16384/65536 byte boundaries | `test_record_of_exactly_the_per_record_limit...`, `test_real_total_byte_boundary...`, `test_padded_four_record_receipt...` | n/a | not_run | whitespace-padded valid records |
| Delimiter-free records | `test_complete_valid_ack_with_line_delimiter_is_rejected` (LF, CRLF, CR); spaces/tabs accepted | n/a | not_run | |

Revision 02 changes: (1) test `baseline()` now builds a defaults dict and updates it, so a
mismatched frame reaches the constructor and fails with `ProtocolError`; (2) `_feed` now checks
bytes type, per-record size and record/byte budget before any `json.loads`; (3) real frozen
byte-boundary tests added; (4) raw CR/LF records are rejected explicitly; (5) the two Ruff
layouts were collapsed to single lines by hand; (6) this report expanded.

## Real game

Not run. No game, mod, save or Cloud interaction. A matching receipt is not proof of
physical input or game acceptance.

## RL evaluation (if applicable)

Not applicable.

## Limitations and continuation

- Final gates (format, ruff, strict mypy, pytest, OpenSpec) are pending the Windows primary.
- A hand-collapsed layout may still differ from `ruff format`; the primary will re-run it.
- Wiring into `NativeStepClient`, a transport sender and Lua emission remain open (task 3.8).
- Self-review: the shared cursor is mutated only after all pending events validate; a
  fault clears pending data and makes the assembler unusable.


## Primary Windows verification and self-review

- Revision d6bdea8 plus reviewed batch, 2026-10-17 Europe/Amsterdam. Python
  3.12.14, pytest 9.1.1. Dependencies unchanged.
- `.venv/Scripts/python.exe -m pytest tests/test_native_receipts.py -q`: exit 0,
  67 passed after revision 02; the first revision's failure is retained above.
- `./scripts/Check.ps1`: exit 0, 698 passed, zero skips; Ruff, 75 formatted files,
  strict mypy (36 source files), pip consistency and strict OpenSpec 24/24.
  Process-local Lua test runtime/json.lua and ignored check-native-protocol temp
  directory were reused; no global settings changed.
- Self-review: strict ack/event/completion order and matching, baseline/cursor
  identity, bounded duplicate-inclusive records/bytes, all-event validation before
  shared cursor advancement, watermark matching and failed/finished reuse checks
  conform to the frozen design. Event envelopes retain their IDs. Required
  session_id/game_epoch cursor properties are read-only; dedup semantics unchanged.
- Revision 02 fixed size-before-parse, fixture duplicate keyword and format issues.
  Parser-spy regressions pass; real padded valid 16384-byte records and a complete
  65536-byte receipt pass; larger aggregate/per-record inputs fail before parsing.
  Complete valid records with LF/CRLF/CR fail. Spaces/tabs remain valid whitespace.
- This accepts the standalone assembler only. Task 3.8 remains incomplete: no
  socket integration, command sender, attach event baseline or Lua emission.
  A receiver must enforce its own total deadline and discard connection-bound
  cursor state after faults; receipt validity alone is not runtime evidence.
- No game, installed mod, save, Cloud, action approval or runtime limit changed.
  Next: bounded receipt socket reader using this assembler, still without sender.
