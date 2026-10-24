## Context

Reward v6 is computed by `RewardLedgerV4` (`rewards.py`) from oracle events. The stall
penalty is added in `IsaacEnv.step` (`env.py`) when the controller truncates with reason
`stall`. The idle clock lives in `StallWatchdog` (`stall_watchdog.py`) inside the live
backend (`live.py`). It counts active wall time without novel progress and is already
exposed to the policy as `stall_fraction`.

## Decisions

- **The cost is read from the idle clock, not from game time.** The watchdog uses active
  wall seconds; the game runs at about half speed during training, so game seconds would
  not match the stall limit. The live backend exposes `stall_idle_seconds` (0.0 without a
  watchdog). The sim backend has none, so it pays nothing.
- **Only increases are charged.** Per step, the cost is
  `per_second * max(0, over(after) - over(before))`, where
  `over(t) = max(0, t - grace_seconds)`. When progress resets the clock, `after` is
  smaller and nothing is paid. The total per stall is bounded by
  `per_second * (stall_seconds - grace_seconds)` across the entire episode/run.
  The ledger tracks paid cost; progress resets and same-run env resets do not
  replenish this allowance. Snapshot overshoot cannot exceed the allowance.
- **The env remembers the previous idle value.** `IsaacEnv` reads `stall_idle_seconds`
  after reset and after each step, passes before/after to
  `RewardLedgerV4.stagnation(before, after)` and adds the result as the `stagnation`
  column. The ledger returns 0.0 for a dead player and for coefficients without the term.
- **One ledger for v4-v7.** `RewardV4Coefficients` gains `stagnation_per_second` and
  `stagnation_grace_seconds`. Reward v7 must define the `stagnation` section; v4-v6
  configs must not, and get 0.0 / 0.0, so old configs load unchanged.
- **Grace 20 s.** Most fights and room changes come well inside 20 s. The cost starts
  only when the run is clearly idle and ramps to the stall limit.
- **Stall restart -5, hit -0.5.** Keeping the full stall (-12) above a full-health death
  (-13) removes any reward for dying on purpose. Halving the hit cost keeps fighting
  attractive next to the death penalty that already prices losing all health.
- **Fresh lineage.** The frozen evaluation shows no learned advantage over random play
  worth keeping, and the value head was fitted to reward v6.

## Risks

- The agent may learn to collect cheap progress (novelty cells do not reset the clock;
  first room visits, enemy damage, clears, new items and new consumable peaks do). Watch rooms visited versus
  clears in the dashboard.
- The cost may push riskier play and more deaths. That is the intended trade; the death
  share is reported next to the stall share.
- Wall-clock idle time depends on machine speed. The cost is bounded per stall, and the
  stall limit already has this property.
