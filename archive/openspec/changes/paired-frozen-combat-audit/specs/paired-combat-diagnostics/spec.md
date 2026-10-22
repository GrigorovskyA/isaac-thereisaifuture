## ADDED Requirements

### Requirement: Policy-only geometric proxy
The diagnostic SHALL consume only an existing encoded policy vector and a valid
integer action,without changing either. It SHALL label its shooting alignment
as a proxy rather than a hit,clear or gameplay-success measure.

#### Scenario: Known relative direction
- **WHEN** an unclipped nearest enemy is at a nonzero relative position
- **THEN** report the cosine between shooting and enemy direction,with screen-y signs and no-shoot explicitly distinguished

#### Scenario: Unavailable geometry
- **WHEN** no target exists,coordinates are clipped,or distance is zero
- **THEN** mark geometry unavailable rather than invent an alignment success

#### Scenario: HP or invalid input
- **WHEN** HP features alone change,or the shape/action is invalid
- **THEN** HP changes do not alter geometry,and invalid inputs are rejected

### Requirement: Honest paired pilot
Frozen decision comparison SHALL use identical encoded inputs and no optimizer,
normalizer update or checkpoint writes. Only the scheduled policy SHALL control
the game. Oracle/phase labels SHALL stay separate and MUST NOT enter inference.
Sequential gameplay outcomes MUST NOT be attributed to shadow actions or ranked
as matched-policy gameplay evidence.

#### Scenario: Same input to three policies
- **WHEN** t1536,t6912 and random actions are recorded at a decision
- **THEN** distinguish executed policy/action from shadows,verify immutable state,and report common history/window reset rules

#### Scenario: Native pilot stops early
- **WHEN** a death,gate,wall-time or step cap ends a window or the audit
- **THEN** retain all outcomes and censored windows,release inputs,close owned game and remove the exact approval without unplanned retries
