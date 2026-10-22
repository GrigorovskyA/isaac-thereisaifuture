## Why
Nine recorded native actions used actor observations 9-21 frames older than their
command after optimizer/checkpoint work. Backend draining updates the command
reference but cannot retroactively refresh the observation used for inference.

## What Changes
- Explicitly end a gated collection segment before optimization, releasing input.
- Use SB3 public force-reset before the next rollout to acquire and normalize a
  fresh gated observation and reset recurrent episode starts.
- Record an unknown collection gap without fabricated transitions or outcomes.
- Preserve existing observation/reward/checkpoint meanings; no automatic learning,
  model migration or New Run.

## Capabilities
### New Capabilities
- `fresh-rollout-observations`: honest refresh across optimization gaps.
### Modified Capabilities
None.

## Impact
Gated live trainer, collection callback, gate diagnostics, behavioral tests and
evidence. Synthetic training defaults stay unchanged. No optimizer or reward tuning.
