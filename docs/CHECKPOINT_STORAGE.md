# Checkpoint publication and continuation

The trainer publishes into `checkpoints/` using an OS-released writer lock, a unique
`.pending-*` directory, completed-directory rename and atomic `latest.txt` replacement.
Model, normalizer and manifest are flushed before the directory becomes visible.
Published directories are never overwritten. Only the latest pointer selects a
checkpoint; directory scanning never adopts a staging or unreferenced candidate.

Storage manifest v2 includes SHA256 for both binary artifacts. Readers validate
them before heavy deserialization, alongside existing observation/action/reward,
configuration, seed and reward-contract compatibility. Existing v1 checkpoints,
including t7424/t6912, remain readable unchanged; v1 has no embedded hash guarantee.
Existing v1 directory aliases remain readable; strict pointer/manifest-name identity
applies to newly published v2 storage. Compatibility checks still apply to both.
This storage version does not reinterpret policy observations or alter config hashes.

A writer verifies current parent and increasing timesteps while holding its lock.
Competing or stale writers fail. The small `.writer.lock` file remains on disk;
the OS releases its lock when the process closes or dies. It is not a stale PID lease.

An initial publication into an empty root may explicitly record an external parent,
as before; it serializes the supplied model and does not load, recover or initialize
one. Missing latest in a root with completed history requires explicit recovery.
Windows sharing refusals on latest replacement have a one-second bounded retry;
persistent refusal preserves previous latest and reports failure.

A crash before publication leaves latest unchanged. A crash after pointer replacement
leaves a complete new checkpoint. Hard-killed staging folders and unreferenced
complete candidates remain ignored and count toward disk use. They are not deleted
automatically. A later completed save with the same timesteps uses a unique ID
suffix rather than overwriting an unreferenced candidate. If there was no previous
latest, resume fails explicitly; there is no automatic recovery or fresh-policy
fallback. Explicit fresh training also refuses existing unfinished artifacts.

Python/NumPy RNG and declared CPU Torch RNG are restored after the SB3 model,
optimizer and VecNormalize state load and before further learning. Failed heavy
restore closes the created environment. Tests verify actual optimizer tensors,
normalizer statistics, RNG state, another completed update and parent lineage on
the synthetic environment. Incomplete rollouts remain unsaved. A corrupt progress
read is a fault, never an invented zero saved-step count.
After worker shutdown the session runner independently rereads latest. A complete
publication is retained in final status even if its worker event was lost; the
manifest's write time supplies the recovered update timestamp. Failed final
readback is reported as a checkpoint fault, not a fabricated successful update.

This is process-interruption consistency, not a guarantee against power failure,
filesystem corruption or external mutation. It does not restore a native game
state or an interrupted partial rollout/RNN trajectory; a game restart begins a
new episode while retaining completed learning state. Native resume/damage/clear/
revival effects require separate finite game evidence and remain pending.
