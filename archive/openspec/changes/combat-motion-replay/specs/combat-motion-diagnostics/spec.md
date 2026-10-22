## ADDED Requirements

### Requirement: Identity-bound motion evidence
Offline motion analysis SHALL compare only same-session,epoch,visit samples with
increasing accepted frames within15updates. It SHALL distinguish requested
movement,idle actions and measured displacement without declaring collisions.

#### Scenario: Comparable motion pair
- **WHEN** two poses share context and a1..15frame gap
- **THEN** report distance and signed progress along the first pose's requested movement;near-stationary requires movement and distance below0.5

#### Scenario: Invalid temporal or identity link
- **WHEN** contexts differ,frames do not increase or the gap exceeds15
- **THEN** return unavailable rather than attribute motion across resets or waits

### Requirement: Analysis-only grid routes
Route diagnostics SHALL use only the finite measured walking mask,with explicit
unavailable results for invalid or unreachable endpoints. They MUST NOT control
combat,alter model inputs or label walking blockers as projectile collisions.

#### Scenario: Detour exists
- **WHEN** endpoints are walkable and connected through a detour
- **THEN** return a cardinal shortest cell path including both endpoints and identify it as measured-grid reachability only

#### Scenario: No valid path
- **WHEN** an endpoint is outside or blocked,or components are disconnected
- **THEN** return unavailable without inventing a direct route or moving the character
