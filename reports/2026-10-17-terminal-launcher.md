# Evidence: terminal observation launcher and progression goal

- Date/time/timezone: 2026-10-17, Europe/Amsterdam (CEST).
- Starting revision: 6df189c3412f3c5ab33f8d7c81cd142a13051267; working tree modified.
- Scope: extend active bridge-handshake-and-observation with bounded terminal
  launch; record Dead God on file 2 as the final gameplay goal. No RL/control/reset.
- Versions: installed Repentance+ v1.9.7.17 / build 22878971; observer 0.1.0;
  Python 3.12.14. Production dependencies and lock files unchanged.
- Configuration: default 3000 snapshots, 180-second connect, 900-second total limit;
  temporary --luadebug, observer artifact hashes in OBSERVATION_PROTOCOL.md.
  Current canonical JSON LaunchOptions SHA-256:
  5036e980bbd120c3567aae185af28ec9ed08cbdeaf7f9d848bad8fbe239c93a4
  (including reconnects=3; initial live version had no retry support).
- Scenario/split/seeds: authorized read-only ordinary-profile observation; no
  training/evaluation split or RNG claim. Ctrl+C, bounded failure or sample/deadline
  ends observation; no game termination.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Quality gates | scripts/Check.ps1 with isolated Lua tooling | 0 | passed | Ruff, format, mypy, 89 tests (25 launcher, 17 Lua, 45 observer, 2 diagnostics), pip and strict validation |
| Strict delta | scripts/OpenSpec.ps1 validate bridge-handshake-and-observation --strict | 0 | passed | Both delta capabilities accepted |
| Archive and main-spec validation | scripts/OpenSpec.ps1 archive bridge-handshake-and-observation --json --yes; validate --all --strict | 0 | passed | Nine requirements synced; archive 2026-10-17-bridge-handshake-and-observation; five main specs passed |
| Already-running guard | python -m isaac_threrisaifuture.launcher --preflight-only | 2 | passed | Expected explicit refusal; existing game not interrupted |
| Closed-game preflight | Same command after user normal exit | 0 | passed | Installed hashes match; no processes launched in preflight |
| First entry implementation | Windows PowerShell -File scripts/Start-Observation.ps1 -PreflightOnly | 1 | failed | Execution policy rejected .ps1; entry replaced with direct Python/.cmd; no policy changed |
| Offline launcher guards | pytest tests/test_launcher.py | 0 | passed | Real loopback with simulated peer; budget, refusal, artifact mismatch, bind failure, launch/interruption cleanup; no Isaac binary executed |
| Real script launch | Start-Isaac.cmd --samples 3000 --duration 900 in visible terminal | not captured | passed for launch/handshake | Listener before launch; actual game and handshake; user confirmed room on file 2 |
| First live disconnection | User died and restarted; Lua closed peer | n/a | failed for session continuity | 427 snapshots in 86.010 seconds; fault logged; bounded reconnect was subsequently implemented |
| Reconnection amendment | Launcher loop with real sockets and simulated peers | 0 | passed offline | Fresh session, shared budgets, exhausted retries and malformed data handled; no automatic game reset |
| Separate observe CLI soak | observe --samples 3000 --accept-timeout 60 --reconnects 2 | not captured | completed with recovered timeout | 3000 snapshots; file growth interval 609.252 seconds; two sessions after one message deadline; cause unknown |
| Production launcher reconnect loop | python reports/local/probe-launcher-reconnect.py; real game, deliberate local socket closure | 0 | passed | 50 actual snapshots, two fresh session IDs, automatic recovery in about 1.05 seconds; no gameplay commands |
| Automatic slot selection / identity | No API installed or exercised | n/a | not_run | Baseline flag unknown; REPENTOGON SaveMenu is a documentation-only candidate |
| Learning / Dead God campaign | None | n/a | not_run | Future roadmap items, not implemented or claimed |

## Real game

User normally exited before this test. A fresh local backup copied and hash-checked
21 files from current Repentance+ Documents and Steam app userdata roots under
ignored reports/local. Earlier broader 120-file backup remains available; neither
establishes full isolation or verified restoration. No saves/settings were edited.

The script was started in a visible terminal, without Computer Use or screen
capture. Steam asked the user to confirm the temporary --luadebug argument;
the agent did not accept that UI. The user subsequently confirmed being in a room
on file 2. Slot identity is operator-reported, not attested by the wire protocol.
Actual handshake: session 81af32e03714478db27be893af8744b8, Lua 5.3, no extender,
mod 0.1.0, protocol/schema 1; game metadata unavailable on the wire. Raw event logs
and process/resource samples are ignored local files; no personal data is included
in this report. The first live session received 427 snapshots in 86.010 seconds,
then peer EOF. The user explicitly reported death and a new run. EOF itself did
not identify death; terminal launch had succeeded but the initial no-retry session
continuity behavior was insufficient for this workflow.

The updated launcher permits three reconnect attempts by default, bounded by the
original sample/deadline budgets; malformed protocol fails immediately. A separate
existing observe CLI reattached to the running game as session
a73e9ced17fc434b88fcb3dd22f18289, epoch 2. Its fresh snapshots reported six red
half-hearts, matching the user's manual HUD report; initial paused frame 512 stayed
constant, then active frames advanced. The game log also referenced the file-2
persistent data basename; this corroborates operator selection but is not a wire
slot attestation or evidence of achievement eligibility.

