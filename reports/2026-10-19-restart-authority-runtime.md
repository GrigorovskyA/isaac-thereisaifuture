# Evidence: restart lifecycle diagnostic capture v1

- Date/time and timezone: 2026-10-19, Europe/Amsterdam.
- Revision: bd51d93; unrelated errors.txt preserved.
- Scope: runtime acceptance of restart-authority-diagnostics; no behavior fix.
- Observer: reviewed 0.5.0-dev with deliberate local lifecycle flag enabled only.
- Python/configuration: existing locked environment; random mode, no model.
- Scenario/budget: docs/EXPERIMENT_RESTART_DIAGNOSTICS_V1.md; seed 27,
  2048 decisions/three minutes, one-minute handoffs, max one natural restart.

## Results

| Check | Scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Operator normal exit | User confirmed full exit after process detected | N/A | passed | No tooling stopped the game |
| Closed-game deployment/preflight | Private backup, deliberate flag-only variant and hash readback | 0 | passed | Two process-absence guards, exact staged-variant preflight and installed-byte equality |
| Native restart/callback evidence | Actual natural-death restart within budget | 0 | passed | Third invocation: one death, one dispatch, retained approval and live reconnect; incomplete attempts retained below |
| Cleanup and restoration | Release/disconnect, operator control, closed-game default-off restoration | 0 | passed | Operator confirms no intervention and working control; repository preflight passed after normal exit |

## Real game

No launch, connection or actions in preparation. Application launch and file
selection remain manual. No save/settings/Steam Cloud change, forced death,
unattended supervisor or approval renewal on reconnect is authorized.

## RL evaluation

Not applicable. No training, model loading, checkpoint change or quality claim.

## Limitations and continuation

Real engine cause remains unknown; offline callback candidates are hypotheses.
Record actual preparation and runtime outcomes below without overwriting failed
attempts. Keep raw logs, approval, backups and any game seeds private.

## Closed-game preparation

Operator confirmed full normal exit. Process absence was checked before staging
and again immediately before installed-file replacement. Private installed Lua,
metadata and prior approval backups are in
reports/local/restart-diagnostics-20261019-055034/backup. No saves were accessed.

Source main.lua SHA-256:
ab68bc29955d89562fe98c1c19fc346c97c4f1df72853a631a365f8a46d794eb.
Installed diagnostic SHA-256:
d4c08d541c610d74674221562653e5318c876ae4ac3513ecdab8fc6bbb2796cf.
Installed bytes equal source with exactly the single lifecycle flag changed to
true. Metadata remains identical. launcher.preflight passed against the private
staged flag-only variant; this is deliberately not a repository-source hash match.

One local ten-minute approval was deliberately prepared while closed via
approve-training --confirmed-save-slot 2 --hours 0.16666666666666667 --max-restarts 1
(exit 0). Expiry is 2026-10-19T06:00:35Z (08:00:35 CEST). Its training-profile
capability is used only to negotiate the random diagnostic live loop; no model
training is planned. No reconnect renewal or second restart is permitted.
Manual launch/file-2 paused readiness is pending. No connection or actions yet.

## First runtime attempt: room cleared, no natural restart

The preparation notes above are historical. Operator manually launched Isaac,
confirmed file 2, enemies, pause and released keys. One fresh process (PID 36456)
was checked, approval had 532 seconds remaining with max_restarts=1. Native log
contained the installed diagnostic records. No approval was renewed.

