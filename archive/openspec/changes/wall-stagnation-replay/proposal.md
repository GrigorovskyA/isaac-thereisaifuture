# Proposal

## Why
The ready-curriculum pilot (t26368 -> t27904) damaged target 1 from the left
wall, then stayed near (70,210) for the rest of the phase after target 1 vanished
from the observation. The published report could not separate a stale target,
encoding or reward defect from learned behavior. Native time must not be granted
again until the cause is reproducible offline.

## What Changes
- Add a bounded offline replay/audit tool (`wall_stagnation`) for paired
  policy/oracle traces: manifest verification, strict record pairing, live-firing
  v5 shaping re-execution against logged bonuses, geometry re-encoding, target
  switch/HP events, per-target action and displacement tables, and published
  metric reproduction.
- Optionally evaluate frozen checkpoints read-only on the recorded observations
  with carried LSTM state, including labeled counterfactual input probes.
- Add a sanitized nine-record fixture and tests.
- Record the diagnosis and a proposal; no reward, observation, action, Lua or
  training change is justified by the evidence (see report).

## Capabilities
### New Capabilities
None.
### Modified Capabilities
- `rl-evaluation`: reproducible offline stagnation replay evidence.

## Impact
New offline module, fixture, tests and report. No policy/reward/normalizer/action
contract change, optimizer update, dependency change or game launch. Checkpoints
are read and verified unchanged. Acceptance: on the 2026-10-22 bundle the replay
reports 1606 paired records, 7 segments, 0 shaping mismatches, 1606 encoding
matches and the published 7 stagnation windows; tests pass offline. Windows
`Check.ps1` and any later native experiment remain separate tasks.
