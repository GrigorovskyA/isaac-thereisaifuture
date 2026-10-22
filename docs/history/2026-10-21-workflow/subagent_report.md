# Windows primary review: terminal-outcome-coverage-20261019-01

Status: accepted offline after primary correction (2026-10-19).

Final confirmation: the executor's frozen handoff at 2026-10-19T19:15:53Z was
followed by a fresh full Windows gate: 1802 passed, zero skips, strict 30/30;
all nine implementation/test/spec/design hashes matched before and after.
This resolves the overlapping-review rejection. Task 3.15 is accepted; no
executor continuation is requested. Mac-owned ready_for_review is retained as
the historical transfer record.

This is a Windows review entry, not a new worker report. At review time this
file's newest entry concerned native-oracle-recording-provenance, while the
task-matched result was in reports/2026-10-19-terminal-outcome-coverage.md and
agent-status.json was ready_for_review. The delivered implementation was reviewed
directly. Primary fixed ignored terminal events in the initial result: start now
faults/releases before allowing an action. Six regressions failed before the fix.
Windows Check.ps1: 1802 passed, zero skips; Ruff, format, mypy, pip and strict
OpenSpec 30/30 passed. Task 3.15 accepted; tasks 3.6/3.8 remain open. No runtime,
deployment, approvals, real training, new executor, commit or push.

---

# Subagent report: native-oracle-recording-provenance-20261019-01

Status: ready_for_review (offline recording provenance; no runtime access).

- Persisted the exact requested kind tuple in new native recording manifests; empty tuples are explicit `[]`, out-of-set events are rejected on write/replay, and legacy manifests without the field remain unknown (`None`) and readable. Non-native manifest bytes remain unchanged.
- Verification: focused recording/replay tests 123 passed; full offline suite 1316 passed, 13 skipped. Ruff, format, mypy, `git diff --check`, and pinned OpenSpec strict validation passed (episode-lifecycle valid; all 30 items passed).
- Windows `Check.ps1` remains unrun. Subtask 3.14 stays unchecked; tasks 3.6 and 3.8 remain open and runtime-ineligible.
- **Review note:** the evidence report discloses one `git checkout` use on `openspec/changes/episode-lifecycle/tasks.md` to repair a line-ending edit. The current diff shows only the added task line, but the Windows reviewer should assess this deviation; the file currently has LF endings.
- Full evidence: `reports/2026-10-19-native-oracle-recording-provenance-offline.md`.

---

# Subagent report: native-oracle-kind-receipt-20261019-01-f2

Status: ready_for_review (narrow public type-annotation correction).

- Changed `NativeReceiptAssembler.oracle_kinds` to `tuple[str, ...] | frozenset[str]`, matching the runtime validation. The default and validation behavior are unchanged.
- Verification: focused native tests 342 passed; full offline suite 1281 passed, 13 skipped. Ruff, format, mypy, `git diff --check`, and pinned OpenSpec strict validation passed.
- Windows `Check.ps1` was not run; the Windows coordinator reruns it for acceptance. Task 3.13 remains unchecked.
- Full evidence: `reports/2026-10-19-native-oracle-kind-receipt-offline.md`.

---

# Subagent report: native-oracle-kind-receipt-20261019-01-f1

Status: ready_for_review (f1 continuation; offline receipt hardening only).

- Applied the Windows-authorized fixture-only updates in `tests/test_native_receipt_reader.py` and `tests/test_native_outbox.py`: fixtures now request/advertise `room_cleared`; no assertions or production behavior changed in those files.
- Verification: affected modules 84 passed; focused native tests 342 passed; full offline suite 1281 passed, 13 skipped. Ruff, format, mypy, `git diff --check`, and pinned OpenSpec strict validation passed (episode-lifecycle valid; all 30 items passed).
- Windows `Check.ps1` and real-game receipt checks were not run. Task 3.13 remains unchecked pending Windows review; tasks 3.6 and 3.8 remain open and runtime-ineligible.
- Full evidence: `reports/2026-10-19-native-oracle-kind-receipt-offline.md`.

---

# Subagent report: native-oracle-kind-receipt-20261019-01

