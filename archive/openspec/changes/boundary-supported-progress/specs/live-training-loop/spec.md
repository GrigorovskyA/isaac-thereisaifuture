## ADDED Requirements

### Requirement: Measured boundary firing progress
The opt-in v5 reward SHALL extend supported interpolation only through a positively
measured current-pose ground line to the nearest fully walkable patch. It MUST keep
oracle support outside model inputs and preserve default v4 replay behavior.

#### Scenario: Initial corner escape
- **WHEN** initial up/right moves approach the same reachable interpolation patch with positive ground-line evidence
- **THEN** potential increases and new high-water progress can receive a capped bonus
- **AND** retreat, standing, oscillation, reset and room reentry do not renew credit

#### Scenario: Recover below the previous record
- **WHEN** measured retreat has charged a penalty and a later approach improves position below the old high-water record
- **THEN** the same-target recovery can refund only previously charged debt
- **AND** outstanding room debt is at most0.25, survives reset/reentry and does not renew novelty allowance
- **AND** cumulative recovery over any history cannot exceed zero; a closed supported oscillation has zero net recovery

#### Scenario: Unsupported or changing evidence
- **WHEN** a link is blocked, unavailable, mismatched to the pose, or its patch has blocked or unreachable support
- **THEN** the boundary extension is unavailable and no bonus is invented
- **WHEN** boundary endpoints select different patches without a common supported patch
- **THEN** the transition rebases without bonus

#### Scenario: Bounded negotiation and compatibility
- **WHEN** boundary support is off
- **THEN** no additional ground query occurs and v4 behavior remains available
- **WHEN** support is on
- **THEN** at most one extra native line query and a bounded grid scan occur per capture
- **WHEN** a v4 checkpoint is resumed under v5
- **THEN** compatibility fails before environment creation without model initialization

#### Scenario: Acceptance evidence
- **WHEN** offline tests or counterfactual probes pass
- **THEN** native geometry and learned gameplay acceptance remain separate pending checks
