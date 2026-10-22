# Proposal

## Why

The first combat-gated training attempt stopped after 12 samples: a single bridge
restart dispatch was followed by two native new-game starts and capability refusal.
Existing telemetry cannot identify callback order or the approval invalidation
branch; existing restart tests model only one exit/start pair.

## What Changes

- Add default-off, bounded local lifecycle diagnostics around dispatch, game
  callbacks, disconnect and capability negotiation, including authority state.
- Extend offline production-Lua scenarios to distinguish expected restart,
  additional exit/start, delayed callbacks, expiry and disconnect ordering.
- Document an operator-present diagnostic capture procedure and its evidence limits.
- Preserve every approval, release, restart and deadline rule. This change diagnoses
  the failure; any behavior fix requires separate evidence and scope.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `live-training-loop`: bounded local lifecycle and authority diagnostic records,
  without changing the wire protocol or training authorization.

## Impact

Expected implementation: mod/observer/main.lua, production-Lua tests and local
diagnostic documentation. No dependencies, saves, settings, policy observations,
reward calculation, checkpoint format or training algorithm change.

Acceptance requires tests of ordering, hard diagnostic limits and fault isolation,
Windows Check.ps1 and strict OpenSpec validation. A later separately budgeted
real-game capture must correlate one dispatch with callbacks and reconnect, or
record the unresolved blocker. No forced death, additional resets, approval
renewal, automatic launcher or supervisor is introduced. Existing native callback
ordering in the two-start failure remains unknown; no new engine API is assumed.
