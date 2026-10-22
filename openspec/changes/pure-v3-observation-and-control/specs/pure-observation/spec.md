## ADDED Requirements

### Requirement: Player capability facts
Observation schema 4 SHALL include player stats, 16 tear-flag bits and a weapon-type
multi-hot read from the game API, and SHALL NOT include external item knowledge.

#### Scenario: Spectral tears
- **WHEN** the player holds an item that grants spectral tears
- **THEN** the spectral bit is set in the frame and in the encoded vector

#### Scenario: Out-of-range stat
- **WHEN** a frame carries a stat outside its declared range
- **THEN** decoding fails with a protocol error

### Requirement: Own attacks and bombs are visible
Own tears, lasers and knives SHALL appear as `own_attack` entities and every bomb
as a `bomb` entity with its age, within fixed capacities and overflow counts.

#### Scenario: Placed bomb
- **WHEN** the player places a bomb
- **THEN** the next frames contain a `bomb` entity at its position with increasing age until it explodes
