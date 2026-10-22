# Evidence: combat-gated-continuation-v1

- Date: 2026-10-18, Europe/Amsterdam.
- Baseline: 18a1294 plus experiment preparation; errors.txt preserved.
- Plan: docs/EXPERIMENT_COMBAT_GATE_V1.md.
- Parent: 1f4a187e-s20-t4096, seed 20; target 6144 total timesteps.
- Budget: ten-minute training cap, two-minute handoffs, zero tolerated faults;
  separate original approval at most 20 minutes/three natural-death restarts.
- Runtime result: not_run; manual launch and paused-room readiness pending.

## Preparation

The operator explicitly approved the experiment and confirmed full normal exit
when the previous authorization had less than a minute left. No action/training
was started under the expiring authorization. Closed-game preflight, parent
readback and the deliberate new bounded approval are recorded below after checks.
Private raw logs, approvals and model files remain outside Git.

Closed-game checks passed (exit 0): no Isaac process, installed/source observer
hash match via launcher preflight, exact latest parent t4096, config/seed match,
model hash unchanged and verify_unchanged passed. Existing models occupy
153.2561 MiB. Deliberate new approval expires 2026-10-18T21:32:37+02:00 and
permits at most three natural-death restarts for the game launch. No launch,
connection or training occurred in preparation. Manual file-2 paused readiness
is required before the run; original approval is not renewed on later handoffs.

## First real attempt: interrupted before any update

- Window: 2026-10-18 approximately 21:13:37–21:16:12 CEST.
- Revision: 7db8ed4; exactly one game process. Original approval had 1140 seconds
  remaining at precheck, max_restarts=3, not renewed.
- Expected latest parent was explicitly checked at t4096 before connecting.
- Command (exit 0 for bounded stop, NOT experiment success):

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --confirmed-save-slot 2 --steps 6144 --minutes 10 --combat-gate --gate-wait-minutes 2 --max-faults 0 --seed 20 --resume --connection-timeout 20
```

| Requirement | Status | Evidence |
|---|---|---|
| Real initial readiness/combat | passed | Accepted exact paused-room request; 12 native actions, 3 tears, 12 releases |
| Real completed PPO update/checkpoint | failed | 0 checkpointed timesteps; 12 unsaved steps; latest remains t4096 |
| Post-death wait and bounded stop | passed | Input released, no further actions; two-minute handoff cap stopped |
| Continued live capability after restart | failed | New epoch observed, later Too many capabilities refusal and unavailable state |
| Original model preservation | passed | t4096 model hash unchanged; verify_unchanged/load passed |
| Cleanup | passed | Process returned; operator confirmed responsive manual control |
| Gameplay improvement | not_run | No new trained checkpoint to evaluate |

Actual observer 0.5.0-dev, Lua 5.3, extender absent; game build fields unavailable.
Session 6d195c65b73b43a5b52ed8d9cf8916a1, epoch 1, room visit 1. Initial readiness
accepted at 21:14:10.695, combat resumed at 21:14:10.735. Death followed after
12 steps/40 updates, at 21:14:12.102. Approximate labels recorded 3.5 enemy HP
removed, two half-hearts player damage, three initial enemies and one death.

One native restart was scheduled/dispatched as attempt 1 and confirmed epoch
1→2. The gate resumed neutral waiting; no second readiness was submitted.
The operator confirmed another enemy room on pause, but the request had lost
fresh observation/provenance, so primary readiness preparation refused it.

The preserved native log shows two new-game starts after the death, but only
ONE logged bridge restart dispatch. The operator explicitly states that only
automatic restart occurred and no menu/New Run/Continue action was performed.
Do not attribute the extra start to manual input. The log later records the
capability/protocol fault Too many capabilities at Lua main.lua:650. This proves
the new negotiation was refused; it does not prove WHY authority was unavailable.

Source review: capabilities depend on active state and current in-memory approval;
normal PRE_GAME_EXIT clears approval unless live restart.awaiting is set. This
is a hypothesis for the refusal, not a confirmed root cause. Current telemetry
does not expose the exact pre-exit state, approval invalidation branch or reason
for the extra game start. The preserved log loads the observer script and core
game scripts; source search finds one restart dispatch site. No conflicting mod
or duplicate dispatcher has been established from these observations.

The handoff remained bounded and ended at 21:16:12.140. Gate summary: two
handoffs, one accepted readiness, 150.156 seconds of total wait, 1341 wait
snapshots, two observation gaps, 12 combat decisions. Rollout accounting reports
checkpointed_timesteps=0 and unsaved_steps=12. No pending samples are claimed as
a trained update. The final prior-action release was at frame 12792 before restart.

## Evidence preservation and outcome

Private directory: runs/live/sessions/20261018-211337-172319, including live.jsonl,
oracle.jsonl, copied game-log-after-failure.txt and failure-readback.json. Raw
logs, seeds, models and approval files are not uploaded. The parent checkpoint
1f4a187e-s20-t4096 and its known model hash remain unchanged. No t4352 checkpoint
was created. No configuration, Lua, dependency, reward or authorization rule
was changed; no game process was stopped or launched by tooling.

Primary self-review, not independent review: this experiment FAILED its primary
pipeline criterion of a real gated PPO update. The cap/cleanup passed, but shell
exit 0 must not conceal the failure. No automatic retry, approval renewal,
checkpoint migration or declaration of improved gameplay follows.

Next: offline investigation and narrow lifecycle diagnostics for the extra
game-start/authority loss, reproducing the exact automatic restart + operator-wait
sequence. Preserve invalidation on genuine normal exits, original expiry and
restart attempt limits. Do not re-read or re-arm approval to make the failure
disappear. Another actual training run waits until this blocker is understood.
