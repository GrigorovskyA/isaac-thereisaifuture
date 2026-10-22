# Experiment: restart lifecycle diagnostic capture v1

Predeclared: 2026-10-19, Europe/Amsterdam. Baseline bd51d93.
Purpose: observe actual callback/authority order after a natural-death restart.
This is a diagnostic random-action check, not training or policy evaluation.

## Second bounded attempt (operator requested, 2026-10-19)

After the first room cleared without death, the operator requested another enemy
room specifically to exercise death/restart through ordinary combat. Use random
seed 28, otherwise the same 2048-decision/three-minute/one-minute-handoff limits,
one deliberate ten-minute approval and max_restarts=1. This is a new separately
requested attempt, not renewal of the finished invocation. No kill command,
health/save edits, scripted damage, enemy spawn or forced reset. If no death
occurs, stop at the original bounds. After any death/restart, remain neutral and
collect reconnect evidence without another combat acknowledgment. No training.

The second invocation expired while still paused, with zero acknowledgments and
actions. The operator then explicitly requested another invocation with a
two-minute handoff wait. Keep seed 28, 2048 decisions, the three-minute global
cap and the SAME original approval/attempt counter. No file replacement,
approval renewal or mod reload between these invocations. Only this fresh
operator-requested invocation uses --gate-wait-minutes 2; its one-shot readiness
helper expires after 90 seconds. Stop after the first combat segment and collect
neutral reconnect evidence; grant no second combat readiness.

## Fixed budgets and authority

- Random seed 27, at most 2048 decisions and three minutes including waits,
  pauses and reconnects; stop at the first applicable bound. Zero tolerated faults.
- Opt-in combat gate, at most one minute per operator handoff, no automatic ack.
- One deliberate ten-minute local approval while closed, max_restarts=1.
  No renewal on reconnect or handoff. Existing guards remain unchanged.
- Diagnostics: 20 minutes from first event, 256 attempts, 768 bytes per record;
  these are diagnostic limits, never permission to extend the three-minute run.
- No model load/update/checkpoint, forced death, additional reset or enemy spawn.

## Preparation and command

Operator closes normally; verify process absence twice. Preserve installed files
privately. Deploy the accepted Lua with only lifecycle_diagnostics changed to true;
repository default remains false. Record hashes and validate against a staged
copy with precisely that one substitution. Normal repository preflight would
correctly reject the deliberate diagnostic difference; do not misreport it as
an exact source match. Metadata must match source exactly.

Manual launch, file 2 and Continue remain operator actions. Prepare a small
ordinary enemy room on pause, then confirm the slot, room and released keys.
Only after current identity checks prepare a one-shot acknowledgment bound to
the actual gate request/session/epoch/room. Ask for unpause after that helper is
ready; never wait in a long blocking poll while the player is exposed.

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode random --confirmed-save-slot 2 --steps 2048 --minutes 3 --combat-gate --gate-wait-minutes 1 --max-faults 0 --seed 27 --connection-timeout 20
```

No second combat acknowledgment is planned: after death/restart or room clear,
remain neutral during the operator wait and inspect lifecycle/hello records.
Do not select New Run/Continue or force a second start to reproduce the symptom.
Do not infer manual input from an uncorrelated callback.

## Outcomes and cleanup

Accept diagnostic runtime evidence only if actual natural death, dispatch,
exit/start, confirmation and subsequent hello are correlated with native log
records. A second unexpected start may identify its invalidation branch; its
engine cause may still be unknown. If no natural restart occurs within budget,
mark this requirement blocked/not_run; do not repeat or extend automatically.

Stop on protocol/authority failure or any original deadline, release and close
Python, preserve private logs, and obtain operator confirmation of manual control.
After normal exit, restore the reviewed repository default-off build and verify
source/installed hashes. Keep tasks 3.1-3.3 open until their evidence exists; no
archive or resumed learning follows solely from this preparation.
