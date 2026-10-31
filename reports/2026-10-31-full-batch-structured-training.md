# Full-batch structured learner: final training report

**Stopped by the human October31,2026 at20:15:18.180143 UTC /21:15:18 CET.**
Final checkpoint **ee4f6599-s1-t22528**: **22528/150000 saved steps**,127472 short.
**127 completed episodes /22535 observed episode steps /22 train rows.**
Neither75k nor150k milestone was reached. Post75k growth is **not measured**;
no milestone report or result is imputed. stop.forever is retained; no retry/relaunch.

## Scope and evidence

Launched once October31 at18:48:31.557860 UTC /19:48:31 CET, source
`2b475b94d19158a60b262156a7ea629c7e21d4f1`; later979df33 is docs only.
Exact contract `ee4f65999d3a8cf0c85dabd5d887e360fd0823a164814bd20753d6dca91ac703`.
Rewardv12,observation9/11691inputs,action2 remain unchanged; historical manifest
reward_contract label pure-v11 does not identify this learner without its exacthash.
RecurrentPPO,seed1,file2,n_steps=batch1024,n_epochs10,targetKL.03,features512,LSTM256,
continuous_only withvariancefloor.1,structured_v1. No source/config/mod/save/Cloud
changes during training. Lua was not redeployed. All frozen source/config/deployed
hashes matched at stop; finalnormalizer is ContinuousVecNormalize with1423continuous
indices and the exact current mask. Finalmodel/normalizer/counts SHA matched manifest.

[Finite plan](2026-10-31-full-batch-structured-native-plan.md),
[offline verification](2026-10-31-full-batch-structured-offline-verification.md),
[launch](2026-10-31-full-batch-structured-launch.md).
Fixed ceiling November1 18:48:31.557860 UTC and150k target were superseded by the
human stop; neither was extended. One native session lasted5206seconds, exceeding
one hour. No8hrollover occurred, so resumed-entry behavior was not exercised here.

Evidence E=reports/local/full-batch-structured-20261031:launch/status/result,
user-stop.request,native-check.json,native-check-snapshot,final-summary.json,
final-freeze.json,final-cleanup.json,archive-before/after/final.json and supervisor
session-20261031-194831-0001 plan/menu/events/status/result. Owner stderr is empty.
All52 archivedv12files match launch archive-before.json after terminal rehash.
V11 and older archives/reports are preserved. Rawlogs/models are not committed.

## Main outcomes and equal-bound comparison

All three lineages use identical cumulative observed bounds **(0,22535]**. Whole
boundary episodes are assigned by cumulative endpoint, never split; actual selected
steps differ. Observedsteps include unsaved tails and differ from saved-model and
optimizer steps. These22535steps are the entire available run and its latest~50k
window; there is no50k-long window. Episode counts use CSVrows, not last sessionID.
V11 supports254782observedsteps andv12 173786; no extrapolation or imputation.

| Metric | structured cumulative/latest available | v11 common bounds | v12 common bounds |
|---|---:|---:|---:|
| Episodes with 3+ rooms | 6.3% (8/127) | 12.5% (12/96) | 2.3% (3/132) |
| Episodes | 127 | 96 | 132 |
| Actual whole-episode steps | 22535 | 22510 | 22480 |
| Exit-start | 54.3% (69/127) | 62.5% (60/96) | 52.3% (69/132) |
| Stall share | 74.0% (94/127) | 67.7% (65/96) | 76.5% (101/132) |
| Rooms / episode | 1.614 | 1.750 | 1.553 |
| Stage >=2 | 0.0% (0/127) | 0.0% (0/96) | 0.0% (0/132) |
| Never-left-start / stalls | 60.6% (57/94) | 55.4% (36/65) | 62.4% (63/101) |
| Stall-ended steps | 79.8% (17972/22535) | 74.7% (16822/22510) | 83.3% (18727/22480) |
| Collectibles total; /episode; /1k steps | 3; 0.024; 0.133 | 4; 0.042; 0.178 | 0; 0.000; 0.000 |
| Kills /1k steps | 2.840 | 2.799 | 3.959 |
| Clears /1k steps | 0.222 | 0.533 | 0.489 |
| Stall goal hops <1 / filled stalls | 79.8% (75/94) | 84.6% (55/65) | 89.1% (90/101) |
| Mean col_novelty | 1.55961 (127/127) | 2.03550 (96/96) | 1.29913 (132/132) |

