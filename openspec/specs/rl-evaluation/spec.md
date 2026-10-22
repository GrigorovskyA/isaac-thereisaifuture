# rl-evaluation Specification

## Purpose

Define evidence of learning and reproducibility for future RL experiments.

## Requirements

### Requirement: Versioned experiment manifest
Every training/evaluation run SHALL record its configuration, seeds, Git revision,
game/library versions, reward/observation/action schemas, device, and finite run budget.

#### Scenario: Resume a checkpoint
- **WHEN** the trainer loads a saved model
- **THEN** it checks schema/normalizer compatibility and records lineage in the manifest

### Requirement: Independent evaluation splits
Evaluation SHALL separate train, validation, and test; parameter tuning MUST NOT
use test outcomes for model selection.

#### Scenario: Select a checkpoint
- **WHEN** trained candidates are compared
- **THEN** selection follows a predefined validation rule and test is reserved for
  final evaluation

### Requirement: Gameplay metrics determine progress
Improvement claims MUST use gameplay metrics, a baseline, sample size, and
uncertainty rather than training reward alone.

#### Scenario: Reward increases while room success falls
- **WHEN** reward rises while room clear rate falls
- **THEN** the result is not accepted as improvement without investigating reward
  exploitation and evaluating gameplay outcomes

### Requirement: Deduplicated bounded reward
The reward ledger SHALL prevent repeated rewards for the same event, repeated
visits, and repeated damage to previously rewarded HP.

#### Scenario: Duplicate room-cleared event
- **WHEN** the same room-clear event arrives again within an episode
- **THEN** the room-clear reward is awarded only once

### Requirement: Honest infrastructure reporting
Evaluation MUST report infrastructure failures separately and MUST NOT omit them
without explicit counts and reasons.

#### Scenario: Some episodes fail to connect
- **WHEN** transport failures interrupt some evaluation episodes
- **THEN** the report includes their count and fault rate rather than showing only
  completed gameplay outcomes