Status: needs_input (offline Python receipt hardening; no runtime access or Git writes).

- Enforced receipt acceptance only for kinds explicitly requested in `ObserverConfig.native_oracle_kinds`; extra `HelloAck` capabilities do not widen the allowed set. The unrequested kind faults before receipt/cursor commit.
- The worker reverted its fixture-only edits to the two test modules outside the allowed-write list. Current scoped tests: allowed modules 120 passed; affected existing modules 7 failed and 77 passed; full offline suite 7 failed, 1274 passed, 13 skipped. All seven failures use `room_cleared` fixtures without requesting/advertising that kind.
- Ruff, format, mypy, `git diff --check`, and pinned OpenSpec strict validation passed. Windows `Check.ps1` was not run.
- Requesting authorization for fixture-only updates to `tests/test_native_receipt_reader.py` and `tests/test_native_outbox.py` so existing tests request and advertise `room_cleared` without weakening fail-closed behavior. Exact edits and failures are in `reports/2026-10-19-native-oracle-kind-receipt-offline.md`.
- Episode-lifecycle task 3.13 remains unchecked; tasks 3.6 and 3.8 remain open and runtime-ineligible.

---

# Subagent report: oracle-kind-negotiation-20261019-01

Status: ready_for_review (offline Python handshake groundwork; no runtime eligibility).

- Added opt-in `ObserverConfig.native_oracle_kinds`; exact kind capability names are required only with native-episode mode and `entity_action_v1`. Existing modes/default lists and positional construction remain unchanged; old/partial peers fail before snapshot data.
- Added focused tests for all seven kinds, request validation, mode incompatibilities, old/partial peers, reconnects, unchanged modes, and 16/17-entry HelloAck boundary. Added OpenSpec requirement/design and offline subtask 3.12; tasks 3.6 and 3.8 remain open.
- Verification: focused tests 89 passed; full offline suite 1703 passed with the JSON shim; Ruff, format, mypy, `git diff --check`, and pinned episode-lifecycle strict validation passed. Windows `Check.ps1` and real-game checks remain unrun.
- Capability negotiation is only an offered contract; it proves no producer coverage, delivery or runtime eligibility. Evidence: `reports/2026-10-19-oracle-kind-negotiation-offline.md`.

---

# Subagent report: oracle-event-contract-review-20261019-01-f2

Status: ready_for_review (bounded offline wording correction; no implementation or runtime access).

- Corrected the capability count: `entity_action_v1` is the existing transport gate; no aggregate/all-kinds or transport-mode capability is added. The seven `oracle_<kind>_v1` names are seven new entries; eight other names + `entity_action_v1` + seven kinds = the existing 16-entry limit.
- The evidence report preserves the Windows default-temp `Check.ps1` failure and isolated-temp pass, plus OpenSpec 30/30 and `git diff --check` results. Feedback 2's pinned episode-lifecycle strict validation and `git diff --check` passed on Mac; `pwsh` was unavailable.
- Per-kind eligibility and exhaustion decisions, tasks 3.6/3.8, and the runtime-check limitations remain unchanged.

Full evidence: `reports/2026-10-19-oracle-event-contract-review.md`.

---

# Subagent report: oracle-event-contract-review-20261019-01-f1

Status: ready_for_review (offline design/report correction; no implementation or runtime access).

- The design names the existing `entity_action_v1` capability and requires every per-kind name to be negotiated with it. Exhaustion before `hello` omits the kind and rejects clients requiring it; exhaustion after `hello_ack` faults/closes the active session and omits the kind from later handshakes.
- Windows validation is recorded without masking the initial failure: default-temp `Check.ps1` failed with WinError 5 after 1117 passed/14 skipped; isolated-temp `Check.ps1` passed with the same counts. Windows `OpenSpec.ps1 validate --all --strict` passed 30/30 and `git diff --check` passed. No game or Lua 5.3 runtime checks ran.
- Preserved per-kind eligibility decision, tasks 3.6/3.8 unchecked, all event distinctions, and unknown-vs-negative semantics. Worker changed only the design subsection and named report.

Full evidence: `reports/2026-10-19-oracle-event-contract-review.md`.

