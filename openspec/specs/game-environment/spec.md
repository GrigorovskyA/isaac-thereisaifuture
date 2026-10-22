# game-environment Specification

## Purpose

Define baseline constraints for the future game loop. Implementation is scheduled
in the roadmap.

## Requirements

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

### Requirement: Safe bounded actions
The future bridge SHALL bind commands to session and episode identity, reject
stale actions, and release control after disconnect, timeout, or client shutdown.

#### Scenario: Python client disconnects during movement
- **WHEN** the client stops maintaining its heartbeat
- **THEN** the watchdog releases held actions within the protocol's specified limit

#### Scenario: Action belongs to previous episode
- **WHEN** a command with the previous episode ID arrives after reset
- **THEN** the bridge rejects it without applying it to the new episode

### Requirement: Policy observation boundary
Policy observations MUST contain only player-permitted information and reference
knowledge; hidden oracle state SHALL be supplied separately for reward/evaluation only.

#### Scenario: Secret room remains undiscovered
- **WHEN** the oracle knows secret-room coordinates but the player has not revealed it
- **THEN** actor observations and normalization exclude those coordinates and hidden identifiers

### Requirement: Explicit transition outcomes
The Gymnasium adapter SHALL distinguish gameplay terminal outcomes, time
truncation, and infrastructure failures while maintaining session/episode/frame consistency.

#### Scenario: Transport times out during step
- **WHEN** a valid next frame is not received before the timeout
- **THEN** the system reports an infrastructure fault instead of returning stale
  state as a successful transition

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
