## Why
Recorded frozen combat showed no sampled enemy HP loss and repeated near-boundary movement. Walking reachability and coarse shot direction cannot establish tear range or projectile obstruction.

## What Changes
- Add literal-true, default-off local tear/target diagnostics to the observer.
- Sample owned player tears, reported range, target geometry and projectile-mode CheckLine without changing game state or wire data.
- Run bounded frozen t6912 native evidence, preserving model/normalizer/checkpoint lineage.

## Capabilities
### New Capabilities
- `combat-tear-diagnostics`: bounded local projectile evidence independent of policy/reward.
### Modified Capabilities
None.

## Impact
Observer-only diagnostic option, simulated Lua tests and native evidence. No policy, reward, observation schema or checkpoint migration. Missing native evidence remains pending rather than inferred from mocks.
