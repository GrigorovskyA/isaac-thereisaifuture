# Settled waypoint and three-frame shooting control

Date2026-10-22;basec628e40. The current user requested proceeding after the
recorded-state braking fix. One new native control is authorized;all previous
budgets remain closed. This plan inherits the exact identity,route,diagnostic
deployment and cleanup guards from the
[three-frame plan](2026-10-22-three-frame-control-plan.md).
Executed once and closed;see [results](2026-10-22-settled-control-results.md).
The inherited900update registered-progress gate was omitted below and stopped
the run before320commands;this plan omission and failed convergence are recorded.

Change only scripted waypoint acquisition:when near a waypoint,enter neutral
braking until speed<=0.1,then recheck x/y tolerances6/4 before advancing. If drift
left those tolerances,reacquire the same waypoint. Final twelve neutral commands
and same-frame clear/aligned/in-range shot guard remain. Do not relax tolerances,
range,expiry or choose another target. The existing four recorded-state checks
support this branch but do not prove native convergence.

One180second inclusive-startup invocation,320 completed three-frame commands,
at most90 guarded left-shoot commands,1GiB output,32MiB paired trace,zero retries,
faults,death restarts or New Run. Fresh guarded file2/Continue,ordinary Isaac,
room83,door within20units of(560,280),fixed visible target near(80,200),same
measured grid and waypoints(560,200),(320,200);mismatch/unavailable Continue stops.
Stop at first target HP decrease,first player health loss,death/clear,missing or
changed target/context/grid/weapon,or any cap. No inference/training/model writes.

Freeze helper/source/deployment/config and every checkpoint artifact;preserve
a0a93c29-s20-t26368,seed20,schema2/723,rewardlive-firing-v5 and all ancestors.
Primary may enable only the reviewed existing tear_diagnostics switch in matching
source/deployment after backup and absent-game verification. Its unchanged bounds
are120seconds/1024records/64labels/100ms sampling/900bytes perline. One Luna/high
worker executes the exact finite assignment;no primary input/frozen edits then.

Release input,close observer and owned game normally,verify absent game/listener/
unchanged owned approval,then restore both exact observer backups with hash guards.
Read actual native action accepts,settled waypoint velocities,tear callbacks/
sampled trajectories and target HP. A clear proxy or absent sample does not prove
a hit or zero tears. Actual HP decrease is required for damage qualification;
scripted success is not learned improvement. Keep partial coverage explicit.
No automatic retry,training or new budget follows. Local artifacts:
reports/local/settled-control-20261022/.
