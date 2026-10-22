# Evidence: native coherent combat geometry qualification

- Date: 2026-10-21, Europe/Amsterdam, UTC+02:00.
- Source revision: 57d182adf36e455b7d8912abb6a17a145f8cc1bd; no production source changes.
- Scope: one short native API/observation/v4 shadow-reward check, no learning.
- User requested checking and continuation. Continue/file2 only; no New Run,
  checkpoint migration, model initialization or optimizer update.
- Python 3.12.14; existing installed dependencies. Bridge mod 0.5.0-dev, Lua 5.3,
  no extender; game version/Steam build not exposed by the installed API.

## Declared execution and preparation

Primary deployed only this repository's first-party observer while Isaac was closed,
with backup and exact readback. main.lua SHA256 changed from
34c8063f60e6d2f7d680d01e50e508d88c901f7295599ecfe9d501ded0dd87a5 to
23bd034f4b66f5878e650cddb198dbde1b74df8094bfe4018ff083429c290650.
metadata.xml remained 00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997.
No save, Steam Cloud, launch-option or third-party mod edits.

The original command accidentally included a trailing dot; the parser rejected it
before any approval/game/session. The corrected command then hit the expired start
cutoff, also before runtime. Both failures are retained in the closed local receipt.
After the user's Continue request, primary declared a fresh finite window explicitly;
no already-running experiment or lease was extended. One subsequent native command
ran, with no runtime retries. The source/checkpoint state was identical.

Exact command, with no trailing argument:

```powershell
& D:\isaac\.venv\Scripts\python.exe -u D:\isaac\reports\local\native-coherent-geometry-20261021\diagnostic.py --run
```

One gpt-6-luna/high script worker, PYTHONUNBUFFERED=1, no concurrent primary game
control. Helper SHA256 e7b1bf3134644dd9e7e2e60deab7e1a2ed2f6d660131123024ca57f8e25ca7f8;
final assignment SHA256 57f1164c45e0144fe06e5b91da6bd747d17e88b64c8fb71c3bc70a3e03393c54.
Start cutoff 1792603516.814504 Unix, action stop 1792603606.814504, cleanup stop
1792603651.814504. Maximum 180 seconds inclusive setup, 1200 decisions, 1 GiB
including the preserved run root, 64 MiB paired trace. Stop on first native death,
900 updates without registered progress, any infrastructure fault, disk or time
limit. Approval max_restarts=1 is the schema minimum; no restart occurred or was
permitted by this check's execution plan. Missing Continue stops without replacement.

The frozen policy is original conservative-v2 t21760, seed20, config hash
7d53f55f92aae137da716f2916e4cc18db2c2594ef76bb58d2104bdb1e7ce4ee.
It receives only the unchanged 649-input prefix. The full 723-input observation is
captured and checked, with corrected v4 reward logged only as a shadow component.
This is not schema2 model inference or evidence that the old policy uses new features.

## Results

| Check | Exit | Status | Evidence |
| --- | --- | --- | --- |
| Native finite diagnostic | 0 | passed | 279 decisions; progress stop at903 native updates |
| Full schema2/legacy-prefix reconstruction | 0 | passed | All558 endpoints reproduce723 inputs and original649 prefix exactly |
| Same-frame visible geometry | 0 | passed | All558 frame identities match; visible-only enemy identities validated |
| Ordinary-tear range and line APIs | 0 | passed | Range260 at558 endpoints; blocked in-range and clear out-of-range targets distinguished |
| Ground probes | 0 | passed | Both clear and blocked left/right/down results; up clear in this scenario |
| V4 shadow reward replay | 0 | passed | Exact0.036865795940748194 total;9 positive pairs;237 stationary pairs paid0 |
| Native accepted-action join | 0 | passed | All279 actions match session/epoch/sequence/directions;245 lag0,34 lag1 |
| Artifact preservation | 0 | passed | All76 frozen source/deployed/config/model/normalizer/latest hashes unchanged |
| Owned cleanup | 0 | passed | Native expiry releases and successful shutdown; process/listener/approval absent |
| Retraining or longer duration | n/a | not_run | No optimizer update; actual reward endpoint span29.991s |
| Optimizer-associated observation delay | n/a | not_run | Frozen inference has no PPO update/checkpoint stall |
| Native query-count instrumentation | n/a | not_run | Source bounds4+12 additional queries; no native query counter was added |
| Special weapons/unavailable APIs in game | n/a | not_run | Unknown/failure cases are offline harness coverage only |

