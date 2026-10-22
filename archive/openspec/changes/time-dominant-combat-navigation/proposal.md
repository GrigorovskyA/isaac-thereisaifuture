# Proposal

## Why

The stopped long run exhausted twenty cumulative transitions. Raising that count
does not solve repeated empty-room routes: the manager remembers exit use counts,
but not their observed destinations or whether any unexplored exits remain.

## What Changes

- Add explicit time-dominant navigation under a finite global deadline, retaining
  bounded diagnostic defaults and every per-action safety check.
- Learn directed room/door connections only from actual same-floor transitions.
  Prefer unexplored exits or follow confirmed paths to an observed frontier.
- Stop with a distinct observed-component-exhausted or unreachable-frontier reason
  instead of cycling; never claim the full hidden floor was exhausted.
- Expose this mode in live CLI/session runner and keep navigation outside learning.

## Capabilities

### New Capabilities
- `combat-navigation`: Scripted travel over observed ordinary-room geometry and
  confirmed connections, with explicit finite operating modes and no-progress stops.

### Modified Capabilities
None. Existing combat gate contracts remain; time-dominant handoffs use the finite
session window as their explicit wait cap, still narrowed by the same run deadline.

## Impact

Python navigation manager, live/CLI/session options, tests and documentation.
No Lua/protocol, policy, observation, reward, checkpoint or dependency changes.
No new native API assumptions, New Run fallback, training launch or deployment.
Native qualification remains pending a separately declared short run.
