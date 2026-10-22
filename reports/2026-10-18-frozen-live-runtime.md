# Evidence: frozen live pilot preparation

- Date/time: 2026-10-18, Europe/Amsterdam; preparation approximately 17:38 CEST.
- Revision: f91ce3d; unrelated untracked errors.txt preserved.
- Scope: first real eval-live check, not training or comparative evaluation.
- Scenario: intended ordinary-profile file 2; current manual readiness pending.
- Policy: checkpoint 1f4a187e-s20-t256, training seed 20; repeat 3.
- Budgets: at most 256 decisions / two minutes, zero tolerated faults. A deliberate
  15-minute approval expires at 17:53:37 CEST and allows at most one natural-death
  restart in the game launch. No automatic renewal.

## Results

| Check | Command/scenario | Exit | Status | Evidence |
|---|---|---|---|---|
| Closed game | Process guard | 0 | passed | No isaac-ng process |
| Installed files | Compare source and installed SHA256 | 0 | passed | Both observer files match |
| Preflight | launcher --preflight-only | 0 | passed | No game launch |
| Frozen policy readiness | CheckpointPolicy load, fabricated zero vector, verify_unchanged | 0 | passed | Correct manifest seed/hash; no game connection |
| Explicit approval | write_training_approval(hours=0.25, max_restarts=1) | 0 | passed | Local only; current manual slot confirmation required |
| Real eval-live | Awaiting manual launch/readiness | — | not_run | No socket or actions started |

## Real game and limitations

No game was launched, attached or controlled in preparation. The user authorized
the proposed short frozen-model check. Launch, file-2 selection/Continue and
normal exit remain manual. No saved model was modified, training started, game
save/Cloud changed or observer redeployed. The existing smoke model has only 256
training steps; this pilot can establish inference plumbing, not improved play.

Next: fresh manual file-2 readiness, verify original approval remains sufficient,
then eval-live with the explicit checkpoint/config hash and the declared caps.
Assistance defaults unknown; any operator input must be reported. Do not silently
renew authority if preparation expires before readiness.

## Real pilot result: passed inference pipeline

The operator confirmed readiness on file 2. Precheck found exactly one Isaac
process, both mod hashes still matched and the original approval had 823 seconds
remaining. It was not renewed. Command (exit 0):

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli eval-live --policy checkpoint --checkpoint runs/live/seed-20/checkpoints/1f4a187e-s20-t256 --expected-config-hash 1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5 --expected-training-seed 20 --policy-seed 20 --steps 256 --minutes 2 --accept-timeout 20 --max-faults 0 --operator-assistance unknown --confirmed-save-slot 2
```

Actual window: 17:39:56–17:40:24 CEST, approximately 27.64 seconds from
configuration to summary. Session ac530d23ff6d4515bdefddde3d0b8576, epoch 1,
observer 0.5.0-dev, Lua 5.3, extender absent; game build fields unavailable.
Frames advanced from 74737 to 75539. Result: completed/step_cap, 256 attempted,
256 completed, zero faults, one final partial segment explicitly logged as
stopped with 256 steps. No episode clear, death or restart was observed.

Session-filtered actual Lua records independently show 256 accepted actions,
66 tears, 255 expiry releases and one transition release. Accepted-action
positions span x=270.0000..328.5797, y=130.0523..400.0. Final action sequence
256 at frame 75536 expired at frame 75539; Peer disconnected follows. No listener
remained on port 9528 (empty query output is expected, not a runner failure).

The runner reports identity_valid=true; manifest/model/normalizer hashes match
the prior training evidence. No learn or checkpoint-save operation ran. Raw
oracle log is empty and reward is zero; this window provides no combat-quality
evidence. The model selected left/up 244 times out of 256; this concentrated
behavior is retained as an unfavorable observation, not improvement evidence.

Private evidence: runs/eval-live/sessions/20261018-173956-7b9aa7, live.jsonl,
oracle.jsonl and runtime-readback.json. Nothing private is uploaded. The CLI label
was unknown at start. After the stop the operator explicitly confirmed manual
control works with no hangs and that no game keys were pressed during the pilot.
Evidence therefore records operator-declared unassisted operation retrospectively;
there is no automatic physical-input attestation and the raw log is not edited.

## Acceptance and continuation

Real frozen-runner task 4.3 passes for one bounded inference pilot. Together with
1329 passing Windows tests and strict 27/27 this completes the runner change's
declared scope. This is primary self-review, not independent review. It does not
complete a random-policy comparison, confirmatory experiment, repeated-restart
test or combat-training milestone. Next: predeclare a meaningful learning and
evaluation experiment with comparable exposure; a 256-step smoke model is not
a capable player. No new run, training or authority renewal follows automatically.

The completed runner change was archived with pinned OpenSpec (exit 0), producing
2026-10-18-frozen-live-pilot-v1. The generated baseline Purpose placeholder was
replaced with the actual capability purpose before final strict validation.
