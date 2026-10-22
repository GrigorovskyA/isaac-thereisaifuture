# Remote recording boundary tests (2026-10-17)

Task: `observation-recording-boundaries-01` (handoff in `subagent.md`).

## Added

`tests/test_recording_boundaries.py` (4 test functions, 5 cases with parametrization):

1. Data record padded with trailing JSON whitespace to exactly `MAX_FRAME_BYTES` is accepted;
   `MAX_FRAME_BYTES + 1` raises `ProtocolError` ("size limit") on first read.
2. Same boundary for the manifest line: accepted at the limit, rejected one byte over, and
   `open_replay` raises eagerly.
3. A later record with a different provenance: the earlier two records are yielded, the third
   raises `ProtocolError` ("provenance") and is never yielded.
4. A truncated final record (with and without trailing newline) raises `ProtocolError`;
   the earlier completed records are still replayed.

All files are small (padding only up to 64 KiB), use `tmp_path`, `\n` newlines written as bytes
(avoids Windows CRLF translation), and only the public `JsonlRecorder`/`open_replay` API.

## Checks

| Check | Status |
|---|---|
| `ast.parse` of the test file (macOS, Python 3.14) | passed (syntax only) |
| `pytest tests/test_recording_boundaries.py` | not_run (no project environment on this machine) |
| `ruff check` / `ruff format --check` on the file | not_run |

Syntax parsing is not a pytest result; the primary agent must run the three Windows commands
from the handoff.

## Defects / follow-up

No defect found by reading `recording.py::_read_record`: `readline(MAX_FRAME_BYTES + 2)` reads
the limit plus newline plus one probe byte, so a `MAX+1`-byte line is rejected whether or not it
ends in a newline. No production change proposed. If a test fails on Windows, the likely cause is
the test expectation (for example frame size already near the limit), not the production code;
report the failure rather than relaxing the limit.

## Primary-agent Windows verification

All five cases passed in the final 476-test Windows suite. Ruff check and format
check passed; no production change was required. The remote result was reviewed
and accepted through subagent.md. Source execution on macOS was not claimed.
