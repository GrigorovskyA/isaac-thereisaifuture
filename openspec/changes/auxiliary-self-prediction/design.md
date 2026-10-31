## Context

`rollout-advantage-and-gpu-learner` (contract `5eb6f93a...`) made `learner.PureRecurrentPPO` the
pure learner: rollout-level advantages, batch 256, epoch-mean `target_kl`, `device: cuda`. Its
docstring reserved `train` for auxiliary losses. The extractor `policy.StructuredFeatures` (512
features) is shared by the actor and critic LSTMs (`share_features_extractor` True). The pure
doctrine allows predicting the agent's own observations and rewards; no hint, no reward term.

## Decision 1: feed-forward heads on the shared features

`auxiliary.AuxiliaryHeads` work on single transitions, so no LSTM state or sequence is replayed:

- latent (SPR, one step): `transition` = MLP(512 + 14 -> 512 -> 512) over features(s_t) and the
  one-hot action (5 + 5 + 4), then `projection` Linear(512, 128) and `predictor` Linear(128, 128).
  The target is `target_projection(target_extractor(s_t+1))`, deep copies of the extractor and
  projection updated by EMA (tau `target_ema` 0.99) after every auxiliary step, never by
  gradients. Loss 2 - 2 cos (normalized MSE), averaged over valid pairs only; a pair whose episode
  ended at t (any done) is masked out.
- reward: MLP(526 -> 128 -> 1), Huber loss against the reward scaled by the current VecNormalize
  return statistics (`normalize_reward`), the scale the learner sees.
- done: MLP(526 -> 128 -> 1), BCE against `terminated` = done and not `TimeLimit.truncated`
  (death or stall restart). A time limit is an episode end but not an outcome.

The three losses are summed with weight 1 (all are O(1) at the start). About 2.2 M auxiliary
parameters (half of them the EMA extractor).

## Decision 2: replay of raw rollouts

`PureRecurrentPPO.collect_rollouts` wraps upstream collection: a `RolloutRecorder` takes the raw
first observation (`VecNormalize.get_original_obs`) and, in `_update_info_buffer` (called once per
env step, after the step), the raw new observation (the reset observation after a done), the raw
reward, the done flag and the truncation flag. A complete rollout becomes a `RolloutRecord` of n
steps and n + 1 observations with the buffer's actions; an aborted one is dropped. `Replay` keeps
the last `replay_rollouts` records in a deque. Continuous features (1423) stay float32, the 10268
binary and one-hot features (`encoding.continuous_mask`) are float16, exact for 0 and 1: 26.9 MB
per 1024-step rollout, 215 MB for 8 (float32 would be 384 MB). Sampling draws transitions uniformly
with replacement from the global NumPy RNG (saved per checkpoint) and normalizes observations and
rewards with the current statistics, as the policy would see them now. The replay is never saved:
after a resume it starts empty and refills one rollout per update. One env only (`n_envs` 1 is
checked); the pure profile has one.

## Decision 3: a separate phase with its own Adam

After the PPO epochs (the game is still paused), `aux_steps` (64) steps on `aux_batch` (256)
replayed transitions train the extractor and the online heads. The Adam (eps 1e-5 as SB3) is
separate from the policy's: the PPO moment estimates never see auxiliary gradients, and the
policy optimizer keeps the parameter groups that frozen evaluation and `RecurrentPPO.load` expect.
With a separate Adam a constant loss weight cancels out (Adam is invariant to gradient scale), so
`aux_coef` scales the phase's step size: lr = `aux_coef` x the current PPO learning rate; 0 skips
the phase. Gradients are clipped to `max_grad_norm`.

The auxiliary losses are not added to the PPO epochs. That would need the heads in the policy
optimizer (changing the saved optimizer layout) and would mix their gradients into the PPO step
that `target_kl` judges. The phase alone already gives 64 replayed steps per rollout next to the
40 PPO steps; in-epoch losses stay a later option.

