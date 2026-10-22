## ADDED Requirements

### Requirement: Layout-only candidate scoring
The system SHALL rank secret-room candidates deterministically from known room cells only, and MUST NOT accept hidden layout or labels in any policy-path function.

#### Scenario: Ranking uses adjacency
- **WHEN** candidates are ranked for a known layout
- **THEN** cells adjacent to at least two known rooms are listed by descending neighbor count with an explanation

#### Scenario: Exceptional layout
- **WHEN** only single-neighbor cells exist and the exceptional option is enabled
- **THEN** they are returned and labelled exceptional

### Requirement: Bounded search with attempt records
The system SHALL stop a search when the bomb or step budget is exhausted, a room is found, or no candidates remain, and SHALL record every attempt.

#### Scenario: Budget exhausted
- **WHEN** the bomb budget is reached without a find
- **THEN** the search stops with reason bombs_exhausted and one record per attempt

### Requirement: Baseline-compared evaluation
The system SHALL compute discovery rate and success per bomb against a seeded random valid-wall baseline with an equal budget, using oracle truth only in a separate evaluation function.

#### Scenario: Deterministic comparison
- **WHEN** evaluation is repeated with the same floors, budget and seed
- **THEN** the results are identical
