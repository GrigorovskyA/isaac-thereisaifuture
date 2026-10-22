## ADDED Requirements

### Requirement: Phase-separated curriculum evidence
Curriculum evidence SHALL identify setup, learning and each frozen evaluation
phase, named checkpoints, start conditions and exposure. Reports MUST separate
damage dealt, damage taken, clears, deaths, stagnation, faults and missing
coverage. Scripted outcomes and optimizer updates MUST NOT be attributed to
learned policy improvement.

#### Scenario: Script succeeds but learner does not
- **WHEN** setup reaches a valid firing position but the learner records no observed damage
- **THEN** the report retains the setup success and learner result separately
- **AND** it does not describe a trained better player

#### Scenario: Native phases start in different world states
- **WHEN** Continue or preceding actions leave different enemies, HP, health or room conditions
- **THEN** both phase start fingerprints are reported
- **AND** the comparison is labeled observational and cannot establish a paired causal improvement

#### Scenario: Frozen phase is unavailable
- **WHEN** a named learned checkpoint or compatible combat state is absent
- **THEN** that evaluation is reported as not run with its exact reason
- **AND** no parent, fresh model or reset silently substitutes for the missing candidate

### Requirement: Immutable parent and explicit curriculum child
A curriculum child SHALL originate from an explicitly named compatible checkpoint.
Before learning, its model, optimizer, normalizer and RNG state MUST match the
declared parent. Parent artifacts and pointers MUST remain unchanged; completed
and unfinished learning work MUST be reported separately and saved children
MUST be reloaded for verification.

#### Scenario: Interrupted before first complete rollout
- **WHEN** the run stops before an optimizer update and checkpoint finish
- **THEN** the report records unsaved work and no trained checkpoint
- **AND** the copied initial child is not presented as a learned improvement

#### Scenario: A completed child checkpoint is saved
- **WHEN** an optimizer update and checkpoint publication complete
- **THEN** saved model and normalization state are reloaded with compatible contracts
- **AND** the report verifies parent hashes and child lineage independently of gameplay outcomes
