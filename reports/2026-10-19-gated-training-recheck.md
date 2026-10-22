# Evidence: gated training recheck v1

- Date/time and timezone: 2026-10-19, Europe/Amsterdam.
- Baseline: 530b73b, unrelated errors.txt preserved.
- Scope: operator-approved 512-new-step/five-minute real gated training check;
  plan docs/EXPERIMENT_GATED_TRAINING_RECHECK_V1.md.
- Observer: 0.5.0-dev, source/installed default-off exact match; no deployment.
- Python/config: existing locked Windows environment; fixed training-live-v1,
  seed 20, config hash 1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5.
- Budget: total target 4608 from t4096, five minutes, two-minute handoffs,
  zero faults, one natural-death restart under original finite approval.

## Results

| Requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Parent/config identity | Latest pointer, CheckpointPolicy load and verify_unchanged | 0 | passed | Exact t4096/seed20/hash match; source model hash unchanged |
| Closed-game preflight | launcher.preflight and process absence | 0 | passed | Exact ordinary default-off Lua/metadata; no game launched |
| Disk budget | Existing checkpoint tree | 0 | passed | 153.2561 MiB below existing 512 MiB cap |
| Runtime training/update | Approved CLI below; three fresh manual handoffs | not retained | passed | One completed 256-step update; target 512 only partially reached |
| Cleanup/new checkpoint reload | CheckpointPolicy load + verify_unchanged; operator control check | 0 | passed | Child t4352/normalizer reload; parent unchanged; approval removed after verified exit |

## Parent preservation

Parent 1f4a187e-s20-t4096 hashes:

- manifest: 3efed78de18950331436ede7351dfe464d2948e42d50a6151290b519565758cb
- model: 07c192e189dda062f547194fe1113d073170ddfbdfbb0aa50812f4ff7da308ca
- normalizer: 2e6cab8f7f676367968134508c0bc4fe5477376d48b36a9164d1fbdeb8d5d11d

Private preparation readback: reports/local/gated-training-recheck-v1/preparation.json.
No checkpoint, model, config or reward was changed in preparation.

## Real game and evaluation

No launch/connection/control yet. Initial slot/paused-room readiness remains
manual and must be current before automatic combat. No gameplay improvement
claim is made by preparation or by earlier synthetic acceptance.

## Limitations and continuation

Retain all failed attempts and partial samples honestly. One successful update
would establish only a narrow pipeline result; earlier double-start cause remains
unknown. Record actual approval expiry, session/epoch/frame and outcomes below.

## Approval preparation

Verified process absence again and exact source preflight before approval write;
there was no pre-existing local approval. One 15-minute approval was deliberately
created for this requested check, max_restarts=1, expiry
2026-10-19T08:39:36Z (10:39:36 CEST). No renewal on reconnect/handoff is allowed.
Private readback is reports/local/gated-training-recheck-v1/approval-summary.json.
Awaiting manual launch/file-2 paused combat readiness; no connection or training yet.

## Executed runtime result (supersedes preparation above)

Baseline execution revision be1f1f4; worktree contained unrelated errors.txt only.
Real run 10:25:25-10:30:19 CEST, private session
runs/live/sessions/20261019-102525-8750fb. Observer 0.5.0-dev, Lua 5.3,
no extender. Game version/build unavailable in hello; no unsupported version claim.
Operator confirmed ordinary save file 2; this is an authorized ordinary-profile
experiment, not an isolated training profile or progression acceptance.

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --confirmed-save-slot 2 --steps 4608 --minutes 5 --combat-gate --gate-wait-minutes 2 --max-faults 0 --seed 20 --resume --connection-timeout 20
```

| Segment | Identity | Resumed CEST | Decisions | Outcome |
|---|---|---|---|---|
| 1 | epoch 1, room visit 3 | 10:26:07 | 95 | empty, subsequently cleared |
| 2 | epoch 1, room visit 4 | 10:27:07 | 94 | natural death |
| 3 | epoch 2, room visit 1 | 10:28:10 | 77 | natural death; restart budget exhausted |

Each segment required fresh operator confirmation and a request/session/epoch/room
bound one-shot readiness after unpause. No readiness was granted for handoff 4.
First session 06da9d307a2c4d839c9ab95ac49f79fc, replacement session
92893a5d8dbd495c9b5a3e4f848ead1f. Native log records one scheduled/dispatched/
confirmed restart, attempt 1, epoch 1 -> 2; second death reports restart unavailable.
No forced resets or further restart/approval renewal occurred.

Native evidence: epoch 1 has 189 accepted actions, 189 releases, 50 tears;
epoch 2 has 77 accepted actions, 77 releases, 19 tears. First action frame 4534
at x=465.596,y=280; later frames/coordinates change. Epoch-2 final action frame
851 releases on transition at frame 853. Native peer disconnected afterward.
Raw native log and checkpoint verification are private inside the session folder.

Gate summary: 266 combat decisions, 4 handoffs/3 accepted, no readiness rejection,
260.797 seconds waiting, 5163 wait snapshots, 1 observation gap, 0 resume races,
0 withheld actions, outcomes empty=1/death=2. Observation gap is recorded rather
than hidden; no infrastructure fault was logged. Final stop is specifically
CombatGateExpired at the two-minute fourth handoff cap, 10:30:19.612, before the
original global deadline 10:30:25.689. Cleanup errors are empty. The generic CLI
budget message says wall time; the actual cause is the handoff cap.

One real RecurrentPPO update saved 256 samples: t4096 -> t4352. The remaining
10 samples were explicitly reported unsaved; no t4608 checkpoint was produced.
The minimum pipeline criterion passes; the 512-new-step target is PARTIAL.
Private latest.txt points to 1f4a187e-s20-t4352, whose manifest parent is t4096.
CheckpointPolicy loaded model and VecNormalize and passed verify_unchanged.

Child SHA256:
- manifest: 9de9fe6b64c1c2ff5248a0dc264ae549ad7b3b36472d01fec9e07a918bfcfe87
- model: de0b6a02fbad81b534b1d7bc8472863b09ab651c9d462d15b352e833cd582217
- normalizer: f2e97a1e98166735cef7ed093ddbe48567bbbf591d10bf111b94578dfd136ffb

All three parent hashes above match after training. No reward/config/schema edits.
Operator confirmed working manual movement/shooting and no intervention during
combat, then confirmed normal game exit. Process absence was verified; only the
exact temporary authorization (expiry 1792399176, max_restarts 1) was removed.
Installed default-off Lua remains SHA256
ab68bc29955d89562fe98c1c19fc346c97c4f1df72853a631a365f8a46d794eb.

## Review, validation and next decision

Self-review: counts agree across gate, native actions/releases and checkpoint
accounting. One update and preserved lineage establish pipeline operation, not
improved play. Rooms were operator-selected; one seed and two deaths are not an
evaluation. Earlier unexplained double-start failure remains unresolved.
Full Windows Check.ps1 previously passed 1451 tests, zero skips/xfails for the
unchanged implementation (530b73b evidence). This continuation changes documents
only; no redundant full code test rerun. Pinned strict validation and diff checks
are recorded after execution below. No OpenSpec archive or wider RL acceptance.
Next: separately decide a finite experiment from t4352; no automatic additional
training, reset, evaluation or approval follows this result.

Validation: scripts/OpenSpec.ps1 validate --all --strict exited 0, 30/30; git diff --check exited 0. Training process emitted Live run finished and terminated; its numeric exit code was not retained by the resumed tool session. Acceptance relies on gate/accounting, native evidence and reload, not shell completion alone. Self-review found no code or private artifact included in this documentation diff.
