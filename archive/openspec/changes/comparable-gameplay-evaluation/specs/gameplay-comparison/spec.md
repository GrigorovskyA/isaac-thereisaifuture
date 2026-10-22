## ADDED Requirements

### Requirement: Frozen comparison matrix
The analyzer SHALL validate bounded manifests and content-hashed traces against
predeclared policy/case/repeat cells, complete policy identities and equal budgets.
Every attempted, missing or failed cell MUST remain visible. Splits MUST NOT mix.

#### Scenario: Changed or duplicate evidence
- **WHEN** a hash changes or a cell occurs twice
- **THEN** analysis refuses rather than silently replacing evidence

#### Scenario: Unmatched or missing attempt
- **WHEN** a case/start/budget differs or an expected attempt is absent
- **THEN** all available attempts are reported and paired comparison is blocked

### Requirement: Reward-independent raw gameplay metrics
The analyzer SHALL derive conservative enemy HP loss, observed player HP loss,
verified clears/deaths and phase exposure from raw samples independently of reward.
Gaps, disappearance, healing, inactive/unknown phases and empty starts MUST NOT
invent damage, kills or clears. Unknown and faults MUST be reported separately.

#### Scenario: Enemy disappears or heals
- **WHEN** an enemy disappears, changes phase, or regains previously lost HP
- **THEN** no missing-HP kill or repeated novel-damage credit is invented

#### Scenario: Censored or empty encounter
- **WHEN** an encounter starts empty, stops mid-room, loses coverage or faults
- **THEN** it is retained with coverage/exposure and is not a verified negative clear outcome

### Requirement: Descriptive paired reporting
Reports SHALL include all policies, exposures, metric denominators, clear uncertainty
and pairwise differences only for complete matched native evidence. Reward, tensor
changes, synthetic traces, shadow/mixed or assisted control MUST NOT establish learning.

#### Scenario: Synthetic or assisted input
- **WHEN** evidence is synthetic, shadow, mixed-control or assisted
- **THEN** metrics stay descriptive and no paired gameplay comparison or learning claim is emitted

#### Scenario: Complete matched cells
- **WHEN** all declared native cells meet the frozen comparison contract
- **THEN** the report includes per-cell candidate-minus-reference damage/clear differences and retains all failures without declaring a winner
