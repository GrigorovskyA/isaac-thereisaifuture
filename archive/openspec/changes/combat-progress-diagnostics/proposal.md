## Why

The stopped hour concentrated 69.96% of accepted positions near one corner, but
did not retain the actual policy inputs or raw enemy geometry. Repeated software
episodes in one room concealed sustained lack of registered combat progress.

## What Changes

- Add opt-in, bounded, same-frame policy and separate oracle diagnostic traces.
- Add an explicit active-game-update no-progress window that survives software
  resets within the same native room visit and stops before the next action.
- Expose both options in live and finite-session entry points and record limits.
- Keep reward, policy schema, checkpoint lineage, native game and learning unchanged.

## Capabilities

### New Capabilities
- `combat-progress-diagnostics`: truthful combat capture and conservative stagnation stop.

### Modified Capabilities

None.

## Impact

Python combat gate, live/session options, offline behavioral tests and documentation.
No new game APIs or deployment. Acceptance requires byte bounds, oracle separation,
same-frame identity, reset continuity, conservative HP floors and cleanup checks.
Native capture qualification remains separate from offline acceptance. Weapon-range
observations, verified kills, firing-position shaping and comparative gameplay
improvement are subsequent changes, not results of this instrumentation milestone.
