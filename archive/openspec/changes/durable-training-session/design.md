# Design

## Context

See proposal.md. Existing live, menu and Windows identity adapters already enforce
bounded bridge actions and guarded Continue. The local overnight helper is evidence,
not a reusable production runner. Current approval serialization truncates seconds.

## Goals / Non-Goals

Implement readiness item 1 as a reusable CLI plus deterministic offline contracts.
Native qualification remains a separate pending acceptance task. Do not modify
navigation policy/caps, reward, observations, checkpoint publication or reset policy.

## Decisions

- A versioned parent process owns one worker, one lease and one Steam launch.
  Use the same Windows monotonic clock in both processes. Startup consumes the
  fixed finite window rather than extending it. Keep cleanup outside the action
  window with a bounded grace; an unresponsive worker is a fault, not completion.
- Strict manifest/config/seed/reward and exact checkpoint ID are checked before
  granting a lease. The worker resumes explicitly and verifies active Isaac.
- Atomic local status snapshots are reduced from bounded worker event reads.
  Last activity and checkpoint update timestamps remain visible. A live process
  alone yields waiting. Activity durations describe observed phases, not proof
  of continuous useful gameplay. Existing navigation gates remain authoritative.
- Add optional deadline, stop signal and progress callbacks without changing
  legacy caller behavior or policy-visible data. Save events are distinct from
  combat decisions; checkpoint updates are not improved-gameplay evidence.
- Stop file and Ctrl+C request cooperative exit. If a bounded grace fails, stop
  only the owned worker; normal owned-game close and lease removal ensure input
  cannot persist. Approval content hashes prevent deleting a replaced lease.
- Write final status before optional metrics. Each cleanup operation is isolated
  so failure cannot skip subsequent cleanup. Do not reuse old local assignments.

## Risks / Trade-offs

- Native focus/close and interrupt timing need a separately authorized five-minute
  qualification; offline fixtures cannot establish those effects.
- Full process/power loss cannot run finally; lease expiry/watchdog bound input,
  and status freshness distinguishes stale snapshots. Crash recovery is later work.
- Existing checkpoint publication is not transactional; a failed concurrent read
  retains last verified checkpoint plus an error, not a false latest claim.
- Existing navigation may stop early; expose it honestly until readiness item 2.

## Migration Plan

Add an explicit module CLI with no automatic startup, schedule or deployment.
Keep old experiment artifacts unchanged. Run targeted regressions and the full
Windows gate before committing. Rollback is removal of the explicit new entrypoint;
saved models/configuration stay compatible.
