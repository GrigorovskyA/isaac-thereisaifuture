# Native frozen combat progress diagnostic

- Date: 2026-10-21, Europe/Amsterdam; cleanup finished14:25:56 CEST /12:25:56 UTC.
- Revision: 9c222a6bfd4f3407b1b19c094bc77d36580dcd46; only unrelated errors.txt
  was untracked. No production source, configuration, mod deployment or dependencies changed.
- Purpose: qualify same-frame capture, native selected/accepted action binding,
  registered-progress stop and owned cleanup, without updating the learning model.
- Policy: frozen deterministic RecurrentPPO,7d53f55f-s20-t21760,training seed20;
  config7d53f55f92aae137da716f2916e4cc18db2c2594ef76bb58d2104bdb1e7ce4ee,
  reward live-conservative-v2; observation/action/reward schema1.
- Mod0.5.0-dev,Lua5.3,extender absent. Native game version/Steam build unavailable;
  do not substitute an assumed installed version.

## Finite experiment

The user requested continuation after the offline milestone. The primary announced
one frozen five-minute-maximum diagnostic, no weight update and no initial New Run.
The source/config/deployed mod/checkpoint/latest pointer and reviewed local helper
were frozen before dispatch. NativeRuntime preflight verified exact deployed mod,
no foreign process/approval/listener and the named compatible parent.

Assignment frozen-combat-progress-native-20261021-01:

| Setting | Declared value |
| --- | --- |
| Earliest experiment clock | Unix1792585432.3795393 |
| Start-before | Unix1792585522.3795393 |
| Absolute action stop | Unix1792585732.3795393 |
| Absolute cleanup stop | Unix1792585777.3795393 |
| Global action window | 300s including preparation/startup/entry/inference |
| Combined trace cap | 67108864bytes /64MiB |
| Total disk cap | 1073741824bytes /1GiB |
| No endpoint-progress window | 1800combat game updates /about60s |
| Faults/retries/initial replacements | 0/0/0 |
| Death stop/native restart ceiling | First death /1(protocol minimum approval ceiling) |
| Model updates/checkpoint writes | 0/0 |

Fresh gpt-6-luna/high, fork_turns=none, executed exactly:

```powershell
& 'D:\isaac\.venv\Scripts\python.exe' -u 'D:\isaac\reports\local\native-progress-20261021\diagnostic.py' --run
```

Helper SHA256 AD97B01467BA2BD351C6503634AD58ED0B0AA91279C365C7612B7D67E644CFD0;
assignment SHA256 0CF30D59CABE9D4B3B556565F7C81CE1B54D921F2ED3FDA55E3CF6FA6299FF5A.
The primary compiled/reviewed the helper before dispatch. It reused shipped
NativeRuntime menu/preflight/approval/cleanup, LiveClient, CombatNavigationGate and
CheckpointPolicy. The local driver reports frozen_inference, never combat_learning.
The worker waited for native Continue/file2 verification before gameplay commands.
No deployment, Git writes, source fixes, nested agents or lease renewal were delegated.

## Native observations and validation

| Check | Result | Status |
| --- | --- | --- |
| Menu | Fresh selected slot2, native Continue,7 guarded menu keys; no New Run | passed |
| Initial player | Character0/Isaac,session80dca441aa6c4bd9b05e5468d2024486,epoch1,frame44506 | passed |
| Captured combat | One handoff/one room visit0;563 decisions;frames44512->46312,exact1800updates;60.190s combat wall time | passed |
| Frame/vector binding | All563 before/after pairs validated against raw snapshots and encoder;0 mismatches/0 clipped values | passed |
| Native action join |563 selected records match563 native accepted commands by sequence/direction/context/frame interval | passed |
| Command-frame timing |503 commands at the policy frame,60 one frame later;all within captured intervals | passed |
| Progress guard | CombatDiagnosticStop at1800updates, before another action/reset;last native action expires at frame46312 | passed |
| Outcome labeling | One software boundary outcome unknown;no invented death/clear or diverse-room claim | passed |
| Capture bound |7525287bytes,563 paired records,no unpaired tail,under64MiB | passed |
| Cleanup | Worker exit0,normal owned game close,no errors,no game/listener9528/approval on primary readback | passed |
| Frozen source/parent | All64 frozen file hashes matched on primary readback,including latest/model/normalizer | passed |
| Full five-minute duration | Guard stopped early as designed | not_run |
| Learning/native updated-checkpoint restore | Frozen inference only;no learning/sample publication | not_run |