The3+room goal>=25% is not met:8/127=6.3%, versus12.5% inv11 and2.3% inv12
at these early equal bounds. Rooms/episode1.614 are betweenv11's1.750 andv12's1.553.
This early stopped run cannot answer whether growth occurs after75k or establishes
better150k performance. Native layouts,one seed and changing policies limit inference;
no causal or frozen-policy superiority is claimed. Optimizer stats are separate from
progression. Never-left-start is rooms_visited=1 among stalls, excluding later returns.

## Reward episode means (available/selected)

| Metric | structured | v11 common | v12 common |
|---|---:|---:|---:|
| col_enemy_damage | 3.26825 (127/127) | 4.48508 (96/96) | 4.22728 (132/132) |
| col_room_clear | 0.39370 (127/127) | 1.25000 (96/96) | 0.83333 (132/132) |
| col_room_visit | 3.07087 (127/127) | 3.75000 (96/96) | 2.76515 (132/132) |
| col_floor_entered | 0.00000 (127/127) | 0.00000 (96/96) | 0.00000 (132/132) |
| col_damage_taken | -1.27165 (127/127) | -1.39062 (96/96) | -1.22727 (132/132) |
| col_death | -2.85827 (127/127) | -3.22917 (96/96) | -2.58333 (132/132) |
| col_time | -0.18073 (127/127) | -0.24022 (96/96) | -0.17316 (132/132) |
| col_pickup_coin | 0.01181 (127/127) | 0.02187 (96/96) | 0.00455 (132/132) |
| col_pickup_bomb | 0.00394 (127/127) | 0.00000 (96/96) | 0.00000 (132/132) |
| col_pickup_key | 0.00000 (127/127) | 0.00521 (96/96) | 0.00379 (132/132) |
| col_collectible_new | 0.11811 (127/127) | 0.20833 (96/96) | 0.00000 (132/132) |
| col_heal | 0.00787 (127/127) | 0.00000 (96/96) | 0.00000 (132/132) |
| col_novelty | 1.55961 (127/127) | 2.03550 (96/96) | 1.29913 (132/132) |
| col_stall | -2.96063 (127/127) | -3.38542 (96/96) | -3.06061 (132/132) |
| col_stagnation | -5.82605 (127/127) | -5.65743 (96/96) | -5.79267 (132/132) |
| col_door_shaping | 1.38192 (127/127) | 0.81370 (96/96) | 1.30482 (132/132) |

Reward totals from different contracts are not interchangeable gameplay scores.

## Optimizer measurements

All columns use recorded model bounds1024..22528,22rows each, separate from
observed-episode bounds. Empty prior-update timing is excluded without imputation.

| Metric | structured | v11 common model bounds | v12 common model bounds |
|---|---:|---:|---:|
| Rows; model bounds | 22;1024..22528 | 22;1024..22528 | 22;1024..22528 |
| entropy_loss | -3.60034 (22/22) | -3.74638 (22/22) | -3.76077 (22/22) |
| approx_kl | 0.00758 (22/22) | 0.02135 (22/22) | 0.02301 (22/22) |
| clip_fraction | 0.02551 (22/22) | 0.15622 (22/22) | 0.16237 (22/22) |
| explained_variance | 0.06047 (22/22) | -0.04158 (22/22) | -0.03048 (22/22) |
| Update seconds median;range;coverage | 13.234;8.344..20.015;21/22 | 10.953;2.437..16.859;21/22 | 10.625;3.203..20.719;21/22 |
| Updates <60s / measured | 21/21 | 21/21 | 21/21 |
| Entered epochs /rollout mean;range | 10.000;10..10 (22/22) | 6.682;1..10 (22/22) | 5.909;2..10 (22/22) |
| KL max;rows>.03 | 0.01270;0/22 | 0.05575;2/22 | 0.05154;3/22 |

