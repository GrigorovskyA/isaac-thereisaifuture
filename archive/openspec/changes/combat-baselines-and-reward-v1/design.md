## Context

`IsaacCombatEnv` accepts a `RewardAccountant` and passes it oracle events per step. Coefficients live in `configs/reward-v1.yaml`.

## Decisions

- Enemy identity is `(entity_id, spawn_generation)`. HP removed per enemy is capped at its initial HP from the `enemy_spawned` event; damage for an unknown enemy earns nothing.
- Active combat time is charged only while at least one known enemy is alive and the player is not dead.
- Identical events (same kind, frame, entity, amount, source) are deduplicated. Known ceiling: two truly identical simultaneous events collapse; upgrading requires an event sequence id in the protocol.
- Only damage with source `enemy` is penalized, so self-damage and pickups are not mixed into the combat reward.

- Scenarios live in `scenarios.py` as a frozen tuple with a version string (`synthetic-combat-v1`); splits are fixed in code, disjoint, and each has difficulty levels 1-3. Enemy count/HP are toy values.
- `RandomPolicy` and `ScriptedPolicy` (label `scripted-baseline`) implement a small `Policy` protocol. The scripted policy reads only the encoded observation (nearest enemy slot), shoots along the dominant axis and strafes when close. It is a comparison bar, not a strategy that replaces learning.
- `evaluate(policy, env_factory, scenarios, episodes, seeds)` runs `episodes` episodes per scenario and seed with per-episode seed `seed * 10000 + index`, one split per call. Metrics: clear rate with Wilson 95% CI, mean damage taken, mean return, deaths, timeouts. `EpisodeFault` episodes are recorded as `fault`, counted separately and excluded from the rate denominator. The report is a dataclass tree with `to_dict()` for JSON.

## Risks

- Coefficients are hypotheses; the real event stream may differ from the synthetic one.
