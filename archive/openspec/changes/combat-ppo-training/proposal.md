## Why

Roadmap item 08: the first learning run needs a bounded, resumable training command whose
checkpoints are self-describing, plus a selection rule fixed before any experiment.

## What Changes

- Add `training.py`: validated `TrainingConfig` (budget with hard stops), `train`, `main(argv)`,
  `run_seeds`, `EvalResult`, `SelectionRule`, `select`.
- Add `checkpoints.py`: `CheckpointManifest`, `save_checkpoint`, `load_checkpoint`, compatibility checks.
- Scenarios and the environment factory are parameters (items 06/07 supply them).

## Scope and non-goals

- Offline contract only: this change MUST NOT be archived until a real training run with several
  seeds and validation evidence exists. Torch/sb3 paths are not exercised by offline tests.
- Out of scope: evaluation callbacks wired to real scenarios, curriculum (item 09), long runs.

## Dependencies and risks

- Depends on the environment (06) and scenario/baseline modules (07) for the factory and evaluation.
- Risk: `RecurrentPPO` resume restores policy and normalizer but not mid-episode LSTM state.

## Acceptance criteria

- Offline: invalid config, incompatible checkpoint and resume without checkpoint are explicit errors.
- Offline: selection rule math (+20 pp, >= 100 episodes) is a pure function with a reported interval.
- Pending real run: several seeds, model beats random on validation in clear rate and damage.

## Impact

New modules `training.py`, `checkpoints.py`; no wire protocol changes.
