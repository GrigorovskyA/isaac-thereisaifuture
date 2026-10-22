# Spec Delta

## MODIFIED Requirements

### Requirement: Training profile isolation
Training MUST use a verified authorized training profile. Bounded action tests
MAY use an explicitly user-approved ordinary-profile exception with current
instance/slot confirmation, a finite budget and release guards; this MUST NOT
imply isolation or permit training. Main saves and Steam Cloud MUST NOT change
without specific authorization. A separate slot SHALL require the isolation
checks below before it establishes isolation.

#### Scenario: Assess slot isolation
- **WHEN** a separate slot is proposed as isolation
- **THEN** shared settings, mod data, Cloud, runtime save synchronization and a
  restoration procedure MUST all be checked

#### Scenario: Isolation has not been verified
- **WHEN** a test requires game reset but the profile is not verified
- **THEN** the destructive test remains blocked while read-only auditing may continue

#### Scenario: Separate slot shares external state
- **WHEN** a proposed training slot shares options, mod data, or synchronized saves
- **THEN** the isolation assessment identifies those shared writes and requires
  an authorized isolation and restoration verification before game tests
