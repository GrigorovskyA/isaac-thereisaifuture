## Context

The live loop (`live.py`) drives the game through the observer mod: the mod sends a snapshot every
50 ms, the agent decides every `action_repeat_game_updates` (6) game updates and the mod injects the
held action through `MC_INPUT_ACTION`. With no hold, that callback returns nil and the game reads
the real input, so the mod can observe a human player with the same snapshot pipeline.

## Decisions

### Record raw snapshots, derive everything offline
The recorder stores validated `DemoSnapshot` JSON with the receipt time, not encoded vectors.
Observations (encoder version, visited cells, stall clock) and labels (action schema, decision
rate) are derived later and cached per recording and derivation key. Recordings survive changes of
the encoder, the reward and the action mapping; only a field the mod did not send needs new
recordings.

### Input masks per game update
Lua samples `Input.IsActionPressed` (11 buttons) and `Input.IsActionTriggered` (bomb, active,
pill/card) for player 0's controller in `MC_POST_UPDATE` and sends the masks since the previous
snapshot (at most 16, older ones counted as dropped). The last mask belongs to the snapshot frame,
so every update gets its own mask without a separate clock.

### Labels
A decision at frame F is labelled from the masks of frames F+1..F+repeat, the updates its action
would cover. Move and shoot take the most held direction; a diagonal (two move axes held equally)
becomes the axis the player moves faster along. Use takes a triggered press (bomb before active
before pill/card). A window with more than half of its masks missing splits the sequence.

### Same observations as live
The dataset replays `EventDeriver`, `RunProgress` and `StallWatchdog` (clock = receipt time, calm
limit from the reward contract) over all snapshots, and `VisitedCells` at decision points only,
exactly like `LiveBackend` and `IsaacCombatEnv`. A test feeds one synthetic snapshot stream through
both paths and compares the vectors. Observations are stored as float16 (12 KB per step instead of
47 KB; error below 1e-3, binary features exact).

### Behaviour cloning, then RL with a decaying regulariser
Fresh lineage only: fit the continuous-only normalizer on the demo observations, then train the
policy (features extractor, actor LSTM, action heads) on the masked NLL of the demo actions over
windows of `seq_len` steps from zero LSTM states. The value head is not pretrained. PPO with an
untrained critic would wash the cloned behaviour out within a few updates, so after each update a
BC phase (own Adam, `bc_steps` steps at `bc_coef` times the PPO learning rate) pulls the policy
back to the demos; its weight decays linearly to 0 at `bc_decay_timesteps`. Its KL on the rollout
is logged like the auxiliary phase's. The BC Adam state is not checkpointed; it restarts each
session, as the replay of the auxiliary phase does.

### Lineage
`pretraining: demo_bc_v1` is a contract field (a cloned start is a different lineage); `none` is
left out of the hash. The demo section is configuration recorded in each manifest: more recordings
can be added between sessions without a new lineage (they only change the regulariser data).

## Risks

- Human play differs from what the 5-way move head can do (diagonals), and the human reacts with
  about 200 ms delay; BC accuracy is bounded by both.
- A few hours of demos cover the first floors only; RL has to extend the behaviour.
- `Input.IsActionPressed` with the player's `ControllerIndex` is assumed to report keyboard and
  controller input alike; this is verified only in the native recording smoke test.
