# Live training loop (observer 0.5.0-dev)

Current Python reward contract (2026-10-20): `live-conservative-v2`. Enemy absence
does not pay remaining HP or a kill bonus. Session/epoch HP floors survive software
segments; uncertain gaps do not pay retroactive damage. Legacy `combat-v1`
checkpoints remain readable for frozen analysis but live resume rejects them before
creating an environment. No automatic migration or fresh-model fallback exists.
See [correction and verification](../reports/2026-10-20-live-reward-continuity.md);
earlier archived acceptance below describes its recorded historical behavior.

OpenSpec change: [`live-training-loop`](../openspec/changes/archive/2026-10-18-live-training-loop/proposal.md).
Status: accepted and archived after Windows checks, guarded 0.5.0-dev deployment,
two real 2000-action random checks with operator-assisted navigation, one natural
death/restart/reconnect, and a real 256-step training checkpoint with model and
normalizer readback. See [runtime evidence](../reports/2026-10-18-live-loop-runtime.md)
and [checkpoint evidence](../reports/2026-10-18-live-training-checkpoint.md).
This does not establish improved play, autonomous navigation or achievement eligibility.

## What it does

One terminal command connects Python to the running game on save file 2 and:

1. receives entity observations at 20 Hz (`live_loop_v1` = entity + safe actions +
   death restart, negotiated together);
2. sends movement/shooting commands (3 game updates per step by default);
3. derives approximate reward events from a separate `oracle` block (enemy HP,
   room clear, player dead) that never enters the policy observation;
4. restarts the run autonomously after a death (bounded by the approval), then
   reconnects and continues;
5. acts randomly (`--mode random`) or trains RecurrentPPO (`--mode train`).

Episode = a segment of one run: death and room clear terminate; 60 s of game time
truncates without a reset. Transport faults truncate with `info["fault"]` (budget
`--max-faults`, default 20); protocol errors stop the run.

## User decisions (2026-10-18)

- Approximate events from frame deltas are accepted instead of an exact engine oracle.
- Autonomous death restarts are accepted within the training approval.
- Training on save file 2 is accepted by the operator.

## Operator steps (Windows)

1. Close Isaac. Deploy `mod/observer/main.lua` and `metadata.xml` to
   `<game>/mods/isaac_threrisaifuture_observer/` (see [GAME_SETUP](GAME_SETUP.md)).
2. Write the approval (private, next to the mod; max 8 h, 1..5000 restarts):

   ```powershell
   .venv\Scripts\python.exe -m isaac_threrisaifuture.cli approve-training --confirmed-save-slot 2 --hours 8 --max-restarts 1000
   ```

3. Start Isaac with `--luadebug`, select file 2, start or continue a run.
4. Run `Start-Live.cmd` (random actions) or
   `Start-Live.cmd --mode train --config configs/training-live-v1.yaml --minutes 60`.
   Add `--resume` to continue the latest checkpoint in `runs/live/seed-<seed>`.
5. Ctrl+C stops Python: input is released and the game keeps running. A normal game
   exit drops the approval from memory; it is re-read on the next game launch until
   it expires.

Logs: `runs/live/sessions/<stamp>/live.jsonl` (episodes, faults) and `oracle.jsonl`
(reward labels, kept separate). Checkpoints: `runs/live/seed-<seed>/checkpoints`.

## Safety bounds kept

- Loopback only; Lua refuses a training approval unless the full live loop is negotiated.
- Commands are bound to session, epoch, room visit and a frame at most 15 updates old;
  sequences strictly increase (a replay closes the session).
- Death/pause/room races produce a `rejected` acknowledgement and release input
  instead of disconnecting. A missed heartbeat releases input.
- Restart: only after an observed game over of the current epoch, 1.5 s delay,
  at least 4 s between dispatches, `max_restarts` per game launch, until approval expiry.

## Known limitations

- The game is not paused during PPO updates (n_steps 256 keeps them short).
- Enemy HP labels are uncalibrated: a vanished enemy counts as killed; all player HP
  loss is attributed to enemies. No exploration reward yet (future reward-v2).
- Real-game unknowns: `HitPoints` semantics, `IsDead`/`IsClear` timing, stability of
  many consecutive restarts.

## Windows checklist (tasks 5.x)

1. `./scripts/Check.ps1` passes.
2. Closed-game deployment; `preflight` hash match.
3. `approve-training`; hello lists `live_loop_v1`; oracle HP values plausible.
4. Random run >= 2000 steps: damage events, a death, an autonomous restart, no protocol error.
5. Short `--mode train` run saves a checkpoint.

Record results with `reports/EVIDENCE_TEMPLATE.md`.

## Primary Windows review corrections

The pinned Windows gate passes 1224 cases, including simulated Lua/socket/PPO
checks; none is a real Isaac run. Missing enemies across overflow are now forgotten
without invented kill/damage events, keeping history bounded to 64 current IDs.
A fatal protocol error recorded by the reader propagates before reset reconnects.
One absolute deadline is shared by reset, pause waits and fault retries. An
already-running bounded I/O operation or model update can finish after that
deadline; no further action/reset retry is allowed afterward. If a rollout is
interrupted by budget expiry, the log does not claim a new checkpoint for it.
Installed observer is now 0.5.0-dev. The Windows review describes the earlier
pre-deployment state; the later deployment and runtime reports establish the
current narrowly accepted live pipeline. Every future run still needs an explicit
budget and applicable unexpired approval; these checks do not authorize longer runs.
