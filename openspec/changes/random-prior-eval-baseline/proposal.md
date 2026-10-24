## Why

The 2026-10-24 frozen evaluation compared checkpoints to the uniform `random` policy.
That policy draws the use head (none/bomb/active/pill-card) uniformly, so it requests
a bomb 114 times per episode against 10-19 for the checkpoints. A freshly created
model starts with P(use=none)=0.85 (`contract.use_head_initial_none_probability`). The
baseline therefore differs in the use head, not only in skill, and the comparison
overstates what the checkpoints learned.

## What Changes

- New `baselines.RandomPriorPolicy`: move and shoot uniform; use head none with the
  configured initial probability, the rest split evenly over the other three uses.
  Seeded per episode like `RandomPolicy`, stateless, never loads a checkpoint.
- `live.LiveRunOptions.eval_policy` and `session_runner.EvaluationSpec.policy` accept
  `random-prior`; `live._evaluate_run` builds it from the training config's
  `contract.use_head_initial_none_probability`. The `evaluation` record names it.
- `session_runner --evaluate` gains `random-prior`; `--checkpoint` is refused with it.
- `Start-Eval.cmd` runs it for the label `random-prior`; `docs/TRAINING_SESSION.md`
  describes it. `scripts/compare_eval.py` needs no change.

## Capabilities

### Modified Capabilities

- `frozen-evaluation-session`: adds a prior-matched random baseline.

## Non-goals

- No change to the existing `random` policy, to training, reward, observation, action
  or the config contract hash.
- No claim that `random-prior` is a skill floor or a model-selection rule; results stay
  descriptive.
- No new config field: the probability is read from the existing contract.

## Impact

`baselines.py`, `live.py`, `session_runner.py`, `Start-Eval.cmd`, docs and tests.
Required real-game evidence: one native Windows `random-prior` evaluation session.