---

# Subagent report: oracle-event-contract-review-20261019-01

Status: ready_for_review (offline design review; no implementation or runtime access).

- Recommends per-kind, exact-version capability negotiation; no `OracleEvent` kind is eligible for Lua export yet. The per-kind matrix separates all seven event kinds and distinct callback/context facts; tasks 3.6 and 3.8 remain open.
- The design subsection now records fail-closed behavior, capability/resource exhaustion, and that missing events are not negative facts without a negotiated kind and completed barrier-validated interval.
- Pinned OpenSpec strict validation passed for `episode-lifecycle` and all 30 items; `git diff --check` passed. Windows `Check.ps1` and runtime checks were not run.
- Review note: the worker briefly used `git add -N` for a report whitespace check, then reset it. Coordinator check found no staged diff; the report documents this.

Full evidence: `reports/2026-10-19-oracle-event-contract-review.md`.

---

# Subagent report: firing-trace-parser-20261019-01 (Feedback 1)

Status: ready_for_review (bounded offline parser task; no commits or runtime access).

- Feedback 1 fixed: accepts one terminal CR/LF/CRLF only; trailing whitespace and embedded line endings are rejected without echoing input. The 300-character record limit and pre-copy bound remain.
- Final focused tests: 150 passed on Python 3.12.13 and 3.11.15; Ruff, format and pinned mypy passed. The coordinator's local rerun could not start because pytest is not installed; no dependency was added.
- OpenSpec strict validation passes on the isolated task copy; current worktree validation still fails on two overlong requirements in the coordinator's unrelated uncommitted spec edit. Windows and runtime checks remain unrun; task 4 is still unchecked.

Full evidence: `reports/2026-10-19-firing-trace-parser.md`.

Coordinator note for Windows: the Mac side can launch a fresh Sonnet 5.5 worker
for bounded non-code tasks too, including roadmap planning, prioritization, and
scope or design review. Put the objective, requested output, and boundaries in
the task file as usual.

---

# Subagent report: async-restart-training-regression-20261019-01 (feedback 1)

Status: needs_input (macOS executor; nothing committed or pushed; stopped as instructed).

Full evidence: the "Feedback 1 response" section of
`reports/2026-10-19-async-restart-training-regression-offline.md`.

- **Windows IPC: BLOCKED.**
  - The production `combat_gate._write_atomic` (`os.replace`) fails with WinError 5 when an operator reads `request.json`. The real `combat-ready` path has the same race.
  - A strict win32-only xfail reproducer was added: `test_request_replacement_succeeds_while_the_operator_reads_it`.
  - Not done, as instructed: no retries, no removal of the concurrent reader, no longer deadlines, no weaker cleanup.
  - The loopback e2e and the Lua learner tests stay unmarked and blocked on Windows.
  - Production scope needed (proposal only):
    - a bounded retry for `os.replace`;
    - readers that tolerate sharing violations;
    - `_stop` must not mask the first error;
    - a Windows concurrency test.
- **Learner over the full chain:** new tests run a real CPU RecurrentPPO over production Lua, loopback LiveClient, LiveBackend and CombatGateEnv.
  - The run crosses a death, the async restart and the reconnect.
  - `Probe` instrumentation:
    - no policy, normalizer or update call happened during waits;
    - all 32 forward calls ran in `combat_active`;
    - `obs_rms.count` is 33;
    - `episode_starts` is [0, 10].
  - Checkpoint t32 reloads. The resume runs in a fresh harness and produces a t64 child with the correct parent; `obs_rms` is 66.
  - An interrupted rollout over Lua saves nothing (4 unsaved steps).
  - Threads are joined in `finally`, and the test asserts they actually stopped.
- **Timestamp:** fixed. The stage 1-4 status was published at 06:37:29Z, not 06:40Z.
- **Checks (macOS):**
  - the test file passed 34/34 three times;
  - ruff passed;
  - check.sh: exit 0, 1435 passed;
  - OpenSpec: 29/29.
  - Not run: Windows Check.ps1/OpenSpec.ps1 and the real game.
- **Question for the primary:** authorize the production scope for the Windows-safe gate IPC fix, or accept with the blocker recorded.

