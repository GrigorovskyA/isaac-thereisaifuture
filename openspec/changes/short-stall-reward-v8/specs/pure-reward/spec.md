## ADDED Requirements

### Requirement: Reward v8 coefficients
Reward v8 SHALL equal reward v7 except `stagnation.per_second: -0.25` and
`stagnation.grace_seconds: 12`. The training config SHALL set the stall watchdog limit to
40 s and `reward_version: 8`. A death from full health (death plus six half-hearts lost)
SHALL NOT pay more than a full stall (stall restart plus the largest stagnation cost for the
configured stall limit).

#### Scenario: Suicide never pays better than a stall
- **WHEN** the reward v8 config and the training config stall limit are loaded
- **THEN** `stall_restart + per_second * (stall_seconds - grace_seconds)` is -12
- **AND** it is at least `death + 6 * player_damage_half_heart`

#### Scenario: Charging starts after the grace period
- **WHEN** the idle clock moves from 10 s to 14 s with a 12 s grace and -0.25 per second
- **THEN** the stagnation column is -0.5

#### Scenario: Full stall at the short limit
- **WHEN** an episode idles from 0 s to the 40 s stall limit and is truncated
- **THEN** the stagnation columns sum to -7.0 and the stall column is -5

### Requirement: Stagnation cap follows the configured stall limit
The stagnation ledger SHALL use the stall limit of the training config, not a default, and
SHALL refuse a stagnation grace period that is not shorter than that limit.

#### Scenario: Grace not shorter than the limit
- **WHEN** a ledger with a 12 s grace and a stagnation rate is created with a 12 s stall limit
- **THEN** creation fails

### Requirement: Old reward contracts refused
Checkpoints saved with the reward contract `pure-v7` or older SHALL be refused when the
config expects `pure-v8`.

#### Scenario: pure-v7 checkpoint
- **WHEN** a pure-v7 checkpoint is resumed with reward contract `pure-v8`
- **THEN** the resume is refused
