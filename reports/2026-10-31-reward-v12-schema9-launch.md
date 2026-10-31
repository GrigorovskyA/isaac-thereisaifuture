# Reward v12/schema9 launch receipt

October31,2026. [Finite plan](2026-10-31-reward-v12-schema9-native-plan.md);
[offline verification](2026-10-31-reward-v12-offline-verification.md).

- Requested commits5627159 (menu start) and4c58937 (reward12) pushed originmain.
- Authoritative Check.ps1 exit0:1569 tests including isolated Lua,no skips;
  lint/format/mypy/pip clean,existing synthetic AllNaN warning;strictOpenSpec30/30.
- Stopped runs/pure-v4 moved to runs/pure-v4-reward-v11-schema9 only after all77files
  were hashed. After-move hashes matched exactly, including finalt253952 model,
  normalizer,noveltycounts andmanifest. Older lineages remain preserved.
- Deployed main.lua b647b712a4dc92d7fee21ce9031d0e2ef24c058f61292d56ba2e41b9969d8c50
  andmetadata00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997
  match prior receipt; no redeployment. No save/Cloud/launch-option change.
- Only the identified dashboard processes38164/15600 were closed as requested.
- Start-Pure.cmd --initialize launched ONCE at06:31:15.330771UTC /07:31:15CET.
  Source4c5893762692b06279747c71b58685fffa97a9db frozen; exactcontract
  1a6d8146f5e89b7bdad14fe21d3afa9cc1f5c4192b8e5f24cefb6bbab0e0c8d8.
  Initial owner30588(wrapper25724),launcher20788,worker26124(wrapper40076),Isaac34956.
- Native menu.jsonl records menu_entry_resolved with slot2/mode new-run, then
  menu_new_run_verified (8 bounded keys). This is initial entry, not rolloverresume.
- First two completed episodes stalled: col_stall=-4 in2/2 and col_stagnation=-7.02
  in2/2; seconds-in-room30.2/30.1 are descriptive. The passive backend idle-clock
  measurement and checkpoint counts/statistics will be evaluated at18minutes.
  Current state training,fault=null,no audit error file. No performance acceptance.
- Full audit due06:49:15UTC /07:49:15CET. First8hrollover expected around14:30UTC;
  separately inspect death-before-transition and actual resumed New Run when
  positive no-game evidence occurs. Never force the precondition.
- Stop at first saved>=300000 or absolute November1 12:31:15.330771UTC /13:31CET,
  whicheverfirst. Any sessionfault/required audit failure stops; no manualretry.
- Report monitoring every15minutes reads files/processes without opening windows;
  healthy/pending progress stays quiet. Reports at50k/150k/300k compare against v11
  only at equal available bounds (v11 final254782observedsteps,1180episodes).

Evidence: reports/local/reward-v12-schema9-20261031 (launch.json,preflight.json,
archive-before/after.json,check-full.log,training.log,audit/); supervisor session
plan/menu/events/status/result are runtime authority. Prepared finite owner and
passive audit are frozen. Native tasks remain open; no OpenSpec change archived.
Final cleanup is not_run while training is active. This is self-review.
