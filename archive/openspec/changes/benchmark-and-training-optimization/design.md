## Context

Roadmap item 17 asks for a reproducible throughput benchmark whose acceleration preserves step
and reward semantics. Only the synthetic backend exists offline.

## Decisions

- **Clock**: every timestamp comes from an injectable `Clock`; the default is `time.perf_counter`.
- **Measurement**: the env step window covers `IsaacCombatEnv.step`; a backend proxy times
  `GameBackend.step`; observation encoding is timed separately on the latest frame, outside the
  env step window, so it is not double counted.
- **Report sections**: `deterministic` (config, counts, outcomes, rates) depends only on config
  and seed; `timing` and `host` are host-dependent. Reproducibility checks compare only the first.
- **Bounds**: `max_steps` and `max_seconds` are validated and capped; a failing reset stops the run.
- **Faults**: `EpisodeFault` is counted into `fault_rate`, never into outcomes.
- **Comparison**: `compare_action_repeat` varies only `action_repeat`; the first run is the baseline.
- **Proposals**: `propose_config_changes` returns data with `applied: false`. A candidate needs a
  game-updates/sec gain, no clear-rate loss beyond a tolerance, no higher fault rate and a minimum
  episode count. The caveat demands real-backend and validation re-checks.

## Risks / Trade-offs

- Steps/sec rises trivially with action repeat, so gains use game updates/sec.
- Peak memory is not measured; deferred with the real-game work.

## Migration

Additive.
