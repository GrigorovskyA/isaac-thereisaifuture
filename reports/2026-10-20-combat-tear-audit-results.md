# Evidence: combat tear audit

- Date:2026-10-20,Europe/Amsterdam;base bdcf941a3dcb1c79a347bf16b4de77a211f07426 plus reviewed observer diagnostics.
- Scope:default-off local diagnostics and bounded frozen native projectile evidence;no learning,checkpoint selection or observation/reward change.
- [Finite plan and retained compatibility amendment](2026-10-20-combat-tear-audit-plan.md).
- Python3.12.14,observer0.5.0-dev,Lua5.3. Native hello reports game/build unavailable;do not relabel configured metadata as runtime detection. Existing authorized ordinary file2 profile/mod set retained,not isolation or vanilla acceptance.
- Inference:deterministic RecurrentPPO,training seed20,config08e0d2627b5cdac2d0be36ff2d19578496a58e9632defa50a67ae7a7653f2d8e,t6912. Preserve binary model/normalizer/latest;no optimizer or normalization updates.

## Implementation and checks

The observer reuses the existing live entity scan. Literal-true opt-in,120s nonrenewable window,100ms pacing,64-entity scan,64 lifetime labels,1024 lines and900-byte records bound work. A context change or error stops only diagnostics. Default-off and malformed flags perform no additional reads. No extra callbacks or collision return values;all records stay in native local logs.

Tear samples contain position,velocity,height/falling fields,grid class,measured displacement from first observed pose and sampled cumulative path. Other owners are ignored. A missing sample is absence with unknown cause. The first pose may follow spawning and intermediate updates are unsampled;these distances are lower bounds,not effective weapon range.

Reported TearRange is a player API statistic. CheckLine uses projectile mode3,no wall/crushable ignores,to the nearest exported policy enemy. Clearance/first-hit position are a query result,not an observed tear collision. BitSet128 flags remain unavailable as raw numeric values;log Lua type and read-only spectral/piercing booleans instead. Never coerce userdata or unsafe integers into floats.

