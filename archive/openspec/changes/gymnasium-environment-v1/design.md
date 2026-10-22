## Context

The encoder yields a fixed vector (`OBSERVATION_SIZE`) and the controller yields transitions with
distinct outcomes. The environment translates between those and Gymnasium.

## Decisions

- **Spaces**: `Box(-1, 1, (OBSERVATION_SIZE,), float32)`; `MultiDiscrete([5, 5])` matching
  `Action(move, shoot)`. Invalid actions raise `ValueError`; they are never clamped.
- **Step**: one `step` runs `action_repeat` game updates (default 3), stopping early on a terminal
  event. Synchronization is by frame ID in the controller, not sleeping.
- **Reset**: `reset(seed)` seeds the Gymnasium RNG; the environment draws a game seed from it and passes
  it to the backend. `info["game_seed_supported"]` states whether the backend honors it.
  `options={"scenario": Scenario}` overrides the sampled scenario.
- **Outcomes**: `terminated` for death/clear, `truncated` for timeout. Faults raise `EpisodeFault`;
  after a fault `step` raises `RuntimeError` until `reset`.
- **Info**: only non-oracle bookkeeping (IDs, scenario, split, outcome, overflow, clipping,
  reward components, final episode summary). Oracle events go to the optional `oracle_sink`.
- **Rewards**: a `RewardAccountant` protocol; default is no reward (0.0) so plumbing can be tested
  independent of reward design.
- **Close**: idempotent; releases control via the controller.

## Risks / Trade-offs

- The Gymnasium API has no fault channel; callers (trainer/evaluator) must catch `EpisodeFault`.
- Episode summary uses toy-room statistics until real fixtures exist.

## Migration

Additive.
