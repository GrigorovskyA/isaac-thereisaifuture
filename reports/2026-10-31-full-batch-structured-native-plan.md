# Full-batch structured learner: finite native plan

Human authorization October31,2026, current chat: run Check.ps1,Smoke-RL.ps1 and
strictOpenSpec; publish prepared full-batch/continuous-only/structured changes;
archive v12 with t173056 hashes; keep deployed Lua unchanged; close dashboard;
initialize once; audit first20minutes; reports75k/150k versusv11/v12 at equal steps.

## Identity and limits

Config configs/training-pure-v4.yaml, rewardv12, observation9=11691/action2,
contract ee4f65999d3a8cf0c85dabd5d887e360fd0823a164814bd20753d6dca91ac703.
Seed1,RecurrentPPO,n_steps=batch_size1024,n_epochs10,targetKL.03,features512,
LSTM256,continuous_only normalization (variance floor.1),structured_v1 features.
Reward/observation/action content unchanged. Source commit is frozen before launch.
Manifest reward_contract pure-v11 label is historical; exact hash distinguishes it.

One Start-Pure.cmd --initialize. Interpret150k as the finite target: stop at FIRST
saved checkpoint>=150000 or24hours after actual launch, whicheverfirst. The finite
owner records the absolute UTC deadline once; no extension. Compatible automatic
8h native lease rollover only, resume latest under same deadline. Disk cap
20480000000 bytes. Any session fault/invalid contract/artifact stops via stop.forever;
no manual retry,relaunch,reinitialization or tuning while running. Death/stall New
Runs remain authorized within these limits; session entry Continue or fresh positive
file2 absence -> New Run. Never force a scenario or alter saves/Cloud.
Human stop writes E/user-stop.request AND runs/pure-v4/supervisor/stop.forever.

## Preparation and publication

E=reports/local/full-batch-structured-20261031. Authoritative Windows Check includes
installed Lua JSON with isolated test-only Lua runtime and process-local TEMP/TMP.
Smoke is synthetic stack/save/load evidence, not native speed or gameplay proof.
Review relevant diffs, staged files and gates; publish to existing origin main.
Exclude tools,runs,reports/local,models,raw logs,approvals and unrelated files.
No OpenSpec archive; native tasks stay open until their exact evidence exists.
Verify no active game/worker before moving runs/pure-v4 to
runs/pure-v4-reward-v12-schema9; hash every file before/after and verify finalt173056
model f1de153d2b7f5728001ae711eccab5b017b8500784623ed12b0098764ef60c0d,
normalizer ee7d9eeb5e76f22d5930b01ad788fa1908e1017f84b3ad84fbf3e8bdac200694,
counts 3d61432b47611c28eb3053775a9b03d5c885c176691ce04636bfc885f7ad3d30.
Preserve all older archives. No redeployment: deployed main.lua must match
b647b712a4dc92d7fee21ce9031d0e2ef24c058f61292d56ba2e41b9969d8c50,
metadata00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997.
Close only identified project dashboard processes. Never open/activate any window
for monitoring; the native guarded menu owns focus. Read-only process checks allowed.

## Twenty-minute audit

Owner captures E/native-check.json at20minutes with a copy of metrics/manifest.
Independently verify exact hash, menu_entry_resolved plus matching verified entry,
vecnormalize.pkl and novelty_counts.npz present together with manifest SHA matches;
normalizer class/mask consistent with continuous_only. Report checkpoint and filled
row denominators. Inspect update_seconds median/range, count below60s, KL,
clip_fraction,explained_variance,negative entropy. update_seconds records prior
update timing and first row per session can be blank: no imputation.
Derive per-rollout epochs entered from successive n_updates differences (initial
counter0 for fresh run). Installed sb3-contrib increments once per epoch including
a KL-rejected final attempt: these counts are not exact successful gradient steps.
Full batch means one minibatch per epoch. Record early-stop limits honestly.
Timing<60s is a measured target; timing/KL/pause alone do not auto-stop or trigger
changes. Missing required identity/artifacts/stats/menu evidence stops and reports.
No native progress or acceptance claim from optimizer statistics.

## Milestones and monitoring

At first saved>=75000/150000 capture E/milestone-TARGET metrics+manifest and verified
artifact hashes. Publish English reports, update STATUS/TRAINING_SESSION in place.
Compare against v11 (254782 observed steps) and archivedv12 (173786 observed steps)
ONLY at identical cumulative observed bounds <= each available limit. Whole episodes
assigned by cumulative endpoint, never split; actual steps/episode denominators shown.
Observed episode steps include unsaved tails, distinct from saved model/train timesteps.
No extrapolation or imputation. Main outcomes: rooms_visited>=3 episodes/count/share
(goal>=25%),rooms/episode, change after75k. Report cumulative and latest~50k windows;
at150k compare (0,75000] vs(75000,150000] and recent~50k for post75k growth. Also report
exit/stall/stage>=2/collectibles/kills/clears/damage, optimizer stats and epoch deltas.
One seed and changing policies do not establish frozen-policy or causal superiority.

Every15minutes check actual game/worker/finite owner plus fresh status,events,
episode timestamps and checkpoint advancement; process presence alone is insufficient.
>10minutes no advancement -> bounded logs and possible-stall notice, never retry.
Healthy unchanged state stays quiet. Notify Russian meaningful audit/milestone/fault/
completion only. Schedule reports/monitor under this plan, not training launches.

## Terminal handoff

Retain stop.forever. Inspect ALL session exits/fault/cleanup_errors/status_writes_skipped;
launcherexit0 cannot erase faults/unverified release. Verify actual absence of game,
worker,finite owner,Start-Pure,listener9528,deployed action_authorization.json and.tmp.
Freeze final model/normalizer/counts/manifest/source/config/deployed hashes and archive
integrity. Report actual end date/reason/achievedsteps vs150k/audit/rollover/cleanup/
baseline limits; reports/docs-only whitespace,links,strictOpenSpec; reviewstaged,
commit/push authorized. Final notify once Russian; delete automation when work ends.
