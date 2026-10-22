# combat-experience-gate Specification

## Purpose
Restrict opt-in live experience to observed combat and hand control back to the
operator between encounters, using fresh provenance-bound readiness, neutral
input and bounded waits without adding manual-navigation samples or reward.

## Requirements

### Requirement: Opt-in gate preserves default modes
The combat-experience gate SHALL be enabled only by an explicit live-run flag. Without
it, random, train, eval-live and observe behavior, logs and records MUST remain
unchanged. The gate MUST NOT change rewards, coefficients, entity encoding, the
checkpoint format or the Lua wire protocol.

#### Scenario: Default run is ungated
- **WHEN** a live run starts without the combat-gate flag
- **THEN** no gate wrapper, request file or gate record is created

### Requirement: Conservative combat eligibility
The gate SHALL classify each snapshot as combat, cleared, empty, dead, paused,
transition, ambiguous or unavailable from existing structured observations and the
oracle block. Only combat (live active player, known uncleared room with complete
coverage, at least one listed enemy with positive hp, unchanged visit) MUST be
eligible. Missing or overflowing data MUST NOT be treated as combat, kill or clear.

#### Scenario: Overflow is ambiguous
- **WHEN** the oracle reports enemy overflow
- **THEN** the snapshot is ambiguous and not eligible

#### Scenario: First frame of a new room
- **WHEN** a snapshot's session, epoch or room visit differs from the previous one
- **THEN** it is a transition and not eligible

### Requirement: Eligibility is management metadata only
Eligibility and oracle values used by the gate MUST NOT enter the encoder, policy,
recurrent state, normalizer or reward ledger, and MUST NOT create a reward label or
coefficient.

#### Scenario: Observation is unchanged
- **WHEN** combat resumes after a handoff
- **THEN** the returned observation is the ordinary encoded frame of the reset

### Requirement: Released handoff between encounters
Each gated reset SHALL release input, enter waiting_for_operator and issue a new
readiness request before any decision. While waiting the gate MUST NOT send action
commands, produce observations or rollout samples, update normalization or credit
reward, and MUST keep only the bounded latest transport state.

#### Scenario: Run starts in an empty room
- **WHEN** a gated run starts while the room has no enemies
- **THEN** zero actions are sent and zero samples are collected until readiness

#### Scenario: Room cleared
- **WHEN** a gated combat episode ends with a room clear
- **THEN** the terminal reward is returned, input is released and the next reset waits

#### Scenario: Natural restart
- **WHEN** the player dies and the game restarts into an empty start room
- **THEN** the gate waits for operator readiness instead of acting

### Requirement: Eligibility maintained during combat
While combat is active the gate SHALL check eligibility and provenance on fresh
transport state before every action is sent and after every step. Any queued or
received state that is not same-visit combat MUST withhold the next action, release
input and end the segment as truncated with the gate exit reason, then hand off.

#### Scenario: Enemies vanish while the clear flag is false
- **WHEN** a step observes no living enemies and the room is not yet clear
- **THEN** the segment ends truncated as `empty` with no clear reward and no further action

#### Scenario: Wait after an eligibility loss
- **WHEN** a segment ends because eligibility was lost
- **THEN** the following wait adds no rollout samples or normalization updates

### Requirement: Eligibility loss keeps observed outcomes
When eligibility is lost, events already observed SHALL still be credited and a death
MUST remain a terminal death. The gate MUST NOT fabricate a clear or death outcome.

#### Scenario: Ineligible snapshot queued before the next action
- **WHEN** a snapshot queued before the next decision is ineligible
- **THEN** the action is not sent, queued damage events are credited and the segment truncates

#### Scenario: Death queued before the next action
- **WHEN** a death snapshot is queued before the next decision
- **THEN** the step ends as a terminal death and no action is sent

### Requirement: Explicit provenance-bound readiness
Combat SHALL resume only after a fresh readiness acknowledgment naming the current
request id, session, game epoch and room visit, while the latest state is combat.
The gate MUST reject invalid, stale, replayed, predating, future, cross-session,
cross-epoch and cross-room acknowledgments, and MUST NOT resume because enemies appear.

#### Scenario: Enemy appears during the wait
- **WHEN** enemies appear while no readiness was acknowledged
- **THEN** the gate keeps waiting and sends no action

#### Scenario: Replayed readiness
- **WHEN** an acknowledgment for an already accepted request is submitted again
- **THEN** it is rejected as replayed and logged

### Requirement: Private bounded handshake files
Handshake files SHALL live only in the fixed per-session directory
`<session>/combat_gate/`. The readiness command MUST write only `ready.json` there,
atomically, and only for a non-stopped request. The runner MUST bound ack size,
consume every ack once and discard leftover acks when a new request is issued.

#### Scenario: Stopped request
- **WHEN** the readiness command targets a stopped session
- **THEN** it refuses and writes nothing

### Requirement: Experience retained across encounters
Gated training SHALL perform the operator wait inside the environment reset, so a
terminal step and its reward remain in the rollout, the recurrent episode boundary
is kept, and one rollout spans several encounters until a normal update and
checkpoint. Interrupted rollouts MUST be reported as unsaved, never as an update.

#### Scenario: Several short fights
- **WHEN** several short gated encounters fill n_steps decisions
- **THEN** a real RecurrentPPO update and checkpoint occur with wait frames absent

### Requirement: Bounded waits and safe stop
One absolute run deadline SHALL include operator waits, pauses, resets and
reconnects. Each handoff MUST have a finite configurable wait cap within the run
budget. Expiry MUST stop the run without renewal, resume, launch or reset, release
input, mark the request stopped and close the client. Waiting is neither death nor
success; protocol errors stop the run.

#### Scenario: Operator never responds
- **WHEN** the wait cap expires without readiness
- **THEN** the run stops, the request is marked stopped and no fault retry occurs

### Requirement: Handoff deadline bounds resume and reconnect
Every wait, reconnect and resume reset SHALL be bounded by the smaller of the run
deadline and the current handoff cap and rechecked on return. Combat MUST NOT activate
after expiry, and neither deadline is renewed or widened.

#### Scenario: Cap expires inside the resume reset
- **WHEN** readiness was accepted but the shared reset or its reconnects outlast the cap
- **THEN** the reset is bounded by the cap, combat never activates and the run stops

### Requirement: Readiness requires fresh observations
Readiness SHALL be judged only against fresh observations. A disconnect or an
observation gap longer than the staleness window MUST clear the retained state.

#### Scenario: Readiness after an observation gap
- **WHEN** an acknowledgment arrives after a disconnect or a silent gap
- **THEN** it is rejected as `no_observation` until fresh state is observed

### Requirement: Gate exposure logging
The gate SHALL log state changes, readiness requests, accepts and rejects with
reasons, wait duration and skipped snapshots, observed room changes during waits,
combat decisions, terminal outcomes, gate exits, faults and unsaved steps,
separately from oracle events.

#### Scenario: Summary on stop
- **WHEN** a gated run stops
- **THEN** a summary row reports handoffs, rejects by reason, wait seconds and combat decisions
