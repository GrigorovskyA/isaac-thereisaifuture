## ADDED Requirements
### Requirement: Offline stagnation replay
Stagnation audits SHALL replay verified paired traces offline and MUST reproduce
logged shaping and policy-visible encoding before attributing behavior to the
policy. They MUST NOT launch the game, update models or normalizers, or use
oracle data as model input.

#### Scenario: Verified reproduction
- **WHEN** a bundle manifest and paired policy/oracle traces are valid
- **THEN** the replay reports record count, refresh segments, target switches,
  per-target actions/displacement and shaping/encoding mismatch counts
- **AND** every recomputed firing-position bonus is compared with the logged value

#### Scenario: Corrupt or unpaired evidence
- **WHEN** a manifest hash/size differs, records are unpaired, reordered,
  identity-inconsistent, oversized or carry an invalid action
- **THEN** the replay fails without writing partial evidence
- **AND** an existing non-empty output directory is never overwritten

#### Scenario: Frozen policy probe
- **WHEN** checkpoints with matching config hash and seed are supplied
- **THEN** action probabilities on recorded observations use carried recurrent
  state and verified unchanged model/normalizer files
- **AND** counterfactual inputs are labeled as probes, not game states or
  native performance
