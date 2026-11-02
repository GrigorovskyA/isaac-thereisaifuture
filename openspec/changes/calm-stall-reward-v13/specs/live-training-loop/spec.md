## ADDED Requirements

### Requirement: Use head entropy scale
The pure learner SHALL take a hyperparameter `use_entropy_scale` (>= 0, default 1.0, not part of
the contract hash, recorded per checkpoint) and use `H_move + H_shoot + use_entropy_scale * H_use`
as the entropy in the PPO loss. Values and log probabilities SHALL equal those of the policy's own
`evaluate_actions`. The shipped config SHALL set 0.2.

#### Scenario: Scaled entropy
- **WHEN** the learner evaluates a minibatch with `use_entropy_scale` 0.2
- **THEN** values and log probabilities equal the policy method's and the entropy is lower

#### Scenario: Upstream at scale 1
- **WHEN** `use_entropy_scale` is 1.0
- **THEN** the entropy equals the policy method's

### Requirement: Disk sampling tolerates retention
The forever supervisor's disk sampling SHALL count a file that is deleted between the directory
walk and its size query as zero bytes instead of failing the session.

#### Scenario: Pruned checkpoint
- **WHEN** retention deletes a checkpoint file while the supervisor sums the run's size
- **THEN** the sum skips that file and the session keeps running
