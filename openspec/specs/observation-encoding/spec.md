# observation-encoding Specification

## Purpose

Define bounded, versioned policy-visible entity observations, explicit masks and
overflow, separate oracle records, native read-only negotiation and recorded
fixture replay. Evidence must distinguish simulated peers from installed-game probes.

## Requirements

### Requirement: Fixed-shape masked policy observation
The encoder SHALL convert a validated entity frame into a deterministic float32 vector with
per-kind fixed capacity, presence masks and per-field validity masks. Missing objects MUST be
distinguishable from objects at zero coordinates. Overflow MUST be counted in diagnostics.

#### Scenario: Variable entity count
- **WHEN** frames with zero, partial and over-capacity entity lists are encoded
- **THEN** every output has the same shape and over-capacity frames report the overflow count

#### Scenario: Object at the origin
- **WHEN** one frame has no enemy and another has an enemy at relative position (0, 0)
- **THEN** the presence mask differs between the two outputs

#### Scenario: Unknown field
- **WHEN** an enemy has no observable HP
- **THEN** its HP validity bit is 0 and the value slot is not interpreted as zero HP

### Requirement: Stable ordering and determinism
Entities SHALL be ordered by distance to the player, then by spawn generation and entity ID.
Identical input MUST produce identical output.

#### Scenario: Shuffled input
- **WHEN** the same entities arrive in a different order
- **THEN** the encoded observation is identical

### Requirement: Oracle separation
Oracle and reward events MUST use a distinct type and stream. The encoder MUST reject any
frame carrying oracle fields, and recordings MUST NOT mix policy frames and oracle events.

#### Scenario: Oracle field in a policy frame
- **WHEN** a frame contains an unknown or oracle-only field
- **THEN** validation fails and nothing is encoded

### Requirement: Versioned recording and replay
Recordings SHALL carry a manifest with observation schema version, and replay MUST reproduce
the same encoded observations and reject incompatible versions.

#### Scenario: Round trip
- **WHEN** frames are recorded and replayed
- **THEN** encoded observations are identical to the live ones

#### Scenario: Incompatible version
- **WHEN** a recording declares an unsupported schema version
- **THEN** replay fails with an explicit error before yielding any frame

### Requirement: Real-game fixture validation
Acceptance of this contract SHALL require recorded real-game fixtures from the installed
build to pass schema validation. Until then the capability is an offline contract only.

#### Scenario: No real fixtures
- **WHEN** only synthetic fixtures exist
- **THEN** the change is not archived and the roadmap item stays unchecked

### Requirement: Explicit native entity negotiation
Native entity snapshots MUST require entity_observation_v1 and remain read-only,
mutually exclusive with actions/restart. Default snapshots MUST retain their
existing shape. Nested frame identity and player data MUST match the envelope.

#### Scenario: Default observer connects
- **WHEN** the peer does not request entity_observation_v1
- **THEN** the adapter does not scan entities and sends no entity_frame field

#### Scenario: Invalid or stale nested frame
- **WHEN** session, epoch, frame, room or player data disagrees with the envelope
- **THEN** Python rejects the message and closes the peer

### Requirement: Bounded visible export
Native export MUST bound scans, object count and wire bytes, report all source
capacity drops and exclude hidden data. Entity coordinates MUST be player-relative;
player coordinates MUST be room-local. Reconnect MUST preserve live entity IDs;
room recreation MUST NOT reuse IDs within an epoch.

#### Scenario: More objects than export capacity
- **WHEN** a valid room contains too many visible objects of a supported kind
- **THEN** the nearest objects are exported with per-kind source_overflow counts

#### Scenario: Scan fails or exceeds its bound
- **WHEN** a native API fails or the scan bound is exceeded
- **THEN** the snapshot is unavailable with no partial or stale entity frame

#### Scenario: Unobservable or hidden values
- **WHEN** API-accessible enemy HP, seeds, hidden entities or hidden map data exists
- **THEN** the export omits hidden entities/map/seeds and marks enemy HP unknown

### Requirement: Finite recording and bounded replay
The attach-only recorder MUST enforce sample/time budgets and release files and
sockets on failure. Replay MUST reject oversized, blank or incompatible records.
Existing recordings MUST NOT be overwritten.

#### Scenario: Peer fails during recording
- **WHEN** the peer disconnects or the wall-time budget expires
- **THEN** recording stops with a non-success result and all resources close

#### Scenario: Invalid recording file
- **WHEN** a line is blank, oversized or incompatible
- **THEN** replay fails explicitly before yielding that line
