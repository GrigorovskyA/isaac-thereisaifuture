# Evidence: paired frozen combat audit

- Date:2026-10-20,Europe/Amsterdam;native follow-up approximately20:45–20:47.
- Base revision:2bdfacc3389a9efcea82887ec4c68e2a42b4e9cd plus reviewed diagnostics.
- [Predeclared plan and amendments](2026-10-20-paired-combat-audit-plan.md).
- Windows/Python3.12.14,Repentance+1.9.7.17.J460,observer0.5.0-dev,Lua5.3,
  RecurrentPPO/torch2.14.1+cpu. No training/model/normalizer writes.
- Scope:identical-input decision proxies and a mixed-control native diagnostic;
  not matched encounters,checkpoint selection or a gameplay ranking.

## Checks and retained failed attempts

| Check/attempt | Command/scenario | Exit | Status | Evidence |
|---|---|---|---|---|
| Pure diagnostic tests | pytest test_combat_diagnostics.py | 0 | passed | 16 tests,shape/action/sign/missing/clipped/zero-target/HP invariance |
| Targeted frozen stack | pytest test_combat_diagnostics.py test_checkpoint_policy.py test_live_evaluation.py | 0 | passed | 120 tests |
| Initial full gate | Check.ps1 without assigned per-process environment | 1 | failed | Worker lost environment;Lua cases incompletely loaded,pytest WinError5 cleanup;no game launch |
| Corrected full gate | Run-PairedGate.ps1 sets environment then Check.ps1 | 0 | passed | 2011 tests,zero skipped;Ruff/format/mypy/pip and OpenSpec37/37 |
| First native attempt | Guarded Continue,automatic focus | 1 | blocked | Foreground refused at intro;no combat decisions;normal close/approval cleanup |
| Human-focus follow-up | One prepared launch,10s click grace,unchanged guards | 0 | passed | Continue2/Isaac,six windows,657 decisions,129.63s,no faults/deaths |
| Identical-input replay | analyze_paired_focus.py | 0 | passed | All657 stored action triplets and proxy results reproduced exactly |
| Immutability/cleanup | Primary hashes/fingerprints/native readback | 0 | passed | 147 frozen files,model/normalizer state,old latest pointers unchanged;game/listener/approval absent |
| Actual revival scenario | Encounter-dependent coverage | — | not_run | Sampled Gushers,not Globin/revival;prior phase change remains6/7 |

Each failed attempt stopped before any new attempt was prepared. Amendments
retain failure evidence and do not weaken checks. No Windows protection/focus
guard was bypassed. The user clicked the game window for the successful follow-up;
menu focus was assisted,gameplay control remained entirely structured.
RL synthetic stack smoke was not repeated:new code is a pure diagnostic and the
targeted/full tests exercised the existing real synthetic checkpoint round trip.

## Native identity and limits

One Steam launch with existing options,seven guarded menu keys,verified Continue
on ordinary authorized file2. Initial active Isaac(type0),session
df3f9373934143efbe6f01e03c452b47,epoch1,room visit0;phase sample began at8288.
No game-state restoration,seeds,Cloud/launch-option edits,third-party mod changes
or screenshots. Existing installed mods/profile retained;not an isolation claim.

Focused assignment cap420s,controller240s,approval360s/max_restarts5,768attempted
decisions,six-death ceiling,maxfaults0,no retries. Actual129.63s,six scheduled
windows,657 decisions,zero deaths/restarts/faults. One software time boundary,
not a clear/death,ended the fourth window early. Remaining windows still ran in
the declared order;no extra111 decisions were invented to fill that window.
The local result's stop label `step_cap` denotes exhausted window schedule here,
not reaching768. Output approximately5.1MB within256MiB;offline temp stayed within
512MiB growth allowance. No leases renewed or uncontrolled repetition occurred.

| Window | Executed controller | Decisions | Completed episode outcome |
|---|---|---:|---|
| 0 | t1536 | 128 | none |
| 1 | t6912 | 128 | none |
| 2 | random | 128 | none |
| 3 | random | 17 | unknown/software truncation |
| 4 | t6912 | 128 | none |
| 5 | t1536 | 128 | none |

Both learned policies used existing deterministic inference;random seed2020.
All policies observed identical vectors/history at every decision,recurrent
states reset at windows/episode boundaries.657/657 latest snapshots re-encoded
exactly to the supplied policy vectors. Only the scheduled policy controlled the
game;shadow predictions have no attributed damage,hits,clears or survival result.
Control inherits earlier windows' positions/state,so even counterbalanced order
does not create matched gameplay trials. Inputs are autocorrelated,not657
independent encounters;no statistical significance or win-rate claim is made.

