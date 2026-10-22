## Why

The t8960 trace labels the same enemy killed and present two frames later.
Software truncations also reset the healed-HP allowance. Correct these live reward
sources before further learning; preserve existing checkpoints as development history.

## What Changes

- Stop deriving remaining-HP damage or kills from list absence. Positive HP drops
  remain approximate; genuine kill bonuses are withheld until verified evidence exists.
- Preserve bounded per-identity HP floors across software resets in the same bridge
  session/epoch. Rebaseline gaps without retroactive reward; stop on history exhaustion.
- **BREAKING**: tag new live learning with a distinct reward contract and reject
  old-contract resume before constructing an environment. Keep old artifacts readable.

## Capabilities

### New Capabilities
- `live-reward-continuity`: bounded HP credit history and explicit training compatibility.

### Modified Capabilities
- `live-training-loop`: replace disappearance-based damage/kill inference conservatively.

## Impact

Python event derivation, checkpoint manifests/training validation and behavioral tests.
No Lua deployment, policy encoding, coefficients or dependencies change. No new training
or automatic model reset. Native acceptance stays pending; this is a conservative
offline correction, not exact native death delivery or persistent campaign accounting.
