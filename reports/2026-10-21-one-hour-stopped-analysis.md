# User-stopped hour attempt: training and stagnation diagnosis

Date:2026-10-21,Europe/Amsterdam. Outcome: stopped at the user's request;
no hour-completion or improved-play claim. No further training/New Run is active.
Latest retained model:7d53f55f-s20-t21760; initial parent t7680 is unchanged.

## Main finding

The user's corner-stagnation observation is supported by captured native positions
and accepted commands. The continuation repeatedly trained in the same room with
the same two recorded enemy identities,without any registered damage/clear events.
This is insufficient evidence that more time in the same state would improve play.
Do not accept changed weights/checkpoint counts or survival as combat progress.

| Captured continuation metric | Result |
|---|---|
| Native accepted action records | 11446 (includes possible management input; combat decisions11445) |
| Session/epoch/visit | 6b89a31c342e40019e0103d9ae039924 /1 /0 throughout |
| Native pre-action position extent | x69.782..560,y251.554..410.495 |
| Dominant position cluster | (70,410),radius5 |
| Samples in that cluster | 8008/11446 =69.96% |
| First5min / next5min / next5min / final full5min occupancy | 42.66% /60.92% /85.43% /88.17% |
| Final partial33s occupancy | 92.48%,306 accepted commands |
| Comparable adjacent motion pairs | 11420,identity/visit stable and1..15 game-frame gap |
| Requested movement pairs | 9190 |
| Requested movement with next observed displacement<0.5 | 5909/9190 =64.30% |
| Movement counts | down4242,left3971,none2233,right480,up520 |
| Shooting counts | up4055,left2647,none2590,down1104,right1050 |

Among non-idle movement commands,89.15% point left/down. Shooting is also not
uniformly random by observed counts,but target-relative correctness cannot be
computed without enemy positions. The dense point is consistent with the user's
observed corner; room bounds/blocker maps were not captured,so a specific collision
or corner geometry cause is not proven. Motion uses pre-action accepted poses and
the next recorded pose,not exact isolated action displacement; inertia/timing are
possible influences. Very short displacement is not an engine collision label.

## What the episode and oracle records establish

The21min continuation contains20 closed unknown episodes plus a partial final
segment. All20 death fields are null,not verified survived outcomes. The live
scenario has a software1800-update boundary (about60 game seconds); code converts
that boundary to unknown when terminal coverage is incomplete. These are not20
independent fights or rooms. Gate observations confirm visit0; oracle spawn records
are42 events for just2 unique session/epoch/visit/entity/generation identities.
Repeated reset baselines must not be counted as42 new opponents.

The continuation's oracle log contains only enemy_spawned records: no registered
enemy_damaged,player_damaged,player_died or room_cleared events. Closed episode
returns total-12.008; combat-gate return including partial segment is-12.2703.
These are partial conservative derived labels,not complete raw HP histories.
Absence of events is not proof of physically zero damage,especially for hidden
phase/healing/coverage effects. Spawn amounts are maximum HP,not current HP.
No verified clear rate or improvement claim is available from these unknown outcomes.

For context,the first421s attempt recorded84HP conservative derived enemy damage,
30 half-hearts lost,five death events,one observed clear transition,and five unknown
outcomes alongside five deaths. Different game states and budgets make these phases
unmatched; their difference is not a causal ranking of checkpoints.

## Interpretation and competing explanations

The reward code/config assigns-0.01 per active combat second,-25 per death and
-8 per half-heart damage. A minute without progress costs about-0.6,far less than
one death. Safe inactivity is therefore a plausible local objective under this
reward/encounter distribution. That arithmetic explains an incentive,not proof
that reward caused the corner policy. Dense correlated samples from one protected
position can dominate subsequent updates without supplying successful combat data.

There is no implemented progress criterion that rejects a long combat-active
collection merely because displacement/damage/clear progress is absent. The
supervisor honestly reports active combat collection,but this does not establish
useful learning. Software episode resets then supply more of the same encounter.

The previous large-room absolute-position clipping issue is not demonstrated by
this capture: all11446 native absolute positions are within the current1000-unit
encoder scale. Enemy coordinates/slot ordering,actual normalized policy inputs,
projectile range/line-of-sight,enemy phases and blocker masks were NOT recorded.
Those hypotheses cannot be ruled out or diagnosed from these logs. Do not silently
change the observation schema or add a scripted approach controller to this lineage.

## Frozen model replay (limited diagnostic)

Primary prepared a frozen deterministic replay of the SAME657 historical policy
vectors through t7680,t10496 and t21760. The historical vectors come from an older
mixed-control large-room capture,not this run. Each model uses its own saved frozen
normalizer/recurrent state,reset at the same window/context boundaries. No oracle
labels enter inference; no learning,environment steps or artifacts were written.

| Checkpoint | Actions differing from t7680 | Historical deterministic shooting modes |
|---|---|---|
| t7680 |0/657|right43,up335,left130,none149|
| t10496 |500/657|right132,down87,up59,none277,left102|
| t21760 |630/657|right657|

This confirms policy changes and a strong directional mode on that historical
input set. It does not prove live collapse on this run,correct target bearing,
or that any model plays better. This dataset is not a held-out matched gameplay
suite and cannot choose a winning model. Actual training samples actions; replay
uses deterministic modes. Keep t21760 as a candidate,not a selected improvement.

## Training, source remedy and cleanup

