# Evidence: extended conservative-v2 continuation

- Date:2026-10-20,Europe/Amsterdam.
- Base revision:5d698822797851ca2fddce0f7d60b07f71490ae9 plus extended config/plan.
- [Pre-execution plan](2026-10-20-extended-conservative-plan.md):at most three
  enumerated sessions/45min/30deaths;target12288 cumulative saved steps.
- Native Windows,Python3.12.14,Repentance+1.9.7.17,observer0.5.0-dev,Lua5.3,
  RecurrentPPO/torch2.14.1+cpu. Ordinary authorized file2,not an isolated profile.

## Budget-only continuation

The primary compared complete non-budget configs and found them identical.
Only total_timesteps4096→12288 and wall_time_minutes15→12 changed.
New config hash08e0d2627b5cdac2d0be36ff2d19578496a58e9632defa50a67ae7a7653f2d8e;
file SHA1a45759bccb5d0535efbe7ce2980a8cdd3177e899864d0c085c4f0bb741013d0.
Model and normalizer were copied byte-identically from92969b7f-s20-t1536 into
08e0d262-s20-t1536;new manifest changes only config hash,ID,parent pointing to
the source t1536. RNG/schema/reward/seed/algorithm values match exactly.
Primary loaded the migrated model at1536 steps/24PPO updates and observation
count1537.0001 before dispatch. All invocations used --resume;no initialization
or weakening of compatibility checks. Local budget-extension.json records provenance.

## Results and actual stopping point

| Check/scenario | Command | Exit | Status | Evidence |
|---|---|---|---|---|
| Full Windows gate | `./scripts/Check.ps1` | 0 | passed | 1995 pytest passed,zero skipped/failed;Ruff/format/mypy/pip clean;OpenSpec36/36 |
| Synthetic stack | `./scripts/Smoke-RL.ps1` | 0 | passed | 16 CPU steps/save/load/predict;not Isaac proof |
| Controlled artifact migration | Strict loader,binary/hash/non-budget comparisons | 0 | passed | Same model/optimizer/normalizer/RNG state at t1536 |
| Native session1 | Frozen helper with exact planned CLI arguments | 0 | passed | New2/Isaac,5597 decisions,three deaths/restarts,zero faults |
| Session2/session3 | Conditional repetition | — | not_run | Session1 stopped on time rather than tenth death;no repetition permitted |
| Target12288 | Declared cumulative target | — | not_reached | Final saved t6912;12min controller cap stopped first |
| Models/lineage/cleanup | Primary readback | 0 | passed | 21 new checkpoints,all83 frozen files unchanged,normal shutdown/no approval/listener |

Wrapper SHAe540ea25c5d7cee9eb0fb7b8adc69a3e5668ad94dad5274eb76d9fadd1c2ff97.
One invocation;no retry,lease renewal or unplanned session. Runtime/wrapper exit0.
Elapsed746.47s (12min26.47s including startup/cleanup). Controller stopped on
`Live wall-time budget exhausted`,not death cap. No claim of a45min or30death run.
Its repeat condition correctly stayed false. This verifies the executed bounded
continuation,not native execution of all three enumerated sessions.

## Real-game identity and complete outcomes

Local menu reached file2 New Run in eight guarded keys;initial active Isaac0,
session0d7acfbbc0374a02b79d92e7169af694,epoch1/frame0. Native New2 seeds:
MZ6YWSXB,DF7XTTK9,8LTLBKW9,AZEX27H7. Three native restart confirmations
establish epochs1→2→3→4. No game/save/Cloud/Steam-option edits or screenshots.
Normal game persistence writes occurred. Gameplay remained on the structured bridge.

All completed gate segments,including failures and software truncations:

| Handoff | Outcome | Decisions | Return |
|---|---|---:|---:|
| 1 | unknown | 519 | -10.300333 |
| 2 | unknown | 570 | 0.099667 |
| 3 | unknown | 556 | 0.799667 |
| 4 | unknown | 575 | -0.600333 |
| 5 | unknown | 565 | -0.600667 |
| 6 | unknown | 562 | -0.600000 |
| 7 | empty | 112 | 1.284333 |
| 8 | death | 38 | -55.656000 |
| 9 | empty | 44 | 0.492128 |
| 10 | death | 103 | -71.020000 |
| 11 | death | 88 | -66.101000 |
| 12 | empty | 292 | 1.083333 |
| 13 | unknown | 399 | 2.199333 |
| 14 | unknown | 399 | -7.200000 |
| 15 | unknown | 396 | -0.250333 |

