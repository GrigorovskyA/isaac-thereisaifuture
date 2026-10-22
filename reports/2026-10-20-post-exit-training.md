# Experiment: post-exit-settling training continuation

User requested continued work after the offline exit-settling correction.
One new finite session: resume seed20 t5120 with saved normalizer, target5632
(512 checkpointed new combat steps),10 minutes,two natural death restarts,
maxfaults0,disk512MiB,gate90 seconds per handoff. Existing cumulative navigation
limits256 commands/90 pulse seconds/four transitions/three stationary pulses
remain; post-combat empty/no-door settling <=2 seconds within original caps.
Startup/menu cap120 seconds, temporary approval15 minutes. No second invocation,
automatic budget renewal,fresh initialization,forced room/reset,save/Cloud/Steam
option edits or deployment. Immediate normal close after runtime return.

Preflight with game absent passed; source/installed observer match, config hash
unchanged1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5.
Full t5120 model/normalizer reload, identity/hash/latest verified; parent PPO
updates80,normalizer count5125.0001. Corrected source last passed1902 tests/zero
skips,full Windows gate. Native narrow shapes2/3/5 remain user-deferred/not_run.
Setup/exact approval hash in reports/local/post-exit-training-20261020-104549/.
Steam launch requested after preflight. No gameplay-quality/progression claim.

Success: native exit-settling evidence plus completed checkpointed PPO continuation,
valid parent lineage, changed finite tensors, normalizer reload and cleanup. If a
limit stops a partial rollout, retain latest complete checkpoint and report unsaved
samples explicitly.

## Superseded before training

User increased the requested experiment to up to five deaths/more samples during
menu preparation. Agent menu keys reached file2/Continue but did not enter the
run; no training invocation, gameplay command or sample occurred. Normal close
requested and exact approval removed. This512-step preparation is superseded by
[the five-death experiment](2026-10-20-five-death-training.md), not a failed or
completed training session. Its startup timer was not silently extended.
