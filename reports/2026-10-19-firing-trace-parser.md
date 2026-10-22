# Evidence: firing-trace-parser-20261019-01

- Date: 2026-10-19.
- Baseline: 9d3d0d2. Existing Windows edits (AGENTS.md, docs/AGENT_WORKFLOW.md,
  subagent.md, errors.txt, scripts/Wait-Change.ps1, scripts/wait-change.sh) and the
  coordinator's concurrent uncommitted work (mod/observer/main.lua, the design.md
  and native-player-actions spec.md of firing-cadence-diagnostics,
  tests/test_lua_firing_diagnostics.py, firing_cadence_probe.py and its test) were
  preserved and not edited.
- Scope: pure offline parser/aggregator for the bounded `[Isaac Future Trace]`
  records. No Lua, wire/schema, reward, policy, approval, save or runtime change.
- Runtime/data: none. No game, mod deployment, approval, model, save, native or
  private log was accessed; tests use synthetic lines in the Lua trace format. No
  raw trace line appears in this report.
- Python: macOS CPython 3.11.15 and 3.12.13 (project target 3.12); scratch tools
  were installed outside the repository (session folder) and bytecode writing was
  disabled for the revision 2 runs.
- Revision 2 (coordinator review): two bounded-work fixes in `firing_trace.py`,
  described below; results in the table are from the final tree.
- Revision 3 (Feedback 1): `parse_line` no longer calls `rstrip()`, which had
  accepted a valid record followed by a space, tab, CRLF+space or CRLF+tab. It
  now strips at most one terminal line ending (CRLF, LF or CR). The table shows
  the revision 3 focused checks; OpenSpec and the other rows were not rerun
  because no OpenSpec or other file changed.

## Results

| Requirement | Command | Exit code | Status | Evidence |
|---|---|---|---|---|
| Parser behavior (offline, Python 3.12.13) | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<scratch pylib>:src python3.12 -m pytest tests/test_firing_trace.py -q -p no:cacheprovider` | 0 | passed | 150 passed, 1.71 s (134 before revision 3, plus 16 new cases) |
| Parser behavior (Python 3.11.15) | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest tests/test_firing_trace.py -q -p no:cacheprovider` | 0 | passed | 150 passed, 0.30 s |
| Lint | `python3.12 -m ruff check --no-cache` on the new module and test (ruff 0.17.1, the pinned version) | 0 | passed | All checks passed |
| Format | `python3.12 -m ruff format --no-cache --check` on the same files | 0 | passed | 2 files already formatted |
| Strict typing | `python3.12 -m mypy --cache-dir=<scratch cache> src/isaac_threrisaifuture/firing_trace.py` (mypy 1.20.2, the pinned version) | 0 | passed | no issues in 1 source file |
| Historical Mac OpenSpec attempt (revision 1) | `openspec validate firing-cadence-diagnostics --strict` | 1 | failed at that revision | Two overlong requirement warnings in the coordinator's then-current uncommitted spec; corrected before final Windows validation |
| OpenSpec, working tree with spec.md restored to HEAD (scratch copy) | same command | 0 | passed | change valid; includes the new task 5 |
| OpenSpec, pure HEAD copy (scratch) | same command | 0 | passed | change valid |
| Full Windows gate on Mac | `scripts/Check.ps1` | N/A | not_run | Windows coordinator verification is recorded below |
| Production Lua suites | lupa-based tests | N/A | not_run | lupa and the Windows `.venv` are unavailable on this Mac |
| Wider Python suite | `pytest tests` | 2 | not runnable here | Existing modules use Python 3.12-only syntax (PEP 695), and gymnasium is missing, so collection fails; unrelated to this change |
| Real cadence comparison | Separate operator-budgeted empty-room test | N/A | not_run | OpenSpec task 4 remains unchecked |

