# native-player-actions Specification

## Purpose

Provide bounded native player movement and shooting without granting general game
commands or silently extending ordinary-profile observation authorization.

## Requirements

### Requirement: Explicit profile action authority
The adapter MUST require reviewed profile authority and active slot-2 evidence.
Authority SHALL be verified isolation or an explicit user-approved ordinary-profile
exception for bounded action tests, never an isolation claim. Local approval MUST
expire within 30 minutes; action authority MUST expire after 120 seconds per mod
load, without reconnect renewal. Default observation SHALL remain read-only;
actions and death restart MUST be mutually exclusive. Launch/selection remain manual.

#### Scenario: Missing evidence
- **WHEN** an action peer connects without valid local profile/slot approval
- **THEN** action negotiation fails before any input override

#### Scenario: Explicit ordinary-profile exception
- **WHEN** the user explicitly approves bounded movement/shooting on their ordinary profile
- **THEN** that recorded exception may replace isolation for this test only, without authorizing training, save/Cloud edits or forced resets

#### Scenario: Different run or incompatible mode
- **WHEN** an action targets another epoch or requests death restart simultaneously
- **THEN** the adapter rejects it and clears bridge inputs

### Requirement: Bounded independent native actions
Only player-0 cardinal movement and independently selected cardinal shooting,
neutral, release and heartbeat SHALL be supported through native input callbacks.
Each accepted command SHALL return an identity-bound acknowledgement;
acceptance MUST NOT be reported as actual movement or projectile evidence.

#### Scenario: Move and shoot independently
- **WHEN** a valid action selects right movement and up shooting
- **THEN** only those native movement/shooting inputs are held for player 0

### Requirement: Strict command identity
Commands MUST include protocol, session, increasing command sequence, game epoch,
room visit and observed frame. The observed frame MUST match the most recent sent
snapshot and be no more than 15 game frames old. Unknown fields, versions,
directions, stale identities and replayed commands MUST be rejected fail-closed.

#### Scenario: Stale replay or malformed command
- **WHEN** a command repeats sequence or carries invalid identity, fields or version
- **THEN** no command is applied and held bridge inputs are cleared

### Requirement: Expiry and cleanup
An action SHALL last at most 15 advancing game frames and 250 milliseconds from
acceptance. Heartbeats SHALL expire after 500 milliseconds and MUST NOT extend an
action. Explicit neutral SHALL set all eight inputs to zero; release SHALL return
manual input handling. Input-time checks MUST prevent a stale hold on resume even if render callbacks
were stalled. Work, framing and queues MUST remain bounded and nonblocking in Lua.

#### Scenario: Client fails while holding
- **WHEN** Python disconnects or stops sending heartbeats
- **THEN** Lua clears the hold on detected disconnect or expiry and never overrides with the old action after the 250 ms action deadline

### Requirement: Lifecycle cleanup
Disconnect, Python failure, pause, death, room/floor/run transition, exit, unload
and callback faults MUST clear bridge holds. A cleared hold MUST NOT resume
without a fresh valid action.

#### Scenario: Heartbeat or transition while holding
- **WHEN** heartbeats continue without a fresh action or the game pauses, dies or changes room
- **THEN** the old action expires or clears and cannot resume without a fresh valid action

### Requirement: Separate offline and runtime acceptance
Offline tests MUST exercise parsing, expiry, stale/replayed/incompatible actions,
reconnect and cleanup. Runtime acceptance MUST require approved profile authority and
instance/slot evidence, specific runtime authorization, 50 controlled sequences
with actual position and shooting evidence, explicit release and measured cleanup
after disconnect and Python failure. Missing prerequisites MUST leave runtime
tasks incomplete and prevent archive or roadmap completion.

#### Scenario: Live control blocked
- **WHEN** profile authority, slot identity or specific runtime permission is unresolved
- **THEN** independent offline work is completed and the exact blocker is recorded without issuing live inputs

### Requirement: Observable native action evidence
Native diagnostics SHALL record accepted commands, expiry/release and matching
player-fired tear velocity with command identity, game frame and local time.
Input acknowledgements alone MUST NOT establish shooting. Evidence SHALL remain
bounded and separate from default observation; unsupported weapon effects MUST
be reported unverified.

#### Scenario: Controlled ordinary tears
- **WHEN** player 0 fires a native tear during an authorized shooting action
- **THEN** diagnostics identify that command and observed tear direction without spawning projectiles

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
