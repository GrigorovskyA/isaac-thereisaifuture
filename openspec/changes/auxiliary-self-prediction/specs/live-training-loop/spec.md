## ADDED Requirements

### Requirement: Auxiliary self-prediction phase
With contract `auxiliary: spr_reward_done_v1` the pure learner SHALL, after the PPO epochs of each
update, train only the shared features extractor and the auxiliary heads for `aux_steps`
optimizer steps on `aux_batch` transitions sampled uniformly from the replay, with a step size of
`aux_coef` times the current PPO learning rate; `aux_coef` 0 MUST skip the phase. The phase MUST
NOT change the reward, the observation or the action.

#### Scenario: One update
- **WHEN** a rollout is learned with auxiliary losses
- **THEN** the PPO epochs run as before, followed by the auxiliary phase
- **AND** the logged latent, reward and done losses and the phase seconds are finite

#### Scenario: Tiny task
- **WHEN** the phase trains on a replay whose rewards and endings follow from the action and the
  observation
- **THEN** the reward and done losses fall below half and the latent loss falls

#### Scenario: No auxiliary losses
- **WHEN** the contract has `auxiliary: none` or no `auxiliary` field
- **THEN** no replay is kept and no phase runs

### Requirement: Auxiliary prediction targets
The feed-forward auxiliary heads SHALL predict, from the features of s_t and the one-hot action,
the projected features of s_t+1 under an EMA target copy of the extractor and projection
(stop-gradient, rate `target_ema`), the VecNormalize-scaled reward of the step, and whether the
step ended the episode by an outcome (death or stall restart). A latent pair whose episode ended
at t MUST NOT count.

#### Scenario: Shapes and target
- **WHEN** the heads are built over 24 features and the action MultiDiscrete([5, 5, 4])
- **THEN** the one-hot action has 14 entries, the reward and done heads return one value per
  transition, and the EMA target starts equal to the extractor and receives no gradient

#### Scenario: Time limit
- **WHEN** a step ends its episode by a time limit
- **THEN** it is an episode end for the latent pair but not an outcome for the done head

### Requirement: Replay of recent rollouts
The learner SHALL keep the last `replay_rollouts` complete rollouts of its one env in memory with
raw observations, actions, raw rewards, episode ends and outcome flags, and SHALL normalize
observations and rewards with the current statistics when it samples them. The replay MUST NOT be
saved with checkpoints and SHALL start empty after a resume; an aborted rollout MUST NOT enter it.

#### Scenario: Bound
- **WHEN** three rollouts enter a replay of two
- **THEN** only the last two remain and samples come from them only

#### Scenario: Episode end
- **WHEN** a sampled step ended its episode
- **THEN** its latent pair is marked invalid, and every valid pair's next observation is the
  following step of the same episode

### Requirement: Policy drift of the auxiliary phase is logged
The learner SHALL measure the approximate KL of the policy on the current rollout's actions
before versus after the auxiliary phase and `train.csv` SHALL record it as `aux_approx_kl`,
together with `aux_latent_loss`, `aux_reward_loss`, `aux_done_loss` and `aux_seconds`, which stay
empty without auxiliary losses. A file with the previous header MUST be upgraded once.

#### Scenario: Tiny and large step size
- **WHEN** the phase runs with `aux_coef` 1e-9 and then with 100
- **THEN** the first leaves the action probabilities of a fixed batch unchanged within 1e-6 and
  its KL is below 1e-9, and the second shows a much larger KL

### Requirement: Auxiliary state in checkpoints
Each checkpoint of a lineage with auxiliary losses SHALL save the heads, the EMA target and the
auxiliary optimizer state in its own hashed file named by the manifest, and resume SHALL restore
them; a resume from a checkpoint without that file MUST be refused. The model file SHALL stay
loadable by plain RecurrentPPO, and frozen evaluation MUST NOT need the auxiliary file.

#### Scenario: Round trip
- **WHEN** a session checkpoints and the next session resumes
- **THEN** the restored heads and EMA target equal the saved ones and the replay is empty

#### Scenario: Frozen evaluation
- **WHEN** `CheckpointPolicy` loads such a checkpoint
- **THEN** it predicts valid actions, also after the auxiliary file is removed

### Requirement: Auxiliary losses bind the lineage
`auxiliary` SHALL be a field of the hashed contract with the values `none` and
`spr_reward_done_v1`; an absent field means `none` and keeps the earlier contract hashes. Its
hyperparameters (`aux_coef`, `aux_steps`, `aux_batch`, `replay_rollouts`, `target_ema`) MUST NOT
be hashed. The shipped profile SHALL use `spr_reward_done_v1` with device cuda, batch 256 and
rollout advantages, and MUST refuse checkpoints of the rollout-advantage contract.

#### Scenario: Shipped configuration
- **WHEN** `configs/training-pure-v4.yaml` is loaded
- **THEN** `auxiliary` is `spr_reward_done_v1`, `aux_coef` 1.0, `aux_steps` 64, `aux_batch` 256,
  `replay_rollouts` 8 and `target_ema` 0.99, and its hash differs from the rollout-advantage
  contract

#### Scenario: Earlier lineage
- **WHEN** a session with auxiliary losses resumes a checkpoint written without them
- **THEN** it is refused as a different training configuration
