## ADDED Requirements
### Requirement: Directional firing evidence
Firing audits SHALL separate cardinal alignment,measured projectile clearance and
range using only same-frame policy-visible data. Missing evidence MUST remain
unknown. They MUST NOT change model inputs,rewards,actions or label a proxy as a hit.

#### Scenario: Blocked or diagonal target
- **WHEN** a selected cardinal shot points near a blocked target or misses its axis
- **THEN** the audit distinguishes blocked alignment from missing alignment
- **AND** a coarse45-degree cone is not reported as clear firing evidence

#### Scenario: Unknown and incomplete observations
- **WHEN** weapon,line,frame identity or visible membership is unavailable
- **THEN** diagnostics retain uncertainty or reject inconsistent identity
- **AND** visible overflow does not prove all targets absent or blocked

#### Scenario: Opportunity and positive control
- **WHEN** another cardinal direction has a measured clear aligned in-range target
- **THEN** selected,missed and wrong-direction opportunity counts are separate
- **WHEN** a finite scripted native positive control damages an enemy
- **THEN** that damage is reported separately from frozen or learned model behavior
