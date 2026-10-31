## ADDED Requirements

### Requirement: Rollout-level advantage normalization
With contract `advantage_normalization: rollout` the pure profile SHALL train with a RecurrentPPO
learner that normalizes the advantages once per rollout, by the mean and standard deviation over
every step of the rollout buffer, after the returns are computed, and MUST NOT normalize them
again per minibatch. Fresh training and resume SHALL use this learner; the value targets MUST
NOT change.

#### Scenario: Several minibatches per epoch
- **WHEN** one rollout of 64 steps is learned with `batch_size` 16 and two epochs
- **THEN** the advantages are normalized exactly once
- **AND** the unpadded advantages of one epoch's four minibatches have mean 0 and standard
  deviation 1 together, while single minibatches keep their own offsets

#### Scenario: Resume
- **WHEN** a session resumes from a checkpoint of this lineage
- **THEN** its updates use the same rollout-level normalization

### Requirement: Several minibatches per epoch
The pure training profile SHALL use `n_steps` 1024 and `batch_size` 256, so that each epoch
makes four gradient steps over rollout-normalized advantages; `load_training_config` MUST keep
refusing a `batch_size` greater than `n_steps`.

#### Scenario: Shipped configuration
- **WHEN** `configs/training-pure-v4.yaml` is loaded
- **THEN** `n_steps` is 1024, `batch_size` 256, `n_epochs` 10 and `target_kl` 0.03

### Requirement: Epoch-mean KL early stop
With `target_kl` set the learner SHALL complete every minibatch of an epoch and then stop the
remaining epochs when the mean approximate KL measured over that epoch's minibatches exceeds 1.5
times `target_kl`; a single minibatch over the limit MUST NOT end the update inside an epoch.

#### Scenario: Tiny limit
- **WHEN** an update with four minibatches per epoch and three epochs has a tiny `target_kl`
- **THEN** exactly one epoch runs and all four of its minibatches take an optimizer step

#### Scenario: No limit
- **WHEN** `target_kl` is unset or large
- **THEN** all epochs run

### Requirement: Configured learner device without fallback
`contract.device` SHALL accept `cpu` and `cuda`, and the pure profile SHALL build and resume its
model on that device. A `cuda` contract MUST be refused with an error that names the missing
CUDA when torch cannot use a GPU, before any environment or model is created, and the forever
supervisor MUST refuse it before any session starts; training MUST NOT fall back to the CPU.
Observation normalization stays on the CPU.

#### Scenario: No CUDA
- **WHEN** the contract says `cuda` and `torch.cuda.is_available()` is false
- **THEN** `train` raises a configuration error and no environment is built
- **AND** the forever supervisor stops with `config refused` and runs no session

### Requirement: Checkpoints load on any device
A checkpoint saved by the learner on one device SHALL load for resume on the contract's device
and for frozen evaluation on the CPU, with the saved tensors mapped onto the loading device.

#### Scenario: CPU round trip
- **WHEN** a model of the rollout-normalizing learner is saved and loaded by that learner and by
  plain RecurrentPPO on the CPU
- **THEN** both have the same weights and predict the same action

#### Scenario: GPU to CPU
- **WHEN** the RL smoke test runs on a machine with CUDA
- **THEN** a model trained on the GPU is saved, loaded on the CPU and predicts a valid action

### Requirement: Advantage normalization and device bind the lineage
`advantage_normalization` MUST be a required field of the hashed contract, and `device` MUST be
hashed with it, so that a configuration or checkpoint of the full-batch structured contract is
refused.

#### Scenario: Earlier contract
- **WHEN** a configuration lacks `advantage_normalization` or names another value or device
- **THEN** it is refused, and the full-batch structured contract hash differs from the current one
