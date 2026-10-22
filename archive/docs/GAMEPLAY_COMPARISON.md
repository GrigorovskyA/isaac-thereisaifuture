# Comparable gameplay evaluation

Readiness item 4 has an offline analyzer, not accepted native comparison evidence.
Run it on explicitly declared normalized raw traces:

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.gameplay_comparison manifest.json report.json
```

This reads local files only. It never launches Isaac, creates approvals, loads a
model, trains, resets a run or edits saves. Existing output is never overwritten.
`matched_descriptive` means submitted evidence meets the comparison contract, not
that submitted native provenance has been independently verified or play improved.
`not_comparable` retains all attempts and exact exclusion reasons without paired
deltas. Neither result emits a winner or learning claim.

## Frozen validation suite

Before collecting outcomes, freeze a versioned manifest and record its hash in
the experiment plan. Do not select cases, caps or checkpoints after viewing results.
The suite needs ordinary combat cases covering an open small room, an ordinary
obstacle room and a large room; specify the actual shape, enemy types/counts,
character, complete item/stat build signature, native game seed and room-entry
history for each. These are required declarations, not implemented seeded starts.
An export cannot truthfully mark native_start_verified until native logs and raw
starting snapshots establish these fields. A case ID alone does not match starts.

Initial protocol: validation only, at least three game seeds per scenario family,
one fixed 256-decision / 30-second cap per cell, action repeat 3 / maximum frame gap
3, ten repeats per cell and a predeclared alternating policy order. This is a
small diagnostic protocol, not the existing confirmatory 100-valid-episode gate.
Two stages can share the contract but must have separately frozen manifests.
The 256-attempt parser cap limits a single manifest; larger studies use predeclared
batches and preserve every batch, including failures, with no post-hoc selection.
A wall/step stop censors the encounter; neither counts as a gameplay death.

| Candidate | Required role |
|---|---|
| Original `08e0d262-s20-t6912` | Reference, unchanged original directory |
| Current `7d53f55f-s20-t7424` | Current learner, explicit directory |
| Future completed checkpoint | Add only when it exists; never fabricate or silently follow latest |
| Seeded random | Control with frozen source hash and declared per-cell RNG seed |
| Scripted diagnostic | Explicitly labelled hand-written positive control; never learned policy |

The original/current configuration hashes differ because of a documented budget
migration; keep both exact identities. Do not rename them into a shared config.
For every checkpoint record model/normalizer/config SHA256, ID and training seed.
For controls freeze the executed policy source/dependency identity in the experiment
receipt. Runtime fingerprint covers game/observer/mod, observation/action schemas,
action repeat and evaluator settings. Freeze the evaluator Git revision too.
Inference is deterministic for checkpoints; VecNormalize is frozen and reward
normalization is not a quality metric. Reset recurrent state exactly once at each
episode start, carry only that controller's own history, and verify hashes before
and after. Random controls use the same declared per-cell policy seed. Never mix
controllers inside an episode or attribute shadow actions to resulting damage.

These checkpoints share training seed 20. Different game seeds are not independent
training seeds. General learning claims need several trained seeds, separate
training/validation/test scenarios and the existing predeclared selection rule.
Test remains held out until final evaluation; no tuning from test reports.
Large-room coordinate clipping must be audited before an observation change.
No schema migration, reward tuning or reinterpretation of t7424 is authorized here.

## Input contract and raw provenance

`Manifest`, `PolicySpec`, `Case`, `Attempt`, `Trace`, `Sample` and `Enemy` in
`gameplay_comparison.py` are the strict version-1 JSON contract. Tests contain a
complete synthetic example. Manifest declares reference, policies, cases, repeats
and content-hashed trace paths; every policy/case/repeat cell is expected.
One split per manifest. Duplicate cells, undeclared cells, changed hashes, unsafe
paths, nonfinite values and invalid ordering refuse analysis. Missing cells block
pairing but stay visible in the report. Shared per-cell policy seeds are required.
Limits: 1 MiB manifest, 256 attempts, 8 MiB/trace, 128 MiB total, 10000 samples/trace.

A trace records native/synthetic source, source raw-log hash, evaluator/runtime
identity, actual case and policy identity, verified native start, policy-unchanged
readback, single/mixed/shadow control, assistance, exact stop/fault and samples.
The source raw-log hash is a provenance reference; the analyzer verifies the
normalized trace bytes, not an unseen raw log. Native acceptance must independently
verify raw-log bytes and every transformation. Hashes cannot prove metadata truth.

Each sample records elapsed seconds from zero, completed decisions from zero,
session/epoch/visit/frame, preceding activity phase, raw red+soul half-hearts and
player position, raw enemy ID/spawn-generation/type/position/HP/active phase,
overflow and raw clear/death flags. The analyzer also compares the actual initial
health, positions and enemy type/HP/phase across each policy/case/repeat cell;
declared matching metadata cannot override differing observed starts. Transient
clear/death flags that disagree with the final sample do not verify a terminal.
These labels are oracle-only; never feed the trace or metrics to a policy,
normalizer or reusable policy input log. Do not feed reward events into this API.
The collector must export initial and final snapshots and respect the same frozen
budget; samples are not interpolated. No native exporter/matched-start controller
is shipped by this change: existing raw logs require a separately reviewed adapter.
Do not relabel an old mixed-control audit as a matched suite.

## Metrics and denominators

Enemy damage is a conservative observed HP-loss lower bound for continuously
present active IDs/generations below their prior observed minimum. Healing,
disappearance, phase changes and frame/identity gaps create no invented damage or
kills. Final unseen killing damage is omitted. This is independent of training
reward and does not prove which projectile or controller caused an HP drop.
Player damage is the sum of observed adjacent red+soul HP decreases in half-hearts,
not net ending health or enemy-attributed damage; gaps cannot manufacture loss.
Bone-container mechanics and other unseen health channels need separate coverage.

Verified clears require an initially occupied encounter, continuous raw coverage
and observed false-to-true clear flag ending with clear. Death similarly needs
observed death and complete coverage for a known negative outcome. Empty starts,
unknown phase, overflow, gaps, mid-room budget/user stops and faults remain visible.
A fault can retain observed partial damage but never becomes a valid clear/death.
Observed death counts and infrastructure fault counts are separate.

Report every attempt and missing cell, all-observed damage totals, decisions,
seconds, phase exposure, unknowns and faults. Phase time ends at the last sample;
no duration is inferred after it. Near-wall stationary movement is explicitly null
until a reviewed positional adapter exists. Aggregate metrics are labelled
all_observed_attempts_not_causal; assisted/mixed/shadow rows cannot support policy
attribution even though their observed numbers remain visible.

Show both verified clears / all attempted episodes and verified clears / known
clear-or-death outcomes with Wilson 95% interval. Unknown/censored cases are not
known failures; an empty known denominator gives null rate and [0,1] interval.
A report with many censored episodes must not be flattered by the smaller known
population: retain the all-attempt fraction and exposures alongside it.

Only complete matched native cells with verified attribution, coverage and no
faults/user stops get per-cell candidate-minus-reference damage/clear deltas.
The signs are explicit: positive dealt and negative taken are favourable; reward
and tensor changes never enter the comparison. No significance, winner or
improvement verdict is generated. Several seeds, sample size and uncertainty must
be assessed under the frozen protocol before any broader conclusion.

## Native acceptance and next action

No actual policy-quality comparison has been run. Native normalized-trace
provenance, same-start verification, frozen inference and raw damage/clear coverage
are pending. The overnight experiment remains suspended. The next live task still
starts with a separately requested five-minute qualification; then 15-30 minutes,
one hour and only after acceptance a newly requested four-hour experiment.
