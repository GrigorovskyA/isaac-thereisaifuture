# Live conservative reward correction

- Date:2026-10-20,Europe/Amsterdam; dirty Windows checkout,existing unrelated changes preserved.
- Base revision b973a2c; Python3.12.14/project virtual environment; actual t8960 parent hashes
  recorded in the native plan and prior checkpoint verification. Native random mode
  has no learned policy/config update. Current mod remains0.5.0-dev; no Lua deployment.

## Scope and implementation

OpenSpec live-reward-continuity, following the t8960 reward diagnosis. Absence no
longer emits remaining-HP damage or kills. Actual kill bonuses are withheld:
there is no verified death channel in current snapshots. Only continuous complete
membership with a new HP low earns damage reward. Per-identity floors survive
software resets in the same bridge session/epoch; gaps lower floors without
retroactive reward. Max-HP changes disable further credit for that identity.
History is capped at4096; exhaustion faults without eviction/renewal.

New manifest reward_contract defaults legacy files to combat-v1. Production live
training requires live-conservative-v2; generic/synthetic training remains
combat-v1. Resume checks the contract before constructing an environment. This
versions accounting semantics while observation/action/event payload schemas stay1.
Old files/latest pointers are untouched and frozen inference remains supported.
New manifests are readable by this version; older strict readers may reject the
new field. No implicit conversion or fresh model initialization was added.

Scope limit: bridge identity continuity is not a campaign-wide physical enemy
lineage. Room re-entry can assign new IDs; cross-process/campaign anti-farming
is not established. No migration/warm-start or clean-baseline decision is made.

Operator observation during the native check: the enemy becomes a pile after
apparent death and revives if the pile is not finished in time; the controller
does not finish it. This explains a plausible gameplay cause for the prolonged
encounter. It is user-provided visual evidence,not native callback/identity proof
or an audited enemy classification. The current check uses random actions,not
the t8960 learned policy,so this behavior is not a policy evaluation. Do not add
a hard-coded targeting strategy. A later observation audit should verify whether
the visible vulnerable phase is represented,without leaking oracle state.

## Offline verification

Bounded gpt-6-luna/high workers executed primary-supplied commands only. Primary
inspected logs and before/after/current source hashes, not just worker summaries.

- Initial targeted mypy:exit0,47 files; targeted pytest92 passed in24.89s,zero
  failures/skips. Six protected Python file hashes unchanged during that run.
- First full Check:exit1,1936 passed/one failed/zero skipped,in46.22s. The old
  combat-gate test expected a disappearance bonus (`7.999 > 8`). Changed the test
  to assert exactly8 clear reward,zero unobserved damage/kill and the elapsed
  combat cost. No implementation guard or gate criterion was weakened.
- Final Check:exit0,1937 passed in45.87s,zero skipped; Ruff,format113 files,
  mypy47 files,pip consistency and32/32 strict OpenSpec validations passed.
- Smoke-RL.ps1:exit0,16 synthetic CPU steps,save/load/predict passed; torch
  2.14.1+cpu,CUDA unavailable. It does not verify Isaac.

Logs: reports/local/reward-continuity-targeted-*,reward-continuity-full-* and
reward-continuity-final-*. Final before/after manifests contain111 identical
Python path/hash entries; primary verified current files also match. Behavioral
coverage includes eight real Gym resets with repeated healing,persistent absence,
reappearance,reset/overflow gaps,namespace versus visit changes,max-HP mutation,
4096-identity exhaustion,legacy/matching manifest compatibility and saved contract.

Primary reloaded actual t8960 for frozen inference and verified its exact identity,
manifest/model/normalizer hashes and latest pointer. New live resume rejects it
explicitly as combat-v1 != live-conservative-v2. No learned weights changed.

## Native check budget (recorded before launch)

One Luna execution of reports/local/Run-RewardContinuityCheck.ps1,working D:\isaac.
Fresh Steam launch,existing installed observer must byte-match source; no deployment.
Menu-only file2/Continue,never New Run. No pre-existing instance/approval/listener.
Seed20 random management/combat check,NOT learning:steps1200,minutes3 after
connection,connection/startup cap120s,absolute global wall cap360s from preflight.
Disk512MiB,maxfaults0,maxdeaths1,one possible natural restart,gate90s,navscale1
(256 commands/90 pulse seconds/four transitions). No retries or budget renewal.
Approval lease342s,not beyond global deadline. t8960 triple hashes/latest must
remain unchanged. No training/checkpoint writes allowed.

