## Context

Reward v12 / schema 9 ran to t173056 (1032 episodes) and, like v9 to v11, plateaued at about 2
rooms per episode with 7-12% of the episodes reaching 3+ rooms. The returns rank rooms
correctly (1: -9.9, 2: +3.7, 3: +16.1, 4+: +41.2), so a learner that fits them should prefer
more rooms. Movement entropy stays at 1.52-1.57 of 1.61 and the use head drifts toward uniform.

## Evidence in the library (sb3-contrib 2.9)

- `RecurrentRolloutBuffer.get` (`common/recurrent/buffers.py` 184-198) does not shuffle: it
  rotates the indices once at a random split and yields contiguous slices. With one env,
  `batch_size` 128 and episodes of 170-220 steps every minibatch is a piece of one episode.
- `RecurrentPPO.train` normalizes advantages per minibatch (`ppo_recurrent.py` 355-356). Inside
  one episode that removes the between-episode signal (a 3-room episode against a 1-room one)
  that the return ranking carries.
- Sequences are cut at minibatch borders, so BPTT never sees more than 128 steps.
- `target_kl` stops all epochs at the first minibatch over 1.5 * target_kl (406-410). Noisy
  128-step minibatches tripped it after 2-3.5 of 10 epochs. With batch 256 and 4 epochs (v9, v10)
  explained variance was 0.7-0.88; with batch 128 it is 0.43.

## Decision 1: one full-rollout minibatch per epoch

`batch_size` = `n_steps` = 1024. Each epoch is one gradient step over the whole rollout: the
advantage normalization spans all its episodes, each episode inside the rollout is one sequence
(BPTT over the whole episode), and `target_kl` judges the whole rollout. Ten epochs give ten
gradient steps per rollout, against 16-28 before (80 nominal, cut by
`target_kl`), but every step uses all data. `target_kl` 0.03 stays as the safety stop. The
rollout rotation still happens; with one minibatch it only moves the sequence borders by one cut.

The buffer pads every sequence to the longest one in the minibatch. With 5-7 episodes per rollout
the padded batch is about 1300-3000 rows of 11691 floats (60-140 MB), fine on CPU.

## Decision 2: normalize continuous features only

`encoding.FEATURE_BLOCKS` lists every index as `continuous`, `binary` or `one_hot`; it is built
from the same constants as `encode` and asserts its anchors (`INVENTORY_OFFSET`, `ROOM_OFFSET`,
every `ENTITY_OFFSETS[kind]`, `COLLECTIBLE_OFFSET`, `MAP_OFFSET`, `STALL_OFFSET`,
`VISITED_OFFSET`, `OBSERVATION_SIZE`). 1423 of 11691 indices are continuous (positions,
velocities, hearts, counters, HP fractions, stage, stats, quality, charges, bomb age, held-tag
counts, stall clock). The mask is never guessed from data; a test encodes rich synthetic frames
and checks that no binary or one-hot index ever holds a value other than 0 or 1 and that one-hot
groups sum to at most 1.

`ContinuousVecNormalize` overrides `_normalize_obs` / `_unnormalize_obs` with
`np.where(mask, VecNormalize result, obs)`. Running statistics still cover all indices, so the
saved state keeps its shape and `CheckpointPolicy` validation applies unchanged. The class is
pickled by module path into `vecnormalize.pkl`; the manifest and its hashes are unchanged.
`check_continuous_only` refuses a plain VecNormalize or a mask that differs from the current
layout on resume, and `CheckpointPolicy(observation_normalization="continuous_only")` (used by
`eval-live`) does the same. Reward normalization is unchanged.

## Decision 3: structured features

`StructuredFeatures` (contract `policy_features: structured_v1`), shared by actor and critic:

| Part | Input | Layers | Output |
| --- | --- | --- | --- |
| Entity kinds (7) | slots x slot width (enemy 32 x 78, projectile 64 x 8, obstacle 64 x 24, pickup 24 x 99, own attack 48 x 8, bomb 8 x 9, interactable 16 x 16) | per-slot Linear(width, 64) ReLU Linear(64, 64) ReLU, masked by the present bit | mean and max over present slots (0 when empty) + present fraction: 7 x 129 |
| Minimap | 13 x 13 cells x 14 channels | Conv 3x3 32, Conv 3x3 stride 2 32, Linear(1568, 128) | 128 |
| Visited cells | 14 x 26 x 1 | Conv 3x3 16, Conv 3x3 stride 2 16, Linear(1456, 64) | 64 |
| Scalars | 1329 other indices (player, inventory, room and the 8 door slots, collectibles bitmap, stats, tear flags, weapons, held tags, off-grid, stall) | Linear(1329, 256) ReLU | 256 |
| Head | 1351 | Linear(1351, 512) ReLU | 512 into both LSTMs |

Doors stay in the scalar MLP: their slot is the door direction, so pooling them would lose
meaning. The present bit is read after normalization, which is why Decision 2 is a precondition:
it must still be exactly 0 or 1. Pooling over present slots makes the output independent of the
slot order; the present fraction keeps the count that mean pooling loses. SB3's orthogonal
initialisation (gain sqrt 2) applies to the Linear and Conv layers. The extractor has 1,387,632
parameters (the input projection had 5,986,304); the whole policy has 3,006,783 (7,605,455
before). `apply_use_head_prior` only touches `action_net` and still holds.

## Update time (this Mac, CPU, 8 torch threads)

One update = 1024 steps, 10 epochs, LSTM 256, `target_kl` off so all epochs run, synthetic
sparse observations of size 11691:

| Setup | Episode lengths | Seconds per update | Peak RSS |
| --- | --- | --- | --- |
| Before: input projection, batch 128 | 170-220 | 17.0-17.5 | 525 MB |
| Input projection, batch 1024 | 170-220 | 6.4-6.8 | 702 MB |
| After: structured, batch 1024 | 170-220 | 17.7-19.5 | 938 MB |
| After: structured, batch 1024 | 20-700 (more padding) | 37.5-39.1 | 1184 MB |

All below the 60 s target. The Windows learner machine is not measured; `train.csv`
`update_seconds` will show it.

## Why not resume reward v12 schema 9

The normalized inputs and the network shape change, so neither the weights nor the statistics
carry over, and the contract hash changes (two new required fields). The run is kept as
`runs/pure-v4-reward-v12-schema9`; `pure-v4` restarts with `--initialize`.

## Risks

- Continuous features that are almost always 0 (coordinates of far entity slots, rare bombs)
  get tiny variances and would reach the clip of 10 when they first appear, which max pooling
  would carry. The normalizer therefore floors the running variance at 0.1 (`VARIANCE_FLOOR`):
  the encoder already scales continuous features to about [-1, 1], so such a value stays within
  about 3 standard units, while features with a larger spread are scaled as plain VecNormalize.
- Ten gradient steps per rollout may learn slower per sample than the earlier nominal 80; the
  acceptance compares at equal steps.
- Padding grows with the longest episode in a rollout; time and memory grow with it (see table).
