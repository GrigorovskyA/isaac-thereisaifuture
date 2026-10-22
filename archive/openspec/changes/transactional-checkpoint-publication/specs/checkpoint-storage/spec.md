## Purpose

Publish model, normalizer, compatibility and continuation state as one complete
checkpoint so interruption cannot silently select a partial learning state.

## ADDED Requirements

### Requirement: Complete atomic publication
Checkpoint publication SHALL stage and flush all artifacts before exposing an
immutable completed directory and atomically replacing latest. Readers MUST see
the previous complete checkpoint or the new complete checkpoint, never a partial
pointer/artifact set. Staging and unreferenced directories MUST NOT be selected.

#### Scenario: Interrupted writer
- **WHEN** saving stops during model, normalizer, manifest, directory or pointer publication
- **THEN** latest still selects a complete prior or new checkpoint and no incomplete state is reported as saved

#### Scenario: Concurrent reader
- **WHEN** a reader resolves latest while publication occurs
- **THEN** it loads a complete old or new checkpoint without scanning temporary folders

#### Scenario: Windows pointer sharing conflict
- **WHEN** opening latest encounters WinError5/32/33 or Windows CRT EACCES without winerror during publication
- **THEN** the reader retries for at most one second and never selects a fallback checkpoint
- **AND** persistent or unclassified errors still fail explicitly without initializing a replacement model

### Requirement: Immutable versioned lineage integrity
New checkpoints SHALL include versioned artifact hashes and reject corrupt or
missing files before loading learning state. Writers MUST serialize and reject
stale parents or overwriting a published checkpoint. Version-1 artifacts MUST
remain readable under their existing compatibility contract without modification.

#### Scenario: Corrupt or incompatible resume
- **WHEN** an artifact hash, schema, seed, configuration or reward contract differs
- **THEN** resume fails explicitly before gameplay, never initializing a replacement policy

#### Scenario: Competing or interrupted publisher
- **WHEN** another writer owns the lock, the parent changed, or a prior unpublished directory exists
- **THEN** published history is preserved and no reader is redirected to that directory by discovery

### Requirement: Auditable strict continuation
Resume SHALL retain stored model/optimizer, normalization, Python/NumPy and declared
Torch RNG state, preserve parent identity and close an environment on failed restore.
Only completed updates MUST be checkpointed; partial rollouts remain unsaved.

#### Scenario: Resume then update
- **WHEN** a compatible completed checkpoint resumes
- **THEN** stored continuation state is restored before learning and a new completed update records that parent

#### Scenario: Missing or failed restore
- **WHEN** resume cannot load its named state or only unfinished artifacts exist
- **THEN** it stops without fresh initialization and releases any created environment
