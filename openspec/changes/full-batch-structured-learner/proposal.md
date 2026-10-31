## Why

Rewards v9 to v12 all plateau at about 2 rooms per episode: 7-12% of the episodes reach 3+ rooms
and the slope is about 0 after 75k steps, although the returns rank rooms correctly (1 room -9.9,
2 rooms +3.7, 3 rooms +16.1, 4+ rooms +41.2). The last run (reward v12, schema 9, `runs/pure-v4`,
report `reports/2026-10-31-reward-v12-schema9-training.md`) was stopped by the human at t173056.
Movement entropy stays at 1.52-1.57 of 1.61 (near random). The reward is not the bottleneck; the
learner is:

1. sb3-contrib does not shuffle recurrent minibatches. With batch 128 and episodes of 170-220
   steps each minibatch is part of one episode, so the per-minibatch advantage normalization
   erases the differences between episodes, BPTT is capped at 128 steps and `target_kl` stops
   the update after 2-3.5 of 10 epochs. Explained variance fell to 0.43 (0.7-0.88 with batch 256).
2. VecNormalize centres and scales binary and one-hot features: a rare bit (new minimap cell,
   rare room class, item bucket) jumps to about +10 on first appearance, exactly in the new
   layouts beyond room 2.
3. One `Linear(11691, 512)` gives every minimap cell and entity slot its own weights, so what is
   learned about an enemy or a cell must be learned again in every position.

## What Changes

- `configs/training-pure-v4.yaml`: `batch_size` 1024 (= `n_steps`); `n_epochs` 10,
  `target_kl` 0.03, learning rate, entropy, gamma and lambda unchanged.
- `encoding.py`: `FEATURE_BLOCKS`, an explicit table of every observation index as
  `continuous`, `binary` or `one_hot`, built from the layout constants and asserted against
  them; `continuous_mask()`; `ENTITY_OFFSETS`.
- `normalization.py`: `ContinuousVecNormalize`, a VecNormalize subclass that normalizes and
  clips only the continuous indices; binary and one-hot features pass through unchanged. Saved
  as `vecnormalize.pkl` like before; `check_continuous_only` refuses a plain or stale normalizer
  on resume and frozen evaluation.
- `policy.py`: `StructuredFeatures`, one MLP per entity kind shared by its slots with masked mean
  and max pooling and the present fraction, a CNN over the 13 x 13 x 14 minimap, a CNN over the
  14 x 26 visited-cell grid, an MLP over the other features, then Linear -> `features_dim` 512 +
  ReLU, shared by actor and critic. `InputProjection` stays loadable.
- Contract: `policy_features: structured_v1` and `observation_normalization: continuous_only`
  (both required), new contract hash `ee4f65999d3a8cf0c85dabd5d887e360fd0823a164814bd20753d6dca91ac703`.
  The reward v12 schema 9 run is kept as `runs/pure-v4-reward-v12-schema9`; its checkpoints are
  refused. `pure-v4` restarts with `--initialize`.
- Training, resume, frozen evaluation (`CheckpointPolicy`, `eval-live`) and `scripts/smoke_rl.py`
  use the same normalizer and extractor.

## Non-goals

- No reward change (v12 stays), no RND, no observation content or schema change (schema 9 stays).
- No Lua, action or hint change; nothing scripted.
- No change of `n_steps`, `n_epochs`, `target_kl`, learning rate or entropy coefficient.

## Acceptance

- Offline gate (`scripts/check.sh` / `Check.ps1`), `scripts/smoke_rl.py` and strict OpenSpec
  validation pass.
- One full update (1024 steps, 10 epochs, LSTM 256) stays below about 60 s on CPU.
- Native run of 150k steps against the reward v12 schema 9 run at equal steps, from
  `episodes.csv` and `train.csv`: explained variance above 0.6, rooms per episode above 2.3 and
  a rising share of episodes with 3+ rooms.

## Impact

- `src/isaac_threrisaifuture/{encoding,normalization,policy,training,checkpoint_policy,live}.py`,
  `configs/training-pure-v4.yaml`, `scripts/smoke_rl.py`, tests, docs.
- Lineage `pure-v4` restarts with `--initialize` (authorized; native evidence pending).
