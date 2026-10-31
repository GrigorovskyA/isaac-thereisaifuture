## Why

Rewards v9 to v12 all plateaued at about 2 rooms per episode, and the learner fixes of
`full-batch-structured-learner` and `rollout-advantage-and-gpu-learner` repair how PPO uses a
rollout, not how much it learns from it. PPO uses each step for about ten gradient steps and then
drops it, and the learner idles while the game plays. Self-supervised auxiliary losses gave large
sample-efficiency gains on Atari100k (SPR, Schwarzer et al. 2020, arXiv 2007.05929), and PPG
(Cobbe et al. 2020, arXiv 2009.04416) shows that reusing samples for the representation helps on
Procgen. Predicting the agent's own next observation, reward and episode end is allowed by the
pure doctrine (`docs/UPDATE_DECISION.md`): it is no hint and no reward term.

## What Changes

- `auxiliary.py`: heads on the shared structured features (the extractor output in front of
  both LSTMs), feed-forward over single transitions: a transition MLP from features(s_t) and the
  one-hot action (5 + 5 + 4) predicts the projection of features(s_t+1) of an EMA target copy of
  the extractor and projection (tau 0.99, stop-gradient, loss 2 - 2 cos, pairs across an episode
  end skipped); a reward head predicts the VecNormalize-scaled reward (Huber); a done head
  predicts the terminal outcome (death or stall restart, BCE).
- A replay of the last `replay_rollouts` (8) rollouts with raw observations (continuous float32,
  binary and one-hot float16), actions, raw rewards and episode ends, normalized with the
  current statistics when sampled. In memory only; it starts empty after a resume.
- `learner.PureRecurrentPPO`: records each complete rollout into the replay and, after the PPO
  epochs, runs `aux_steps` (64) Adam steps on `aux_batch` (256) uniformly sampled transitions,
  training only the extractor and the heads with their own Adam at `aux_coef` (1.0) x the PPO
  learning rate. It logs the three losses, the approximate KL of the policy on the current
  rollout before vs after the phase, and the phase seconds.
- Contract field `auxiliary: none | spr_reward_done_v1` (hashed; absent means `none`, so the
  earlier contracts keep their hashes). Hyperparameters `aux_coef`, `aux_steps`, `aux_batch`,
  `replay_rollouts`, `target_ema` (not hashed).
- Checkpoints save heads, EMA target and the auxiliary Adam as `auxiliary.pt` (hashed in the
  manifest, `auxiliary_file`); resume restores it and refuses a checkpoint without it. The model
  file is unchanged, so frozen evaluation (`CheckpointPolicy`) loads the policy and never reads the
  auxiliary file.
- `train.csv` gains `aux_latent_loss`, `aux_reward_loss`, `aux_done_loss`, `aux_approx_kl` and
  `aux_seconds` (empty without auxiliary losses); older files are upgraded once.
- `configs/training-pure-v4.yaml`: `auxiliary: spr_reward_done_v1`, device cuda, batch 256 and
  rollout advantages unchanged. New contract hash
  `0399c37db311f00df37cea79a66385ff6cd7150dfcfa0c9e3e46415f577da79a`; `pure-v4` restarts.
- `scripts/smoke_rl.py` runs the auxiliary phase on the CPU and reloads its state.

## Non-goals

- No reward, observation, action or Lua change; reward v12 and schema 9 stay.
- No intrinsic reward from the auxiliary losses (a separate later change).
- No PPG value or policy distillation over recurrent sequences; no auxiliary loss inside the
  PPO epochs (the phase alone, see design).
- No multi-step SPR, augmentation or LSTM in the auxiliary heads; one env only.
- The replay is not saved with checkpoints.

## Acceptance

- Offline gate (`scripts/check.sh` with the two known macOS-only failures / `Check.ps1`),
  `scripts/smoke_rl.py` and strict OpenSpec validation pass.
- Tests show: head shapes; the EMA update; the replay bound and that no latent pair crosses an
  episode end; the recorded raw rollout matches the rollout buffer; the phase lowers its losses
  on a tiny synthetic task; a tiny `aux_coef` leaves the policy unchanged while a large one shows
  in `aux_approx_kl`; checkpoint save and resume restore the auxiliary state and refuse a
  checkpoint without it; frozen evaluation loads; the contract refuses the earlier lineage;
  `train.csv` has the new columns.
- One train call (1024 steps, batch 256, 10 epochs and the phase) measured on the Mac CPU; on the
  Windows GPU `update_seconds` stays well under 60 s.
- Native: `aux_approx_kl` stays well below `approx_kl` in the first hour; after 150k steps rooms
  per episode and the share of episodes with 3+ rooms exceed those of the earlier runs at equal
  steps.

## Impact

- `src/isaac_threrisaifuture/{auxiliary,learner,training,checkpoints,training_metrics}.py`,
  `configs/training-pure-v4.yaml`, `scripts/smoke_rl.py`, tests, docs.
- Lineage `pure-v4` restarts with `--initialize`; checkpoints get about 26 MB more
  (`auxiliary.pt`); the learner process holds about 215 MB more RAM for the replay.
