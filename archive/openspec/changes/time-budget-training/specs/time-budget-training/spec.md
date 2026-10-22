## ADDED Requirements

### Requirement: Explicit time-governed counts
Time-budget sessions SHALL derive nonbinding step/restart schema sentinels within
the supported finite window, use time-dominant navigation and retain deadline,
resource, lineage, local input, no-progress and infrastructure guards.

#### Scenario: Many deaths or decisions before deadline
- **WHEN** a time-only window up to4h runs with compatible configuration
- **THEN** count sentinels cannot practically stop it before the fixed deadline

#### Scenario: Hidden or conflicting count limit
- **WHEN** explicit counts conflict, the window exceeds4h or config ceilings bind
- **THEN** preflight refuses before game/approval rather than claiming time-only execution
