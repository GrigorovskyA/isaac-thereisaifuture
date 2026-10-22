## Why

Roadmap item 04: the Python side has only a snapshot of the player and room. The
RL environment (items 05-08) needs a fixed-shape, masked policy observation,
a separate oracle/reward event stream and frame recording/replay. This change
defines that contract and adds an opt-in read-only native export so recorded
fixtures can establish compatibility before later game integration.

## What Changes

- Add versioned wire models for entities (enemies, projectiles, obstacles, pickups) in a
  new frame message, kept separate from the policy observation.
- Add a deterministic observation encoder: fixed capacity, stable ordering, masks,
  overflow counters, explicit unknown vs zero, normalization constants.
- Add a separate oracle/event record type; the encoder rejects oracle fields.
- Add a frame recorder and replayer (JSON lines) with schema version in a run manifest.
- Add synthetic fixtures and behavioral tests.

## Scope and non-goals

- In scope: Python contract, encoder, bounded recorder/replayer, synthetic fixtures,
  opt-in native entity export, finite attach-only recording and real fixtures.
- Out of scope: reward accounting (item 07),
  Gymnasium environment (item 06), episode lifecycle (item 05).
- Runtime acceptance gate: this change MUST NOT be archived or checked off in the roadmap
  until real-game recorded fixtures validate against the schema.

## Dependencies and risks

- Depends on archived observation protocol v1. Item 03 (bridge-safe-actions) has accepted runtime evidence and is archived;
  this export remains read-only and does not request its action capability.
- Unknown: which Isaac Lua APIs expose entity IDs, spawn generation, enemy HP and
  projectiles on J460; the schema marks such fields optional and records provenance.
- Risk: the schema may need a revision after real fixtures; hence a schema_version field.

## Acceptance criteria

- Offline: encoder output has constant shape for 0..N+overflow entities; padding
  differs from a real object at the origin via mask; identical input gives identical output.
- Offline: oracle fields cannot reach the encoder; a test enforces this.
- Offline: record then replay yields identical observations; unknown schema versions are rejected.
- Pending real game: recorded fixtures from the installed build pass validation.

## Impact

New modules in src/isaac_threrisaifuture, tests, docs/RL_DESIGN.md update, and a new
observation-encoding capability.

## 2026-10-17 continuation

The user requested continuing the next roadmap step after committing the offline
batch and explicitly permitted a closed-game mod update. Lua export is now
included to satisfy the original real-fixture acceptance gate. Application
launch and save selection remain manual. Runtime checks must record which
entity kinds were actually encountered; empty-room snapshots do not verify
all four kinds. No reward/oracle export or training is introduced.
