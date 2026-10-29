## ADDED Requirements

### Requirement: Stall context metrics
Each episode row SHALL record `last_room_clear`. An episode truncated by the stall watchdog SHALL
also record the room context of its last snapshot in `stall_*` columns (clear flag, enemy counts
and kinds, nearest enemy, open doors, half hearts, seconds in the room), empty for every other
end. They SHALL NOT be a policy, normalizer or reward input. An older header SHALL be rewritten
once and keep its rows.

#### Scenario: Stall in an uncleared room
- **WHEN** an episode is truncated by the stall watchdog in an uncleared room with an invulnerable
  flying enemy
- **THEN** its row has `stall_room_clear` 0 and `stall_enemies_invulnerable` and
  `stall_enemies_flying` of at least 1

#### Scenario: Death
- **WHEN** an episode ends in death
- **THEN** its `stall_*` cells are empty and `last_room_clear` is set

#### Scenario: Older header
- **WHEN** the writer opens a file with the previous header
- **THEN** the file is rewritten with the full header and the old rows keep empty new cells
