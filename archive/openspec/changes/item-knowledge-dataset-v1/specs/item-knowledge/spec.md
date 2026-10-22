## ADDED Requirements

### Requirement: Provenance-checked dataset loading
The loader SHALL accept only datasets with schema version 1, at least one source carrying a
license, retrieval date, permitted use and a url or commit, and unique item ids, and MUST reject
oversized files and unknown fields.

#### Scenario: Missing license
- **WHEN** a source has no license
- **THEN** loading raises a knowledge error

#### Scenario: Duplicate ids or unknown schema version
- **WHEN** two records share an item id or the schema version is not 1
- **THEN** loading raises a knowledge error

#### Scenario: Oversized file
- **WHEN** the file exceeds the size limit
- **THEN** loading raises a knowledge error without parsing it

### Requirement: Optional dataset
The knowledge base SHALL be optional: an absent file MUST yield an empty knowledge base.

#### Scenario: File absent
- **WHEN** the dataset path does not exist
- **THEN** an empty knowledge base is returned and lookups return nothing

### Requirement: Explicit uncertainty
Records SHALL carry `confidence` and `verified_in_game`, and unknown items MUST be handled
explicitly rather than guessed.

#### Scenario: Unknown id lookup and encoding
- **WHEN** an id absent from the dataset is looked up or encoded
- **THEN** lookup returns none and the encoder reports it in the unknown fraction slot

### Requirement: Fixed-size knowledge features
The encoder SHALL produce a vector of constant size from the player's own item ids and MUST NOT
use any hidden state.

#### Scenario: Stable size
- **WHEN** any number of owned ids is encoded
- **THEN** the vector length equals the knowledge base vector size