Last accepted action was sequence563 at frame46309; native expiry released its
hold at46312. No accepted action followed the diagnostic stop. The final result
is early_stop, not completed-duration learning. Cleanup completed at
Unix1792585556.1850667, well before the original action/cleanup deadlines.

Strict unchanged artifacts:

- Manifest9b39fce4114aa333f67abfcf8bd061936735b5f2b0841171a5e86122655f9f14.
- Model045f96ac5ae34c3d5db7584f3642dc5ed823fa4496d838ee416994fa6e64fca2.
- Normalizerca30e667a81cee27faac5e6229fb2e7d02f13d77596b02896be272b7788b06f7.

The approval ownership hash was recorded locally before launch and verified before
removal. Parent t7680,t7424 and original/migrated t6912 were not edited.

## What this shows about stagnation

527/563 after-poses(93.61%) were within5units of(70,410).526/563 requested movement
pairs(93.43%) displaced less than0.5units. Commands were left290/down273 and up
shooting563/563. At sampled endpoints, the two enemy identities retained10HP each;
player red health remained6 half-hearts. There was no registered endpoint HP-loss
lower bound or observed clear edge. This is sampled evidence, not proof of zero
actual damage or exhaustive terminal coverage.

The policy-only coarse45degree aiming proxy aligned with the nearest encoded enemy
in538/563 decisions(95.56%). That is direction geometry, not a hit/line-of-fire metric.
At the last endpoint the nearest enemy was roughly10 units right and210 units
above the player; shooting up was geometrically plausible. Visible obstacle
records also existed along that region, but41 obstacle records were omitted by
the source's capacity. Walking collision cells do not establish projectile
collision or actual line of fire. Weapon range was not exported. Therefore this
capture does not prove an obstacle, range or vulnerability mechanism caused failure.

This supports targeting the choice of firing position and blocked movement next,
rather than treating every shot as random or simply paying for proximity.
Reproducing corner concentration under one deterministic frozen checkpoint is not
a model-quality comparison, training-seed study or proof of its stochastic behavior.

## Evidence, verification and next action

Private artifacts are under reports/local/native-progress-20261021:
assignment.json,diagnostic.py,session/{runtime.json,approval-owner.json,menu.jsonl,
live.jsonl,events-oracle.jsonl,worker-result.json,result.json,status.json,console.txt,
combat_gate/diagnostics/{policy.jsonl,oracle.jsonl}},native-game-log.txt,
analysis.json,extra-analysis.json,native-action-join.json,primary-hashes.json.
The primary independently revalidated the logs, raw pairs, accepted commands,
resource bounds, unchanged64 hashes and process/listener/approval cleanup.

OpenSpec verify/self-review: native capture/progress-stop/cleanup scenarios now have
real evidence. Overall combat-progress-diagnostics remains3/4: task2.1's full
five-minute qualification was not completed; no archive or duration escalation.
Storage remains4/5 because no native update/interruption/restore was tested here.
No production code changed, so the prior2229-test/48-item offline gate still applies;
strict OpenSpec validation is repeated for documentation. Raw logs/models/approvals
are not published. This is primary self-review, not independent review.

Next implementation: versioned legitimate weapon-range/type and firing-position
evidence, including valid target/line-of-fire checks; then bounded progress shaping
with no standing/empty-shot/oscillation bonus. Do not turn a walkability grid into
a claimed shot-clearance oracle. Preserve t21760 and explicitly plan any new
observation/reward lineage. Compare real damage taken/dealt and clears after a
new bounded5min qualification,then15-30min,1h,and only then a new4h request.
The single Continue diagnostic is closed;no automatic second launch or New Run.
