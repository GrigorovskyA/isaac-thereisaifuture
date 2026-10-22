## ADDED Requirements

### Requirement: Gymnasium contract
The environment SHALL implement reset, step and close with fixed observation and action spaces
and MUST pass the Stable-Baselines3 environment checker.

#### Scenario: Environment checker
- **WHEN** the SB3 checker runs on the environment
- **THEN** it reports no error

#### Scenario: Invalid action
- **WHEN** an action outside the action space is passed to step
- **THEN** a ValueError is raised and the game state is unchanged

### Requirement: Explicit transition outcomes in the adapter
The environment SHALL return terminated for death or room clear and truncated for timeout, and
MUST raise an infrastructure fault instead of returning a transition for a transport failure.

#### Scenario: Transport fault during step
- **WHEN** the backend times out during a step
- **THEN** step raises an episode fault, no observation is returned and later steps require reset

### Requirement: Seed semantics
Reset SHALL pass a derived game seed to the backend and MUST report whether the backend can honor it.

#### Scenario: Same seed twice
- **WHEN** reset is called twice with the same seed on a seed-supporting backend
- **THEN** the first observations are identical

### Requirement: Oracle channel separation
The environment MUST NOT expose oracle events in observations or info and SHALL deliver them only to
an explicit sink.

#### Scenario: Events during a step
- **WHEN** a step produces oracle events
- **THEN** they reach the sink and no info key carries them

### Requirement: Stale-state rejection over long runs
The environment SHALL NOT accept a repeated or regressing frame within an episode.

#### Scenario: Ten thousand steps
- **WHEN** ten thousand steps run with automatic resets on the offline backend
- **THEN** within each episode frame IDs strictly increase
