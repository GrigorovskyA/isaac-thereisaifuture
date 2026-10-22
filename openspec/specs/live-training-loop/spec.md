# live-training-loop Specification

## Purpose
Provide an explicitly authorized, bounded real-game learning pipeline that combines
native observations, movement, shooting and natural-death restarts, while keeping
approximate reward labels separate from policy inputs and preserving cleanup,
protocol validation and run budgets.

## Requirements

### Requirement: Combined live-loop negotiation
The observer SHALL combine entity observation, actions and death restart only through the
`live_loop_v1` capability, which MUST be advertised only under a valid training approval.

#### Scenario: Training approval present
- **WHEN** a valid training approval is loaded and Python requests live_loop_v1 with entity, action and restart capabilities
- **THEN** the hello acknowledgement lists live_loop_v1 and snapshots carry an entity frame and a separate oracle block

#### Scenario: Incomplete or mixed request
- **WHEN** live_loop_v1 is requested without one of the three modes or together with the oracle probe
- **THEN** the observer closes the session without arming actions or restart

#### Scenario: Training approval without live loop
- **WHEN** a training approval is loaded and only safe_actions_v1 is requested
- **THEN** the handshake fails and no input is applied

### Requirement: Bounded training approval
A training approval MUST name slot 2, MUST NOT be bound to a game epoch, MUST expire within
8 hours and MUST declare a restart limit of 1..5000.

#### Scenario: Approval survives a death restart
- **WHEN** a live session restarts the game after death
- **THEN** the approval remains loaded and the next session can negotiate live_loop_v1 again

#### Scenario: Normal exit or invalid approval
- **WHEN** the operator exits the game normally, or the approval has an epoch, a longer expiry or no restart limit
- **THEN** live_loop_v1 and actions are not available

#### Scenario: Restart budget exhausted
- **WHEN** the number of restart attempts reaches max_restarts or the lease expires
- **THEN** no further restart is dispatched and the Python side reports a bounded fault

### Requirement: Oracle separation
Live oracle data SHALL be transmitted only in the snapshot `oracle` block and MUST NOT appear
in the policy-visible entity frame, the observation encoding or the normalizer input.

#### Scenario: Enemy HP is exported
- **WHEN** an active enemy has hit points
- **THEN** its HP appears only in the oracle block and the entity frame still reports unknown HP

### Requirement: Race-tolerant live commands
In a live session, a well-formed command that is stale or arrives while the game is paused or
the player is dead SHALL receive a rejected acknowledgement and release input; malformed,
noncanonical, wrong-session or non-increasing commands MUST still close the session.

#### Scenario: Command races a death
- **WHEN** a live action command arrives after the player died
- **THEN** the observer answers rejected, holds no input and keeps the session for the pending restart

#### Scenario: Replayed sequence
- **WHEN** a live command repeats an earlier sequence number
- **THEN** the session closes and input is released

### Requirement: Live episodes over a continuing run
The live backend SHALL treat episodes as segments of one run: death and room clear terminate,
the time limit truncates without a reset, and an epoch change without an observed death MUST be
an infrastructure fault rather than a death.

#### Scenario: Death and autonomous restart
- **WHEN** the oracle reports player death
- **THEN** the episode terminates with outcome death and the next reset waits for the restarted game and reconnects

#### Scenario: Restart without observed death
- **WHEN** snapshots change game epoch before any death was observed
- **THEN** an episode fault is raised and recorded and no death is reported

#### Scenario: Python blocks during a model update
- **WHEN** the training process does not step for longer than the observer output deadline
- **THEN** the reader keeps draining snapshots and the session stays open

### Requirement: Approximate event derivation
Reward events in the live loop SHALL be derived from consecutive oracle blocks and MUST be
documented as approximate; derived kills MUST be suspended while the enemy list overflows.

#### Scenario: Enemy damaged then vanished
- **WHEN** an enemy HP decreases and the enemy later disappears without overflow
- **THEN** damage, remaining-HP damage and one kill event are emitted for that entity

#### Scenario: Room re-entry
- **WHEN** the player enters another room visit
- **THEN** enemy tracking restarts without kill events and no room-clear event is emitted on entry

#### Scenario: Changing membership during overflow
- **WHEN** overflowing snapshots expose different sets of enemies
- **THEN** tracking stays bounded to the current 64-enemy list and missing identities are discarded without invented damage or kills

### Requirement: Live budgets and fatal protocol failures remain bounded
The live backend SHALL apply one absolute run deadline to reset, reconnect,
pause waits and fault retries. Expiry MUST stop without retry renewal; an already
running bounded I/O operation may finish within its configured timeout. A fatal
reader protocol failure MUST propagate before reconnection clears its state.

#### Scenario: Initial reset exceeds remaining budget
- **WHEN** no playable state arrives before the run deadline
- **THEN** the run stops as budget exhaustion without spending more fault retries

#### Scenario: Fatal reader before reset
- **WHEN** the reader has already recorded a protocol error before reset
- **THEN** reset raises that error without reconnecting or converting it to an episode

#### Scenario: Training budget interrupts a rollout
- **WHEN** the run deadline interrupts a model rollout
- **THEN** the environment is closed and the log records budget exhaustion without claiming a new checkpoint for the unfinished rollout
