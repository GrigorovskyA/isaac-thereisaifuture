# Evidence: coherent-combat-geometry

Historical offline implementation receipt. Subsequent ordinary-tear native
qualification passed; see [native follow-up](2026-10-21-native-coherent-combat-geometry.md).
The limitations and pending items below describe this original offline stage.

- Date: 2026-10-21, Europe/Amsterdam (UTC+02:00).
- Base revision: e87380df1f6444d4df80f92ff727803249f0e6d8, with the declared implementation diff.
- Scope: offline corrective reward and opt-in visible geometry. No game deployment,
  model initialization/migration, native input, or learning experiment.
- Python: 3.12.14, existing project environment and pinned dependencies.
- Game/mod versions: not applicable to this offline run. Production Lua was loaded
  through the existing Lua 5.3 harness and installed json.lua; this is simulated API evidence.
- Checks: one gpt-6-luna/high script worker at a time, primary implementation and
  acceptance. Each receipt has an absolute deadline, 2 GiB disk cap, zero retries,
  zero native actions/deaths/restarts, isolated pytest artifacts and restored environment.

## Delivered behavior

`--firing-position-reward` now selects `live-firing-v4`. A bounded multi-source
BFS and bilinear graph-distance field remove the old mandatory cell-center detour.
An open-row retreat no longer earns credit; approach monotonically improves across
cell boundaries. All required interpolation corners must be measured reachable.
Unknown support yields no shaping, never an invented distance. This is a
conservative graph field, not an exact continuous shortest-path solver.

High-water records are per physical-room/visible-target identity. Different targets
share one persistent room allowance of at most 0.25; switching, reentry, software
reset, repeated approach, and standing cannot renew credit. History limits fail
without eviction. Legacy v3 functions retain their historical meaning for replay.

`--combat-geometry` independently selects observation schema 2. The unchanged
649-element prefix is extended by 74 features: own ordinary-tear range, four
masked 40-unit ground probes and masked projectile clearance/range/alignment for
visible enemy slots. This is a negotiated top-level field, separate from oracle.
It contains no hidden HP, target goals, navigation grids or hidden enemies.

