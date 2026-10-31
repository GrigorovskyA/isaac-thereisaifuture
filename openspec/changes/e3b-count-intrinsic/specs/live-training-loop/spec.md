## ADDED Requirements

### Requirement: E3B bonus times the cross-run count
With contract `intrinsic: e3b_count_v1` the pure training SHALL add to each training step's reward
r_int = `e3b_beta` x clip(b_t / std(b) x max(1 / sqrt(N), `e3b_floor`), 0, 1): b_t is the episodic
E3B bonus phi(s_t+1)^T C_t^-1 phi(s_t+1) (C_0 = `e3b_lambda` I, reset at each episode start),
std(b) its running std, and N the cross-run count of the cell of s_t+1. N MUST be read without
counting it, and the reward v12 terms MUST NOT change.

#### Scenario: Repeated state and new episode
- **WHEN** the same observation follows itself within an episode
- **THEN** each b_t is smaller than the one before, and after a new episode starts the first b
  equals the first b of the earlier episode

#### Scenario: Sherman-Morrison
- **WHEN** 40 random embeddings enter the bonus
- **THEN** each b_t and the kept inverse match the direct inverse of lambda I plus the earlier
  outer products

#### Scenario: Count factor and floor
- **WHEN** the same episodic term is paid with N = 1, 4 and 400 and a floor of 0.1
- **THEN** the paid bonus scales as 1, 0.5 and 0.1, a step without a key pays the floor share, and
  r_int never exceeds `e3b_beta`

### Requirement: E3B embedding and inverse dynamics
The embedding SHALL be a separate copy of the structured extractor followed by a linear layer to
`e3b_embed_dim`, with its own weights, reading the raw observation with the stall clock and the
visited-cell grid zeroed. An inverse-dynamics head SHALL predict each action head from phi(s_t)
and phi(s_t+1) and SHALL train after the PPO epochs on replayed pairs of one episode only.

#### Scenario: Excluded blocks
- **WHEN** two observations differ only in the stall clock and the visited-cell grid
- **THEN** their embeddings are equal, while a change of the player position changes it

#### Scenario: Tiny task
- **WHEN** the inverse dynamics trains on pairs whose change follows from the action
- **THEN** its loss falls below half of the starting loss

#### Scenario: Shared replay
- **WHEN** auxiliary losses are on
- **THEN** the E3B phase samples the auxiliary replay; without them it keeps its own replay

### Requirement: E3B bonus is auditable and training only
The env SHALL pay r_int as its own reward component `e3b`, and `episodes.csv` SHALL record its
per-episode sum as `col_e3b` (empty without the bonus); `train.csv` SHALL record `e3b_idm_loss`,
`e3b_bonus_mean` and `e3b_seconds`. Frozen evaluation MUST NOT pay the bonus.

#### Scenario: Column sums
- **WHEN** an episode with the bonus ends
- **THEN** `col_e3b` is the sum of its step bonuses and all columns sum to the episode return

#### Scenario: Frozen evaluation
- **WHEN** a bonus is set on an env whose novelty table is frozen
- **THEN** no step pays `e3b` and the bonus is never called

### Requirement: E3B state binds the lineage
`intrinsic` SHALL be part of the contract hash except for `none`, absent or explicit, which keeps
earlier hashes. Each checkpoint under `e3b_count_v1` SHALL save the embedding, the inverse
dynamics, their optimizer and the running std in its own hashed file, and resume SHALL restore
them; a checkpoint without that file MUST be refused.

#### Scenario: Shipped contract unchanged
- **WHEN** the shipped config is loaded without `intrinsic` or with `intrinsic: none`
- **THEN** its hash is `0399c37db311f00df37cea79a66385ff6cd7150dfcfa0c9e3e46415f577da79a` and its
  manifests record no `e3b_*` hyperparameters and no E3B file

#### Scenario: Round trip and refusal
- **WHEN** an E3B session checkpoints and the next session resumes
- **THEN** the restored weights and std equal the saved ones, and a manifest without the E3B file
  is refused
