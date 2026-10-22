# Evidence: native-oracle-kind-receipt-20261019-01 (episode-lifecycle, offline Python receipt hardening)

**Status: accepted by Windows primary review (2026-10-19; f1/f2).** The fail-closed receipt contract and authorized fixture updates passed the full Windows gate (1213 passed, 14 optional isolated-Lua skips) and explicit strict OpenSpec validation (30/30). F2 narrows the constructor type annotation to the tuple/frozenset forms accepted at runtime. This is offline protocol hardening only; no game/runtime acceptance is claimed. The first pass reported `needs_input` because two existing test modules outside the original allowed-write list went red; the Windows coordinator authorized exactly those fixture-only paths in f1, and they were re-applied unchanged.

**f1 scope (coordinator revision, 2026-10-19):** `tests/test_native_receipt_reader.py` and `tests/test_native_outbox.py`, fixture-only. Allowed adaptations: the reader loopback peer/config requests and advertises `room_cleared`, direct assembler fixtures pass `oracle_kinds`, and the outbox assembler passes `oracle_kinds`. No assertion and no production behavior changes in those files; no runtime access, commits, pushes, archives, installs or nested workers. `agent-status.json` and `subagent_report.md` stay coordinator-owned.

- Date/time and timezone: 2026-10-19, Europe/Amsterdam (macOS worker, shared SMB checkout).
- Git revision and dirty status: 6676ecf (Add per-kind oracle negotiation groundwork). The worktree already held unrelated edits to AGENTS.md, docs/AGENT_WORKFLOW.md, reports/2026-10-19-oracle-probe-live-runtime.md, subagent.md and subagent_report.md plus untracked errors.txt, scripts/Wait-Change.ps1 and scripts/wait-change.sh; all were preserved and none was touched. No commit, push or archive. `agent-status.json` and `subagent_report.md` were not modified (coordinator-owned this task).
- Change scope and acceptance criteria: a native receipt accepts a `NativeOracleEvent` only when its `OracleEvent.kind` is in the exact set the consumer requested through `ObserverConfig.native_oracle_kinds`. Python offline protocol hardening only: no Lua change, no kind is advertised or runtime-eligible, no recording wire/file format change, no event semantics, reward or training change. Tasks 3.6 and 3.8 stay open.
- Game/mod/bridge versions: not applicable. No game, deployment, approval, training, save, Steam Cloud, private log or model was used.
- Python/package versions and configuration hash: Python 3.12.13 (~/.venvs/isaac), repository-pinned ruff, mypy, pytest and OpenSpec. No model or configuration hash.
- Scenario, split, seeds, budget, and stop conditions: simulated loopback peers and in-memory receipt records; no seeds, no learner.

## Changes

| Path | Change |
|---|---|
| src/isaac_threrisaifuture/native_receipts.py | `NativeReceiptAssembler` gains keyword-only `oracle_kinds` (default `()`, fail-closed). It must be a `tuple` or `frozenset` of known `ORACLE_KINDS` names, else `ProtocolError`. `_take_event` raises `ProtocolError("Native oracle event kind was not requested")` for any other kind after decode and the session/epoch/room/frame context check and before the cursor or receipt is touched. The cursor is only mutated in `_finish`, so a fault leaves it uncommitted. |
| src/isaac_threrisaifuture/native_client.py | `receive_receipt` passes `oracle_kinds=self.config.native_oracle_kinds or ()`. The set is derived only from the exact kinds this consumer requested; `HelloAck.capabilities` is never consulted, so extra advertised names are not treated as negotiated. A `ProtocolError` is wrapped as `EpisodeFault` and closes the peer, as for every other receipt fault. |
| tests/test_native_receipts.py | Assembler-level cases: requested kinds accepted in wire order; each of the seven kinds accepted when requested and faulted when another kind is requested; unrequested kind faults with nothing committed (including a valid prefix); a replayed event ID does not bypass the kind check; the default assembler rejects every native event; an event-free receipt still completes without kinds; invalid `oracle_kinds` rejected at construction. |
| tests/test_native_client.py | Production `NativeStepClient` cases: requested kinds accepted; a kind the peer advertised but the config did not request faults before commit and closes the client; no requested kinds rejects every kind; an event-free receipt still completes without requested kinds. |
| openspec/changes/episode-lifecycle/design.md | New subsection "Receipt kind enforcement (offline subtask 3.13, 2026-10-19)" at the end of the receipt socket reader section. |
| openspec/changes/episode-lifecycle/specs/episode-lifecycle/spec.md | New requirement "Native receipts accept only requested oracle kinds" with four scenarios. |
| openspec/changes/episode-lifecycle/tasks.md | Offline subtask 3.13 accepted after Windows `Check.ps1` and primary review. 3.6 and 3.8 untouched. |
| reports/2026-10-19-native-oracle-kind-receipt-offline.md | This report. |
| tests/test_native_receipt_reader.py | f1, fixture-only: imports `ROOM` instead of `NATIVE` from `test_native_client` and aliases `NATIVE = ROOM`; adds `KINDS = ("room_cleared",)`; the loopback peer also advertises `oracle_kind_capability(kind)` for `KINDS`; the three direct assembler constructions pass `oracle_kinds=KINDS`. 31 lines changed; no assertion changed. |
| tests/test_native_outbox.py | f1, fixture-only: the one assembler construction passes `oracle_kinds=("room_cleared",)`. 7 lines changed; no assertion changed. |

