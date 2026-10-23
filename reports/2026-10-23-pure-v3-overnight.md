# Evidence: pure-v3 after 15 hours (622 episodes, 243k steps)

- Date: 2026-10-23 12:40, Europe/Amsterdam. Host: macOS, offline read of copies of
  `runs/pure-v3/metrics/{episodes,train}.csv` after the run stopped. No game control.
- Lineage `pure-v3`, seed 1, contract `03b9c5e3...`. Two sessions after the stall
  watchdog fix (`a985dbe`): 7 h 59 min (completed, `t141824`) and about 7 h 1 min
  (stopped by the user-authorized timer, `t243200`). Native result.json files report
  28741.313 s and 25260.547 s, learner exit 0 and no cleanup errors for both sessions.
  Total 622 episodes, 242,856 steps, 475 updates, 2026-10-22 19:33
  to 2026-10-23 12:27 (about 4 steps per second). Run folder 423 MB.

## Episodes in eight bins (77-78 each)

| Bin (ends) | Return | Death share | Left start room | Rooms cleared | Damage dealt | Half-hearts lost | Bomb requests per step |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 (10-22 22:20) | -0.78 | 0.44 | 0.74 | 0.19 | 0.86 | 3.40 | 0.10 |
| 2 (00:34) | -0.16 | 0.32 | 0.68 | 0.17 | 0.86 | 2.56 | 0.20 |
| 3 (02:20) | -2.42 | 0.38 | 0.68 | 0.13 | 0.67 | 3.01 | 0.18 |
| 4 (04:21) | -0.57 | 0.55 | 0.90 | 0.17 | 1.11 | 4.09 | 0.10 |
| 5 (06:04) | -2.11 | 0.54 | 0.86 | 0.08 | 0.90 | 3.63 | 0.11 |
| 6 (08:10) | -0.13 | 0.55 | 0.88 | 0.14 | 1.07 | 3.94 | 0.13 |
| 7 (10:29) | -0.30 | 0.39 | 0.90 | 0.09 | 0.87 | 3.04 | 0.11 |
| 8 (12:26) | 0.01 | 0.44 | 0.91 | 0.19 | 0.82 | 3.35 | 0.11 |

- Changed: start-room exits 68-74% -> 86-91% from bin 4 on; "no move" share in
  `train.csv` 0.21 -> 0.09-0.12. Deaths rose to 54-55% in bins 4-6 (more fights after
  leaving the start room) and fell back to 39-44% in bins 7-8.
- Flat: return about -1 to 0; rooms cleared 0.1-0.2 per episode (537 of 622 episodes
  clear nothing, 82 clear one); stage 2 never reached; a collectible in 26 episodes.
- Reward alignment holds: return vs rooms cleared r=0.82, vs damage dealt r=0.60.
- Watchdog fix works (closes task 2.3 of `stall-watchdog-novel-progress`): after it
  stall episodes have median 438 steps; the longest (1437) had 4 rooms, a clear and
  damage. Before the fix one episode ran 4242 steps.
- Fast deaths are mostly combat: 58 of 281 deaths took under 80 steps, most with
  enemy damage dealt. The startup report also found self-bomb, curse-door spike and
  creep damage (`reports/2026-10-22-pure-v3-12h-start.md`).

## Policy and optimisation (train.csv, eight bins of about 59 updates)

| Steps | Entropy (max 4.605) | Explained variance | Approx KL | Clip fraction | use none | use bomb | use active | use pill-card |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 512-30,720 | 3.83 | 0.14 | 0.011 | 0.07 | 0.78 | 0.08 | 0.06 | 0.08 |
| 31,232-61,440 | 3.96 | 0.27 | 0.015 | 0.09 | 0.49 | 0.19 | 0.14 | 0.18 |
| 92,672-122,368 | 3.89 | 0.30 | 0.021 | 0.13 | 0.53 | 0.11 | 0.27 | 0.10 |
| 153,088-182,784 | 3.71 | 0.40 | 0.024 | 0.14 | 0.48 | 0.13 | 0.13 | 0.26 |
| 213,504-243,200 | 3.59 | 0.42 | 0.027 | 0.15 | 0.50 | 0.11 | 0.19 | 0.19 |

- The value head learns (explained variance 0.14 -> 0.42).
- Entropy started to fall only in the last third (3.9 -> 3.55-3.59).
- The use head moved from the prior P(none)=0.78 back toward uniform (0.44-0.53): use
  presses earn nothing directly, so the entropy bonus (`ent_coef` 0.01) is the main
  force on that head.

## Assessment and actions

No infrastructure problem: zero faults, the 8 h session rollover worked. Behaviour
changed (exploration, fewer idle moves, later fewer deaths) but outcomes (clears,
floors, items) did not improve over 243k steps. This is early for real-time RL (1M
steps is about 70 h).

- Actions taken: `ent_coef` 0.01 -> 0.005 and `gamma` 0.99 -> 0.995 in
  `configs/training-pure-v3.yaml` (hyperparameters, same lineage), effective from the
  next session. With 0.99 and 0.2 s per decision the horizon is about 20 s, so the stall
  penalty 90 s ahead weighed about 1%; 0.995 gives about 40 s. Stall episodes returned
  more than death episodes (+1.05 vs -1.74 in the last third), so stalling pays better
  than fighting. Rollback: 0.01 and 0.99.
- Gaps for a later lineage: obstacle type (rock, pit, spikes, TNT; bombable or not),
  damage source attribution in metrics, `enemies_killed` counter (always 0).

Limits: one seed, observational, sequential; no frozen evaluation.
