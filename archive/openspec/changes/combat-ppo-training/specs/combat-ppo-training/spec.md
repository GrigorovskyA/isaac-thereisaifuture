## ADDED Requirements

### Requirement: Bounded training
The training command SHALL validate its configuration and MUST stop at the first reached budget limit
among timesteps, wall time and checkpoint disk size.

#### Scenario: Invalid configuration
- **WHEN** the configuration has an unknown key or selects the test split
- **THEN** loading fails with a configuration error before any training starts

#### Scenario: Wall-time limit
- **WHEN** the wall-time budget is exhausted between chunks
- **THEN** training stops with stop reason wall_time after the last checkpoint

### Requirement: Self-describing checkpoints
Every checkpoint SHALL contain the model, the normalizer statistics and a manifest with schema
versions, config hash, seed, parent checkpoint, timesteps and RNG state, and loading MUST reject any
checkpoint whose schema versions, config hash or seed do not match.

#### Scenario: Incompatible schema version
- **WHEN** a checkpoint with a different observation schema version is loaded
- **THEN** a checkpoint error is raised

#### Scenario: Missing normalizer file
- **WHEN** the normalizer file named by the manifest is absent
- **THEN** a checkpoint error is raised

### Requirement: Explicit resume
Resume MUST fail with an explicit error when no compatible checkpoint exists and SHALL NOT start from
scratch silently.

#### Scenario: Resume without checkpoint
- **WHEN** resume is requested and the checkpoint directory is empty
- **THEN** a checkpoint error is reported and no training occurs

### Requirement: Predeclared selection rule
Model selection SHALL accept a model only when its clear-rate gain over the random baseline is at least
20 percentage points on at least 100 evaluation episodes, and MUST report an uncertainty interval.

#### Scenario: Threshold met
- **WHEN** the model clears 50 of 100 episodes and random clears 30 of 100
- **THEN** the model is accepted with improvement 0.20 and an interval is reported

#### Scenario: Too few episodes
- **WHEN** fewer than 100 evaluation episodes exist
- **THEN** the model is rejected regardless of the gain

### Requirement: All seeds reported
The multi-seed driver SHALL record every seed, including failed ones.

#### Scenario: One seed fails
- **WHEN** training for one seed raises an error
- **THEN** that seed is recorded as failed and the other seeds still run
