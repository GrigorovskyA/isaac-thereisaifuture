# Experiment: bounded continuation to 4096 steps

Predeclared: 2026-10-18, Europe/Amsterdam. Experiment ID: live-continuation-4096-v1.
This is one exploratory training run and one subsequent frozen inference check,
not confirmatory evidence of policy improvement. No new software behavior or
reward coefficient is introduced. Existing combat-training criteria stay open.

## Question and starting point

Does the accepted real training pipeline resume correctly over several rollouts,
retain checkpoints and expose useful gameplay experience instead of only empty
rooms? Does deterministic behavior after this continuation still concentrate on
one action? The earlier frozen pilot selected left/up in 244/256 decisions and
had no combat labels. These are reference observations, not matched controls.

Starting checkpoint: 1f4a187e-s20-t256, seed 20, config hash
1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5.
Pin this parent and verify its existing model/normalizer/manifest hashes remain
unchanged. Use configs/training-live-v1.yaml without modifying hyperparameters.
Training seed 20, CPU RecurrentPPO, action repeat 3, rollout 256, epochs 4.
Observation/action/reward schema versions remain 1. Approximate oracle labels
stay separate from policy observations and normalization.

## Fixed budgets and stop conditions

1. Training: resume explicitly, target 4096 TOTAL model timesteps, hence at most
   3840 new steps from the 256-step parent. Stop after ten minutes even if the
   target is not reached. Existing checkpoint disk cap 512 MB; expected new files
   approximately 150 MB. Save each completed 256-step rollout. No automatic retry
   or fallback to training from scratch; infrastructure faults stop the run.
2. Frozen check: only after successful training/checkpoint readback and fresh
   operator readiness, at most 256 decisions / two minutes using an explicit
   checkpoint directory and config hash. Use seed 20, deterministic inference,
   no learning, no normalizer updates and zero tolerated faults.
3. One private approval: 20 minutes from closed-game preparation and at most
   three natural-death restart attempts for the entire game launch. Waiting,
   reconnecting or switching training/inference must not renew either limit.
   A later expired gate requires deliberate operator coordination, never renewal
   to conceal an unfinished run.
4. Stop on protocol failure, unexpected instance/epoch changes, operator stop,
   budget expiry or incompatible/corrupt checkpoint. Release/close; leave Isaac
   for normal operator exit. No forced death/reset, save/Cloud edits, scenario
   spawning, automatic initial run start or unattended process recovery.

## Operator workflow and exposure

Launch and file-2 selection/Continue are manual. Confirm the room and readiness
before control. For combat exposure, the operator may position the character in
a room with enemies BEFORE starting a run. Do not press keys while Python acts.
If manual navigation becomes necessary, stop the run first, record its partial
result and intervention, and do not silently restart to fill the original budget.
No process is killed to prepare an experiment.

Record initial room/build/health when observable; otherwise unknown. A fresh
game instance does not imply an isolated profile. Training on the ordinary
file-2 profile is the existing explicitly approved exception, not isolation.

## Evidence and decision rule

Retain every segment and fault, not just successful rooms. Report training and
frozen inference separately: attempted/completed decisions, elapsed time, game
updates, checkpoint count and parent lineage; combat-bearing/empty exposure;
damage taken, approximate enemy HP removed, clear/death/timeout/fault counts;
native action directions, tear records, release and operator interventions.
Training logs do not fully retain the unfinished final segment: record this
limitation and reconcile loop/checkpoint counts from the available evidence.

Report frozen action concentration and boundary/idle behavior descriptively.
Do not rank this checkpoint against random or the 256-step parent: rooms,
builds, initial health and exposure are unmatched. If there are fewer than five
complete combat-bearing segments, label combat evidence insufficient. Even
five segments do not satisfy the unchanged multi-seed/100-episode/+20-point
confirmatory criteria. Reward increase alone never establishes better play.

Pipeline success means valid parent resume, completed rollout checkpoints,
successful reload, bounded stopping and release. Any quality result remains
inconclusive until comparable scenarios and separate evaluation exist. Do not
change rewards, select a favorable intermediate model or extend the budget after
seeing results. Use the final completed checkpoint, including an early budget
stop if it is valid, and report the stop rather than hiding it.

Private commands/logs/checkpoint hashes go into a report using EVIDENCE_TEMPLATE.
Never upload checkpoint binaries, raw game logs or approval files. No later
multi-hour training or successor experiment is authorized by this plan.