The CLI soak completed 3000 snapshots, 758 positions and 14 distinct local room
visits. Raw log creation-to-last-write interval was 609.2517689 seconds. One read
exceeded the three-second deadline and was explicitly recovered, changing the
session to 2010b83e83694513ba7497a728fe2806. There were no malformed accepted
records. This is not an uninterrupted zero-fault soak; callback silence cause is
unknown. The user reported walking and changing rooms; the same interval changed
the observed position and room-visit counter (0 to 1 at the first correlation).

Then a local harness called the production observe_sessions function directly
against the real Lua module. Its ObservationClient subclass deliberately closed
the Python peer after ten validated snapshots and raised PeerDisconnected; the
production retry handler accepted the actual Lua reconnect and completed fifty
snapshots. Sessions fd5af127849e4b939cc8cb81fc619e6d and
9301da1b5797424ab9fba33249f0ee5d differed; retry-to-handshake delay was 1.050 seconds.
The probe exited 0 and no listener remained. This verifies the production loop's
transport recovery with real game I/O; it did not force a character death, restart
the game or claim a new full terminal-launch test after the amendment.

Resource sampling: 127 game samples from 12:09:17 to 12:20:15 and a later 5-second
series covering the soak tail. Game private memory stayed within 518176768 to
522936320 bytes (less than 5 MB range while rooms changed). The later Python
process samples were 20103168 to 20172800 bytes; sampling began mid-soak, not at
Python startup. No evident unbounded growth was seen; this finite observation is
not proof that leaks cannot exist. The game remained Responding=True after all
Python probes exited. The user then explicitly confirmed that there were no visible
hangs and the character still moved after observer shutdown. This supplies the
human-visible check separately from process responsiveness. Runtime acceptance
passes for the recorded read-only scenario with the recovered timeout disclosed.

## Legacy-mod follow-up

After the runtime checks, the user requested disabling old mods. Inventory found
seven enabled legacy mods plus the observer, and four already-disabled legacy
mods. The long-run evidence above used that mixed profile, not an observer-only
profile; do not generalize it to all mod combinations. With the game already
closed, seven empty disable.it markers were created without deleting mod files or
changing Workshop subscriptions. Existing disabled markers were preserved. Prior
marker state and source-root map are backed up under ignored reports/local.

Newly disabled: Boss Rush Wave Counter, Detailed Respawn, Better Lucky Pennies,
Enhanced Boss Bars, External Item Descriptions, Planetarium Chance and TimeMachine.
Readback showed only Isaac Future Observer enabled. The Documents Repentance+ mods
root was empty. No save or Steam/Cloud setting was edited. The existing game log
contains modding-state mismatch messages for some saved-run candidates; changing
the mod set must not be followed by a forced restart or save replacement. Runtime
loading of the new observer-only configuration remains to be verified on next
normal launch; the original acceptance is scoped to the recorded test profile.

A separate Start-Isaac.cmd request with samples=50, duration=240 and reconnects=0
bound its listener and requested launch, but received no peer before the deadline.
No game process was observed during the follow-up. Steam argument confirmation
and manual file/run selection had been handed to the user; no agent UI input was
issued. This follow-up is **not verified integration of the observer-only profile**.
Its finite failure is separate from the accepted earlier recorded scenario.

### Subsequent observer-only confirmation

The user later confirmed continuing the existing run on file 2. Fresh game log
(2026-10-17, local timestamp 17:09:15) showed only the observer under mod Lua script
execution entries. Disk readback showed 11 legacy disable.it markers, with only
isaac_threrisaifuture_observer enabled. No settings or markers were changed again.

Command: `.venv/Scripts/python.exe -u -m isaac_threrisaifuture.cli observe --samples 50 --accept-timeout 15 --reconnects 0`.
Exit 0; one handshake, session 70a882d976ee45eb8c5fc9f38f7eea1c; 50 valid paused
snapshots, first/last frame 24830; error log empty. Constant frames are consistent
with the reported paused status, not evidence of active frame advancement. This
closes the short observer-only loading/connection unknown without claiming a
second ten-minute active-game test or achievement eligibility. The listener closed
after the budget; game remained open and Responding=True. No game input, reset,
save write or relaunch was performed by the agent in this confirmation.
Raw probe records remain under ignored reports/local.

## RL evaluation

Not applicable: no training or controlled gameplay. Dead God progress, win rates,
achievement eligibility and learning quality were not tested.

## Self-review and continuation

Completeness: all 12 tasks are complete. Task 4.1 has approved-profile exception, exact deployment, actual
handshake and user-correlated health/movement/room evidence. Launcher tasks 5.1–5.5
have implementation/planning and the evidence above. Task 4.2 includes the user's
final no-hang/continued-control confirmation; the recovered timeout is recorded.
Correctness: real sockets with simulated peers cover listener-before-launch,
budgets, bind conflict, process guard, deployment mismatch and cleanup. The actual
launch and handshake are separate evidence. Coherence: the launcher reuses the
typed client without adding commands or UI automation; the initial PowerShell
design was explicitly revised after the execution-policy failure. No persistent
security or Steam settings were changed.

Verification scorecard: completeness 12/12 tasks; all nine requirements mapped to
implementation and offline/real evidence; design and implementation agree after
the explicit Python-entry/reconnect amendments. This was a separate self-review,
not an independent reviewer. No unresolved acceptance blockers remain for this
bounded read-only change. The change was synced and archived after strict validation;
post-archive Check.ps1 passed all 89 tests and five main specifications. Final
goal requirements, new observer-only profile validation and current online/mod
achievement eligibility remain research dependencies, not implemented claims.
Automatic slot selection remains unimplemented. Stop before safe actions.
