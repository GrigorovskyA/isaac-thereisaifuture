# Evidence: firing-position-shaping

- Date/time:2026-10-21, Europe/Amsterdam.
- Tested revision:330c86363c5053d1839217e39137a4fa0926fc4b plus frozen working diff.
- Scope:default-off firing-position reward and negotiated reward-only geometry;
  no training, deployment, model migration or native acceptance in this report.
- Python3.12, pinned project environment; synthetic smoke torch2.14.1+cpu, no CUDA.
- One fresh gpt-6-luna/high script worker per assignment, no source writes or Git
  authority. Primary implemented and accepted results after reading saved logs.
- Final offline assignment:10.5minute absolute wall allowance,2GiB artifact cap,
  zero game actions, no retries. Existing Lua5.3 harness and installed game json.lua;
  isolated pytest temp directory. No dependency installation.

## Results

| Check | Command/scenario | Exit | Status | Evidence |
|---|---|---|---|---|
| Initial targeted checks | Prepared check-01 script |0|passed|191 tests, zero skips |
| Initial full gate | Check.ps1 through check-01 |1|failed|2265 passed,1 failed: Windows concurrent latest.txt read raised CRT errno13 without winerror |
| Targeted final checks | Prepared check-02 script |0|passed|194 tests, zero skips,10.66s |
| Full final gate | scripts/Check.ps1 through check-02 |0|passed|2269 tests, zero skips,50.92s; lint/format, mypy58 files, pip consistency |
| OpenSpec | Full gate strict validation |0|passed|49/49 items |
| RL smoke | scripts/Smoke-RL.ps1 through check-02 |0|passed|16 synthetic CPU steps, save/reload; native integration false |
| Primary input verification | Rehash frozen assignment inputs |0|passed|387 inputs, zero mismatches; saved exit codes/logs read independently |
| Native weapon/range/clearance | Separate finite audit |n/a|not_run|No new native run in this report |
| Gameplay improvement | Comparable training/evaluation |n/a|not_run|No new model or learning |

Local artifacts:reports/local/firing-shaping-check-01 and firing-shaping-check-02.
Exact final entry command:
`& D:\isaac\reports\local\firing-shaping-check-02\run.ps1`.
Helper SHA256:E2B0E032EDD5E365C4C4DA49EE54F7ED618D48C92446B2D6F74F4BDF2EA2E98B.
Input manifest SHA256:7EA8F8D0A88782EF4D6FBF1AD105A1A55AF1636D929E42F237885B2E3713144C.
Final result.json records targeted/full/smoke exit0; primary-verification.json
records the387 hashes. Raw local logs are excluded from publication.

## Implementation and requirement mapping

`firing_position.py` validates versioned bounded evidence and computes a bounded
cardinal BFS distance to positively witnessed firing cells. It independently
checks range, alignment, standoff and walking validity. `FiringProgress` retains
room high-water records across resets/reentry, caps credit at0.25, rejects replay
and exhausted history, and pays only for actual movement. Both positions use the
same target geometry and intersection of positively checked cells. Moving target
alone, idle shots, wall pressure and oscillation cannot renew credit.

`mod/observer/main.lua` exports geometry only after negotiation and feature detects
HasWeaponType, ordinary TearFlags, TearRange and CheckLine(mode3). It makes at most
32 projectile-line queries per sample. Special weapons/flags or missing APIs do
not invent useful geometry. `observer_client.py` and `LiveSnapshot` validate
negotiation and visible target identity/position at the boundary.

`firing_reward.py` wraps real combat inside the gate, adds a named reward component
and includes it in episode returns. Management navigation cannot earn it. Existing
combat coefficients and conservative event coverage remain unchanged. Geometry
does not enter the649-element encoder, normalizer or policy info.

`live.py`, `cli.py` and checkpoint contracts make live-firing-v3 explicit and refuse
an old-contract training checkpoint before environment creation. Frozen policy
identity records its original reward contract. No migration is included.

Behavioral tests in test_firing_position.py cover valid/blocked/no-path/range cases,
standing/shooting/tiny drift, resets/reentry, target/grid changes, replay/history
bounds, unchanged encoding, wrapper accounting and early legacy refusal. The Lua
harness covers opt-in, unsupported/unavailable weapons, blocked lines, invulnerable
targets and the query cap. These scenarios support offline requirements only.

The initial full-gate failure was investigated, not suppressed. On native Windows,
CRT can expose a sharing denial as errno.EACCES without winerror. Checkpoint pointer
reads now retry that classified case within the existing1second/10ms bound, as
well as WinError5/32/33. Persistent denial still fails. Arbitrary permission errors
and non-Windows EACCES do not get this fallback. Regression tests cover transient,
persistent and non-Windows cases; storage design/spec were updated explicitly.

## Self-review and OpenSpec verification

Using openspec-verify-change for firing-position-shaping, primary self-review;
this is not independent review. Planning artifacts, implementation, scenarios and
the final checked diff were inspected.

| Dimension | Assessment |
|---|---|
| Completeness | Implementation1.1-1.3 accepted; native2.1 and learning2.2 incomplete |
| Correctness | All three added requirements mapped to code/behavioral tests; native API meaning and gameplay effects not verified |
| Coherence | Matches reward-only schema1 design, bounded work, explicit v3 compatibility and conservative progress guard |

Critical incomplete tasks:2.1 requires a finite native weapon/range/clearance audit;
2.2 requires a declared compatible lineage and actual damage/taken/clear comparison
at5min then15-30min. Do not archive until required acceptance is complete.
Warning:collector-local novelty history is not persisted across external process
restart. Record that discontinuity before any resumed v3 experiment; do not claim
exact shaping-state restoration. No other source/spec mismatch was found in this
self-review. No applicable offline checks skipped; native/learning remain not_run.

## Real game and continuation

No game control, deployment, save changes or model updates occurred in these checks.
t21760 and its model/normalizer parents are preserved. Native geometry qualification
is next, with frozen deterministic inference, shadow reward, file2/Continue only,
finite time/disk/progress guards and owned cleanup. No New Run or automatic learner
resume follows from offline publication. No claim of improved play is made.

API references establish intended semantics only, not installed-game acceptance:
[EntityPlayer.HasWeaponType and TearRange](https://wofsauge.github.io/IsaacDocs/rep/EntityPlayer.html),
[Room.CheckLine](https://wofsauge.github.io/IsaacDocs/rep/Room.html#checkline),
[WeaponType](https://wofsauge.github.io/IsaacDocs/rep/enums/WeaponType.html),
[BitSet128 equality](https://wofsauge.github.io/IsaacDocs/rep/BitSet128.html#__eq).
