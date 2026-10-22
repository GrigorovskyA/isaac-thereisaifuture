## Context

AGENTS.md requires distinct terminated/truncated/fault outcomes, release of held actions on
disconnect, and fail-closed eligibility. No orchestrator or controlling LLM is allowed.

## Decisions

- **Composition**: `RunController` takes a combat callable, a `FloorPolicy`, a `BuildChooser`, an
  eligibility gate callable, and optionally secret search and a knowledge source. Floors run via
  the existing `FloorExecutor`.
- **Backend**: `RunBackend` exposes depth, won, a `FloorBackend`, resource state/offers, known
  rooms and secret attempts, and `release`. No hidden data.
- **Gate**: called before every `start_run`; any exception or non-allowed decision yields
  `ineligible` and aborts the series.
- **Budgets**: `max_decisions` bounds floor steps; a wall deadline makes later combat calls return
  timed-out. A level that does not complete truncates the run; `max_levels` exhaustion truncates.
- **Faults**: any exception (including a failed release) is `fault`, never death. Rates exclude
  faults and ineligible aborts, which are counted separately.
- **Report**: schema-versioned dict with outcome counts, win rate, depth, damage and every run.

## Risks / Trade-offs

- Wall budget is cooperative (checked at combat calls), not preemptive.

## Migration

None.
