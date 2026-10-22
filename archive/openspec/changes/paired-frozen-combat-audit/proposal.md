## Why

Checkpoint weights change but native combat can stagnate. Training return alone
cannot establish improvement, and conservative HP credit is not a hit counter.
Ordinary gameplay cannot reproduce identical encounters without unapproved state
manipulation. Paired decisions on identical encoded inputs provide a narrower,
honest diagnostic alongside a counterbalanced descriptive native pilot.

## What Changes

- Add a pure geometric shooting-direction proxy over existing encoded observations.
- Use exact frozen t1536,t6912 and random policies on the same observation stream.
- Record counterfactual actions separately from executed actions and oracle labels.
- Run one bounded native Continue audit with default-off existing phase diagnostics,
  conditional death restart,immutable models and explicit pilot limitations.

## Capabilities

### New Capabilities
- `paired-combat-diagnostics`: identical-input frozen decision diagnostics.

### Modified Capabilities
None.

## Impact

One pure Python analysis module and tests;prepared local experimental runner and
reports. No observation/action/reward schema,learning algorithm or game-control
strategy changes. No save/reset/seed edits or strict gameplay ranking.
