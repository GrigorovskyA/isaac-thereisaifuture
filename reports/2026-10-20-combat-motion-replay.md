# Evidence: combat motion replay

- Date: 2026-10-20, Europe/Amsterdam.
- Base revision: 1486d213bac33eb5c4e72d7bf48b9265bd9c885f plus the reviewed
  combat-motion-replay module, tests and OpenSpec artifacts.
- Scope: offline displacement and walking-grid analysis of the already completed
  [paired native pilot](2026-10-20-paired-combat-audit-results.md). No new game run,
  learning, inference modification, reward or observation-schema change.
- Native source: Repentance+ 1.9.7.17.J460, observer 0.5.0-dev, Lua 5.3;
  Python 3.12.14. Existing authorized ordinary file2 profile; no isolation claim.
- Checkpoints retained: conservative-v2 development t1536 and its explicit
  budget-only extended descendant 08e0d262-s20-t6912. No checkpoint selection.

## Recorded movement

The source is one mixed-policy trajectory, not independent or matched encounters.
All 657 decisions match native accepted direction, session and epoch; accepted
frame is the reference observation frame plus one update. Consecutive accepted
poses produce 656 comparable pairs, all within one session/epoch/room visit and
1..15 updates. The last decision has no future pose and is excluded.
Near-stationary means requested movement and Euclidean displacement below 0.5
units. It is not an engine collision label: inertia, knockback and timing remain
possible influences. Idle commands are never counted as movement failures.

| Executed controller | Comparable pairs | Right commands | Right with displacement <0.5 | Right starting at x>1088 |
|---|---:|---:|---:|---:|
| t1536 | 255 | 1 | 1 | 1 |
| t6912 | 256 | 216 | 197 | 207 |
| random | 145 | 28 | 4 | 4 |

These are executed controller windows, not all shadow predictions. The newer
policy's repeated right commands were usually near-stationary beside the right
boundary. This supports a positioning-stagnation diagnosis on this capture;
percentages do not estimate general gameplay performance.

## Measured geometry

Initial accepted player position was (1080,280), grid cell (26,4). Its right
neighbor (27,4) is blocked; left/up/down neighbors are walkable. The grid has
28x16 cells spaced 40 units, origin (40,120), room index82, shape9. Cardinal
shortest walking-grid route to the nearest initially encoded enemy at (680,560)
is 17 edges, or 680 units along cell centers. Routes to all eight initial enemy
centers exist (17..24 edges). This route was calculated offline and never executed.

The policy already received 12 obstacle slots in each recorded observation,
including nearby right-side obstacles. Their relative coordinates remained
available; the obstacle input was not absent. Absolute player x was clipped in
648/657 inputs while native x ranged approximately990..1090. Existing checkpoint
inputs were preserved rather than silently changing coordinates during replay.

Walking blockers include room geometry and other grid hazards; they are not a
projectile-collision mask. A route on this coarse grid is not physics acceptance.
Nearest-target Euclidean distance was approximately350..597 units, but actual
weapon range, tear trajectory and line of sight were not recorded. No conclusion
that enemies were out of range or behind tear-blocking obstacles is justified.
Prior raw sampled enemy HP remained90 throughout; no new damage claim is made.

## Replay and finite worker contract

One fresh gpt-6-luna/high script worker executes the exact prewritten
`reports/local/Run-MotionChecks.ps1`, sequentially running targeted pytest,
`./scripts/Check.ps1` and `reports/local/replay_combat_motion.py`.
The script sets PYTHONPATH to the existing Lua test runtime, ISAAC_JSON_LUA to
installed resources/scripts/json.lua and TEMP/TMP to the existing local test temp
inside the same process. No dependency installation or retry is authorized.

Recorded plan: reports/local/motion-worker-plan.md. Bounds: eight minutes command
wall time, absolute deadline2026-10-20T21:18:00+02:00,512MiB incremental test-temp,
32MiB new check/analysis artifacts; zero game steps/deaths/restarts. 159 frozen
paths cover implementation, helpers, input captures and retained models/configs.
The primary freezes those files during execution and verifies returned evidence.