`native_events.py` and `observer_client.py` were not needed. An unrestricted `None` default for `oracle_kinds` was rejected so a future caller cannot accept every kind silently. The reader and outbox fixture edits were first applied, reverted on 2026-10-19 after the coordinator scope review, and re-applied unchanged under f1.

## Behavior

- Allowed set = exactly `config.native_oracle_kinds` (empty when `None`). `receive_receipt` already requires a negotiated peer, and `accept()` already required `oracle_<kind>_v1` for every requested kind, so the requested set is also the negotiated set. Extra advertised names, including all seven kind names with an empty request, do not widen it.
- Without requested kinds, any native oracle event faults; a receipt with no events still completes with the unchanged completion-watermark behavior.
- Identity, ordering, session/epoch/room/frame-interval and watermark checks are unchanged and still run first for the event; the kind check adds one rejection.
- Default and non-native observation paths, `NativeOracleEvent` separation from policy frames and ordinary recordings are unchanged. An absent kind is never turned into a negative outcome.
- Recording wire/file format is unchanged; see follow-ups.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Baseline before edits | Seven native test files on a Python 3.11 verification-only shim (project files unmodified) | 0 | passed | 305 passed. Retained for lineage only; the shim is not a project check. |
| Scope-only focused tests (pre-f1) | `PYTHONDONTWRITEBYTECODE=1 ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_native_receipts.py tests/test_native_client.py` | 0 | passed | 120 passed (new and existing cases in the two originally allowed test modules). |
| Scope-only affected modules (pre-f1) | same pytest, `tests/test_native_receipt_reader.py tests/test_native_outbox.py` without fixture edits | 1 | failed | 7 failed, 77 passed; every failure is `ProtocolError: Native oracle event kind was not requested`. Resolved by f1. |
| Scope-only full suite (pre-f1) | same pytest, `-m "not game"` | 1 | failed | 7 failed, 1274 passed, 13 skipped; the same 7 failures. Resolved by f1. |
| f1: affected modules | `PYTHONDONTWRITEBYTECODE=1 ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_native_receipt_reader.py tests/test_native_outbox.py` | 0 | passed | 84 passed. |
| f1: focused tests | `PYTHONDONTWRITEBYTECODE=1 ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_native_receipts.py tests/test_native_client.py tests/test_native_receipt_reader.py tests/test_native_outbox.py tests/test_native_negotiation.py tests/test_oracle_negotiation.py tests/test_native_events.py` | 0 | passed | 342 passed (305 baseline + 37 new). |
| f1: full offline suite | `PYTHONDONTWRITEBYTECODE=1 ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q -m "not game"` | 0 | passed | 1281 passed, 13 skipped (optional isolated-Lua decoder tests need `ISAAC_JSON_LUA`). Windows `Check.ps1` remains authoritative. |
| Lint | `~/.venvs/isaac/bin/python -m ruff check --no-cache src tests scripts/smoke_rl.py` | 0 | passed | All checks passed. |
| Format | `~/.venvs/isaac/bin/python -m ruff format --no-cache --check src tests scripts/smoke_rl.py` | 0 | passed | 105 files already formatted. |
| Types | `~/.venvs/isaac/bin/python -m mypy --platform win32 --cache-dir ~/.cache/isaac-mypy` | 0 | passed | No issues in 44 source files. |
| Whitespace | `git diff --check -- src tests openspec/changes/episode-lifecycle reports` | 0 | passed | No whitespace errors (only the existing CRLF autocrlf warnings for the three OpenSpec files, which keep CRLF). |
| OpenSpec strict | `XDG_CONFIG_HOME=$PWD/.tooling OPENSPEC_TELEMETRY=0 node ~/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js validate episode-lifecycle --strict` (the pinned CLI used by scripts/check.sh; `./scripts/OpenSpec.ps1` is PowerShell/Windows-only and `pwsh` is not installed here) | 0 | passed | "Change 'episode-lifecycle' is valid". The first run failed strict because the new requirement text exceeded 500 characters; it was shortened and the detail moved into scenarios. |
| OpenSpec all items | same CLI, `validate --all --strict` | 0 | passed | 30 passed, 0 failed. |
| Windows quality gate (after f1) | `./scripts/Check.ps1` with isolated `TEMP`/`TMP` | 0 | passed | 1213 passed, 14 optional isolated-Lua skips; Ruff, formatting, mypy, dependency consistency and embedded strict OpenSpec passed. |
| Real-game receipt | Any Lua peer or Isaac session | N/A | not_run | Out of scope; no Lua producer advertises any kind. |