## Same-input geometric decision comparison

Proxy:shoot within45degrees of the nearest encoded enemy;no-shoot counts false.
All657 inputs had unclipped/nonzero target geometry. It ignores obstacles,line
of sight,range,tear travel and enemy vulnerability;it is not hit accuracy.

| Shadow policy | Coarse alignment | Fraction | Shooting inputs |
|---|---:|---:|---:|
| t1536 | 5/657 | 0.76% | 586 |
| t6912 | 244/657 | 37.14% | 633 |
| random | 143/657 | 21.77% | 535 |

Old and new full actions disagreed on657/657 shared inputs. The newer checkpoint
shows a better direction proxy on this captured trajectory,but useful combat
improvement remains unproven. t1536 chose shoot-right581 times and no-shoot71;
t6912 chose right321,left244,up68,no-shoot24. It never chose shoot-down here.
These are deterministic shadow decisions,not the stochastic training distribution.

## Phase,damage and position findings

Raw oracle membership contained eight enemies,total sampled HP90 throughout.
There were no sampled HP increases/decreases and no credited enemy-damage events.
Sixteen spawn labels reflect two software episode baselines,not16 native enemies;
phase labels establish eight lifetimes. No sampled evidence of healing/damage
credit suppression occurred in this audit. Sparse samples cannot prove absence
of every intervening hit;no engine hit callback was installed.

Phase journal:24 state records,type11/variant0 (installed enum ENTITY_GUSHER=11;
ENTITY_GLOBIN=24). Seven ordinary enemies,one champion-color-index2;the raw
index is retained without guessing a color mechanic. Invisible load states were
correctly absent from policy export while present in oracle data. All sampled
visible vulnerable states were in both exports. No sampled revival/Globin or
vulnerable target missing from both exports;the original scenario remains pending.

Native accepted-action x positions ranged990.09..1090.00. Encoded absolute x
was at its clipping boundary on648/657 inputs. Nearest encoded enemy distance
was349.77..597.30,median468.11. This points to positioning/approach and possible
range/obstacle issues to investigate,not an established range limit or collision
diagnosis. Relative target geometry remained available on every input despite
absolute-player-coordinate clipping. Changing observation scaling would require
a versioned compatibility plan,not silently altering existing checkpoint inputs.

## Offline synthetic sensitivity probe

Independent synthetic smoke:24 one-enemy cases (eight directions,three distances),
16 repeated frames/case,384 paired inputs,reset recurrent state between cases.
t1536 always chose(move-right,shoot-right);t6912 always chose(move-left,shoot-right).
Both coarse scores144/384 versus random116/384;these numbers are not native
performance evidence. Mean normalized shooting entropy was0.99694 and0.99778
(uniform=1);mean per-action probabilities were roughly18–23%. High stochastic
entropy on these synthetic cases is consistent with random-looking training
actions,but missing real-room obstacles/build diversity may put the probe outside
the training distribution. Do not generalize it into a global policy ranking.

## Integrity,self-review and next action

Before/after in-memory model/normalizer fingerprints matched for both policies;
primary independently replayed all657 decisions and rechecked147 frozen files,
source/default installed bytes,normal shutdown,port9528 and approval absence.
Default source4190fca03ddee98380eef6e75d16fc5bffb7e480eeacce434202e29c434a2e25
was restored while closed. All learned checkpoints/latest pointers stayed intact;
current training continuation remains08e0d262-s20-t6912.

OpenSpec verification(primary self-review,not independent):completeness4/4 tasks,
both requirements implemented;correctness5/5 scenarios covered by behavioral
tests,exact replay and native stop/cleanup evidence;coherence follows pure proxy,
frozen adapters,separate oracle files and explicit counterfactual limitations.
No critical issues/warnings found within this scoped diagnostic. No archive.

Next:measure effective firing range/obstacle paths and model approach behavior,
then evaluate on several comparable naturally reached combats before increasing
training budgets or changing reward. A direction proxy improvement is a useful
signal,not a completed-combat learning claim. Preserve t6912 and the original
revival-phase acceptance gap.

Ignored local evidence:paired-{targeted,check,check-fixed}*.txt/json,
paired-combat-native/ (failed focus),paired-combat-focus/{result,analysis,
position-analysis}.json/phase-lines.txt/game-log.txt,paired-focus-restore.json,
paired-synthetic-probe.json. Policy-only decisions and separate oracle captures
are under runs/paired-combat-focus-20261020. Raw local data/checkpoints/approvals
are excluded from publication.
