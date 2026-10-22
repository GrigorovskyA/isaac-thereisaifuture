# Design

## Decisions
Inputs are an extracted evidence bundle whose `MANIFEST.json` sizes/SHA256 must
match before any record is read; files outside the bundle are rejected. Policy
and oracle streams are read with record, line-byte and event caps, paired by
identical strictly increasing `record_id`, and validated as `LiveSnapshot`
before/after states with identical session/frame identity, schema-2
`encoder_before_vecnormalize` observations of size 723 and in-range
`[move, shoot]` actions. Any violation raises `ReplayError`; no partial output
is written.

Shaping is recomputed by a fresh `FiringProgressV5`; a chain break
(`before` identity differs from the previous endpoint) calls `begin()` and
starts a new segment, matching rollout refresh without env reset. Each bonus is
compared exactly with the logged `firing_position_reward` for the endpoint
frame. Oracle data (HP, navigation grid, firing target) is used only for audit
columns and never enters model inputs. Frozen-model evaluation uses
`CheckpointPolicy` (config hash and seed required), normalizes with the saved
statistics without update, carries LSTM state from the first record and verifies
model/normalizer hashes unchanged afterwards. Counterfactual probes (mirrored
enemy x, unknown movement mask) are labeled as non-game inputs.

Output goes to an absent or empty directory (`rows.jsonl`, `summary.json`);
existing evidence is never overwritten. Learning metrics reuse
`exposed_start.sample_of/phase_metrics`; endpoint samples differ from the
published sample basis (1607 vs 1613) and the report states it.

## Compatibility
No protocol, schema, reward, observation or action version changes. The tool
only reads current contracts; a future contract version is rejected rather than
silently reinterpreted.
