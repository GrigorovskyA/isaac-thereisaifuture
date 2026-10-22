## ADDED Requirements

### Requirement: Eligibility gate before start
The run controller SHALL call an injected eligibility gate before starting each run and MUST NOT
start the run when the gate denies or raises.

#### Scenario: Gate denies or fails
- **WHEN** the gate returns a denied decision or raises
- **THEN** no run starts, the episode is reported as ineligible and the series stops

### Requirement: Separate failure taxonomy
The run report SHALL distinguish won, death, truncated, fault and ineligible episodes, and MUST
exclude faults and ineligible aborts from win-rate and depth denominators.

#### Scenario: Backend fault
- **WHEN** the backend or a policy raises during a run
- **THEN** the episode is a fault, not a death, and is listed in the report

### Requirement: Release on every exit
The controller MUST release held actions after every started run, including after faults.

#### Scenario: Policy crash
- **WHEN** a policy raises mid-run
- **THEN** the backend release is called exactly once and the run is a fault

### Requirement: Bounded levels
Each level SHALL be bounded by a decision budget and a wall-time budget; exceeding either MUST
truncate the run rather than report a death.

#### Scenario: Wall budget exceeded
- **WHEN** the level deadline passes during combat
- **THEN** the run outcome is truncated

### Requirement: Complete JSON report
The report SHALL list every episode, including failures, and be JSON-serializable.

#### Scenario: Faulted series
- **WHEN** every episode faults
- **THEN** the report still contains each episode and zero valid episodes
