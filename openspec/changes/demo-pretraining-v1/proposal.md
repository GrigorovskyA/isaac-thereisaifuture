## Why

Every lineage so far learned from a random policy and outcome rewards only. The E3B lineage needed
273k steps (about 20 hours of play) to reach about 2 rooms and 1-2 kills per episode; reward v13
at 23k steps still moves almost at random (1.3-1.6 rooms per episode). The policy already observes
the minimap, the doors and their targets, the visited cells and every entity, so the input is not
the bottleneck: the agent has to discover from scratch that doors lead on and that tears kill.

A few hours of human play show exactly that. Behaviour cloning from such demos gives the policy a
reasonable starting behaviour (walk to doors, shoot at enemies, avoid projectiles), and RL then
improves on it instead of starting from button mashing.

## What Changes

- Observer capability `demo_record_v1` (read-only, no approval): together with
  `entity_observation_v1` only. Snapshots carry the live oracle block and `human_input`, one bit
  mask per game update of player 0's held buttons (move, shoot, bomb, active, pill/card) and the
  use buttons triggered on that update. The mod injects nothing in this mode.
- `demo_recorder.py` and `Record-Demo.cmd`: while the human plays, raw snapshots with their
  receipt time go to `runs/demos/<time>-<session>.jsonl.gz`, one file per mod session. The raw
  form keeps the recordings valid across encoder, reward and action changes: they are re-encoded
  offline, and a new game field is the only reason to record again.
- `demo_dataset.py`: recordings to behaviour cloning sequences at the agent's decision rate
  (`action_repeat_game_updates`), with observations built exactly as the live env builds them
  (stall clock replayed from the receipt times, visited cells at decision points). Labels: the
  most held move and shoot direction over the step's updates (a diagonal becomes its faster axis),
  and a use press when one was triggered. Cached next to each recording.
- Contract `pretraining: demo_bc_v1` (absent = `none`, older hashes unchanged) with a
  `demo` config section (not hashed): a fresh lineage first fits the observation normalizer on the
  demos and trains the actor by behaviour cloning (`pretrain_steps`), writes
  `pretraining.json` and a checkpoint at step 0, then runs RL. During RL, a BC regulariser
  (`bc_steps` per update, step size `bc_coef` times the PPO learning rate, linear decay to 0 at
  `bc_decay_timesteps`) keeps the demo skill while the critic learns.
- The shipped config starts the new lineage with `pretraining: demo_bc_v1` over `runs/demos`.
  Training refuses to start with fewer than `demo.min_steps` demo steps.

## Non-goals

- No change to observations, actions or the reward; the policy never sees `human_input`.
- No diagonal movement action: the 5-way move head stays (a later action schema can re-label the
  same recordings from the raw masks).
- No offline RL or value pretraining from demo returns; the critic learns online.
- No recording while training runs (one game, one port).
