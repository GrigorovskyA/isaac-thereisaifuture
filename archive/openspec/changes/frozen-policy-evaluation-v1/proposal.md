## Why

The first live RecurrentPPO smoke checkpoint exists (`1f4a187e-s20-t256`), but nothing can run a
saved checkpoint as a fixed, non-learning policy. Evaluating checkpoints against the random and
scripted baselines needs a frozen inference adapter with a verifiable identity, and a predeclared
plan that keeps exploratory live pilots apart from confirmatory comparisons.

## What Changes

- Add `checkpoint_policy.py`: `CheckpointPolicy` implements the existing `Policy` interface
  (`name`, `label`, `reset(seed)`, `act(encoded_observation)`) over one explicit RecurrentPPO
  checkpoint directory with its saved VecNormalize state, plus a serializable `PolicyIdentity`
  (model/config/normalizer/manifest hashes) and `verify_unchanged()`.
- Add `docs/LIVE_EVALUATION_PLAN.md`: a future exploratory pilot and a blocked confirmatory
  comparison, with denominators, stop conditions and operator-intervention rules.
- Fix found while testing (authorized by the user): `training.train` wraps the environment in
  SB3 `Monitor`, because the environment's own `info["episode"]` summary crashed SB3 rollout
  logging with `KeyError: 'r'` after the first finished episode.

## Scope and non-goals

- Acceptance is the offline adapter, its tests and the plan only. Real performance evaluation is
  `not_run`/blocked and MUST NOT be claimed from this change.
- No live runner, CLI command, game connection, deployment, training or approval writing.
- No other algorithms, no second manifest system; existing `checkpoints.py` checks are reused.
- Does not replace `combat-baselines-and-reward-v1` or `combat-ppo-training`; their multi-seed,
  held-out, 100-episode and +20 percentage-point criteria are unchanged.

## Dependencies and risks

- Depends on `checkpoints.py` manifests, `encoding.OBSERVATION_SIZE`, the `MultiDiscrete([5, 5])`
  action space and the lazily imported sb3-contrib RecurrentPPO.
- Risk: checkpoint artifacts are pickles; loading is code execution. Only local project
  checkpoints may be loaded; identity hashes detect later changes but do not make pickles safe.
- Risk: the live backend has no seeded starts, so live comparisons are descriptive only.

## Acceptance criteria

- Offline tests cover frozen statistics, single normalization, recurrent carry/reset,
  deterministic inference, unchanged artifact hashes, compatibility failures, missing/corrupt
  artifacts, malformed/non-finite observations and invalid model outputs, using one real
  synthetic RecurrentPPO save/load round trip.
- The adapter runs through the existing offline `evaluate` harness on the synthetic room.
- `openspec validate frozen-policy-evaluation-v1 --strict` passes.
- Pending (not part of acceptance): any real-game pilot or comparison.

## Impact

- New: `src/isaac_threrisaifuture/checkpoint_policy.py`, `tests/test_checkpoint_policy.py`,
  `docs/LIVE_EVALUATION_PLAN.md`.
- Changed: `src/isaac_threrisaifuture/training.py` (Monitor wrapper),
  `tests/test_training_manifest.py` (regression test).
