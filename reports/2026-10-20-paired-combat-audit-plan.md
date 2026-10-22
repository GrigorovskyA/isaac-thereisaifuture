# Plan: paired frozen combat audit

Predeclared2026-10-20,Europe/Amsterdam. Goal:diagnose prolonged combat and compare
decisions on identical inputs without learning. User authorized the diagnostic
and frozen comparison. This is a validation pilot,not held-out evaluation.

Exact checkpoints:original conservative92969b7f-s20-t1536 (config92969b7fcfa3990ef5a8612dd7905437c4a9a46149e64dc7d912cb408f7f2da8)
and extended08e0d262-s20-t6912 (config08e0d2627b5cdac2d0be36ff2d19578496a58e9632defa50a67ae7a7653f2d8e),training seed20.
Use existing deterministic CheckpointPolicy adapters and RandomPolicy seed2020.
No model/optimizer/normalizer updates,saves or lineage changes.

One Steam launch,explicit file2 Continue of the existing living run;fresh menu
proof and active Isaac required. No New Run fallback,save restoration,seed commands
or operator gameplay. Actions remain structured;menu input uses existing guards.
All three policies receive the same raw encoded vector/history at each decision.
Reset all recurrent states at each window and software/native episode boundary.
Only the scheduled policy controls the game. Sequence:1536,6912,random,random,6912,
1536,up to128 attempted decisions each,ending early on an episode boundary,maximum768 total. Counterfactual predictions
have no attributed damage,clear or death outcome. Window outcomes are confounded
by inherited state/sequential control;do not rank gameplay performance from them.

Geometric proxy:cosine toward nearest encoded enemy,coarse alignment within45deg;
no-shoot=false,missing/zero/clipped targets unavailable. This does not test line
of sight,tear speed,enemy vulnerability or actual hits. Report denominator and
action distributions alongside paired action disagreement. Consecutive inputs
are autocorrelated;do not claim independent-sample statistical significance.

Budgets:one assignment/global outer600s,absolute latest finish recorded before
dispatch. Controller240s from listener setup,accept90s,menu60s/eight keys,
768 attempted decisions,six natural deaths/five structured restarts,maxfaults0,
zero retries. Approval540s/max_restarts5 within outer deadline. Gate90s;navigation
scale1 (256 commands/90 pulse seconds/four transitions),not learned actions.
Total output256MiB,offline test-temp growth512MiB. Any cap/refusal/fault stops.
No reset after a sixth death;partial windows remain censored.

Primary enables only existing bounded diagnostics while game closed,passive
effects false. Journal retains its120s/10Hz/128labels/512line caps;raw oracle
snapshot capture is separately bounded by768 decisions. Keep raw oracle/phase
files separate from policy vectors and action diagnostics. Neither is reused as
inference input. Correlate identity/frame/IDs;unknown matching stays unavailable.
Inspect raw HP rises/declines separately from rewarded HP floors;do not equate
zero credit with no hits. Actual revival scenario remains pending if absent.

Before dispatch freeze all sources,helpers,configs,exact checkpoint files/latest
pointers and configured observer hash. Run targeted/full Windows gates and actual
frozen-model loading. Worker executes prepared scripts only. After runtime close
the owned game normally,release listener/actions,remove only exact owned approval;
primary restores byte-identical default-off observer while closed. Independently
verify all hashes,loaded model/normalizer fingerprints,identity and cleanup.
Publish code/specification/evidence only;raw local captures/checkpoints stay private.

## Offline dispatch amendment before any game launch

Initial targeted120 tests passed. The first full gate failed with WinError5 in
pytest cleanup after its worker lost the specified environment across PowerShell
processes;the Lua-backed cases were not fully loaded. That attempt is retained
as failed,not accepted as a passing gate. No game/runtime/approval was started.
Primary prepares one replacement full-gate invocation with all environment values
set inside Run-PairedGate.ps1. No checks are weakened. All frozen source/model
hashes remain identical. Original absolute latest finish/native/disk budgets stay
unchanged;no lease existed to renew. A fresh worker may execute this one fixed
gate,then the original once-only native wrapper only if it passes. Failure stops.

## Human-focus follow-up

Fixed gate passed2011 tests,zero skipped. First native attempt stopped at the
intro after foreground refusal;no combat decisions/deaths occurred. It closed
normally and removed its approval;primary restored default-off deployment.
The user then explicitly answered ready to assist the next launch by clicking
the game window. Prepare one new finite assignment,not a guard bypass:10s grace
after Steam launch,then unchanged guarded Continue. Outer420s/controller240s,
approval360s/max_restarts5,768decisions/sixdeaths,zero retries/faults,256MiB output.
Record a new absolute latest finish before dispatch;prior lease was already gone.
Use separate paired-combat-focus outputs. The child configuration label now
correctly states the six-death limit already enforced by its gate. Production
source/module/tests/configs remain byte-identical to the2011-test passing gate.
