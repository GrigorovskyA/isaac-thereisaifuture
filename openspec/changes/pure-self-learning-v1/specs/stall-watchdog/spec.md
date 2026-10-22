## ADDED Requirements

### Requirement: Stall detection
The watchdog SHALL measure active wall time since the last progress event
(`enemy_damaged`, `room_entered`, `room_cleared`, `pickup_gained`, `floor_entered`).
Paused or unavailable time MUST NOT count. After 90 s it SHALL truncate the
episode with reason `stall` and send one restart command.

#### Scenario: Stuck in a room
- **WHEN** 90 active seconds pass with living enemies and no progress event
- **THEN** the episode is truncated with reason `stall` and one restart is sent

#### Scenario: Pause
- **WHEN** the game is paused for 120 s and then resumes
- **THEN** the paused time does not count toward the stall limit

### Requirement: Faults are not stalls
Missing snapshots, disconnects and protocol errors SHALL be infrastructure faults,
never stalls, and MUST NOT be used as learning outcomes.

#### Scenario: Game not responding
- **WHEN** no snapshot arrives within the transport timeout
- **THEN** the step ends as an infrastructure fault and no stall restart is sent
