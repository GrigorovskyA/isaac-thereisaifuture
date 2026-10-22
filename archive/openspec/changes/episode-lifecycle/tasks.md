## 1. Implementation (offline)

- [x] 1.1 Add `episodes.py` (Scenario, Action, GameBackend, EpisodeController, outcomes, faults).
- [x] 1.2 Add `sim.py` toy backend with fault injection.
- [x] 1.3 Write tests/test_episodes.py (outcomes, identity, release, 100-episode loop, fault separation).

## 2. Checks (run on Windows)

- [x] 2.1 Run the new tests.
- [x] 2.2 `./scripts/OpenSpec.ps1 validate episode-lifecycle --strict`.
- [x] 2.3 `./scripts/Check.ps1` passes.

## 3. Native offline code tasks (partially implemented)

- [x] 3.1 Extend `ObserverConfig`/handshake models for the combined capability with fail-closed negotiation tests.
- [x] 3.2 Add a native step result type: requested repeat, elapsed updates, accepted/completed status.
- [x] 3.3 Add typed bounded oracle event decoding, per-session deduplication and policy/oracle separation tests.
- [x] 3.4 Add an adapter that filters paused/unavailable snapshots within a deadline using a fake peer; stale active frames fault.
- [x] 3.5 Add explicit unsupported errors for start/reset without authority; test that no command is sent.
- [ ] 3.6 Lua-side capability and event export, only after the export eligibility gate in `design.md` is satisfied.
- [x] 3.7 Add required completion event watermark and strict cursor-barrier validation with offline tests.
- [ ] 3.8 Implement bounded native transaction multiplexing after attach/event ordering and authority contracts are frozen; simulated-peer tests.

- [x] 3.10 Offline bounded Lua step-evidence hooks (acceptance, post-update, release/input facts inside `callback_trace`; source 0.4.6-dev; no consumption/readiness claim, no runtime acceptance). Primary review on macOS: one trace_num fix; scripts/check.sh passed 1167 tests with a JSON shim, ruff, mypy (win32) and strict validation 24/24; Subsequent primary Windows gate passed 1224 tests and strict 25/25; runtime probe remains not_run. See reports/2026-10-18-windows-live-review.md.
- [x] 3.9 Offline pure native step lifecycle reducer (`native_step_lifecycle.py`): typed facts, absorbing outcomes, release-required flag, 64-fact bound; unwired, no engine evidence (primary review, 1133 Windows tests and strict validation passed; no runtime integration).
- [x] 3.11 Clarify native-step fact provenance and distinguish bridge hold removal from neutral final game input; specification/design/documentation only, no runtime claim. Windows Check.ps1 and strict OpenSpec validation passed; see reports/2026-10-19-native-step-evidence-contract.md.
- [x] 3.12 Offline Python per-kind `OracleEvent` negotiation groundwork: opt-in `ObserverConfig.native_oracle_kinds`, exact `oracle_<kind>_v1` names plus `entity_action_v1`, local rejection and fail-closed peer tests, 16-entry ack boundary test. Windows `Check.ps1` passed 1176 tests with 14 optional isolated-Lua skips; all-items strict OpenSpec passed 30/30. Handshake only: no Lua advertisement, event emission, producer coverage or runtime eligibility; tasks 3.6 and 3.8 stay open. See reports/2026-10-19-oracle-kind-negotiation-offline.md.
- [x] 3.13 Offline Python native receipt kind enforcement (accepted after Windows primary review): `NativeReceiptAssembler(oracle_kinds=...)` (default empty; tuple/frozenset of known kinds) faults a `native_oracle_event` of an unrequested kind before any cursor/receipt commit, and `NativeStepClient.receive_receipt` passes exactly `ObserverConfig.native_oracle_kinds` (nothing when unset), never extra `hello_ack` names. Windows `Check.ps1`: 1213 passed, 14 optional isolated-Lua skips; all-items strict OpenSpec: 30/30. Python only: no Lua advertisement or emission, recording-format change, producer coverage or runtime eligibility; tasks 3.6 and 3.8 stay open. See reports/2026-10-19-native-oracle-kind-receipt-offline.md.
- [x] 3.14 Offline native oracle recording provenance (accepted after Windows primary review): new `native_oracle_events` recordings persist the exact requested `OracleEvent` kind tuple in the manifest (`native_oracle_kinds`; `[]` means none requested), the writer and replay reject an event outside an explicit list, and a legacy native manifest without the field decodes as unknown (`None`), not empty. `policy_frames` and `oracle_events` manifests are unchanged. Windows `Check.ps1`: 1248 passed, 14 optional isolated-Lua skips; all-items strict OpenSpec: 30/30. A persisted request is not producer coverage, delivery or runtime eligibility; tasks 3.6 and 3.8 stay open. See reports/2026-10-19-native-oracle-recording-provenance-offline.md.
- [x] 3.15 Offline coverage-aware terminal outcomes (accepted after frozen Windows review): `StepResult.terminal_coverage` explicitly covers `player_died`/`room_cleared`, defaulting to unknown; coverage gaps persist across the episode. Summary facts are tri-state, unresolved clears/limits are `unknown` (truncated, released), and fully covered synthetic behavior is preserved. LiveBackend retains no coverage claim. Evaluation report v2 counts unknown separately from faults and known outcomes, excludes it from the clear-rate/Wilson denominator, and retains non-fault damage/return means. A terminal initial result faults/releases before any action (six reproduced regressions). Unknown cannot satisfy minimum-valid gates; thresholds and curriculum.py are unchanged. After frozen handoff 2026-10-19T19:15:53Z, Windows Check.ps1 passed 1802 tests, zero skips, plus lint/format/mypy/pip and strict OpenSpec 30/30; all nine implementation/test/spec/design hashes matched before and after. Offline only: no native producer, Lua export, runtime eligibility, reward/checkpoint change or real training; tasks 3.6 and 3.8 stay open. See reports/2026-10-19-terminal-outcome-coverage.md.

