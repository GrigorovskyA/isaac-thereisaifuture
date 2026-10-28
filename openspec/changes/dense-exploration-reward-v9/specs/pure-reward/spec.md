## ADDED Requirements

### Requirement: Reward v9 coefficients
Reward v9 SHALL equal reward v8 except `outcome.room_first_visit: 5.0`,
`outcome.floor_first_entered: 30.0`, new `outcome.boss_room_clear_first: 20.0`, pickups coin
0.3, bomb 0.5, key 0.5, `consumable_run_cap` 10.0, `collectible_new` 5.0, `novelty.coefficient`
0.1 and the new `door_shaping.coefficient: 2.0`. The archived v4-v8 configs SHALL stay loadable;
`door_shaping` and `boss_room_clear_first` SHALL be required for v9 and forbidden for older
versions.

#### Scenario: Older configs
- **WHEN** the archived v8 config is loaded
- **THEN** it loads without door shaping and without a boss bonus

### Requirement: Stall bound unchanged
Stagnation and the 40 s stall limit SHALL be unchanged. A death from full health SHALL NOT pay
more than a full stall.

#### Scenario: Suicide never pays better than a stall
- **WHEN** the reward v9 config and the training config stall limit are loaded
- **THEN** `stall_restart + per_second * (stall_seconds - grace_seconds)` is -12
- **AND** it is at least `death + 6 * player_damage_half_heart`

### Requirement: Boss room clear bonus
The first clear of a boss room (`RoomFacts.type` 5) per (stage, room) in a run SHALL pay
`boss_room_clear_first` in addition to `room_clear_first`. Later clears of that room and clears of
other room types SHALL pay no bonus.

#### Scenario: First boss clear
- **WHEN** a boss room is cleared for the first time in the run
- **THEN** the room clear column is 30
- **AND** a second clear event for that room pays 0

### Requirement: Door potential
`Phi(s) = -coefficient * d / D`, with `d` the distance from the player to the nearest open door
whose target room has not been visited and `D` the diagonal of the room shape's bounding box
(the ratio is at most 1). `Phi` SHALL be 0 when the room is not clear or has enemies, when no
open unexplored door exists, when the player is dead and when door data is missing.

#### Scenario: Room with enemies
- **WHEN** enemies are present or the room is not clear
- **THEN** the door shaping column is 0

#### Scenario: Visited targets
- **WHEN** every open door leads to a visited room
- **THEN** the door shaping column is 0

### Requirement: Potential-based door shaping
Reward v9 SHALL pay `gamma * Phi(s') - Phi(s)` per step in the `door_shaping` column, with
`gamma` the training discount. A terminal step SHALL use `Phi(s') = 0`. The episode start SHALL
set the first `Phi(s)` without paying. After a room change `Phi(s)` SHALL be the old room's last
value and `Phi(s')` the new room's.

#### Scenario: Walking toward a door
- **WHEN** the player walks toward an open unexplored door in a cleared room
- **THEN** every step pays a positive door shaping reward

#### Scenario: Closed loop
- **WHEN** the player walks away from the door and back to the starting point
- **THEN** the sum is 0 with gamma 1
- **AND** with the training gamma it is at most `(1 - gamma) * coefficient` per step

#### Scenario: Standing still
- **WHEN** the player stands still in a cleared room with an open unexplored door
- **THEN** each step pays only `(gamma - 1) * Phi`

#### Scenario: Terminal step
- **WHEN** a step ends the episode
- **THEN** it pays `-Phi(s)`

### Requirement: Old reward contracts refused
Checkpoints saved with the reward contract `pure-v8` or older, or observation schema 5, SHALL be
refused when the config expects `pure-v9` and schema 6.

#### Scenario: pure-v8 checkpoint
- **WHEN** a pure-v8 checkpoint is resumed with reward contract `pure-v9`
- **THEN** the resume is refused
