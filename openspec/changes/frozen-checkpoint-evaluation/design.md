## Design

Live loop. `_evaluate_run` loads the training config (pure profile only) and builds
the env with the same `make_live_env` arguments as `_train_run` for the pure profile,
wrapped in `EpisodeMetricsEnv` writing `<eval root>/metrics/episodes.csv`. The loop is
`step -> (terminated or truncated) -> env.reset(), policy.reset(seed + episode)` until
the shared deadline. `LiveBudgetExpired` and `LiveSessionCancelled` propagate, so
`run_live` records them as `budget` exactly as in training. Events: `evaluation`
(policy, checkpoint id, timesteps, config hash, seed) at start and
`evaluation_result` (episodes, steps) in a `finally`.

Policy. `CheckpointPolicy` already applied the saved `VecNormalize` observation
statistics without updating them, kept LSTM state across steps and cleared it on
`reset`. It only predicted deterministically, so it gains `deterministic` (default
`True`, unchanged for existing callers) and `sampling_seed` (seeds the torch
generator). Evaluation uses `deterministic=False`, as training samples, with the
seed from the plan. It also gains `expected_reward_contract`; evaluation passes
`pure-v6`. The config contract hash and the config seed are checked on load. After
the loop `verify_unchanged()` re-hashes manifest, model and normalizer; a change is
a fault. `RandomPolicy` reseeds with `seed + episode`.

Supervisor. `SessionPlan.evaluation` (`EvaluationSpec`: policy and checkpoint path)
selects evaluation. Its validation requires a fresh start (no parent, no resume),
`steps = TIME_ONLY_STEPS`, `max_restarts = 0` (unlimited New Run after death or
stall, as in pure training, so the lease is the only bound) and at most 4 h. The
CLI derives seed (config seed unless `--seed`), disk cap (`budget.disk_limit_mb`)
and these counts; the user passes game, log, config, run root, output, seconds and
the policy. `NativeRuntime.preflight()` returns no parent for an evaluation: it
validates the checkpoint (config hash, seed, reward contract), refuses a run root
that overlaps the checkpoint or training root, holds a `checkpoints` folder or
already has episodes, and freezes the checkpoint files. `identity()` refuses to run
for an evaluation, so the checkpoint-progress readback is skipped. Classification is
unchanged: the worker stops at `deadline - STOP_MARGIN_SECONDS` and records
`budget` with a wall-time reason, which yields `completed`; an early worker exit is
`early_stop` and any fault stays `fault`. The `evaluating` phase replaces `training`
in status files.

Failure handling. Unreadable or mismatched checkpoint, foreign approval, invalid root
and a changed checkpoint stop the session with a fault; cleanup (worker, game,
approval, sleep, frozen hashes) is the existing, unchanged path.

Compatibility. No schema version changes. A second session in the same root is
refused when it already has episodes, so one folder holds one checkpoint, one policy
and one seed.

Limitations (future intent, not implemented). No pairing of seeds across policies:
the game seed is not controlled, so comparisons are statistical. Evaluation does not
detect that the game started a different character beyond the existing initial Isaac
check.
