## ADDED Requirements

### Requirement: Reward v10 coefficients
Reward v10 SHALL equal reward v9 except `door_shaping: {coefficient: 2.0, max_hops: 5}`.
`max_hops` SHALL be required (an integer >= 1) for v10 and forbidden for v9, and the archived
v4-v9 configs SHALL stay loadable. A v9 config SHALL keep the v9 door potential unchanged.

#### Scenario: Older configs
- **WHEN** the v9 config is loaded
- **THEN** it loads with the distance-only door potential

### Requirement: Room graph
The ledger SHALL keep, per episode and floor (`stage`, `stage_type`), the visited grid rooms,
the usable doors seen from each room the player stood in, and the boss room once entered. A new
episode or a floor change SHALL clear it. The hop distance of a room SHALL be 0 for an unvisited
target of a usable door and for the boss room, and one more than its best usable neighbour for a
visited room.

#### Scenario: Dead end
- **WHEN** the player is in a room whose only door leads back to a room with a door to an
  unvisited room
- **THEN** the hop distance of the current room is 1

#### Scenario: Floor change
- **WHEN** the floor changes
- **THEN** the graph holds only the new room

### Requirement: Graph door potential
For reward v10, `Phi(s) = -coefficient * cost(s)`. Outside the boss room the cost SHALL be the
minimum over usable doors with a known target of the in-room term plus the target's hop distance
capped at `max_hops`. The in-room term is the clipped distance to an open door over the room
diagonal in a clear room without enemies, else 1. With no such door the cost SHALL be
`1 + max_hops`.

#### Scenario: Dead end gradient
- **WHEN** the player walks toward the only door of a cleared dead-end room
- **THEN** every step pays a positive door shaping reward

#### Scenario: Fighting room
- **WHEN** the room has enemies or the door is closed
- **THEN** the in-room term is 1 wherever the player stands

#### Scenario: Sealed doors
- **WHEN** every door is locked or leads to a closed secret room
- **THEN** the cost is `1 + max_hops` at every position

#### Scenario: Hop cap
- **WHEN** the nearest goal is more than `max_hops` rooms away
- **THEN** the hop part is `max_hops`

### Requirement: Zero and boss room potential
The cost SHALL be 0 without doors data, for a dead player and for an off-grid room. In the boss
room it SHALL be 1 while the room is not clear or has enemies, else the clipped trapdoor distance
over the room diagonal (0 without a trapdoor).

#### Scenario: Boss room
- **WHEN** the boss room is clear and a trapdoor lies at distance `t`
- **THEN** the cost is `min(t / D, 1)`

#### Scenario: Off grid
- **WHEN** `room_grid` is -1
- **THEN** the potential is 0

### Requirement: Shaping stays potential-based
Reward v10 SHALL pay `gamma * Phi(s') - Phi(s)` per step with `Phi(s') = 0` on a terminal step.
For any trajectory ending in a terminal step, the discounted sum of the door shaping SHALL equal
`-Phi(s0)`.

#### Scenario: Re-entering rooms
- **WHEN** the agent walks between known rooms for many steps
- **THEN** the discounted door shaping sum stays equal to `-Phi(s0)` at the terminal step

### Requirement: Stall goal metric
The episode file SHALL have a `stall_goal_hops` column holding the best door term of the last
state of a stalled episode (two digits), and empty for other episodes and when no door gives a
finite term. An episode file with an older header SHALL be upgraded in place.

#### Scenario: Stall and death rows
- **WHEN** an episode ends in a stall in a fighting room with a door to an unvisited room
- **THEN** its row has `stall_goal_hops` 1.0
- **AND** a death row has it empty

### Requirement: Reward v9 contracts refused
Checkpoints saved with the reward contract `pure-v9` or older SHALL be refused when the config
expects `pure-v10`.

#### Scenario: pure-v9 checkpoint
- **WHEN** a pure-v9 checkpoint is resumed with reward contract `pure-v10`
- **THEN** the resume is refused