API provenance:[Room.CheckLine](https://wofsauge.github.io/IsaacDocs/rep/Room.html#checkline),[EntityTear](https://wofsauge.github.io/IsaacDocs/rep/EntityTear.html),[TearFlags](https://wofsauge.github.io/IsaacDocs/rep/enums/TearFlags.html),plus installed Lua enums/source. Documentation is not native proof.

| Check/attempt | Command/evidence | Exit | Status |
|---|---|---:|---|
| Initial diagnostic suite | pytest test_lua_tear_diagnostics.py | 0 | passed:12 simulated behavior cases |
| Initial targeted/full gate | run_tear_gate.py -> Run-TearChecks.ps1 | 0 | passed:65 targeted/2040 full,zero skipped;OpenSpec39/39 |
| Initial deployment preflight | Start-IsaacAgent.cmd --preflight-only | 1 | blocked as expected:older installed observer differed;no launch |
| Reviewed default-off deployment preflight | Same command after primary deployment while closed | 0 | passed,no process launched |
| First native trajectory audit | run_tear_audit.py | 0 | wrapper/control passed;diagnostic failed before first tear sample,not native trajectory acceptance |
| Bitset compatibility regression | test_lua_tear_diagnostics.py | 0 | passed:16 tests,including userdata/table/unsafe numeric flags |
| Final targeted/full gate | run_tear_gate2.py -> Run-TearChecks2.ps1 | 0 | passed:69 targeted/2044 full,zero skipped;Ruff/122 formatted files,mypy51 source files,pip clean,OpenSpec39/39 |
| Second deployment preflight | Start-IsaacAgent.cmd --preflight-only after reviewed default-off update | 0 | passed,no process launched |

First gate50.53s,167 frozen hashes before/after,87,459,757byte sampled temp growth. Final gate50.81s,169 hashes before/after,88,262,694byte sampled temp growth. Primary independently recomputed all hashes and read command exits/logs. Both within480s/512MiB growth bounds. Stage output files are small and separately retained;the driver console itself was empty because the PS script redirects stage outputs.

## First native attempt: retained diagnostic failure

Fresh Continue2,seven guarded menu keys,active Isaac(type0),session4de4e7b4376748beb1eac0dfe088ecf4,epoch1,initialframe11285. One frozen window recorded400 decisions andzero infrastructure faults. A software episode boundary with outcome unknown ended the window;no death/restart and no512-step completion claim. Wrapper elapsed89.33s,exit0;normal close,exact approval removal and unchanged t6912 fingerprints/files verified. Primary verified171 frozen files and restored default-off observer while closed.

Native audit produced30 target records andone stop(error) atframe11294;28 target records were unavailable during loading,onlytwo had a visible target. Both reported range260,nearest-target distance488.26..488.69,andclear3=false,first hit near(989.88,343.08)/(990.37,343.03). Zero tear trajectory samples. Sampled enemy HP total90 throughout400 decisions;onlyeight spawn events,no credited damage. Raw first exception text was not captured;the BitSet128 compatibility mechanism was identified from source/API and subsequently regression-tested,not asserted as an exact retained native exception.

Local evidence:reports/local/tear-audit-t6912/{result.json,menu.jsonl,console.txt,game-log.txt,tear-lines.txt,analysis.json};runs/tear-audit-t6912-20261020/{policy-decisions.jsonl,oracle-snapshots.jsonl,oracle-events.jsonl,result.json}. Raw logs/private approvals/models excluded from Git.

## Compatibility follow-up

Fresh file2 Continue/Isaac confirmed again with seven guarded keys. Session
638f37afeb2d41379a56e4c02f643bf4,epoch1,room visit0,initial active frame13122.
The canonical new output is runs/tear-audit-t6912-2-20261020/,not the first-run
root. Primary counted399 policy rows and read399 in its own result.json. A worker
summary accidentally quoted400 from the older root;the canonical source controls.
One software unknown episode boundary ended this single window before512;zero
faults/deaths/restarts. Wrapper/control exit0,89.45s,no failure or cleanup errors.

| Native fact | Observed result |
|---|---|
| Audit output | 548 lines:361 target records,122 tear samples,64 sampled absences,one stop |
| Stop reason | labels,after64 observed owned-tear lifetimes;no diagnostic error |
| Target unavailable | 30 records during loading;excluded from clearance denominator |
| Valid target clearance | 331/331 clear3=false |
| Reported range | 260 throughout |
| Nearest-target distance | 118.39..502.74 game units |
| Distance <= reported range | 124/331;all124 still clear3=false |
| Observed trajectories | 64;sampled displacement lower bounds0..120 units |
| Native tear flags | userdata;raw numeric flags unavailable,spectral=false,piercing=false |
| Sampled HP | eight enemies,total90 throughout399 policy rows;no credited damage or kills |
| Cleanup/immutability | 173 frozen hashes matched;model/normalizer fingerprint unchanged;game/listener/approval absent |

All122 tear samples matched a same-frame target record. Closest sampled tear
position to that frame's nearest-player-target center was120.89units;this is
neither all-target distance nor hit accuracy. Many tears had only one sample and
may have existed or disappeared between samples. No disappearance reason was
instrumented. Do not interpret0..120 as the weapon's effective maximum range.

The obstruction query consistently reports blocked geometry even when the nearest
target is closer than the range statistic. This rules out a simple distance-only
explanation for all of this observed stagnation. It supports obstacle/positioning
as an actionable problem together with the earlier near-wall motion evidence.
It does not quantify what fraction of shots actually collided or prove that
correcting position alone will produce learned combat success.

Primary independently parsed journal/decisions/oracle data,checked action count,
three stage receipts,raw enemy HP,all173 frozen hashes and in-memory fingerprint.
After normal shutdown,the primary bound the now-free port9528 and verified both
approval JSON/tmp absent,then restored byte-identical reviewed default-off source
cc81b2daa5c52437dcae042c3f6e702d18e053c546d9933b06985e9b1c271390.
Final output including raw traces/analysis was approximately3.3MB within256MiB.

Local evidence:reports/local/tear-audit-t6912-2/{result.json,menu.jsonl,console.txt,
game-log.txt,tear-lines.txt,analysis.json,geometry.json};runs/tear-audit-t6912-2-20261020/
contains the399 policy/oracle rows and canonical result. Restore receipt is
reports/local/tear-native-2-restore.json. Both native attempts together recorded
799 decisions and178.78seconds outer time;no more attempts scheduled.

## OpenSpec verification and self-review

Using openspec-verify-change for combat-tear-audit;primary self-review,not an
independent code review. Luna executed prepared commands only.

| Dimension | Result |
|---|---|
| Completeness | 4/4 tasks;2 added requirements;no removed/renamed requirements |
| Correctness | 2/2 requirements and4/4 scenarios mapped to implementation/tests;native facts checked |
| Coherence | Existing live scan/local logging patterns;bounded scalar state,no entity references,new callbacks or policy consumers |

Isolated bounded audit maps to mod/observer/main.lua:1018 and its literal-true/
live/context/time/scan/label/line guards. Measured-facts requirement maps to
tear_sample,target queries,owned tear selection and absence records. Behavioral
coverage in tests/test_lua_tear_diagnostics.py verifies disabled malformed flags,
wire equality,unchanged entities,ownership,trajectory/path,unknown optional APIs,
throwing/logging APIs,deadline/context/scan/lifetime/line bounds and BitSet128-like
non-scalars. Four added unsafe flag cases reproduce the scalar incompatibility
without coercion. Existing action/restart/encoding/reward tests remain in the
2044-case gate. Offline tests are distinguished from the two native attempts.

No critical issues or spec/design warnings remain for this diagnostic scope.
No inference/learning improvement claim;actual removal causes and effective
physical range are explicitly unmeasured. No applicable specification check was
skipped. Synthetic RL smoke not repeated:training stack/dependencies/checkpoint
behavior unchanged;existing full-gate model tests passed. Change unarchived.

## Limits and next action

No training or observation repair in this change. A geometry query is not a hit label;reported range is not a measured maximum,absence is not a collision cause,and one correlated trajectory gives no win-rate estimate. Globin/revival mechanics remain unverified by this scenario. The next concrete experiment is a separately labeled, bounded diagnostic baseline with an obstacle-aware approach and a reachable firing opportunity, to verify actual damage/reward before deciding between combat curriculum and observation changes. That baseline must remain separate from the learned policy and cannot be presented as learned play. Prepare a separate finite plan for that comparison. Any observation-schema repair requires explicit compatibility/lineage and must preserve legacy t6912.
