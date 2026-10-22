## Why

The frozen native diagnostic confirmed corner concentration despite coarse aim
alignment. Distance or shooting alone cannot distinguish a useful firing position
from a blocked lane. Changing coefficients cannot create that missing signal.

## What Changes

- Add opt-in negotiated reward-only ordinary-tear firing geometry: measured range,
  vulnerable visible target and at most32 native projectile-clear candidate cells.
- Add bounded graph-distance progress credit, once per physical room within a
  collector, surviving software resets/reentry, with no idle/shot/oscillation pay.
- Integrate a default-off live option under a distinct reward contract that refuses
  conservative-v2 checkpoints. Policy encoder/schema1 is unchanged; no new model,
  migration, native run, mod deployment or training is performed by implementation.

## Capabilities

### New Capabilities
- `firing-position-shaping`: bounded reward for measured reachable firing positions.

### Modified Capabilities
None.

## Impact

Observer negotiation/capture, typed reward-only wire data, live reward wrapper,
checkpoint reward contract, CLI and behavioral/Lua tests. No action controller or
policy observation change. Native weapon-model API support and geometry correctness
remain unaccepted until separately qualified. Actual damage/clears remain evaluation
metrics; unsupported weapons disable shaping explicitly. An explicit future lineage
plan is required before learning; t21760 and its parents remain preserved.
