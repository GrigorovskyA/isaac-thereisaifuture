## ADDED Requirements

### Requirement: Oracle doors
The live oracle block SHALL list the existing doors of the current room as `doors` (at most 8,
unique slots 0..7), each with `x`, `y` (world position of the door slot), `open` and
`unexplored` (the room behind the door has never been visited).

#### Scenario: Doors listed
- **WHEN** a room has an open door to an unvisited room and a closed door to a visited room
- **THEN** the oracle lists both with their positions, `unexplored` true and false

#### Scenario: No doors
- **WHEN** the room has no door
- **THEN** `doors` is an empty list

### Requirement: Unreadable door data
A door whose position cannot be read SHALL be skipped. A door whose target room cannot be read
SHALL be listed with `unexplored` false.

#### Scenario: Unreadable target
- **WHEN** the level has no readable room for a door's target
- **THEN** the door is listed with `unexplored` false

### Requirement: Doors are labels
The door list is a reward label: it SHALL NOT appear in the policy frame. A snapshot without it
or with malformed entries SHALL be rejected, and a live snapshot with eight doors SHALL stay
below the 49152-byte message limit.

#### Scenario: Malformed doors
- **WHEN** a snapshot has nine doors, a duplicate slot, a slot outside 0..7 or a non-finite
  coordinate
- **THEN** it is rejected
