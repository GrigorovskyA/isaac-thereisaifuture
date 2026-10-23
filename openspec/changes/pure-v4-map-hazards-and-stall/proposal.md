## Why

After 15 hours and 243k steps of `pure-v3` (`reports/2026-10-23-pure-v3-overnight.md`)
the agent explores more but clears no more rooms (0.1-0.2 per episode, stage 2 never
reached). Four causes are in the setup:

- Stalling pays better than fighting: stall-truncated episodes returned +1.05 on
  average in the last third, death episodes -1.74. A stall costs 5, a death 10 plus
  the hearts lost.
- The agent cannot see the stall clock, so a stall restart arrives without warning,
  and with gamma 0.99 the penalty 90 s ahead weighs about 1%.
- Obstacles carry no type: a rock, a pit, spikes, poop, TNT and a wall look the same,
  fireplaces (entities) are not visible at all, and the 12 nearest obstacles are often
  perimeter wall cells. The agent cannot tell that a pickup is enclosed or that a rock
  can be bombed.
- There is no minimap: the player sees which rooms are known, visited and special
  (boss, treasure, shop); the agent does not.

Metrics also miss the damage source (own bomb, enemy, spikes, fire, creep) and
`enemies_killed` is always 0.

## What Changes

- Observation schema 5:
  - obstacle class one-hot per obstacle slot (rock, marked rock, bomb rock, block, pit,
    spikes, poop, TNT, fire, wall, other); fireplaces become obstacles; perimeter wall
    cells are dropped; observer obstacle cap 12 -> 24 (encoder capacity stays 24);
  - room shape one-hot (12);
  - minimap: 13 x 13 level grid, per cell known / visited / current / boss / treasure /
    shop / other special, plus an off-map flag for the current room;
  - stall clock: seconds without progress / stall limit, appended by the environment
    (0 when no watchdog runs).
- Messages up to 48 KiB on both sides.
- Reward v5 = reward v4 with `stall_restart` -10 (equal to death).
- Metrics only (oracle, never in the policy): cumulative enemy kills and player hits by
  source per run; episode rows gain `enemies_killed` from kills and `hits_*` columns.
- New lineage `pure-v4` (`configs/training-pure-v4.yaml`, `runs/pure-v4`) with gamma
  0.995 and ent_coef 0.005. `pure-v3` is preserved, not resumed; its config moves to
  `archive/configs/`.

## Capabilities

### Modified Capabilities

- `pure-observation`, `pure-reward`, `training-metrics` (base requirements live in the
  unarchived `pure-self-learning-v1` and `reward-v3-and-training-metrics` changes).

## Non-goals

- No reachability, path or "enclosed" flag computed for the agent: the map and
  obstacle classes are facts; using them is learned.
- No hidden-room, secret-room location or unrevealed map data: only what the in-game
  minimap shows (display flags) or what the player visited.
- No reward for kills, items used or map coverage beyond reward v4 terms.
- Damage-source counters never enter the observation, normalizer or reward.

## Impact

Lua observer, wire models, encoder, env, live backend, reward config, metrics,
lineage config, launchers, dashboard default, docs and tests. Requires redeploying
`mod/observer` and a short native check. Unverified natively: GridEntityType and
RoomShape values, DisplayFlags icon bit, L-shaped room anchor cells, fireplace
detection, damage flags and NPC death callback.
