# Windows primary review: terminal-outcome-coverage

**Superseding result: ACCEPTED OFFLINE after the frozen handoff
2026-10-19T19:15:53Z.** The final Windows rerun passed 1802 tests, zero skips,
lint/format/mypy/pip and strict OpenSpec 30/30. Seven implementation/test hashes
and the spec/design hashes matched before and after the full gate. Task 3.15 is
complete, while 3.6/3.8 remain open. See the final acceptance section in
`reports/2026-10-19-terminal-outcome-coverage.md`. The original rejection below is
preserved as evidence of the earlier overlapping review, now resolved. No runtime,
commit/push, successor task or archive was performed by this primary.

- Date: 2026-10-19, Europe/Amsterdam.
- Task: terminal-outcome-coverage-20261019-01; baseline b973a2c.
- Matching ready_for_review timestamp: 2026-10-19T19:06:04Z.
- Monitor paused before review. No runtime authority or game work.

## Results

| Check | Exit | Status | Evidence |
|---|---|---|---|
| scripts/Check.ps1 | 1 | failed | Ruff check passes; Ruff format rejects new initial-terminal cases in tests/test_episodes.py; later full gates not executed |
| Four affected test modules on Windows | 0 | passed | 83 passed in 13.93 seconds |
| scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 30/30 |
| Stable final implementation handoff | N/A | blocked | Implementation/test edits continued after ready_for_review and during primary inspection |

Used existing isolated Lua runtime on PYTHONPATH and installed resources/scripts/json.lua
through ISAAC_JSON_LUA; private reports/local/check-native-protocol TMP/TEMP.
No dependency installation or skipped-test substitution.

## Review observations

Coverage defaults unknown and aggregates by intersection; positive facts remain
distinct from unknown absence. LiveBackend continues to claim no native terminal
coverage. Evaluation version 2 excludes unknown from clear-rate/Wilson and
minimum-valid populations while retaining non-fault damage/return means.
This is the implementation choice reported by the coordinator; final acceptance
still requires the stable full Windows gate. No curriculum threshold change.

The first inspected start method did not reject initial terminal events. A later
read includes that guard and the targeted initial-terminal cases pass. The first
full gate rejects their formatting, while a later read shows formatted tests.
Therefore the initial failure must not be presented as a failure of the final
formatted snapshot, and partial results must not be attributed to an immutable
review revision. Do not accept code while another writer is changing it.

## Outcome

NOT ACCEPTED. Feedback 2 in subagent.md requests a fresh frozen task-matched
report with final file hashes and no subsequent edits. Existing allowed writes
and runtime restrictions stay unchanged. Tasks 3.6/3.8/3.15 stay unfinished;
monitor stays paused. No project commit/push or OpenSpec archive.

Unrelated workflow files, reports, errors.txt and private data were preserved.
