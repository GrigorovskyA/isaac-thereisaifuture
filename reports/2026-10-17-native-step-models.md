# Native step models (native-step-models-01)

Executor: Copilot CLI on macOS over SMB. Offline only; no game, sockets, installs or Git.

## Files

- `src/isaac_threrisaifuture/native_protocol.py` (new): `StepCommand`, `StepCompletion`,
  `validate_completion`.
- `tests/test_native_protocol.py` (new): 20 test functions (many parametrized); data and peers
  are simulated.
- `agent-status.json`, this report.

## Design notes

- `StepCommand` is a standalone `WireModel` with the same canonical field order as `Command`
  (type, protocol_version, session_id, sequence, game_epoch, room_visit, frame_id, kind, move,
  shoot, frames), `type=step_command`, `kind=action`, `frames` 1..15. It is not a subclass:
  narrowing the `Literal` type of an inherited field would need a `type: ignore` that I could not
  confirm under mypy on this machine. Field order parity is tested against `Command`.
- Reused: `CommandAck`, `Counter`, `SessionId`, `WireModel`, `EntityFrame`, `Direction`, bounded
  `decode`. Sequence validation mirrors `Command` (>=1).
- `StepCompletion` validates in the model: nested frame provenance `game_api` and matching
  session/epoch/room, `frame_id >= accepted_frame`, `elapsed_updates == frame delta`, and the
  status/reason table (completed -> interval_elapsed with elapsed == requested; expired ->
  wall_deadline; cancelled -> pause/transition/input_fault/explicit_release).
- `validate_completion` checks action kind, session/sequence/epoch/room on ack and result,
  `accepted_frame == ack.frame_id`, `requested_updates == command.frames`, and ack freshness in
  `[command.frame_id, command.frame_id + 15]`. It is a receipt check, not engine proof.
- Violations raise `ProtocolError` (inside model validators, as `Command` does) or
  `pydantic.ValidationError` for field-level limits; tests accept either.

## Checks

| Check | Result |
|---|---|
| `ast.parse` on both new files (macOS python3) | passed |
| line length > 100 scan | passed (0 lines) |
| pytest, Ruff check/format, mypy, OpenSpec | not_run (no dependencies on macOS) |

## Known limits and risks for the Windows run

- Never executed. Expect to verify: strict pydantic accepting `EntityFrame` instances in
  `StepCompletion(frame=...)`; ruff format reflow of the `dict(...)` helpers; `1.0`/`"1"` rejection.
- `StepCompletion.sequence` uses an inline `ge=1, le=2**53-1` constraint instead of `Counter`
  because the frozen design requires `>=1`.
- No oracle events, transport, Lua or capability negotiation were touched.

## Primary-agent Windows acceptance

- Revision: based on 4643cc6 with the two new code/test files then uncommitted.
- `python -m pytest tests/test_native_protocol.py -q`: exit 0, 46 passed.
- Ruff check/format: exit 0; strict mypy: exit 0, 33 source files.
- `scripts/Check.ps1`: exit 0, 522 tests, no skips; Ruff, 68 formatted files,
  mypy, pip consistency and strict OpenSpec 24/24. Existing isolated Lua runtime
  and process-local TEMP/TMP were used; no dependencies/settings changed.
- Self-review: frame/status/reason consistency, acceptance vs completion,
  canonical legacy rejection, ordering and identity matching map to the active
  step contract. Full native transport and callback application remain absent.
- No game launched, modified, reset or controlled. No native receipt was received.
  All new tests are simulated. A parsed receipt is not evidence of actual motion.
- Task 3.2 is complete; item 05 remains active and unarchived. Code generation
  next covers event envelopes/deduplication/recording; all runtime gates remain.
- Follow-up hygiene: reuse Command payload validation and test cross-result
  identity with internally consistent foreign frames before transport integration.

The follow-up delegation and internally consistent foreign-result tests were
included in the final 574-test suite (49 step cases); all passed. Their review
and the separate event slice are recorded in the native-events report.
