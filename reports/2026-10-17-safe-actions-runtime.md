# Evidence: bridge-safe-actions runtime acceptance

- Date/time and timezone: 2026-10-17, Europe/Amsterdam (CEST). Native action 50-case interval 849656–881557 ms on Isaac.GetTime (31.901 seconds); initial/final native frames recorded below. User manually launched the game at 20:00 CEST and confirmed file 2, safe room and released keys before control.
- Git revision and dirty status: started clean at 9b74446 in D:\isaac. The containing commit adds the runtime record, safer probe pulse/regression check and accepted OpenSpec archive; private raw evidence remains ignored.
- Change scope and acceptance criteria: item 03; explicitly approved ordinary-profile exception, actual slot/instance confirmation, 50 controlled independent/combined sequences, neutral/release, disconnect, forced Python failure and silent-client expiry. All eight tracked tasks are complete within the declared character-0/ordinary-tear scope.
- Game/mod/bridge versions: real Repentance+ J460, v1.9.7.17.J460 in current native startup log; Steam build 22878971 in current manifest. Actual adapter 0.3.1 / Lua 5.3 / extender absent / protocol/schema 1. Wire version/build remain null with unavailable provenance; version identification came separately from local evidence.
- Python/package versions and configuration hash: Python 3.12.14; no dependency change. Installed/source main.lua SHA-256 43d2bc10e63b96d86cefa57630528040e0017674a08d4b57b23a683628879efc, metadata.xml 11d0659831cd4ffec75453f6db13261a02a05f75160501ee27133a973ecffda9. Approval was a private ordinary_profile_exception record for current epoch 1 and operator-confirmed file 2, expiry 600 seconds, with 120-second per-mod-load action authority. Existing action 250-ms / <=15-frame and heartbeat 500-ms limits unchanged.
- Scenario/split/seeds/budget/stop: active solo character type 0, room visit 0, raw red health 8/8 half-hearts. No game seed, train/validation/test split or RL. Ten direction cases repeated five times; movement used one two-frame pulse per case, shooting up to three refreshes with no repeated movement. Each case ended with neutral then release. Stop on room/epoch/health/pause/fault/boundary change; no reset or forced death.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Approved profile/slot/instance | Direct user approval plus current operator slot-2/room/key-release confirmation; process and hash checks | 0 | passed | Ordinary-profile exception explicitly approved; actual game process/current epoch observed; no isolation or automatic slot-detection claim |
| Default connection | ObservationClient, five real snapshots | 0 | passed | Adapter 0.3.1, session b828e63480954de48a18a408f8685946, epoch 1, active frames 61521–61545 |
| Preliminary combined action | Three short refreshes, right movement/up shooting, neutral/release | 0 | passed | Session 5702aa785ed94127a70868cf5f1cf21d; frames 63876–63900, x 314.192 -> 464.118; actual up-tear callbacks, same health/room |
| 50 controlled cases | Finite attach-only Python probe with two-frame movement pulses | 0 | passed | 50/50; session 6be79d8ae9d04b9f9be2bbe331cc4f8f, epoch 1, room visit 0, frames 64863–65825; full case table below |
| Movement effects | Before/after room-space coordinates and expected signed displacement >1 unit | 0 | passed | All 30 non-neutral movement cases changed the intended axis with the expected sign |
| Shooting effects | Native MC_POST_FIRE_TEAR diagnostics joined to session/command sequence; signed dominant velocity | 0 | passed | All 30 shooting cases have matching real tear velocity; 60 matching native tear records, two per shooting case |
| Explicit neutral/release | Each case issues neutral then release; native release diagnostics and received state | 0 | passed | Bridge override removed between cases; no held action reused on fresh connections |
| Socket disconnect cleanup | Dedicated connected peer closes after action ack | 0 | passed | Native release reason Peer disconnected; acceptance-to-release 16 ms |
| Python process failure cleanup | Own hidden test Python child forcibly terminated after ack/ready marker | 1 intentional | passed | Native release reason Peer stopped receiving; acceptance-to-release 183 ms; no game process terminated |
| Silent-client cleanup | Own peer sends nothing for 700 ms after ack, without initial FIN | 0 | passed | Native expiry release 249 ms after acceptance, then heartbeat/authority disconnect diagnostic |
| End-of-test default/lease | Ten real read-only snapshots after cleanup | 0 | passed | Frames 69732–69786, epoch 1, active; safe_actions_v1 absent after nonrenewable lease; private approval removed, no port-9528 listener |
| Operator correlation | User confirms both effects and manual control after shutdown | N/A | passed | User saw movement and shooting and confirmed manual control works without hangs |
| Offline gates | .\scripts\Check.ps1 with isolated Lua test environment | 0 | passed | 242 tests, no skips; Ruff/format/strict mypy/pip consistency and strict OpenSpec |
| Spec/review/archive gates | Strict change validation, separate self-review, verified main-spec sync and archive | 0 | passed | Final completion below records sync/archive validation; no incomplete acceptance task |
| Other weapons, live death/transition edges, RL/campaign | Outside this bounded acceptance scope | N/A | not_run | No generalized compatibility, training, achievement or progression claim |

