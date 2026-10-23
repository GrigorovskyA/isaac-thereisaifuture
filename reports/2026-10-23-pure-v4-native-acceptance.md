# Evidence: pure-v4 schema-5 Windows gate and native qualification

- Date: 2026-10-23, Europe/Amsterdam (CEST, UTC+02:00). Timer start 14:34:34.517;
  native session start 14:34:35.113, first playable snapshot 14:34:58.564;
  timer fired 14:49:34.813; cleanup complete 14:49:42.651.
- Source revision: `c494aff6774b1fee5a4013f0b543a88943a7cc43`, personal identity
  GrigorovskiiA, pushed to origin/main. Only pure-v4 and the handed-off pure-v3
  report were staged; unrelated untracked `tools/` preserved.
  Runtime checkout `9d158a5` added only this plan/task/status documentation.
- Scope: OpenSpec `pure-v4-map-hazards-and-stall`, observation schema 5 (3499 floats),
  action v2 [5,5,4] held six updates, reward v5 (stall -10), oracle kill/hit counters,
  and training timing fields. No scripted gameplay or reward shaping added.
- Game: Steam Repentance+ 1.9.7.17, file 2, observer 0.5.0-dev / Lua 5.3.
  Mod deployed with Isaac closed, only main.lua and metadata.xml replaced.
  main.lua SHA256 `38fa156b5bb49e935a987dcdd565cd1cec7edc1420a591a68f15c4ab2b948556`;
  metadata.xml `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.
- Python 3.12 project .venv, torch 2.14.1+cpu; `configs/training-pure-v4.yaml`.
  Full config SHA256 `336fe9b4018d419ab6be14816b5005b27617cd51cbea859d2f4a793677bc9969`;
  contract `9aab0d2d22a7f11225ea2392beaddf1b0f71add1167e1fdb83db30128db9592b`.
  Seed 1, gamma 0.995, ent_coef 0.005; fresh lineage runs/pure-v4, --initialize once.
- Budget/plan: one 900-second qualification wrapper timer from launch, stop.forever
  at its absolute deadline, parent PowerShell keeps Start-Job alive. Native sessions
  retain the 28740-second lease ceiling; disk 20480000000 bytes, fault cap 5, unlimited
  authorized death/stall New Runs. Any qualification fault or missing requirement
  is reported; it does not establish acceptance. One-hour resume is conditional on
  successful qualification; no initialization fallback or old-lineage resume.
- Passive audit: ignored helper SHA256
  `c91dd4cf6c52553dfa7860b357fd6aa7fb33343dce9d17fad590af62ee7f2ea9`;
  cap 1000 seconds, 20000 records, 64 MiB per worker. Unchanged transport values
  and actual pre-normalization policy stall scalars are sampled. Diagnostic oracle
  counters are recorded separately and never passed into policy input.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Windows gate including Lua | scripts/Check.ps1, isolated lupa.lua53 + installed JSON decoder | 0 | passed | reports/local/pure-v4-acceptance-20261023/check.log: 1175 passed, no skips; mypy 31 files; lint/format/pip clean, strict OpenSpec 15/15 |
| CPU RL stack | scripts/Smoke-RL.ps1 | 0 | passed | smoke.log: 16 steps, 3499 inputs, actions [5,5,4]; no game integration claim |
| Closed-game deployment | Copy only main.lua / metadata.xml and compare SHA256 | 0 | passed | deployed-hashes.json; both source and installed hashes match |
| Perimeter walls | Native narrow room, shape 3 | n/a | failed | Room 97 exports 14 wall cells along its left/right perimeter; details below |
| Typed obstacles | Native frames and periodic UI screenshots | n/a | passed | Rock/poop visually match; bomb_rock present; fire and other unencountered classes remain not verified |
| Minimap and room shape | Native snapshots + UI comparison | n/a | passed | Current+visited start, known neighbours, treasure/curse/shop/library icons; shapes 1 and 3 match visible rooms; larger/L-shaped current rooms not verified |
| Stall clock growth/new-room reset | Actual pre-normalization policy scalar | n/a | passed | 0..1, frame 1880 drops 0.4830 -> 0.00191 on entering new room 85 |
| Stall clock enemy-damage reset | Nonlethal damage in the same room | n/a | not_run | No positive same-identity HP decrease captured; enemies seen dying in one hit |
| Kills and own-bomb hits | Native counters and completed episode CSV rows | n/a | passed | Episodes 2/5: kills 2/5; episodes 3/4: hits_own_bomb=1 with two half-hearts lost |
| Restarts | Five stall New Runs, one death New Run | n/a | passed | Five restart commands accepted; epochs 2-7 start at frame 6/7 with full health |
| Checkpoint reload | Actual saved RecurrentPPO + VecNormalize load, recorded-frame inference | 0 | passed | 9aab0d2d-s1-t3584, input 3499, valid [2,4,0] action; checkpoint-reload.json |
| Train timing | Seven train.csv rows | n/a | passed | rollout_seconds numeric; update_seconds empty first, then 7.640..10.281 s |
| Frozen inputs | Hash readback before report edits | 0 | passed | All 807 tracked files unchanged; source/config/deployed hashes also verified by supervisor |
| Timed stop/owned cleanup | Native result + process/listener/approval readback | 0 | passed | learner_exit=0, fault=null, cleanup_errors=[]; no game/learner/listener/approval; stop file retained |
| Conditional one-hour continuation | Acceptance failed | n/a | blocked | Not launched; task 2.3 remains open |

## Real game

Pure-v3 is stopped at `03b9c5e3-s1-t257024`; its final learner exit was 0 and
cleanup_errors empty. There was no running Isaac or native learner during deployment.
Guarded Steam/menu startup confirmed file 2 and Continue. Fresh model initialization
was used once; Continue loaded the saved game (epoch 1, initial frame 538, full health,
no bomb). Subsequent runs were created naturally by the watchdog/death lifecycle.
Gameplay stayed on the structured bridge. Periodic read-only UI screenshots were
compared with structured facts; screenshots never entered the policy.

One wrapper preparation attempt failed before launching Isaac because the new
supervisor directory did not exist. The process and its job exited. The exact
runtime directory was created and startup retried; no model existed and no game
input had been sent by that failed attempt. Evidence: qualification-attempt1-error.log.

Native session: `runs/pure-v4/supervisor/session-20261023-143435-0001`.
The wrapper's Start-Job stayed alive under parent PID 8912 and fired after 900.296 s.
Session elapsed 907.531 s includes 23.281 s startup and shutdown/stop handling.
The first playable snapshot-to-timer interval was about 876 s. Final state
`user_cancelled` reflects the planned timer, not an infrastructure fault.

Six completed episodes: five stalls and one death, 3301 completed-episode steps.
Epoch 7 was unfinished at stop (283 further observed steps); it has no episode CSV
row. Seven saved rollouts / 28 SB3 training epochs, final checkpoint 3584 steps.
No native infrastructure fault or automatic retry occurred. Each stalled episode
charged col_stall=-10, with col_death=0; the death episode charged no stall penalty.

Audit: `runs/pure-v4/qualification-audit/audit-15660.jsonl` (9,768,747 bytes),
1716 sampled native snapshots and 3591 policy observations including seven resets.
Maximum retained native snapshot 8955 bytes, below 49152; this does not qualify all
heavy-room cases. `reports/local/pure-v4-acceptance-20261023/summary.json` and
`hit-kill-evidence.json` retain bounded aggregates.

### Confirmed perimeter defect (blocks task 2.3)

In session `2ac9300d6af649a2a0ee3fb8f3e2b1d1`, epoch 1, room 97, shape 3, frame 4481,
the observer exported seven wall cells at x=200 and seven at x=440, with
y=160,200,240,280,320,360,400. UI observation at 14:36:50 showed these as the narrow
room's left/right exterior walls. The same geometry occurred in epoch 4.
Ordinary rectangular start rooms had no wall obstacles, as intended.

`mod/observer/main.lua:511-519` removes only the outer ring of the rectangular grid
using grid width/height. Native narrow-room perimeter walls lie inside that ring,
so they still fill obstacle slots. This is a real native requirement failure,
not merely missing coverage. Fix the perimeter predicate to respect actual room
geometry, add narrow/irregular-room regression coverage, rerun the Windows gate,
redeploy while closed and repeat the bounded native check before accepting 2.3.
No code or mod fixes were applied during this session.

### Other native evidence

- Initial room 84: map current=true, visited=true, shape 1. Neighbours 85 (treasure,
  type 4), 97 (curse, type 10, shape 3) and 71 (ordinary) matched the visible map.
  Epoch 7 additionally showed treasure 71, shop 97 and library 85 (type 12), all
  known/unvisited; the screen showed the corresponding icons. Unknown/non-current
  rooms were not assumed visited. Off-grid and large/L-shaped current rooms were
  not exercised.
- Actual policy width was 3499 throughout. In epoch 1 the stall scalar rose to
  0.48298 and dropped to 0.00191 at frame 1880 when entering room 85. It dropped
  0.43889 -> 0 at frame 3060 on first entering room 97. Stalled epochs reached 1.0
  before one accepted restart. No native same-enemy nonlethal HP decrease was
  captured, so the enemy-damage reset scenario remains unverified.
- Epoch 2 kills changed 0->1 at frame 1490 (two enemies became one) and 1->2 at
  frame 1518 (one became zero). Episode CSV recorded enemies_killed=2 and a clear.
  Epoch 5 / its completed CSV row recorded five kills and another clear.
- Epoch 3, session `a5e55366de1640ae8b03cb85612e2474`, frame 377: health 6->4,
  own_bomb counter 0->1; a bomb age 36 was 70.7 units away 0.33 s earlier.
  Epoch 4, frame 78: health 6->4, own_bomb 0->1; bomb age 36, distance 81.7,
  0.30 s earlier. Both completed CSV rows have hits_own_bomb=1. Partial epoch 7
  also had a hit, which correctly has no completed-episode row yet.
- Epoch 4 died, then epoch 5 began at frame 6 with six half-hearts. Its release
  acknowledgement after death was rejected. Two final release acknowledgements
  in epoch 7 were also rejected; no bypass/retry was attempted. The native log's
  last action is explicitly released by expiry at epoch 7 sequence 283/frame 1837,
  followed by peer disconnect, observer closure and successful normal game shutdown.
  Thus accepted explicit-release acknowledgement is not claimed.
- Reload used CheckpointPolicy on the explicit final directory, matching hash/seed;
  actual model and normalizer loaded, recorded native frame encoded at stall=0.5
  yielded valid deterministic [2,4,0]. Artifact hashes stayed unchanged.
  Model SHA256 `d2a7ec71b16a4a67500b29be0292e5ecfc50b1f089a43eec65df125c51b222d6`;
  normalizer `a064d5d640b42bebbf7a58c99f041fe31b7271b2a1f2736e0d9743b4a27861aa`.
  Saved gamma=0.995 and ent_coef=0.005, reward contract pure-v5.

## OpenSpec verification

| Dimension | Result |
|---|---|
| Completeness | 5/6 tasks complete; native task 2.3 intentionally open |
| Correctness | Five added requirements reviewed; offline scenarios pass; native perimeter exclusion fails; fire and enemy-damage clock reset not verified |
| Coherence | Implementation follows the rectangular-grid design, but that design is insufficient for actual narrow-room geometry |

One critical issue: exported narrow-room perimeter walls. Missing native coverage:
fire classification, same-enemy damage clock reset, other obstacle classes and
large/irregular/off-grid room/map cases. No archive readiness is claimed.

## RL evaluation

Qualification only, one seed, no improvement or achievement claim. Synthetic smoke
and optimizer updates do not prove better play. The purpose is native correctness.

## Limitations and continuation

Task 2.2 is complete; 2.3 stays open with a confirmed native defect and coverage gaps.
No fire obstacle was encountered, so fireplace classification is not natively
confirmed. Rock/poop were visually matched; bomb_rock was present in native facts.
No hourly continuation was launched because the user's acceptance condition failed.
Pure-v4 is stopped at 3584, stop.forever retained; older lineages remain stopped.
The runtime source/config/mod and all 807 tracked files were unchanged until cleanup
finished; only then was this report/status/task documentation updated.
