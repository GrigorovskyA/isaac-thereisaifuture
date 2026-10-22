# Evidence: combat-experience-gate runtime preparation

- Date: 2026-10-18, Europe/Amsterdam.
- Baseline: 308d766; unrelated errors.txt preserved.
- Scope: first bounded real combat-gate integration check, random mode only.
- Budgets: at most 512 decisions / six minutes; each operator handoff at most
  three minutes; one natural-death restart in the original approval/game launch.
- Training/checkpoint changes: none planned or authorized by this check.

## Preparation

The operator confirmed the game closed and asked which room to use. Closed-game
process guard and launcher --preflight-only passed (exit 0), including installed
observer/source hash agreement. A private 15-minute approval with max_restarts=1
was prepared. No game launch, connection, action or training started here.

## Planned scenario

1. Operator manually starts file 2 in an empty safe room; primary attaches and
   verifies waiting_for_operator, zero action commands and no automatic takeover.
2. Only after the wait is verified, operator manually enters an ordinary enemy
   room, releases keys and explicitly confirms readiness. Primary submits the
   current request acknowledgment; verify combat resumes on matching provenance.
3. After clear/empty/death/timeout, verify release and another handoff. Additional
   manual navigation only during the explicit waiting state; no automatic ack.
4. Stop at existing caps, inspect summary/release, confirm manual control.

## Results and limitations

Runtime not_run, pending manual launch and current file-2/room confirmation.
No forced reset, death, enemy spawning, saves/Cloud/settings change or mod update.
Random-policy behavior does not establish learning. Existing offline synthetic
rollout/normalization evidence does not become real training evidence here.

## First real attempt: waiting and timeout passed; combat not exercised

- Window: 2026-10-18 18:57:30–19:00:30 CEST.
- Revision: 1a3dcbd; exactly one game; approval had 857 seconds remaining,
  max_restarts=1. No renewal.
- Command (exit 0):

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode random --confirmed-save-slot 2 --steps 512 --minutes 6 --combat-gate --gate-wait-minutes 3 --max-faults 0 --seed 21 --connection-timeout 20
```

Actual observer 0.5.0-dev, Lua 5.3, no extender. Initial session
7f6ebbb768884495ac63c9715779a08c, epoch 1, room visit 1. The operator confirmed
an empty room. Request state waiting_for_operator, eligibility cleared, native
accepted actions zero. After manual navigation the bridge observed combat in
room visit 3 but did not take control without an acknowledgment.

The operator confirmed readiness, but primary handling was delayed by an
already-pending 30-second output poll. Before readiness was written the player
died; the permitted natural-death restart changed epoch to 2. The pre-ack check
detected a cleared new room and REFUSED to write acknowledgment for the prior
combat state. No action command had been sent by Python. The operator was then
asked to prepare a paused fight to avoid taking damage while messaging.

Further manual movement was observed, with combat/dead/paused states in epoch 2,
session 9499a0546b12407ca49b4b078451e0fc. No second readiness confirmation was
received before the cap. The existing single restart attempt was not refreshed.
No forced reset or additional run was started by tooling.

Final native gate summary: stopped, CombatGateExpired, wait 180.016 seconds,
3485 wait snapshots, one observation gap, accepted=0, rejected=0,
combat_decisions=0, reward=0, withheld_actions=0. Request state stopped; the
process closed normally. Shell exit 0 is budget-stop behavior, NOT full runtime
acceptance or a successful combat encounter. No training/model writes occurred.

Private evidence: runs/live/sessions/20261018-185730-d94fd4 and the actual game
log. No raw logs/approval/model data are committed. Primary self-review: empty
waiting, absence of implicit takeover when enemies appeared, no stale readiness
after restart and bounded no-response stopping are observed. Real readiness
acceptance, combat continuation and post-combat handoff remain not_run; task 5.2
stays unfinished and no archive is allowed.

The next attempt must use a fresh operator-coordinated budget without silently
renewing authority. Prepare the character paused in an enemy room, then arrange
short prompt handling and unpause immediately before acknowledgment. Do not leave
the operator exposed to combat during long blocking output polls. No automatic
second attempt follows this report.

## Second attempt: live negotiation refused, no control

The operator subsequently confirmed a fight prepared on pause. An explicitly
bounded fresh invocation was prepared with seed 22, 256 decisions / three
minutes and a two-minute handoff cap under the ORIGINAL unchanged approval.
Precheck found one process and 440 seconds remaining; max_restarts stayed 1.

Private logs: runs/live/sessions/20261018-190426-19f4dd. The initial handshake
failed before a gate request or any action: Python reported Peer closed before
a complete record (observed shell exit 1), and the fresh actual Lua log recorded
Observer capability/protocol fault, main.lua:650, Too many capabilities.

Source review confirms hello advertises safe_actions/live_loop only when the
in-memory approval is authorized; a normal PRE_GAME_EXIT clears that approval,
and the previously loaded flag prevents silent reloading on another hello. The
observed new run after the second death and capability refusal are consistent
with this lifecycle invalidation; direct inspection of Lua memory is unavailable.
Disk expiry alone therefore does not prove current in-memory action authority.
No retry, authority edit, mod change, launch or action followed the refusal.

The operator was asked to exit Isaac normally so a full manual process restart
can reload the approval. No current run was interrupted by tooling. Runtime
acceptance remains unfinished; the paused room did not yield a valid handshake.

## Operator-directed full-restart preparation

The operator explicitly confirmed Isaac fully closed. Process guard and launcher
preflight passed (exit 0), including source/installed observer hashes. A deliberate
replacement 15-minute approval was prepared, expiring 2026-10-18T21:12:14+02:00,
max_restarts=1. Planned recheck: random mode, at most 256 actions / three minutes,
operator wait cap two minutes, no training. No game launch or control occurred.
Manual launch, file-2 selection and paused-room confirmation are pending. The
operator must remain paused until listener/readiness preparation is complete.

## Third attempt: explicit readiness and bounded combat passed

The operator confirmed file 2 in a fight on pause after the full process restart.
Precheck: exactly one process, original replacement approval had 838 seconds,
max_restarts=1, no renewal. Observer 0.5.0-dev/Lua 5.3/no extender negotiated
live_loop_v1 successfully. Game version/build remained unavailable.

Command (exit 0):

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode random --confirmed-save-slot 2 --steps 256 --minutes 3 --combat-gate --gate-wait-minutes 2 --max-faults 0 --seed 23 --connection-timeout 20
```

