# Design

## Context

See proposal.md. Existing save IDs encode config/seed/timesteps; manifests already
hold RNG and compatibility, and SB3 archives contain optimizer state. Public readers
resolve latest.txt explicitly; no discovery fallback is needed.

## Goals / Non-Goals

Protect publication against process interruption and concurrent reads/writers.
Retain old saved states unchanged. Do not promise power-failure/filesystem-level
durability, recovery of an unpublished first checkpoint, or native engine/RNN
trajectory continuation. Game restarts remain episode boundaries, not model resets.

## Decisions

- Acquire a nonblocking OS byte-range/advisory writer lock per checkpoint root.
  The small lock file remains; process death releases its handle automatically.
  Check the current parent while holding it; a stale writer cannot publish rollback.
  Preserve the existing first-publication API: an empty root may explicitly record
  an external parent. A missing pointer with completed history cannot use that path.
- Save into an owned UUID staging directory on the same filesystem. Flush model,
  normalizer and manifest, then rename the complete directory. Do not overwrite
  existing directories. A collision with an unpublished complete candidate uses
  a unique suffix; it is never selected as recovery by directory scanning.
- Write and flush a unique pointer temporary, then replace latest atomically.
  Retry Windows sharing refusals for at most one second; failure preserves old
  latest. Clean only owned temporary paths; hard-kill leftovers remain ignored.
- Storage manifest v2 adds SHA256 for model/normalizer. Readers validate hashes
  before heavy deserialization; v1 remains supported with its original missing-file
  and schema/config/seed/reward checks. No legacy manifest is rewritten or upgraded.
- Native Windows full-gate follow-up exposed a pointer-open sharing race during
  publication. Read the bounded pointer directly, retry only WinError 5/32/33 or
  native Windows CRT EACCES without winerror for
  at most one second, and retain explicit failure for persistent/unclassified
  refusals, missing pointers and corruption. Never fall back to directory discovery.
- Validate pointer/artifact basenames and v2 pointer/manifest identity; preserve v1
  directory aliases under their original compatibility contract. Reject explicit
  resume when latest is missing or invalid. Refuse accidental fresh training in a
  root containing unfinished or completed checkpoint artifacts.
- Preserve existing trainer restore order, testing actual SB3 optimizer tensors,
  normalizer and RNG at the learning boundary. Close the base environment if heavy
  model/normalizer loading fails. Interrupted rollouts retain existing accounting.
  Final runner readback independently verifies latest after worker shutdown, so
  a committed publication survives a lost checkpoint-completed event in status.

## Risks / Trade-offs

- Metadata flush/rename is not a general power-loss guarantee; claim process-crash
  consistency only. Existing v1 files have no embedded artifact hash guarantee.
- Staging/orphan files left by a killed process consume disk and remain within
  existing disk accounting. No automatic deletion or save/model salvage is added.
- A caller already reading a complete older directory can finish safely after
  latest advances. Strict stale-parent rejection may refuse a second writer; it
  cannot silently merge independently trained state.
- Native damaged/cleared/revival validation is not supplied by synthetic storage
  tests; existing native acceptance tasks remain pending.
