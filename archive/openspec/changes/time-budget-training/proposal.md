# Proposal

## Why
The native pilot stopped learning after three deaths because its declared two
restart cap was too small. The user requested no practical death/step stops for
long runs. A time-budget mode must make that choice explicit and refuse hidden
configuration limits without changing learning state.

## What Changes
Add --time-budget-only for finite windows up to4h: nonbinding schema sentinels
1billion cumulative steps and5000 restarts, time-dominant navigation, configuration
ceiling checks, recorded effective limit mode. Diagnostic explicit counts remain.

## Capabilities
### New Capabilities
- `time-budget-training`: duration-governed count budgeting.
### Modified Capabilities
None.

## Impact
Runner CLI/preflight and tests/docs only. No Lua/deployment/schema/reward/config
migration, learning change or new native run. Existing max5000 approval schema is
retained; four-second restart pacing makes it nonbinding within4h.

## Risks and acceptance
Do not claim literal infinity; refuse time-only windows over4h or smaller config
ceilings. Deadline, infrastructure, disk, focus, lineage, navigation no-progress
and owned-cleanup guards remain. Native sustained acceptance remains pending.
