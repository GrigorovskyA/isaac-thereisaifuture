# Reward v10 finite native training plan

Authorized October 30, 2026: preserve reward v9 schema8, initialize reward v10 once,
verify native graph labels after 15 minutes, then train until October 31 at 09:00 CET
(08:00 UTC). Save file 2; no save, Steam Cloud or launch-option edits.

## Identities and bounds

- Contract: `3043a54c9d56e402f4a2bb6bd96906e79ee6ae3d7cc272a834d13ac13e31f621`.
- Observation schema8 (9762 values), action2, RecurrentPPO, features512, n_steps1024,
  batch256, gamma0.998, ent_coef0.005, stall40. Only reward potential changes to pure-v10.
- Preserve `runs/pure-v4` as `runs/pure-v4-reward-v9-schema8`, final
  `b26db425-s1-t102400`; verify checkpoint/metrics hashes before and after the move.
- Fresh `runs/pure-v4`, `Start-Pure.cmd --initialize` exactly once. No manual retry or
  fresh-model fallback. Native supervisor session rollovers resume compatible latest.
- Absolute stop.forever deadline October31 08:00 UTC. Disk cap20,480,000,000 bytes;
  native per-session lease28740 seconds. Training faults stop; best-effort pause failure
  alone is recorded and does not stop. No additional pause threshold or config changes.
- Close the existing dashboard before launch. During training read files only;
  never open/activate other PC windows. Guarded native game keyboard handles focus.

## Native 15-minute check

Bounded passive decode audit (one sample/second, first20 minutes, maximum32 MiB per
worker) copies oracle doors, policy-visible door flags and minimap labels into local
files. Original decoder outputs and policy inputs are preserved. No gameplay controls
or oracle data are added to the policy.

Check nonnegative door targets matching minimap grid indexes; normal-room room_grid;
locked doors have usable=false when encountered; nonzero col_door_shaping and populated
stall_goal_hops when finite routes are observed. Missing structural labels (all -1)
stop and report. Other missing required evidence or inconsistent labels also stop for
investigation, without repair/retry. Unencountered locked/secret doors remain unverified.
The deployed transport cap is131072 bytes, unchanged from schema8; the OpenSpec task's
49152-byte wording is historical and cannot be claimed as a passed cap check.

## Offline verification (self-review)

Windows Check.ps1 passed1466 tests, including the isolated Lua5.3 harness, no skips;
lint, formatting, mypy and pip check passed. Strict OpenSpec passed26/26. One existing
synthetic All-NaN warning. Check output: reports/local/reward-v10-20261030/check.log.

OpenSpec verification: 8/10 tasks complete. The two remaining native tasks2.2/2.3 stay
open; no archive. All9 added requirements have implementation evidence in Lua oracle
export, strict wire models, room_graph.py, rewards.py, checkpoint contracts and stall
metrics. Tests cover coefficient compatibility, graph/reset/BFS, locked/secret doors,
unknown grid, potential bounds/telescoping, boss trapdoor and metric header migration.
The encoder is unchanged; graph labels stay outside policy observations.

Native behavior and outcome acceptance are not verified by these offline checks.
Minor specification discrepancy: the dead-end scenario calls the current room's graph
distance1, while BFS distance to the unvisited room is2; the intended door-target hop
term is1 and matches design and tests. Native acceptance remains separate.

## Completion and report

At deadline, training fault, failed native verification or human stop, retain stop.forever;
inspect every session result, exit code, fault and cleanup error, plus actual absence of
game, worker, owner, port9528 listener and exact owned approval. A launcher exit0 does
not override session faults. Preserve all models and historical failed reports.

Compare approximately30k cumulative completed-episode-step windows against archived
v9 schema8 at identical cumulative bounds, no extrapolation past its105104 observed
steps. Boundary episodes are not split; complete-episode rate denominators are explicit.
Cumulative observed steps include unsaved rollout tails and are not exact checkpoint or
optimizer steps. Report exit-start share, rooms/episode, kills and clears/1k, stage>=2,
stall/death and stalled-step shares, clear-stall/dead-end shares with available denominators,
stall_goal_hops distribution and mean col_door_shaping. No frozen evaluation or gameplay
improvement/task2.3 claim from optimizer statistics alone. Commit/push only the final
report and relevant documentation; never local helpers, raw logs, models or unrelated tools.
