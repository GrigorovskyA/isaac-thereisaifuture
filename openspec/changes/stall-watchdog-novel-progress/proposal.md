## Why

In the first `pure-v3` hour one episode (33) ran 4242 steps, about 16 minutes, with
2 rooms visited and no enemy damage before the stall watchdog fired. Every
`room_entered` event reset the watchdog, including re-entering a known room, so
walking back and forth through one door kept a stalled run alive. `pickup_gained`
had the same hole: placing a bomb and picking up another raised the counter again.
The reward did not pay for this (first visit only), so the learner collected long
stretches of near-constant reward (value loss fell to 0.0016).

## What Changes

- Only facts new for the current run reset the watchdog: a room `(stage, room_index)`
  or floor not seen this run, coin/bomb/key counters above the run's peak, a
  collectible not held before, plus any enemy damage or room clear. These match the
  facts reward v4 pays for.
- The first snapshot of a run seeds its start room, floor, counters and items.

## Capabilities

### Modified Capabilities

- `stall-watchdog` (base requirement lives in the unarchived `pure-self-learning-v1`).

## Non-goals

- No change to the 90 s limit, reward, observation, action or lineage contract;
  `pure-v3` resumes unchanged.
- No Lua change and no mod redeploy.

## Impact

`stall_watchdog.py`, `live.py` and tests. Native effect is observed in
`episodes.csv` (no stall episode far above 90 s of progress-free play).
