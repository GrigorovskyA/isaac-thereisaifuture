## Why

Roadmap item 11: the agent needs floor memory limited to rooms it has visited or legitimately
seen, plus navigation primitives, without hidden layout data ever reaching the policy.

## What Changes

- Add `navigation.py`: `FloorMap` (oracle layout), `KnownMap` (policy view), `MapTracker`,
  `RoomEvent`, `shortest_path`, `door_move`, `next_move`, `encode_known_map` (version 1).
- Door-transition actions map to the existing cardinal `Action` moves.

## Scope and non-goals

- In scope: offline contract, synthetic layouts, BFS over known open doors, versioned fixed-size
  map encoder, stale/replayed room-event rejection, offline tests.
- Out of scope: real bridge room/minimap data, learned navigation policy, the 100-scenario
  evaluation, floor routing (item 12), secret-room discovery (item 14).
- This is an offline contract. The change MUST NOT be archived until real-game evidence exists.

## Dependencies and risks

- Depends on `episode-lifecycle` (`Action`, `DIRECTIONS`).
- Unknown: what the installed game exposes for minimap/room-seen state; revealed-type rules
  for seen rooms are a hypothesis (secret and super-secret rooms hidden until visited).

## Acceptance criteria

- Offline: no hidden-room leakage, correct BFS paths, stale event rejection, fixed encoder size.
- Pending real game (blocked): at least 100 unseen scenarios; goal success, stuck rate and
  excess transitions improve over random; success threshold (for example 90% in enemy-free
  rooms) fixed before the evaluation.

## Impact

New module `navigation.py`; no change to the wire protocol.
