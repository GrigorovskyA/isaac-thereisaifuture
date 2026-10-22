# Evidence: pure-v2 (reward v3) training analysis

- Date: 2026-10-22, Europe/Amsterdam. Host: macOS, offline analysis of read-only
  copies of `runs/pure-v2/metrics/{episodes,train}.csv` and the 5 retained
  checkpoints `d9b93984-s1-t56832` .. `t58880`. No game, training or SMB writes
  except the stop file `runs/pure-v2/supervisor/stop.forever` (user request).
- Lineage `pure-v2`: reward v3 (contract `pure-v3`), observation schema 3,
  action repeat 3, seed 1. Stopped by stop file at 19:00 after the user closed the
  game; the last two faults ("Peer closed before a complete record", "No playable
  live state before the restart deadline") were caused by that manual close.

## Scope

58,880 steps, 115 optimizer updates (Adam step 1840), 32 completed episodes over
about 2 hours. 1705 of 1837 first-layer input columns were unchanged from a
reconstructed seed-1 initialisation, which confirms the reconstruction is exact
(those inputs were always zero, e.g. collectibles never held).

## Episodes by thirds

| Third | Episodes | Mean return | Mean steps | Deaths / stalls | Left start room | Rooms cleared | Half-hearts lost | Bomb requests per step |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | 10 | -4.76 | 735 | 3 / 7 | 50% | 0.00 | 3.00 | 0.238 |
| 2 | 10 | -0.65 | 1598 | 0 / 10 | 60% | 0.30 | 2.00 | 0.235 |
| 3 | 12 | -3.94 | 2555 | 3 / 9 | 50% | 0.17 | 2.42 | 0.234 |

No measurable gameplay improvement over 32 episodes. Episodes got longer because
progress events (damage, room entry) reset the stall watchdog.

## Reward alignment (episode-level correlations)

- Return vs rooms cleared r=0.77, vs rooms visited r=0.59, vs damage dealt r=0.54.
- Left the start room: mean return -0.27 (17 episodes); stayed: -6.45 (15).
- At least one clear: +9.13 (5 episodes).
- Half-hearts lost vs damage dealt r=0.53: fighting costs health, as expected.
- Bomb requests vs episode length r=1.00: bomb pressing is a constant per-step
  rate, not a learned choice.

Reward v3 ranks outcomes as intended (clear > fight > idle).

## Policy and optimisation (train.csv, first / middle / last 20 updates)

| Steps | Policy entropy (max 4.605) | Explained variance | Approx KL | Clip fraction | use none | use bomb | move none | shoot none |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 512-10,240 | 4.573 | -0.13 | 0.0072 | 0.048 | 0.231 | 0.242 | 0.198 | 0.198 |
| 24,576-34,304 | 4.322 | -0.79 | 0.0129 | 0.095 | 0.306 | 0.262 | 0.168 | 0.203 |
| 49,152-58,880 | 3.971 | -3.28 | 0.0173 | 0.121 | 0.303 | 0.246 | 0.178 | 0.163 |

- The policy is moving: entropy fell to 86% of maximum, KL and clip fraction rose,
  "no move" and "no shoot" became rarer (it moves and shoots more).
- Bomb share did not fall (0.242 -> 0.246). One bomb per run and a delayed
  explosion give a weak, rare signal at 10 decisions per second.
- Explained variance is strongly negative late (-3.28): the value head does not yet
  predict returns. To watch in pure-v3; candidates if it persists are a lower
  learning rate or more steps per rollout (hyperparameters, no new lineage).
- A probe with synthetic Gaussian observations and zero LSTM state showed near-uniform
  probabilities (bomb 0.224); the rollout shares above, measured on real states, are
  the more relevant evidence.

## Conclusions and actions

- Supports the pure-v3 changes already prepared: own attacks and bombs visible,
  decisions every 0.2 s, use-head prior P(none)=0.85.
- Keep reward v4 as planned; its ordering is confirmed by these correlations.
- `use_*` episode counts are requested uses, not acknowledged presses.

Limits: 32 episodes, one seed, sequential and observational; not a controlled
comparison. Continue does not restore identical worlds.
