## ADDED Requirements

### Requirement: Typed obstacles
Observation schema 5 SHALL give every obstacle a class (rock, marked rock, bomb rock,
block, pit, spikes, poop, TNT, fire, wall, other) read from the game, SHALL include
fireplaces as `fire` obstacles and SHALL NOT export wall cells, including the side walls
of narrow and L-shaped rooms that lie inside the rectangular grid. The `wall` class stays
in the one-hot and is unused by the observer.

#### Scenario: Narrow room side walls
- **WHEN** the player is in a narrow room whose side walls are grid cells inside the
  outer ring of the rectangular grid
- **THEN** no obstacle with class `wall` is exported and the room shape is reported

#### Scenario: Pickup behind rocks
- **WHEN** a pickup is surrounded by rocks
- **THEN** the nearest obstacle slots carry the rock class at the rocks' positions

#### Scenario: Obstacle without a class
- **WHEN** an obstacle entity arrives without `obstacle_class`
- **THEN** decoding fails with a protocol error

### Requirement: Minimap facts
The frame SHALL include the rooms the in-game minimap shows or the player visited, with
shape, visited and current flags and the room type only when its icon is shown or it was
visited, and SHALL NOT include undisplayed rooms.

#### Scenario: Neighbour revealed
- **WHEN** the player stands in the start room and a neighbouring room is displayed
- **THEN** the map block marks the start room current and visited and the neighbour known but not visited

### Requirement: Stall clock
The observation SHALL include the stall watchdog's idle time as a fraction of its limit,
and 0 when no watchdog runs.

#### Scenario: Idle then progress
- **WHEN** 45 active seconds pass without progress and then an enemy is damaged
- **THEN** the stall clock reads 0.5 before the damage and 0 after it
