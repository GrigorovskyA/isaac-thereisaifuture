# Evidence: native LTL route

User requested a check in a new prepared room. PID46980/gamev1.9.7.17,file2
confirmed by latest persistent-data load. Initial action-free native probe:
active epoch22/visit1/frame1738,index71,shape9/LTL,clear/no enemies,
position(831.51116943359,276.04217529297),six red half-hearts. Measured v2
grid28x16 with upper-left quadrant missing; only open ordinary exit slot3 at
(320,720). This supplies a new native L rotation and a route around its concavity.
Observer0.5.0-dev/Lua5.3/no extender, source/main.lua+metadata match, no deployment.
Full t5120 model/normalizer reload, identity/hash/latest unchanged before actions;
fresh15-minute approval loaded, exact hash retained. Private setup/probe:
reports/local/new-room-20261020-100559/.

One production random seed21 invocation, <=1 combat decision if unexpected combat
appears,90-second run/60-second gate cap,maxfaults0,at most one natural death
restart,disk512MiB. Navigation256 commands/90 pulse seconds/four transitions/
three stationary pulses. Immediate normal close on runtime return, before slower
evidence handling. No training/model update, forced room/reset/teleport, second
invocation or automatic renewal. Initial telemetry is not a completed route.

## Runtime result: observed LTL route passed

Production random CLI used seed21/steps1/minutes1.5/maxfaults0/combat-gate/
auto-navigate/gate-wait-minutes1/confirmed-save-slot2/connection-timeout15.
Logs runs/live/sessions/20261020-100618-c38c3b/ and
reports/local/new-room-console.txt. Exit0, handled four-transition cap.

Goals: index71/shape9/slot3 ->84/shape1/slot1 ->71/shape9/slot3
->84/shape1/slot3 ->97/shape1/slot1(last goal stopped before movement).
Actual traversal reached the lower doorway from the upper-right player position,
exited LTL, returned, exited LTL again and continued through a cleared neighbor.
The native measured mask excludes the upper-left void; no direct blocked-cell
fallback or screenshot route was used. This proves this measured LTL layout/slot3
route, not all exits, obstacle combinations or start positions.

36 accepted navigation movement pulses and36 releases:34 accepted releases,
two rejected transition races reconciled with fresh same-epoch later visits under
the original bounds, without inventing successful neutral acknowledgments.
11.156s wait/219 snapshots,four visit changes; zero combat decisions/readiness,
reward, episodes,restarts,stalls,resume races,observation gaps,infrastructure
faults or cleanup errors. No PPO/model update, extra invocation or budget renewal.

## Cleanup and verification

Launcher requested normal WM_CLOSE immediately after production process return.
Process/listener absence and Observer unloaded / Isaac has shut down successfully
verified. Exact approval hash checked/file removed; closure removed cached
authority. Full t5120 model/normalizer reload, identity/hash/latest and installed/
source comparison passed unchanged. Disk202195327 bytes <512MiB. Private cleanup
JSON retained with initial probe/setup. No final live-health snapshot before
prompt close: six initial half-hearts are not an exact final-health readback.
No human non-intervention/manual-control recovery claim.

Evidence-only follow-up; no code/dependency/schema changes or deployment. Previous
1893-test/zero-skip full gate retained, not rerun for documentation. Separate
self-review confirms native shape9/observed slot3 coverage while other layouts/
exits remain explicit not_run. Current strict validation and whitespace checks
passed; representative OpenSpec tasks remain10/10. No archive/commit/delegation.
Native shapes1/7/8/9/10/11 now observed. Next: LBR/shape12 (missing lower-right
quadrant), then remaining narrow shapes2..6, under separate finite checks.
