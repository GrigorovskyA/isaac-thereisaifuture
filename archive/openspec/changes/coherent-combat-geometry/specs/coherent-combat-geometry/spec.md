## ADDED Requirements
### Requirement: Target-coherent progress with correct open-path sign
The v4 ledger SHALL use supported interpolated graph distances, separate target
records and one persistent room allowance of at most0.25. Legacy v3 replay MUST
remain unchanged and v3 resume under v4 MUST fail explicitly.
#### Scenario: Open-passage retreat and target switch
- **WHEN** a player retreats from the only goal on an open row or column
- **THEN** no progress bonus is paid
- **WHEN** a different visible target becomes nearest
- **THEN** its unpaid baseline does not inherit another target's high-water value
- **AND** returning to old targets, resetting or reentering does not renew credit
#### Scenario: Missing interpolation support
- **WHEN** a required corner is blocked,unreachable or outside measured support
- **THEN** no potential is guessed and no position bonus is paid

### Requirement: Explicit observable geometry and compatibility
The opt-in observation2 SHALL expose ordinary weapon range, bounded local ground
and visible-target projectile probes with known masks. It MUST NOT contain oracle
HP, navigation grids, hidden targets or reward goal cells. Schema1 remains unchanged.
#### Scenario: Blocked shot and absent API
- **WHEN** a visible target is in range behind a projectile blocker
- **THEN** schema2 distinguishes in-range from a blocked line
- **WHEN** a probe or weapon API is unavailable
- **THEN** unknown is encoded explicitly without guessed clearance
#### Scenario: Old checkpoint and default mode
- **WHEN** schema1 checkpoint is resumed in schema2 mode
- **THEN** rejection occurs before environment creation without a fresh model fallback
- **WHEN** geometry opt-in is off
- **THEN** legacy649 inputs and no additional line queries are retained
