# Evidence: short navigation and three-frame shooting

Date: 2026-10-22, Europe/Amsterdam. Revision: 1c7ce84050899de766263d690f8079723f57965f.
The current user authorized the proposed offline convergence work and subsequent
mixed control. One Luna/high worker executed each exact prepared assignment;
primary independently verified the artifacts. See the
[finite plan](2026-10-22-mixed-control-plan.md). No inference, learning or New Run.

## Result

The scripted native positive control passed in this measured room: the target's
HP decreased from 10 to 6.5, with player health unchanged at 5 half-hearts. Both
waypoints were acquired at speed 0.077, before seven guarded left-shoot commands.
Three native leftward tear callbacks and sampled flight were recorded. The first
observed target HP decrease stopped the run. This qualifies actual damage in
the scripted scenario, not learned gameplay or general controller performance.

| Measurement | Observed evidence |
|---|---|
| Entry | Fresh guarded file 2 / Continue, Isaac, room 83, door (560,280) |
| Session | 3ea1c33bf84b4b70a5ac39f29b79bf76, epoch 1 |
| Frames | 78592 through 78891 |
| Commands | 185 completed: 154 route, 10 braking, 2 waypoint neutral, 12 final neutral, 7 shooting |
| Actual holds | 178 commands at 1 frame; 7 shooting commands at 3 frames; all expired at their requested duration |
| Waypoints | (560,201.1891), then (317.8625,200.5689); both at speed 0.077 |
| First shot | Frame 78865, position (317.2200,200.5689), zero recorded velocity |
| Native tear callbacks | Frames 78867, 78878, 78889, all leftward |
| Sampled flight | 12 leftward samples, 3 labels; sampled x from 307.2187 to 112.2122 |
| Target HP / player health | 10 to 6.5 / 5 to 5 half-hearts |
| Deaths / clears | Neither observed; terminal and damage coverage remain partial |
| Native action joins | 185 matched; 98 lag 0 frames, 87 lag 1 frame |
| Inclusive startup through cleanup | 39.941 seconds of the 180-second bound |

Every shooting decision had same-frame clear, aligned, in-range visible target
evidence. Every encoded before-vector reconstructed exactly. The three callbacks
and HP endpoints support the positive-control chain; sampled disappearance is
not an exact collision report, and the two 11-frame callback gaps do not establish
a universal firing rate. No unobserved damage or kills are inferred.

## Offline convergence gate

The empirical axis model used the prior 254-command one-frame and 40-command
three-frame development traces. Separate 197/291-command traces supplied model
checks; one health-loss interval was explicitly excluded from the pre-damage
residual pool because it includes knockback. No residual-size filtering occurred.

The actual candidate route branch passed 512 closed-loop development cases:
64 seeds across four timing schedules, with and without sampled empirical
residuals. Position offsets were +/-10 and initial velocities +/-3; all acquired
both waypoints within 230 commands, maximum 215. All five nominal old three-frame
control cases failed to converge in that model. The stored case identities,
counts and input hashes were read back by primary.

These are correlated development/stress cases, not 512 independent native trials
or a held-out learned-policy evaluation. The approximate model and observed-style
1/2-frame timing schedules do not cover arbitrary engine dynamics, collisions or
delays. The subsequent single native success supplies the scenario qualification.

## Bounds, identities and cleanup

Offline assignment: mixed-motion-offline-20261022-01, exit 0 in 0.859 seconds.
Offline helper SHA256: 0b060c91cf8f89672c83ab428b3c0e65225786facaadca1f0fc9614d15588708.
Native assignment: mixed-native-20261022-01, exit 0, one invocation, no retries.
Native helper SHA256: 7a626378d9f6c8cfd3fdb4afe81f29b5bc904409af4d80cc4c160b5fd4561a8b.
Parent: a0a93c29-s20-t26368, seed 20, schema 2/723, reward live-firing-v5.
Config: a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15.

All bounds were explicit: 180 seconds, 320 commands, 90 shooting commands,
900 updates without registered progress, 1800-update scenario ceiling, 1 GiB
output and 32 MiB trace. Zero infrastructure faults, retries or death restarts.
The 900-update gate was retained, not removed or renewed; the observed frame
span was 299. Input freshness, heartbeat, hold expiry and local diagnostic caps
remained unchanged. No training samples or model/normalizer/optimizer writes.

All 537 frozen inputs matched before restoration. Normal native shutdown and
observer close were confirmed; game, listener and owned approval were absent,
with no cleanup errors. Both temporary diagnostic source/deployment files were
restored exactly to SHA256
b9a55abc5c63e68e02ad71bb44b64313dad294bdd2f310d103baff4521b18425.
The other 535 frozen files remained unchanged, including preserved checkpoints.
No manual save/Cloud or launch-option edits occurred.

Local evidence: reports/local/mixed-control-20261022/{closed-loop-result.json,
closed-loop-cases.json,verification.json,analysis.json,timing-readback.json,
restoration.json,native/{assignment.json,deployment.json,native-game-log.txt,session/}}.
Raw traces, models, approvals and backups remain ignored.

## OpenSpec verification and next step

Apply/verify self-review, not independent code review: completeness 4/4; the
directional diagnostic requirement and three scenarios retain their existing
source/test mapping; actual scripted damage now qualifies the native task.
Oracle/learning separation, visible shot guards, bounded execution and lineage
preservation follow the design. No general firing/dodging, learned improvement,
held-out evaluation or room-clear acceptance is claimed. No automatic archive.

Shipped source/config/dependencies are unchanged after diagnostic restoration.
The prior 2342-test full gate and 36-test diagnostic receipt remain applicable;
they are not new test executions. Final validation uses strict specs, diff/links
and frozen-file readback. Next is a declared short firing curriculum and frozen
baseline comparison using damage dealt, damage taken, clears and stagnation.
Changing weights/reward or merely extending the old run is not acceptance.
No training or New Run is authorized by this completed control.
