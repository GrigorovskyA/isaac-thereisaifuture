# Evidence: exposed-start-curriculum Windows review

- Date: 2026-10-22, Europe/Amsterdam.
- Reviewed revision: `0c2647d0040b914da62064a2d23f35511f64f524`, tasks 1.1-3.2
  implemented by another agent. This review includes the corrections below.
- Source/config/checkpoint identities and the one-shot assignment are frozen in
  `reports/local/exposed-start-pilot-20261022/assignment.json` (1185 inputs).
- Python 3.12.14, seed20, schema2/723, rewardlive-firing-v5,
  collectorlive-segment-refresh-v1; configuration SHA256
  `a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15`.
- Source/deployed observer is the unchanged default-off baseline; no Lua deployment.
  Native observer0.5.0-dev/Lua5.3; game build unavailable in handshake.
- Preserve unrelated `errors.txt` and `tools/`; no dependency or save edits.

## Review corrections

1. Enforce global action, phase time, cumulative health, output and shared trace
   limits at the final command boundary, including gate navigation. Queued records
   cannot bypass expiry. A later phase cannot renew the outer lease.
2. Recheck the first learner command against the actual freshest reference after
   queue draining, including health, context, target and clear firing line. Frozen
   commands recheck combat/context and stop on observed health loss.
3. Stop before reset on observed death even when health fields are nonzero.
   Opt-in reader-level shutdown cancels Lua's delayed restart while PPO is busy.
   This mechanism passed offline tests; native death/optimizer latency was not tested.
4. Retain one reader through phase client views. Unexpected connection loss refuses
   later phases; same-instance reconnect has no ownership proof and is not attempted.
5. Correct frame-derived exposure/stagnation to30updates/s; count nonoverlapping
   ten-second windows. Unsupported/incomplete shot geometry is unknown, not false.
   Include room/grid/weapon/range/enemy-position fingerprints and actual rollout
   accounting/learner decision count. All remain diagnostics outside policy input.
6. After the native refusal, add one bounded initial setup snapshot and report
   fingerprint before precheck. This improves a future refusal's evidence; it cannot
   reconstruct the missing snapshot or explain this attempt retrospectively.

## Checks

| Check | Status | Evidence |
|---|---|---|
| Focused exposed-start tests | passed:60 | local/exposed-start-review-20261022/; final full gate also includes them |
| First Windows Check.ps1 | passed:2402,0 skips;66 mypy files;56 strict items;lint/format/pip | local/exposed-start-review-20261022/full.log |
| First gate identity | passed:716/716 before and after | local/exposed-start-review-20261022/gate-hashes.json |
| Final source Windows gate after snapshot diagnostic | passed:2402,0 skips;56 strict items;717/717 hashes before/after | local/exposed-start-review-20261022/final-full.log |
| Native one-shot cap/entry/refusal/cleanup | passed scoped execution; no learning acceptance | local/exposed-start-pilot-20261022/session/result.json |
| Parent/copied child reload | passed,byte-identical;0 new optimizer updates | local/exposed-start-pilot-20261022/primary-verification.json |
| Native learner damage/real update/learned child | blocked:setup refused | task4.3 stays unchecked |

## Real game

One exact prepared `pilot.py --run`, no retry or New Run. The maximum300s shared
lease began at09:55:13.370; cleanup finished09:55:40.120 (26.750s inclusive).
Startup verified fresh file2 Continue using7guarded menu keys, ordinary Isaac,
session `59e09f6c61144602939c0dad8fe1ff41`, epoch1, frame78914.
Native precheck refused `Expected visible target unavailable or moved` before any
movement/shooting command. This is a scenario refusal, not a policy-performance
measurement. Learning, frozen parent and frozen child are all `not_run`.

Gameplay accepts0; learner steps0, saved0, unsaved0; optimizer updates0. No learner
exposure means damage dealt/taken, clears, deaths and stagnation are unmeasured;
zero-valued empty-phase fields must not be interpreted as observed zero damage.
The game log records enemy spawn at(80,200), but no structured refusal snapshot
was retained. Visibility, actual position and timing at precheck are unknown.
Do not infer a missing enemy, changed world or sole cause from the refusal text.

The one-shot assignment is consumed. No automatic retry, old-pilot resume, new
branch, New Run or longer stage is authorized by its remaining unused seconds.
The native approval schema requires max_restarts1; the pilot permits zero actual
restarts. Native log shows arming but no dispatched restart. No death was tested.

Cleanup verified release/observer disconnect, normal successful game shutdown,
observer close/unload, absent game/listener/owned approval, worker exit0 and no
cleanup errors. The1185 frozen inputs matched during cleanup. Primary later
read back1183 unchanged plus exactly2 declared post-run source/test edits for the
initial diagnostic; no unexpected changes. Raw native log and approval-owner hash
remain local. The normal game's save delta was not measured; no manual save edits.

## Checkpoints and outcome

Parent `runs/live-boundary-v5-pilot-20261021/seed-20/checkpoints/a0a93c29-s20-t26368`
and initial child under `runs/live-exposed-start-pilot-20261022` have identical
artifact bytes, manifests and policy identities. Primary loaded both model/Adam
and normalizers:26368timesteps,412optimizer updates,Adamstep1648,
normalizercount26392.0001,723inputs. Every preserved parent/ancestor pointer remains
protected. Child latest still names the copied parent; no learned checkpoint exists.
Model SHA256 `6e94cc1ffeb3280adf5881cc56e1625cbe62f400a1c1b34b173165a2f0f55d08`;
normalizer SHA256 `2d4e839015fd0e2aaafa1230e7edbece1dd28f85128d77d13c86d65609b1662c`.
These copied files are not evidence of learning or improvement.

## OpenSpec verification

Using `openspec-verify-change` for `exposed-start-curriculum`; primary self-review,
not independent code review. Four added requirements/nine scenarios were mapped
across `exposed_start.py`, `live.py`, `test_exposed_start.py`, existing collector,
checkpoint and policy tests. Source/static/offline checks support the implementation;
this native refusal verifies no successful handoff, training or frozen comparison.

| Dimension | Status |
|---|---|
| Completeness | 8/9 tasks complete (1.1-4.2);4.3 blocked |
| Correctness | 4/4 requirements have implementation/offline scenario coverage; native qualification not verified |
| Coherence | Matches setup/collector separation, exact branch, unpaired descriptive phases and fixed caps; reconnect design explicitly narrowed to refusal |

Critical:task4.3 remains incomplete. Required successful native learner handoff,
learner-attributed damage, actual optimizer update and reloadable learned child
are not verified because setup refused. Do not archive or promote a model.
Next:prepare a separate bounded no-action initial-state capture to diagnose the
precheck visibility/timing, then revise a measured setup plan if justified. A new
runtime attempt needs its own finite authority/assignment; no invented warmup,
changed target or budget renewal is included here.

Final source gate independently read back:exit0,60.780s,2402passed/0skips,
66mypy files,153formatted files,56strict items;717/717 frozen inputs matched.
Only task/status/report text changed afterward;source/tests/config stayed frozen.
Post-gate documentation uses strict validation,local-link and diff checks.
