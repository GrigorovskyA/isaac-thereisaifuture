## ADDED Requirements

### Requirement: Known-room option selection
The floor policy interface SHALL offer only decisions whose target is a known room, and the
executor MUST reject any other decision.

#### Scenario: Unknown room targeted
- **WHEN** a decision targets a room absent from the known rooms
- **THEN** validation raises an illegal-decision error

#### Scenario: No legal option
- **WHEN** the view has no legal decision
- **THEN** the floor ends as truncated with outcome stuck

### Requirement: Boss routing precondition
Boss routing SHALL require a known boss room, and descending MUST require the exit to be available.

#### Scenario: Boss unknown
- **WHEN** no boss room is known
- **THEN** the go-boss and descend options are not legal

### Requirement: Distinct floor outcomes and metrics
The executor SHALL report death as terminated, timeout or stuck as truncated, and infrastructure
faults separately from both, with per-source decision counts.

#### Scenario: Fault during an option
- **WHEN** the backend raises a floor fault
- **THEN** the outcome is fault, neither terminated nor truncated, and the fault is counted

#### Scenario: Decision budget exhausted
- **WHEN** the floor is not completed within the decision budget
- **THEN** the outcome is a timeout (truncated), not a death

### Requirement: Labelled deterministic baselines
Random and scripted floor baselines SHALL be deterministic for a given seed and MUST label every
decision with its source.

#### Scenario: Repeated seeded runs
- **WHEN** the random baseline runs twice with the same seed on the same synthetic floor
- **THEN** outcome, rooms cleared and damage are identical
