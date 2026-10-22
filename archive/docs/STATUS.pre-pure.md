# Project status

Updated 2026-10-22 (Europe/Amsterdam). Current state only; dated evidence is history.

## Active work and authority

- `exposed-start-curriculum`: 9/9 scoped tasks complete, unarchived. Corrected
  entry readiness, unscored setup, native learner handoff, optimization, saving and
  reload passed. This is pipeline qualification, not a better-player claim.
- The newly authorized five-minute maximum ready pilot is CLOSED. Actual startup
  through cleanup:232.587s; no worker/game/listener/owned approval remains.
  No automatic repeat, old-pilot resume, New Run or duration escalation.
- [Ready-pilot results](../reports/2026-10-22-ready-curriculum-pilot-results.md).
- `wall-stagnation-replay`:offline replay tool/tests/report done; Windows gate pending.
- `shot-selection-audit`:4/4 tasks complete, unarchived; scripted clear-shot control
  passed. `boundary-supported-progress`:6/6 complete, unarchived.
- [Mixed control](../reports/2026-10-22-mixed-control-results.md) and
  [boundary evidence](../reports/2026-10-21-boundary-progress-results.md).

## Current lineage

- Newest experimental child:`a0a93c29-s20-t27904`, seed20, under
  `runs/live-exposed-start-ready-pilot-20261022/seed-20/checkpoints/`.
  Schema2/723, rewardlive-firing-v5, collectorlive-segment-refresh-v1.
- Exact immutable parent:`a0a93c29-s20-t26368`, under
  `runs/live-boundary-v5-pilot-20261021/seed-20/checkpoints/`.
  Its latest pointer and all ancestors remain unchanged. New child has its own pointer.
- Saved1536 new steps in six256-step rollouts. 70 completed steps were unsaved;
  one further accepted action has no collected endpoint and no sample/credit.
- Independent load:6 completed PPO cycles; SB3 epoch counter412->436,
  Adamstep1648->1744; normalizer count26392.0001->27934.0001,723 inputs.
- Final model SHA256:
  `bb5e3bbd3b4f834b493024014e2047338eff7ed8426f256bedd83fded698f089`.
  Normalizer SHA256:
  `2ece91f96677417db5cf75dbcf3d7b4c0334198f698683d2fbbffabbe200c74e`.
- Exact initial t26368 copy and all six learned checkpoints reloaded; contracts,
  model/normalizer hashes and optimizer/parent chains passed. No model promotion.
- Preserve earlier exposed-start initial copy in `runs/live-exposed-start-pilot-20261022`,
  original v5t24064/t26368, v4`10cb7030-s20-t24064` and initial v4t21760,
  v2`7d53f55f-s20-t21760`, v3`7951bf19-s20-t24064`, t7680/t7424 and original/migratedt6912.

## Latest gameplay and limits

- Setup waited3.000s/60snapshots for visible enemies, then171 one-frame commands
  reached a clear in-range firing position without health loss or shooting.
  Setup contributed no learner entries, rewards or normalization updates.
- Learning:1606 completed decisions; observed enemy HP-loss lower bound7.0,
  player loss2half-hearts, room-clear edges0, deaths0. Coverage is partial.
- Both HP drops occurred at records26/30 on target1 (10->6.5->3). It was last
  listed with3HP at record33, then absent; absence is not credited as a kill.
- 1572/1606 endpoints (97.883%) stayed within20units of(70,209.35), along the
  left wall. Old-corner occupancy was0 but stagnation moved rather than disappeared.
  Seven10-active-second stagnation windows; clear-line exposure6/1613 sampled states.
- Frozen parent and child:64 decisions each, observed HP loss0, player loss0,
  clears/deaths0. Their later one-enemy states differ from the learning start.
  Sequential observational phases cannot establish paired causal improvement.
- Remaining target2 stayed at10HP near(560,360), beyond tear range from the wall.
- Offline diagnosis (`wall-stagnation-replay`, tasks1-3 of5, unarchived): replay
  reproduced all1606 records,0 v5-shaping mismatches,1606 exact re-encodings,
  switch to target2 at record33. No stale state/encoding/execution defect.
  Cause:inherited left prior (frozen t26368 argmax-left1574/1574 post-switch,
  P(right)0.038) plus near-flat zero-sum shaping (phi_v5 0.382-0.397) and no
  observable route (12/53 obstacles). No reward/observation patch justified.
- Next:Windows `Check.ps1` and replay reproduction at the committed revision; then a
  separate observation-3 OpenSpec change. No native stage until its offline screen.
- [Wall-stagnation diagnosis](../reports/2026-10-22-wall-stagnation-diagnosis.md);
  [offline task](tasks/2026-10-22-wall-stagnation-offline.md).

## Verification

- Final source gate remains2416 tests passed, zero skips;56 strict items,
  mypy66files, lint/format/pip passed;718 gate inputs matched.
  Its rejected50.2s total timing is corrected to unknown; counts/identity passed.
- Ready pilot:1195 frozen inputs independently unchanged,1906 accepted actions,
  all released. 171 setup holds exactly1frame;1735 others exactly3frames.
- All1606 completed learner rows joined to native accepts and re-encoded to723
  recorded inputs. Lag0/1 on1601 rows;one each at2/3/4/6/7 within the15frame guard.
  All6 actual optimizer-refresh first commands joined at0/1frame lag.
- One deadline-censored accept at84664 expired/released at84667, not fabricated
  into a completed endpoint. Saved1536/unsaved70 and native attempts reconcile.
- Trace23432632bytes, terminal output101701107bytes; within128MiB/2GiB caps.
  No retry/fault/restart/NewRun. Native shutdown/observer close and absent
  game/listener/owned approval verified. No forced kill or manual save edits.
- Current milestone changes documentation only after native execution; source,
  config, dependencies and deployed Lua unchanged. Final checks:strict specs,
  local links, diff and saved model/trace/hash readback; no unnecessary full rerun.
- Native death/fault injection, held-out/multi-seed improvement, robust room
  traversal, full-run and Dead God acceptance remain unverified.

## Earlier entry evidence

- First curriculum pilot refused initial visibility before action;closed,not resumed.
- No-action capture then found60initial snapshots with oracle enemies but no visible
  enemies;target appeared at sample61 after3.031s. Bounded readiness now allows
  5s/100snapshots inside setup's30s;zero commands or lease renewal while waiting.
- [Windows review](../reports/2026-10-22-exposed-start-windows-review.md) and
  [entry readiness](../reports/2026-10-22-entry-readiness-results.md).

## Workflow and navigation

Primary owns implementation/acceptance;one optional Luna/high script worker executes
an exact finite assignment. No file bus, heartbeat or scheduled supervisor.

[Roadmap](../ROADMAP.md) | [Runtime authority](RUNTIME_AUTHORITY.md) |
[Development guide](DEVELOPMENT_GUIDE.md) | [Script runner](SCRIPT_RUNNER.md) |
[Historical snapshot index](history/2026-10-21-workflow/INDEX.md)
