## Context

AGENTS.md requires versioned schemas, explicit rejection of incompatible checkpoints, normalizer
saved with the model, no silent restart from scratch, and all seeds reported.

## Decisions

- **Config**: strict pydantic model of `configs/training-v1.yaml`; unknown keys and the `test` split
  are rejected. A `template_not_executable_yet` status refuses to run without `--allow-template`.
- **Budget**: training runs in `n_steps` chunks; timesteps, wall time and checkpoint disk size are
  checked between chunks. A checkpoint is saved after every chunk.
- **Checkpoint**: one directory holding `model.zip`, `vecnormalize.pkl` and `manifest.json`
  (written last); `latest.txt` points at the newest. The manifest records observation, action and
  reward schema versions, config hash, seed, parent id, timesteps and RNG state; no git data.
- **Resume**: requires an existing compatible checkpoint (schemas, config hash, seed); otherwise
  `CheckpointError`. Starting fresh in a directory that already has checkpoints is also refused.
- **Selection**: `select` accepts when clear-rate gain over random is at least 0.20 with at least
  100 episodes each; a Newcombe 95% interval is reported but is not part of the rule.
- **Multi-seed**: `run_seeds` records every seed including failures.
- **Lazy imports**: torch and sb3 load only inside `train`.

## Risks / Trade-offs

- Only global NumPy/Python/torch RNG are captured; environment RNG resumes from its seed.