Task 3.6 remains open. The per-kind capability decision is frozen in
`design.md` and `reports/2026-10-19-oracle-event-contract-review.md`. The installed
callback names and offline audit identify candidates, not event semantics. No
existing `OracleEvent` kind currently has a complete verified Lua producer
mapping; do not emit native oracle envelopes or advertise an all-kinds capability
from diagnostic facts. Establish bounded runtime evidence for every exported
kind, identity, attach baseline, event order/delivery and cleanup. Offline tests
cannot replace that evidence. Task 3.8 also remains open until attach/event
ordering and authority contracts are frozen.

A later passive 0.5.0-dev runtime probe captured real damage/HP, NPC
kill/removal/death, clean-award and room callbacks, but one run did not establish
identity, semantics, delivery or a transaction barrier. Death/revival, floor and
game-end scenarios were not observed. This partial evidence does not check off
3.6 or 3.8; see reports/2026-10-19-oracle-probe-live-runtime.md.

Task 3.8 component evidence: the offline receipt assembler/reader and producer
outbox are implemented. The outbox retains neutral-time events, stages explicit
intervals, bounds records/bytes and faults on late events or delivery misuse.
Engine attach ordering, sender and terminal/short-step semantics remain open;
this is not completion of task 3.8. See reports/2026-10-17-native-event-outbox.md
and reports/2026-10-17-native-oracle-api-audit.md.

## 4. API/runtime probes (pending implementation and current-instance checks)

The default-off passive oracle probe is implemented with isolated Lua tests;
docs/ORACLE_PROBE.md defines the bounded manual run and cleanup. This prepares
4.1 only; no runtime scenario or native outcome is accepted from offline tests.
Activation now uses explicit oracle_probe_v1 negotiation with one permanent
source-matching installation. Mode switching needs no source patch or cleanup copying;
the same one-shot budgets apply. Live explicit activation passed on 0.4.4-dev;
the partial recording does not complete the lifecycle scenarios below.
Observer 0.4.4-dev adds bounded post-update HP samples with explicit unavailable
statuses and reference-cleanup tests. This is diagnostic preparation, not realized
damage or an accepted event/step barrier.
The live run captured 106 deferred samples but demonstrated old HP at the first
post-update before changed HP at later kill callbacks. Diagnostics reached their
count limit; observation then ended early after logged game over/run exit.
Death/revival/floor diagnostic coverage remains unaccepted. See
reports/2026-10-18-post-update-hp-runtime.md. Next offline work should define bounded
later-frame settlement observations and unavailable/transition semantics.

- [ ] 4.1 Observation-only probe: callback order and snapshot status in death, revival and room/floor transitions.
- [ ] 4.2 Reuse accepted base sampling evidence; verify new step completion timing and pause behavior without assuming callback order.
- [ ] 4.3 Bounded action probe for accepted versus completed status on the approved ordinary profile.

Offline subtask 4.4 is separate from the original 12/19 tasks; it does not accept
another runtime scenario. With offline subtasks 3.9 and 4.4 accepted, the current checklist is 14/21. It adds the later-frame HP diagnostic to source 0.4.5-dev;
reviewed 0.4.5-dev is installed after closed-game backup/hash guards. A bounded
manual-combat run verified later-frame raw sampling and explicit removed facts;
593 snapshots completed normally, with 87 changed-HP windows. Death/revival and
broader transition/step checks remain unfinished; task 4.1 is not accepted. See
reports/2026-10-18-later-frame-hp-runtime.md.

- [x] 4.4 Offline later-frame HP diagnostic: design, production-Lua tests and source 0.4.5-dev (primary review; 983 tests and strict validation passed; deployed, bounded raw sampling verified; lifecycle/step acceptance pending).

## 5. Real-game evidence (blocked)

- [ ] 5.1 Implement the real-bridge `GameBackend` after reset/start authority and training isolation are verified.
- [ ] 5.2 100 consecutive short real episodes without manual recovery; evidence report; archive.
