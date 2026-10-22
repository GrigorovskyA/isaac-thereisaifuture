# Evidence: same-client assisted combat rollout

- New user-requested finite attempt after the pause/setup/resume check. Existing seed-20 t4864 parent and config hash are required.
- One Steam launch, file-2 selection and Continue; one learner invocation targeting t5120/256 new steps, five minutes total, 90 seconds per handoff, zero tolerated infrastructure faults, one natural-death restart, 512 MiB training disk cap.
- Management navigation only inside CombatGateEnv's reset wait, through its existing LiveClient with the policy episode stopped. At most 80 navigation action/release commands, 45 seconds cumulative pulse time, four agent-inspected door plans, three stationary pulses stop. Each plan binds unique token/session/epoch/room, cardinal door, current visible normal-room geometry. No gameplay keyboard input.
- Navigation/wait data never passes env.step or reaches observations, reward accounting, normalizer or recurrent policy state. Readiness uses the existing token validation on a fresh combat snapshot.
- Initial paused-menu recovery may send Escape once through the pinned runtime. No production source/schema/reward/checkpoint changes; one-process private experiment subclass only, no shipping or archive claim.
- One invocation completed below. No automatic budget renewal or second invocation.

## Offline checks

- Private experiment code: `reports/local/assisted_rollout.py`; production source unchanged by this experiment. Python compilation passed.
- `python -m pytest -q reports/local/test_assisted_rollout.py`: five behavioral tests passed, exit 0, 1.85 seconds with workspace-local TEMP/TMP. Coverage includes strict context-bound plans, multiple fights through the real gate/backend/environment wrappers, navigation exclusion from normalizer/sample accounting, active-controller/budget rejection, and health-drop release/stop.
- An earlier invocation reached passing assertions but exited 1 on Windows system-TEMP cleanup (`WinError 5`). It is not counted as a passed invocation. No protection settings were changed.
- Full Check.ps1/OpenSpec checks were not rerun for ignored experimental helpers and evidence updates. No production acceptance or archive is claimed.

## Runtime results

| Check | Status | Evidence |
| --- | --- | --- |
| Launch/profile | passed | One Steam launch, PID 42052, visible file-2 selection/Continue; game v1.9.7.17, observer 0.5.0-dev, effective Lua access. Initial alive/paused state captured before learner setup |
| Resume lineage | passed | Seed 20, config `1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5`, parent `1f4a187e-s20-t4864`; no fresh initialization |
| Navigation to combat | passed | Existing learner connection, session `e1ffe4447c23468581ff9bc5b6b66755`, epoch 1/room 0 -> room 1. Agent inspected the starting-room image and chose its open right door. Nine management action/release pairs, no shooting or gameplay keyboard input. Fresh combat readiness accepted before policy resume |
| Policy collection | passed, partial target | One combat episode: 94 decisions, 312 game updates, six half-hearts lost, approximate enemy HP removed 20.5, one enemy killed of five spawned, terminal death; return -69.554. These are logged approximate metrics, not evidence of improved play |
| Natural-death restart | passed | One bounded restart, new session `5bff0d38b3ff4daf801fa1ce60bc65e3`, epoch 2/room 0, full three hearts. No menu restart or second learner invocation |
| Navigation after restart | passed, partial route | Agent inspected the new starting-room image and chose the ordinary left door. Eleven management action/release pairs reached room 1, classified empty. Last release was rejected during the room transition; no neutral acknowledgment is claimed for it |
| Search for next fight | failed target | Third room image/request was produced, but no third plan was submitted before the original second-handoff 90-second cap. Planning latency consumed much of this wait. No false readiness in the empty room |
| Gate cleanup/accounting | passed | Two handoffs, one accepted readiness, 94 combat decisions, zero rejected readiness, resume races, observation gaps, withheld actions or cleanup errors. Explicit reason: `CombatGateExpired: Operator wait cap expired without readiness`. Generic live budget log also says wall time reached; the specific handoff timeout is authoritative |
| PPO update/checkpoint | not_run | Only 94/256 rollout samples; 94 unsaved, zero checkpointed, no optimizer update or new checkpoint. Latest remains t4864 |
| Bounds | passed | 40/80 management action/release commands, 4.350/45 cumulative pulse wall seconds, three/four requested plans (two supplied), one/one death restart; total training tree 191,937,809 bytes, below 512 MiB. Original limits were not renewed |
| Input recovery | passed, agent check only | After learner exit, one menu Escape opened a visible pause menu; character alive with three hearts. Human manual-control recovery and human non-intervention were not independently confirmed |
| Closure/parent | passed | Normal window close and successful observer unload/game shutdown log; game process and port listener absent. Exact matching temporary approval removed by SHA256. Full parent model/normalizer reload, full identity equality, unchanged latest pointer and post-close source/installed observer preflight passed |

Learner session: `runs/live/sessions/20261019-233718-3f6b2a/`. Private artifacts:
`reports/local/assisted-rollout-20261019-233614/`, console
`reports/local/assisted-console.txt`, cleanup `reports/local/assisted-cleanup.json`.
Raw screenshots, approvals and checkpoints remain local/ignored.

Runtime timestamps: 2026-10-19 21:37:18.194–21:39:26.180 UTC (127.987 seconds).
Command: `.venv/Scripts/python.exe reports/local/assisted_rollout.py`, with
`ISAAC_HANDOFF_DIR` set to the fresh private artifact directory; exit 0 at the
handled handoff cap. Exit 0 is clean termination, not target completion.
Post-close `launcher.preflight` and parent `CheckpointPolicy` reload/identity
assertions exited 0. Final `git diff --check` passed.

## Interpretation and self-review

Same-client management navigation can now reach combat and cross another room
after a natural-death restart in this private agent-assisted experiment. It does
not establish unattended room planning, a completed PPO rollout, improved policy
quality or legitimate progression. The agent supplied visible door choices;
those choices were not learned by the policy. Navigation stayed inside reset
management, outside env.step and policy/normalizer/reward inputs; the offline
boundary tests exercise this separation.

The immediate remaining gap is reliable, prompt next-room planning across empty
rooms within the existing handoff budget. A future implementation needs its own
bounded OpenSpec scope and tests, preserving visited-room context and excluding
management data from learning. Do not lower the rollout size, change the config
hash, reset from scratch, or extend a consumed budget to disguise partial data.
No second run, deployment, Git write or archive followed this attempt.
