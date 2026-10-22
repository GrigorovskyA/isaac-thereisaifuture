## ADDED Requirements
### Requirement: Fresh actor input after optimization gaps
Gated live collection SHALL release input before optimization and reacquire a
fresh gated observation before the next rollout action. It MUST use the same
normalized observation in inference and rollout storage, with one normalization
update per actual reset/step and a recurrent episode-start boundary.
#### Scenario: Game advances while learner works
- **WHEN** optimizer/checkpoint work advances the native state between rollouts
- **THEN** the next actor input and diagnostic before frame use the reacquired state
- **AND** the previous rollout bootstrap remains unchanged
#### Scenario: Default and failure behavior
- **WHEN** generic synthetic training does not request the collection contract
- **THEN** its existing rollout/reset behavior remains unchanged
- **WHEN** release, gating, refresh or deadline checks fail
- **THEN** collection stops without an old-observation fallback action

### Requirement: Honest collection discontinuity
Collector gaps SHALL be logged with frame identity and elapsed time, without
invented actions, rewards, timesteps, terminal outcomes or progress. Existing
physical-room novelty and damage identity history MUST survive refresh resets.
#### Scenario: Damage or movement occurs while no action is collected
- **WHEN** a native state changes in an optimizer/checkpoint gap
- **THEN** reset establishes an unpaid baseline and records an unknown gap
- **AND** no sampled transition spans the gap or counts it as a death or clear
