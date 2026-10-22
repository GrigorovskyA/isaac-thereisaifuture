## Why

The frozen native pilot retained enemy visibility but no sampled HP reduction.
The player stayed near a room edge. A broad shooting-angle proxy cannot establish
actual aim,range,obstruction or useful movement. Replay the recorded commands,
positions and measured walking grid before changing reward or inference.

## What Changes

- Add offline-only motion and measured-grid route diagnostics.
- Reject movement comparisons across session/epoch/visit changes or long frame gaps.
- Measure requested movement versus observed displacement without labeling it an
  authoritative collision or creating a reward penalty.
- Replay the recorded native pilot;keep walking-grid reachability separate from
  projectile line of sight,weapon range and learned navigation.

## Capabilities

### New Capabilities
- `combat-motion-diagnostics`: offline identity-bound motion and route evidence.

### Modified Capabilities
None.

## Impact

Pure analysis module,behavioral tests and evidence. No new game launch,policy,
observation/reward schema,checkpoint change or scripted combat path following.
