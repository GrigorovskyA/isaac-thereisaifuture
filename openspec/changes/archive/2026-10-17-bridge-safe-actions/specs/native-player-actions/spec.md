# Spec Delta

## Purpose

Provide bounded native player movement and shooting without granting general game
commands or silently extending ordinary-profile observation authorization.

## ADDED Requirements

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
