# Spec Delta

## ADDED Requirements

### Requirement: Opt-in firing callback values
`callback_trace` SHALL remain default off. It MAY read `FireDelay` and
`MaxFireDelay` only for shooting input and native-tear diagnostic records. It
MUST preserve the shared nonrenewable ten-second, 512-attempt and 300-byte
limits, correlate existing identities, encode invalid values as `na`, and
never write player properties.

#### Scenario: Shooting callback with fractional cooldown
- **WHEN** an authorized held shooting input is queried with trace enabled
- **THEN** its record includes returned input and finite raw cooldown values at that phase

#### Scenario: Missing or invalid property
- **WHEN** a cooldown is absent, nonnumeric, nonfinite or outside the diagnostic bound
- **THEN** its value is na and no player property is written

### Requirement: Sparse firing diagnostic mode
`firing_diagnostics` SHALL be default off and opt in only when literally true.
Without `callback_trace`, it SHALL record only the commanded direction's
`GET_ACTION_VALUE`, at most once per game frame. When both switches are true,
the existing exhaustive trace takes precedence. Sparse mode shares its limits,
omits render/update/release-input records, retains action/tear/release/lifecycle
facts, and emits a final `stop reason=close` unless a budget stop already ended it.

#### Scenario: Sparse firing-only sampling
- **WHEN** `firing_diagnostics` is enabled without `callback_trace` during a held shooting command
- **THEN** only the commanded direction's `GET_ACTION_VALUE` is recorded, no more than once in each game frame, while the explicit release event is retained without per-button release-input records

#### Scenario: Detailed callback tracing remains compatible
- **WHEN** both diagnostic switches are enabled
- **THEN** the existing exhaustive `callback_trace` hook behavior remains in effect under the same shared limits

#### Scenario: Sparse trace closes within action lease
- **WHEN** the bounded firing probe closes its connection before the original trace deadline
- **THEN** the trace emits an explicit stop record without requiring a lease-extending heartbeat

#### Scenario: Disabled or failed diagnostics
- **WHEN** trace is off or a diagnostic read/sink fails
- **THEN** ordinary input and expiry/disconnect cleanup remain unchanged and no diagnostic retry renews the window

#### Scenario: Native tear correlation
- **WHEN** the approved controlled player fires during its current held shooting command
- **THEN** a bounded trace may correlate that tear with identity and raw cooldown without creating another tear

### Requirement: Diagnostic gameplay independence
Firing diagnostics MUST NOT modify input returns, command expiry, wire/policy
observations, normalization, rewards or action authority. Read/sink/recursive
failures MUST disable diagnostics without blocking cleanup. Real firing
acceptance requires native cooldown/input/tear evidence and operator-confirmed
cleanup; offline tests MUST NOT count as real-game acceptance.

#### Scenario: Cooldown read failure during active command
- **WHEN** a diagnostic cooldown getter throws
- **THEN** diagnostics stop while the input result and subsequent expiry/release behavior match the disabled mode

### Requirement: Empty-room firing preflight
The probe SHALL require a manually confirmed file-2 approval, active type-0
player and centered-room position (x=120..520, y=100..420). Before commands, a
read-only entity handshake on the same listener MUST find no enemies,
projectiles or overflow of those kinds. The action snapshot MUST match its
epoch, room, health and position. Any failed check closes the peer without an
action. The check uses game state and no screen capture.

#### Scenario: Empty-room preflight rejects unsafe state
- **WHEN** the read-only entity feed is paused, has an enemy/projectile, overflows those kinds, or disagrees with the subsequent action snapshot
- **THEN** the probe sends no shooting command and closes the connection

### Requirement: Bounded stationary cadence comparison
The attach-only probe MUST remain stationary (`move=none`), run for at most 30
seconds and 16 commands, send seven three-frame shots, one neutral command,
seven six-frame shots and one release, and never restart or retry. It MUST stop
on changed status, session, epoch, room, health, position or budget; cleanup
releases while connected and otherwise closes the peer. Sparse trace closure
logs `stop reason=close` without heartbeat renewal.

#### Scenario: Fixed stationary comparison completes
- **WHEN** the approved active instance remains in the same live room for the fixed probe
- **THEN** it sends the bounded two-phase schedule with no movement, ends with release and reports actual command/frame identities

#### Scenario: Readiness changes during the comparison
- **WHEN** the game pauses, becomes unavailable, changes room/epoch/session/health/position, or the budget expires
- **THEN** the probe sends no further shooting command, attempts release within the same command budget and never reconnects or restarts
