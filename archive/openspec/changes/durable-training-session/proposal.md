# Proposal

## Why

The stopped overnight experiment depended on unversioned orchestration and reported
a live process as running without evidence of learning. Startup clocks and final
metrics failures could also obscure the actual stop or cleanup result.

## What Changes

- Add a versioned, finite, Continue-only session runner with strict parent identity.
- Share one monotonic deadline across startup, learner and navigation; derive the
  nonrenewed approval from a single paired wall/monotonic clock sample.
- Persist observed phases, combat decisions, completed checkpoint and its update
  time, management durations, precise stop reason and owned cleanup results.
- Test delay, refusal, early exit, cancellation and cleanup failure offline.
- Keep native five-minute qualification pending a separately declared request.

## Capabilities

### New Capabilities

- `training-session`: Finite owned startup, supervision, truthful status and cleanup.

### Modified Capabilities

- `live-training-loop`: Accept an externally fixed deadline and cooperative stop.

## Impact

Python runner, live loop, trainer progress hooks, combat gate telemetry, tests and
operator documentation. No new dependencies, game APIs, deployment, reward,
observation, learning settings, save edits or New Run permission. Navigation caps,
transactional saves and comparable evaluation remain subsequent readiness items.
