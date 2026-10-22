# Evidence: user-prepared paused combat resume

User manually launched Isaac, selected file 2, entered combat and confirmed pause.
One learner invocation is authorized: resume seed-20 t4864 with unchanged config,
256 new samples (target t5120), five minutes total, 90 seconds per gate wait,
zero tolerated infrastructure faults, one natural-death restart, 512 MiB disk.
Use the previously boundary-tested private same-client manager. At most four
agent-inspected normal-room door plans, 80 action/release commands and 45 pulse
wall seconds. Stop on three stationary pulses or unsupported geometry. Menu keys
only; gameplay uses the structured bridge. No deployment, schema/reward changes,
fresh initialization, second invocation or budget renewal.

Initial screenshot shows pause menu, three hearts and live enemies in a narrow
room; game PID 36960, v1.9.7.17. Installed observer main.lua/metadata match source.
Parent model/normalizer fully reload and match the recorded t4864 identity.
Temporary approval created only after proving no existing approval was present;
exact path/hash retained for cleanup.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Initial bridge check | passed | Read-only capture of paused/alive session `158ed209c3c34a26b145f55ee39bca2d`, epoch 1/room visit 3/frame 3387; no movement command. File-2 identity relies on the user's selection/confirmation and standing authorization, not independent slot attestation |
| Learner handoff | passed | New connection `ed9f368b89ce48e1a9e8b574ab93ec09`, same epoch/room. Manager sent one menu Escape, observed fresh combat, supplied existing request-token readiness and gate accepted. Initial wait 1.469 seconds |
| Training | passed | 256 combat decisions, one complete rollout, target total 5120, 29.594 learner seconds, stop reason completed, process exit 0. All 256 checkpointed, zero unsaved. No navigation command or death restart needed |
| Gate integrity | passed | One handoff/accepted readiness; zero rejected readiness, room changes, resume races, observation gaps, withheld actions or cleanup errors. No terminal outcome was recorded before budget completion; no cleared-room or won-episode claim |
| PPO update | passed | Full parent/child model reload: saved PPO `_n_updates` 76 -> 80, 20 policy parameter tensors changed; all saved policy tensors finite. This verifies an actual training update, not improved play |
| Lineage/normalizer | passed | Latest `1f4a187e-s20-t5120`, manifest parent `1f4a187e-s20-t4864`, unchanged seed/config/schema versions. Full parent identity still matches. Normalizer count 4868.0001 -> 5125.0001 (256 steps plus reset observation); child model and normalizer reload successfully |
| Bounds | passed | One invocation, 256/256 steps, < five minutes; zero/one restarts, zero navigation plans/commands, training tree 201,986,146 bytes < 512 MiB. No budget renewal |
| Input recovery | passed, agent check | After learner exit, menu Escape opened visible pause menu. Character alive with three hearts and enemies still visible. Human control recovery/non-intervention not independently confirmed |
| Cleanup | passed | Exact matching temporary approval removed after SHA256 comparison; no port-9528 listener. User-launched game deliberately remains open on pause for the user; no additional training/action loop remains running |

Command: `.venv/Scripts/python.exe reports/local/assisted_rollout.py` with fresh
`ISAAC_HANDOFF_DIR=D:\isaac\reports\local\manual-paused-20261020-062304`.
Learner log: `runs/live/sessions/20261020-062304-f2c864/live.jsonl`.
Local verification: `reports/local/manual-20261020-verification.json`.
Initial paused bridge state, console and final paused image remain under
`reports/local/manual-20261020-*`; raw artifacts and checkpoints remain ignored.

Child model SHA256:
`bb5b717066b1707f8c9ac449f3ab004d37b39e3260c166cbe9bec7f715bfbe7c`.
Child normalizer SHA256:
`47eb78d0da87518c68c2695e45fa9b6dd7b6234d6a2b79c7510035d137e808b5`.

## Checks and limitations

Parent/child reload, lineage, finite parameter and changed-weight assertions,
normalizer count, and exact approval cleanup ran through the project Python and
passed. Final listener check and `git diff --check` passed. A combined shell call
returned 1 because Get-NetTCPConnection found no listener; its preceding Python
assertions completed successfully and emitted the saved verification result.
Full Check.ps1, synthetic smoke and OpenSpec verification were not rerun: this
attempt changed only evidence/status documentation and reused the previously
tested ignored helper. No production implementation, deployment or archive.

Self-review: this establishes a bounded real-game PPO continuation from t4864
to t5120, with user-prepared combat and agent-coordinated unpause/readiness. It
does not establish improved gameplay, room clearance, progression, general
navigation or unattended operation. The initial narrow-room geometry was never
fed to the private normal-room navigation helper because no navigation occurred.
Approximate combat reward -0.274333 is not a quality assessment. Next work remains
bounded next-room planning across encounters, followed by separate evaluation.
