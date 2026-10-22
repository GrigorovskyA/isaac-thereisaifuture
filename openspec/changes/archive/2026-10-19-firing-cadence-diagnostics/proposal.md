# Proposal

## Why
The real v2 capture contains policy-selected silence and release/reissue gaps,
but no weapon cooldown. Native maximum-fire-rate loss cannot be established.

## What Changes
Extend existing opt-in callback_trace with bounded read-only FireDelay and
MaxFireDelay fields on shooting input records and correlated native tear records.
No character-stat, command, expiry, policy observation, reward or wire change.

## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `native-player-actions`: opt-in bounded firing cadence evidence.

## Impact
Production Lua and focused offline callback tests; diagnostic documentation and
evidence. Existing trace remains default off, 512 attempts/10 seconds/300 bytes,
nonrenewable per mod load. One separately authorized safe-room comparison is
recorded in `reports/2026-10-19-firing-cadence-runtime.md`. No repeat permission,
stat change, or training authorization follows implementation or that single run.