Input files (local raw logs excluded from Git):
- runs/paired-combat-focus-20261020/policy-decisions.jsonl
- runs/paired-combat-focus-20261020/oracle-snapshots.jsonl
- reports/local/paired-combat-focus/game-log.txt

Outputs: reports/local/combat-motion-replay/analysis.json and spatial-map.svg,
plus motion-targeted/gate/replay.txt and corresponding exit JSON receipts. The
SVG is a numerical plot of the recorded positions/grid, not a screen capture.
Future poses and management navigation are offline analysis only; neither enters
policy observations, normalization, recurrent state or reusable inference input.

## Verification

| Check | Command/evidence | Exit | Status |
|---|---|---:|---|
| Targeted behavior | pytest test_combat_spatial_diagnostics.py test_combat_diagnostics.py -q | 0 | passed:33 tests |
| Full Windows gate | Run-MotionChecks.ps1 -> Check.ps1 | 0 | passed:2028 tests,zero skipped;Ruff/format121 files,mypy51 source files,pip clean,OpenSpec38/38 |
| Frozen native replay | replay_combat_motion.py | 0 | passed:657 commands,656 pairs,no unmatched actions;657 measured nearest-target routes available,10..22 edges across samples |
| Primary readback | Three stage receipts,raw logs,independent coordinate/count checks | 0 | passed:216 right/197 near-stationary;all eight initial routes and12 obstacle slots verified |
| Immutability | Primary SHA256 recomputation | 0 | passed:159/159 frozen files unchanged,including both models/normalizers and all three capture hashes |
| New native physics/range test | Not required by offline scope | -- | not_run |

Worker receipts finish21:09:32(targeted),21:10:20(gate),21:10:21(replay),
all before the deadline. Exact command start was not captured; preparation at
21:08:52 bounds total subsequent execution below90seconds. Final observed test
storage was250,303,197bytes;analysis JSON/SVG387,790bytes plus stage receipts/logs
11,276bytes,well below the declared limits. No periodic peak sampler was active,
so peak disk use is unverified. This bookkeeping limit is retained rather than
claimed as enforced peak monitoring. No retries or game actions occurred.

### OpenSpec verification and primary self-review

| Dimension | Result |
|---|---|
| Completeness | 4/4 tasks;2 added requirements mapped;no removed/renamed requirements |
| Correctness | 2/2 requirements and4/4 scenarios covered by motion/grid behavioral tests |
| Coherence | Design followed;bounded1024-cell BFS,existing typed Vec/NavigationGrid;offline-only imports confirmed |

Motion evidence maps to combat_spatial_diagnostics.py:38 (context/frame checks,
displacement,projection,idle exclusion);grid evidence maps to line56 (endpoint
validation,finite cardinal BFS). Tests cover inertia,idle,all directions,session/
epoch/visit changes,nonincreasing/long frames,detours,blocked/outside endpoints,
disconnected and same-cell paths. Code search found no runtime controller,
observation,normalizer or reward consumer of the new module. JSON source hashes
and SVG XML were checked separately. This is primary self-review,not an
independent code review;Luna executed commands only.

No critical issues or specification warnings found. One operational suggestion:
record command start and periodically sample disk on the next worker assignment.
All offline behavior/spec checks passed;new native physics was outside scope.
The change remains unarchived. Synthetic RL smoke was not repeated because no
training stack/dependency/checkpoint behavior changed;the full gate retained its
existing checkpoint tests.

## Limitations and continuation

No new runtime test or training was attempted. Existing Globin/revival acceptance
remains pending under live-target-phase-audit6/7. The next concrete measurement is
range/tear trajectory/projectile-blocker telemetry and comparable frozen combats,
before allocating more training budget or changing reward. Any observation-schema
repair requires explicit new checkpoint compatibility/lineage; do not silently
resume t6912 with different inputs. Keep training latest at t6912.
