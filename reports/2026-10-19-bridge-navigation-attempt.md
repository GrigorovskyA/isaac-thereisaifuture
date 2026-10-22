# Evidence: bounded bridge navigation attempt

- User requested the agent to try reaching combat itself after the held-menu check.
- One Steam launch; agent-inspected file-2/Continue menu route. Existing seed-20 t4864 parent must remain the resume source.
- Navigation budget: one live connection, 30 seconds after connect, at most 14 movement commands of at most 15 requested frames, plus bounded final release (at most 16 total commands); no shooting. Stop on first room change, combat, damage, death, pause, epoch change, transport failure or three stationary results. Do not restart the navigation budget.
- If confirmed combat is reached: one gated continuation, at most 256 new samples/t5120, five minutes, one-minute waits, zero tolerated infrastructure faults, one natural-death restart, 512 MiB disk budget. No follow-up run or automatic renewal.
- Navigation is management assistance outside model input, reward, normalizer and training rollout; it is not learned exploration or evaluation evidence.
- No production code, save/Cloud/Steam options or third-party mods changed. This is a new finite attempt after the user's new request, not an automatic extension of the prior completed budget.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Parent/preflight | passed | t4864 model/normalizer/manifest reload and identity checks before launch and after cleanup; source/installed observer hashes match |
| Authority and launch | passed | One new 15-minute approval, max_restarts=1, no pre-existing file overwritten; Steam PID 42336 with --luadebug; file 2 visibly highlighted, selected and Continue used |
| Structured navigation | passed for one transition | Private LiveClient session `3391928ac39944a6ba82f790da934182`, epoch 1; five accepted down/no-shoot commands, requested frames=15 each; room visit 0 -> 1, no further movement issued |
| Actual movement | passed | Same-session observed y positions: 160 -> 209.59 -> 272.58 -> 336.54 -> 402.60, then entry at y160 in room 1. This is movement evidence, not exact consumed-update evidence |
| Navigation stop/cleanup | partial | Stopped on the first transition/paused snapshot at frame 22592, within about two seconds of movement. Final release returned rejected during transition; no neutral acknowledgement is claimed. The client then disconnected. Source transition/disconnect cleanup and normal game closure remain distinct from a release acknowledgement |
| Destination | passed visually; gate readiness not confirmed | Snapshot capture showed a different room containing enemies. No fresh stable `combat` classification was acknowledged in the training connection |
| Natural game over | observed | Next capture showed Game Over; game log records `Killed by (10.1)` after navigation disconnect. The character entered with one heart. No forced reset or menu restart was sent |
| Training connection/resume | passed startup only | New session `abb8aac6cf4b4127a93a2e3ef524131c`, same epoch 1/room 1, configured seed 20 and resume to target t5120; gate classified paused and no readiness ack was sent |
| Learning target | not achieved | Zero decisions/reward/checkpointed samples/unsaved samples. No PPO update or new checkpoint. One handoff ended after 60.016 seconds; 1241 wait snapshots, 0 accepted readiness, cleanup_errors empty; CLI exit 0 |
| Restart | not_run | Approval armed a one-attempt live-loop limit after the logged game over, but no natural-death dispatch/confirmation was observed. No new epoch or second run was started |
| Final cleanup | passed | Normal WM_CLOSE from the observed game-over state, successful shutdown/unload logged, process absent after two seconds; exact approval hash matched before unlink; no listener on 9528 (only TIME_WAIT) |

Training command:

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --confirmed-save-slot 2 --steps 5120 --minutes 5 --combat-gate --gate-wait-minutes 1 --max-faults 0 --seed 20 --resume --connection-timeout 20
```

Private evidence is in `reports/local/bridge-nav-events.jsonl`,
`bridge-nav-output.txt`, `nav-*.png`, `nav-training.txt`, parent/approval identities,
and `runs/live/sessions/20261019-225844-8c599b`. No raw captures/models/private
authority are published. Menu input was used only before the run; all five
gameplay movement commands used the bridge. No gameplay keyboard input occurred.

## Interpretation and correction needed

The route to one adjacent room works without human menu selection or movement.
It is management assistance, not learned navigation or a completed automatic
training cycle. A new connection plus learner initialization left an uncontrolled
combat interval; the low-health character died before readiness. Do not infer
that live-loop restart must recover a game over that occurred before that
connection's death observation. Do not acknowledge a paused/game-over gate merely
because enemies were visible in an earlier capture.

Next implementation should close this gap: immediately pause at the first room
transition once a menu pause is valid, verify the pause, initialize/resume the
learner, then coordinate unpause and fresh same-session/epoch/room combat readiness
without tool-roundtrip delay. Prefer a single coherent session boundary where
possible. This requires its own offline contract and bounded runtime check, not
an automatic second run under the expired attempt.

Self-review: five movement commands plus one rejected release stay below the
16-command navigation budget. Navigation stopped after the first room change;
the budget was not renewed after death. No ack was fabricated, no transition was
counted as a policy sample, and t4864 remained byte-identical and loadable. There
was no human manual-control recovery test; normal shutdown is recorded separately.
Only private experiment helpers and evidence/status documentation were written;
no production diff or new tests. Full offline gate was not rerun for this report.
