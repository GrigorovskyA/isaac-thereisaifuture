## Why

Reward v9 lineage (schema 8, `b26db425`): after 105k native steps the agent still stalls. 92%
of the stalls happen in an already cleared room, and 40% of those rooms have no open door to an
unvisited room (dead ends), so the v9 door term (distance to the nearest open door to an
unvisited room) is silent exactly where the agent is stuck. Door shaping paid about +0.6 per
episode, against about -9 per episode for stagnation and stall. The agent has no gradient out of
a dead end: it must walk back through rooms it has already seen to reach the way on.

The v9 term measures a distance inside one room. The floor is a graph, and the agent has seen
most of it. Making the same single potential graph-aware gives the missing gradient: how many
rooms still have to be crossed to reach an unvisited room, or the boss room, through doors that
were seen on this floor.

## What Changes

- Lua observer: every oracle door gains `target` (grid index 0..168 of the room behind it, -1
  when unreadable or off the grid) and `usable` (false for a locked door and for a closed door to
  a secret, super secret or ultra secret room; unreadable means false). The live oracle gains
  `room_grid`, the grid index of the current room (-1 off the grid). All are reward labels, never
  policy input. `OracleDoor` and `LiveOracle` require the new fields, so an old mod fails
  validation loudly. The oracle event schema constant does not change (it versions events, not
  the live oracle block).
- Reward v10 (`configs/reward-v10.yaml`; v9 stays loadable as `configs/reward-v9.yaml`): all
  values as in v9 except `door_shaping: {coefficient: 2.0, max_hops: 5}`. `max_hops` present
  selects the graph potential; v9 configs keep the old potential unchanged.
- New `room_graph.py`: per episode and floor, the visited rooms and the doors seen from them.
  Hop distance to a goal (an unvisited target of a usable door, or the boss room) by BFS.
- Potential: `Phi(s) = -coefficient * cost(s)` with `cost` described in `design.md`. Still the
  only potential-based term, `gamma * Phi(s') - Phi(s)` per step, terminal `Phi = 0`.
- Episode column `stall_goal_hops` (best door term at a stall, empty otherwise). Old files are
  upgraded in place.
- `configs/training-pure-v4.yaml`: `reward_version: 10`; reward contract `pure-v10`; the
  schema 8 reward v9 run (`b26db425`, final t102400) is kept as
  `runs/pure-v4-reward-v9-schema8` and its checkpoints are refused (new contract hash).

## Non-goals

- No change to observations (schema 8), actions, the policy network or hyperparameters.
- No new reward term; every coefficient other than the door potential is unchanged.
- No reward for a technique: the potential rewards getting closer to an unvisited room or the
  boss room, nothing about how.
- No new wire capability: the new labels ride in the existing live-loop oracle block.

## Acceptance

- Offline gate (`scripts/check.sh` / `Check.ps1`) and strict OpenSpec validation pass.
- Native comparison at equal steps against reward v9 schema 8 (`b26db425`) at 30k, 60k and
  100k steps, from `episodes.csv`: the share of stalls that happen in a cleared room is lower,
  the dead-end share of stalls (`stall_open_unexplored_doors` 0 in a cleared room) is lower, the
  `rooms_visited` mean per episode is higher, and floor 2 is reached in more episodes.

## Impact

- `mod/observer/main.lua`, `src/isaac_threrisaifuture/{entities,live_wire,room_graph,rewards,
  env,episodes,episode_metrics,live,checkpoints,training}.py`, configs, tests, docs.
- The mod must be redeployed with the code: Python refuses snapshots without the new fields.
- Lineage `pure-v4` restarts with `--initialize` (done on Windows).
