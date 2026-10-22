# Evidence: native-oracle-recording-provenance-20261019-01 (episode-lifecycle, offline recording format)

**Status: accepted offline after Windows primary review.** Subtask 3.14 is checked in `tasks.md`. This is an offline recording-format change in Python only. No game, Lua, runtime or training acceptance is claimed, and tasks 3.6 and 3.8 stay open and runtime-ineligible.

- Date/time and timezone: 2026-10-19, Europe/Amsterdam (macOS worker, shared SMB checkout).
- Git revision and dirty status: 97fd87a (Enforce negotiated oracle kinds in native receipts). The worktree already held unrelated edits to AGENTS.md, docs/AGENT_WORKFLOW.md, reports/2026-10-19-oracle-probe-live-runtime.md, subagent.md and subagent_report.md plus untracked errors.txt, scripts/Wait-Change.ps1 and scripts/wait-change.sh; all were preserved and none was touched. No commit, push or archive. `agent-status.json` and `subagent_report.md` were not modified (coordinator-owned).
- Change scope and acceptance criteria: a new `native_oracle_events` recording is created with the exact requested `OracleEvent` kind tuple, persists it in its manifest, and the writer and replay reject a native event outside an explicit list. A legacy native manifest without the field decodes as unknown (`None`), not empty. `policy_frames` and `oracle_events` keep their behavior and manifest bytes. Requested kinds only: no event semantics, receipt, reward/training, Lua, bridge negotiation or recording payload change.
- Game/mod/bridge versions: not applicable. No game, deployment, approval, training, save, Steam Cloud, user recording, private log or model was used.
- Python/package versions and configuration hash: Python 3.12 (~/.venvs/isaac), repository-pinned ruff, mypy, pytest and OpenSpec. No model or configuration hash.
- Scenario, split, seeds, budget, and stop conditions: simulated `NativeOracleEvent` envelopes written to and read from pytest temporary directories; no seeds, no learner.

## Changes

| Path | Change |
|---|---|
| src/isaac_threrisaifuture/recording.py | `RecordingManifest` gains optional `native_oracle_kinds` (tuple of `OracleKind`, lax list-to-tuple so JSON arrays decode). An after-validator rejects the field on any stream but `native_oracle_events`, an explicit `null`, and duplicates; unknown or non-string names fail the `OracleKind` literal. `JsonlRecorder` gains keyword-only `native_oracle_kinds`: a native stream requires a `tuple` (empty allowed), other streams accept nothing (not even `()`), anything else raises `ProtocolError`. The manifest is built and validated before the file is opened, so a rejected request leaves no file. The manifest is dumped with `exclude_none=True`, so non-native manifests stay byte-identical and a legacy-style absent field stays absent. `record()` rejects a native event outside the set before writing. `open_replay` rejects a native event outside an explicit manifest list after decode and provenance checks and before yielding it; `None` (legacy) applies no restriction. |
| tests/test_native_recording_provenance.py (new) | 35 cases through the public `JsonlRecorder`/`open_replay` APIs: see the coverage map. |
| tests/test_native_events.py | Fixture-only: the five existing native recorder constructions pass `native_oracle_kinds=("room_cleared",)` (new constant `KINDS`), because a new native recording now requires an explicit tuple. No assertion changed. |
| openspec/changes/episode-lifecycle/specs/episode-lifecycle/spec.md | New requirement "Native oracle recordings persist requested kinds" with seven scenarios. |
| openspec/changes/episode-lifecycle/design.md | New subsection "Native recording requested kinds (offline subtask 3.14, 2026-10-19)"; the 3.13 follow-up sentence now points to it. |
| openspec/changes/episode-lifecycle/tasks.md | Unchecked offline subtask 3.14 added after 3.13. 3.6 and 3.8 untouched. |
| docs/NATIVE_EPISODE_PROTOCOL.md | New paragraph in "Oracle stream" describing the manifest field, states and rejections. |
| docs/ENTITY_OBSERVATION_PROTOCOL.md | One-sentence cross-reference in "Finite recording and replay", because the shared manifest gains an optional native-only field. |
| reports/2026-10-19-native-oracle-recording-provenance-offline.md | This report. |

## Behavior

- Three states, never conflated: explicit nonempty list; explicit `[]` (no kind requested, every event rejected); absent field (legacy native manifest, `manifest.native_oracle_kinds is None`, replay unchanged, no event inferred as a negative outcome). An explicit `null` is malformed.
- The persisted list is exactly what the caller passed, in order. It is a request, not producer coverage, delivery, a barrier or runtime eligibility; a requested kind with no event stays unknown.
- Replay enforcement is integrity validation: earlier in-set events are already yielded when a later out-of-set event faults.
- No new manifest version: the field is additive and optional, `observation_schema_version` stays 1 and is not repurposed, and every existing manifest stays readable. An older reader rejects a new native manifest through `extra="forbid"` (fail-closed). No native recording producer exists in `src` yet, so nothing wires a session's requested kinds to a recorder.
- Receipts, `NativeOracleEvent` semantics, `native_receipts.py`, `native_client.py`, `observer_client.py`, Lua and recording payload lines are untouched.

## Results

