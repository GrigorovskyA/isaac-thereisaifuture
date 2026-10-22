# Evidence: readiness-corrected exposed-start curriculum pilot

- Date: 2026-10-22, Europe/Amsterdam. Source revision:
  `e5264e52fccd308fcf96e874bcb01eb46da816a9` (full frozen revision is in the local assignment).
- Scope: one newly authorized five-minute maximum pilot, task
  `exposed-start-ready-native-20261022-01`; no old lease or run resumed.
- Source gate: 2416 passed, zero skips; 66 mypy files, 56 strict OpenSpec items,
  lint/format/pip passed. Source/tests/config/deployed Lua stayed frozen.
- Configuration SHA256:
  `a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15`.
  Seed20, observation2/723, rewardlive-firing-v5, collectorlive-segment-refresh-v1.
  Python3.12.14, observer0.5.0-dev, Lua5.3; game build unavailable in handshake.
- All raw logs, manifests, exact helper and cap plan remain under
  `reports/local/exposed-start-ready-pilot-20261022/` and the separate child run.
  No dependency, deployment, save/Cloud or unrelated changes were applied.

## Outcome

The bounded setup, first learner handoff, real optimization, checkpoint publication
and reload passed. This does not establish a better player: almost all later
behavior remained concentrated against the left wall. No longer stage is approved.

| Phase | Decisions / commands | Observed active seconds | Enemy HP loss lower bound | Half-hearts lost | Clears / deaths |
|---|---:|---:|---:|---:|---:|
| Unscored setup | 171 one-frame commands | 11.922 wall seconds, including readiness | not a learner phase | 0 observed | 0 / 0 |
| Learning | 1606 completed decisions | 176.233 | 7.0 | 2 | 0 / 0 |
| Frozen parent t26368 | 64 decisions | 6.767 | 0 | 0 | 0 / 0 |
| Frozen child t27904 | 64 decisions | 6.667 | 0 | 0 | 0 / 0 |

Coverage is partial. Empty or zero-valued outcomes do not prove absence of all
unobserved damage. Frozen phases were deterministic, sequential and observational;
Continue does not clone the world. They are not paired or held-out comparisons.

## Native entry and control

The ordinary Steam file2 profile was used; no isolation or achievement-eligibility
proof is claimed. Fresh Steam launch and guarded file2 Continue verified Isaac in room83,
session `301b49893dca4d3785313a0aed292581`, epoch1, roomvisit0. No New Run, second
launch, retry, reconnect, fault or death restart occurred. The default-off deployed
observer stayed unchanged; no diagnostic Lua deployment was needed.

Readiness waited 3.000 seconds / 60 snapshots before the fixed target became
visible. Setup then reached the firing position with 171 one-frame move/neutral
commands, no shooting and no observed health loss. At handoff: target1, frame79271,
health5. The first learner observation was frame79376, position(317.217,200.598),
a clear aligned in-range target at(80,200), ordinary tears with range260.
The model-loading gap was not used as a stale handoff token.

1906 action attempts were natively accepted: 171 setup, 1606 completed learning,
128 frozen decisions, and one final learning action without an accounted endpoint.
Every accepted sequence has a release record. Setup holds were exactly1frame;
all1735 other holds were exactly3frames, including the censored final action.
The final action was accepted at frame84664 and expired/released at84667; it is not
invented as a completed learner sample. No game restart was dispatched.

All1606 learning trace rows joined uniquely to native accepts with matching
session/epoch, action directions and endpoint bounds. Their raw frames re-encode
exactly to the recorded723 policy inputs. Reference-to-accept lag: 1601 rows at
0/1frame; one each at2,3,4,6,7frames, within the existing15frame guard. All6 actual
post-optimizer refreshes joined at0/1frame lag. No broad zero-latency claim is made.

## Learning, saved state and lineage

The immutable parent is `a0a93c29-s20-t26368` under
`runs/live-boundary-v5-pilot-20261021/seed-20/checkpoints/`.
Its exact copy and initial latest pointer were prepared only in the absent root
`runs/live-exposed-start-ready-pilot-20261022`. The earlier exposed-start copy and
all other ancestor artifacts/pointers remained protected.

Six256-step rollouts were saved, ending at `a0a93c29-s20-t27904` in the new root.
1536 new steps are saved;70 completed steps belong to an unfinished, unsaved
rollout. One additional accepted action has no collected endpoint. None of these
71 actions is claimed as an extra trained/saved step.

