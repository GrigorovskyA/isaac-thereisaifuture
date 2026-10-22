# Evidence: offline diagnosis of corner stagnation

Date: 2026-10-21, Europe/Amsterdam. Analyzed revision:
`3ad1b094ed2c1e79f5e525a95c45f9ec7b797c13`. The user requested analysis, not another
training session. No game, environment, action sampling, optimizer update, model
rewrite, approval or deployment was invoked. Original v2 t21760 and v3 t24064
remain unchanged. Production fixes described below are recommendations, not applied.

## Findings and priority

1. **Critical: the distance formula can reward retreat in an open passage.**
   `firing_position.py:97` adds distance from the player back to the nearest cell
   center to a graph distance beginning at that center. Inside a cell this can
   reverse the intended gradient. The actual production ledger reproduces a
   positive reward while the player moves farther from the only firing goal.
   This is a demonstrated mathematical defect, not proof that it alone caused
   the native corner behavior.
2. **Warning: one room record compares incompatible target goals.**
   `firing_position.py:210` uses a physical-room high-water mark even after the
   nearest enemy and firing-goal set change. This suppresses legitimate new-target
   progress below the previous target's record. A bounded counterfactual on the
   actual trace recovers only two small bonuses, so fixing this alone is insufficient.
3. **Confirmed behavioral bias, without complete entropy collapse.** The final
   model still prefers left/down and shooting up on the recorded states. Entropy
   increased and alternatives retain probability. More updates did not establish
   hits or clears; a deterministic controller still selects the same broad pattern.
4. **Policy information remains limited by design.** Schema1 encodes relative
   positions/velocities and optional HP, not tear range, vulnerability, projectile
   clearance or obstacle collision type. Both enemies' policy HP stayed unknown.
   The missing data are plausible learning limitations, not individually proven
   causes. Range/clearance reward telemetry must not be silently fed into schema1.
5. **Optimizer-associated stale observations are real but sparse.** Nine actions
   lagged their policy frame by 9-21 game frames; 2497 were within one frame.
   This merits a freshness fix, but does not by itself explain thousands of
   stationary decisions. No observation/normalizer corruption was found.

## Inputs, bounded execution and verification

One fresh gpt-6-luna/high script worker ran exactly:
`D:/isaac/.venv/Scripts/python.exe -u D:/isaac/reports/local/analyze-firing-policy.py`.
Working directory D:/isaac, PYTHONUNBUFFERED=1. Script SHA256:
`d86779b8431cedd5c37180183e4012446b6ffa22cd024650ea0233361f08be15`.
Task firing-policy-offline-diagnosis-20261021-01; latest permitted start
1792591146.9051518 Unix, absolute stop 1792591326.9051518, command cap180s,
output cap128MiB, 2506 trace records, zero native actions/training/retries.
The worker initially interpreted start-before as an earliest start; primary
corrected that interpretation before execution, with no deadline change or retry.

Frozen inputs: 99 paths including paired traces, all ten explicit pilot
checkpoints, source and installed SB3/RecurrentPPO normalization/distribution code.
No unpinned external API assumptions or dependency updates. The script sets one
Torch CPU thread inside its own process and only evaluates distributions.
Local output: reports/local/firing-policy-diagnosis-20261021/analysis.json.

| Check | Exit/status | Result |
|---|---|---|
| Prepared offline replay |0 / passed|2506 records, 8.375s computation, no analysis errors |
| Reconstructed normalizer |passed|9/9 saved checkpoint boundaries: exactly equal counts, means and variances |
| Primary artifact readback |0 / passed|99 frozen input hashes unchanged; original v2 source/latest 4 hashes unchanged |
| Raw and normalized clipping |passed|Zero clipped raw features on all2506 frames; zero normalized clipping in all replays |
| Counterfactual ledger sign |command0 / expectation failed|Production ledger pays +0.003231509 for moving away from the only goal |
| Per-target/shared-cap simulation |command0 / diagnostic|19 bonuses versus17; total0.113936920 versus0.111155021 |
| Full source gate/native checks |not_run|No source changes or new game run; prior2269-test gate is not evidence against this newly exposed counterexample |