A pre-existing earlier attempt with the repository's `node_modules` copy of OpenSpec failed with `EPERM` on the SMB share before the mirrored CLI was used; that is an environment limit, not a validation result.

## Test coverage map

- Accepted: each of the seven kinds when exactly that kind is requested; two requested kinds interleaved in wire order; at both assembler and production `NativeStepClient` level.
- Rejected: every other kind for each requested kind; an advertised-but-unrequested kind (client level, peer advertises all seven names); every kind with no requested kinds (assembler default and `native_oracle_kinds=None`).
- Uncommitted on fault: the cursor's `last_id` and the receipt result are unchanged, a valid prefix before the bad event is not committed, a replayed event ID does not bypass the check, and the client closes with `_receipts == 0`.
- Unchanged: an event-free receipt completes without kinds; invalid `oracle_kinds` types, strings, lists, unknown names are rejected at construction.

## Needs input (first pass, resolved by f1)

Historical record. The original allowed-write scope was not sufficient. After reverting the fixture edits the two existing modules failed, because their fixtures feed `room_cleared` events through assemblers and loopback peers that request no kinds, which the task requires to be rejected ("If no kinds were requested, native oracle events are not accepted"). The worker stopped and requested authorization; the Windows coordinator granted it in f1 for exactly the two paths below, and the edits were re-applied as documented here.

| Test | Why it fails without a fixture edit |
|---|---|
| tests/test_native_receipt_reader.py: `test_split_and_coalesced_records_yield_a_receipt_and_no_outbound_bytes`, `test_sequential_receipts_with_replayed_event_are_deduplicated`, `test_late_receipt_is_rejected_before_the_cursor_advances` | They use `NativeStepClient` with `NATIVE` (no kinds) and a loopback peer in this file that advertises no `oracle_*` names. Fixing them needs the peer to advertise `oracle_room_cleared_v1` and the config to request `room_cleared`; `accept()` rejects a requested kind the peer did not advertise, so the peer in this file must change. |
| tests/test_native_receipt_reader.py: `test_guard_runs_once_after_validation_and_before_the_cursor_advances`, `test_guard_error_leaves_the_cursor_and_fails_the_assembler`, `test_guard_induced_external_cursor_mutation_is_detected` | Direct `NativeReceiptAssembler` constructions with the fail-closed default. |
| tests/test_native_outbox.py: `test_outbox_records_complete_a_bounded_consumer_receipt[32]` | The direct `NativeReceiptAssembler` construction with the fail-closed default. |

Authorization requested then (granted by f1), exactly two extra paths, fixture-only edits that change no assertion and no production behavior:

- `tests/test_native_receipt_reader.py`: import `ROOM` instead of `NATIVE` from `test_native_client` and alias `NATIVE = ROOM`; add `KINDS = ("room_cleared",)`; have the loopback peer also advertise `oracle_kind_capability(kind)` for `KINDS`; pass `oracle_kinds=KINDS` in the three direct assembler constructions.
- `tests/test_native_outbox.py`: pass `oracle_kinds=("room_cleared",)` in the one assembler construction.

With exactly those edits (applied, reverted for scope review, then re-applied under f1), the 7 tests pass, the focused set is 342 passed, the full offline suite is 1281 passed with 13 skipped, and ruff, ruff format and mypy are clean.

Alternatives considered and not chosen: making `oracle_kinds` default to unrestricted (`None`) would keep those tests green without edits but makes the receipt path fail-open for any caller that forgets the argument, contradicting the requirement; changing the shared `NATIVE` config in `tests/test_native_client.py` cannot fix the reader-file peer, which would still not advertise the kind.

