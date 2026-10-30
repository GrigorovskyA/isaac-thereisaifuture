## ADDED Requirements

### Requirement: Oracle door graph labels
Each oracle door SHALL carry `target`, the grid index (0..168) of the room behind the door, or
-1 when it cannot be read or is off the 13 x 13 grid, and `usable`. A door SHALL NOT be usable
when it is locked, when it leads to a closed secret, super secret or ultra secret room, or when
its lock or target type cannot be read.

#### Scenario: Target and usable flag
- **WHEN** a room has a plain open door to room 85, a locked door to room 86 and a closed door
  to a secret room 87
- **THEN** the oracle lists targets 85, 86 and 87 with `usable` true, false and false

#### Scenario: Unreadable target
- **WHEN** the level lookup of a door's target fails or returns an off-grid index
- **THEN** the door is listed with `target` -1

### Requirement: Oracle room grid
The live oracle SHALL carry `room_grid`, the grid index of the current room, or -1. The door
labels and `room_grid` are reward labels: they SHALL NOT appear in the policy frame, and a
snapshot without them or with values outside -1..168 SHALL be rejected.

#### Scenario: Current room grid
- **WHEN** the current room descriptor has GridIndex 97
- **THEN** `room_grid` is 97
- **AND** it is -1 for a descriptor outside 0..168