---

# Subagent report: async-restart-training-regression-20261019-01

Status: ready_for_review (macOS executor; nothing committed or pushed; stopped as instructed).

Full evidence: `reports/2026-10-19-async-restart-training-regression-offline.md`; draft
`docs/EXPERIMENT_GATED_TRAINING_RECHECK_V1_DRAFT.md` (NOT AUTHORIZED / NOT RUN).

- **Tests:** new `tests/test_async_restart_training.py`, with 31 tests covering:
  - the async real order (exit +15 ms, start +111 ms) with diagnostics parity;
  - the Lua fault matrix: peer loss at 4 boundaries, the 5 s confirmation bound, wall/lease expiry, spent attempts, duplicate exit/second start, buffered commands, stale identity and accepted-hold release;
  - the Python gate/backend matrix;
  - a loopback e2e through the real LiveClient/LiveBackend/CombatGateEnv;
  - a real CPU RecurrentPPO run across an async death with resume lineage, plus a deadline-interrupted rollout.
- **STUBS:** `tests/test_lua_observer.py` gained an optional deferred scheduler; it is backward compatible.
- **Learner:**
  - obs_rms count is 1+32, so waits are never normalized;
  - observations are oracle-free;
  - checkpoint t32 reloads, and the t64 child has the correct parent;
  - the interrupted run saves nothing and reports 4 unsaved samples.
- **Mutations:**
  - 8/9 caught; production hashes were restored exactly.
  - Removing `release` only from Lua `close` is an equivalent mutant (the unarmed guard releases).
  - The initial release gap was closed with new assertions.
- **Checks:**
  - macOS `check.sh` exit 0: 1432 passed, 0 skipped. A first run failed the format check on the new file; it was fixed.
  - OpenSpec: 29/29.
- **not_run:** Windows Check.ps1/OpenSpec.ps1, and the real game/runtime.
- **Unresolved:** the 2026-10-18 two-start failure is not explained or fixed. The async timing comes from one real trace only.

---
# Subagent report: restart-authority-diagnostics-20261018-01 (feedback 1)

Status: ready_for_review (macOS executor; nothing committed or pushed; stopped as instructed).

- **Portable parity:**
  - Raw JSON line equality is replaced by an ordered, type-tagged decoded comparison. Only object key order is ignored; message and array order, keys, values and types are kept.
  - Approval creation and Lua `os.time` are frozen to one wall second.
  - A discrimination test shows a key permutation passes, while a changed value, a type change, array order, message order, a missing key and a partial tail all fail.
  - Production Lua is unchanged.
- **Delayed second exit:** new persistent simulated scenario. A confirmed restart and live rearm, with an action held, are followed by exit/start without a dispatch:
  - one command;
  - `approval_drop live=1 awaiting=na approval=1`, `corr=uncorrelated`;
  - input released;
  - the final hello is `auth=none`;
  - enabled/disabled parity holds.
- **Checks:** macOS `check.sh` exit 0, 1401 passed, 0 skipped, OpenSpec 29/29; change strict valid; 4/4 mutations caught.
- **not_run:** Windows `Check.ps1`/`OpenSpec.ps1` (2.1) and all runtime tasks.
- **Details:** "Feedback 1 response" in `reports/2026-10-18-restart-authority-diagnostics-offline.md`.

---
# Subagent report: restart-authority-diagnostics-20261018-01

Status: ready_for_review (macOS executor; nothing committed or pushed; stopped as instructed).

Full evidence: `reports/2026-10-18-restart-authority-diagnostics-offline.md`; operator doc `docs/RESTART_LIFECYCLE_DIAGNOSTICS.md`.

- **Diagnostics:**
  - New default-off `Config.lifecycle_diagnostics` (only a literal `true` enables it) in `mod/observer/main.lua`.
  - Bounded `[Isaac Future Lifecycle]` key=value records at rare points only: game-end, pre-exit and post-start entry/exit; dispatch before/after; close; hello before capability validation; restart arm/cancel/stop/timeout; and the actual `approval_preserve`/`approval_drop` and `restart_invalidate` branches (pre-mutation facts).
  - Each record carries the safe authority facts plus an `auth` explanation of the real predicate: `none`/`inactive`/`expired`/`lease`/`other_validation`/`ok`.
