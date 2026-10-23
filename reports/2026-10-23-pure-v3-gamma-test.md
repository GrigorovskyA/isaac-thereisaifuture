# Evidence: pure-v3 one-hour test with gamma 0.995 and ent_coef 0.005

- Date: 2026-10-23, Europe/Amsterdam. Host: macOS, offline read of copies of
  `runs/pure-v3/metrics/{episodes,train}.csv` after the run stopped. No game control.
- Session `runs/pure-v3/supervisor/session-20261023-130342-0001`, 11:03:42-12:03:42 UTC
  (`one-hour-timer.json`, `one-hour-timer-fired.json`). Resumed `03b9c5e3-s1-t243200`,
  ended at `03b9c5e3-s1-t257024` (27 updates, 13,824 steps, 39 episodes). The stop file
  ended it; the unfinished rollout was not saved. Same lineage and contract; only
  `gamma` 0.99 -> 0.995 and `ent_coef` 0.01 -> 0.005 changed.

## Episodes

| Window | n | Return | Death share | Stall share | Return of stalls | Return of deaths | Left start room | Rooms cleared | Damage dealt | Half-hearts lost | Median steps | Bomb requests per step |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 15 h, last 156 | 156 | -0.17 | 0.42 | 0.58 | 0.87 | -1.60 | 0.90 | 0.14 | 0.84 | 3.23 | 410 | 0.116 |
| 15 h, last 78 | 78 | -0.05 | 0.45 | 0.55 | 1.64 | -2.12 | 0.91 | 0.19 | 0.83 | 3.38 | 406 | 0.115 |
| Gamma test | 39 | 0.22 | 0.62 | 0.38 | 2.57 | -1.25 | 1.00 | 0.15 | 1.19 | 4.26 | 315 | 0.093 |

- Fewer stalls (0.58 -> 0.38, about 2.5 standard errors for n=39) and more fights:
  damage dealt +40%, every episode left the start room, but deaths rose and episodes got
  shorter. Clears per episode did not change; no stage 2; collectibles in 4 episodes.
- Stalls still return more than deaths (+2.57 vs -1.25). Reward v5 (`pure-v4`) makes a
  stall restart cost -10, the same as death.

## Policy and optimisation (train.csv)

| Window | Updates | Entropy | Explained variance | Value loss | Approx KL | Clip fraction | move none | use none | use bomb |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 15 h, last 59 | 59 | 3.59 | 0.42 | 0.24 | 0.027 | 0.15 | 0.12 | 0.50 | 0.11 |
| Gamma test | 27 | 3.43 | 0.47 | 0.32 | 0.030 | 0.17 | 0.10 | 0.59 | 0.09 |

- Lower `ent_coef` acted at once: entropy 3.59 -> 3.43 (range 3.01-3.88), use head back
  toward "none" (0.50 -> 0.59), bomb requests down.
- The longer horizon raised value targets: value loss 0.24 -> 0.32. Explained variance
  stayed positive (0.47 mean, per-update -0.40 to 0.86); the value head adapted.
- KL and clip fraction slightly higher; no instability.

## Assessment

The change did what it should: less stalling, more fighting, a less random use head.
It did not yet raise clears or depth. One hour, one seed, 39 episodes, observational.
Keep gamma 0.995 and ent_coef 0.005 for `pure-v4` (already in
`configs/training-pure-v4.yaml`).
