## ADDED Requirements

### Requirement: Known-only map view
The policy-facing map SHALL contain only rooms the agent visited or saw through a door, and
hidden layout data MUST NOT reach the policy view or its encoding.

#### Scenario: Adjacent secret room
- **WHEN** the agent visits a room next to an unvisited secret room
- **THEN** the known map has no entry for the secret room and reports that door as a wall

#### Scenario: Unvisited neighbor
- **WHEN** a room is seen through a door but not visited
- **THEN** its other doors are reported as unknown, not as walls

### Requirement: Navigation over known doors
Navigation SHALL use only open known doors, and door actions MUST be refused for locked,
blocked, wall or unknown doors.

#### Scenario: Shortest path
- **WHEN** a goal is reachable through open known doors
- **THEN** the BFS path of door directions is returned, and the path never crosses a closed door

#### Scenario: Unreachable goal
- **WHEN** only locked or blocked doors lead to the goal
- **THEN** no path is returned

#### Scenario: Unavailable door action
- **WHEN** a move through an unknown or blocked door is requested
- **THEN** a navigation error is raised

### Requirement: Fresh room events
The map tracker MUST reject room events that are stale, replayed, from another session, or
inconsistent with the current room's open doors.

#### Scenario: Replayed room visit
- **WHEN** an enter event carries a room visit not greater than the last one
- **THEN** it is rejected and the known map is unchanged

#### Scenario: Teleport to a non-adjacent room
- **WHEN** an enter event names a room that is not behind an open door of the current room
- **THEN** it is rejected

### Requirement: Versioned fixed-size map encoding
The map encoder SHALL produce a float32 vector of constant size for schema version 1 and MUST
use coordinates relative to the current room.

#### Scenario: Growing map
- **WHEN** more rooms are discovered
- **THEN** the vector size is unchanged