Private session: runs/live/sessions/20261018-205816-cc5eb6. Actual game session
20d94d25c176460280867b3a5c1e614d, epoch 1, room visit 0. Initial wait classified
paused; no policy action was enabled. One explicit prepared readiness was bound
to request e4cf47e0b2891c6416cf470e1bc0a7a5 and the exact session/epoch/room.
A separate local one-shot helper waited at most 60 seconds for that SAME paused
room to become combat, cancelling on room/request change or noncombat state.
It submitted exactly one acknowledgment, never retried or renewed anything.

Only after that helper was ready did the primary instruct the operator to
unpause and release keys. This was the explicit operator-coordinated readiness,
not implicit takeover whenever an arbitrary new enemy appeared. Live state
became combat at 20:58:55.196; ready_accepted followed at 20:58:55.270 and
combat_resumed at 20:58:55.313, about 0.117 seconds later. No long output poll
delayed readiness during the exposed fight.

The initial handoff wait lasted 37.985 seconds and consumed 751 snapshots but
zero combat decisions/reward. The run then completed its 256-decision cap at
20:59:33.792. Summary: stopped/closed, one handoff, one accepted ack, zero
rejected acks/gaps/resume races, 256 combat decisions, no completed outcome.
Random-policy reward was -4.1327; no training occurred. No fault record exists.

Actual Lua records independently show 256 accepted actions, 82 tears and 256
expiry releases. Accepted-action coordinates span x=825.9649..1067.5204 and
y=353.3503..677.7827. Final sequence 256 at frame 1269 expired at frame 1272.
The listener was absent after normal close. The operator explicitly confirmed
no manual keys during automatic combat and responsive manual control afterward.

Private oracle labels: ten enemy spawns, three enemy-damage labels (7.5 HP), one
player-damage label (one half-heart) and one disappearance/kill estimate. No
clear or death occurred in this window. These approximate labels are separate
from policy inputs. Checkpoint/model files were neither read nor written.

## Acceptance status after third attempt

Passed real slices: zero-action empty/paused waiting, no implicit takeover,
one accepted matching readiness, actual movement/shooting, cap stopping and
operator-confirmed release. First-attempt no-response timeout evidence remains.
Still not_run: post-clear/empty combat handoff and a fresh readiness after that
handoff, plus gated training sample/update behavior in the actual game. Earlier
synthetic training evidence is not promoted to real acceptance. Task 5.2 remains
unfinished and the change is not archived.

Next scenario should be a small room with 1–3 ordinary enemies, staged paused,
under a separately declared bounded continuation. Do not extend or rerun this
256-step trial retroactively to obtain a favorable outcome. No new run follows
automatically from the successful partial result.

## Fourth attempt: three-enemy room, cap before final clear

The operator prepared the same room with three remaining enemies, paused.
A new explicitly declared trial used random seed 24, at most 512 decisions /
four minutes, two-minute handoff cap. The same original approval had 597 seconds
remaining and was not renewed; exactly one game instance was present.

