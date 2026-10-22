# Evidence: episode-lifecycle / native-receipt-reader-01 (task 3.8, receiver component only)

- Date/time and timezone: 2026-10-17, Europe/Berlin (CEST, UTC+2); Mac executor edits.
- Git revision and dirty status: base fdfd430 plus uncommitted working-tree changes (no Git writes by the executor).
- Change scope and acceptance criteria: `NativeStepClient.receive_receipt(command, baseline, cursor)`
  in `native_client.py`; optional keyword-only `before_commit` in `NativeReceiptAssembler`;
  simulated-socket and guard tests in `tests/test_native_receipt_reader.py`.
  Task 3.8 is NOT complete: no command sender, attach-baseline, Lua, CLI or runtime wiring.
- Game/mod/bridge versions: not applicable (simulated loopback peers only).
- Python/package versions and configuration hash: not run on the Mac executor (no dependencies).
- Scenario, split, seeds, budget, stop conditions: not applicable.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Syntax of changed files | `python3 -c "import ast; ast.parse(...)"` on the three changed/new files | 0 | passed | Mac |
| Line length <= 100 | `awk 'length>100'` on the changed/new files | 0 | passed | no output |
| `./scripts/Check.ps1` (ruff, format, strict mypy, pytest, OpenSpec) | Windows primary | n/a | not_run | executor has no runtime; import order/format unverified |
| Split/coalesced records, sequential receipts, dedup of replayed event | `test_split_and_coalesced...`, `test_sequential_receipts...` | n/a | not_run | written |
| Zero post-hello outbound bytes | peer asserts EOF-only via `hold_until_closed` in all holding tests | n/a | not_run | written |
| Absolute deadline: silent peer, slow trickle | `test_silent_peer...`, `test_slow_trickle...` | n/a | not_run | written |
| Precommit deadline guard, cursor unchanged | `test_late_receipt_is_rejected...` (fake `time.monotonic` late at the commit call) | n/a | not_run | written |
| Wrong identity/order/barrier/foreign/noncompleted/invalid records | `test_invalid_receipts_close_the_peer_and_keep_the_cursor` (13 streams) | n/a | not_run | written |
| Disconnect, replay, stale snapshot, preconditions, reconnect, sender stays unsupported | dedicated tests | n/a | not_run | written |
| Assembler guard: not called on malformed, called once before advance, error and mutation | four `guarded` tests | n/a | not_run | written |
| Old native waiting/unsupported tests | `tests/test_native_client.py` unchanged | n/a | not_run | no edits to old tests |

Design notes:

- One monotonic deadline from `message_timeout` covers every `_read_line`, buffered lines included
  (checked before each read), plus a guard immediately before the shared cursor commit.
- Preconditions: negotiated peer (plain `BridgeError`), a prior active snapshot or receipt,
  command session equals the connection session, `command.sequence == last receipt + 1`, and
  baseline epoch/room/frame equals the latest active/receipt frame.
- Every failure closes the peer and raises `EpisodeFault` with the cause; interruptions close and
  propagate. On success `_active` and `_frame` move to the completion frame, snapshot sequence and
  update counters stay unchanged, and the receipt sequence advances. `close_peer` resets it.
- A matching receipt is wire-level consistency, not proof of application or physical input.

## Real game

Not run. No game, mod, save or Cloud interaction.

## RL evaluation (if applicable)

Not applicable.

## Limitations and continuation

- Everything beyond ast and line length is unrun; import ordering and format may need a Ruff fix.
- `receive_receipt` is typed against `NativeEventCursor`; the no-peer test passes `None` only
  where the call fails before use.
- Remaining for 3.8: command sender, authority gate, attach-baseline, Lua emission.
- Self-review: the shared cursor is mutated only after full validation and the deadline guard;
  the assembler stays clock-free.


## Primary Windows verification and self-review

- Reviewed at f6b306d plus the batch, 2026-10-17 Europe/Amsterdam; Python 3.12.14,
  pytest 9.1.1. No dependencies changed.
- `.venv/Scripts/python.exe -m pytest tests/test_native_receipt_reader.py -q`:
  exit 0, 31 passed including parametrized invalid-stream cases.
- `./scripts/Check.ps1`: exit 0, 729 passed, zero skips; Ruff, 76 formatted
  files, strict mypy (36 source files), pip consistency, OpenSpec strict 24/24.
  Existing process-local Lua test runtime/json.lua and ignored temp directory
  were reused. No global settings changed.
- Self-review: one total deadline across partial/coalesced records and final
  precommit check; baseline, session, successful receipt sequence and cursor
  validation; stale snapshot rejection after completion; reconnect cleanup.
  Cursor is not advanced when deadline guard fails. Guard failures invalidate
  the assembler; post-guard external cursor changes are detected. Snapshot
  sequence/update counters remain unchanged by receipt handling.
- Peers assert EOF-only after hello; no command sender or authority was added.
  start_episode/reset/step remain unsupported; no outcome is inferred.
- Accepted receiver component only. Task 3.8 remains unfinished pending a valid
  attach/event baseline, authority-gated sender and matching Lua emission.
- No installed game/mod/save/Cloud or runtime limit changed. Next: bounded opt-in
  callback instrumentation to measure the unknown native ordering before claiming
  exact input application or terminal event semantics. Real probes remain not_run.
