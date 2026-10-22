# Experiment: gated training recheck v1

Approved exploratory check: 2026-10-19, Europe/Amsterdam. The operator requested
the proposed 512-new-step/five-minute check after Windows IPC acceptance. This
plan supersedes the NOT AUTHORIZED draft only for this one invocation. Baseline
530b73b, Windows Check.ps1 1451 passed/zero skips or xfails, strict OpenSpec 30/30.

## Parent and budgets

- Verified latest parent: 1f4a187e-s20-t4096, training seed 20, unchanged model,
  manifest and normalizer, load and verify_unchanged passed.
- Fixed configs/training-live-v1.yaml, config hash
  1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5.
  No schema/reward/hyperparameter/action-repeat changes.
- At most 512 NEW samples: CLI target 4608 TOTAL timesteps, explicit resume,
  no fallback to a new model. Two complete 256-step updates are the target.
- At most five minutes including combat, operator waits, pauses and reconnects;
  each handoff at most two minutes; zero tolerated infrastructure faults.
- One deliberately prepared 15-minute local approval while closed, at most ONE
  natural-death restart for this mod load. No renewal on reconnect or handoff.
- Existing disk cap 512 MiB; parent tree currently 153.2561 MiB. Preserve all
  resulting checkpoints and parent, including unsuccessful/partial outcomes.
- No forced death/reset, health/save edit, enemy spawn, Steam Cloud/settings
  change, desktop input, screen capture, unattended supervisor or extra run.

## Manual launch and combat readiness

Operator launches with --luadebug, selects file 2 and Continue, stages a small
ordinary enemy room paused, then confirms released keys. Primary verifies the
current process and unexpired approval, connects the gate in neutral wait and
prepares one short-lived readiness helper pinned to request/session/epoch/room.
Only then instruct operator to unpause. No automatic readiness for later rooms.

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --confirmed-save-slot 2 --steps 4608 --minutes 5 --combat-gate --gate-wait-minutes 2 --max-faults 0 --seed 20 --resume --connection-timeout 20
```

No operator game input during automatic combat. After clear/empty/death/timeout,
the gate releases and enters a handoff. Only in that neutral state may the
operator navigate manually, pause in another ordinary fight and confirm again.
Each handoff needs fresh provenance-bound readiness; manual wait/navigation is
excluded from learning. A second death cannot restart under this approval.

## Success and cleanup

Minimum pipeline success: at least one completed real gated PPO update and a
reloadable child checkpoint preserving parent lineage/normalizer. Target t4608
does not override any deadline. If the run expires before an update, report
unsaved samples and zero completed checkpoints honestly. Record every segment,
death, handoff, fault and operator intervention; keep raw/oracle logs private.

After stop, close Python/release, obtain manual control confirmation and verify
new artifacts/parent unchanged offline. Operator exits normally before removing
this temporary approval. No additional training or frozen evaluation is automatic.
No mod deployment is needed: Lua/source already match with diagnostics OFF.

The earlier double start is still unexplained, and one successful death/reconnect
plus synthetic tests does not prove stability. This is a bounded pipeline check,
not a performance evaluation: one seed, unmatched operator-prepared rooms and
approximate reward labels cannot establish improved play or autonomous navigation.
