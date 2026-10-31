## ADDED Requirements

### Requirement: Reward v12 values
Reward v12 SHALL equal reward v11 except `door_shaping.coefficient` 4.0, `outcome.death` -11.0,
`outcome.stall_restart` -4.0 and `stagnation.per_second` -0.39, with `grace_seconds` 12 and
`blocked_cost` 0.0 unchanged. Door shaping SHALL stay potential-based with max |Phi| = 24.

#### Scenario: Config values
- **WHEN** `configs/reward-v12.yaml` is loaded
- **THEN** the coefficients carry exactly these values

#### Scenario: Door pull
- **WHEN** the same sequence of steps is paid under v11 and v12
- **THEN** every door shaping payment under v12 is twice the one under v11

### Requirement: Stall limit in the reward contract
Reward v12 SHALL define `stall: {seconds: 30}`, a number > 0 and greater than
`stagnation.grace_seconds`. The section SHALL be required for v12 and forbidden for v4 to v11.

#### Scenario: Loader
- **WHEN** a v12 config has no `stall` section, or seconds that are missing, boolean, not
  positive or not above the grace period
- **THEN** loading fails
- **AND** a v11 config with a `stall` section fails too

### Requirement: Stall limit matches the contract
`make_live_env` SHALL raise ValueError when a given `stall_seconds` differs from the reward's
`stall.seconds`. `load_training_config` SHALL raise TrainingConfigError when
`watchdog.stall_seconds` differs from it.

#### Scenario: Mismatching limit
- **WHEN** the training config sets `watchdog.stall_seconds` 40 under reward v12
- **THEN** loading the training config fails

#### Scenario: Live env
- **WHEN** `make_live_env` gets reward version 12 and `stall_seconds` 40
- **THEN** it raises ValueError

### Requirement: A death never pays better than a stall
Under reward v12 a full stall (`stall_restart` plus the stagnation floor at the stall limit)
SHALL cost no less than a death with 1 or 6 half hearts of damage taken.

#### Scenario: Cost order
- **WHEN** the shipped v12 config is evaluated
- **THEN** the full stall is -11.02 and the death is -11.5 (1 half heart) or -14.0 (6)

### Requirement: Reward v11 contracts refused
The pure training config SHALL name reward version 12, and a contract with an older reward
version SHALL be refused.

#### Scenario: Reward v11 contract
- **WHEN** a training config names `reward_version: 11`
- **THEN** loading it fails
