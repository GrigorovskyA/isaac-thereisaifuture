## Context

Lineage `pure-v4` (contract `0399c37d...`: reward v12, schema 9, structured features, rollout
advantages, cuda, auxiliary self-prediction) trains on one real-time game at about 9 decisions per
second (about 111 ms per step). Reward v11/v12 already keep a cross-run table of first visits per
(stage, room, cell) (`novelty_counts.py`, saved per checkpoint). The auxiliary change keeps a
replay of the last 8 raw rollouts in memory.

## Decision 1: bonus in the env, embedding owned by the learner

phi(s_t+1) is needed at every env step, and the bonus must enter the reward before VecNormalize
scales it, before the rollout buffer stores it and before the episode summary sums the columns.
`IsaacCombatEnv.step` is the only place where all three hold, so the env calls the learner's
`E3BLearner.reward(obs, N)` right after it encodes the next observation; `reset` calls
`start_episode(obs)`, which resets C and adds phi(s_0) without pay. `train` attaches the learner to
the unwrapped training env (`_attach_e3b`) and refuses an env that is not an `IsaacCombatEnv` with
a ledger whose table is the one the checkpoints save. Evaluation builds its env with
`make_live_env` and never attaches anything; as a second guard the env pays only with a writable
(not frozen) table. SB3 runs the env in the learner's process and thread (DummyVecEnv), so the
learner and the env never use the networks at the same time.

## Decision 2: embedding input and weights

phi is `StructuredFeatures(features_dim=256)` plus Linear(256, `e3b_embed_dim`), built fresh with
its own weights; it never shares the policy extractor, so policy updates and the auxiliary phase
do not move the bonus. Its input is the raw encoder output (already in [-1, 1]), not the running
normalizer's output, so the bonus does not drift with normalizer statistics. `keep_mask()` zeroes
the blocks `stall` (idle clock over the stall limit) and `visited_cells` (the run's visited grid of
the room) from `FEATURE_BLOCKS`; both grow with time and would make every state unique (E3B
paper, section 5, the MiniHack time counter). Bomb ages stay: they are local entity facts that
exist only while a bomb is out, not a global clock. The minimap's visited flags stay as well: they
change only when a room is entered.

## Decision 3: bonus, normalization and combination

b_t = phi^T C_t^-1 phi with C^-1 updated by Sherman-Morrison, u = C^-1 phi, C^-1 -= u u^T /
(1 + b), in float64 NumPy on the CPU (128 x 128: microseconds). b is divided by a running sample
std (Welford over every paid step, learner state, 1.0 until two values), multiplied by
max(1 / sqrt(N), `e3b_floor`) and clipped to [0, 1] before `e3b_beta`. N is
`counts.get(ledger.novelty_key())`: the ledger already counted this run's first visit in the same
step, so the bonus reads without counting (no double count). A step without a key (no room index)
uses the floor; N = 0 (full table) counts as new. The product, not a sum, follows the ICML 2023
paper: the count factor fades the bonus in cells seen in many runs, and the episodic factor fades
it for states already seen in the episode.

Determinism: phi is a no-grad forward of fixed weights; C^-1 and the std are float64 sequences
in step order, so a given weight state and observation sequence always pay the same bonus. The
IDM update between rollouts changes phi for the next rollout only.

## Decision 4: inverse dynamics on the replay

The IDM is an MLP(2 x 128 -> 256 -> 14) with three cross-entropy heads (move 5, shoot 5, use 4),
loss summed over heads, averaged over pairs whose episode did not end at t (`next_valid`). It
trains with its own Adam (eps 1e-5) for `e3b_idm_steps` steps of `e3b_idm_batch` pairs sampled
uniformly from the replay, after the PPO epochs and the auxiliary phase, while the game is paused.
With auxiliary losses on, the replay is the auxiliary one (one copy, no extra memory); otherwise
the learner keeps its own `Replay(replay_rollouts)`. The policy and its optimizer are untouched.

## Decision 5: contract, checkpoints, metrics

`intrinsic` is hashed like `level_replay`: `none`, absent or explicit, is dropped before hashing,
so the shipped hash stays `0399c37d...`. The `e3b_*` hyperparameters are recorded per checkpoint
only under `e3b_count_v1`, so manifests of the shipped contract do not change. `e3b.pt` (format 1:
embedding, IDM, Adam, std) is saved and hashed beside `auxiliary.pt`; resume under `e3b_count_v1`
refuses a checkpoint without it and a model trained with another `intrinsic`. A different
`e3b_embed_dim` cannot load the state (refused as a checkpoint error). The episodic C^-1 is not
saved: a resumed session starts with an env reset. `train.csv` gains `e3b_idm_loss`,
`e3b_bonus_mean` (mean r_int per step since the previous update) and `e3b_seconds`;
`episodes.csv` gains `col_e3b` after the ledger columns. Older files are upgraded once.

## Magnitudes

- Per step 0 <= r_int <= `e3b_beta` = 0.05; the ledger's per-step time cost is 0.001.
- Measured with a fresh embedding over a random walk in a 1x1 room (Mac CPU, scratch script):
  per episode about 3.5 for 300 steps and 5.4 for 600 steps when every cell has N = 1, and about
  0.5 and 0.8 once the cells are at the floor (N >= 100). The sum grows about with log T because b
  decays as states repeat.
- Against reward v12: room first visit +5, room clear +10, floor +30, death -11, full stall
  -11.0. In the first runs the bonus is comparable to one room visit per episode; the start room
  reaches the floor after about 100 runs, so later the bonus is mostly paid in rooms and
  situations still new across runs. A trained embedding separates states better than the fresh
  one, so the real sum may be somewhat higher; `e3b_bonus_mean` and `col_e3b` show it. Lower
  `e3b_beta` (for example 0.02) if `col_e3b` rivals `col_room_visit`.

## Cost (development Mac CPU, torch 2.14.1)

- Per env step: 0.76 ms with one torch thread, 1.7 ms with the default 8 threads (phi forward plus
  Sherman-Morrison), under 2% of a 111 ms decision. On cuda the forward adds one small transfer.
- Per update: 64 IDM steps of 256 pairs took 22 s on 4 CPU threads (two extractor passes per pair,
  like the auxiliary phase); on the RTX 4070 it should be a few seconds (not measured). Lower
  `e3b_idm_steps` for CPU-only runs.
- Memory: about 1 M parameters (embedding and IDM) plus Adam, `e3b.pt` about 4 MB; no extra replay
  with auxiliary losses on.

## Risks

- Bonus farming: the bonus is bounded per step and fades with counts, but an agent may still
  linger in situations its embedding cannot predict (noisy TV). The inverse dynamics keeps only
  what the action controls, which is the paper's defence; watch `col_e3b` against outcome terms.
- Non-stationarity: phi changes after every update, so b of the same state differs between
  rollouts; the std normalization keeps the scale.
- The extra per-step forward runs inside the game loop; on a slow CPU it could stretch decisions.
