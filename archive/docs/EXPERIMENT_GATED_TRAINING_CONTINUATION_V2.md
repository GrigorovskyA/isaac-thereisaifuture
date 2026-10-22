# Experiment: gated training continuation v2

Status: APPROVED for one invocation by explicit operator response on 2026-10-19.
Budget: 512 new steps, five minutes, one natural-death restart. No renewal.
Date: 2026-10-19, Europe/Amsterdam. Baseline f82587c.

## Purpose and fixed scope

Check whether the accepted t4352 child can resume into additional completed real
combat updates under the same gate, without changing rewards, configuration,
model architecture, action repeat or restart limits. This is pipeline replication,
not evidence of improved play or autonomous navigation.

Proposed one invocation: at most 512 NEW steps, total target 4864; five minutes
including all waiting, reconnects and learning; each manual handoff at most two
minutes; zero tolerated infrastructure faults; at most ONE natural-death restart.
No automatic second invocation or permission renewal. Existing three-restarts-per-
ten-minutes ceiling remains applicable; the stricter one-restart approval applies.
One 15-minute temporary approval may be prepared only after an explicit operator
budget decision and closed-game recheck. It is not renewed on reconnect/handoff.

## Verified preparation

Exact parent 1f4a187e-s20-t4352 is latest; CheckpointPolicy loaded model and saved
normalizer and verify_unchanged passed. Seed 20; fixed training-live-v1 config
hash 1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5.
Parent model SHA256 de0b6a02fbad81b534b1d7bc8472863b09ab651c9d462d15b352e833cd582217.
Checkpoint tree 162.835 MiB, below unchanged 512 MiB cap. Approval absent; installed
default-off Lua matches the previous verified hash. Game process absent at check.
Private models/logs and unrelated errors.txt remain excluded from Git.

## Execution after operator decision

Operator launches manually with --luadebug, selects file 2 and manually enters a
small ordinary enemy room, pauses and releases keys. Verify current instance and
slot confirmation before connection. Each combat handoff needs fresh confirmation
and a one-shot readiness pinned to request/session/epoch/room. Instruct unpause
only after preparing that bounded helper. No input during automatic combat;
manual navigation is allowed only after neutral handoff and excluded from learning.

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --confirmed-save-slot 2 --steps 4864 --minutes 5 --combat-gate --gate-wait-minutes 2 --max-faults 0 --seed 20 --resume --connection-timeout 20
```

Preserve the parent. Save only complete updates (expected t4608 then t4864),
report partial/unsaved samples honestly. Stop on fault, deadline, readiness expiry
or operator cancellation; after second death no further restart is permitted.
No forced death/reset, save/Cloud/settings edit, spawn, screen capture, injected
desktop input, mod replacement while running or unattended supervisor.

## Acceptance and cleanup

Minimum: at least one complete real update from t4352 with correct lineage,
reloadable model/normalizer and unchanged parent. Record all combat outcomes,
waiting, native movement/shooting/releases, restart count, faults and unsaved steps.
Two updates are a target, never a reason to extend authority. Operator confirms
working controls and no combat intervention. Close Python/release; operator exits
normally before removing the exact temporary approval. Record actual process
exit status when available. No frozen evaluation or extra training follows.
The original unexplained double-start remains unknown even if this trial passes.

Approval prepared after closed-game preflight; expires UTC 2026-10-19T08:49:35+00:00. Manual launch/file-2 paused combat readiness pending. No training connection yet.