- **Limits and isolation:**
  - Hard limits per mod load: 256 attempts including the stop record, a 20-minute window and 768 bytes per record. Close, reconnect and epochs never renew them.
  - Emission runs under `pcall` with a reentrancy latch, so faults disable only diagnostics. No file I/O, wire fields, approval reads, or changes to authority or cleanup.
- **Tests:**
  - 34 new production-Lua scenarios with scripted `DISPATCH_EVENTS`, plus 2 diagnostics-on variants of existing restart/normal-exit tests.
  - Enabled/disabled parity holds for the wire, actions, commands and logs.
  - Sink, clock, frame and recursion faults; count, time and line bounds; and `io.open` parity are all covered.
  - 12/12 mutations caught.
- **Simulated findings** (candidates only, not engine evidence): with one dispatch, these orders all drop approval at the existing branch and refuse the live loop afterwards, with guards unchanged:
  - second exit/start;
  - duplicate exit before confirmation;
  - start-before-exit;
  - disconnect-before-exit.
- **Checks:**
  - macOS `check.sh`: exit 0, 1398 passed, 0 skipped, OpenSpec 29/29.
  - Change strict validation: valid.
  - Tasks 1.1-1.5, 2.2 and 2.3 checked; 2.1 (Windows) and section 3 unchecked.
- **not_run:** Windows `Check.ps1`/`OpenSpec.ps1`, deployment, real capture, root-cause confirmation, learning evaluation.

---
# Subagent report: combat-experience-gate-20261018-01 (feedback 1)

Status: ready_for_review (macOS executor; nothing committed or pushed; stopped as instructed).

- **Fix 1, eligibility during combat:**
  - An opt-in `LiveBackend.action_gate` veto is evaluated on fresh queued state before every action. Events are absorbed first, so damage is kept and a queued death stays terminal.
  - A veto withholds the action and releases input.
  - A post-step classification truncates on empty (including clear=false), ambiguous, paused, unavailable or a room change, with `gate_exit`/`action_withheld`. No fabricated clear or death.
- **Fix 2, deadlines:** during each handoff, `run_deadline` on the backend and `FaultTolerantEnv` is narrowed to min(run deadline, handoff cap), then restored. This bounds waits, poll reconnects, the resume reset and its reconnect loop. Both deadlines are rechecked after the reset; combat never activates after expiry; nothing is renewed.
- **Freshness:** a disconnect or a gap longer than `stale_seconds` (1 s) clears the retained state, so acks are rejected as `no_observation` until fresh state arrives.
- **Tests:** 17 new fake-clock/no-sleep behavioral tests, including both reviewer reproductions and the VecNormalize count/boundary check. 7/7 applicable mutations caught.
- **Checks:** macOS gate exit 0, 1362 passed, 0 skipped, OpenSpec 28/28; the delta spec gained 3 requirements and is strict valid. not_run: Windows `Check.ps1` and the real run.
- **Details:** "Feedback 1 response" in `reports/2026-10-18-combat-experience-gate-offline.md`.

---
# Subagent report: combat-experience-gate-20261018-01

Status: ready_for_review (macOS executor; nothing committed or pushed; stopped as instructed).

Full evidence: `reports/2026-10-18-combat-experience-gate-offline.md`; OpenSpec `combat-experience-gate-v1` (strict valid before code); operator guide `docs/COMBAT_EXPERIENCE_GATE.md`.

- New opt-in `combat_gate.py`. With `live --combat-gate`, the learner acts only in observed eligible combat. The classifier reads the oracle for management only: overflow, unknown, paused, dead, transition, cleared and empty are never combat.
- Handoff inside `reset()`:
  - releases input and issues a nonce request in `<session>/combat_gate/request.json`;
  - while waiting, sends no commands and creates no samples, normalizer updates or reward;
  - resumes only on a fresh `combat-ready --session-dir` ack bound to request, session, epoch and room while the room is combat;
  - rejects invalid, stale, replayed, predating, future, cross-session/epoch/room and not-eligible acks; spawning enemies never resume control.