The preliminary combined action produced a larger displacement than needed
(~150 room units in three 200-ms refreshes) without a room/health change. The
50-case probe therefore used two-frame movement pulses and stationary subsequent
shooting refreshes. The standard action_probe was updated to the exact tested
command pattern, with a regression check preventing shooting refreshes from
repeating movement. Protocol limits and acceptance criteria were not weakened.
No attempt at the unsafe longer 50-case movement pattern was made.

## Real game

Profile authority is the user's explicit ordinary-profile exception, retained for
future bounded checks. File 2 is operator-confirmed, not attested by Lua. The
user first moved from the room edge to its center and released manual keys.
Real native process/handshake/epoch and installed hashes were checked before
writing the private expiring local approval. No Cloud/save editing/restoration,
Steam configuration, mod change under the running game, launch/selection action,
restart dispatch or reset-limit change occurred. Natural gameplay/save writes by
the game are not claimed to be isolated.

All 50 cases kept epoch 1, room visit 0 and raw red health 8/8. Movement success
means signed intended-axis delta >1 raw room unit; it does not require zero
inertia. Shooting success requires an actual native player tear with matching
session/action sequence and the commanded dominant-axis velocity, not just an
input ack. Combined right/up was also observed in the separate preliminary
case while actual movement continued. No projectiles were spawned by the bridge.

Cleanup bounds are measured conservatively from native action-acceptance time to
native release time, not from Python wall-clock exit. The failure happened after
ack/ready, so the observed 183-ms acceptance-to-release interval upper-bounds the
failure-to-release interval. This avoids claiming clock synchronization between
Python and Lua. Socket release was 16 ms; silent expiry was 249 ms, both within
the 250-ms action bound. Tests exercised actual Lua cleanup events while real
movement/shooting had been authorized; physical coasting after release is normal
inertia, not a continued bridge hold.

Every cleanup connection had a fresh session and command sequence starting at 1;
no prior action was replayed. The final read-only handshake exposed no action
capability after the per-mod-load lease. The private approval file was deleted,
all consumers/listeners stopped and game process remained Responding=True. The
user confirmed responsive manual control and no hangs after the test. Nothing
keeps operating the game in the background.

## All 50 outcomes

Common session: 6be79d8ae9d04b9f9be2bbe331cc4f8f; epoch 1; room visit 0;
character type 0. Frame ranges and deltas are actual structured snapshots. Tear
counts are native diagnostics matched to that case's accepted command sequences.

| Case | Move | Shoot | Frame range | dx | dy | Native tears | Result |
|---|---|---|---|---:|---:|---:|---|
| 1 | left | none | 64863–64875 | -8.257 | 0.000 | 0 | passed |
| 2 | right | none | 64875–64887 | 7.730 | 0.000 | 0 | passed |
| 3 | up | none | 64887–64899 | 0.445 | -8.257 | 0 | passed |
| 4 | down | none | 64899–64911 | 0.017 | 7.730 | 0 | passed |
| 5 | none | left | 64911–64935 | 0.001 | 0.544 | 2 | passed |
| 6 | none | right | 64935–64959 | 0.000 | 0.001 | 2 | passed |
| 7 | none | up | 64959–64983 | 0.000 | 0.000 | 2 | passed |
| 8 | none | down | 64983–65007 | 0.000 | 0.000 | 2 | passed |
| 9 | right | up | 65007–65031 | 13.200 | 0.000 | 2 | passed |
| 10 | left | down | 65031–65055 | -13.158 | 0.000 | 2 | passed |
| 11 | left | none | 65055–65067 | -12.367 | 0.000 | 0 | passed |
| 12 | right | none | 65067–65079 | 11.478 | 0.000 | 0 | passed |
| 13 | up | none | 65079–65091 | 0.673 | -12.326 | 0 | passed |
| 14 | down | none | 65091–65103 | 0.023 | 11.480 | 0 | passed |
| 15 | none | left | 65103–65127 | 0.001 | 0.873 | 2 | passed |
| 16 | none | right | 65127–65151 | 0.000 | 0.002 | 2 | passed |
| 17 | none | up | 65151–65175 | 0.000 | 0.000 | 2 | passed |
| 18 | none | down | 65175–65199 | 0.000 | 0.000 | 2 | passed |
| 19 | right | up | 65199–65223 | 13.200 | 0.000 | 2 | passed |
| 20 | left | down | 65223–65248 | -13.163 | 0.000 | 2 | passed |
| 21 | left | none | 65248–65260 | -8.293 | 0.000 | 0 | passed |
| 22 | right | none | 65260–65272 | 7.728 | 0.000 | 0 | passed |
| 23 | up | none | 65272–65284 | 0.445 | -8.257 | 0 | passed |
| 24 | down | none | 65284–65296 | 0.017 | 7.730 | 0 | passed |
| 25 | none | left | 65296–65320 | 0.001 | 0.544 | 2 | passed |
| 26 | none | right | 65320–65344 | 0.000 | 0.001 | 2 | passed |
| 27 | none | up | 65344–65368 | 0.000 | 0.000 | 2 | passed |
| 28 | none | down | 65368–65392 | 0.000 | 0.000 | 2 | passed |
| 29 | right | up | 65392–65416 | 8.805 | 0.000 | 2 | passed |
| 30 | left | down | 65416–65440 | -13.177 | 0.000 | 2 | passed |
| 31 | left | none | 65440–65452 | -12.367 | 0.000 | 0 | passed |
| 32 | right | none | 65452–65464 | 11.478 | 0.000 | 0 | passed |
| 33 | up | none | 65464–65476 | 0.673 | -12.326 | 0 | passed |
| 34 | down | none | 65476–65488 | 0.023 | 11.480 | 0 | passed |
| 35 | none | left | 65488–65512 | 0.001 | 0.873 | 2 | passed |
| 36 | none | right | 65512–65536 | 0.000 | 0.002 | 2 | passed |
| 37 | none | up | 65536–65560 | 0.000 | 0.000 | 2 | passed |
| 38 | none | down | 65560–65584 | 0.000 | 0.000 | 2 | passed |
| 39 | right | up | 65584–65608 | 13.200 | 0.000 | 2 | passed |
| 40 | left | down | 65608–65632 | -13.158 | 0.000 | 2 | passed |
| 41 | left | none | 65632–65644 | -12.367 | 0.000 | 0 | passed |
| 42 | right | none | 65644–65656 | 11.478 | 0.000 | 0 | passed |
| 43 | up | none | 65656–65668 | 0.673 | -12.326 | 0 | passed |
| 44 | down | none | 65668–65680 | 0.023 | 11.480 | 0 | passed |
| 45 | none | left | 65680–65705 | 0.001 | 0.873 | 2 | passed |
| 46 | none | right | 65705–65729 | 0.000 | 0.002 | 2 | passed |
| 47 | none | up | 65729–65753 | 0.000 | 0.000 | 2 | passed |
| 48 | none | down | 65753–65777 | 0.000 | 0.000 | 2 | passed |
| 49 | right | up | 65777–65801 | 13.200 | 0.000 | 2 | passed |
| 50 | left | down | 65801–65825 | -13.158 | 0.000 | 2 | passed |

