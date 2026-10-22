## Context

AGENTS.md requires distinct terminated/truncated/fault outcomes and no hidden data in policies.
Floor-level control sits above combat and navigation.

## Decisions

- **View**: `FloorView` exposes known rooms (kind, cleared) and `exit_available`; nothing hidden.
- **Options**: `legal_decisions` enumerates deterministic legal decisions; `validate_decision`
  rejects anything else (`IllegalDecisionError`). `GO_BOSS` needs a known uncleared boss room;
  `DESCEND` needs `exit_available`.
- **Executor**: `FloorExecutor` loops policy -> `FloorBackend.run_option(decision, combat)`;
  combat is an injected `Callable[[Room], CombatOutcome]`.
- **Outcomes**: death is terminated; timeout and stuck (no legal option) are truncated; a
  `FloorFault` is a separate outcome excluded from rates in `aggregate`.
- **Loop bound**: `max_decisions` exhaustion is a timeout.
- **Baselines**: `RandomFloorPolicy(seed)` and `ScriptedFloorPolicy` (priority heuristic, labelled
  `scripted`); each decision records its source and metrics count them separately.

## Risks / Trade-offs

- The scripted priority is a heuristic baseline only; real floors need a learned policy later.

## Migration

None.