Primary independently loaded the parent, exact initial copy and every one of the
six learned checkpoints. Model/normalizer hashes, contracts and parent IDs passed.
The copied initial artifacts stayed byte-identical. The final loaded state has:

- Timesteps26368 ->27904; 6 completed PPO optimization cycles.
- SB3 `_n_updates`412 ->436 (+24 epoch-counter units); Adamstep1648 ->1744
  (+96 actual optimizer steps). Every intermediate checkpoint matches this chain.
- Observation normalizer count26392.0001 ->27934.0001 (+1542:1536 steps plus
  6 fresh reset observations), with723 inputs. Scripted setup did not add171
  normalization updates or learner entries.
- Final model SHA256:
  `bb5e3bbd3b4f834b493024014e2047338eff7ed8426f256bedd83fded698f089`.
- Final normalizer SHA256:
  `2ece91f96677417db5cf75dbcf3d7b4c0334198f698683d2fbbffabbe200c74e`.

The frozen child references this exact saved t27904, not the copied initial t26368.
Native accepts, saved counters and loaded states establish actual learning work;
changed weights alone do not establish improved gameplay.

## What the gameplay shows

Two measured HP drops on target1 occurred at learning records26 and30:
10 ->6.5 ->3.0, giving a7.0 lower bound. Setup never fired; both drops occurred
during policy control. Target1 was last listed at record33 with3HP, then disappeared.
That absence is not credited as a kill or the remaining3damage. Target2 stayed at10HP.
Player health fell from5 to3half-hearts during learning; no death or room-clear
edge was observed. All observed enemy HP loss happened near the start.

1572/1606 learning endpoints (97.883%) were within20units of(70,209.35).
The exact old corner(70,410) metric was zero, but that is not an escape from
stagnation: the dominant point shifted along the left wall. Seven nonoverlapping
10-active-second stagnation windows were detected. Only6/1613 sampled learner
states had a clear aligned in-range firing direction. The remaining enemy was
roughly(560,360), beyond tear range from the wall, with no clear shot there.

Both frozen models stayed in this later one-enemy state for64decisions and
recorded no HP drop or clear. Their start fingerprints differ from the learning
start, which had two enemies and a clear nearby target. The7-versus0 numbers
cannot be used as causal evidence that the child outperformed the parent.
Before longer training, inspect the transition after target1 disappears: remaining
enemy selection, reachable firing positions, and movement/reward feedback away
from the wall. No weights or rewards were changed in this milestone.

## Budgets, cleanup and verification

The run started at10:39:48.560 and cleanup finished at10:43:41.146,
Europe/Amsterdam. The one action lease allowed299.440seconds after integral expiry alignment;
actual startup through final cleanup took232.587seconds. Learning was bounded
by180wall seconds including model loading/optimization. Frozen phases ended at
64decisions each. All other limits were explicit: setup30s/240commands,
readiness5s/100snapshots inside setup,2048new steps,3000shared actions,
9000progress updates,1800segment updates,128MiBshared trace and2GiBall output.
Observed trace size23432632bytes; terminal output readback101701107bytes.

No cleanup errors. Release, peer disconnect, normal successful game shutdown,
observer close/unload, absent game/listener/owned approval and worker exit0 were
verified from receipts and the saved native log. No forced game kill or foreign
approval deletion. Normal gameplay save changes were not measured; no manual save
writes. Primary independently matched all1195frozen inputs before documentation
updates. Full raw evidence and failed/censored work remain local and untracked.

## OpenSpec verification

Using `openspec-verify-change` for `exposed-start-curriculum`; primary self-review,
not independent code review. Requirements/scenarios are covered by existing offline
checks and the measured native positive path. Native death/fault injection was
not tested and is not claimed. No source changed after the2416-test gate.

| Dimension | Status |
|---|---|
| Completeness | 9/9 scoped tasks complete, including task4.3; change remains unarchived |
| Correctness | Four added requirements implemented; setup separation, bounded execution, native learner damage, real updates and reload independently verified |
| Coherence | Exact parent/child lineage, unchanged policy/reward contracts, fixed caps and observational frozen phases match the design |

No critical issue remains for this scoped positive-path qualification. General
model improvement, robust navigation/combat, native injected-fault coverage,
paired/multi-seed evaluation, longer stages and Dead God remain unverified.
Do not promote t27904 as a better model or start another run from this closed lease.
