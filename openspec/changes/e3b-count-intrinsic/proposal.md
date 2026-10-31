## Why

Rewards v9 to v12 plateaued at about 2 rooms per episode, and the cross-run cell novelty of
reward v11/v12 pays only the first visit of a cell per run: inside a run it stops guiding as soon
as the nearby cells are counted, and it cannot tell a new situation in a known cell (other enemies,
items or doors) from a repeat. E3B (Henaff et al., NeurIPS 2022, arXiv 2210.05805) pays the
episodic elliptical novelty of a learned inverse-dynamics embedding and was state of the art on
MiniHack and Habitat; Henaff, Jiang and Raileanu (ICML 2023, arXiv 2306.03236) show that the
episodic bonus works best multiplied by a global count bonus and fails when the two are added.
Intrinsic exploration is allowed by the pure doctrine (`docs/UPDATE_DECISION.md`, principle 2):
it is no hint, no observation and no change of the reward v12 terms.

## What Changes

- `e3b.py`: an embedding phi (a separate small copy of the structured extractor, own weights,
  then Linear to `e3b_embed_dim` 128) over the raw observation with the stall clock and the
  visited-cell grid zeroed (from `FEATURE_BLOCKS`); an inverse-dynamics head g(phi(s_t),
  phi(s_t+1)) -> a_t with three softmax heads (5, 5, 4); the episodic bonus b_t = phi(s_t+1)^T
  C_t^-1 phi(s_t+1), C_0 = `e3b_lambda` I, C_t+1 = C_t + phi phi^T, reset at every episode start,
  C^-1 by Sherman-Morrison in float64; a running std of b.
- Combined intrinsic reward r_int = `e3b_beta` x clip(b_t / std(b) x max(1 / sqrt(N),
  `e3b_floor`), 0, 1), N the cross-run novelty count of the (stage, room, cell) key of s_t+1, read
  from the ledger's table without counting (`RewardLedgerV4.novelty_key`).
- `env.IsaacCombatEnv.intrinsic`: set by training only; adds r_int to the step reward as its own
  component `e3b`, summed per episode into `episodes.csv` `col_e3b` (empty when off). It pays only
  with a writable cross-run table, so frozen evaluation (frozen table, no hook) never pays it.
- `learner.PureRecurrentPPO`: contract `intrinsic`, builds the E3B learner, records complete
  rollouts into the auxiliary replay (or its own replay without auxiliary losses) and, after the
  PPO epochs and the auxiliary phase, runs `e3b_idm_steps` (64) Adam steps of `e3b_idm_batch`
  (256) pairs at `e3b_idm_lr` (3e-4); logs `e3b_idm_loss`, `e3b_bonus_mean`, `e3b_seconds`.
- Contract field `intrinsic: none | e3b_count_v1` (hashed; `none`, absent or explicit, is left out
  of the hash). Hyperparameters `e3b_beta` 0.05, `e3b_lambda` 0.1, `e3b_floor` 0.1,
  `e3b_embed_dim` 128, `e3b_idm_steps` 64, `e3b_idm_batch` 256, `e3b_idm_lr` 3e-4 (not hashed;
  recorded per checkpoint only under `e3b_count_v1`).
- Checkpoints save embedding, inverse dynamics, their Adam and the running std as `e3b.pt`
  (`e3b_file`, `e3b_sha256` in the manifest); resume under `e3b_count_v1` refuses a checkpoint
  without it. `train.csv` gains three columns and `episodes.csv` one, with one-time upgrades.

## Non-goals

- Not enabled in the shipped config: `intrinsic` stays absent and the contract hash stays
  `0399c37db311f00df37cea79a66385ff6cd7150dfcfa0c9e3e46415f577da79a`.
- No change of reward v12 coefficients, observation schema 9, actions or Lua.
- No additive combination, no RND and no second value head; one value head learns the sum.
- No intrinsic reward in frozen evaluation; the episodic matrix and the replay are never saved.

## Acceptance

- Offline gate (`scripts/check.sh` with the two known macOS-only failures / `Check.ps1`),
  `scripts/smoke_rl.py` and strict OpenSpec validation pass; the shipped contract hash is
  unchanged.
- Tests show: Sherman-Morrison equals the direct inverse; the bonus decays for a repeated state
  and resets on a new episode; the excluded blocks do not change phi; the multiplicative count
  factor and its floor; the `e3b` column sums and the columns sum to the return; the checkpoint
  round trip and the refused resume; evaluation pays nothing; `none` keeps the hash and the
  manifests; the inverse-dynamics loss falls below half on a tiny synthetic task.
- Per-step and per-update cost measured on the Mac CPU (design).
- Native, later and as its own lineage: an `e3b_count_v1` lineage compared with the `none` lineage
  at equal steps (rooms per episode, share of episodes with 3+ rooms, floor 2 rate) in frozen
  evaluation, with `col_e3b` well below the outcome columns per episode.

## Impact

- `src/isaac_threrisaifuture/{e3b,env,rewards,learner,training,checkpoints,training_metrics,
  episode_metrics}.py`, `configs/training-pure-v4.yaml` (comments and unhashed defaults only),
  `scripts/smoke_rl.py`, tests, docs.
- Turning it on is a new lineage; checkpoints get the E3B state (about 4 MB) and the learner adds
  one phi forward per env step.
