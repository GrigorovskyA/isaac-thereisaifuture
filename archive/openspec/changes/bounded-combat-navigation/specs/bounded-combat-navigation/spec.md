## Purpose

Find combat through bounded ordinary-room management travel while excluding all
scripted navigation and its metadata from learned combat experience.

## ADDED Requirements

### Requirement: Negotiated management telemetry
The bridge SHALL emit versioned navigation metadata only when combat_navigation_v1
is negotiated with live_loop_v1. It MUST expose at most eight unique slots with
finite positions and only existing open unlocked ordinary-room exits, plus current
room identity and geometry. Unknown API/data MUST fail closed.

#### Scenario: Default peer
- **WHEN** navigation is not requested
- **THEN** no navigation field is emitted and existing wire behavior is preserved

#### Scenario: Missing support or malformed telemetry
- **WHEN** the required capability is absent or duplicate/out-of-range data arrives
- **THEN** negotiation or transport validation rejects it before movement

### Requirement: Bounded same-client traversal
Opt-in traversal SHALL run only inside gate reset with the policy controller
stopped, using fresh active clear/empty snapshots and existing structured commands.
It MUST admit all twelve ordinary room shapes using measured walkability, prefer
less-used reachable observed exits, and keep its memory scoped to connection,
epoch and floor. All eight door positions MUST use measured coordinates.

#### Scenario: Repeated empty room
- **WHEN** a previously used room has another eligible less-used exit
- **THEN** that exit is preferred without a screenshot or operator plan

#### Scenario: Damage or stuck movement
- **WHEN** health changes or three consecutive pulses fail to move
- **THEN** input is released and the run stops without claiming a room transition

#### Scenario: Unsupported or missing data
- **WHEN** navigation data is missing or the room shape is outside 1..12
- **THEN** no movement is sent and an explicit stop is recorded

### Requirement: Versioned measured path geometry
The runner MUST negotiate combat_navigation_grid_v2 and require navigation version
2 with a bounded current-room walkability grid. Legacy v1 peers MUST retain their
previous telemetry. Routing SHALL use only safe four-neighbor cells and measured
door approach coordinates, replan before pulses and stop on unreachable exits.

#### Scenario: Every native layout
- **WHEN** a room uses shape 1..12, including any rotated L room
- **THEN** a route uses only measured walkable cells, avoiding walls and concave voids

#### Scenario: Obstacles change
- **WHEN** a previously selected path becomes blocked
- **THEN** the next pulse replans around it or stops without a direct fallback

#### Scenario: Malformed or old geometry
- **WHEN** mask length, dimensions, spacing or version is invalid, or only v1 geometry is available
- **THEN** no navigation action is authorized

#### Scenario: Continue is still loading
- **WHEN** active render snapshots repeat a frozen gameplay frame
- **THEN** navigation and automatic readiness wait for two consecutive same-context frame advances without renewing the handoff deadline

### Requirement: Navigation limits and release
Navigation MUST release after <=6-frame no-shoot pulses and by default stop at 256 commands,
90 pulse seconds, four transitions, three stationary pulses, damage, invalid or
same-context rejected state, or the original gate/run deadline. Limits MUST NOT
renew between handoffs. An explicit integer navigation budget scale 1..5 MAY
multiply only cumulative command, pulse-second and transition caps. Other safety
limits and original deadlines MUST remain unchanged and the scale MUST be logged.

#### Scenario: Explicit multi-attempt budget
- **WHEN** scale5 is selected for an authorized multi-attempt session
- **THEN** cumulative caps are1280 commands,450 pulse seconds and20 transitions, retained across deaths/handoffs, while default runs retain256/90/4

#### Scenario: Budget exhausted
- **WHEN** a navigation limit is reached
- **THEN** the run stops with input released and no automatic budget renewal

#### Scenario: Release races the room callback
- **WHEN** release is rejected while the latest snapshot still names the source room
- **THEN** no further action is sent until fresh same-session/epoch data confirms a later room visit with unchanged health within 0.5 seconds and the original budgets; otherwise the run stops, without claiming a neutral acknowledgment

#### Scenario: Accepted release precedes the doorway callback
- **WHEN** a final outward pulse from the measured door approach releases successfully while the snapshot still names the source room
- **THEN** poll without further movement for at most0.5 seconds within the original cumulative pulse/gate/run limits; unchanged health/session/epoch and a later native visit are required to claim a transition, otherwise any next pulse requires a fresh valid measured route

#### Scenario: Small doorway alignment correction
- **WHEN** the player is only a few units outside alignment tolerance
- **THEN** the navigation lease is at least two and at most six frames, without disabling the stationary stop

#### Scenario: Player is partway through an open doorway
- **WHEN** the player passed the safe interior approach inside the selected open door's narrow crossing corridor
- **THEN** movement continues outward, without recentering backwards or allowing a fallback through blocked interior cells

#### Scenario: Last enemy disappears before doors open
- **WHEN** an active ordinary room has no living enemies, room_clear is still false and no open ordinary exit is reported
- **THEN** management waits without movement or learning for at most two wall seconds in that context under the original deadlines; health changes stop, pause or an earlier room_clear update does not renew the wait, and fresh open exits or returning combat must pass the existing validation

#### Scenario: No exit after the settling interval
- **WHEN** the same empty uncleared context never reports an eligible open exit within the bounded interval
- **THEN** management stops explicitly without fabricating a room clear, transition or checkpoint

### Requirement: Management and learning separation
Navigation SHALL produce no env.step, rollout sample, reward, normalizer update or
recurrent policy input. Combat readiness MUST use existing token/context validation
and a fresh combat snapshot. Default operator-gated runs MUST remain unchanged.

#### Scenario: Travel between encounters
- **WHEN** the gate traverses an empty room and reaches combat
- **THEN** only combat steps enter the learner and readiness is checked on the new context

#### Scenario: Room changes during resume
- **WHEN** the accepted combat context changes before env.reset completes
- **THEN** existing resume-race validation withholds policy control
