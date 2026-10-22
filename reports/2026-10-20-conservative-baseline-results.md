# Evidence: independent conservative-v2 five-death baseline

- Date/time: 2026-10-20, Europe/Amsterdam; native session19:40:49, stopped19:45:29.
- Revision: 00ca10deebb11a9d3ce7c10d86c8de0ea746902a plus the declared config/plan.
- Plan: [pre-execution lineage and budget](2026-10-20-conservative-baseline-plan.md).
- Native Windows, Python3.12.14, Repentance+1.9.7.17.J460, observer0.5.0-dev,
  Lua5.3, no extender; torch2.14.1+cpu, RecurrentPPO.
- Config hash92969b7fcfa3990ef5a8612dd7905437c4a9a46149e64dc7d912cb408f7f2da8;
  file SHA9f40e85b9f94166f12b28a6df2d7a4610e40543429e86bee860e4bf5038dbf18.
- Explicit new development lineage, seed20, reward live-conservative-v2. No weights,
  optimizer or statistics imported from legacy t8960; no failed-resume fallback.

## Verification

| Check | Command/scenario | Exit | Status | Evidence |
|---|---|---|---|---|
| Full Windows gate | `./scripts/Check.ps1` | 0 | passed | 1995 pytest tests, zero skipped/failed; Ruff/format/mypy/pip clean; OpenSpec36/36 |
| Synthetic stack | `./scripts/Smoke-RL.ps1` | 0 | passed | 16 CPU steps, save/load/predict; not game evidence |
| Finite native training | Exact plan command through frozen startup identity guard | 0 | passed | 1777 combat decisions, five natural deaths, four restarts; stop at death limit |
| Checkpoint acceptance | Primary read-only model/manifest/normalizer analysis | 0 | passed | Six checkpoints, intact parent chain, consistent step/config/reward/seed metadata, updated tensors |
| Cleanup and preservation | Primary raw native log/process/listener/hash readback | 0 | passed | Normal game shutdown, approval absent, observer unchanged, legacy t8960 unchanged |
| User's revival enemy | Encounter-dependent phase coverage | — | not_run | Revised diagnostic run did not encounter a champion/revival phase |

The worker ran the prepared helper once; no recovery or budget renewal.
Helper SHA1b4d9243d362f50ed2099afb0bf4125462a7cda8ea2f2f3b2b7d0c553d456d36;
startup guard SHA1974a8185551a1f9c4f8aa466f994d70b252a23fd1ef0076609e7e466cc95615.
The guard consumed validated snapshots without commands and required active Isaac
before constructing the learner. CLI arguments match the plan; the child imports
the existing CLI through this local guard rather than `-m`. No production learner
code was modified. All55 frozen source/config/helper hashes matched afterward.

## Native identity and complete outcomes

Steam/local menu-only input verified fresh `[New,2]`, initial character0,
session8a921c4775d8441eb53c2cf2e3f87d19,epoch1/frame0. Gameplay used the structured
bridge. Native seeds for all five runs: L39H4K6Y, BJC28DZP, C66JAFAS, SCJ7N4Z2,
YM92ZSQZ. Four native restart confirmations establish epochs1→2→3→4→5;
no fifth restart or sixth run. Ordinary authorized file2, not an isolated profile;
normal game save/Cloud writes occurred without manual save or Cloud edits.

All combat segments, including failures and nonterminal software boundaries:

| Handoff | Outcome | Decisions | Return |
|---|---|---:|---:|
| 1 | unknown/software time boundary | 548 | 6.399667 |
| 2 | unknown/software time boundary | 550 | -5.100333 |
| 3 | empty | 172 | -0.183000 |
| 4 | death | 193 | -62.422000 |
| 5 | death | 50 | -70.275000 |
| 6 | death | 82 | -66.828333 |
| 7 | empty | 67 | -29.271333 |
| 8 | death | 31 | -39.634333 |
| 9 | death | 84 | -67.486333 |

Nine accepted gate handoffs,53.499s gate wait,11 visit changes during waits;
zero recorded faults,resume races or observation gaps. Empty eligibility is not
counted as a proven room clear or win. Exact kills remain withheld by the reward
contract; logged zero kills must not be interpreted as zero gameplay kills.

## Learning and budgets

Six saved checkpoints t256,t512,t768,t1024,t1280,t1536 under
`runs/live-conservative-v2-development-20261020/seed-20/checkpoints`.
First parent=null; subsequent parent IDs form a contiguous chain. Latest pointer
`92969b7f-s20-t1536`; every loaded model's timestep equals its manifest.
PPO update counter4→24 across these checkpoints; all20 policy state tensors changed
between first and last. This demonstrates updates, not improved gameplay.
Observation normalization count257.0001→1537.0001; final return count1536.0001.

Of1777 decisions,1536 were checkpointed and241 in the interrupted final rollout
were not saved. The fifth-death stop prevented another rollout/reset. Resume must
use saved t1536, not claim1777 trained steps. Final model SHA
bcd4e015950a8653b4e49a43130ac0a8c408c4181d5565df9a7a66088a890a12;
normalizer SHAd00f947474ab10dfa9b71f99d272b1e633e8b25bb0b8425b1cc6937651f8fcef.

Elapsed282.88s, approximately61.4MB assigned output within512MiB;
test temp grew1482B within its separate512MiB cap. Approval18min/max_restarts4
fit the recorded outer deadline; it was not renewed. Runtime/wrapper exit0,
no cleanup errors. Primary verified normal native shutdown, absent process and
port9528 listener, exact approval removal, default-off installed/source equality,
and unchanged legacy model/manifest/normalizer/latest hashes.

Ignored receipts: reports/local/conservative-{check,smoke}*.txt/json,
conservative-temp-accounting.json, conservative-baseline/{plan,result,
acceptance-analysis}.json, menu.jsonl, game-log.txt. Complete session:
`runs/live-conservative-v2-development-20261020/sessions/20261020-194049-41c27a`.

## Primary self-review and continuation

The configuration, experiment plan and observed behavior agree: explicit new
lineage, preserved legacy history, five-death ceiling, four restarts, finite
budgets, conservative reward and separate oracle logs. Existing OpenSpec reward,
gated-training and restart requirements remain unchanged; all36 strict items pass.
This is primary self-review, not independent review. No change is archived.

This single-seed integration baseline is not held-out evaluation. No completion
rate, multi-seed comparison or improved play is established; the revival/champion
scenario remains pending. Future work: ship the finite startup/training/cleanup
wrapper, resume this exact t1536 lineage under a newly recorded budget, and retain
the current4096-step experiment ceiling. Extending beyond that configuration cap
requires an explicit versioned continuation/configuration plan.