Primary read actual JSON and checked direction mapping explicitly:
0=none,1=left,2=right,3=up,4=down. A worker's informal direction/clipping paraphrase
was incorrect; it was not accepted as evidence. `raw_encoder_clipped_values={"0":2506}`
means zero clipping on2506 records, not2506 clipped features.

Additional local artifacts: primary-verification.json and reward-counterfactual.json.
Models, raw traces and diagnostics remain local and are excluded from Git.

## Distance-sign counterexample

Use a synthetic open7x3 grid, spacing40, origin(0,0), all cells walkable. One known
clear firing goal at(160,40), target at(240,40), ordinary-tear range260 and80unit
standoff. This is a mathematical fixture using production functions, not native
line-query evidence and not a trajectory supplied to a policy or trainer.

| Player position | True distance to firing goal | Current modeled path distance | Potential |
|---|---:|---:|---:|
|(10,40)|150|170|0.604651163|
|(1,40)|159|161|0.617577197|

Moving from(10,40) to(1,40) retreats9 units, but `FiringProgress.begin/transition`
pays **+0.003231508589736476** with a fresh unpaid baseline. Walking toward the
goal reverses this local change. The cause is the forced route via the current
cell center: `steps*40 + distance(player,current_center)`. Approaching that center
can improve the formula while moving away from the actual goal. The specification's
intent of crediting firing-position progress is not satisfied by this case.

The cap and high-water guard prevent unlimited repeat farming; they do not make
the first incorrect reward valid. The replacement needs continuous position-aware
path cost with monotonic direct-path counterfactuals, bounded feasible connectors
and unchanged projectile-clearance requirements. Merely scaling the coefficient
preserves the wrong sign. A different reward contract is required before learning
with corrected semantics; preserve v3 artifacts rather than reinterpret them.

## Signal lifetime and target changes

All17 actual positive bonuses occurred at decisions9-34, within the first35
decisions and before the first optimizer update at256. No bonus followed during
the remaining2471 completed decisions. This is not exhaustion of the0.25 room
budget: only0.111155 was paid. The historical potential reached0.926102.

At decision36 the nearest target changed from enemy2 to enemy1. Current potential
was0.594962, but the inherited room record remained0.926102. Improvements for the
new target below that unrelated record cannot pay. A diagnostic simulation with
persistent per-target records and a shared0.25 physical-room cap recovers bonuses
at decisions36/37, totaling only +0.002781898. This is not a validated replacement
contract or evidence of improved future learning. It shows the suppression and
also its limited effect on this particular already-retreating trajectory.

Correction of a preliminary commentary hypothesis: the reward target did **not**
stay enemy2 throughout. Full-trace analysis showed nearest enemy and shaping
target agree in all2506 cases, always policy slot0: enemy2 for36 decisions and
enemy1 for2470. The initial mismatch hypothesis came from overgeneralizing an
early snapshot and is rejected. Both chosen targets have positive vulnerability
evidence in the firing channel; there is no support for an invulnerable-nearest
enemy explanation in this trace.

## Action probabilities and normalization

Replayed actor LSTM states reset at the five recorded software episode starts.
The adaptive reconstruction uses the initial observation statistics, updates them
once per real recorded policy input and switches weights at each saved256-step
boundary. All nine saved observation-statistic states match bit for bit. This
strongly validates input reconstruction, but probabilities and hidden states were
not logged natively; do not relabel this as direct on-policy probability telemetry.
Frozen endpoint comparisons replay the same recorded observations and are
counterfactual: they do not establish which trajectory a different model would play.

Mean probabilities on the recorded states:

