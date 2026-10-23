# Evidence: pure-v4 first hour (schema 5, reward v5)

- Date: 2026-10-23, Europe/Amsterdam. Host: macOS, offline read of copies of
  `runs/pure-v4/metrics/{episodes,train}.csv` after the run stopped. No game control.
- Session `runs/pure-v4/supervisor/session-20261023-145622-0001`, 3601.75 s, resumed
  the qualification checkpoint `9aab0d2d-s1-t3584`, ended at `9aab0d2d-s1-t18432`
  (`user_cancelled` by the timer, learner exit 0, no fault, no cleanup errors).
  39 episodes in the hour plus 6 qualification episodes; 36 updates in total.

## Episodes (hour, thirds of 13)

| Third | Return | Death share | Stall share | Left start room | Rooms cleared | Damage dealt | Kills | Half-hearts lost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | -6.66 | 0.38 | 0.62 | 0.92 | 0.00 | 0.54 | 0.38 | 3.31 |
| 2 | -6.45 | 0.46 | 0.54 | 0.62 | 0.15 | 0.40 | 0.46 | 3.46 |
| 3 | -8.10 | 0.38 | 0.62 | 0.62 | 0.08 | 0.30 | 0.38 | 2.77 |

- Reward v5 removed the stall advantage: stall episodes -7.25, death episodes -6.80
  (pure-v3 with reward v4: +2.57 vs -1.25). Returns are lower overall because a stall
  now costs -10.
- Fresh model, 15k steps: the trend across thirds is within noise.

## Findings

1. One-shot kills pay nothing. Episodes 2 and 5 killed 2 and 5 enemies and cleared the
   room with `col_enemy_damage` 0; episodes 6 and 24 also had kills and no damage
   reward (4 of 16 episodes with kills). An enemy that dies between snapshots leaves
   the oracle list, and the event deriver treats a missing enemy as unknown, not dead.
   The stall watchdog misses these kills too. Fix: `openspec/changes/kill-credit-reward-v6`.
2. Hits by source (45 episodes, 124 hits): enemy 52, own bomb 21, projectile 17,
   spikes 15, fire 5, explosion 2, other 1, creep 0. Own bomb is in 10 of 17 deaths:
   the agent spends its start bomb and stands in the blast.
3. Optimisation pause measured: `update_seconds` 9.2-11.2 s per rollout of about 113 s
   (`rollout_seconds`), about 8% of wall time; 4.1 steps per second.
4. Policy: entropy 3.76 -> 3.20 in 36 updates (pure-v3 needed about 400 updates to reach
   3.59); explained variance 0.02 -> 0.52; use head stays near the prior (none 0.86-0.90).
   Watch entropy: if it falls below about 2.5 without more clears, restore ent_coef 0.01.

Limits: one seed, one hour, observational. No claim of improved play.
