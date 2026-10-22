# Evidence: episode-lifecycle / callback trace deployment and runtime probe

Current outcome: one bounded live callback-order pulse passed; operator confirmed
manual control and closed normally; trace-off cleanup and launcher preflight passed.
The wider native-step/outcome/runtime acceptance remains unfinished.

- Date/time and timezone: 2026-10-17 23:18 Europe/Amsterdam (21:18 UTC).
- Git revision and dirty status: 796423b, unrelated untracked errors.txt preserved.
- Scope: reviewed trace-on 0.4.1-dev deployment while the game is closed; then one
  bounded callback-order probe. This report is partial; runtime acceptance is open.
- Versions: prior installed observer 0.4.0; installed diagnostic observer 0.4.1-dev;
  repository 0.4.1-dev remains trace-off. No new game instance has been launched.
- Python/package configuration: unchanged accepted full Check.ps1 baseline,
  Python 3.12.14, 746 passed/no skips, strict OpenSpec 24/24.
- Planned scenario/budget: one existing action_probe sequence (two-frame left,
  neutral/release), <=120-second action lease, 512 trace attempts/10 seconds.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Manual normal game exit | operator confirmation; Get-Process isaac-ng returned no process | 0 | passed | confirmed before any installed file writes |
| Prior artifacts | Get-FileHash on installed main.lua/metadata.xml | 0 | passed | accepted 0.4.0 hashes below |
| Backup | Copy-Item to a new ignored private directory; Get-FileHash readback | 0 | passed | both prior hashes verified |
| Diagnostic artifact installation | Copy-Item exact reviewed bundle; Get-FileHash readback | 0 | passed | both trace-on hashes verified |
| No cached approval | Test-Path action_authorization.json | 0 | passed | absent before and after deployment |
| Launch/loading/epoch | manual launch then bounded read-only attach | - | not_run | waiting for manual launch/file-2 confirmation |
| Callback-order pulse | existing action_probe --sequences 1 | - | not_run | requires fresh current-instance/slot/safe-room checks |
| Post-probe release and log analysis | bounded current-session trace/Action records | - | not_run | no runtime probe yet |
| Trace-off cleanup | closed-game default-off installation and later observation | - | not_run | occurs after the probe |

Artifact SHA-256:
- Backup 0.4.0 main.lua:
  d4d40604138fa3826970900c65033d2784c4ff61a25baeb7e42d5cf803440f4d.
- Backup 0.4.0 metadata.xml:
  3a7749dffab0ddb43f496cd1688baa1c55eec5521f2ecd15a0e1e212858d9961.
- Installed trace-on main.lua:
  4161ccd18ba0449d7eb6dc296e3a22dcdc4eff79a32691e1b76fd96868df068e.
- Installed diagnostic metadata.xml:
  a066751aa5bc96dba8be581ad712d61e47e63fa8fdd3c331c2524036fca12131.

Private backup and deployment manifest are under ignored reports/local; no logs,
approvals, game saves or backups are committed. Only the two reviewed mod artifacts
were replaced. No game was stopped or launched by the agent; no Steam options,
Cloud, save or reset/action budgets changed. No private action approval exists.

## Real game

Not run after deployment. The operator confirmed the previous game was closed;
process absence was checked before backup and immediately before each copy.
File 2/current epoch/instance and a centered safe-room character remain to be
confirmed after manual launch. Standing ordinary-profile bounded-action permission
is unchanged and is not training isolation. Trace starts only after an authorized
action, so deployment alone cannot arm inputs or emit the action trace.

## RL evaluation

Not applicable. No training, forced reset, automatic restart or repeated episode
was started. Real native step/event acceptance remains unfinished.

## Limitations and continuation

Self-review: reviewed bundle and backup hashes match, no cached approval, game
closed during writes, default source stays trace-off, private files excluded.
Launch manually with temporary --luadebug from the game directory; select file 2
and Continue manually. Start-Isaac.cmd intentionally refuses the trace-on/source
hash mismatch. Next: read-only attach and fresh operator readiness, then one pulse.
Do not count installation or offline tests as callback-order/game acceptance.


## Live probe and cleanup update (2026-10-17 23:20-23:24 CEST)

The operator manually launched with temporary --luadebug, confirmed file 2,
centered the character in a safe room and released controls. New process PID
12376, start 23:20:10 CEST. Live handshake reported observer 0.4.1-dev, Lua 5.3,
no extender; game build fields were unavailable (installation previously audited
as Repentance+ J460). Slot confirmation is manual, not automatic attestation.

