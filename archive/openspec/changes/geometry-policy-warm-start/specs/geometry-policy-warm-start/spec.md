## ADDED Requirements
### Requirement: Explicit behavior-preserving geometry warm start
A one-time migration SHALL preserve old parameters,optimizer moments,prefix
statistics,RNG and counters,zero new input columns/moments,and publish a separate
schema2/v4 checkpoint linked to its immutable parent. Unknown layouts MUST fail.
#### Scenario: New visible features before learning
- **WHEN** any bounded74-feature extension is appended to the same649 prefix
- **THEN** the migrated recurrent action/value outputs match the original within
  a declared numerical tolerance before training
- **AND** original files and ordinary resume rejection remain unchanged
#### Scenario: Expanded optimizer and statistics
- **WHEN** migration prepares723 inputs
- **THEN** old moment/statistics values are retained and new moments are0
- **AND** new observation mean0/variance1 with inherited count is recorded as a prior
### Requirement: Finite exploratory native trial
The pilot SHALL use only the named compatible checkpoint on file2 Continue within
300s inclusive startup,2GiB,128MiB trace,max10 death restarts and zero retries or
infrastructure faults. It MUST report saved/unsaved samples and gameplay metrics
separately from reward and clean up owned input,game and approval.
#### Scenario: Missing Continue or no improvement
- **WHEN** Continue is absent or the trial produces no damage/clear improvement
- **THEN** no replacement game or longer experiment starts automatically