Command (exit 0):

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode random --confirmed-save-slot 2 --steps 512 --minutes 4 --combat-gate --gate-wait-minutes 2 --max-faults 0 --seed 24 --connection-timeout 20
```

Actual session 912b5b5b97cb4a9ca6562ea0fd71f518, epoch 1, room visit 0.
Private logs: runs/live/sessions/20261018-210218-701d54. The same one-shot,
60-second, exact-provenance readiness preparation was used while paused; no
other request was automatically acknowledged. After the instruction to unpause,
combat was observed at 21:02:58.567, readiness accepted at 21:02:58.676 and
control resumed at 21:02:58.719. Wait: 40.391 seconds, 797 snapshots, zero combat
decisions during waiting. No observation gaps, rejected acks or resume races.

The run reached its 512-decision cap at 21:03:52.137 and closed normally. Actual
Lua records show 512 accepted actions, 129 tears and 512 expiry releases. Oracle
labels include three spawns (4 HP each), four damage estimates totaling 8 HP,
two disappearance/kill estimates and one half-heart of player damage. No clear
or death was observed; the last enemy was not verified defeated within the cap.
There are no logged faults. No training or checkpoint writes occurred.

Final sequence 512 at frame 4016 expired at frame 4019. The operator confirmed
manual control works and no keys were used during automatic combat. Outcome
summary is empty because the cap interrupted the fight; stopped/closed is not
evidence of post-clear handoff. Task 5.2 remains unfinished, no archive. Both
prior successful slices and unfavorable/incomplete attempts are retained.

Further checks need a new explicit small budget/readiness; do not extend this
completed invocation or label its two estimated kills a learned-policy result.

## Fifth attempt: final enemy, timeout handoff, fresh readiness and clear

The operator explicitly requested defeating the last enemy and later explicitly
asked to continue after the first combat timeout. Both combat segments ran in
ONE invocation; no run deadline, action cap or game approval was renewed.

Precheck found one game instance and 381 seconds left in the original approval,
max_restarts=1. Command (exit 0):

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode random --confirmed-save-slot 2 --steps 1024 --minutes 3 --combat-gate --gate-wait-minutes 1 --max-faults 0 --seed 25 --connection-timeout 20
```

Private evidence: runs/live/sessions/20261018-210553-d7c974. Session
eb39405ed72b4f3b90043f3626a956de, epoch 1, room visit 0. The first exact-room
one-shot readiness was prepared while paused; the operator unpaused after the
instruction. Accepted at 21:06:29.756, combat resumed at 21:06:29.800, after
35.516 seconds of neutral waiting. The first segment hit its existing 60-second
episode timeout after 576 steps and about 3.5 HP enemy damage. It released input
and issued a NEW request, 8b7d9f62f8630d47f09056c9c7aadc17. No automatic ack or
implicit continuation occurred.

The operator explicitly asked to continue. A second bounded one-shot readiness
was prepared for that request and the SAME session/epoch/room while paused.
After the next unpause, readiness was accepted at 21:08:14.350 and combat resumed
at 21:08:14.393. This is fresh readiness for a new handoff, not replay of the first.
The original invocation still had its unchanged three-minute absolute deadline.

At 21:08:23.896, after 91 further decisions, the gate classified the room as
empty, truncated conservatively, released input and issued request three,
315407e4c0fac06c5cd71a5912dd3fd0. The clear flag followed at 21:08:24.230.
No clear bonus was fabricated while the flag lagged: the gate outcome remains
empty, rather than a claimed exact engine-clear event. One kill estimate and
four HP total damage are present in the oracle log; no player damage/death.

Two separate native-log readbacks during the final wait both counted exactly
667 accepted actions; there was NO next action after combat ended. Final sequence
670 was accepted at frame 6706 and expired at frame 6709. The request remained
waiting_for_operator in a cleared room, with no third acknowledgment. At
21:08:54.290 the original global deadline stopped the process normally.

Final summary: three handoffs, two accepted fresh acknowledgments, zero rejected
acks/gaps/resume races, 667 combat decisions, 110.407 seconds and 2177 snapshots
of waiting. Actual Lua logs show 170 tears, 667 accepted actions and 667 expiry
releases. No faults were logged. The listener is absent after close. The operator
confirmed the room is cleared, manual control works and there was no manual help
during automatic combat. Random-policy results are NOT learned-policy evidence.

## Final declared acceptance

The primary-owned bounded real-gate criterion now passes: real combat, timeout
handoff, fresh readiness, subsequent enemy defeat, immediate empty-room handoff,
no implicit resumption, no actions while waiting, unchanged deadline and cleanup.
Earlier failed/partial attempts remain visible. Offline Windows review passed
1362 tests with zero skips and pinned strict OpenSpec 28/28; source did not change
during these runtime attempts. This is primary self-review, not independent review.

The narrow gate change can be archived after strict validation. This does NOT
accept a real gated PPO update/checkpoint (only its synthetic test has run),
multi-seed learning, autonomous navigation, exact kill/clear semantics or the
larger combat-training milestone. No forced reset/death, spawned enemies,
screen capture, desktop input injection, save/Cloud changes or new dependency.
No further training or game command is started after this result.

Pinned OpenSpec archive completed with exit 0 as
2026-10-18-combat-experience-gate-v1. The non-blocking delta-count advisory was
retained; validation was not disabled. The generated Purpose placeholder in the
new baseline was replaced before final strict validation.
