## Why

Roadmap item 16: integrate combat, floor, resource, secret and knowledge layers into one
autonomous run loop with an honest report. Offline contract only; MUST NOT be archived until
real-game evidence exists.

## What Changes

- Add `fullrun.py`: `RunBackend` protocol, `RunController`, `RunConfig`/`LevelBudget`,
  `RunOutcome`, `RunRecord`, `build_report`.
- Add `tests/test_fullrun.py` with an explicitly synthetic backend.

## Scope and non-goals

- In scope: eligibility gate before start (injected, fail-closed), per-level decision and wall
  budgets, outcome taxonomy, release on every exit, JSON run report with every episode.
- Out of scope: a real `RunBackend`, target character/difficulty/route/final-boss choice (needs
  real-game evidence), the success threshold (MUST be fixed before test evaluation), training,
  any orchestrator or LLM.

## Dependencies and risks

- Uses floors, resources, secrets, eligibility and (optionally) knowledge contracts.
- Risk: the synthetic backend hides real reset, transition and item-room complexity.

## Acceptance criteria

- Offline: a denied or failing gate prevents `start_run` and aborts the series.
- Offline: death, truncation, fault and ineligible-abort are distinct and reported separately.
- Offline: `release` is called after every episode, including faults.
- Offline: the report lists all episodes, failures included, and round-trips through JSON.
- Pending real game: a series of complete runs without manual input; one victory or seed does not
  establish competence.