Base HEAD8051db578b4598c280062f5ee54934415b680c75. Initial hour driver/new-file2
approval matched the finite plan. Native positive absence preceded [New,2]; initial
bridge session993ebc72272e4c45a58998fea51e8f39,epochs1..6,five death restarts.
First attempt faulted421.547s into the original3600s window on Windows WinError5
replacing status.tmp with status.json. Cleanup was clean;the first attempt remains
failed. It saved2816 steps to t10496 and discarded112 unfinished rollout decisions.

Primary implemented a bounded1s/10ms atomic-JSON replacement retry only for Windows
errors5/32/33. Other/persistent failures still propagate. A concurrent reader
sharing race is plausible,not proven without a handle trace. No policy/reward/
config/deployment change. Native game was closed before source edits.

Offline status-sharing checks via one fresh gpt-6-luna/high worker:
`.venv/Scripts/python.exe reports/local/run_status_sharing_checks_1.py`.
Expected HEAD8051db5;411 frozen files. Start-before1792572785.8306262,
absolute stop-by1792573025.8306262,240s/512MiB,zero native actions/retries.
Exact environment/commands are in private status-sharing-checks-plan-1.json:
existing Lua test-runtime PYTHONPATH,installed resources/scripts/json.lua,
owned TEMP/TMP. No installs/Git/source fixes by worker.

| Sequential check | Exit | Result |
|---|---|---|
| python -m ruff check src tests scripts/smoke_rl.py |0|passed|
| python -m mypy |0|55 source files,no issues|
| python -m pytest tests/test_menu_entry.py tests/test_session_runner.py -q |0|98 passed,zero failed/skipped|
| pwsh.exe -NoProfile -File D:/isaac/scripts/Check.ps1 |0|2198 passed,zero failed/skipped;OpenSpec47/47;pip/format passed|

Actual Windows held-reader regression ran (not skipped). Runtime56.8s,
peak94728978 bytes. Primary independently rehashed411 files unchanged and read
actual logs/exits. Logs:reports/local/status-sharing-checks-1/.

One newly recorded corrective Continue-only command used t10496 and the remaining
ORIGINAL hour deadline1792575619.0. No new New Run or hour extension. Source/config/
parent hashes frozen again;retry remedy had passed the full gate before launch.
The user then requested stop for analysis. stop.request yielded user_cancelled,
exit0,1260.703s (21min),11264 saved steps,181 unsaved. Native Continue/file2 and
activeIsaac verified;no infrastructure fault or further death/restart event recorded.

Totals across both attempts:14373 combat decisions,14080 new saved steps,293
unsaved decisions;55 immutable completed checkpoints,strict parent chain back to
t7680. Active combat collection1516.279s (~25min16s),not a completed hour. SB3
num_timesteps7680->10496->21760;_n_updates120->164->340. These show updates only.

Primary strict manifest/artifact/config/reward/seed readback verified t21760 and
all55 parents. Both native61-file freezes matched before subsequent source edits;
no game/listener9528 or owned action_authorization.json/.tmp remained. Supervisor
cleanup_errors empty,normal game close and cooperative release. Sleep release
reported successful;independent powercfg readback required elevation and was not
counted as verification. Peak sampled run/output593987248 bytes under4GiB.
Original/migrated t6912,t7424,t7680 and all later history preserved. No forcekill,
save edits,Cloud/Steam-option changes or third-party mods.

## Analysis execution and OpenSpec verification

One fresh gpt-6-luna/high offline worker executed exact command
`.venv/Scripts/python.exe reports/local/native-hour-analysis-20261021/analyze.py`.
Start-before1792574518.045187,stop-by1792574698.045187,180s/256MiB,
zero native actions/retries/model writes. OMP_NUM_THREADS=1/MKL_NUM_THREADS=1 for
analysis only.71 frozen input/source/checkpoint files;primary independently
verified all71 hashes unchanged and read analysis.json. Exit0,5.132s wall,
3.159s script time. The copied native log is5.36MiB and is private,as are all
raw oracle/policy traces and models. Optional plot command failed before output
because matplotlib was absent;no dependency installation or plot success claimed.
Tables above use the completed numeric analysis.

OpenSpec status-sharing-retry self-review (primary,not independent review):
completeness2/2;correctness1/1 added requirement,two scenarios mapped to atomic_json
and transient/persistent/unrelated/actual-Windows tests;coherence follows bounded
replacement design. Corrective21min native status/readback/update/user-stop cleanup
passed with no repeat fault. The original fault's exact external cause and actual
native retry count were not instrumented;these remain unknown. Full one-hour timer
acceptance and matched learning evaluation were NOT run to completion. Keep change
unarchived;do not promote offline tests or checkpoint changes to better-play proof.

## Next work before more training

1. Keep all candidate checkpoints;do not declare t21760 the best or overwrite it.
2. Specify a bounded progress diagnostic that couples policy vectors/actions with
   raw enemy positions/HP/phases and same-frame native poses. Separate immobility,
   blocked path,aim/range/LOS and missing-input hypotheses. Existing data lacks
   those channels;another blind hour does not answer them.
3. Add an explicit no-progress signal for combat collection and prevent many
   software timeout segments in one unchanged encounter from looking like diverse
   combat experience. Design/test criteria before live changes.
4. Compare candidates on predeclared comparable encounters and several seeds,
   including all failures,damage taken/dealt and verified clears. Only then test
   versioned reward/curriculum changes;do not pick arbitrary new weights or force
   a hand-written approach behavior into the current learner.

No new live diagnostic,training,resets or model selection is authorized by this
report. Current user instruction is stop and analyze.
