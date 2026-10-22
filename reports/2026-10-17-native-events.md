# Native oracle envelopes (native-event-models-01)

Executor: Copilot CLI on macOS over SMB. Offline only; no game, sockets, Lua, installs or Git.

## Files

- `src/isaac_threrisaifuture/native_events.py` (new): `NativeOracleEvent`, `NativeEventCursor`.
- `src/isaac_threrisaifuture/recording.py`: additive `native_oracle_events` stream and a `Record`
  union alias; existing streams, byte limits, provenance/version checks unchanged.
- `tests/test_native_events.py` (new).
- Follow-ups: `native_protocol.py` (`StepCommand` now delegates payload checks to `Command` with
  `type=command`, still a standalone model), `tests/test_native_protocol.py` (new test:
  internally consistent foreign session/epoch/room result must be rejected by `validate_completion`).
- `agent-status.json`, this report. No other files touched.

## Behavior

- Envelope: strict `protocol_version=1`, positive bounded `event_id`, nested `OracleEvent` must be
  `game_api` and agree on session/epoch/room/frame. `OracleEvent` is unchanged.
- Cursor (`__slots__`, O(1)): validates session/epoch first, then always validates the interval
  (strict ints, `start < end`, including for duplicates); `event_id <= last_id` returns `None`
  without checking the event frame against the interval; otherwise gap (`last_id + 1`) and frame in
  `(start, end]`. Any fault leaves `last_id` unchanged. A reconnect needs a new cursor.
  (Correction in revision 02, not in the first draft: the first draft suppressed duplicates before
  interval validation and its test accepted a duplicate with bounds (8, 8). Now invalid bounds
  raise for duplicates too; the test was replaced by valid-bounds old-frame suppression plus a
  parametrized invalid-bounds test (equal, reversed, negative, bool, oversized, float).)
- Recording: `NativeOracleEvent` is the only record type of the new stream; `event_id` survives
  replay. `NativeOracleEvent.provenance` is a read-only property (delegates to the nested event)
  so the existing manifest provenance check applies. A synthetic manifest therefore cannot hold
  native events. Legacy streams reject native records and vice versa; encoder already rejects
  non-`EntityFrame` input (tested).

## Checks

| Check | Result |
|---|---|
| `ast.parse` on the five touched Python files | passed |
| line length > 100 scan | passed (0 lines) |
| pytest, Ruff check/format, mypy, OpenSpec | not_run (no dependencies on macOS) |

A syntax parse is not a pytest pass.

## Known limits / expected Windows checks

- Never executed. Watch: pydantic raising `ProtocolError` (not `ValueError`) from the model
  validator on direct construction (same pattern as `Command`); mypy on the `Record` alias with
  `type[Record]` and on `item.provenance` for the property; ruff format of long test lines.
- `StepCommand` delegation builds a `Command` via `model_dump()`; relies on identical field names.
- No event transport, native generation, outcome inference or Lua changes.

## Primary-agent Windows acceptance

- Based on commit 4643cc6, with the reviewed new model/test files and additive
  recording stream then uncommitted. All new oracle data/tests are simulated.
- Revision 01 passed 114 targeted tests, Ruff/format and strict mypy; the primary
  review caught the invalid-duplicate-bound precondition and requested revision.
- Revision 02 was read and checked against the frozen contract: bounds/context
  precede duplicate suppression, original duplicate frames can be old, gaps and
  invalid windows do not advance state, and stream identities survive replay.
- `scripts/Check.ps1`: exit 0; 574 tests, no skips; Ruff; 70 formatted files;
  strict mypy on 34 sources; pip consistency; strict OpenSpec 24/24. Existing
  isolated Lua harness and process-local TEMP/TMP were used; no installs.
- 49 step-model cases and 49 native-event cases now pass in that full suite.
  The extra step cases cover internally coherent foreign completion identities.
- A separate primary-agent self-review covered bounds/identities, O(1) cursor
  state, policy rejection, legacy-stream rejection, event-ID-preserving replay,
  source diff and default behavior. No known critical issue in this offline slice.
- Task 3.3 accepted. Native emission/transport, synchronized gameplay, reset/start
  and the 100-real-episode gate remain unfinished. No game/Lua/deployment, save,
  Cloud, lease/reset limit or runtime authority changed. Item 05 is not archived.