Actual command (exit 0 for bounded stop, not proof of restart acceptance):

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode random --confirmed-save-slot 2 --steps 2048 --minutes 3 --combat-gate --gate-wait-minutes 1 --max-faults 0 --seed 27 --connection-timeout 20
```

Window: 2026-10-19 07:51:55–07:53:58 CEST. Observer 0.5.0-dev, Lua 5.3,
extender absent; game build fields unavailable in hello. Session
5125000874804a3db8e6531e334a0c64, epoch 1, room visit 0. Hello advertised
live_loop_v1. Diagnostic hello recorded auth=ok, live_req=1, live_adv=1;
restart_arm recorded limit=1 and attempts=0.

One bounded acknowledgment helper pinned the exact paused request/session/epoch/
room and waited at most 35 seconds for combat after operator unpause. It wrote
one acknowledgment; no further readiness was granted. Initial readiness was
accepted at 07:52:49.011 and combat resumed at 07:52:49.073, after 53.235 seconds
of neutral wait.

The native observer recorded 82 accepted movement/shooting actions, 20 tears and
82 releases. Combat ended at 07:52:57.998 on empty observations before the clear
flag; the gate released and entered handoff 2. The game reported cleared at
07:52:58.288. No additional actions or acknowledgment followed. No death,
dispatch or epoch change occurred, so the intended restart path was not exercised.
This is random behavior in one room, not learned gameplay or model improvement.

The second handoff expired at 07:53:58.013. Summary: two handoffs, one accepted
readiness, 113.235 seconds total wait, 2224 wait snapshots, zero observation gaps,
82 combat decisions, zero fault events. Shell exit 0 means orderly bounded stop.
Python disconnected. Operator explicitly confirmed working manual movement and
shooting, no intervention during the automatic part, then normal full exit.

## Actual diagnostic and restoration evidence

Private session directory: runs/live/sessions/20261019-075155-dbe3ac, including
live.jsonl, oracle.jsonl, game-log-after-stop.txt, game-log-after-exit.txt,
capture-summary.json and restoration.json. Raw native logs remain private.

The final native log contains 63 ordered lifecycle records. Normal operator exit
produced exit_enter (id 59, corr=uncorrelated, live=0, approval=1), then the actual
restart invalidation and approval_drop (id 61), followed by exit_exit (id 63,
active=0, approval=0, auth=none). This verifies real normal-exit diagnostic facts;
it does not establish the callback sequence of the prior restart failure.

After two closed-game guards, restored main.lua and metadata.xml from the reviewed
repository source. The temporary approval from this exact capture was verified
by expiry/restart limit and removed; no historical approval was restored. Normal
launcher.preflight passed against repository source (exit 0), installed Lua hash
ab68bc29955d89562fe98c1c19fc346c97c4f1df72853a631a365f8a46d794eb,
lifecycle_diagnostics=false, approval absent. No game was stopped by tooling.

Primary self-review: tasks 3.1 and 3.3 pass. Task 3.2 remains blocked because no
natural death occurred inside the agreed budget. Do not archive this change or
label the restart root cause resolved. No automatic repeat, training, model read,
checkpoint update, save edit or limit change occurred. A further capture needs
a separate finite attempt and fresh room readiness; never force the failure.

## Second attempt preparation (operator requested)

Operator explicitly requested another ordinary enemy room to exercise the
death/restart case. No process was running. Exact default-off source preflight
passed, installed files backed up privately in
reports/local/restart-diagnostics-second-20261019-075623/backup, and process
absence checked again before deployment. Same flag-only variant/hash as above;
staged preflight and byte readback passed (exit 0).

New requested invocation: seed 28, random, 2048 decisions/three minutes,
one-minute handoffs, zero faults, max_restarts=1. One deliberate ten-minute
approval expires Unix 1792389984; no renewal within the invocation. No kill
command, scripted damage, health edit or forced reset. No launch/connection or
actions yet. Awaiting manual file-2 paused enemy-room readiness. Diagnostic flag
is temporarily ON again; restore default-off and remove this temporary approval
after normal exit, regardless of whether a death occurs. First attempt evidence
and its successful cleanup remain unchanged.

## Second invocation: paused readiness timeout

Private session runs/live/sessions/20261019-075739-5e7d98. One game process,
PID 36300, with 530 approval seconds remaining/max_restarts=1. Live hello
succeeded; epoch 1, room visit 1, session 7752c2e55a174bfa8fdf1b67a7e60dc8.
The 35-second provenance-bound helper expired while observations remained paused.
The one-minute handoff then stopped the invocation: 60.015 seconds, 1182 wait
snapshots, zero acknowledgments/actions/reward/episodes/faults. Process exit 0;
this was no test of the death path. No authorization renewal, game input or
automatic retry occurred.

The operator explicitly requested a repeat with two-minute handoffs after this
stop. The fresh three-minute invocation retained seed 28, 2048 decisions, zero
fault tolerance and the SAME loaded approval/max_restarts=1; no file renewal,
game restart, mod replacement or deadline extension within either invocation.

## Third invocation: actual natural death and reconnect

Private session runs/live/sessions/20261019-075909-63c15b. Command differs from
the seed-28 second invocation only by --gate-wait-minutes 2. Initial native
session 0a66adc66f314c24b2e2274620b23407, epoch 1, room visit 1. Pinned one-shot
readiness accepted after operator unpause; 28.828 seconds of neutral wait.

At 07:59:39.405 CEST combat resumed. At 07:59:44.524 it terminated on death after
46 decisions/153 updates. Native records show 46 accepted actions, 12 tears and
46 releases. Approximate management labels: three half-hearts lost, 8.5 enemy HP
removed, eight initial enemies and one kill estimate. This is random diagnostic
behavior, not a trained policy. No second combat readiness was granted.

Actual native lifecycle (monotonic milliseconds, diagnostic record IDs):

| Record | Time | Facts |
|---|---|---|
| 62 game_end_enter | 60795718 | game_over=1, epoch=1, live=1, approval=1 |
| 63 game_end_exit | 60795718 | pending=1 |
| 64 dispatch_before | 60797235 | restart_id=1, attempts=1, limit=1, awaiting=1 |
| 65 dispatch_after | 60797235 | ok=1, still awaiting; command returns BEFORE engine exit |
| 66 exit_enter | 60797250 | corr=awaiting, live=1, approval=1 |
| 67 approval_preserve | 60797250 | existing preserve branch taken |
| 68 close / 69 exit_exit | 60797250 | live/session clear; approval retained |
| 70 start_enter | 60797346 | continued=0, corr=awaiting |
| 71 start_exit | 60797346 | epoch=2, approval=1, auth=ok, awaiting absent |
| 72 hello | 60798300 | live_req=1, live_adv=1, auth=ok |
| 73 restart_arm | 60798300 | attempts=1, limit=1, rs_armed=0; original budget exhausted |

Reconnected session 524174434a83444bafb516008c5382b7, epoch 2, room visit 0,
observed at 07:59:48.996. Unlike the synchronous test stub, dispatch_after precedes
exit/start in this actual engine sequence. No behavior fix is inferred. One
dispatch and retained approval/reconnect are verified; the earlier unexplained
second new start has not been reproduced. Continue neutral observation only
until the original current-invocation deadline/handoff cap, then verify cleanup.

### Final stop and cleanup

The capture stopped at 08:01:44.571 CEST on its original two-minute second-handoff
cap, before the three-minute global deadline. Exit 0, zero logged faults. Total
148.844 seconds neutral wait, 2908 wait snapshots, two handoffs/one accepted
readiness, 46 combat decisions. One observation gap corresponds to restart and
reconnect; it did not authorize new action. No second start or extra action
occurred during the remaining approximately two-minute observation window.
Native log has two start_enter records in total: initial manual Continue and
the single dispatched restart, not two automatic starts.

Operator explicitly confirmed working manual movement/shooting, no intervention
or menu input during the automatic phase, then full normal exit. Captured final
native log and parsed lifecycle facts privately in this session directory.
Two process-absence guards preceded default-off restoration from reviewed source.
Verified the temporary approval's exact expiry/restart limit, removed it, and
normal launcher.preflight passed against repository source. Installed hash equals
ab68bc29955d89562fe98c1c19fc346c97c4f1df72853a631a365f8a46d794eb.

### Acceptance and limits

Primary self-review: diagnostic runtime requirements now pass (tasks 3.1-3.3),
including actual asynchronous dispatch, lifecycle correlation, retained approval,
finite attempt counter, neutral wait/reconnect and operator-confirmed cleanup.
No production behavior, dependencies, reward or model changed. The previously
failed/blocked attempts remain part of this evidence. Strict OpenSpec validation
is rerun for the updated record; prior Windows source gate remains 1401 tests.

The 2026-10-18 extra-start failure remains unexplained and was NOT reproduced.
This successful trace must not be presented as its repair or as stable multi-run
training evidence. No approval renewal, additional dispatch, scripted damage,
forced reset, learning or checkpoint update occurred. Keep the change unarchived
pending final archive review; no further live run or training starts automatically.