## f2 (review feedback, 2026-10-19)

The Windows review of f1 passed `scripts/Check.ps1` (1213 passed, 14 optional isolated-Lua tests skipped) and `scripts/OpenSpec.ps1 validate --all --strict` (30/30). One public-interface mismatch remained: `NativeReceiptAssembler.__init__` annotated `oracle_kinds` as `Collection[str]` while runtime validation accepts only `tuple` or `frozenset`.

- Scope: only `src/isaac_threrisaifuture/native_receipts.py` and this report. No behavior, protocol, specification, fixture or other path changed; the default `()` and the construction-time validation (`ProtocolError` for non-tuple/frozenset, non-`str` or unknown names) are untouched. `agent-status.json` and `subagent_report.md` were not modified. No commit, push, archive, install, game launch or nested worker.
- Change: the annotation is now `oracle_kinds: tuple[str, ...] | frozenset[str] = ()`; the then-unused `Collection` import was removed (`from collections.abc import Callable`). `native_client.py` still passes `self.config.native_oracle_kinds or ()` and type-checks unchanged.

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| f2: focused tests | `PYTHONDONTWRITEBYTECODE=1 ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_native_receipts.py tests/test_native_client.py tests/test_native_receipt_reader.py tests/test_native_outbox.py tests/test_native_negotiation.py tests/test_oracle_negotiation.py tests/test_native_events.py` | 0 | passed | 342 passed. |
| f2: full offline suite | `PYTHONDONTWRITEBYTECODE=1 ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q -m "not game"` | 0 | passed | 1281 passed, 13 skipped (optional isolated-Lua decoder tests need `ISAAC_JSON_LUA`; Windows counts differ because its Lua tests run). |
| f2: lint | `~/.venvs/isaac/bin/python -m ruff check --no-cache src tests scripts/smoke_rl.py` | 0 | passed | All checks passed. |
| f2: format | `~/.venvs/isaac/bin/python -m ruff format --no-cache --check src tests scripts/smoke_rl.py` | 0 | passed | 105 files already formatted. |
| f2: types | `~/.venvs/isaac/bin/python -m mypy --platform win32 --cache-dir ~/.cache/isaac-mypy` | 0 | passed | No issues in 44 source files. |
| f2: whitespace | `git diff --check -- src tests openspec/changes/episode-lifecycle reports` and `git diff --check -- src/isaac_threrisaifuture/native_receipts.py` | 0 | passed | No whitespace errors (only pre-existing CRLF autocrlf warnings for other files). |
| f2: OpenSpec strict | `XDG_CONFIG_HOME=$PWD/.tooling OPENSPEC_TELEMETRY=0 node ~/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js validate episode-lifecycle --strict` (pinned CLI as in scripts/check.sh; `./scripts/OpenSpec.ps1` is Windows-only) | 0 | passed | "Change 'episode-lifecycle' is valid". |
| f2: Windows quality gate | `./scripts/Check.ps1` with isolated `TEMP`/`TMP` | 0 | passed | 1213 passed, 14 optional isolated-Lua skips; the coordinator reran after the annotation correction. |
| Windows explicit strict OpenSpec | `./scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed | All 30 OpenSpec items validated. |

Changed files in f2: `src/isaac_threrisaifuture/native_receipts.py` (two lines: the import and the annotation) and this report. Limitation: the annotation change is not runtime-observable; mypy and the unchanged validation tests are the evidence. 3.13 is accepted after Windows `Check.ps1` and primary review.

## Limitations and follow-ups

- The f1 fixture edits restore the affected offline suite (1281 passed); task 3.13 was accepted after Windows primary review.
- Windows `Check.ps1` and primary review are complete for 3.13; no real-game integration was run or accepted.
- The negotiated set is not persisted in native recording metadata and `NativeStepReceipt` carries no kind coverage. design.md says consumers receive the set with the session and any native recording; persisting it changes the recording format and is a separate follow-up scope, as is carrying coverage on the receipt.
- Requested is not delivered: a requested kind proves nothing about producer coverage, delivery, event identity or a transaction barrier, and an absent event stays unknown rather than negative.
- Tasks 3.6 (Lua export) and 3.8 (native transaction multiplexing) stay open and runtime-ineligible; the 16-entry `HelloAck` cap is unchanged.
- Self-review against the diff: only the originally listed paths plus the two f1-authorized fixture files changed; no assertion or production behavior changed in the fixture files; the production client path, not a new helper, is exercised by the tests.
