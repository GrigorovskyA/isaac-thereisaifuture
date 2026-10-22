## ADDED Requirements

### Requirement: Explicit bounded measured firing evidence
The live bridge SHALL export firing evidence only under negotiated opt-in and
SHALL distinguish unsupported/unavailable weapons from known ordinary tears.
At most32 native projectile-line checks SHALL occur per sample. Reward data MUST
remain outside policy inputs and normalization.

#### Scenario: Supported and unsupported weapon
- **WHEN** ordinary tears and measured candidate cells are available
- **THEN** range,vulnerable target and positively checked projectile-clear cells are exported
- **WHEN** required APIs or weapon semantics are unsupported
- **THEN** shaping is explicitly unavailable and no guessed geometry earns reward

### Requirement: Reward only novel reachable firing-position progress
The shaping ledger SHALL use a measured walking path to a range-valid,aligned,
projectile-clear position and SHALL pay at most0.25 per physical room per collector.
Software resets/reentry SHALL NOT renew that allowance.

#### Scenario: Standing and repeated movement
- **WHEN** the player stands,shoots into empty space,presses a wall or repeats an approach/retreat
- **THEN** no repeated progress credit is paid
- **AND** baseline resets,target movement and room reentry alone pay nothing

#### Scenario: Invalid or changing geometry
- **WHEN** clearance,range,path,weapon support or coherent target/grid identity is absent
- **THEN** no position bonus is paid
- **AND** stale/replayed frames or exhausted history fail explicitly

### Requirement: Separate learning contract and gameplay success
The live firing reward SHALL be opt-in under live-firing-v3, retain existing combat
coefficients and oracle coverage, and reject old reward-contract resume before
environment creation. Shaping SHALL NOT count as damage,kill,clear or policy success.

#### Scenario: Legacy checkpoint
- **WHEN** t21760 or another conservative-v2 checkpoint is resumed with firing reward
- **THEN** compatibility fails explicitly without creating a game environment or fresh model

#### Scenario: Unchanged policy and management
- **WHEN** firing evidence changes or management navigation runs
- **THEN** existing encoded policy inputs remain unchanged and management earns no shaping
