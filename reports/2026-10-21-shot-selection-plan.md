# Shot-selection audit and native positive control

Date2026-10-21 Europe/Amsterdam;source01c4898 plus diagnostic-only change.
The user requested isolating firing direction after the v5 pilot failed to improve.
No learning/model migration or New Run is authorized by this diagnostic.

## Offline
Audit exact v4/v5 paired native traces,2500/2502 completed decisions respectively,
at axis tolerances8 and20worldunits. At most3000records pertrace,128MiB perpair,
1MiB result,one original five-minute absolute deadline shared by prepared fixes.
Read only modela0a93c29-s20-t26368 and matching normalizer/config;freeze their hashes.
Evaluate final frozen shooting probabilities on actual v5 states with fresh/reset
recurrent replay. This is counterfactual probability analysis,not logged training
probabilities or improved play. Preserve failed attempts and do not silently retry.

## Native positive control
One180-second inclusive-startup window,200 completed1-update decisions,1GiB disk,
32MiB paired trace,zero infrastructure faults,retries,death restarts or New Run.
Approval formatmax_restarts1 is retained,but no reset is requested. Continue/file2
and ordinary Isaac only;actual start is captured before positional checks.
Expected existing room83,initial within20units of(560,280),ordinary tears,visible
enemy centered near(80,200). Abort mismatched state. Preserve v2/v3/v4/v5 model,
normalizer/manifests/pointers;no inference or optimizer writes.

Scripted movement follows waypoints(280,280),(280,200),only after measured navigation
grid verifies each center along these cardinal segments is walkable. Keep the grid,
target identity/position and room/session/epoch fixed. Choose one movement axis per
1-update command;settle near the final waypoint,with bounded vertical alignment
pulses and settling under the same200-command budget. Fire left only when policy-visible
same-frame evidence positively identifies that enemy on a clear line,within measured
tear range and transverse error<=8. No automatic target fallback or blind shots.
If alignment is unavailable,stop rather than enlarge tolerances or change budgets.

Stop at first observed HP drop on the fixed enemy,any player health loss,death,
clear,context/target/grid/weapon mismatch,step/disk/time cap or infrastructure fault.
HP endpoint comparison proves only the observed drop;other event coverage remains
partial. Log scripted phases/actions separately;none enter training. It is a
positive control of acquisition/action/projectile/damage accounting,not learned play.

Use the reviewed NativeRuntime ownership harness:Steam launch,guarded fresh file2/
Continue menu evidence,bridge-only gameplay;release/observer close,normal owned
WM_CLOSE,unchanged owned approval removal,absent process/listener and frozen hashes.
No save/Cloud/configuration or third-party mod edits. Record exact helper/source/
checkpoint hashes and finite absolute deadlines in a fresh local assignment before
execution. Stop on failed preflight;no lineage/budget/state substitutions.
