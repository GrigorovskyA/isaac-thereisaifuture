## ADDED Requirements

### Requirement: Bounded status sharing recovery
Atomic status publication SHALL retry transient Windows sharing replacement
refusals within1s while preserving old complete JSON and the original action
deadline. Persistent or unrelated errors MUST remain explicit faults.

#### Scenario: Windows reader holds destination
- **WHEN** status is briefly open without delete sharing
- **THEN** publication atomically succeeds after release without a torn snapshot

#### Scenario: Persistent or unrelated refusal
- **WHEN** sharing persists beyond1s or another permission error occurs
- **THEN** the writer stops boundedly with an explicit fault and prior status intact
