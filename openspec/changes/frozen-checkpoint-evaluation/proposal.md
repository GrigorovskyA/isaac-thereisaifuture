## Why

The `pure-v4` lineage trains unattended, but there is no way to say whether a
checkpoint plays better than an earlier one or than random. The old attach-only
`eval-live` runner is stale for this lineage: it uses 3 game updates per action
(training uses 6), has no stall watchdog (an idle policy never ends an episode),
writes no `episodes.csv` and needs a manually launched game. Retained checkpoints
t102400, t204800, t237568 and a random policy must be compared under exactly the
training protocol.

## What Changes

- `live.LiveRunOptions.mode` gains `evaluate` with `eval_policy` (`checkpoint` or
  `random`) and `eval_checkpoint`. `live._evaluate_run` builds the env exactly like
  the pure training env (action repeat, reward v6, stall watchdog, consecutive fault
  cap, deadline, stop file), writes `metrics/episodes.csv` under the evaluation root
  and never trains or saves.
- `CheckpointPolicy` gains `deterministic`, `sampling_seed` and
  `expected_reward_contract`; evaluation samples stochastically like training, with
  a fixed seed, and re-hashes the checkpoint at the end.
- `session_runner` gains `SessionPlan.evaluation` and the single-session flags
  `--evaluate checkpoint|random` and `--checkpoint <dir>`. Seed, disk cap, restarts
  and counts are derived. Approval, Continue entry, stop margin, cleanup and frozen
  source hashes are unchanged; the evaluated checkpoint files are added to the
  frozen hashes.
- `scripts/compare_eval.py` prints one summary row per evaluation root.
- `docs/TRAINING_SESSION.md` and `Start-Eval.cmd` describe and wrap one session.

## Capabilities

### New Capabilities

- `frozen-evaluation-session`: supervised, bounded, frozen evaluation under the
  training protocol.

## Non-goals

- No change to training, reward, observation, action or the `pure-v4` lineage;
  nothing under `runs/pure-v4` is written.
- No change to `live_evaluation.py` / `evaluate-live` beyond one docstring line.
- No model selection rule, ranking claim or new lineage; results are descriptive.
- No `--forever` evaluation and no automatic scheduling of several evaluations.
- No change to `dashboard.html`.

## Impact

`live.py`, `checkpoint_policy.py`, `session_runner.py`, `scripts/compare_eval.py`,
`Start-Eval.cmd`, docs and tests. Required real-game evidence: one native Windows
evaluation session per checkpoint and random, each ending `completed` with an
`episodes.csv`.