| Check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Initial read-only state | ObservationClient, 3 snapshots, no approval | 0 | passed | epoch 1, room 2, frames 396821/396827/396833; no safe_actions_v1 advertised |
| Current-instance approval | private validated ActionApproval, PID/epoch/slot bound | 0 | passed | <=600 s expiry, ordinary-profile exception, <=2048 bytes; no save writes |
| One bounded pulse | action_probe --sequences 1 --confirmed-save-slot 2 | 0 | passed | one left pulse, then neutral/release; no launch/reset/retry |
| Private approval cleanup | finally: Remove-Item exact approval path | 0 | passed | absent after probe |
| Callback trace extraction | bounded tail, current-session trace/Action lines only | 0 | passed | 115 contiguous records, 417 ms; no trace budget truncation |
| Disconnect | trace record 115, Peer disconnected | 0 | passed | frame 397282, sequence 3 |
| Post-disconnect observation | 8 default read-only snapshots | 0 | passed | frames 399146..399188 in six-frame increments, all positions identical |
| Manual control and exit | operator confirmation | - | passed | controls work; game closed normally |
| Default-off cleanup | process absence; copy reviewed source; SHA-256 readback | 0 | passed | installed 0.4.1-dev now matches trace-off repository source |
| Launcher gate | python -m isaac_threrisaifuture.launcher --preflight-only | 0 | passed | no process launched; matching artifact hashes |

Pulse session 9cf31f75f99d401e9ea5d88cfa387c7f, epoch 1, room 2. Before state:
frame 397269/update 1398, position (312.89105224609,280), red health 8/8.
Action accepted at frame 397270/update 1399, two-frame left, no shooting.
After frame 397282/update 1411: position (300.45498657227,280), health unchanged.
Later eight snapshots were stationary at (299.6484375,280), same epoch/room.
Position changes establish actual bounded movement; they do not establish which
individual input queries were consumed or exactly how many simulation updates
applied left input. Inertia/latency is not classified as held-input failure.

### Observed callback ordering (one instance, one pulse)

| Trace IDs | Observation | Frame/update |
|---|---|---|
| 1, 2 | action_accepted, render_exit | 397270 / 1399 |
| 3-14 | first input-query group: movement/shot GET_ACTION_VALUE and shot IS_ACTION_PRESSED | 397270 / 1399 |
| 17-28 | input-query group before the next logged post-update | 397271 / 1399 |
| 29, 30 | update_enter, update_exit | 397271 / 1400 |
| 33-44 | repeated input-query group after that logged post-update | 397271 / 1400 |
| 47 | hold release, reason expiry | 397272 / 1400 |
| 48, 49 | next update_enter/exit, after release | 397272 / 1401 |
| 77 | explicit neutral action accepted, one frame | 397276 / 1405 |
| 79 | neutral hold expiry | 397277 / 1405 |
| 115 | disconnect closes trace | 397282 / 1411 |

36 input records formed three query groups across only two engine frame IDs;
GET_ACTION_VALUE had eight cardinal queries per group, IS_ACTION_PRESSED four
shoot queries per group. Left returned 1.0; other movement/shot values were zero
and shot pressed flags false. No IS_ACTION_TRIGGERED record was observed. Input
calls occurred both before and after a post-update with the same frame ID.
Only one update_enter occurred between acceptance and release in this sample;
that is a callback fact, not proof of one engine-consumed action update.

Twelve post-update entries were 32-34 ms apart (median 33 ms). This supports about
30 updates/s for this short observed interval, not a universal rate guarantee.
Multiple renders/input queries occur per game update. Counting raw input calls,
render calls or unique frame IDs as applied simulation updates is not justified.
The current trace cannot distinguish engine-consumed queries from other queries.

Raw trace and JSONL snapshots remain private/ignored. Extract SHA-256:
7220dae96ae34ef7f8c9403220550bff2423f7963decdc3a0da389412bf9b806.
No raw logs, approvals, saves or backups are committed. Public tables are reviewed
summaries, not a wholesale log upload. A new action sequence was not repeated.

### Current installed state and remaining acceptance

Game closed by operator; no approval file; installed main.lua hash
669918a74910fdbd7c34cb0caf8b3649e29c5836510b688e6d885ff83cb21634;
metadata hash a066751aa5bc96dba8be581ad712d61e47e63fa8fdd3c331c2524036fca12131.
Config.callback_trace is false. Preflight passes. A fresh real default-off read
after this last copy was not_run; it would require another manual launch, and
hash/preflight is not claimed as that runtime check.

This passes the narrow normal-play callback-order subcheck only. Pause, death,
revival, transitions, native StepCommand completion and oracle event emission
remain not_run. Tasks 3.6/3.8/4.1/4.2/4.3/5 stay unfinished; no archival. Failure-
release acceptance from item 03 remains historical; no Python-kill/stall test was
repeated here. Training isolation, general reset authority and 100 real episodes
remain blocked. No restart budget or action lease was extended.

Self-review: fresh instance/slot check, private approval, one bounded action,
trace/context continuity, unchanged health/room, disconnect/stationary observation,
operator responsiveness, normal exit and hash/preflight cleanup all documented.
Next: executor reviews these observed timing constraints and recommends the next
safe Lua implementation/probe slice without equating hook exposure to application.
