# Evidence: first real live-loop random check

- Date/time and timezone: 2026-10-18, 16:18:33–approximately 16:22:10 CEST.
- Git revision: 14fc0a7; unrelated errors.txt preserved.
- Scope: live-training-loop tasks 5.3/5.4; random integration, not learning.
- Runtime: real Repentance+, observer 0.5.0-dev, Lua 5.3, extender absent.
  Handshake game version/build fields are unavailable; do not invent them.
- Python: existing 3.12.14 environment, no dependency/configuration changes.
- Profile: ordinary profile, operator-confirmed file 2, not isolated.
- Budget: seed 18, 2000 steps or six minutes, max_faults=0; existing approval
  expires at 16:32:47 CEST and permits at most three natural-death restarts.

## Results

| Requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Precheck | Exactly one Isaac process; approval has 854 seconds remaining | 0 | passed | No launch, slot selection or approval renewal |
| Live handshake | Command below; actual Lua peer | 0 | passed | 0.5.0-dev and live_loop_v1 negotiated |
| Movement/shooting | 2000 accepted native actions | 0 | passed | Changed coordinates and 517 tear records |
| Action expiry/cleanup | Native release logs; listener absent after exit | 0 | passed | 1997 expiry, one heartbeat, two transition release records |
| Raw HP/oracle path | Real enemy labels, separate oracle log | 0 | passed | Eight spawn labels, seven damage labels, four disappearance/kill estimates |
| Natural death/restart | No death occurred | — | not_run | Task 5.4 remains unfinished |
| Training checkpoint | Random mode only | — | not_run | Task 5.5 remains unfinished |

Command (exit 0):

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode random --confirmed-save-slot 2 --steps 2000 --minutes 6 --max-faults 0 --seed 18 --connection-timeout 20
```

## Real game

Session c35fe2af5b0c4dcdafecc09b69c1cc46, epoch 1. The hello came from the
installed game, not a harness. Accepted actions number 2000, independently counted
from session-filtered Lua records. They include native movement and shooting;
accepted-action positions span x=46.4001..569.9998, y=147.0712..433.8619.
The final action is sequence 2005, frame 385381; its expiry release is recorded
at frame 385384. No listener remains on port 9528. This is expiry and graceful
disconnect evidence, not a deliberate Python-crash test or a guarantee against
post-release physical inertia. Manual-control confirmation remains pending.

Five completed segment records total 1983 steps: 560/566/564 timeout segments,
then 166/127 cleared segments. The last 17 steps belong to an unfinished segment
and are not included in episode summaries. The actual loop completed normally
at its 2000-step bound; no fault or budget interruption was logged.

The private oracle log contains 23 approximate labels: one heal, eight enemy
spawns, one player damage, two room clears, seven enemy damage and four enemy
kill estimates. Completed summaries report one half-heart lost and 12 enemy HP
removed. Positive HP labels include 100 in a spawn observation; values are raw,
not calibrated applied damage. Disappearance estimates are not exact kill proof.

The operator subsequently confirmed manually entering rooms during this check.
Manual input therefore contributed to the recorded gameplay. Do not infer
autonomous room navigation, autonomous combat success or
learning from the room-clear records. No forced death/reset or restart was sent.

Private evidence: runs/live/sessions/20261018-161833-a0ff2f/{live,oracle}.jsonl,
local summary.json and the current game's session-filtered Lua log. Raw logs,
approvals and personal game data are excluded from Git.

## RL evaluation

Not run. Random mode is an integration scenario, not a trained-policy evaluation.
No model checkpoint was created and no progression/achievement claim is made.

## Limitations and continuation

Task 5.3 is accepted for negotiation and plausible raw oracle values, with exact
HP semantics still uncalibrated. Task 5.4 remains open because its death/restart
criterion was not exercised, despite completing 2000 real accepted actions with
no logged protocol errors. Do not force a death to manufacture acceptance.
Task 5.5 and archive remain open. The next operator-directed check requires
manual-control confirmation and readiness in a room with enemies, within the
remaining original approval. A new run must not renew its restart authority.

## Second real check: operator-assisted room navigation

- Start: 2026-10-18 16:23:36 CEST; original approval had 552 seconds remaining.
- The operator reported the same file-2 game paused in a room with enemies.
  The agent connected, then instructed the operator to unpause and release keys.
- Command: the command above with seed 19; same 2000-step/six-minute/zero-fault
  limits. No approval renewal, relaunch or installed-file change occurred.
- Private evidence: runs/live/sessions/20261018-162336-0b02be; exit 0.

The second check completed 2000 accepted actions and 513 tear records across two
Lua sessions: 7761b7bfd74647feba13f00357eb6258 (epoch 1) and
542bb43fb6ef4fedb0e2be5575aa8801 (epoch 2). Eight finished segments total 1846
steps; the final unfinished segment contains the remaining 154 loop steps.
There are no logged fault/protocol-error events. The operator explicitly reported
helping enter several rooms, so both recordings are assisted integration checks,
not independent gameplay or policy-quality evaluations.

The oracle file has 158 approximate labels: 23 spawns, 101 enemy-damage labels,
15 disappearance/kill estimates, 13 player-damage labels, five clear labels and
one death. Finished-segment totals are 228.5 enemy HP removed and 13 half-hearts
lost; these are estimates, not exact applied-damage attribution or all-run totals.

The death produced an automatic sequence in the actual Lua log:

```text
Death restart scheduled session=7761b7bfd74647feba13f00357eb6258 epoch=1
Death restart dispatch session=7761b7bfd74647feba13f00357eb6258 epoch=1 attempt=1
Death restart confirmed old_epoch=1 new_epoch=2
```

Fresh actions and tear records follow in the epoch-2 session. Only one restart
dispatch is recorded; none was forced by the operator/agent tooling. Release
records total 1993 expiry and seven transition releases. Final sequence 1339,
accepted at frame 4250, expired at frame 4253. The Python process ended normally
and no listener remained on port 9528. The operator then confirmed manual movement
and shooting work with no stuck inputs or hangs. This does not replace a separate
deliberate Python-crash test or establish stability of many consecutive restarts.

Task 5.4 is accepted as an assisted live integration check: 2000 steps, damage,
death, automatic restart, reconnect, continued actions and no logged protocol
errors. No autonomous navigation, learning or progression claim is made. Task
5.5 (short budgeted training checkpoint) remains not_run; do not archive yet.
