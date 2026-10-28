# Evidence: Isaac parallel-instance launch probe, 2026-10-28

## Scope and preserved training

The user explicitly requested pausing training and attempting two to four simultaneous game instances to investigate faster collection. Training stopped through stop.forever at 12:02:56 CET, learner exit 0, fault null, cleanup_errors empty. The saved checkpoint is `fb22b342-s1-t539648`; t510976 remains pinned. The ent_coef=0.01 continuation is summarized in the [interrupted-run report](2026-10-29-pure-v8-ent001-overnight.md).

The launch probe ran from 12:03:51 to 12:06:23 CET, within a ten-minute cap, at most four concurrent game processes and six launch requests. It performed zero gameplay steps and no save selection, Continue, New Run, training or evaluation. No source, configuration, mod, Steam launch options, save files or Cloud settings were edited. Normal game startup/shutdown can perform its own file writes.

## Attempts and observed results

| Attempt | Method | Observation |
|---|---|---|
| 1 | Existing Steam URI, app 250900 | One Isaac process, PID 29504, parent Steam PID 36764; responsive Repentance+ v1.9.7.17 window; existing --luadebug preserved. |
| 2 | Same Steam URI while PID 29504 remained active | Still only PID 29504; no independent second process observed after 12 seconds. |
| 3 | Steam executable with -applaunch 250900 | Still only PID 29504 after a further 10 seconds. |
| 4 | Installed isaac-ng.exe directly, same directory, Steam active | Requested PID 34496 disappeared; only PID 29504 remained after 12 seconds. |
| 5 | Same direct launch with captured process exit | Requested PID 13408 exited with code 53, empty stdout/stderr; no second persistent process. |

Maximum observed simultaneous Isaac instances: **one**. Four-instance testing was not reached because two independent instances did not survive. Code 53 is recorded as an observed exit code; this probe did not establish its underlying cause or prove whether Steam, the game or its launch environment enforces the restriction. No executable patching, injected libraries, authentication workarounds, third-party multi-instance tools or save-profile changes were attempted.

## Resources and architecture

Before launching, 16,923,816 KiB (16.1 GiB) RAM was free out of 33,338,560 KiB (31.8 GiB) visible RAM; sampled total CPU load was 18%. The first game used about 495 MiB working set at the menu/intro. These are idle/menu measurements, not a parallel gameplay throughput benchmark. Hardware capacity did not explain the observed immediate second-process exit.

The current trainer also requires implementation work before parallel games could train one policy: session_runner binds a single listener on 127.0.0.1:9528; launcher rejects an existing Isaac process; Windows menu control expects one newly launched matching window; training creates one DummyVecEnv environment. Merely starting independent trainers would not aggregate experience into one learner. No parallel-training implementation or speedup is claimed.

## Cleanup and evidence

The sole owned test window, PID 29504, was closed using CloseMainWindow. Steam gameprocess_log.txt recorded its exit code 0 at 12:06:23 CET. Live checks found no remaining Isaac/training/timer-owner process and no listener on port 9528. stop.forever remains; the recurring training monitor is paused. No automatic resumption is scheduled by this probe.

Local receipts, outside Git: `reports/local/parallel-instance-probe-20261028/plan.json`, `preflight.json`, `after-first-launch.json`, `after-second-uri.json`, `after-applaunch.json`, `after-direct.json`, `direct-exit.json`. Training results remain under `reports/local/pure-v8-ent001-20261028/` and `runs/pure-v4/`.

Self-review only. Result: launch feasibility was not established for two instances; four instances and shared-learner throughput remain untested. A further experiment needs a supported independent-instance launch method and separate instance identity, bridge endpoints, supervision and save/profile handling before native parallel training.
