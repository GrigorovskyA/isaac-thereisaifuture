## ADDED Requirements

### Requirement: Feature kind table
The encoder SHALL publish an explicit table of contiguous feature blocks that covers every
observation index exactly once and names each block's kind: `continuous`, `binary` or
`one_hot`. The table MUST be built from the same layout constants as the encoder and checked
against its block offsets, never inferred from data. Binary and one-hot indices MUST only hold 0
or 1, and a one-hot block MUST hold at most one 1.

#### Scenario: Coverage
- **WHEN** the table is read
- **THEN** its blocks start at 0, follow each other without gaps or overlaps and end at the
  observation size

#### Scenario: Encoded values
- **WHEN** synthetic frames with every entity kind, doors, minimap rooms and items are encoded
- **THEN** every binary and one-hot index is 0 or 1, every one-hot block sums to at most 1, and
  every fractional value falls on a continuous index
