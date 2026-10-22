## Why

Roadmap item 17: before tuning training, the single-game bottleneck must be measured
reproducibly. This change delivers an offline timing harness over the synthetic backend and
a rule-based, never-applied proposal of configuration changes.

## What Changes

- Add `benchmark.py`: `BenchmarkConfig`, `run_benchmark`, `compare_action_repeat`,
  `propose_config_changes`, `write_report`, `host_info`.
- Injectable clock, bounded steps and duration, JSON report split into `deterministic`,
  `timing` and `host` sections.
- Action-repeat comparison on the synthetic backend only, labelled `synthetic`.

## Scope and non-goals

- In scope: env steps/sec, game updates/sec, backend step latency, observation-encode cost,
  clear and fault rates under a seeded random policy, offline tests.
- Out of scope: real-game throughput, CPU/GPU and batch-size comparison, multiple game
  instances, memory profiling. No CUDA, Docker or multi-instance requirement.
- Proposals never edit configuration files.

## Dependencies and risks

- Depends on gymnasium-environment-v1, episode-lifecycle and the synthetic simulator.
- Risk: synthetic numbers do not transfer to Isaac; the real bridge latency is unmeasured.
- Risk: a random policy is a weak quality proxy; proposals therefore carry a re-validation caveat.

## Acceptance criteria

- Offline: with a fake clock, reported latency and steps/sec equal exact expected values.
- Offline: the `deterministic` section is identical across different clocks for one config.
- Offline: step and duration bounds stop the run; invalid bounds are rejected.
- Offline: proposals include evidence, are marked not applied, and are withheld without a clear win.
- Pending real game: reproducible throughput on an authorized profile; CPU/GPU, batch size and
  multi-instance comparisons.

This is an offline contract; it must not be archived until real-game evidence exists.

## Impact

New module `benchmark.py`; no change to existing behavior or wire protocol.
