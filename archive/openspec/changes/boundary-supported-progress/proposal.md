# Proposal

## Why
The closed geometry pilot spent 97.72% of sampled endpoints near a corner. Its
supported bilinear reward has no value for the first up/right escape steps.

## What Changes
- Add explicitly negotiated, reward-only ground-line evidence from the current
  player position to the nearest fully walkable interpolation patch.
- Add opt-in `live-firing-v5`, retaining historical v3/v4 behavior and checkpoints.
- Verify initial escape, retreat, blocked/unknown links, oscillation and room caps.
- Prepare native qualification separately from any learning or model migration.

## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `live-training-loop`: measured boundary support and explicit v5 compatibility.

## Impact
Lua acquisition, validated oracle telemetry, reward shaping, live CLI and manifests.
No dependencies, policy inputs, action semantics or save changes. Acceptance requires
offline regressions/full gate and separate native evidence. A five-minute learning
check follows qualification and an explicit preserved-parent migration plan;
neither changed reward nor optimizer updates establish better play.
