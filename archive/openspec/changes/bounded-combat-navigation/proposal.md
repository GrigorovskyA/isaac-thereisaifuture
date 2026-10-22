## Why

The t5120 continuation proves one complete live combat rollout. Between fights,
the gate still needs an operator or a slow screenshot-based private helper. Add a
bounded management route to another fight without training on scripted navigation.

## What Changes

- Negotiate optional `combat_navigation_v1` live management telemetry: current room
  identity/shape and existing open, unlocked doors to ordinary rooms only.
- Add opt-in same-client navigation inside the combat gate reset wait, preferring
  less-used exits and stopping on unsupported geometry, damage, stalls or budgets.
- Keep combat observations, reward, config hash and checkpoint schemas unchanged.

## Capabilities

### New Capabilities
- `bounded-combat-navigation`: management telemetry, bounded traversal and automatic
  fresh combat readiness through the existing gate.

### Modified Capabilities

- `combat-experience-gate`: distinguish the existing operator-managed handoff from
  opt-in navigation management. Default wire/action/readiness behavior stays intact.

## Scope, Risks and Acceptance

User extension (2026-10-20): support all twelve room shapes, including narrow,
long, 2x2 and four rotated L geometries, using measured walkability and bounded
cardinal pathfinding. No floor routing, secret/special/locked doors, item use,
screenshot processing or learned navigation. An unreachable route stops rather
than fabricating a transition. API documentation is
a candidate contract; installed-build acceptance remains required. Offline checks
must prove bounded cleanup, default compatibility and navigation exclusion from
policy/normalizer/reward. One bounded real-game check must show telemetry, an
actual transition and fresh combat readiness before runtime acceptance; keep open
if the scenario does not supply that evidence. No gameplay-quality claim.

## Impact

Observer Lua, live wire/config, CLI, one gate subclass, behavioral tests and docs.
The additional combat_navigation_grid_v2 capability carries a version-2 bounded
walkability mask; legacy version-1 telemetry remains available to explicit v1 peers.
Deploy only with Isaac closed. Current episode-lifecycle and other unfinished
changes are preserved; this is a separate runner prerequisite, not their archive.
