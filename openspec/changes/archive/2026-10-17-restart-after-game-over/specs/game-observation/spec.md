## MODIFIED Requirements

### Requirement: Negotiated loopback connection
The observer SHALL use only IPv4 loopback TCP and bounded UTF-8 newline JSON.
Protocol and schema versions MUST be 1. A hello request SHALL negotiate required
capabilities and a fresh connection session; mismatches MUST fail before
any snapshot is accepted. Default observation MUST be read-only. The optional
death_restart_v1 mode MUST obey post-death-restart requirements. No arbitrary
gameplay or executable command endpoints are allowed.

#### Scenario: Compatible peer
- **WHEN** a Lua peer answers a version-1 hello with the required capabilities
- **THEN** the client exposes validated version provenance and the agreed session

#### Scenario: Unsupported or malformed peer
- **WHEN** the peer sends incompatible versions, unknown fields, invalid JSON or a missing capability
- **THEN** the client closes that peer with an explicit protocol error
