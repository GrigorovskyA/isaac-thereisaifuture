# Proposal

## Why

Saving currently writes model/normalizer directly into the final checkpoint and
rewrites latest.txt in place. Interrupted writers or concurrent readers can see
partial state; an existing completed directory can also be overwritten.

## What Changes

- Stage complete immutable checkpoints, flush files, validate artifact hashes,
  rename the completed directory and atomically replace the latest pointer.
- Add version-2 storage manifests with hashes, retaining read compatibility for
  version-1 checkpoints without changing observation/action/reward/config schemas.
- Serialize publishers with an OS-released writer lock and check current parent
  lineage to reject stale writers or rollback. Never select staging/orphan folders.
- Test interruption, concurrent reads, real synthetic optimizer/normalizer/RNG
  restore and fresh updates; preserve existing live checkpoint roots.

## Capabilities

### New Capabilities
- `checkpoint-storage`: Complete publication, immutable artifacts and explicit resume integrity.

### Modified Capabilities
None. Existing rl-evaluation compatibility/lineage requirements remain in force.

## Impact

Checkpoint storage, trainer setup cleanup, strict saved-step accounting reads,
behavioral tests and documentation.
No new dependencies, model initialization fallback, live game/training run,
save edits, reward/observation changes or checkpoint migration. Power-loss durability
and exact native-engine trajectory restoration are not claimed. Native damage/
revival evidence and broader qualification remain pending under existing changes.
