# Evidence: bounded held menu input and optional training continuation

- User requested this attempt after the proposed file-2 startup check and 256-new-step/five-minute continuation.
- Budget: one Steam launch, up to five minutes menu setup, at most 20 menu presses/captures; if startup and combat readiness pass, one training invocation capped at 256 new steps (t4864 to t5120), five minutes wall time, one minute per combat handoff, zero tolerated infrastructure faults, at most one natural-death restart, 512 MiB training disk budget. No renewal or second training invocation.
- Input: private local menu-only SendInput helper, scan codes, 300 ms hold, foreground guard and finally key-up. No Computer Use UI calls are mixed into this attempt. Gameplay stays on the structured bridge.
- No save/Steam Cloud/Steam option edits, mod deployment, forced live reset, delegation or publication.
- Parent: seed 20, `1f4a187e-s20-t4864`; config SHA256 `1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5`. Existing model/normalizer/manifest reload and exact identity check passed before and after the attempt.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Closed-game preflight | passed | Source/installed observer files match, no existing Isaac instance; no deployment |
| Temporary authority | passed | One deliberate 15-minute approval, max_restarts=1, created only after verifying no existing approval would be overwritten. Its evidence string accurately identifies an agent menu check rather than an operator attestation |
| Steam launch | passed | `steam://rungameid/250900`, one PID 2444, command line confirms existing `--luadebug`; v1.9.7.17, observer 0.5.0-dev |
| Held menu input | passed | Scan-code Enter with 300 ms hold skipped startup; next Enter reached FILE SELECT; Right visibly highlighted FILE 2; Enter selected it; Continue was enabled and selected; next Enter loaded the existing run |
| Slot evidence | passed, UI only | Agent inspected FILE 2 highlight and selected it. The bridge still has no save-slot attestation API |
| Read-only attach | passed | `cli observe --samples 10 --accept-timeout 60 --message-timeout 3 --reconnects 0`: exit 0; session `5b4592a2042547bd92bc5cba4094be3f`, epoch 1, 10 active snapshots. These initial load-boundary samples shared frame 19548/update 0; do not claim advancing-frame evidence from that slice |
| Live training startup | passed | Invocation below connected with `live_loop_v1`, loaded seed-20/config continuation, and entered the real combat gate; session `8051313096754358abaaccab6cb0a00c`, epoch 1, room visit 0 |
| New training samples / PPO update | not_run | Gate classified the room `cleared`; no readiness was acknowledged, zero combat decisions, zero reward, zero checkpointed or unsaved steps. The 256-new-step target was not reached |
| Bounded gate termination | passed | One handoff expired after its original 60-second cap; 1239 waiting snapshots, 0 room changes, 0 observation gaps, 0 accepted readiness, cleanup_errors empty. CLI exit 0; the generic budget log's wording does not mean the global five-minute cap was used |
| Input recovery | passed, agent menu check only | After live client exit, held Escape visibly opened the pause menu. No human manual-control test or absence-of-human-intervention claim was obtained |
| Cleanup | passed | Normal WM_CLOSE from the pause menu; successful shutdown and observer unload in game log; process absent after two seconds. Exact temporary approval hash matched before unlink; no listener on 9528 (only TIME_WAIT sockets) |
| Parent preservation | passed | Latest still t4864; checkpoint identity including model, normalizer and manifest hashes matches the initial readback; all artifacts reload unchanged |

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --confirmed-save-slot 2 --steps 5120 --minutes 5 --combat-gate --gate-wait-minutes 1 --max-faults 0 --seed 20 --resume --connection-timeout 20
```

Private evidence: `reports/local/held-menu-*.png`, `held-menu-observe.txt`,
`held-menu-live.txt`, checkpoint/approval identity files, and
`runs/live/sessions/20261019-225334-0e0a9c`. No screenshots, private authorization
content or model data are added to tracked project artifacts.

## Scope and interpretation

The successful mechanism differs from the failed Computer Use attempt in both
scan-code injection and hold duration, so this is not a controlled experiment
proving which difference caused the earlier failure. It verifies one practical
menu route with agent-inspected screenshots. The helper is a private experiment,
not a delivered unattended runner, general menu recognizer or gameplay controller.
No production behavior, reward, threshold, model format or dependency changed;
no new unit test or full offline gate is warranted for this report-only result.

The proposal's conditional training phase reached startup but found no eligible
combat, so there was no optimization or gameplay-quality evaluation. No navigation,
enemy spawning, new run, forced reset or restart was attempted. No automatic
second invocation or renewed approval is authorized by this completed budget.

Next concrete work: bounded structured-bridge navigation from the current clear
room to eligible combat, kept outside the learning rollout, with fresh gate
readiness. Successful file-2 startup does not solve that transition or establish
continuous training. The native exact-event/step contracts remain separately open.

Self-review: all six held keys were menu actions (startup Enter twice, Right,
file-selection Enter, Continue Enter, final Escape); nine screenshots and one
launch stay below the declared caps. Release was in finally on every key press.
No physical manual-control recovery is claimed. Training sample target is
explicitly not achieved rather than inferred from exit 0 or model loading.
