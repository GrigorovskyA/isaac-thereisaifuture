## Why

Reward v8 lineage (`fb22b342`): after about 580k steps, kills and clears per 1000 steps
plateaued from about 240k steps (kills 6-7, clears about 1.0). 60-70% of episodes still stall
(40 s watchdog), about 1.9 rooms are visited per episode, floor 2 was never reached and a new
collectible shows up in about 5% of episodes. The frozen evaluation of t270336 beat
`random-prior` (`kills_1k` +3.03 [+1.34, +4.80], `clears_1k` +0.52 [+0.13, +0.91]), so the
agent learns, but slowly. Raising `ent_coef` to 0.01 did not raise entropy and did not help
(from `fb22b342-s1-t510976`, about 70k steps: stalls 60% to 70%, `kills_1k` 6.7 to 5.4).

Average reward per episode over the last 500 episodes: enemy damage +5.49, room visit +2.33,
room clear +1.2, novelty +0.40, pickups about +0.15, against stagnation -5.10, stall -3.49,
death -3.02 and damage taken -1.43. The exploration signal is tiny next to damage and the
penalties. Throughput is fixed at about 15k steps per hour (one Steam instance; game logic runs
at its native 30 updates per second), about 100x fewer samples than Pokemon Red PPO (Pleines et
al. 2025, arXiv 2502.19920), where +0.005 per new map coordinate was essential, 10x more made the
agent only explore, and a healing reward was farmed. With so few samples the reward must be
denser, mainly for exploration and run goals.

The operator explicitly approved one potential-based term that is not an outcome: shaping toward
unexplored doors (Ng et al. 1999: F = gamma * Phi(s') - Phi(s) keeps the optimal policy). This
changes the outcome-only reward rule for this one term.

## What Changes

- Lua observer: the oracle block of live snapshots gains `doors` (up to 8 entries: `slot`,
  world `x`, `y` of the door slot, `open`, `unexplored`). Reward label only, never in the policy
  frame. `LiveOracle` validates it strictly.
- Reward v9 (`configs/reward-v9.yaml`; v8 moves to `archive/configs/reward-v8.yaml` and stays
  loadable):
  - `room_first_visit` 5 (was 3), `floor_first_entered` 30 (was 10), new
    `boss_room_clear_first` 20 on the first clear of a boss room (`RoomFacts.type` 5), paid with
    `room_clear_first`.
  - Pickups: coin 0.3, bomb 0.5, key 0.5, `consumable_run_cap` 10, `collectible_new` 5; healing
    stays 0.5 and bounded by the heal pool.
  - Novelty coefficient 0.1 (was 0.02), cell size 40.
  - Stagnation unchanged (-0.25 per second past 12 s; stall limit 40 s), so a full stall costs
    at most -12 and a death from full health (-13) never pays better.
  - New `door_shaping: {coefficient: 2.0}`: Phi(s) = -coefficient * d / D, d the distance to the
    nearest open door to a never visited room, D the room's bounding-box diagonal. Phi is 0
    unless the room is clear with no enemies. A step pays gamma * Phi(s') - Phi(s) with gamma
    from the training hyperparameters; a terminal step ends in Phi(s') = 0; on a room change the
    old room's last Phi and the new room's first. New episode column `col_door_shaping`.
- Observation schema 6: a visited-cells block (27 x 15 novelty cells of 40 px over the largest
  room, 1.0 where the player stood in this room during this run) built from player position,
  stage and the current minimap room only. `OBSERVATION_SIZE` 3904 (was 3499). The wire frame
  stays at schema 5.
- `configs/training-pure-v4.yaml`: `observation_schema_version: 6`, `reward_version: 9`,
  `ent_coef: 0.005` (was 0.01). Everything else is unchanged.
- Contract: reward contract `pure-v9`; pure-v8 checkpoints (schema 5) are refused. Lineage
  `pure-v4` restarts with `--initialize`; the reward v8 run is kept as
  `runs/pure-v4-reward-v8` (done on Windows).

## Non-goals

- No change to actions, the policy network or hyperparameters other than `ent_coef` back to
  0.005.
- No change to the stall limit or the stagnation cost.
- No reward for aiming, shooting or any other technique; door shaping rewards no input pattern,
  only getting closer to an unexplored way out of a cleared room.
- No new wire capability: `doors` rides in the existing live-loop oracle block.

## Acceptance

- Training side, first 8 h session against the reward v8 lineage at the same step count: the
  `rooms_visited` mean is higher and the share of stalled episodes is lower.
- Frozen evaluation of the latest checkpoint after at least 250k steps: two 3600 s sessions of the
  checkpoint and two of `random-prior` under this config, then
  `scripts/compare_eval.py --baseline random-prior`: the 95% bootstrap interval of the
  `kills_1k` difference is above zero and the `clears_1k` point difference is positive.
- The `rooms_visited` mean of the frozen checkpoint is above that of the reward v8 frozen
  evaluation of t270336: 1.89 over its 154 episodes (a: 1.92 over 76, b: 1.86 over 78, read from
  `runs/pure-v4-eval/v8-t270336-a` and `-b` `episodes.csv`; `random-prior` under v8: 1.58).

## Impact

- `mod/observer/main.lua`, `src/isaac_threrisaifuture/{entities,live_wire,encoding,env,episodes,
  rewards,live,checkpoints,training,recording}.py`, configs, tests, docs.
- The mod must be redeployed with the code: Python refuses snapshots without `doors`.
