## Context

At 254k steps of reward v11 the agent leaves the start room but still stalls in 64% of the
episodes, and the door pull is weak: a walk to the door gains about 0.9. Half of all steps are
the idle tail of a stall, and a death at one half heart is cheaper than a stall.

## Change

- Door shaping coefficient 2 -> 4. The potential is `Phi = -coefficient * cost`, so the pull per
  room crossed doubles. It stays the only potential-based term, so the optimal policy does not
  change (Ng et al. 1999). Max |Phi| = 4 * (1 + 5) = 24, still far below `floor_first_entered` 30
  and the sum of clears.
- Stall limit 40 s -> 30 s, stagnation -0.25 -> -0.39 per second: the floor is
  `0.39 * (30 - 12)` = 7.02, as before (7.0), reached sooner. The idle tail of a stall shrinks by
  a quarter.
- Stall restart -5 -> -4 and death -10 -> -11 restore the order stall > death at every health.

## Cost balance

| Event | v11 | v12 |
| --- | --- | --- |
| Stall restart | -5.0 | -4.0 |
| Stagnation floor | -0.25 * (40 - 12) = -7.0 | -0.39 * (30 - 12) = -7.02 |
| Full stall | -12.0 (-12.3 with time) | -11.02 (plus time) |
| Death, 1 half heart of hits | -10.5 | -11.5 |
| Death, 6 half hearts of hits | -13.0 | -14.0 |
| Death cheaper than a full stall | yes at 1 half heart | never |

`death + n * player_damage_half_heart <= stall_restart + stagnation_floor` for n = 1 and 6 is
kept as a test.

## Why the stall limit is in the contract

The stall limit decides the stagnation floor (`per_second * (limit - grace)`) and what the
stall-clock observation means (`idle / limit`, `live.py`). A changed limit with the same reward
config changes both silently, and the contract hash would not show it. v12 therefore carries
`stall.seconds` in the reward file. `make_live_env` and `load_training_config` check that the
watchdog uses the same number. The section is forbidden before v12 so older configs and results
stay as they were.

## Why not resume v11

The reward values and the stall limit change the return of every state, and the stall clock
observation is scaled by a new limit. The v11 value function and policy fit a different reward
and a different clock, and the contract hash changes anyway (`reward_version`), so a resume is
refused. The v11 run is kept as `runs/pure-v4-reward-v11-schema9`; `pure-v4` restarts with
`--initialize`.

## Loader and compatibility

`stall` is required for v12 and forbidden for v4 to v11. `door_shaping` for v12 uses the v11 key
set (`coefficient`, `max_hops`, `blocked_cost`). `novelty.cross_run` is required for v11 and v12.
The reward contract label of checkpoints (`pure-v11`) stays: the contract hash separates the
lineages.
