## Context

`training.train` saves `model.zip` (RecurrentPPO), `vecnormalize.pkl` and a manifest per
checkpoint, and moves `latest.txt`. Evaluation (`evaluation.evaluate`) drives any `Policy` with
`reset(seed)`/`act(observation)` over encoded observations. A trained checkpoint needs to enter
that interface without learning and without a second manifest format.

## Decisions

- **Explicit directory only.** The adapter takes one checkpoint directory. A path that is, or
  contains, `latest.txt` is refused, and the manifest `checkpoint_id` must equal the directory
  name, so a moving pointer cannot silently change what is evaluated.
- **Reuse compatibility checks.** `checkpoints.load_checkpoint` validates the manifest and
  schema versions; the caller must pass the expected config hash and may pass the training seed.
  Only `RecurrentPPO` is accepted. Model observation shape and `MultiDiscrete([5, 5])` action
  space, and the normalizer statistics shape, must match the current encoder.
- **Identity before loading.** SHA-256 of manifest, model and normalizer is computed once and
  exposed as a frozen, JSON-serializable `PolicyIdentity`. `verify_unchanged()` re-hashes for
  use at the end of an evaluation. Hashing and loading are not atomic; a tamper between them is
  detected only by `verify_unchanged()`.
- **Frozen normalization.** `VecNormalize.load` over a spaces-only stub env; `training=False`,
  `norm_reward=False`. `normalize_obs` is applied once per `act` and does not update
  statistics. The model is loaded without an env, so `predict` adds no second normalization.
- **Normalizer validation (review feedback 1).** At construction, before any inference, the
  saved observation mean and variance must be numeric, shape `(OBSERVATION_SIZE,)` and finite,
  variance nonnegative (zero allowed: epsilon keeps the divisor positive), statistics count
  finite and positive, and `epsilon` and `clip_obs` finite and positive. Corrupt state is a
  `CheckpointError`; it is never repaired or clamped. As defense in depth, `act` checks the
  normalized vector is finite before `predict` and does not advance state otherwise.
- **Recurrent state.** `reset` clears LSTM state and sets the episode-start flag; `act` passes
  both to `predict(deterministic=True)` and clears the flag after a valid action. A rejected
  observation or model output does not advance state.
- **Validation at the boundary.** Input must be numeric, shape `(OBSERVATION_SIZE,)` and finite
  (range is not clipped, matching what the environment emits). Output must be integer, shape
  `(2,)`, each component in `[0, 5)`; otherwise `InvalidPolicyOutput`.
- **Seed semantics.** Deterministic inference uses no RNG; `reset(seed)` ignores the seed for
  inference, and the seed never implies a reproducible game state.
- **Lazy heavy imports.** torch/sb3/sb3-contrib/gymnasium are imported only when loading.

## Training fix

`IsaacCombatEnv` places its episode summary under `info["episode"]`, the key SB3 reserves for
Monitor statistics (`r`, `l`, `t`). With RecurrentPPO's default `log_interval=1`,
`_dump_logs` raised `KeyError: 'r'` after any rollout containing a finished episode; the live
256-step smoke likely passed because no episode ended. `train` now wraps each environment in
`Monitor`, which overwrites the key only above the environment; `FaultTolerantEnv` records and
`evaluate` still read the inner summary.

## Risks / Trade-offs

- Pickle loading is trusted-input only. Accepted for local checkpoints; documented.
- No live runner is added, so a pilot needs a later, separately approved change.