- SB3: the terminal step and reward are kept, auto-reset blocks in the wait, and a rollout spans several fights before the normal update and checkpoint. `training.py` is unchanged.
- Budgets and stopping:
  - one run deadline plus the per-handoff `--gate-wait-minutes` cap (stop, no renewal or fault retry);
  - on stop: release, request marked `stopped`, summary logged;
  - an interrupted rollout logs `rollout_accounting` with `unsaved_steps`.
- `live.py`: read-only `LiveBackend.latest`/`poll`, opt-in options and wiring; defaults unchanged. `cli.py`: the flags and the `combat-ready` command.
- Tests: 15 behavioral tests, including a real synthetic RecurrentPPO update and checkpoint across several handoffs (boundaries, terminal rewards, `obs_rms.count` = 1+32, resume lineage); 9/9 mutations caught. macOS gate exit 0, 1344 passed, 0 skipped, OpenSpec 28/28.
- not_run: Windows `Check.ps1` and the real gated run. No real-game activity.

---
# Subagent report: frozen-live-runner-20261018-01

Status: ready_for_review (macOS executor; nothing committed or pushed; stopped as instructed).

Full evidence: `reports/2026-10-18-frozen-live-runner-offline.md`; OpenSpec `frozen-live-pilot-v1`; operator guide `docs/FROZEN_LIVE_PILOT.md`.

- New `live_evaluation.py` + CLI `eval-live`: attach-only, inference-only runner for one explicit frozen checkpoint (path + expected config hash, optional training seed) or `RandomPolicy`, reusing `LiveClient`/`make_live_env`. Defaults 2000 decisions / 6 min / 0 faults / assistance `unknown`; `--confirmed-save-slot 2` required; no launch, train, save, resume, latest pointer, approval write or forced restart.
- Validation, policy load and `verify_unchanged()` before listening; one absolute deadline (accept capped by it, passed to `make_live_env`); cap/deadline checked before and after `act`; attempted vs completed counts; `policy.reset` after every `env.reset` (death reconnect, timeout, fault truncation); env/client closed on every path; artifacts re-hashed in `finally` (`invalid`, exit 3).
- Private `live.jsonl`: identity, schema versions, action repeat, every hello, segments incl. final partial, faults, summary on every path; oracle only in `oracle.jsonl`. Tolerated faults are `failed` (exit 1); room/build provenance `unknown`.
- `LIVE_EVALUATION_PLAN.md` aligned: one policy per invocation, no within-session alternation, whole-session assistance label, stop before manual input; Part B criteria unchanged.
- Tests: 53 new (fake clock/peer/env, real synthetic RecurrentPPO checkpoint, one synthetic Lua+socket run); 7/7 mutations caught. macOS gate exit 0, 1329 passed, 0 skipped, OpenSpec 27/27. not_run: Windows `Check.ps1`, real pilot.
- Limitation: manifests lack action repeat; runner uses 3 (training-live-v1) and logs it. No shared API bug found; `live.py`, `checkpoint_policy.py`, `training.py` and existing tests unchanged.

---
# Subagent report: frozen-policy-evaluation-20261018-01 (feedback 1)

Status: ready_for_review (macOS executor; nothing committed or pushed).

- Fixed review finding: `CheckpointPolicy` now rejects corrupt saved normalizer state at construction (mean/variance shape and finiteness, negative variance, non-finite/nonpositive count, epsilon, clip limit, `norm_obs` off) as `CheckpointError`, without repair or clamping; `act` refuses non-finite normalized input before `predict` and keeps state.
- +22 behavioral regressions (corruption written via SB3 `VecNormalize.save` to private copies; predict patched to fail if called; zero variance stays valid); 19 fail on the pre-feedback code.
- OpenSpec delta spec/design/tasks 2.4 updated; strict valid. macOS gate exit 0, 1276 passed, OpenSpec 26/26. Windows checks not_run. Training Monitor fix unchanged.
- Details: "Feedback 1 response" in `reports/2026-10-18-frozen-policy-evaluation-offline.md`. No real-game activity; `runs/` untouched.