All21 measured structured update times are below60seconds:median13.234s,
range8.344..20.015s. Delta n_updates is10 in22/22rollouts. Installedsb3-contrib
increments once per entered epoch, including a finalKL-rejectedattempt; this is not
an exact successful-gradient count. Fullbatch has one minibatch per epoch. KL,
clipfraction,explainedvariance and negativeentropy have22/22filled values. Mean
explainedvariance.06047 is below the.6native goal; this is an early stopped run.
Timing/KL/pause are descriptive, no halt guard,tuning or performance acceptance.

## Twenty-minute audit

Owner captured at **19:08:34.347345 UTC /20:08:34 CET**,t4096,
30episodes/4trainrows. Independent terminal read confirmed snapshot counts,
statistics and capturedmanifest hashes against the durable owner receipt.

- Exact contract matched; slot2 menu_entry_resolved Continue plus
  menu_continue_verified7keys are present.
- Model,vecnormalize.pkl andnovelty_counts.npz were SHA-verified by the owner at
  capture and the continuous-only class/mask checked. Historicalt4096rawartifacts
  follow normal checkpoint retention; finalt22528artifacts were independently read
  and SHA/class/mask verified at stop. The capturedmanifest/receipt remain.
- update_seconds3/4rows:median11.968s,range10.547..15.063,3/3below60.
- n_updates differences10/10/10/10:all4entered10epochs;not exactsuccessfulgradients.
- KLmean.00283935,max.00521154;clipfractionmean.00290527 (4/4each).
- Explainedvariancemean-.187028,range-1.333686...603674 (4/4);negativeentropy
  mean-3.756617. This does not establish value-fit or gameplay acceptance.

## Session exit and terminal cleanup

One session: user_cancelled,learnerexit0,fault=null,cleanup_errors=[],
status_writes_skipped=0. Launcherexit0 agrees with this result and does not conceal
another attempt. The unfinished rollout had no checkpoint aftert22528.
Read-only process inspection confirmed no game,worker/wrapper,finiteowner/wrapper
or Start-Pure launcher; listener9528 absent; deployedaction_authorization.json and
action_authorization.tmp absent. stop.forever retained. No forced termination needed.

## Frozen hashes and publication

- model.zip: `90b6e1a8757268fb56d4a044f488a7e0efb73073af071c0d41aad9c33af53434`
- vecnormalize.pkl: `77d6ddeb3365e538fa14b51e080aeb949301422b5b8548ba5d8adabbeaebecf7`
- novelty_counts.npz: `abd3df94c16479b7c622010d8609771d11d267f73bbb57a80697baed5755ca4c`
- configs/training-pure-v4.yaml: `99e8def55a86c6e4a42a1d289e1d20cfb84b43a943c0c1e0bf2391995f94a1b5`
- configs/reward-v12.yaml: `e4becfd631d92406470cfdf3307acfad76501466ddff4b0501a403bf68b925d9`
- C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\mods\isaac_threrisaifuture_observer\main.lua: `b647b712a4dc92d7fee21ce9031d0e2ef24c058f61292d56ba2e41b9969d8c50`
- C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\mods\isaac_threrisaifuture_observer\metadata.xml: `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`
- manifest.json: `1a871c84b2138a40eed8d588756dc537ae1ff3c3d1cff2147fff134ea879a602`

Prelaunch Check1583includingLua/no skips,SmokeRL and strict31/31 passed; one existing
syntheticAllNaNwarning. Report/docs/task-only whitespace,local-link and strictOpenSpec
checks passed at publication; no unchanged-code fullRL rerun. One-hour plumbing
verification task2.2 is now complete from the actual5206s session and Windowsgates.
Native150k/gameplay acceptance tasks2.3/2.4 remain open; no OpenSpec archive.
This report is self-review, not independent review. Monitoring is deleted on completion;
further training requires a human decision.