Handoff16 remained unfinished at the wall stop,379 decisions;it is not another
completed outcome. All16 handoffs accepted;42.423s total gate wait,eight visit
changes during waits,zero reported faults/resume races/observation gaps.
Unknown outcomes are software time boundaries;empty eligibility is not proven
room-clear/win evidence. Exact kill rewards remain withheld;zero derived kills
does not establish zero actual kills.

## Saved learning and preservation

5597 combat decisions =5376 newly checkpointed +221 unsaved final-rollout samples.
New checkpoints t1792..t6912 in256-step increments,21 total plus imported t1536.
Parent chain is contiguous and links back to original92969b7f-s20-t1536.
Latest08e0d262-s20-t6912,model timestep6912,PPO update counter24→108;
all20 policy tensors changed between imported source and final checkpoint.
Normalizer observation count1537.0001→6914.0001,return count1536.0001→6912.0001.
Resume must use6912,not7133 (which would falsely include discarded samples).

Final model SHA9b8e7eaa8aa89cc23debc82e99f26c365a24c617f63bbd6f5676b7ed350a22f4;
normalizer SHAd5ec622cf5dd653b7ac5bc8070693ddb0c5b65768f4d90c6bb3ba95ceaba6fd0.
Primary verified all manifests/config/reward/seed/parent values,loaded first/final
models and every saved normalizer,then checked all83 frozen file hashes,
including both old roots and imported state. Original t1536 and t8960 histories
are unchanged. Native output approximately223.9MB within512MiB;offline temp
grew86,093,048B within its separate512MiB allowance. Approval13.5min/max_restarts9
was removed by exact hash;source/default installed observer stayed identical and
diagnostics off. Native successful shutdown,absent process/port9528 and approval
were independently verified after the worker returned.

## Learning limitation and next decision

Three consecutive completed minute-scale software segments recorded no enemy HP
removed. Across12 complete environment summaries (not all gate-only/unfinished
segments),reported HP removed112.0,damage taken19 half-hearts. These are approximate
training labels,not an evaluation score.
The zero-credit intervals do not prove no hits:conservative HP floors deliberately
withhold renewed damage credit after healing. Correlated native phase evidence is
needed to distinguish weak targeting from healing/revival and credit suppression.
Native accepted action counts5683 include
navigation as well as policy commands:movement none1229/down1171/left1202/up926/
right1155;shoot none1198/left1140/up1082/down1129/right1134. There is no evidence of
a permanent single-command lock,while effective targeting remains weak/unverified.
This does not prove a room was cleared or the policy improved.

Primary self-review:plan/config migration preserves learning semantics and all
state;resume/step accounting,deadline/non-repetition,source integrity and cleanup
match the executed evidence. Existing OpenSpec contracts remain unchanged and
all36 strict items pass. This is not independent review;no change is archived.
One development seed,uncontrolled native game seeds,no held-out evaluation or
checkpoint-selection claim. Revival/champion coverage remains pending.
Next:inspect combat stagnation/target visibility and run comparable frozen-policy
evaluation before increasing the budget again. Preserve exact extended latest6912.

## Local evidence inventory

Ignored reports/local/extended-{check,smoke}*.txt/json,extended-frozen.json,
extended-conservative/{plan,result,acceptance-analysis,combat-metrics}.json and
session1/{plan,result}.json/menu.jsonl/console.txt. Session:
runs/live-conservative-v2-extended-20261020/sessions/20261020-195909-8b184c.
The native log exceeded the worker's2MiB full-copy cap. A primary read-only bounded
collector retained11 essential seed/restart/shutdown markers (1626B),without
altering game/budgets. After closure,the primary matched its session identity and
captured the2,681,459B native log under an8MiB read cap for final verification.
These private raw logs/models/approval records are excluded from publication.