---
# Subagent report: frozen-policy-evaluation-20261018-01

Status: ready_for_review (macOS executor; nothing committed or pushed; stopped as instructed).

Full evidence: `reports/2026-10-18-frozen-policy-evaluation-offline.md`; OpenSpec `frozen-policy-evaluation-v1`; plan `docs/LIVE_EVALUATION_PLAN.md`.

- New `checkpoint_policy.py`: `CheckpointPolicy` (Policy interface) over one explicit RecurrentPPO checkpoint dir; reused manifest checks; `PolicyIdentity` with manifest/model/normalizer SHA-256; frozen VecNormalize applied once; recurrent carry/reset; deterministic; input/output validation; `verify_unchanged()`; lazy imports.
- New `tests/test_checkpoint_policy.py` (29): real synthetic RecurrentPPO save/load round trip plus fakes; 4 mutation checks all caught.
- Bug fixed (user-authorized, outside the assignment list): `training.train` crashed with SB3 `KeyError: 'r'` after any finished episode because the env uses `info["episode"]`; now wrapped in `Monitor`. Regression test in `tests/test_training_manifest.py` fails without the fix. `combat-ppo-training/tasks.md` 1.4 records it. Longer live training would have hit this after the first death/clear.
- OpenSpec change valid strict; tasks 1.x-4.2 done, 4.3 (Windows checks) and 5.x (real evaluation, blocked) open.
- macOS gate `scripts/check.sh`: exit 0, 1254 passed, OpenSpec 26/26. not_run: `Check.ps1`, `OpenSpec.ps1 validate --all --strict`.
- No real-game inference, control or evaluation occurred; private smoke checkpoint untouched.

---
# Subagent report: lua-step-evidence-20261018-01

Status: ready_for_review (nothing committed or pushed; stopped as instructed).

Full evidence: `reports/2026-10-18-lua-step-evidence-offline.md`; design in `docs/NATIVE_STEP_EVIDENCE.md`.

- Spec/design/unchecked task 3.10 written before code (checklist 14/22; no other task marked).
- `mod/observer/main.lua` + `metadata.xml` -> source 0.4.6-dev (installed 0.4.5-dev untouched).
- Default-off `callback_trace` gained: acceptance endpoint/deadline, once-per-frame `hold_update`, release with original `hold_seq` and frame/wall due flags, one pending release correlated to the next post-update and next nil-override input query. Same trace limits; over-long line stops instead of truncating; no wire/validation/input-return changes.
- Tests: new `tests/test_lua_step_evidence.py` (24 cases); one compatibility assertion in `test_lua_callback_trace.py`.
- Checks (Mac, /tmp copy, Python 3.11 + lupa + JSON shim): 155 Lua tests passed, 0 skipped; `luac -p` ok.
- not_run/blocked: `Check.ps1`, ruff, mypy, pinned pytest, OpenSpec strict (EPERM on SMB), all real-game checks.
- Limits: no consumed-update, neutral-input or READY claim; live acceptance needs a reviewed closed-game deploy and a separate preflight.

---

# macOS session report (2026-10-18): review of 3.10 and Mac tooling

Context: the Windows agent is out of budget. Development and pre-checks continue on
macOS against the shared checkout (`/Volumes/isaac` = `D:/isaac`). Nothing is
committed or pushed from macOS; the remote/Windows side commits.

## 1. Review of lua-step-evidence-20261018-01 (task 3.10): accepted

- Reviewed the `mod/observer/main.lua` diff against the 3.10 design/spec.
- Fix: `release_superseded` formatted `hold_seq`/`by_seq` without `trace_num`; now
  formatted through `trace_num` and fails closed (`trace_fail`) on invalid scalars.
- Note: the `trace_release` epoch/visit mismatch branch is defensive only; every
  `release()` call precedes epoch/visit changes in current callbacks.
- Line endings: the executor's shell appends left mixed CRLF/LF lines in
  `docs/NATIVE_EPISODE_PROTOCOL.md`, episode-lifecycle `design.md` and `spec.md`;
  normalized to CRLF in the working tree. Git stores LF per `.gitattributes`, so the
  diff has no whole-file churn.
