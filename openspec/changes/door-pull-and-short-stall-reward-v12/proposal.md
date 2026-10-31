## Why

Reward v11 / schema 9 ran 253952 steps (1180 episodes; report
`reports/2026-10-31-reward-v11-schema9-training.md`). Exit from the start room rose to 88.6%, but
64% of the episodes still stalled (72.5% in the last 50k), rooms per episode stayed about 2.0
and floor 2 was never reached.

Of 755 stalls, 30% were in a clear dead-end special room in room 2 (it needs a backtrack), 25% in
a cleared room next to an open unexplored door and 24% in the start room. About 56% of all steps
were the idle tail of a stall (40 s limit). The door potential pulled only about 0.9 per walk.

The stall and death costs also cross over. A stall costs -5 restart and -7.0 stagnation floor
(-0.25 per second after 12 s, up to 40 s) = -12.3. A death costs -10 plus the hits, so at one
half heart left a death (-10.5) is cheaper than a stall: a small suicide incentive.

## What Changes

- Reward v12 (`configs/reward-v12.yaml`; v9 to v11 stay loadable) equals v11 except:
  `door_shaping.coefficient` 4.0 (was 2.0; still potential-based, max |Phi| = 4 * 6 = 24),
  `outcome.death` -11.0 (was -10), `outcome.stall_restart` -4.0 (was -5),
  `stagnation.per_second` -0.39 (was -0.25, grace 12 s unchanged).
- New top-level section `stall: {seconds: 30}`: the stall watchdog limit is part of the reward
  contract. It sets the stagnation floor and the meaning of the stall-clock observation. It is
  required for v12 and forbidden for v4 to v11. The value must be a number > 0 and greater than
  `stagnation.grace_seconds`.
- `RewardV4Coefficients.stall_seconds` (None for v4 to v11); `make_live_env` accepts reward
  version 12 (default 12) and raises ValueError when a given `stall_seconds` differs from the
  contract's; `load_training_config` rejects a `watchdog.stall_seconds` that differs from it.
- `configs/training-pure-v4.yaml`: `reward_version: 12`, `watchdog.stall_seconds: 30`;
  `PURE_REWARD_VERSION = 12`. Observation schema stays 9. The reward v11 schema 9 run is kept as
  `runs/pure-v4-reward-v11-schema9`; its checkpoints are refused (new contract hash).
- Balance: a full stall costs -4 - 0.39 * 18 = -11.02 (plus time); a death costs -11.5 at one
  half heart and -14 from full health, so a death never pays better than a full stall.

## Non-goals

- No Lua, observation, action or hyperparameter change.
- No RND, no room-type bonus and no approach-the-door term outside the potential.
- No other reward term changes; kill, clear, visit, pickup and novelty values are as in v11.

## Acceptance

- Offline gate (`scripts/check.sh` / `Check.ps1`) and strict OpenSpec validation pass.
- Native run of 150k steps against reward v11 at equal steps, from `episodes.csv`: stall share
  below 50%, rooms per episode above 2.5, and floor 2 reached in some episodes.

## Impact

- `src/isaac_threrisaifuture/{rewards,live,training}.py`, `configs/`, tests, docs.
- Lineage `pure-v4` restarts with `--initialize` (done on Windows).
