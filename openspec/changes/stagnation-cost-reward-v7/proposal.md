## Why

The frozen evaluation (`reports/2026-10-24-pure-v4-frozen-eval.md`) shows that no
pure-v4 checkpoint plays better than a uniform random policy. Per episode:

| | random | t102400 | t204800 | t237568 |
|---|---:|---:|---:|---:|
| Stall share | 41% | 62% | 74% | 53% |
| Left start room | 82% | 71% | 45% | 70% |
| Enemy damage fraction | 1.70 | 1.93 | 0.51 | 1.46 |
| Half-hearts lost | 4.18 | 3.35 | 2.32 | 3.30 |

The trained policies stall more and lose less health than random play. They learned to
avoid damage, not to fight. pure-v3 showed the same drift (stall share 0.39 -> 0.81 in
four hours, `configs/training-pure-v4.yaml`), and the gamma/GAE change for the night run
did not stop it.

Reward v6 makes this easy to learn. A hit costs -1 at once. The stall penalty (-10)
comes once, up to about 400 steps after the last progress, and is spread over all of
those steps. Standing still in a quiet spot is therefore the cheapest behaviour the
policy can find early on.

## What Changes

- New reward term `stagnation`. While the stall watchdog's idle clock is past a grace
  period, each step costs `stagnation.per_second` times the idle seconds added in that
  step. The policy already observes this clock (`stall_fraction`, observation schema 5),
  so the cost is visible to it. New progress resets the clock and stops the cost.
- Reward v7 (`configs/reward-v7.yaml`) = reward v6 with these changes:
  - `stagnation.per_second: -0.1`, `stagnation.grace_seconds: 20`. With the 90 s stall
    limit an entire episode accrues at most -7.0, including repeated idle periods;
  - `outcome.stall_restart: -5` (was -10), so a full stall costs at most -12;
  - `outcome.player_damage_half_heart: -0.5` (was -1). Death (-10) already prices
    losing all health; the per-hit cost no longer outweighs fighting.
- Invariant: dying from full health never pays better than a full stall
  (death + 6 half-hearts = -13 versus stall at most -12), so the reward never pays for
  dying on purpose to escape the stagnation cost.
- Contract: `reward_version: 7`, reward contract `pure-v7`. Reward v6 config moves to
  `archive/configs/`. pure-v6 checkpoints are refused.
- Lineage `pure-v4` starts again with `--initialize`. The reward v6 lineage directory is
  kept as `runs/pure-v4-reward-v6` (done on Windows). Hyperparameters stay unchanged.

## Non-goals

- No change to the observation, actions, policy, stall limit or hyperparameters.
- No reward for using items, aiming, moving or any other technique.
- The stagnation term is not a progress signal; it does not reset the stall clock.

## Acceptance

After 8 hours of training, a frozen evaluation of the latest checkpoint under the same
protocol (`Start-Eval.cmd`, 3600 s) has a stall share below random's 41% and an enemy
damage fraction at least random's 1.70. Otherwise the next change targets exploration.

## Impact

- `src/isaac_threrisaifuture/{rewards,env,live,checkpoints,training}.py`, configs,
  tests, docs. No Lua change and no observer redeploy.
