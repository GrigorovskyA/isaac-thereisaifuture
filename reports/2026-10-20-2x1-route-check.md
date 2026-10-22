# Evidence: native horizontal 2x1 route

User prepared a long room and requested the check. PID37664/gamev1.9.7.17,file2
confirmed by latest persistent-data load. Initial action-free native probe:
active epoch1/visit4/frame5009,index97,shape6/2x1,clear/no enemies,
position(75.303207397461,264.67190551758),five red half-hearts. Measured v2
grid28x9/252 cells; open ordinary exits slots5(upper-right)/7(lower-right).
Observer0.5.0-dev/Lua5.3/no extender. Full t5120 model/normalizer reload,
identity/hash/latest and source/installed Lua+metadata unchanged; no deployment.
Fresh15-minute approval loaded, exact hash retained. Private setup/probe:
reports/local/long-room-20261020-102358/.

One production random seed21 invocation: <=1 combat decision if unexpected combat
appears,90-second run/60-second gate cap,maxfaults0,at most one natural death
restart,disk512MiB. Navigation256 commands/90 pulse seconds/four transitions/
three stationary pulses. Immediate normal close on runtime return before slow
evidence handling. No training/model update, forced room/reset/teleport, second
invocation or automatic renewal. Native capture alone is not a passed route.

## Runtime result: observed horizontal 2x1 route passed

Production random CLI used seed21/steps1/minutes1.5/maxfaults0/combat-gate/
auto-navigate/gate-wait-minutes1/confirmed-save-slot2/connection-timeout15.
Logs runs/live/sessions/20261020-102416-3c2c5b/ and
reports/local/long-room-console.txt. Exit0, handled four-transition cap.

Goals: index97/shape6/slot5 ->84/shape1/slot1 ->71/shape12/slot3
->84/shape1/slot2 ->85/shape1/slot0(last goal stopped before movement).
The new2x1 route crossed from the left-side player position to upper-right
secondary slot5 and physically exited. Subsequent cleared-room travel included
an already observed LBR and neighboring1x1s. Total four native visit changes.
Lower-right2x1 slot7 was not tested; no full-exit/all-layout claim.

44 accepted navigation movement commands and44 releases:40 accepted releases,
four rejected transition races reconciled with fresh same-epoch later visits
under the existing bounds; rejected releases are not neutral acknowledgments.
13.218s wait/259 snapshots, zero combat decisions/readiness/reward/episodes/
restarts/stalls/resume races/observation gaps/infrastructure faults/cleanup errors.
No PPO/model update, extra invocation or automatic budget renewal.

## Cleanup and verification

Immediate normal WM_CLOSE after runtime return; Observer unloaded / Isaac has
shut down successfully plus process/listener absence verified. Exact temporary
approval hash checked/file removed; closure removed cached authority. Full t5120
model/normalizer reload, complete identity/hash/latest and source/installed Lua+
metadata comparison unchanged. Disk202251767 bytes <512MiB. Private cleanup JSON
retained. No final live-health snapshot before prompt close; five initial
half-hearts are not exact final-health evidence. Human manual-control recovery/
non-intervention was not measured.

Evidence-only follow-up, no code/dependency/schema/deployment change. Prior
1893-test/zero-skip gate retained, not rerun for documentation. Separate self-review
confirms new shape6/slot5 route coverage only. Strict validation and whitespace
check passed; representative tasks remain10/10. No archive/commit/delegation.
Native observed shapes1/6/7/8/9/10/11/12; remaining2..5(IH,IV,1x2,IIV) require
separate finite native scenarios. All twelve shapes retain offline coverage.
