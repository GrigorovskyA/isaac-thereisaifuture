## Context

At 273k steps of the E3B lineage the agent leaves the start room in 88% of the episodes, fights
better than any earlier lineage, and then stands in a calm room until the 30 s watchdog ends the
episode. The policy is still near random (87% of the maximum entropy) and half of the steps are
these idle tails.

## Calm stall limit (reward v13)

- In a calm room the only progress left is a new room (or a pickup). 15 s is enough to cross two
  rooms; the idle tail of a calm stall halves, so more of each rollout is fighting and walking.
- A room with enemies keeps 30 s, so a fight is never cut shorter than in v12.
- The watchdog applies the limit of the last active snapshot. The last kill of a room is enemy
  damage, so the clock is at 0 when a room turns calm after a fight. Entering a known calm room
  is not progress, so the clock keeps running there.
- The stagnation floor is one run-wide allowance. It is sized for the calm limit, so every stall
  costs the same -4 - 0.39 * 12 = -8.68 and a death (-11.5 to -14) never pays better.
- The stall-clock observation is idle / current limit, so it reaches 1 when the episode is cut.

| Event | v12 | v13 |
| --- | --- | --- |
| Stall limit, calm room | 30 s | 15 s |
| Stall limit, enemies | 30 s | 30 s |
| Stagnation grace | 12 s | 3 s |
| Stagnation floor | -0.39 * 18 = -7.02 | -0.39 * 12 = -4.68 |
| Full stall | -11.02 | -8.68 |
| Death, 1 / 6 half hearts of hits | -11.5 / -14.0 | -11.5 / -14.0 |
| Cost per idle second of a calm stall | 0.37 | 0.58 |

## Use head entropy

`MultiCategoricalDistribution.entropy()` sums the heads. `PureRecurrentPPO._evaluate_actions`
repeats sb3-contrib 2.9 `RecurrentActorCriticPolicy.evaluate_actions` to keep the distribution and
returns `H_move + H_shoot + use_entropy_scale * H_use`; at scale 1 it calls the policy method
itself. Values and log probabilities are those of the policy method (tested). `ent_coef` 0.005
stays for move and shoot; the use head gets 0.001.

## Risks

- A cheaper stall (-8.68 instead of -11.02) arrives twice as fast in a calm room; per idle second
  it is dearer. If the stall share rises instead of falling, raise `stall_restart` in a reward v14.
- A lower use-head bonus can freeze the use head on `none`; the head's prior is already 85%
  `none`, which is the intended start. Bombs and items are still pressed when they pay.
