## Why
The native room clarification and offline counterexample expose wrong-sign
subcell progress, records shared across enemy goals and missing explicit shot
geometry in policy inputs. More unmodified training is not justified.

## What Changes
- Correct progress with interpolated grid distances and persistent per-target
  records sharing a physical-room allowance under live-firing-v4.
- Add opt-in policy observation2: own ordinary-tear range, four local ground
  movement probes and projectile-clear evidence to visible enemies only.
- **BREAKING**: schema2 uses a distinct input size and explicit checkpoint
  compatibility; old649/schema1 inputs and v3 artifacts retain their meaning.
- Offline implementation/testing only; no model initialization/migration,
  deployment, native control or automatic training is included.

## Capabilities
### New Capabilities
- `coherent-combat-geometry`: corrected progress and observable geometry inputs.
### Modified Capabilities
None.

## Impact
Reward wrapper, typed bridge extension, negotiated Lua capture, optional live
observation wrapper, checkpoint/training compatibility and diagnostics. Unknown
weapons/probes stay explicit; oracle HP/maps/goal cells never enter policy inputs.
Native API qualification remains separate; optimizer freshness is a later change.
