## ADDED Requirements

### Requirement: One full-rollout minibatch per epoch
The pure training profile SHALL use `batch_size` equal to `n_steps`, so that each optimizer epoch
is one minibatch over the whole rollout: advantages are normalized over the whole rollout and
every episode inside the rollout is one recurrent sequence. `load_training_config` MUST keep
refusing a `batch_size` greater than `n_steps`.

#### Scenario: Shipped configuration
- **WHEN** `configs/training-pure-v4.yaml` is loaded
- **THEN** `n_steps` and `batch_size` are both 1024, with `n_epochs` 10 and `target_kl` 0.03

#### Scenario: Full-batch learn step
- **WHEN** RecurrentPPO learns one rollout with `batch_size` equal to `n_steps` and two epochs
- **THEN** the rollout buffer yields exactly one minibatch of all steps per epoch

### Requirement: Continuous-only observation normalization
With contract `observation_normalization: continuous_only` the pure profile SHALL normalize and
clip only the observation indices whose kind is `continuous` in the encoder's feature table;
binary and one-hot features MUST reach the policy unchanged. Training, resume, frozen evaluation
and the RL smoke test SHALL use the same normalizer class, saved as `vecnormalize.pkl`.

#### Scenario: Rare bit
- **WHEN** a binary feature that was 0 in all earlier observations is set
- **THEN** the policy input at that index is exactly 1.0
- **AND** continuous features are normalized as VecNormalize does

#### Scenario: Save and load
- **WHEN** a continuous-only normalizer is saved and loaded
- **THEN** it keeps its class and mask and gives the same output

### Requirement: Saved normalizer matches the contract
Resume and frozen evaluation under `observation_normalization: continuous_only` MUST refuse a
saved normalizer of another class or with a feature mask that differs from the current layout.

#### Scenario: Plain normalizer
- **WHEN** a checkpoint's normalizer is a plain VecNormalize or has a stale mask
- **THEN** resume and frozen evaluation refuse it with a checkpoint error

### Requirement: Structured policy features
With contract `policy_features: structured_v1` the pure profile SHALL build one features
extractor shared by actor and critic: per entity kind one MLP shared by all slots, masked by the
present bit and pooled by mean and max over present slots plus the present fraction; CNNs over
the minimap and the visited-cell grid; an MLP over the other features; and a final Linear to
`features_dim` with ReLU. The use-head initial prior SHALL still apply.

#### Scenario: Slot order
- **WHEN** the slots of an entity kind are permuted, present ones included
- **THEN** the extractor output is unchanged

#### Scenario: Empty kinds
- **WHEN** no entity of any kind is present
- **THEN** the output and its gradients are finite

### Requirement: Learner fields bind the lineage
`policy_features` and `observation_normalization` MUST be required fields of the hashed
contract, so that a configuration or checkpoint of the earlier contract is refused.

#### Scenario: Earlier contract
- **WHEN** a configuration lacks `policy_features` or `observation_normalization`
- **THEN** it is refused, and its contract hash differs from the current one
