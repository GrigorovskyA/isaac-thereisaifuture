# Proposal

## Why
The v5 pilot still shot toward blocked enemies. A45-degree nearest-enemy proxy
cannot distinguish a plausible cardinal firing line from a wall or a diagonal.

## What Changes
- Add pure policy-visible cardinal shot diagnostics: alignment, range, clear,
  blocked, unknown, incomplete visible membership and selected versus missed options.
- Audit the saved v4/v5 trajectories and frozen v5 shooting probabilities.
- Run one bounded scripted positive control in the existing room to test native
  clear-line damage accounting; keep it separate from model performance.

## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `rl-evaluation`: honest, bounded directional firing evidence.

## Impact
New offline diagnostic module/tests and evidence. No policy/reward/normalizer/
action contract changes, optimizer updates or dependency changes. Preserve all
models. No action mask or reward for shooting a wall. Native control is finite,
Continue/file2 only, no New Run; positive control is not learned improvement.
