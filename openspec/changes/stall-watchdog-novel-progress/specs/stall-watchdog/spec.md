## ADDED Requirements

### Requirement: Only new facts are progress
The watchdog SHALL treat as progress only enemy damage, room clears and facts new for
the current run: a `(stage, room_index)` room or a floor not seen this run, coin, bomb
or key counters above the run's peak, and a collectible not held before. Re-entering a
known room or regaining a counter up to its earlier peak MUST NOT reset the watchdog.

#### Scenario: Walking between two known rooms
- **WHEN** the agent crosses one door back and forth for 90 active seconds without
  damage, clears or new pickups
- **THEN** the episode is truncated with reason `stall` and one restart is sent

#### Scenario: Bomb placed and another picked up
- **WHEN** the bomb counter drops from 1 to 0 and a bomb pickup raises it to 1 again
- **THEN** the watchdog is not reset
