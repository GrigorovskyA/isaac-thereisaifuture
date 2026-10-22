# Spec Delta

## Purpose

Provide bounded, explicitly read-only observations of the current visible player
and room, with negotiated compatibility and honest connection failures.

## ADDED Requirements

### Requirement: Negotiated loopback connection
The observer SHALL use only IPv4 loopback TCP and bounded UTF-8 newline JSON.
Protocol and schema versions MUST be 1. A hello request SHALL negotiate required
read-only capabilities and a fresh connection session; mismatches MUST fail before
any snapshot is accepted. No gameplay or executable command endpoints are allowed.

#### Scenario: Compatible peer
- **WHEN** a Lua peer answers a version-1 hello with the required capabilities
- **THEN** the client exposes validated version provenance and the agreed session

#### Scenario: Unsupported or malformed peer
- **WHEN** the peer sends incompatible versions, unknown fields, invalid JSON or a missing capability
- **THEN** the client closes that peer with an explicit protocol error

### Requirement: Bounded responsive transport
Each message MUST be at most 16384 bytes excluding LF. Python SHALL use absolute
accept, handshake and message deadlines. Lua SHALL use nonblocking I/O, bounded
buffers and work per callback, and disconnect on stalled output or invalid requests.
Fragmented and combined messages MUST retain framing and partial-send progress.

#### Scenario: Slow or absent Python
- **WHEN** Python is absent, stops reading, or sends an oversized/partial request
- **THEN** Lua returns from callbacks without waiting and expires the connection

#### Scenario: Fragmented stream
- **WHEN** a message is split across reads or several arrive together
- **THEN** complete messages are decoded once, bounded by size and absolute deadline

### Requirement: Explicit observation semantics
Snapshots SHALL contain schema/session, sequence, game epoch, engine frame,
availability, current-room visit identity and player-0 position/raw health.
Unavailable state MUST carry null frame/room/player with a reason. Coordinates,
health units and identity lifetimes MUST be documented without hidden map data
or fabricated game versions.

#### Scenario: Active or paused game
- **WHEN** player and room reads succeed
- **THEN** snapshots expose documented raw fields and explicit pause status

#### Scenario: Menu or transition
- **WHEN** no player/room is available or a read fails
- **THEN** snapshots report unavailable state, or the client reports a timeout if callbacks stop

### Requirement: Ordered sessions and cleanup
Sequence MUST strictly increase within a session. Engine frames MUST NOT regress
within a game epoch; equal frames are allowed for sampling/pause. A new epoch
permits a new frame origin. Reconnection MUST negotiate a new session and reset
ordering history. Errors and interruption SHALL close peer/listener resources.

#### Scenario: Duplicate or stale data
- **WHEN** sequence repeats/regresses, epoch regresses, frame regresses or session differs
- **THEN** the client rejects the message instead of exposing stale state

#### Scenario: Reconnect or interrupt
- **WHEN** the peer reconnects or the user interrupts observation
- **THEN** a reconnect has a fresh session and interruption releases sockets

### Requirement: Evidence separates simulation from integration
Offline peers and Lua stubs MUST be labeled simulated. Real-game acceptance
SHALL require authorized profile/deployment, actual handshake and manually
correlated changing state, a ten-minute soak and responsive reconnect/shutdown.
Blocked runtime tasks MUST remain incomplete and prevent integration archival.

#### Scenario: Deployment not authorized
- **WHEN** profile isolation or specific deployment authorization is absent
- **THEN** local implementation can be delivered but real-game acceptance stays blocked
