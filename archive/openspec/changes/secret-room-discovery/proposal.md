## Why

Roadmap item 15: derive secret-room candidates from known geometry, manage bombs, and measure success per bomb against a random valid-wall baseline without leaking hidden layout to the policy.

## What Changes

- Add `secrets.py`: `rank_candidates`, `SearchBudget`, `run_search`, `AttemptRecord`, `evaluate_against_truth`.
- Add `tests/test_secrets.py` with a synthetic floor generator (fixture only).

## Scope and non-goals

- Offline contract only, over plain grid-coordinate tuples. No real bomb placement, no opening/entry events, no rewards (see RL_DESIGN).
- This change MUST NOT be archived until real-game evidence exists.

## Risks

- Synthetic floors place the secret by the same adjacency heuristic, so the measured advantage is optimistic; real floors need labelled held-out evidence.
- Exact Isaac secret-room placement rules are not verified here.
