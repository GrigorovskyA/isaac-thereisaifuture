## ADDED Requirements

### Requirement: Distinct diagnostic comparator
A scripted approach baseline SHALL read only exported observation slots,remain bounded and be labeled not learned. It MUST NOT alter the learned checkpoint or use management/oracle navigation as combat input.

#### Scenario: Known blocker and shooting alignment
- **WHEN** a visible target has a known intervening obstacle or poor cardinal alignment
- **THEN** withhold the direct shot and seek an approximate local firing opportunity using bounded observation-only search

### Requirement: Explicit time-dominant continuation
A four-hour continuation SHALL preserve model,optimizer,normalizer,RNG and all nonbudget training settings from the declared compatible parent. It SHALL impose no death cap and no binding step/restart cap during that time,while preserving infrastructure,resource,focus and cleanup guards.

#### Scenario: Continue from current state
- **WHEN** the exact compatible t6912 parent is available
- **THEN** record the budget-only lineage,verify unchanged binary state,and resume rather than initialize

#### Scenario: Stop or missing lineage
- **WHEN** the wall deadline,infrastructure fault or missing/incompatible lineage occurs
- **THEN** release input,stop and preserve completed checkpoints without silently starting over