Commands ran from `/Volumes/isaac` with `PYTHONDONTWRITEBYTECODE=1` and `P=~/.venvs/isaac/bin/python`.

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Baseline before edits | `$P -m pytest -p no:cacheprovider -q tests/test_native_events.py tests/test_recording_boundaries.py tests/test_observation_encoding.py` | 0 | passed | 72 passed. |
| New + native-event tests | `$P -m pytest -p no:cacheprovider -q tests/test_native_recording_provenance.py tests/test_native_events.py` | 0 | passed | 84 passed (35 new, 49 existing in test_native_events). |
| Focused recording/replay tests | `$P -m pytest -p no:cacheprovider -q tests/test_native_recording_provenance.py tests/test_native_events.py tests/test_recording_boundaries.py tests/test_observation_encoding.py tests/test_entity_probe.py tests/test_real_entity_fixtures.py tests/test_spectator.py` | 0 | passed | 123 passed. Includes the real j460 policy-frame fixtures and the other `JsonlRecorder` callers. |
| Full offline suite | `$P -m pytest -p no:cacheprovider -q -m "not game"` | 0 | passed | 1316 passed, 13 skipped (isolated-Lua decoder tests need `ISAAC_JSON_LUA`). Windows `Check.ps1` remains authoritative. |
| Lint | `$P -m ruff check --no-cache src tests scripts/smoke_rl.py` | 0 | passed | All checks passed. |
| Format | `$P -m ruff format --no-cache --check src tests scripts/smoke_rl.py` | 0 | passed | 106 files already formatted. |
| Types | `$P -m mypy --platform win32 --cache-dir ~/.cache/isaac-mypy` | 0 | passed | No issues in 44 source files (public `JsonlRecorder` and `RecordingManifest` types changed). |
| Whitespace | `git diff --check -- src tests openspec/changes/episode-lifecycle docs reports` | 0 | passed | No whitespace errors (only autocrlf CRLF warnings for CRLF files). |
| OpenSpec strict | `XDG_CONFIG_HOME=$PWD/.tooling OPENSPEC_TELEMETRY=0 node ~/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js validate episode-lifecycle --strict` (the pinned CLI used by scripts/check.sh; `./scripts/OpenSpec.ps1` is PowerShell/Windows-only) | 0 | passed | "Change 'episode-lifecycle' is valid". |
| OpenSpec all items (informational) | same CLI, `validate --all --strict` | 0 | passed | 30 passed, 0 failed. The Windows coordinator still runs `scripts/OpenSpec.ps1 validate --all --strict`. |
| Windows quality gate | `./scripts/Check.ps1` | not run | not_run | Coordinator-owned. |
| Real-game recording | Any Lua peer or Isaac session | N/A | not_run | Out of scope; no native recording producer exists. |

## Test coverage map

- Explicit nonempty set: kinds persisted in order in the manifest, replayed as a tuple, in-set events of both kinds round-trip; a recording with no events replays with the manifest set and no records.
- Explicit empty set: persisted as `[]`, replayed as `()` (not `None`), the writer rejects every event, and a hand-written file with an event under a `[]` manifest faults on the first event.
- Outside the set: the writer rejects the event without writing it; replay faults before yielding it, both as the first record and after an in-set record was yielded.
- Legacy native manifests without the field: `None`, every kind replays, also for a manifest-only file.
- Malformed replay metadata (native stream): `null`, a string, an object, an unknown name, `1`, `true`, `null` and a nested list as items, a duplicate, wrong case; all rejected when the file is opened.
- Non-native streams: the field in any form (`null`, `[]`, nonempty) is rejected by `open_replay`; the writer rejects `()` and a nonempty tuple and creates no file; written manifest bytes equal the previous exact line.
- Writer arguments: a list, an unknown name, `1`, `True`, a duplicate or a `None` item is rejected with `ProtocolError` and no file; a native recording without kinds is rejected with no file.

## Limitations and follow-ups

- A persisted request is not producer coverage, delivery or runtime eligibility, and no native recording producer exists yet to pass a session's requested kinds to a recorder. Wiring, receipt kind coverage, the Lua export (3.6) and native transaction multiplexing (3.8) remain separate and unfinished.
- A new native manifest is rejected by pre-change reader code (`extra="forbid"`, fail-closed); only new native recordings carry the field, and non-native recordings stay readable by any version.
- The `tests/test_native_events.py` fixture edit is required because a new native recording now needs an explicit tuple; its assertions are unchanged.
- `openspec/changes/episode-lifecycle/tasks.md` was reverted once with `git checkout` to repair an edit-tool line-ending slip. The repository content is the one added task line, but this checkout's working copy of that file now has LF endings instead of CRLF; Git normalizes it, so the diff is one line.
- Worker self-review against the diff: only the allowed paths changed; payload semantics, receipts, Lua and bridge negotiation are untouched. Subtask 3.14 remained unchecked pending Windows primary review and was checked after acceptance.

## Windows primary review

- Review: the worker report, allowed-path diff, public writer/replay behavior, legacy handling, malformed metadata checks and manifest-byte compatibility were inspected. `git diff --check` passed for the task's code, tests, specifications and protocol documents. No scope or behavior defect was found.
- Initial `./scripts/Check.ps1` attempt: Ruff, formatting, mypy and all 1248 tests completed, but pytest failed during teardown while cleaning the shared default temp root (`PermissionError` on `pytest-current`). This was an environment cleanup failure, not a test failure.
- Successful `./scripts/Check.ps1` rerun: exit 0 using a dedicated private `TEMP`/`TMP` directory; 1248 passed, 14 optional isolated-Lua tests skipped; Ruff, format, mypy (44 source files), pip consistency and embedded strict OpenSpec passed.
- Explicit `./scripts/OpenSpec.ps1 validate --all --strict`: exit 0, 30/30 passed.
- Acceptance boundary: offline recording/specification task 3.14 only. No game, Lua producer, native recording integration, training or runtime eligibility was tested. Tasks 3.6 and 3.8 remain open.
