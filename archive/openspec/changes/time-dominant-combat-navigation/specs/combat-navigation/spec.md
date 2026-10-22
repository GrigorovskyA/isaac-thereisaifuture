## Purpose

Find further ordinary combat using observed room geometry and confirmed travel,
while bounding control and distinguishing local exploration from learned gameplay.

## ADDED Requirements

### Requirement: Explicit finite navigation modes
Default navigation SHALL retain cumulative diagnostic limits. Explicit time-dominant
mode MUST require a finite global deadline, omit cumulative command/transition/pulse
time stops, and use the finite session window as its handoff cap. Per-pulse,
release, identity, health, freshness, path and stationary guards MUST remain active.

#### Scenario: More than twenty transitions
- **WHEN** a time-dominant session traverses more than twenty observed rooms before another fight
- **THEN** travel can reach combat without a cumulative count stop and management frames never enter learning

#### Scenario: Deadline or local safety failure
- **WHEN** the shared deadline expires or an action/health/freshness guard fails
- **THEN** input is released and navigation stops without renewing the budget

### Requirement: Observed route memory
Navigation SHALL remember only observed ordinary-room exits and directed connections
confirmed by a selected door followed by a fresh same-floor room transition. It MUST
prefer reachable unexplored exits or confirmed routes to an observed frontier, reset
memory on session/epoch/floor changes, and never infer hidden neighbors or reverse edges.

#### Scenario: Return through cleared rooms
- **WHEN** a known route returns to a room with an unexplored observed exit
- **THEN** navigation follows that route and then attempts the unexplored exit

#### Scenario: Changed game context
- **WHEN** session, epoch or floor changes
- **THEN** old routes cannot authorize travel in the new context

### Requirement: Explain no further progress
Time-dominant navigation SHALL stop when no observed unexplored ordinary exit is
reachable, distinguishing exhausted observed connections, unreachable frontier and
transport/safety faults. It MUST log the local search state, preserve learning
state, and never label partial exploration as full-floor completion or invoke New Run.

#### Scenario: Closed observed cycle
- **WHEN** all observed exits in a repeated route have confirmed destinations and no frontier remains
- **THEN** navigation reports observed-component exhaustion and stops without another cycle

#### Scenario: Unreachable exit
- **WHEN** an unexplored observed exit has no measured local path or confirmed route
- **THEN** navigation reports unreachable frontier rather than successful exploration or endless circling
