## Design

- `list_checkpoints(root)` scans direct subdirectories that contain a manifest, reads it with
  `read_manifest`, flags incompatibility via `check_compatible` (reason kept in the entry), and
  reads optional `report.json` (an `EvaluationReport.to_dict()`) for clear rate. Corrupt
  manifests are listed as incompatible, not hidden.
- `spectate(policy, env_factory, scenario, mode=, seed=, max_steps=, recorder=)` is a generator
  of text lines: header, per-step `frame_id/action/reward/outcome`, final `summary`. The policy
  is reset with the seed and the env reset with the same seed and fixed scenario, so output is
  deterministic. `finally` releases the backend and closes the env.
- Frames are copied to a `policy_frames` recorder through a backend proxy; oracle events are
  never passed to the recorder or printed.
- `resolve_policy` validates a checkpoint (rejecting incompatible ones) before calling an
  injected loader; the spectator never trains.
- `main` defaults to the synthetic simulator and prints a `# SYNTHETIC` banner; `--game` is
  refused unless an `env_factory` is injected.
- Trade-off: no wall-clock pacing offline; real-speed playback is deferred to the real backend.