A distillation term on policy outputs is not possible feed-forward (the policy needs the LSTM
state), so drift is bounded by the step size and measured: before and after the phase the policy
log-probabilities of the current rollout's actions are computed in buffer order (same sequences
and padding as `buffer.get`, without its random rotation) and `aux_approx_kl` = mean((r - 1) -
log r) is logged. The next rollout is collected with the policy after the phase, and its PPO
ratios start from there, so drift never corrupts the clipped objective; it only moves the policy.
If `aux_approx_kl` rivals `approx_kl` natively, lower `aux_coef` (a hyperparameter, no new
lineage).

## Decision 4: checkpoints and contract

The auxiliary state (heads, EMA target, auxiliary Adam; `format` 1) is saved by
`AuxiliaryLearner.save` as `auxiliary.pt` beside `model.zip`, hashed in the manifest
(`auxiliary_file`, `auxiliary_sha256`, validated like the novelty counts). `PureRecurrentPPO`
excludes it from the model file (`_excluded_save_params`), so `model.zip` stays loadable by plain
RecurrentPPO and `CheckpointPolicy` ignores the auxiliary file. The hyperparameters are plain model
attributes, saved in the zip and overridden on resume through `custom_objects`. Resume
(`training._restore_auxiliary`) refuses a model whose `auxiliary` differs from the contract and a
checkpoint without the auxiliary file, then loads it onto the contract device
(`torch.load(..., weights_only=True, map_location=device)`). About 26 MB per checkpoint.

`contract.auxiliary: Literal["none", "spr_reward_done_v1"] = "none"`; an absent field keeps the
earlier contract hashes (`5eb6f93a...` is the shipped contract without the field). The five
hyperparameters are not hashed; version 1 configs never receive them.

## Update time (this Mac, CPU)

One train call = 1024 steps, batch 256, 10 epochs (`target_kl` off), LSTM 256, structured
features, synthetic sparse binary observations of size 11691, episodes of 170-220 steps, 8 torch
threads; script `bench_update_aux.py` (adapted from the rollout-advantage benchmark):

| Setup | Seconds per train call | Of which auxiliary phase | Peak RSS |
| --- | --- | --- | --- |
| `auxiliary: none` (2 calls) | 30.3-33.3 | - | 602 MB |
| `spr_reward_done_v1`, 64 x 256 (3 calls) | 63.1-64.8 | 31.4-31.6 | 653 MB (3 rollouts) |

The phase costs about as much as the 40 PPO steps on the CPU and doubles the update there, so the
Mac is above the 60 s target. The extractor dominates both; on the RTX 4070 the PPO update is
expected to be several times faster, and the phase (no LSTM, no padding) more so. The GPU time is
not measured; `update_seconds` and `aux_seconds` in `train.csv` of the first native hour will show
it, and `aux_steps` can be lowered without a new lineage. On the synthetic data `aux_approx_kl` was
0.005 after the first phase and below 5e-5 after the next two, against `approx_kl` 0.008-0.010.
With 8 full rollouts the replay adds about 215 MB (3 rollouts: 81 MB measured).

## Lineage

The contract gains `auxiliary: spr_reward_done_v1`, so the hash changes to
`0399c37db311f00df37cea79a66385ff6cd7150dfcfa0c9e3e46415f577da79a`. The rollout-advantage contract
never trained natively, so no run is renamed for it; `pure-v4` restarts with `--initialize`.

## Risks

- Only native Windows can verify: the phase time on the GPU, GPU memory of the EMA extractor and
  batches next to the game, the learner RAM with a full replay, and that `aux_approx_kl` stays
  small against `approx_kl` with real observations.
- Representation drift: the phase moves the features both LSTMs read; with `aux_coef` 1 it could
  slow PPO or raise the value loss. Watch `explained_variance` and `aux_approx_kl`.
- SPR without augmentation or multi-step targets can collapse to constant features; the reward and
  done heads anchor the features, and `aux_latent_loss` near 0 with rising value loss would show it.
- The done target is rare (about one step in 200); its loss is dominated by negatives.
- After each resume the replay is empty, so the first updates of a session replay only their own
  rollouts.
