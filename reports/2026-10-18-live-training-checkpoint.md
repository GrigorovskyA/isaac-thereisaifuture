# Evidence: first real live training checkpoint

- Date/time and timezone: 2026-10-18 16:29:08–16:29:40 CEST.
- Git revision: fd1bb14; unrelated untracked errors.txt preserved.
- Change: live-training-loop, task 5.5; one short real-game training pipeline check.
- Runtime: Repentance+, installed observer 0.5.0-dev, Lua 5.3, no extender.
- Python/packages: existing pinned Windows environment, Python 3.12.14.
- Configuration hash: 1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5.
- Scenario: operator-confirmed ordinary-profile file 2, continuing epoch 2.
- Budget: RecurrentPPO CPU, seed 20, one 256-step rollout, two-minute maximum,
  max_faults=0, existing 512 MB disk cap. Original 15-minute approval and three
  restart attempts were not renewed. No game launch, forced reset or save edit.

## Results

| Requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Original approval | Remaining time readback before training | 0 | passed | 227 seconds at preparation; >150 required immediately before run |
| Real training | Command below | 0 | passed | completed, 256 timesteps, 27.812 seconds of trainer elapsed time |
| Applied actions | Session-filtered Lua records | 0 | passed | 256 accepted actions, 66 tear records, 256 release records |
| Checkpoint persistence | latest pointer, manifest, model, normalizer | 0 | passed | checkpoint 1f4a187e-s20-t256; sizes/hashes below |
| Checkpoint reload | Compatibility check; RecurrentPPO.load; own saved normalizer readback and offline prediction | 0 | passed | 256 timesteps, normalizer count 257.0001, valid action [2,0] |
| Input release | Final command expiry and peer disconnect | 0 | passed | Sequence 256, frames 7999→8002, followed by Peer disconnected |
| Policy improvement | No comparative evaluation | — | not_run | Pipeline check only; no learning-quality claim |

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --confirmed-save-slot 2 --steps 256 --minutes 2 --max-faults 0 --seed 20 --connection-timeout 20
```

## Real game

Actual session c22a9c1470a64e0bbab55881a6a3b006 negotiated live_loop_v1 with
observer 0.5.0-dev. The game received the model's native actions. No death or
restart was required in this short training run. The policy update and saving
completed within the declared budget. The oracle log is empty in this window;
there is no claim of combat learning. All eight previous integration segments,
including the failed/death segment, remain in private logs and summarized evidence.

This is a real-game checkpoint, distinct from earlier synthetic PPO checks.
The reload prediction used one fabricated zero observation offline, with the
saved normalizer and recurrent model; it sent no action to the game and is not
a replay/evaluation of the learned policy in Isaac.

## Checkpoint

Private directory: runs/live/seed-20/checkpoints/1f4a187e-s20-t256.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| model.zip | 9941271 | ded582100be595da4c3949b87e17eb9176d2e26b4d5a9d2c4992c134ac2675db |
| vecnormalize.pkl | 21268 | dc6cab87c5e0cdd1f1cae276f04163921d28e744380d8a699a02b896be5225ce |
| manifest.json | 81021 | e9f145cf740bed178dabec364b218128fcf5fef50620550b1b8576df3fd9f539 |

Logs and reload summary: runs/live/sessions/20261018-162908-575c54.
Models, private approvals, raw logs and game data are not committed or uploaded.

## Self-review and limitations

Primary self-review compared actual protocol/specifications, all completed task
criteria, earlier Windows checks, assisted runtime evidence and checkpoint
readback. This is not independent review. The declared live-loop acceptance
criteria pass: offline checks, real damage/death/restart/reconnect integration and
a short real training checkpoint. Room navigation in the random recordings was
operator-assisted; exact damage semantics and native synchronized steps remain
unproven. Neither a 256-step model nor this archive demonstrates improved play,
achievement eligibility, isolation or Dead God progress.

Next work: define an explicit experiment and comparable baseline before longer
training; resolve navigation incentives and evaluate gameplay separately from
reward. Do not automatically renew authority or launch more training. Isaac is
left running for normal operator use/exit. Manual control was confirmed after
the preceding integration run; no additional user confirmation is inferred for
the training run.

Final verification: Check.ps1 exit 0, 1224 tests with zero skips, Ruff, formatting,
mypy, pip consistency and strict OpenSpec 25/25. After the acceptance review,
`OpenSpec.ps1 archive live-training-loop --yes` exited 0, creating the baseline
live-training-loop specification and archive 2026-10-18-live-training-loop.
Its proposal-length warning was non-blocking; validation was not disabled.
The first post-archive strict pass rejected the CLI-generated placeholder Purpose
in the new baseline spec. It was replaced with the actual capability purpose;
no behavioral requirement or validation setting was weakened.
