## Context

Policies must not see unexplored layout (oracle data). Navigation needs a map of what the
agent legitimately knows.

## Decisions

- **Oracle/policy split**: `FloorMap` is the full layout; only `MapTracker` holds it and exposes
  `known`, a `KnownMap` rebuilt from the visited set on demand, so leakage is impossible by
  construction.
- **Discovery rule**: visiting a room reveals its doors and the adjacent rooms behind them
  (position and type). A door toward a secret or super-secret room is shown as a wall until that
  room is visited.
- **Door status**: `open`, `locked`, `blocked`, `wall` (visited room, no door) or `unknown`
  (unvisited room, undetermined). Only `open` doors are traversed.
- **Navigation**: BFS with fixed direction order; `door_move` maps a direction to
  `Action(move=...)` and raises `NavigationError` for any other status.
- **Events**: `RoomEvent(session_id, room_visit, room_id, kind)`. `enter` needs a strictly larger
  room visit and an open door from the current room; `clear` needs the current visit and is not
  repeatable. Violations raise `StaleMapEvent`.
- **Encoder v1**: window of radius 3 centred on the current room, 20 features per cell (known,
  visited, cleared, current, open doors, closed doors, room type one-hot): 980 float32 values.
  Coordinates are relative; no room ids.

## Risks / Trade-offs

- Window size and reveal rule are hypotheses; real floors are up to 13x13 with L-shaped rooms
  that this grid model ignores.
- Rooms outside the window are not encoded.