Pinned menu helper uses the existing focus guard and only Isaac-window captures.
At most12 menu presses for intro/title,file2 selection and Continue; no gameplay
keys. Focus refusal,missing Continue,unrecognized screen or inability to prove
file2 stops setup with normal closure. Worker observes progress under the same
absolute deadline and closes only the owned instance. Wrapper immediately closes
normally on runtime return,then verifies process/listener/approval cleanup and
unchanged model. The primary independently reads resulting evidence. A scenario
ending before a software boundary does not pass continuity acceptance.

## Separate self-review and OpenSpec verification

Using openspec-verify-change for live-reward-continuity (spec-driven),against
proposal,design,both delta specs,tasks and the final source/test diff. This is
self-review by the primary,not independent review.

| Dimension | Finding |
| --- | --- |
| Completeness | Implementation tasks1.1..1.3 and offline gate2.1 complete; native2.3 pending until observed. |
| Correctness | All four added/modified requirements map to derivation,manifest/train validation and behavioral tests. Native software-boundary check pending; true kill channel is explicitly not implemented. |
| Coherence | Bounded Python-only adapter state,explicit contract compatibility,unchanged policy/oracle separation and conservative stop behavior follow design. |

Reviewed namespace reset versus native visit rebaseline,max-HP mutation,overflow
at both endpoints,initial membership,absence and permanent disappearance,history
exhaustion,segment-local ledger seeding and early resume rejection. No additional
code defect found. Legacy frozen load was verified on the actual model,not a
fixture. Strict OpenSpec validation and whitespace checks must pass on final docs.
Native results below satisfy the continuity smoke scenario. Phase visibility and
confirmed-death delivery remain outside this correction and are not implied.

## Native results

Passed bounded continuity check: session runs/live/sessions/20261020-144041-5e32c3,
bridge89254ced40264424a526d910ab20d54d,game1.9.7.17 (window title),mod0.5.0-dev,
Lua5.3. Primary inspected menu-4.png: FILE2 selected; worker proceeded through
Continue. Fresh connection epoch1/visit0,initial event frame12416. Runtime exit0;
wrapper process numeric exit was not retained after its exec session expired.
Do not report that missing wrapper code as passed. cleanup.json,close.txt and
native successful-shutdown log were retained and independently verified.

1200 random decisions,three accepted handoffs,one unknown segment559 decisions/
1802 updates,one empty gate exit497 decisions,and144 final decisions. Same
session/epoch/visit across the software boundary. No death,restart,room transition,
resume race,observation gap,withheld action or cleanup error. Management waits3.53s;
reward -0.543 is not a policy-quality measure. No learned weights were used/updated.
Total preflight-to-cleanup183s <360;startup approximately49s <120,controller runtime
approximately133s <180. Stopped at1200 decisions,without budget renewal.

Native derived events:13 spawn baselines,15 damage labels,one player-damage label,
zero kill/clear labels. Entity4/maxHP20 was baselined eight times at frames12416,
13517,13931,14114,14226,14768,15154,15858. Its damage credits total17.5,all before
frame13505; later reappearances/software resets gave no additional damage labels.
This is installed-game continuity evidence,not an exact native healing/death trace.
The operator's pile/revival observation supplies gameplay context,not a proven
mapping between that visible phase and a specific logged identity.

An empty gate exit at time1792500206.68 resumed combat in the same visit roughly
0.24s later. Combined with the operator observation and IsActiveEnemy(false)
filtering,this raises a visible-phase acquisition/gating concern. It does not
prove the vulnerable pile was omitted; raw phase/type snapshots were not recorded.
Next action is a bounded structured audit of visible target membership and phase
availability before changing policy inputs or scripting a targeting strategy.

Normal WM_CLOSE,Observer unloaded and successful native shutdown. Primary verified
no game process or port9528 listener,exact approval absent,current source hashes
matching final gate,and unchanged t8960 manifest/model/normalizer/latest. Disk
353046519 bytes <512MiB. No extra close/relaunch or manual user menu assistance.

## Final assessment and continuation

OpenSpec6/6 tasks complete for this conservative scope; all four added/modified
requirements have implementation and behavioral coverage,plus native continuity
smoke. No skipped offline checks. Limitations: wrapper exit status not retained,
no exact kill channel or campaign identity proof,and revived-phase visibility not
verified. Change left unarchived. Navigation's earlier post-clear/checkpointed
sequence remains pending; this random check does not satisfy it.

Do not resume learning until the visible-phase concern is resolved and an explicit
compatible lineage plan exists. t8960 stays preserved; a future warm-start must
identify the legacy parent,changed reward contract and reward-normalization
treatment. Do not silently relabel the old checkpoint,drop --resume or initialize
another model to bypass compatibility rejection.
