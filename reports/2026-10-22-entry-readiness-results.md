# Evidence: no-action entry visibility and bounded readiness

- Date:2026-10-22,Europe/Amsterdam. Captured native revision
  `e2abe5274c740d45b99583da298c532823e2bedc`; readiness correction is subsequent.
- Active OpenSpec change:`exposed-start-curriculum`,8/9tasks complete;4.3unfinished.
- User accepted the proposed short observation;one fresh assignment only,
  `entry-observation-20261022-01`. No curriculum retry or training was authorized.
- Parent:a0a93c29-s20-t26368,seed20,observation2/723,rewardlive-firing-v5,
  collectorlive-segment-refresh-v1. Model/normalizer/all ancestor pointers read-only.
- ConfigSHA256a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15.
- Default-off source/deployed Lua unchanged;observer0.5.0-dev,Lua5.3,Python3.12.14.
  Game build unavailable. No deployment,dependency,save/Cloud or unrelated changes.

## Results

| Check | Status | Evidence |
|---|---|---|
| Prepared observer helper | passed:4 offline guards | local/exposed-start-refusal-observation-20261022/helper-check-result.json |
| Native no-action observation | passed,exit0,31.589s inclusive cleanup | local/exposed-start-refusal-observation-20261022/session/result.json |
| Primary trace/hash readback | passed,1189/1189 inputs unchanged | local/exposed-start-refusal-observation-20261022/primary-analysis.json |
| Corrected readiness on captured native trace | passed offline:61 samples, 3.031s, 0 commands | local/exposed-start-refusal-observation-20261022/entry-replay-result.json |
| Focused source checks | passed: 74 tests,lint/format/mypy | final full gate also includes these |
| Final Windows Check.ps1 | passed: 2416 tests, 0 skips; 66 mypy files; 56 strict items; 718/718 frozen inputs matched | local/exposed-start-refusal-observation-20261022/full.log |
| Corrected native movement/handoff/update/damage | not_run | observation assignment is closed;task4.3 remains unfinished |

## Native evidence and diagnosis

Fresh Steam launch and guarded file2 Continue;ordinary Isaac,room83,
session444591a9810b4ba49fbf63d2d3b42472,epoch1,roomvisit0.
One 60s maximum inclusive lease,45s startup ceiling,5s/100snapshot capture,
16MiB output,zero movement/shooting/training/reset/restart/fault/retry/NewRun.
Actual capture: 100 snapshots over 4.984 wall seconds; 673202 bytes at terminal readback.
No source or game control by primary while the Luna/high worker ran.

Samples1-60:oracle memberships[1,2],visible enemies empty. The fixed-target
precheck refused. At sample61(frame78917),both enemies were visible;target1
was at(80,200) and shared its identity with oracle membership. Samples61-100
passed the unchanged precheck. First frame78914;only3game-update IDs elapsed
before eligibility,whereas observed receipt time increased3.031seconds. Report
both spans;do not substitute 3/30 for the measured startup wall delay or claim
an exact engine mechanism. This establishes delayed visible readiness in this
attempt;the preceding failed pilot did not retain its initial snapshot,so its
identical refusal is consistent with this finding,not retrospectively proven.

Player position stayed(560,280),observed health stayed5half-hearts. No actions,
policy inference,normalizer updates or learner rewards occurred. The capture
explains an entry predicate;it does not evaluate learned play or prove zero
unobserved damage. The source/deployed observer was not changed.

Release command sequence1 was accepted at frame78976. Peer disconnect,normal
successful game shutdown and observer close/unload are in native-game-log.txt.
Worker exit0;no cleanup errors;game/listener/owned approval absent. Primary
verified every1189frozen input after completion,before changing source/specs.
All checkpoints and latest pointers remain unchanged. Normal game's save delta
was not measured;no manual save writes. Raw records remain local and untracked.

## Correction and acceptance boundary

The existing setup immediately refused the first target check. It now waits
without commands only if all other entry checks pass and no enemy is visible.
The wait is capped at5seconds/100snapshots including the initial snapshot,inside
setup's existing30seconds and the fixed outer lease. Every queued sample is
checked in order;health loss,context/grid/weapon/door/oracle-membership changes,
cancellation or deadline exhaustion refuse before movement. Once enemies are
visible,the original fixed target must pass immediately;no substitute or wider
tolerance is allowed. Initial/ready observations and wait provenance are logged.
Caps are explicit in the pilot manifest. Default modes,reward,policy inputs,
normalizer,recurrent state,hyperparameters,lineage and Lua contracts are unchanged.

Regression coverage includes visibility at sample61;zero earlier commands;
health/context/grid/weapon/death/door/membership changes;own and shared deadlines;
snapshot limit;user cancellation;wrong visible target before/after waiting.
Offline replay feeds the saved 100 native snapshots through the actual readiness
function with their recorded receipt times. It returns at sample61,target1,
3.031seconds,without a client command. This is offline replay,not a new native run.

OpenSpec self-verification maps the added readiness scenario to the helper,
regressions and native-input replay. No independent code review is claimed.

| Dimension | Status |
|---|---|
| Completeness | 8/9 tasks; task 4.3 native qualification incomplete |
| Correctness | 4 added requirements implemented; readiness scenario covered by regressions and captured-input replay; corrected native handoff not verified |
| Coherence | Existing opt-in setup/collector separation and fixed budgets preserved;no policy/Lua/lineage changes |

Critical: task 4.3 remains incomplete. The corrected successful native learner handoff, real
optimizer update, native learner damage and saved learned-child reload in 4.3 are
not verified. Do not archive or promote a model. The no-action observation lease
is consumed. Next is a separately planned fresh five-minute curriculum pilot with
an absent child root and the exact preserved parent;do not resume the closed
pilot or reuse its approval. No duration escalation is justified by this capture.

Primary read back complete gate output and all718frozen hashes. Only this report
and STATUS text changed afterward; source/tests/spec/config stayed frozen.
Gate receipt total 50.2s conflicts with pytest 55.17s and file timestamps;do not
use that total as accepted timing. Counts, exit 0 and input identity are verified;
a separate local timing correction preserves the original receipt.
