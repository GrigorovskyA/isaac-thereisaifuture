## ADDED Requirements

### Requirement: Demo recording capability
The observer SHALL advertise `demo_record_v1` without action approval and SHALL accept it only
together with `entity_observation_v1` and without any action, restart, live loop, native episode
or seeded restart capability. In that mode the observer MUST NOT inject input and each snapshot
SHALL carry the live oracle block at the live sample rate.

#### Scenario: Recording handshake
- **WHEN** a peer requests `entity_observation_v1` and `demo_record_v1`
- **THEN** the session streams snapshots with the oracle block at the live sample rate

#### Scenario: Mixed with control
- **WHEN** a peer requests `demo_record_v1` with `safe_actions_v1`, `death_restart_v1` or
  `live_loop_v1`
- **THEN** the handshake fails and no snapshot is sent

### Requirement: Human input masks
In demo mode each snapshot SHALL carry `human_input`: one 14-bit mask per game update since the
previous snapshot (player 0's held move, shoot, bomb, active and pill/card buttons, then the bomb,
active and pill/card buttons triggered on that update), at most 16 masks with older ones counted
as `dropped`. The policy frame MUST NOT contain the human input.

#### Scenario: Input masks
- **WHEN** the player holds left and shoot up for two updates and presses the bomb button once
- **THEN** the next snapshot has two masks with the left and shoot-up bits and one of them has the
  bomb-triggered bit

### Requirement: Demo run identity metadata
In demo mode the observer SHALL include the current run start seed in the oracle metadata when
available, or null when unavailable. The seed MUST NOT be encoded as a policy observation.

#### Scenario: Recording seed
- **WHEN** the game exposes the run start seed during a demo snapshot
- **THEN** the snapshot carries it in the oracle block for offline continuity checks
