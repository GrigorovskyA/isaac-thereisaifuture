## Decisions

- Score = count of adjacent known rooms for empty in-bounds cells (13x13). Default needs >=2 (ordinary); `min_neighbors=1` is the exceptional-layout opt-in.
- Policy functions take only known cells; the search talks to the environment through a callback. Oracle labels (`FloorLabel`) are accepted only by `evaluate_against_truth`.
- Budget: max bombs and max steps; stop reasons `found`, `bombs_exhausted`, `steps_exhausted`, `no_candidates`. Tried cells are never retried.
- Baseline: seeded shuffle of all valid walls (empty cells next to a known room), same budget.
- Metrics: discovery rate and found-per-bomb for both arms.
