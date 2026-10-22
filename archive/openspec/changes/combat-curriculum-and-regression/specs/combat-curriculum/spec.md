## ADDED Requirements

### Requirement: Validation-only stage advancement
The curriculum SHALL advance a stage only when validation metrics meet the stage's predeclared threshold, and MUST refuse any other split.

#### Scenario: Threshold on confidence bound
- **WHEN** the validation clear-rate CI lower bound is below the stage threshold or episodes are too few
- **THEN** the advancement decision is false

#### Scenario: Test split refused
- **WHEN** advancement is requested with the test split
- **THEN** a ValueError is raised

### Requirement: Frozen regression tolerance
The regression gate SHALL use a frozen, hashed tolerance and MUST fail when the new policy regresses on the old task set beyond it.

#### Scenario: Clear-rate regression
- **WHEN** the new clear rate falls below the snapshot minus the tolerance
- **THEN** the gate fails and records the tolerance hash

#### Scenario: Tolerance cannot change
- **WHEN** a tolerance field is assigned after construction
- **THEN** the assignment raises an error

### Requirement: Negative-result retention
The results log SHALL append every stage outcome including failures and MUST detect removal or alteration of entries.

#### Scenario: Dropped failure
- **WHEN** a failed entry is removed from the log file
- **THEN** reading the log raises an error

### Requirement: Policy input integrity
Policy inputs SHALL be exactly the encoded observation size and MUST be rejected otherwise.

#### Scenario: Oversized input
- **WHEN** a policy is called with a vector larger than the observation size
- **THEN** OracleLeakageError is raised