- `openspec/changes/episode-lifecycle/tasks.md`: 3.10 marked `[x]` with the review
  note (checklist 15/22). `docs/STATUS.md` 3.10 paragraph updated. Review section
  appended to `reports/2026-10-18-lua-step-evidence-offline.md`.
- `agent-status.json` (ignored) state set to `accepted`.

## 2. macOS pre-check tooling

- New `scripts/check.sh`: POSIX mirror of `Check.ps1` (ruff, format, mypy
  `--platform win32`, pytest `-m "not game"`, `uv pip check`, OpenSpec strict).
  Overridable via `ISAAC_PY`, `ISAAC_JSON_LUA`, `ISAAC_OPENSPEC`.
- Local, outside the repo (SMB share cannot host them): Python 3.12 venv
  `~/.venvs/isaac` from `requirements-lock.txt` + torch 2.14.1 + lupa + editable
  package; OpenSpec 1.14.3 in `~/.cache/isaac-openspec`; test-only JSON shim
  `~/.cache/isaac-json/json.lua` (not the game file; same `decode -> value, pos`,
  `null`, `EMPTY_ARRAY`, `EMPTY_OBJECT` surface).
- Result: `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ./scripts/check.sh` exit 0:
  ruff clean, 87 files formatted, mypy (win32) 38 files clean, **1167 passed, 0
  skipped**, OpenSpec strict 24/24.

## 3. Windows still required

- `./scripts/Check.ps1` with the real game json.lua (authoritative gate): not_run.
- Deployment of source 0.5.0-dev (supersedes 0.4.6-dev) and any runtime probe: not_run.
- Live loop real-game tasks 5.1-5.5 (see section 4 and `docs/LIVE_LOOP.md`): not_run.

## 4. Live training loop (OpenSpec change `live-training-loop`)

User decisions (2026-10-18): approximate events from frame deltas; autonomous death
restart; training on save file 2. Implemented offline, nothing committed:

- `mod/observer/main.lua` + `metadata.xml` -> 0.5.0-dev: `profile_mode="training"`
  approval (no epoch, <= 8 h, `max_restarts` 1..5000); `live_loop_v1` requires exactly
  entity + safe actions + death restart; separate `oracle` block (room clear, player
  dead, enemy HP <= 64 + overflow); death/pause/stale races -> `rejected` ack instead of
  disconnect; missed heartbeat releases input; restart budget from approval, 4 s
  minimum interval; approval kept across a restart exit; 20 Hz sampling.
- `src/isaac_threrisaifuture/live.py` (new): LiveClient (reader thread), EventDeriver,
  LiveBackend, FaultTolerantEnv, approval writer, `run_live` (random/train).
- `observer_client.py`: `ObserverConfig.live_loop`; `cli.py`: `approve-training`, `live`.
- `configs/training-live-v1.yaml`, `Start-Live.cmd`, `docs/LIVE_LOOP.md`.
- Tests: `tests/test_lua_live_loop.py` (31), `tests/test_live.py` (18),
  `tests/test_live_e2e.py` (3; real main.lua in lupa over loopback incl. death ->
  restart -> reconnect and a RecurrentPPO checkpoint).
- Gate: `scripts/check.sh` exit 0, 1219 passed, OpenSpec strict 25/25.
- Docs: STATUS, README, ROADMAP, AGENTS; evidence `reports/2026-10-18-live-loop-offline.md`.
- not_run (Windows): `Check.ps1`, deploy 0.5.0-dev, `approve-training`, live random
  run >= 2000 steps, short train run (tasks 5.1-5.5).


## Primary Windows review update

Original 3.10 evidence passed 165 targeted Lua tests / 1167 full cases before the
subsequent live-loop additions. The updated 0.5.0-dev tree passed the pinned gate
with the real bundled json.lua; primary review then fixed three reproduced
live-mode defects and added five regression cases. Final Windows gate: 1224 tests,
zero skips, strict OpenSpec 25/25. Details: reports/2026-10-18-windows-live-review.md.
No installation, approval file, game launch/control or real training occurred.
Mac acceptance and authorization statements are not a substitute for the next
operator-directed runtime preflight. No change was archived.
