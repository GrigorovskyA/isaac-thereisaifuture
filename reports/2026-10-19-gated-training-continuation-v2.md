# Evidence: gated training continuation v2

- Date/time: 2026-10-19, Europe/Amsterdam, 10:35:21-10:38:33 CEST.
- Revision: c973992; approved plan/STATUS edits only, unrelated errors.txt preserved.
- Scope: operator-approved one invocation, 512 NEW samples from t4352,
  five-minute global cap, two-minute handoffs, zero tolerated faults, ONE restart.
- Mod: 0.5.0-dev, Lua 5.3, no extender; game build unavailable in hello.
- Existing locked Windows Python environment, RecurrentPPO on CPU, seed 20,
  configs/training-live-v1.yaml; unchanged config hash
  1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5.
- Plan: docs/EXPERIMENT_GATED_TRAINING_CONTINUATION_V2.md.

## Results

| Requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Real gated updates | Approved CLI below | 0 | passed | 512 decisions, 512 saved, 0 unsaved; t4864 completed |
| Parent/config/resume | CheckpointPolicy load and verify_unchanged | 0 | passed | t4352 unchanged; t4352 -> t4608 -> t4864 lineage |
| Reload | Load both child models and saved normalizers | 0 | passed | Seed/hash/schema validation and verify_unchanged |
| Restart and readiness | Natural death, epoch 1 -> 2, fresh room confirmation | N/A | passed | One dispatch/confirmation; three fresh accepted handoffs |
| Native actions/release | Private native log | N/A | passed | 512 accepted, 512 releases, 127 tears |
| Cleanup | Operator control check and normal exit, exact approval unlink | 0 | passed | No stuck controls, no combat intervention; process absent |

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --confirmed-save-slot 2 --steps 4864 --minutes 5 --combat-gate --gate-wait-minutes 2 --max-faults 0 --seed 20 --resume --connection-timeout 20
```

## Real game

Operator manually launched Isaac (PID 6028, start 10:34:45), selected file 2,
staged ordinary enemy rooms paused and confirmed released keys. Ordinary-profile
permission is specific to this bounded experiment, not training isolation or
achievement eligibility. Closed-game exact default-off mod preflight passed;
no deployment. One approval prepared 10:34:35, expiry 10:49:35 CEST, max_restarts=1;
never renewed through the restart or handoffs.

| Segment | Epoch / room visit | Start CEST | Decisions | End |
|---|---|---|---|---|
| 1 | 1 / 3 | 10:36:04 | 93 | Empty, subsequently cleared |
| 2 | 1 / 4 | 10:36:54 | 13 | Natural death |
| 3 | 2 / 2 | 10:37:49 | 406 | Sample target reached during combat; no terminal outcome claimed |

Session d18506ef49034bdf90b4e9650583399c has 106 native actions/releases,
26 tears. Replacement session d13356b26223467aa7cabe16dbdbda40 has 406
native actions/releases, 101 tears. Restart scheduled/dispatched once at attempt 1,
confirmed old_epoch=1 new_epoch=2. Each readiness required explicit operator
confirmation plus bounded unpause helper pinned to request/session/epoch/room.
No second restart or automatic future readiness. Native frame/coordinate records
are retained privately in runs/live/sessions/20261019-103521-9b419f.

Gate summary: 3 handoffs/3 accepted, no rejections, 133.547 seconds waiting,
2656 wait snapshots, one observation gap, zero resume races or withheld actions.
No infrastructure fault logged; cleanup_errors empty. Final reason closed after
successful training_result completed, elapsed learner time 188.906 seconds.
512 combat decisions saved across two updates; zero partial samples lost.
No manual waiting/navigation samples were intentionally used for learning.
Operator confirmed no combat intervention and functioning movement without stuck
controls, then normal exit. Process absence verified before removal of the exact
approval (expiry 1792399775, runtime_authorization live-training-20261019-103435).

## Checkpoints and preservation

Latest points to 1f4a187e-s20-t4864. Heavy model and VecNormalize reload passed for
parent and both children. All parent hashes match the prior verified report.
Child lineage and SHA256 recorded privately in verification-private.json.

- t4608 parent t4352; model SHA256
  e5f1ee052514f206ad9e1910b440d37a8e9944380cbd56cfd1589d1360fb7ec0.
- t4864 parent t4608; model SHA256
  055bba9a3326c87febf296b44d58cf0d851f158a8ae9d2a1ad820320f2cbe4c6.
- t4864 normalizer SHA256
  8cb23fedc3f7274e474e4cb6f9bceff3f0419a7eff01d5b8e9753c6b1a96641c.

## Shooting observation

Of 512 native commands, 117 selected shoot=none (22.85%); command intervals have
100 ms median in each epoch. This supports the presence of policy-selected
shooting pauses, not a measured tear-rate defect. Short expiry/reissue gaps and
actual MaxFireDelay were not isolated by this run. No stat, weapon, firing delay,
reward or action-repeat modification was made. The native tear count alone is
not a maximum-fire-rate benchmark. A future bounded diagnostic must distinguish
policy choices, input duty cycle and the character's natural cooldown.

## Evaluation, review and continuation

One seed, operator-selected unmatched rooms, one death, one cleared segment and
one nonterminal segment are insufficient to establish gameplay improvement.
Reward -84.64966666666837 is an approximate training label, not a success metric.
The original unexplained double-start failure remains unknown. This completes
only the declared bounded continuation pipeline check; wider roadmap acceptance
and OpenSpec archive do not follow automatically.

Self-review: native counts equal gate decisions and checkpoint accounting;
parent is preserved, fresh readiness and original finite budget respected.
No new implementation, reward or private data is included in the Git diff.
Unchanged implementation previously passed full Windows Check.ps1 (1451 tests,
zero skips/xfails); this documentation-only continuation does not rerun it.
Pinned strict OpenSpec and git diff checks are recorded below. Next: inspect
shooting duty cycle offline, then separately choose a bounded diagnostic or frozen
model evaluation; no automatic further training or runtime approval.

Validation: pinned scripts/OpenSpec.ps1 validate --all --strict exited 0 (30/30); git diff --check exited 0. Documentation diff self-review completed; no archive.