Local receipt, raw logs and analyzers: `reports/local/native-coherent-geometry-20261021/`.
Primary read saved result/log files, then ran `analyze-geometry.py` and
`verify-native.py`, both exit0, and saved `geometry-analysis.json`,
`primary-native-verification.json`, `primary-summary.json`. Raw logs stay outside Git.
Worker assertions alone were not accepted as evidence.

## Concrete room evidence

Fresh native log confirms `[Continue, 2]`, no `[New, 2]`, and no death restart.
Active Isaac/type0 was verified before gameplay. Session
93e17135253f4c28b06a20620f85768e, epoch1, room visit0, frames57089 through57992,
updates6 through909. Runtime started1792603459.590877 and finished1792603520.272833:
60.682 seconds including setup and cleanup, well inside the declared cap.

At entry player(560,280), X is80 units below, within range260. The down ground probe
and projectile line to X are both blocked. This matches the annotated stone barrier.
At final player(70.1008,409.9954), left/down are blocked while right/up are clear.
Y is approximately210.23 units away (within range260) but its projectile line is
blocked. X is approximately492.44 units away, with a clear line but outside range.
Thus the new observation distinguishes both failure modes that the old input did
not describe explicitly. These are native CheckLine witnesses, not a claim of
independent physical verification of every line or a guaranteed future hit.

Across duplicated before/after endpoints:560 blocked in-range enemy lines,
53 blocked out-of-range lines,503 clear out-of-range lines. No clear in-range case
was sampled. Ground left:71 clear/487 blocked; right:551 clear/7 blocked;
up:558 clear; down:46 clear/512 blocked. These are repeated endpoint counts,
not independent trials. Query limits were reviewed in the frozen source, not
measured using an extra native counter.

There were42 moving pairs and237 stationary pairs. The v4 reward reproduced its
live scalar exactly and never paid for stationary movement. **495/558 endpoints
lack full interpolation support**, confirming the known conservative near-corner
availability limitation. No broad remedy for corner stagnation follows from a
positive reward or telemetry pass. The old policy still selected left146/down133
and shot up; it had no access to the new features.

Observed enemy HP-loss lower bound0, player half-heart loss0 and clear edges0;
actual damage coverage remains partial. No gameplay improvement, kill or successful
clear is inferred. The 900-update progress threshold was crossed by the final
completed action (903 total), then collection stopped before another action.

## Preservation, self-review and continuation

Original v2 t21760 and v3 t24064 model/normalizer/manifest/latest artifacts were
included in the76-input freeze and are unchanged. No checkpoint was published.
Native log confirms action279 expired/released, observer closure and successful
game shutdown. Primary independently checked no Isaac process, port9528 listener,
approval or temporary approval. Runtime roots totaled597637727 bytes, below1GiB.
The first-party observer remains deployed with geometry opt-in only.

Primary self-review using coherent-combat-geometry requirements accepts task2.1 for
this ordinary-tear scenario: both requirements and four scenario groups have offline
coverage, and ordinary native telemetry/shadow plumbing now has direct evidence.
The change is4/4 and remains unarchived; no automatic archive or training follows.
This is self-review, not independent review. Unsupported weapons and unavailable
APIs remain limited to offline coverage. Source did not change during the native
check:the prior261 targeted/2285 full tests,50 strict OpenSpec items and synthetic
CPU smoke remain the source gate. They were not repeated for report-only edits;
change strict validation is rerun after the task update.

Next address observation freshness around optimization and choose an explicit
compatible schema2 lineage/model transfer plan. Qualify additional clear-in-range
and obstacle scenarios before drawing broad targeting conclusions. Any learning
needs its own finite five-minute experiment and comparable damage dealt/taken/
verified-clear metrics. No automatic15-30min/hour/four-hour escalation, resume or
New Run is authorized by this receipt.
