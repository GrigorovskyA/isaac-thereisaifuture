# Experiment plan: conservative-v2 development baseline

Declared before execution on 2026-10-20, Europe/Amsterdam. User authorized
continued bounded learning and up to five natural deaths; the primary chooses
this explicit independent development lineage after the reward correction.
This is deliberate initialization, not a fallback from a failed resume.

## Lineage and purpose

Legacy `runs/live/seed-20/checkpoints/1f4a187e-s20-t8960` uses combat-v1.
It remains immutable and is not relabeled or imported. The new model starts
randomly, with new optimizer, recurrent state and observation/return statistics,
using `configs/training-live-conservative-v2.yaml`, seed20 and the existing
live-conservative-v2 reward contract. No warm start is claimed.

New output root: `runs/live-conservative-v2-development-20261020`.
Its absence is a mandatory preflight check for this single initial invocation.
Any future continuation must resume its exact latest compatible checkpoint;
missing/incompatible state stops. Never delete the output to recreate a model.
The old model is development history, not a baseline selected for gameplay quality.

Purpose: verify completed recurrent PPO updates/checkpoints and finite natural
death/restart behavior under corrected reward accounting. This is an integration
experiment, not a held-out evaluation, multi-seed comparison or final long training.
No improved play or completion rate can be inferred from this small seed20 sample.

## Finite execution

One Steam launch on authorized ordinary file2, explicit New Run after the native
diagnostic death, active Isaac verification from structured data before learning.
Existing Continue is protected by the menu helper. Listener precedes Steam.
No screenshots, save edits, seed commands, Cloud changes or unlocks.

- Maximum 4096 combat decisions/checkpointed timesteps; rollout256.
- At most five natural deaths and four in-game structured restarts; no forced deaths.
- Fifteen minutes controller time; twenty minutes outer wall time, covering launch,
  model setup and cleanup, with an absolute deadline recorded before dispatch.
- Approval lease18 minutes, max_restarts4, never renewed; expiry must fit outer cap.
- Output cap512MiB across assigned logs/checkpoints; check throughout execution.
- Infrastructure faults0, no recovery/retry or second invocation in this plan.
- Gate wait90s; cumulative navigation scale5:1280 commands,450 pulse seconds,
  twenty transitions, retaining existing health/stationary/room eligibility guards.
- Stop at any cap, refusal, unexpected session identity, non-Isaac initial player,
  source/config/parent mismatch or changed approval. Five deaths is a ceiling.

Prepared command:

```text
.venv/Scripts/python.exe -u -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-conservative-v2.yaml --seed 20 --steps 4096 --minutes 15 --max-faults 0 --combat-gate --auto-navigate --gate-wait-minutes 1.5 --navigation-budget-scale 5 --max-deaths 5 --confirmed-save-slot 2 --connection-timeout 90 --out-dir runs/live-conservative-v2-development-20261020
```

The initial command intentionally has no --resume under this explicit plan.
The worker executes only the primary's frozen helper, manifests and exact command.
It cannot change configurations, create another lineage or renew budgets.

## Acceptance and cleanup

Close only the owned game normally immediately after runtime; release controller
resources and remove only the unchanged exact owned approval. Preserve partial
rollout accounting, every episode and any fault. Record actual seed/session/epoch,
deaths/restarts, completed updates, saved and unsaved decisions, normalizer counts,
model/checkpoint/reward/config hashes and parent/latest chain. Verify legacy
model/manifest/normalizer/latest byte identity independently.

A native phase/champion audit passed with the revised journal but did not observe
the user's red revival enemy. That unresolved scenario remains explicit; no
hard-coded tactic or claim of fixing that mechanic precedes this experiment.
Results will be recorded separately; this plan is not evidence of execution.