Coordinator recheck after Feedback 1: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src
python3.12 -m pytest tests/test_firing_trace.py -q -p no:cacheprovider` exited 1
because pytest is not installed in this coordinator environment. No dependency
was installed. The worker's revision 3 test runs used its session-local pytest
path and passed on both Python versions, as recorded above.

Pinned OpenSpec could not run from repository `node_modules` over the Mac SMB
mount (EPERM). The same pinned version (1.14.3) was installed into the ignored
`reports/local/openspec-1.14.3`, with telemetry disabled and a local
`XDG_CONFIG_HOME`. The warning was historical and came from the coordinator's
then-current spec edit. The Windows coordinator shortened the requirements and
recorded a passing final `--all --strict` run below.

## Interface and behavior

`isaac_threrisaifuture.firing_trace`: `parse_line`, `parse_trace`,
`summarize_trace` and `analyze_trace(lines)`; frozen dataclasses `TraceRecord`,
`ParsedTrace`, `TraceSummary`, `GroupSummary`, `ValueRange`, `ReleaseInterval`
and `IntervalStats`. Documented in docs/FIRING_CADENCE_DIAGNOSTICS.md.

- Input is any iterable of text lines; bytes or non-text items are rejected as
  `malformed`. The module opens no file and does no traversal. At most 1,000,000
  lines are scanned, ids are unique within 1..512, and at most 16 rejection
  samples are kept, so memory is bounded. `max_lines` can only lower the scan
  budget: a value outside 0..1,000,000 raises `ValueError` before any line is
  read (revision 2).
- Lines without the exact prefix in their first 1024 characters, including
  `[Isaac Future OracleProbe]` lines, are discarded without counting.
- A prefixed record must fit 300 characters plus a two-character line ending,
  be printable ASCII and match one of the source events with its exact fields.
  The length check uses `len()` before any slice, so an arbitrarily long
  prefixed line (including long trailing whitespace) is rejected as `oversized`
  without a copy. Only one terminal line ending (CRLF, LF or CR) is removed;
  spaces and tabs are never trimmed. An embedded line ending or any whitespace
  beyond that one line ending makes an otherwise valid record `malformed`, and a
  record over 300 characters after the line ending is removed stays `oversized`
  (revision 3; revision 2 had used `rstrip()`). Rejections use fixed categories
  (`oversized`, `malformed`, `missing_field`, `duplicate_field`, `unknown_event`,
  `unknown_field`, `invalid_cooldown`, `duplicate_id`) with the line number only.
  Free-text `release`/`close` reasons are reduced to a known class or dropped.
- Identity (`id`, `event`, `time_ms`, `frame`, `update`, `session`, `epoch`,
  `room`, optional `seq`) is preserved. A missing or repeated identity field is
  rejected, and a repeated id keeps the first record.
- Cooldowns must be finite and within +/-1e6. Fractions are kept. `na` is
  counted as missing and never becomes zero. Ranges are kept per source.
- Groups are keyed by (session, epoch, sequence) and count events, commanded
  direction/frames, and cooldown ranges. A group with four `fire_tear` records
  is flagged `tear_log_saturated`. Summary-level counts cover shoot directions
  and input hook/return phases.
- A release-to-next-accept interval is paired only inside the same session,
  epoch and room. It needs an advanced sequence and non-negative gaps. It is
  excluded across new room/level, game start/end, close, exit and
  `stop reason=close`, and unmatched releases are counted. Sessions, epochs and
  reconnects therefore never merge, and handoff gaps are never intervals.
- `incomplete` is true for a count/deadline/line_limit stop or no stop record,
  and with named extra reasons for rejected records, id gaps, extra stops,
  records after a stop or a truncated scan. An explicit `stop reason=close`
  (emitted by the coordinator's sparse `firing_diagnostics` mode) is not a
  budget stop and does not itself set the flag. The exhaustive mode ends with a
  `close` event and so reports `no_stop_record`.
- The summary has no rate, loss, consumption or causal fields. A static
  `limitations` tuple states that nothing about the maximum firing rate, shot
  loss, physical input consumption or keyboard neutrality is inferred, and that
  a missing tear record is not evidence that no shot occurred.

## Test coverage (tests/test_firing_trace.py)

Every source event parses with exact provenance and decorated log prefixes.
Cooldown values are tested for fractions, zero, `na`, nonfinite, over-bound and
malformed tokens in both slots. Malformed, oversized and huge lines, duplicate
and missing identity fields, duplicate ids, non-text input, and no echo of
secret markers in summaries, errors or JSON are covered. Interleaved sessions,
reconnects, epoch changes, sequence grouping, tear saturation, intervals and
handoff exclusion, budget/close/missing/extra stop rules, gap and scan limits,
and the 512-record cap are covered. Revision 2 adds regressions: oversized
prefixed input (2 MB, long trailing whitespace, long line endings) is rejected
by `parse_line` and `parse_trace` using a `str` subclass that fails on any slice
or strip, the 300-character-plus-line-ending boundary, and `max_lines` values
above 1,000,000 or negative (`ValueError` before the iterable is consumed).
Revision 3 adds 16 cases on the record boundary using synthetic lines only: a
valid record with no ending, LF, CRLF or CR is accepted; the same record plus a
trailing space, tab, CRLF+space or CRLF+tab (and space+CRLF, LF+space, double
CRLF, double LF, LF+CR) is rejected as `malformed` by both `parse_line` and
`parse_trace` (no record, one counted rejection, no raw text in the result);
and an embedded LF, CRLF or CR is rejected as `malformed`. A final test asserts that no rate or causal
field exists and the limitation text is present. A drift test checks that every
trace event emitted in `mod/observer/main.lua` has parser coverage.

## Changed files

- `src/isaac_threrisaifuture/firing_trace.py` (new)
- `tests/test_firing_trace.py` (new)
- `docs/FIRING_CADENCE_DIAGNOSTICS.md` (parser interface and interpretation appended)
- `openspec/changes/firing-cadence-diagnostics/tasks.md` (task 5 added and checked; task 4 still unchecked)
- `reports/2026-10-19-firing-trace-parser.md` (this report)

`agent-status.json` and `subagent_report.md` were not touched, because the
coordinator owns them under the current workflow. Revision 1 scratch tool installs
lived only under git-ignored `reports/local/` and were removed afterwards.
Revision 2 installed the pinned tools outside the repository and used separate
or disabled caches, so neither `.mypy_cache` nor `.ruff_cache` was touched. A
mypy 2.4.0 probe in revision 1 wrote into the git-ignored `.mypy_cache/3.12` and
made pinned mypy 1.20.2 crash with an internal error, so that derived cache
directory was deleted; mypy rebuilds it on the next run.

## Self-review

- Checked each requirement of the assignment against the code and tests: bounded
  line size, safe rejection without echo, identity provenance, finite cooldowns
  with `na` as missing, grouping, interval scope, incomplete rules, and no rate
  claim. No existing module, test, Lua, approval or spec changed.
- The Lua source was checked, including the coordinator's sparse mode: the line
  format is unchanged, and the new `stop reason=close` is accepted. Without
  that, a sparse capture would have been rejected as malformed.
- Caveats: the parser trusts the Lua format at the time of writing, and a drift
  test guards event labels but not field layouts. The tail of a `release`
  record is parsed from the end, so key-like text in a free reason cannot
  change identity, but it is not detected either. Intervals use the game-reported
  `time_ms` and `frame` deltas, so they are descriptive only.
- Revision 3: the line-ending handling and the 300-character, two-character
  allowance and pre-copy size check were rechecked against the code. No private
  log was read, and only the module, its test and this report were edited.
- Not verified: behavior on a real private log (none was read), Windows
  `Check.ps1` and the Lua suites, and OpenSpec `--all --strict`.

## Remaining acceptance

The real safe-room cadence comparison remains `not_run`. Run it only under the
separately supplied finite operator authorization, preserve the 30-second and
16-command bounds, and keep the OpenSpec change unarchived until real evidence
and cleanup are reviewed.

## Windows coordinator verification (2026-10-19)

The earlier Mac coordinator could not run pytest locally; no dependency was
installed there. On the Windows project environment, the focused parser suite
passed with 150 tests. `scripts/Check.ps1` passed with 1644 tests, zero
skips/xfails, Ruff, 105 formatted files, mypy on 44 source files, pip consistency,
and pinned strict OpenSpec (31/31). The explicit
`scripts/OpenSpec.ps1 validate --all --strict` rerun also passed 31/31. The
full check used the existing Lua test runtime and a private ignored
`reports/local` directory for temporary files. No game was launched, no private
log was read, and OpenSpec task 4 remains not_run.

The Windows review reproduced and then closed the trailing-whitespace defect
with synthetic input before acceptance. `git diff --check` returned 0 for the
reviewed project paths (Git reported only existing CRLF-to-LF normalization
warnings). The executor's writes are closed; the remaining live comparison is a
separate real-game acceptance step.
