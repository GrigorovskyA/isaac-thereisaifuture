## Why

Reward v10 lineage (schema 8): after 61k native steps the agent still stalls, and 73% of the
stalls (135/184) happen in a cleared room within 0.1-0.45 room diagonal of an open door to an
unvisited room. The agent does not walk through. The cause is in the v10 potential: the in-room
term is `d / D` in a calm room with an open door, else a constant 1. Entering a new, uncleared
room moves the in-room term from about 0 (at the door) to 1, so every room entry pays about
`-coefficient` = -2. v9 had `Phi = 0` in an uncleared room, so it had no entry penalty.

Two more causes show in the same v10 data. In 111 of 191 stalls (58%) the agent never left the
start room although 2-4 open unvisited doors existed. Returns by rooms visited: 1 room -9.0
(n=111), 2 rooms +4.5 (n=153), 3 rooms +19.3 (n=25). An episode that never leaves collects about
3.0 novelty in the start room, on every run. And a stall was returned to the learner as
truncated: sb3-contrib bootstraps `gamma * V(terminal obs)` on `TimeLimit.truncated`, but a New
Run follows a stall and the stall clock is in the observation, so the value of the cut state was
wrong. The env also zeroed `Phi(s')` on that bootstrapped step, a refund of up to
`+coefficient * cost` (+12 at a dead end).

## What Changes

- Reward v11 (`configs/reward-v11.yaml`; v9 and v10 stay loadable) equals v10 plus one
  `door_shaping` key: `blocked_cost` (float >= 0). It replaces the constant 1 of the in-room
  term (a closed door, or a room that is not calm) and the cost of a live boss room. v10 is
  `blocked_cost` 1.0 (implicit: the v10 config has no such key and its results do not change);
  the v11 config sets 0.0.
- A stall ends the episode for learning: `env.step` returns `terminated=True, truncated=False`
  for a stall truncation (episode summary, info and `episodes.csv` still say truncated / stall).
  The reward `terminal` flag is `terminated or stall`; other truncations (scenario cap, faults)
  keep bootstrapping and keep `Phi`.
- Novelty counts across runs (`novelty.cross_run: true`): the per-run first-visit gate stays, a
  first visit of a (stage, room, cell) key pays `coefficient / sqrt(N)`, N the number of runs
  (this one included) that first visited the key. The count table is reward state, saved with
  every checkpoint (`novelty_counts.npz`, listed in the manifest with its hash) and loaded on
  resume; a v11 resume without it is refused. Frozen evaluation never writes counts.
- Hyperparameters (not in the contract hash): `n_epochs` 4 -> 10, `batch_size` 256 -> 128,
  `target_kl: 0.03` (new optional key). A 64k-step run had only about 62 updates, approx_kl
  ~0.006 and clip_fraction ~0.04, and the policy was still near random.
- Everything else is as in v10: the fallback `1 + max_hops` with no door to a goal, the trapdoor
  term in a cleared boss room, the hop cap, terminal `Phi = 0` and the BFS for `H`.
- Effect: entering a frontier room whose new neighbours are unvisited costs nothing; entering a
  dead end still drops `Phi` by `coefficient * H` (informative); clearing a room lowers `Phi` by
  at most `coefficient * d / D` (<= 2, far below `room_clear_first` 10). Still the only
  potential-based term, so the optimal policy is unchanged.
- `configs/training-pure-v4.yaml`: `reward_version: 11`; reward contract `pure-v11`. The reward
  v10 run (about 61k steps) is kept as `runs/pure-v4-reward-v10`; its checkpoints are refused
  (new contract hash).

## Non-goals

- No Lua, observation or action change within this reward change. The separate item identity
  change introduces observation schema 9 in the same fresh lineage.
- Other outcome coefficients (stagnation, stall, clear and visit) remain as in v10; novelty
  uses the cross-run decay specified above.
- No new reward term or reward for a technique; reward version becomes 11.
- No observation input from the counts. The reward version and combined schema 9 change
  produce a new contract hash; changing only hyperparameters does not change that hash.

## Acceptance

- Offline gate (`scripts/check.sh` / `Check.ps1`) and strict OpenSpec validation pass.
- Native run of 150k steps: exit-start share > 0.8, stall share < 50%, rooms per episode > 2.5.
- Native comparison at equal steps against reward v10 and reward v9 schema 8, from
  `episodes.csv`: the share of stalls near an open unvisited door (`stall_goal_hops` < 1) is
  lower, the exit-start share is higher, `rooms_visited` per episode is higher, and floor 2
  (stage 2) is reached in more episodes.

## Impact

- `src/isaac_threrisaifuture/{rewards,live,checkpoints,training,env,novelty_counts}.py`, configs, tests, docs.
- Lineage `pure-v4` restarts with `--initialize` (done on Windows).
