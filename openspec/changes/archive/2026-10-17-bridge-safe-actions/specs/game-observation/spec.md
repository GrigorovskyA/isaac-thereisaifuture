# Spec Delta

## MODIFIED Requirements

### Requirement: Negotiated loopback connection
The observer SHALL use only IPv4 loopback TCP and bounded UTF-8 newline JSON.
Protocol and schema versions MUST be 1. Hello SHALL negotiate required capabilities
and a fresh session; mismatches MUST fail before any snapshot is accepted.
Default observation MUST be read-only. Arbitrary gameplay or executable command
endpoints MUST NOT be allowed.

#### Scenario: Optional control capabilities
- **WHEN** a peer requests an optional control mode
- **THEN** death_restart_v1 MUST obey post-death-restart requirements and
  safe_actions_v1 MUST obey native-player-actions requirements; the two modes
  MUST NOT be combined

#### Scenario: Compatible peer
- **WHEN** a Lua peer answers a version-1 hello with the required capabilities
- **THEN** the client exposes validated version provenance and the agreed session

#### Scenario: Unsupported or malformed peer
- **WHEN** the peer sends incompatible versions, unknown fields, invalid JSON or a missing capability
- **THEN** the client closes that peer with an explicit protocol error
