## Why

Local timing and the native `update_seconds` column show that the optimizer pause is large
and that the game keeps running during it.

- `train.csv` `update_seconds` (the gap between two rollouts: optimizer and checkpoint)
  has median 11.7 s on the reward-v7 lineage, 20.0 s on v8 and 25.3 s (p90 36 s) on v9 with
  observation size 3863 and `n_steps` 512. That is 17% of wall time.
- Isaac is not paused in that gap. It stands without input in a live room, so damage and
  deaths there are blamed on the first action of the next rollout.
- One `train()` call on CPU (RecurrentPPO, MultiDiscrete [5, 5, 4], LSTM 256, `n_epochs` 4,
  synthetic episodes of 170 steps, 4 torch threads):

  | Observation | n_steps | Policy | Seconds |
  | --- | --- | --- | --- |
  | 3863 | 512, batch 128 | default | 12.4 |
  | 7522 (next schema) | 1024, batch 128 | default | 54.7 |
  | 7522 | 1024, batch 256 | default | 50.5 |
  | 7522 | 1024 | default, no critic LSTM | 24.5 |
  | 7522 | 1024, batch 128 | `Linear(obs, 512)` + ReLU before the LSTMs | 7.1 |
  | 7522 | 1024, batch 256 | same | 6.7 |

  The cost is the LSTM input projection applied to the full observation over padded
  sequences. The projection cuts parameters from 16.0M to 5.5M.

## What Changes

- Policy: a features extractor `Linear(obs_dim, features_dim)` + ReLU, shared by actor and
  critic, in front of the unchanged actor and critic LSTMs (`lstm_hidden_size` 256).
  `features_dim` 512 sits in the hashed `contract` section of
  `configs/training-pure-v4.yaml`, so it binds the lineage (new contract hash; older
  checkpoints are refused). One helper (`policy.py`) builds the policy kwargs for fresh
  models; resume, frozen evaluation and the checkpoint policy load the saved architecture.
- Hyperparameters (not hashed): `n_steps` 1024 (was 512) and `batch_size` 256 (was 128):
  fewer, cheaper updates, about one per four minutes of play. Other values are unchanged.
- Pause the game during each optimizer update, live backend only. At rollout end the learner
  releases held input, presses Esc through the guarded Windows keyboard of the worker
  (`windows_menu.py`, same focus guard as menu entry) and waits up to 3 s for a `paused`
  snapshot. At the next rollout start it presses Esc again and waits for an `active`
  snapshot. The snapshots read meanwhile go to a backlog that the next step absorbs in order,
  so paused time adds no stall or stagnation time and the first command uses a fresh frame.
  A flag `live.pause_during_updates` (not hashed) switches it on; sim and fake backends do
  nothing.
- Failures never fault the session: an already paused game, a game that is not active,
  missing or unfocused window, a failed key or a timeout is recorded once per occurrence as
  `update_pause_skipped` or `update_resume_failed` in `events.jsonl`, and training goes on.
- `metrics/train.csv` gains `pause_seconds` and `pause_ok`; older headers are upgraded.

## Capabilities

### Modified Capabilities

- `live-training-loop`

## Non-goals

- No reward, observation or action change.
- No change to the use-head prior, learning rate, `gamma`, `gae_lambda`, `ent_coef`,
  clip range or `n_epochs`.
- No pause for evaluation, random runs or the simulated backend.
- No new input device or key beyond Esc through the existing guarded path.

## Acceptance

- Offline gate: `scripts/check.sh` and strict OpenSpec validation pass, including tests for
  the policy shape and lineage refusal, the pause ordering and failure paths, the backend
  backlog and the metrics columns.
- Native one hour on the new lineage: `update_seconds` median below 12 s at `n_steps` 1024,
  `pause_ok` share above 90%, no fault caused by pausing, and steps per hour not lower than
  the reward-v9 schema-7 run (about 15k per hour, less the paused time).

## Impact

`src/isaac_threrisaifuture/{policy,update_pause,training,training_metrics,live,session_runner}.py`,
`configs/training-pure-v4.yaml`, `scripts/smoke_rl.py`, `docs/RL_DESIGN.md`,
`docs/LIVE_LOOP.md`, `docs/ARCHITECTURE.md` and tests. The lineage restarts from scratch.