## RL evaluation

Not applicable. No policy, rewards, environment training, campaign or achievements.

## Separate self-review and OpenSpec verification

One implementing agent used openspec-verify-change for a separate self-review;
no independent reviewer/subagent. All nine changed requirements map to code,
tests and evidence: seven native-player-actions requirements cover explicit
profile authority, bounded inputs, identity, expiry, lifecycle cleanup, evidence
separation and native tear diagnostics; two modified requirements cover observer
negotiation and the explicit ordinary-profile exception without training access.
Offline parsing/replay/expiry/reconnect scenarios passed, and every declared real
acceptance case passed. No removed/renamed requirements exist.

| Dimension | Result |
|---|---|
| Completeness | 8/8 tasks complete; proposal/design/three deltas/tasks present |
| Correctness | All 9 added/modified requirements mapped; 242 offline tests and declared 50 real cases/three cleanup probes/user correlation passed |
| Coherence | Native callbacks and bounded protocol; default observer/restart preserved; no desktop injection, launch/selection automation, RL or reset-budget change |

No unresolved critical issue or warning within the declared acceptance scope.
No required acceptance check was skipped. Additional live character/weapon/
transition edge cases are explicitly outside this first declared scope, not
simulated successes presented as integration evidence.

## Limitations and continuation

Accepted case is one active solo character-type-0 run with ordinary tears on J460,
operator-selected file 2, under explicit ordinary-profile permission. Training
isolation, automatic slot identity, achievement eligibility, special weapons,
co-op, full episode lifecycle and long-run reliability remain unverified future
work. Offline transition/death cleanup is not a claim of live edge-case coverage.

The action lease for this mod load is exhausted and reconnect does not renew it.
Future bounded testing needs current slot/instance confirmation and a fresh
manually started instance/local expiring authority; standing ordinary-profile
test permission is already recorded. Keep application launch/save selection
manual, preserve all reset limits, and do not introduce a supervisor or training.

Private evidence is in ignored reports/local: real readonly/combined/50-case
records, native excerpts, per-case analysis, failure peers and cleanup measurements.
No raw game log, save, backup or local approval is committed. The main-spec sync,
archive and final strict validation are recorded below after they complete.

## Final lifecycle completion

On 2026-10-17, main-spec content comparison passed for all nine changed
requirement blocks. All 8 tracked tasks and required runtime acceptance passed.
`OpenSpec.ps1 archive bridge-safe-actions --skip-specs --yes` exited 0;
`--skip-specs` avoided reapplying already synchronized deltas. Archive:
openspec/changes/archive/2026-10-17-bridge-safe-actions. Subsequent strict
validation passed. No unrelated offline change was archived.
