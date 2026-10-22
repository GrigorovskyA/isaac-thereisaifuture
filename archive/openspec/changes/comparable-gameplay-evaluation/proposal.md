# Proposal

## Why

Changed tensors and reward do not show better play. Readiness item 4 needs a
reproducible offline comparison contract that cannot rank unmatched trajectories.

## What Changes

- Add bounded offline manifest/trace comparison with immutable content hashes.
- Require predeclared scenario/seed/repeat cells, policy identities and equal budgets;
  report every attempted cell, failure, censoring and missing attempt.
- Derive conservative HP-loss and observed death/clear metrics from raw normalized
  samples, independently of rewards; report coverage and paired deltas only when matched.
- Document original t6912, current t7424, future continued checkpoint and controls,
  frozen normalization/recurrent rules and held-out separation.

## Capabilities

### New Capabilities
- `gameplay-comparison`: auditable matched offline gameplay reports.

### Modified Capabilities
None.

## Impact

New Python module/CLI, tests and evaluation guide. No dependencies, policy/reward/
observation changes, native controller or deployment. Existing evaluation stays
compatible. Native matched-start acquisition and attribution remain unverified.

## Goals and acceptance

Reject changed evidence, duplicate cells and invalid numeric data. Unmatched,
assisted, mixed-control, synthetic or incomplete evidence cannot establish learning.
Tests cover damage gaps/healing/disappearance, empty clears, faults and pair validity.
Full Windows gate passes with primary-verified bounded Luna execution.

## Non-goals and risks

No game launch/reset/save edit/training, automated winner, power calculation or
claim that hashes establish truth. Native same-start capture remains a separate
finite task. HP drops are conservative observed loss, not projectile causation;
unseen final damage and phase transitions remain unknown.