| Action | Frozen initial t21760 | Frozen final t24064 | Reconstructed adaptive run |
|---|---:|---:|---:|
|Move left|42.39%|49.22%|39.59%|
|Move down|46.73%|29.22%|44.00%|
|Move right|1.76%|3.27%|2.54%|
|Move up|2.19%|4.88%|4.32%|
|No movement|6.93%|13.41%|9.55%|
|Shoot up|60.39%|53.47%|55.89%|

Left/down combined declined89.12%->78.44%, with mean movement entropy
1.004->1.197 nats (maximum log5=1.609). Shooting entropy1.165->1.244.
This is less concentrated, not a completely deterministic policy. Nevertheless,
move argmax remains left or down for all2506 states, and shoot argmax is up for
all2506 states in both frozen endpoint replays. Deterministic selection therefore
hides the alternatives that stochastic training sometimes samples.

Final weights with the **old** normalizer produce very similar means: left49.03%,
down29.40%, shoot up53.45%. Normalizer drift is not the dominant explanation for
the probability changes in this replay. Both normalization stages had zero clipping.
Existing return standard deviation changed3.559->3.390; it is not evidence of a
reward-normalizer crash. No conclusion about optimal entropy/reward coefficients
follows from these observations.

## Information and timing limits

The649-element encoder has no weapon range or clearance input and no enemy type,
vulnerability/phase or obstacle collision-class field. Policy enemy HP was unknown
in every sampled enemy slot, despite raw reward HP being available separately.
This separation is intentional; oracle data must not be copied into the policy.
The actor receives both relative enemy positions and **12** nearest obstacle
positions from Lua, although the Python encoder reserves24 obstacle slots.
41 additional obstacles were omitted in this room by the Lua source cap, not
numeric clipping. The prior24-obstacle statement confused encoder capacity with
actual exported coverage and was corrected after raw-frame readback.
These constraints can make aiming/path learning difficult, but the
analysis does not prove which additional observable feature would be sufficient.

Nine native commands had9-21frame policy-observation lag (0.30-0.70s at30Hz).
Each followed checkpoint completion by35.5-51.1ms on the paired clocks, supporting
association with optimizer/checkpoint pauses. They are9/2506=0.359% of completed
decisions.2497/2506 were within one frame. The backend checks transport freshness,
but that does not refresh the observation already normalized for the actor.
Any fix must preserve exact observation/action/normalizer and recurrent-state
accounting; silently replacing SB3 input or inventing transitions is unacceptable.

## Self-review and continuation

Using openspec-verify-change for firing-position-shaping, primary self-review,
not independent review. Existing planning artifacts/design/specs and source were
read against the new counterexample and saved evidence.

| Dimension | Assessment |
|---|---|
|Completeness|4/5 historical tasks;2.2 comparison/15-30min remains incomplete |
|Correctness|Critical distance-sign counterexample invalidates a clean progress-reward correctness claim;target-coherence warning also open |
|Coherence|Code follows the existing center-offset/room-record design, exposing a design flaw;do not weaken the requirement to accept it |

The change remains unarchived and unsuitable for automatic escalation. Proposed
next work, not performed here:

1. Create a small corrective OpenSpec change for continuous position progress and
   target-coherent records sharing one persistent room cap. Add the open-passage
   retreat/approach regression, multi-target switching and reset/oscillation bounds.
   Version corrected reward semantics explicitly; retain original/v3 checkpoints.
2. Address post-optimizer observation freshness with explicit trace/accounting.
   Do not present these sparse delays as the sole cause of stagnation.
3. Design any needed observable weapon/target/geometry features as a separate
   observation version, with unknown semantics and checkpoint compatibility.
   Keep reward labels and hidden geometry out of that channel.
4. Only then declare another finite five-minute experiment and compare actual
   damage dealt/taken and verified clears;do not jump to15-30minutes or an hour.

No claim that these changes guarantee better play. No production change, training
resume, New Run or new model was made during this diagnosis.
