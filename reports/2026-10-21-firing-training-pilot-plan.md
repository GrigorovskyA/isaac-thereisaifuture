# Plan: five-minute firing-reward learning pilot

User2026-10-21 accepted trying the proposed separate compatible model lineage and
five-minute learning pilot. This explicitly authorizes the finite experiment below;
it does not reopen the cancelled hour/four-hour experiments or authorize New Run.

## Lineage and objective transition

Source:7d53f55f-s20-t21760 in runs/live-conservative-v2-overnight-20261021,
seed20,original reward live-conservative-v2. Preserve this directory, its latest
pointer, and all older parents. Create one separate warm-start root
runs/live-firing-v3-pilot-20261021. New config
configs/training-live-firing-v3-pilot.yaml changes only status and budget fields.
All algorithm/learning/observation/action parameters stay identical.

Explicitly copy model.zip and vecnormalize.pkl byte for byte, preserving optimizer,
observation/return normalization statistics and RNG. A new storage-v2 manifest
records the new configuration/reward contract live-firing-v3 and original parent
ID. Initial timesteps remain21760:copying is not learning. Save migration provenance
and verify source/destination hashes, strict contract acceptance and unchanged
model timestep/update counters before any game launch. Missing or incompatible
source stops; no fresh initialization fallback. Existing direct v2 resume under
v3 remains refused. This is an explicit objective transition, not exact continuation
of the old reward process; inherited critic and return statistics may adapt slowly.
The collector-local novelty ledger starts with a fresh unpaid baseline and its
restart discontinuity is recorded. No policy encoder/schema migration occurs.

## Finite execution

One fresh gpt-6-luna/high script worker executes primary-prepared commands from
D:/isaac, sequential offline verification then one native training invocation.
The primary owns migration, source changes and acceptance. The worker does not
implement, deploy, install, alter saves/Steam options/Cloud, write Git or spawn agents.

Native time:maximum300 seconds inclusive Steam/menu setup, plus owned cleanup.
No automatic retry, lease renewal or second game session. File2/Continue only,
fresh native menu identity and active Isaac verification precede gameplay. No
New Run fallback. Existing focus guard and structured bridge control remain.
Step sentinel1billion,restart sentinel5000,no practical death count stop;
finite time,2GiB disk,128MiB endpoint trace,maxfaults0,strict lineage,release and
owned cleanup guards remain. Navigation uses time-dominant mode. The no-registered-
combat-progress guard is9000 updates (300s native combat), declared before learning
to permit a full small training window; shaping never resets that guard.

The worker uses --resume from the exact migrated checkpoint, --firing-position-reward,
combat gate, auto-navigation, seed20 and session deadline. Completed256-decision
rollouts publish immutable model/normalizer/RNG checkpoints; partial rollout at
stop may be unsaved. The primary must verify a new completed optimizer update
before reporting learning. Parent checkpoints are frozen, while this pilot's own
latest/new descendants are mutable outputs. Exact helper hashes, absolute start/
action/cleanup deadlines, approved paths and command receipt are added before dispatch.

## Measurement and escalation

Capture paired policy/raw endpoints, named reward components, native accepted
actions, checkpoint/save counts and faults/outcomes. Independently report observed
enemy HP-loss lower bound, player red+soul health loss, raw clear edges and exposure,
including unknown terminal coverage. Do not infer kills from disappearance.
Compare descriptively with the frozen t21760 shadow audit, recording actual initial
state differences and control modes. Adaptive stochastic training versus frozen
deterministic inference is not a paired frozen model evaluation or proof of gain.
No winner selection from reward or changed weights. Test split remains held out.

This invocation requests only the five-minute stage. A future15-30minute stage
requires reviewing actual progress/stagnation, saved-state integrity, fault-free
cleanup and an explicit follow-up finite plan. Hour/four-hour stages remain later.
Task2.2 stays incomplete until its actual comparison/duration requirements pass.

## Prepared warm start

Primary migration/readback passed before launch. New canonical configuration hash
7951bf196cd5181f825c71c6e40d496a2e2c7cfc843755e4e05cafdf04a22c8c,
initial checkpoint7951bf19-s20-t21760,parent7d53f55f-s20-t21760.
Model045f96ac5ae34c3d5db7584f3642dc5ed823fa4496d838ee416994fa6e64fca2
and normalizerca30e667a81cee27faac5e6229fb2e7d02f13d77596b02896be272b7788b06f7
are byte-identical. Both loaded models report21760 timesteps/340 optimizer epochs;
RNG unchanged, all nonstatus/nonbudget config fields equal, original latest unchanged.
Provenance:run-root reward-migration.json and local migration.json. No learning
occurred during copying/readback. Existing2269-test full source gate remains valid;
source/mod/test code is unchanged. Fresh targeted checks precede native execution.
