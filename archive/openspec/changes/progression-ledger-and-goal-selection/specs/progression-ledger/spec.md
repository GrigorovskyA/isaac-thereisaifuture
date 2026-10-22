## ADDED Requirements

### Requirement: Tamper-evident evidence ledger
The ledger SHALL be append-only JSONL where each event records source, session id, run id,
timestamp and the hash of the previous event, and the loader MUST detect any edited, removed
or reordered event.

#### Scenario: Edited event
- **WHEN** a stored event is modified after being written
- **THEN** the ledger reports failed verification and refuses to count or append goals

#### Scenario: Removed event
- **WHEN** an event in the middle of the file is deleted
- **THEN** verification fails because the hash chain is broken

### Requirement: Only observed evidence counts
The ledger SHALL count a goal as completed only when it has evidence with source
`observed_in_game`; `manual_note` and `inferred` evidence MUST NOT count.

#### Scenario: Non-observed evidence
- **WHEN** a goal has only manual_note or inferred events
- **THEN** it is not in the completed goals and the selector still treats it as remaining

### Requirement: Validated unlock graph
The unlock graph SHALL be loaded from data and MUST be rejected when a dependency is undefined
or the graph contains a cycle.

#### Scenario: Missing dependency
- **WHEN** a goal requires an id that is not defined
- **THEN** loading raises a graph error naming the missing dependency

#### Scenario: Cycle
- **WHEN** goals depend on each other in a loop
- **THEN** loading raises a graph error reporting a cycle

### Requirement: Deterministic explained goal selection
The selector SHALL choose the alphabetically first achievable goal that the target still needs,
SHALL return a reason and the remaining goals, and MUST refuse to select when ledger
verification fails.

#### Scenario: Repeated selection
- **WHEN** selection runs twice on the same graph and ledger
- **THEN** both results are identical and include a reason

#### Scenario: Unverified ledger
- **WHEN** the ledger fails verification
- **THEN** selection raises a ledger error instead of counting any goal
