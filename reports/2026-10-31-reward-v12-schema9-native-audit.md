# Reward v12/schema9:18-minute native audit

October31,2026,06:49:15UTC /07:49:15CET. Source4c5893762692b06279747c71b58685fffa97a9db
remains frozen; later05c8fa5 changed launch docs only. Contract
`1a6d8146f5e89b7bdad14fe21d3afa9cc1f5c4192b8e5f24cefb6bbab0e0c8d8`.
[Launch receipt](2026-10-31-reward-v12-schema9-launch.md),
[finite plan](2026-10-31-reward-v12-schema9-native-plan.md),
[offline verification](2026-10-31-reward-v12-offline-verification.md).

The prepared owner audit passed with no fatal errors. A separate read of raw passive
samples,CSV rows and checkpoint bytes confirmed the required cases below. This is
primary self-review, not an independent reviewer or frozen gameplay evaluation.
Training remains active, fault=null; game/worker/finite owner processes are present.

Evidence root E=reports/local/reward-v12-schema9-20261031. Owner native-check.json
and native-independent.json use the same06:49:15.428710UTC cutoff. Raw audit items/
steps/errors, supervisor menu/events/status/plan and metrics are retained locally.
No source/config/mod/save/Cloud changes or manual retries occurred.

| Check | Status | Native evidence / denominator |
|---|---|---|
| Exact contract | passed | Checkpoint1a6d8146-s1-t4096 manifest matches expected hash; saved4096 model steps |
| Completed episodes | observed | 27 rows,22 stall-ended episodes; this is not a gameplay success measure |
| Stall idle clock | passed for encountered cases | 22/22 passive terminal transitions,30.000..30.188 active game seconds; episode duration/time-in-room not substituted |
| col_stall | passed | 22/22 CSV stall episodes exactly-4.0; per-transition stall component agrees |
| Full col_stagnation | passed | 22/22 CSV stall episodes-7.02 within floating-point precision |
| Learner stall flags | passed | 22/22 terminated=true,truncated=false; CSV remains truncated/stall |
| Persisted novelty counts | passed | t4096 novelty_counts.npz SHA matchesmanifest;256 keys,maxcount21 |
| Repeat-cell decay | passed in sampled evidence | 689/783 positive starting-room payments below0.099 |
| Entry decision | passed for initial start | menu_entry_resolved slot2/new-run then menu_new_run_verified,8 bounded keys |
| Snapshot transport | passed in sampled evidence | 1035 decoded samples,maximum12501 bytes <131072;1035/1035 tag vectors contain8 numbers |
| Decode/audit errors | passed | No error records at cutoff |
| Train statistics | passed | All9 required statistics filled in4/4 train rows,36/36 values |
| First8h rollover | not_run | Initial New Run is not proof of resumed New Run after lease-end death |
| Native gameplay acceptance | not_run | One seed,changing policy,no held-out/frozen comparison or progression claim |
| Terminal cleanup | not_run | Training remains active |

Recorded model timesteps1024..4096,4 rows: mean entropy_loss (negative entropy)
-3.78131,approx_kl mean0.01404/max0.02457,clip_fraction mean0.09926.
Update_seconds has3/4 measured rows: median17.969s,range14.094..20.719s;
first timing blank is excluded. Timing/KL are descriptive, not stop thresholds;
pause failure alone never stops. Optimizer statistics do not prove improved play.

The initial menu evidence verifies New Run on positive file2 absence. The separate
requirement to resume latest after a death immediately before the first lease rollover
remains open. Inspect the first transition around14:30UTC /15:30CET; if that exact
precondition is absent, report it as unencountered. Do not manufacture a death.
Reward native one-hour/performance/comparison tasks and session-start native resume
task remain open. No OpenSpec change is archived.

Continue unchanged to first saved>=300000 or fixedNovember1 12:31:15UTC /13:31CET,
whicheverfirst; faults/required audit failures stop without manual retry. Reports
at50k/150k/300k compare v11 only at equal available observed-step bounds. Routine
15-minute checks stay quiet. Archive v11t253952 and earlier lineages remain preserved.

Publication checks: git diff --check/local Markdown links and strict OpenSpec30/30;
no full RL rerun for this report-only update. No local evidence/models/raw logs staged.
