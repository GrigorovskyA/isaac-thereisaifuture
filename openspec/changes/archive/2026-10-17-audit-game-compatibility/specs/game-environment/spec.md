# Spec Delta

## MODIFIED Requirements

### Requirement: Verified game compatibility
The integration MUST record actual game/mod versions and available APIs before
claiming Repentance+ support. Compatibility records SHALL distinguish local
file/configuration evidence, source/documentation evidence, and real-game probes;
unprobed runtime capabilities MUST remain unknown.

#### Scenario: Candidate bridge claims compatibility
- **WHEN** an external README claims Isaac support
- **THEN** the installed version and a real probe are checked before accepting compatibility

#### Scenario: Read-only audit completes before installation
- **WHEN** required runtime probes need a game modification outside the authorized scope
- **THEN** the audit records unknown capabilities and exact gated actions and can
  complete as an audit without claiming verified game integration

### Requirement: Training profile isolation
Game tests MUST use a verified authorized training profile; main saves and Steam
Cloud MUST NOT be changed without specific authorization. A separate save slot
SHALL NOT establish isolation without checking shared settings, mod data,
Cloud, runtime save synchronization, and a restoration procedure.

#### Scenario: Isolation has not been verified
- **WHEN** a test requires game reset but the profile is not verified
- **THEN** the destructive test remains blocked while read-only auditing may continue

#### Scenario: Separate slot shares external state
- **WHEN** a proposed training slot shares options, mod data, or synchronized saves
- **THEN** the isolation assessment identifies those shared writes and requires
  an authorized isolation and restoration verification before game tests
