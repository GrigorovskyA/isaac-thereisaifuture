# Evidence: fresh-rollout-observations (offline stage)

Follow-up: [native frozen-delay audit](2026-10-21-native-fresh-rollout-observations.md)
passed; final offline journal-cleanup regression passed149 targeted/2292 full tests,
51 strict items and CPU smoke. Original stage details below are retained.

- Date: 2026-10-21, Europe/Amsterdam, UTC+02:00.
- Base revision c0015e90cc3e25857b157edf23e693bcb5fa0667 plus frozen implementation diff.
- Scope: gated live collection freshness; no reward/observation schema, optimizer
  tuning, checkpoint migration, model initialization or real-game training.
- Installed Python3.12.14; stable-baselines3/sb3-contrib2.9.0, gymnasium1.4.0,
  torch2.14.1+cpu. Existing installed source was inspected at public set_env,
  learn setup, rollout-end callback, recurrent forwarding and VecNormalize.reset.
- Native game/mod versions: not applicable to the offline stage.

## Diagnosis and remedy

Saved native pilot diagnosis identified9/2506 actions with9-21 frames of actor
observation lag, each35.5-51.1ms after checkpoint completion. The backend drains
recent frames before sending a command, but the actor has already selected that
action from the old normalized cache. Sparse delays are not the sole established
cause of corner stagnation. See the
[original diagnosis](2026-10-21-firing-policy-diagnosis.md).

At completed rollout end, after bootstrap/advantages and before optimizer work,
the callback calls end_collection_segment. Strict release acknowledgement is
required; the gate blocks further step calls until reset. The event records old
session/epoch/frame, software segment steps/return and monotonic time. No fake
terminal result or transition is inserted into the completed rollout.

Before the next learn chunk (after optimizer and checkpoint work), public
model.set_env(existing_vec_normalize, force_reset=True) requests the ordinary
SB3 reset path. It reacquires eligibility/current raw state, updates normalization
once, refreshes actor and original-observation caches, and sets the episode-start
mask. Recurrent state resets through the normal policy mask, without rewriting
private SB3 cache or LSTM fields. The previous end-observation bootstrap is kept.

Gate collection_refreshed logs old/new frame identities and idle duration with
coverage=unknown_idle_gap_no_transition_or_outcome. Physical-room novelty/damage
identity and no-progress histories survive resets. The gap adds no action/reward,
step, death or clear. The contract live-segment-refresh-v1 is explicitly logged.
Generic/synthetic training defaults stay unchanged; gated live training enables it.
See [collection contract](../docs/COLLECTION_FRESHNESS.md).

## Checks and evidence

One fresh gpt-6-luna/high script worker executed one exact prepared runner, no
retries, source edits, native actions or actual learning. Its fixed absolute
stop was1792605107.069 Unix, start cutoff1792604387.069, disk cap2GiB. Exact command:

```powershell
& D:\isaac\reports\local\fresh-rollout-check-01\run.ps1
```

Helper SHA25691a769a5011e6505895d5a51a52edfd597e125269dc990190f9e1cdc81856f58;
649-input manifest SHA256fb79b067a672a8c23e9d1dabbb021ca20c9a47286f881760f1280f39dfa8bec8.

| Check | Exit | Status | Evidence |
| --- | --- | --- | --- |
| Targeted behavioral suites | 0 | passed | 148 tests, no failures/skips |
| Full Check.ps1 | 0 | passed | 2291 tests, no failures/skips; lint/format/mypy62 files/pip consistency passed |
| Strict OpenSpec | 0 | passed | 51 items; repeated change validation after task edits |
| Smoke-RL | 0 | passed | 16 synthetic CPU steps; Isaac integration explicitly false |
| Primary frozen readback | 0 | passed | All649 hashes unchanged, protected t21760/t24064 included |
| Native boundary audit | n/a | not_run | Separate finite frozen-delay check pending at this stage |
| Live optimizer/play improvement | n/a | not_run | No native training or model change |

Logs/results are local under reports/local/fresh-rollout-check-01, including
primary-verification.json. Primary read saved counts/result/smoke and independently
rehashed all frozen inputs. Output191742886 bytes, below2GiB. Environment variables
PYTEST_ADDOPTS/PYTHONPATH/ISAAC_JSON_LUA restored; no game or approval created.

The actual PPO/RecurrentPPO tests run two32-step rollouts with a simulated21-frame
optimizer gap. Both verify actual actor input equals stored normalized buffer
input, fresh raw/original caches,66.0001 observation RMS count (64 steps plus2
resets plus initial epsilon), unchanged64 cumulative samples and next-rollout
start mask. Recurrent forwarding with carried state and reset mask matches zero
state. Defaults retain one reset and no segment events. A real gate-stack test
changes HP10->3 during a gap: no idle damage credit, no fabricated transition,
no changed outcome/step/progress counters; the next trace starts at the fresh frame.
Rejected release and expired refresh cannot send a fallback action.

## Primary self-review

Using openspec-verify-change for fresh-rollout-observations; primary self-review,
not independent review.

| Dimension | Assessment |
| --- | --- |
| Completeness | Offline tasks1.1-1.3 complete; native2.1 pending; unarchived |
| Correctness | Both added requirements and all3 scenario groups covered offline; native not yet verified |
| Coherence | Public SB3 reset/callback path, unchanged default/schema/reward contracts; no cache mutation |

Mapping: rollout_refresh.py releases via rollout-end callback; training.py controls
refresh across learn chunks; live.py enables only gated live training;
combat_gate.py records and reopens software segments; test_rollout_refresh.py
covers actual algorithms and simulated live frames/failures. No known offline
implementation issue remains. Native task2.1 is incomplete acceptance, not a pass.

Intentional limits: software segment resets bound recurrent memory to a rollout;
ungated live and within-rollout inference delays remain outside the remedy.
Unobserved idle outcomes remain unknown. Synthetic optimization verifies accounting,
not installed-game dynamics. Preserve original v2t21760 and v3t24064.

Next:one finite frozen-policy native audit with three explicit idle gaps and the
same gate boundary method, no optimizer, no New Run. Compare captured fresh actor
frame with accepted command and verify release/cleanup and artifact hashes. A
real training comparison and compatible schema2 lineage require their own plan;
no automatic duration escalation is authorized here.
