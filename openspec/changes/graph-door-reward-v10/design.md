## Context

Reward v9 shaping is `Phi(s) = -coefficient * d / D` for the nearest open door to an unvisited
room, nonzero only in a clear room without enemies. In a dead end (the cleared room has no such
door) it is 0, so nothing tells the agent to go back. v10 keeps one potential and one formula
(`F = gamma * Phi(s') - Phi(s)`, terminal `Phi = 0`) and changes only what `Phi` measures.

## Room graph (per episode, reset on a floor change)

State, built from oracle labels only:

- `visited`: grid indexes the player has stood in (`room_grid` is added every step when >= 0).
- `edges[room][target] = usable`: overwritten from the oracle doors every step the player is in
  `room`. Doors with `target < 0` are ignored; two doors to one target are OR-ed.
- `boss`: grid index of a room with `RoomFacts.type == 5` once the player has been in it.
- A new episode (`begin`) and a change of `(stage, stage_type)` clear all three.

Hop distance `H(v)` by multi-source BFS over reversed usable edges:

- Goals have `H = 0`: every target of a usable edge that is not in `visited`, and the boss room.
- A visited room `v` has `H(v) = 1 + min H(w)` over its usable edges `v -> w`.
- Unknown or unreachable rooms have no distance. The cap is `min(H, max_hops)` with
  `max_hops = 5`.

A door is usable unless it is locked or leads to a closed secret-type room. The observer reads
this once per door so the graph never routes through a wall.

## Potential

`Phi(s) = -coefficient * cost(s)` and `D` is the room diagonal as in v9.

- `cost = 0`: no oracle doors data, dead player, `room_grid < 0`.
- Boss room: clear and no enemies -> `d(player, nearest trapdoor) / D` (clipped to 1, 0 when
  the frame holds no trapdoor); otherwise 1.
- Any other room: `cost = min over usable doors e with target >= 0 of in_room(e) + H(target(e))`
  where `in_room(e) = min(d(player, e) / D, 1)` when the room is clear with no enemies and `e`
  is open, else the constant 1. Doors without a finite `H` are skipped. With no such door,
  `cost = 1 + max_hops` (a constant, no gradient).

Bounds: `0 <= cost <= 1 + max_hops`, so `|Phi| <= 2 * 6 = 12`, below the -12 full-stall cost
scale and the -13 death-from-full-health scale of the other terms (only the shape of the
gradient matters, the sum over an episode is bounded by `Phi(s0)`).

Why constants in fighting rooms: while enemies live the agent must fight; a distance term would
pull it toward a door in the middle of combat, and a closed door is not a route. The constant 1
keeps `Phi` continuous when the room clears (the in-room share then decreases from at most 1)
and gives no gradient to follow while fighting. The hop part still counts, so entering a room
that is closer to a goal raises `Phi`.

## Exploit analysis

- Telescoping: with `Phi_T = 0` the discounted sum of `F` over an episode is exactly
  `-Phi(s0)` (`sum gamma^t F_t = gamma^T Phi_T - Phi_0`). Re-entering rooms repeatedly pays no
  more than this bound; without discount the closed-walk sum is 0 and with the training gamma it
  is at most `(1 - gamma) * max|Phi|` per step. `Phi` depends on the episode's room graph and
  position, and the stored value is what the next step subtracts, so the identity holds exactly
  for any trajectory.
- Opening or revealing doors raises `cost` only through new goals: a new unvisited target lowers
  the hops of its neighbours (a gain the agent earns by exploring), and visiting a room removes
  it as a goal, which raises `cost` of the rooms behind it. That rise is paid back by the room
  first-visit reward (5) which is larger than the potential change (at most `2 * max_hops`
  per room on a chain, in practice 2 per hop).
- Locked and secret doors are not edges, so the agent cannot be pulled to a wall.
- Oracle data stays a reward label: the graph is never encoded and never reaches the policy.
- A step into an off-grid room (planetarium-like special rooms read -1) has `Phi = 0`, so leaving
  the grid never creates an unbounded gain: `Phi` is bounded above by 0.

## Interfaces

- `OracleDoor`: `target` (-1..168), `usable`. `LiveOracle`: `room_grid` (-1..168). Required
  fields. `ORACLE_SCHEMA_VERSION` stays 1: it versions oracle events, and the live oracle block
  is validated strictly and has no version of its own, so an old mod already fails loudly.
- `StepResult` and `Transition` carry `room_grid`; the ledger takes it as a keyword.
- `RewardV4Coefficients.door_shaping_max_hops` (0 means the v9 potential).
- Metric `stall_goal_hops`: the best door term at the stall step, rounded to two digits,
  empty for other rows and when no door gives a finite term.

## Risks

- `GridIndex` and `IsLocked` are read in the native game for the first time; offline tests use
  stubs, so the first native hour must confirm `target` and `room_grid` are real grid indexes.
- After an episode restart inside one run, the graph starts empty: rooms the game already visited
  look unvisited until the player enters them again. Stall restarts start a new run, so this
  mainly affects resets that keep the floor.
