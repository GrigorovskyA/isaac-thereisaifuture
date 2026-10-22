# Validated short navigation and three-frame shooting control

Date2026-10-22;base1c7ce84. The user requested the proposed offline convergence
work followed by short navigation/three-frame firing. No previous budget resumes.
Use one new native control only if the declared offline development check passes.
Executed once after 512/512 cases passed; closed with observed target HP loss.
See [results](2026-10-22-mixed-control-results.md). No remaining runtime budget.

## Offline gate

Fit a bounded empirical axis-motion model from the previous254 one-frame and40
three-frame native command traces. Validate against separate197/291command
development traces. Exclude the single observed health-loss/knockback interval
from the pre-damage motion residual pool,not by error-size filtering. The fit
is approximate,not engine physics or learned-policy evaluation.

Execute the actual candidate route branch in512 bounded closed-loop cases:
64 seeds,4 observation timing schedules,with/without sampled empirical residuals.
Starts vary x/y by+/-10 and velocity by+/-3;at most230navigation commands percase.
Require all512 to reach both waypoints;report all failures and command counts.
Check the old three-frame approach as five nominal negative-control cases.
One120second helper,180second absolute offline assignment,10000source axis
transition bound,no game/learning/dependency writes. Development/residual stress
testing is not an independent held-out gameplay test or native convergence proof.

## One conditional native control

Same guarded file2/Continue,Isaac,room83,door within20units of(560,280),fixed target
near(80,200),same measured grid/ordinary weapon and waypoints(560,200),(320,200).
Keep neutral braking until speed<=0.1 and recheck x/y tolerances6/4. Navigation,
alignment and neutral settling use1frame holds;only guarded left shooting uses3.
Record each command's actual repeat. This changes no learner/config/model contract.

| Active bound | Fixed value |
|---|---|
| Inclusive startup/action time |180seconds,one fresh absolute lease |
| Completed commands / guarded shooting commands |320 / at most90 |
| No-registered-progress window |900game updates;checked at batch boundaries |
| Environment scenario ceiling |1800game updates;earlier900progress gate retained |
| Output / paired trace |1GiB /32MiB |
| Faults,retries,death restarts,New Run |0 |
| Native hold / freshness / wall expiry |1or3frames /<=15frames /250ms |
| Diagnostic logging |120seconds,1024records,64labels,100ms sampling,900bytes/line |

Startup worker readiness20seconds,menu60,initial active snapshot30 and connection
accept60 all share the180second outer deadline. Socket/heartbeat/transport guards
remain unchanged. Stop at first target HP decrease,first player health loss,
death/clear,unknown/changed target/context/grid/weapon or any listed bound.
Unavailable Continue or incompatible state stops;no fallback. No automatic retry
or training follows. Shooting remains positively guarded clear/aligned<=8/in-range.

Preserve a0a93c29-s20-t26368,seed20,schema2/723,rewardlive-firing-v5 and all ancestor
checkpoint files. Freeze final helper/source/deployment/config/checkpoints before
launch. Primary may temporarily enable only existing tear_diagnostics in matching
source/deployment with exact backups. One Luna/high worker executes the frozen
assignment;primary does not alter frozen inputs or control its game.

Release input,close observer and owned game normally,verify absent game/listener/
unchanged owned approval,then restore exact source/deployment backups with hash
guards. Allow45seconds separate bounded cleanup;never renew gameplay authority.
Actual target HP decrease is required for positive damage qualification. Report
native accepts,release durations,tear callbacks/sampled flight and HP separately.
Retain partial coverage;scripted damage never proves learned improvement.
Local artifacts:reports/local/mixed-control-20261022/.
