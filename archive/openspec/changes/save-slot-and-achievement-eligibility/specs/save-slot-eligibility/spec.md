## ADDED Requirements

### Requirement: Fail-closed eligibility
The eligibility gate SHALL allow progression only when the observed slot is 2, achievements are
enabled, no console or debug use, edited or imported save, or achievement-blocking mod is present,
and the game version is known. Unknown or missing evidence MUST be denied with an explicit reason.

#### Scenario: All evidence good
- **WHEN** every evidence field is observed and acceptable
- **THEN** the decision is allowed with no reasons

#### Scenario: Wrong slot
- **WHEN** the observed slot is not 2
- **THEN** the decision is denied with reason slot_wrong

#### Scenario: Unknown evidence
- **WHEN** any evidence field is None or the game version is empty
- **THEN** the decision is denied with the matching unknown reason

### Requirement: Guard before progression
The system MUST provide a guard that raises EligibilityError carrying the denial reasons before any
autonomous progression when the decision is denied.

#### Scenario: Denied guard
- **WHEN** require_eligible is called with a bad console or debug flag
- **THEN** EligibilityError is raised with reason console_debug_used

### Requirement: Audit record
The system SHALL produce a JSON-serializable audit record of evidence and decision that contains no
personal paths.

#### Scenario: Serialize record
- **WHEN** an audit record is built for any decision
- **THEN** it round-trips through JSON and includes allowed, reasons and evidence values