Lua adds at most four ground plus twelve visible-enemy line queries per capture,
and none with the feature off. Missing/failed/nonboolean API results are unknown;
flight does not receive a guessed ground-path guarantee. Ground mode 0 and
projectile mode 3 are based on [Room.CheckLine documentation](https://wofsauge.github.io/IsaacDocs/rep/Room.html#checkline),
not newly verified installed-game semantics. The existing source obstacle cap is
still 12. See [feature layout](../docs/COMBAT_GEOMETRY.md).

Training, saved normalizers, diagnostics and frozen inference use explicit schema
sizes. Resume rejects old schema/contract before environment creation. A synthetic
723-input test trains 32 steps, saves, loads frozen inference, rejects a 649-vector,
then resumes to 64. That tests persistence plumbing, not gameplay learning. There
is no automatic conversion of t21760 or t24064 and no fresh-model resume fallback.

## Check history

| Run | Result | Subsequent phases |
| --- | --- | --- |
| check-01 | 203 passed, 4 failed | Full gate and smoke not_run |
| check-02 | 205 passed, 2 failed | Full gate and smoke not_run |
| check-03 | Targeted 207 passed; full 2281 passed, 1 failed | Smoke not_run |
| check-04 | Targeted 261 passed; full 2285 passed, 0 failed/skipped | 50 OpenSpec items passed; CPU smoke 16 steps passed |

The first failures identified two test-fixture mistakes and missing Lua snapshot
geometry emission. The second exposed use of data.frame_id instead of data.frame.
Both production wire defects were fixed. The third identified changed wording in
an existing unsupported-schema rejection; the loader now preserves the field name
in its error. No failed check was counted as passing or bypassed.

Exact final runner: `& D:\isaac\reports\local\coherent-geometry-check-04\run.ps1`.
It runs the targeted geometry/firing/live/observer/checkpoint suites, then
`./scripts/Check.ps1`, then `./scripts/Smoke-RL.ps1` only after prior success.
The full gate includes lint, format, mypy, offline pytest, pip consistency and all
strict OpenSpec validation. Local receipt/logs are under
`reports/local/coherent-geometry-check-04/`; raw logs and synthetic artifacts are
excluded from Git. No test skips were reported. Lint, format, mypy (61 source files), pip consistency
and strict validation all passed. The helper SHA256 is
`562dc7efc07f0105e68a893fa225e8c11976e33a4f77646c25c5a34db9f82fd9`;
its 641-input manifest SHA256 is
`4e54c7858e2f095a5d1da8d84b6d7416d3eaf211f23d086b367d8ef678c4ad2e`.
Primary final frozen-input verification passed: all 641 hashes matched after the
worker exited, including both protected checkpoint triplets. Result and full/smoke
logs were read directly; worker assertions were not the sole acceptance evidence.

## Saved-trace counterfactual

Primary replay validated all 2506 before/after LiveSnapshot pairs from the closed
pilot, retaining five explicit continuity rebaselines and one ledger across them.
No geometry observation was invented from oracle data. Local result:
`reports/local/coherent-geometry-replay-20261021.json`.

| Metric | Historical v3 | Corrected v4 |
| --- | --- | --- |
| Positive movement bonuses | 17 | 14 |
| Total novelty reward | 0.11115502123989211 | 0.04758647837209194 |
| Bonus across 1786 stationary pairs | 0 | 0 |

The legacy total matches the original replay exactly. V4 stores two target records
and pays at most 0.047586478 in the one physical room. Crucially, **2465/2506
endpoints lack complete interpolation support** on this corner-heavy trajectory.
That is a major availability limitation, not evidence of useful new incentives
near the corner. The fix removes a proven sign error but is not sufficient proof
that the character will escape or learn to fight. Visible geometry is intended to
make blockers/range distinguishable to a future compatible policy; learning to use
those features has not happened.

## Preservation and primary self-review

The frozen manifest includes source/config/tests/specs and both protected checkpoint
triplets (manifest, model, normalizer). Original model/normalizer SHA256 values:

| Checkpoint | Model | Normalizer |
| --- | --- | --- |
| v2 t21760 | 045f96ac5ae34c3d5db7584f3642dc5ed823fa4496d838ee416994fa6e64fca2 | ca30e667a81cee27faac5e6229fb2e7d02f13d77596b02896be272b7788b06f7 |
| v3 t24064 | a8fb6c500fd1ab356c323edf602b542b4ae0ccf2d466f336c2b252d31f67775d | 0ba0c288b68400a272c05e73fb010f8116a62cbd9441ad47f0855d100b49dcb6 |

Primary reviewed the implementation against proposal, design and delta scenarios.
This is self-review, not independent review.

| Dimension | Assessment |
| --- | --- |
| Completeness | 3/4 tasks complete; native task 2.1 incomplete |
| Correctness | 2/2 added requirements implemented; 4/4 scenario groups covered offline; native API/behavior not verified |
| Coherence | Default schema1, immutable legacy replay, opt-in schema2 and oracle separation follow design |

Implementation mapping: `firing_progress_v4.py` covers sign, support, target records
and cap; `policy_geometry.py` and `geometry_env.py` cover visible encoding;
`mod/observer/main.lua` covers negotiation/capture; `live.py`, `training.py`,
`checkpoints.py` and `checkpoint_policy.py` cover schema integration and refusal.
Behavioral coverage lives in `tests/test_coherent_geometry.py` and
`tests/test_lua_policy_geometry.py`, with existing legacy regressions retained.

Critical incomplete acceptance item before archive: task 2.1 needs a separately declared finite native
qualification. Warning: interpolation support is sparse near blocked corners.
Warning: optimizer-associated observation/action delay is still unresolved and
was not changed by this work. Collector-local reward history is not serialized
into checkpoints; process restarts remain declared trajectory discontinuities.
No source implementation issue remains known after the recorded offline checks;
this does not clear the native acceptance issue. The change remains unarchived.

## Continuation

First qualify the visible geometry, frame freshness, corrected shadow reward,
query bounds, and cleanup without learning in a finite native check. Then address
observation freshness and declare an explicit compatible-lineage plan before any
five-minute learning comparison. Compare damage dealt, damage taken and verified
clears under comparable scenarios; reward magnitude or changed weights are not
success metrics. No automatic 15-30 minute, hour, four-hour, resume or New Run
escalation is authorized here.
