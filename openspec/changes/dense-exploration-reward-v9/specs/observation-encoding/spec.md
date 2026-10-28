## ADDED Requirements

### Requirement: Visited cells block
Observation schema 7 SHALL append a visited-cells block of 26 x 14 floats (row-major) to the
policy vector: 1.0 for every 40 px floor tile, counted from the room interior corner (60, 140), in which the player stood in the current room during the current run, else 0.
`OBSERVATION_SIZE` SHALL be 3863 and checkpoints of schemas 5 and 6 SHALL be refused.

#### Scenario: Cell set on visit
- **WHEN** the player stands at (300, 200)
- **THEN** exactly the cell (6, 1) is 1.0
- **AND** it stays 1.0 on later steps

#### Scenario: Outside the room
- **WHEN** the player position is outside the largest room
- **THEN** the nearest edge cell is set

### Requirement: Visited cells scope
Cells SHALL be computed from observed facts only (player position, stage, the current minimap
room). The room SHALL be identified by stage and the current minimap room; a room without a grid
position SHALL start empty on every visit. A new session or game epoch SHALL clear all rooms.

#### Scenario: Separate rooms
- **WHEN** the player enters another room and returns
- **THEN** each room shows only its own cells

#### Scenario: New run
- **WHEN** the game epoch or session changes
- **THEN** all cells are cleared
