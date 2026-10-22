## MODIFIED Requirements

### Requirement: Released handoff between encounters
Each gated reset SHALL release input, enter waiting_for_operator and issue a new
readiness request before any decision. Waiting MUST produce no observations,
rollout samples, normalization updates or reward. Without explicit auto-navigation,
waiting MUST send no action commands. Opt-in navigation management MUST follow
bounded-combat-navigation and keep only bounded transport/routing state.

#### Scenario: Run starts in an empty room
- **WHEN** an operator-managed gated run starts while the room has no enemies
- **THEN** zero actions are sent and zero samples are collected until readiness

#### Scenario: Room cleared
- **WHEN** a gated combat episode ends with a room clear
- **THEN** the terminal reward is returned, input is released and the next reset waits

#### Scenario: Natural restart
- **WHEN** the player dies and the game restarts into an empty start room without auto-navigation
- **THEN** the gate waits for operator readiness instead of acting

#### Scenario: Explicit death budget
- **WHEN** a gated run declares an integer death limit1..10 and that many terminal death outcomes have been observed
- **THEN** the gate releases and stops before another readiness request or environment reset, without fabricating a completed rollout; completed checkpoints survive and partial samples are reported separately

### Requirement: Explicit provenance-bound readiness
Combat SHALL resume only after a fresh readiness acknowledgment naming the current
request id, session, game epoch and room visit, while the latest state is combat.
The gate MUST reject invalid, stale, replayed, predating, future, cross-session,
cross-epoch and cross-room acknowledgments. The ordinary operator gate MUST NOT
resume because enemies appear. Only explicit auto-navigation may supply readiness
automatically from fresh verified combat; it MUST use the same token/context checks.

#### Scenario: Enemy appears during the wait
- **WHEN** enemies appear in operator mode while no readiness was acknowledged
- **THEN** the gate keeps waiting and sends no action

#### Scenario: Replayed readiness
- **WHEN** an acknowledgment for an already accepted request is submitted again
- **THEN** it is rejected as replayed and logged
