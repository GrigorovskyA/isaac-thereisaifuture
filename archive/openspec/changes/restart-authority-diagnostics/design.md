# Design

## Context

See proposal.md and reports/2026-10-18-combat-gated-training.md. Production Lua
currently clears approval in MC_PRE_GAME_EXIT unless live.on and restart.awaiting
are both present. close clears live.on; POST_GAME_STARTED consumes awaiting.
The existing test stub synchronously executes exactly exit then start from
Isaac.ExecuteCommand. It cannot establish actual engine ordering or explain the
second native start. The existing callback trace lasts only ten seconds and
records per-frame events; it is unsuitable for a two-minute operator wait.

## Goals / Non-Goals

**Goals:** capture rare lifecycle decisions through a bounded operator handoff,
distinguish missing approval from inactive state/expiry, and reproduce candidate
callback sequences offline with explicit simulated labels.

**Non-Goals:** repair authorization, extend limits, restore approval from disk,
add automatic retries, change reward or train another model. A diagnostic record
is a bridge fact and cannot attest engine cause, manual input or physical release.

## Decisions

1. Use a separate literal-true Config.lifecycle_diagnostics flag, default false.
   Its private bounded state starts on the first relevant event and survives
   close/reconnect and epoch changes. Maximum 256 emission attempts, 768 bytes
   per record, twenty minutes from the initial monotonic clock. A stop record
   consumes a slot. No per-frame/input logging, file writes or new wire field.
   Reusing callback_trace would exhaust its budget before the failure window.
2. Record event ID, event name, monotonic milliseconds, epoch/room, safe session
   identity and frame or explicit unavailable marker. Record active/phase,
   live mode, approval present/loaded, expiry/lease state, boolean eligibility,
   awaiting epoch/deadline, pending epoch, attempts, disabled and armed state.
   Use fixed enumerations and numeric/boolean fields only; exclude user evidence,
   approval payloads, paths and arbitrary exception strings.
3. Capture callback entry and exit for game-end, pre-exit and post-start; record
   dispatch before/after and hello state before capability validation. Emit the
   actual preserve/drop decision at the existing branch, without evaluating a
   replacement authorization rule. Bound and correlate restart IDs with existing
   attempt counters; do not create another command path. A callback with no
   awaiting dispatch must remain explicitly uncorrelated.
4. Guard the whole diagnostic operation with pcall and a reentrancy latch; a
   read/sink failure permanently disables only the diagnostic state. Attempt
   budgets count failures. Tests compare enabled/disabled action/restart/wire
   outcomes and inject sink, clock, frame and recursive failures. Diagnostic
   reads must never bypass or prevent the original release/invalidation branch.
5. Extend the test harness with explicit event schedules. Cover expected single
   exit/start, second exit/start after confirmation, duplicate pre-exit before
   confirmation, start-before-exit and disconnect around callbacks. These are
   candidate traces, not a claim about the observed engine sequence. Preserve
   current semantics even when a trace reveals an undesirable refusal; document
   it for a separate fix rather than changing guards in this task.

## Risks / Trade-offs

- Logging may perturb timing -> rare events only, fixed limits, default off;
  offline failures do not propagate into cleanup.
- Two identical callback counts do not establish engine cause -> preserve native
  log alongside ordered records; report unknown origins honestly.
- Generic hello refusal may hide other validation failures -> log eligibility
  plus safe facts, classify remaining failures as other_validation, never guess.
- Normal-exit invalidation is essential -> regression tests retain refusal and
  prove no disk reload, renewed lease or restart budget under diagnostics.

## Migration Plan

No protocol/schema/dependency migration. Implement and review offline first.
Deploy only after normal operator exit and process-absence checks, with local
backup and source/installed hash readback. Enable diagnostics deliberately for a
separately budgeted operator-present capture; manual file selection/readiness
remain required. Do not force a death to obtain a trace. If no natural restart
occurs within the budget, mark runtime acceptance blocked/not_run and stop.
Restore default-off files only while closed. No new runtime authority is granted
by this plan and the change remains unarchived until its declared evidence passes.

## Open Questions

What emitted the second native start, and which callback invalidated approval?
The current log cannot answer either question. Diagnostics are intended to make
the next observed sequence attributable; a behavior correction needs its own
review after that evidence exists.
