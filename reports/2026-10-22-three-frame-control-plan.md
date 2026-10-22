# Three-frame clear-shot control

Date:2026-10-22 Europe/Amsterdam;base1909fff. The user requested execution after
the prior report proposed a control matching training's three-frame hold. This
authorizes one new bounded control;previous budgets remain closed.
Executed once and closed;see [results](2026-10-22-three-frame-control-results.md).
No remaining budget or automatic retry.

Use the same guarded file2/Continue,ordinary Isaac,room83,door within20units of
(560,280),fixed visible target near(80,200),walkable-grid validation and route
(560,200)->(320,200) as the
[previous plan](2026-10-22-shot-flight-control-plan.md). Change the environment
action repeat to3 for all route/settle/shoot commands,matching training config.
No model inference,learning,New Run,death restart,save/Cloud edit or new lineage.

One180-second inclusive-startup invocation,320 completed commands,at most90
guarded left-shoot commands,1GiB output,32MiB trace,zero retries/faults/restarts.
All other target/room/session/grid/weapon guards remain. Stop at first observed
target HP loss,first player health loss,death/clear,unknown/mismatched state or
cap. Three-frame commands imply up to960 requested game frames within these
limits;no hold exceeds existing native expiry. Do not expand alignment tolerance.

Preserve a0a93c29-s20-t26368,seed20,schema2/723,rewardlive-firing-v5 and its
config/model/normalizer identity;freeze all checkpoint artifacts and ancestors.
Primary may temporarily enable only existing bounded tear_diagnostics in both
source and installed observer to satisfy matching-source preflight,with exact
backups. Same120second/1024record/64label/100ms/900byte diagnostic bounds.
Freeze final helper/source/deployment/config/checkpoints and fresh absolute
assignment deadlines before launch. One Luna/high worker executes only that
prepared command. Primary does not edit frozen inputs or control its game.

Release input,close observer and owned game normally,verify absent process,
listener and unchanged owned approval,then restore both exact observer backups
only if current diagnostic hashes match. Restoration failure is a fault.
Read actual native accepts,tear callback notes/sampled trajectories and target
HP endpoints. No observed trajectory/hit may be invented from a clear proxy.
Damage qualifies only on observed target HP decrease;scripted damage is not
learned improvement. Sampling/endpoint coverage remains partial. No automatic
retry or training follows this control,regardless of outcome.

Prepared local helper/assignments/logs belong under
reports/local/three-frame-control-20261022/. Source/software behavior and tests
are unchanged apart from the temporary reviewed diagnostic switch;the previous
36-test diagnostic receipt remains applicable,not a newly run suite.
