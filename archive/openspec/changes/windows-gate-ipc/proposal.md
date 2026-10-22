# Proposal

## Why

Actual Windows integration tests reproduce WinError 5 when the gate replaces
request.json during an operator read. Stop cleanup can mask the original error.
This blocks the coupled Lua/Python/learner tests and future gated game use.

## What Changes

- Retry only Windows sharing/access conflicts for a short finite I/O window,
  clipped to existing handoff/global deadlines; preserve atomic publication.
- Make request/ack reading and removal tolerate the same bounded conflicts.
- Preserve the primary failure and attempt release/logging even if stop-file
  publication or token deletion fails.
- Validate real concurrent reader/writer behavior and the delivered coupled CPU
  learner on Windows, without accessing Isaac or real checkpoints.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `combat-experience-gate`: bounded Windows file sharing recovery and failure cleanup.

## Impact

combat_gate.py, focused tests, existing async regression tests and documentation.
No wire/schema/reward/model/dependency, game/save/approval or restart-limit change.
Acceptance is offline: deterministic I/O failure/deadline tests, Windows concurrency,
complete Lua/socket/gate/CPU learner tests and Check.ps1/strict OpenSpec. Real-game
training remains a separate operator decision. No new game API is involved.
