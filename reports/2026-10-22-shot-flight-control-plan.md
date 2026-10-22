# Shot-flight positive-control preparation

Date: 2026-10-22, Europe/Amsterdam. Base: a929752.
Status: explicitly authorized and executed once;closed,no remaining budget.
See [execution evidence](2026-10-22-shot-flight-control-results.md);damage remains unqualified.
The previous 180-second/200-command experiment is closed and grants no retry.

## Evidence and purpose

The previous control accepted three left-shoot commands at frames 77068, 77070
and 77071, then stopped at frame 77072 on the first player half-heart loss.
Only four game frames separate the first accepted shot and the last endpoint.
There is no recorded tear trajectory. The target approximately 200 world units
away retained HP10 at observed endpoints. These facts establish neither a hit
nor a broken firing pipeline. See [the audit](2026-10-21-shot-selection-results.md).

Prepare a new scripted control, not model evaluation or training. Use Continue
on file2 with ordinary Isaac, expected room83 and door start within20 units of
(560,280). Stop if Continue or this compatible state is unavailable. No New Run,
death restart, save/Cloud edit, optimizer or checkpoint write is included.

## Finite proposed experiment

- One invocation,180 seconds including startup;320 completed one-update commands,
  at most90 guarded shooting commands;1GiB output and32MiB paired trace.
- Zero retries, infrastructure faults, death restarts or budget renewals.
- Preserve checkpoint a0a93c29-s20-t26368,seed20,schema2/723,reward live-firing-v5,
  its model/normalizer/manifests/pointers and all preserved v2/v3/v4 ancestors.
- Move first to(560,200), then(320,200), settle and align, then shoot left only
  while the same visible target near(80,200) has measured clear/in-range evidence
  with transverse error<=8. Keep the original fixed target/context/grid guards.
- Ten route-center checks passed on the saved grid. This does not establish a
  safe current route or projectile avoidance; revalidate the current grid before
  movement. The route avoids the former central crossing, but safety is unproved.
- Stop on first observed target HP drop, first player health loss, death/clear,
  target/context/grid/weapon mismatch, missing evidence or any bound. More firing
  capacity does not relax the health stop or promise sufficient flight coverage.

## Diagnostic deployment and restoration

Only after authorization, absent game and baseline hash checks, back up the exact
installed first-party observer and enable its existing local-only
`tear_diagnostics` switch. No new Lua behavior or wire/policy/reward fields.
The prepared variant changes exactly one literal false to true. Existing bounds
remain120 seconds,1024 records,64 tear labels,100ms sampling and900 bytes/line;
stop/exhaustion/truncation must be reported. Do not enable other diagnostics.

Record baseline/diagnostic/deployed hashes and the fresh finite assignment before
launch. The candidate helper requires a matching deployment receipt. Freeze the
final revision and source/config/deployment/checkpoint inputs, then use Steam,
fresh guarded file2/Continue evidence and bridge-only gameplay. No cached menus.

Release input, close observer and owned game normally, confirm process/listener
absence, remove only the unchanged owned approval, then restore the exact backup
only if the installed diagnostic hash still matches. Verify restored hash and
unchanged ancestors. A restoration failure is a fault, not successful cleanup.

## Required readback and acceptance

Join every selected command to its native accept and actual endpoint identity.
Report observed target HP delta, player half-heart loss, clears/deaths, all caps,
faults and coverage. Join tear samples by session/epoch/visit/frame; retain sampled
position/velocity and disappearance uncertainty. A first sampled tear is not its
exact birth time;100ms sampling does not establish exact firing cadence or all
collisions. A target-center line is not tear-radius or vulnerability evidence.

Positive damage qualification requires an actual observed target HP decrease,
with adequate provenance. Tear samples alone are not hits. Scripted damage is
not learned improvement. If health/state/logging bounds prevent qualification,
leave OpenSpec task3 unchecked; do not repeat or train automatically.

## Prepared artifacts and checks

Ignored preparation folder: `reports/local/shot-flight-control-20261022/`.
`diagnostic-candidate.py` derives from the reviewed ownership harness, with the
new route/caps, persisted shoot count, truthful scripted status and deployment
receipt guard. `main.tear-diagnostic.lua` is local-only and not installed.
`preparation.json` records hashes, ten historical route checks and syntax parsing.
No approval, finite assignment, deployment, game launch or training occurred.
The final helper revision/hash and absolute deadlines must be frozen after this
documentation milestone, immediately before an authorized execution.

The preceding preparation statements describe the pre-authorization milestone.
Execution used a fresh frozen assignment at1da941e after the user authorized it.
Matching source and installed observer were temporarily switched together for
the existing deployment preflight,then restored exactly;see the linked receipt.

Validation:36 focused tests passed with the existing isolated Lua5.3 runtime and
installed JSON decoder;zero skips. An initial invocation without the harness
environment passed20 Python tests and skipped the Lua module, then the documented
harness paths were supplied;no dependency installation occurred. Strict validation
of `shot-selection-audit` passed. Task3 remains unchecked;no archive or gameplay
improvement claim. Full-gate source is unchanged,so the previous2342-test receipt
is retained and not presented as a new full run. OpenSpec apply/verify self-review:
completeness3/4;existing diagnostic requirement/tests remain mapped;new native
flight/damage qualification is not run and cannot be accepted from preparation.
