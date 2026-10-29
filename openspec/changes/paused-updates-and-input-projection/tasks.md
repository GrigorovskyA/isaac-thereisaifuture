## 1. Implementation

- [x] 1.1 `policy.py`: shared `Linear(obs, features_dim)` + ReLU extractor and one kwargs
  helper; `features_dim` in the hashed contract and used for every fresh model; checkpoints
  of another width are refused by the contract hash.
- [x] 1.2 `n_steps` 1024 and `batch_size` 256 in `configs/training-pure-v4.yaml`; retention
  comment and docs updated.
- [x] 1.3 `update_pause.py` and the backend backlog: pause at rollout end, resume at the next
  rollout start, bounded waits, failures recorded and never raised; `live` config section.
- [x] 1.4 Worker keyboard (`LazyWindowsMenu`) reusing the guarded menu input.
- [x] 1.5 `train.csv` columns `pause_seconds` and `pause_ok` with upgrade of older headers.
- [x] 1.6 Tests: policy shape and refusal, contract hash, config parsing, pause ordering,
  timeout, already paused, focus loss, failed resume, callbacks, backend backlog, metrics.

## 2. Verification

- [x] 2.1 Offline gate: `scripts/check.sh` and strict OpenSpec validation (macOS).
- [x] 2.2 Native one hour on Windows: `update_seconds` median below 12 s, `pause_ok` share
  above 90%, no fault from pausing, steps per hour not below the schema-7 run.

Windows follow-up (2026-10-29): Check passed (1422 tests including Lua, no skips),
strict OpenSpec 24/24, synthetic CPU smoke passed. Observer deployment hashes matched;
schema 7 was archived. Native startup failed before training because file-2 Continue
was unavailable. Task 2.2 remains unchecked; no native acceptance is claimed.
See [bounded startup report](../../../reports/2026-10-29-schema8-startup-blocked.md).

Authorized repeated hour ended cleanly on 2026-10-29 at t15360. Native task 2.2
remains unchecked: all 15 pause_ok/pause_seconds cells are empty; required pause
success cannot be verified. Snapshot size, update latency and positive door/minimap/
enemy identity samples were observed, but continuation was not accepted. No fix/retry.
See [final qualification report](../../../reports/2026-10-31-pure-v9-schema8-training.md).

Review (2026-10-29): the pauses worked; only their metrics were lost. train() calls learn()
once per rollout, so the metrics row was written at learn() end, before the resume that
carries the pause result. The game log shows it: `Observer perf` windows drop from ~300 game
updates per 10 s to 51-140 (or two windows of ~190) about every 3.7 min, about 14 times, with one
recorded foreground refusal. Fixed: the row waits for the resume (`waiting`), train() flushes it
after the final resume, and a working pause records `update_paused` with its seconds. Rerun 2.2.

Windows follow-up (2026-10-29): Check1427 includingLua/no skips and strict specs25/25
passed at bc5e985. Authorized no-initialize resume fromt15360 stopped early att16384:
pause_ok0/1, foreground refusal; startup also had a faulted automatic attempt.
All60 old episode/15 train rows preserved; new6 stall/1 death contexts were valid
in the available sample. Task2.2 remains unchecked: full-hour acceptance not reached.
No fix or retry. [Report](../../../reports/2026-10-31-schema8-pause-stall-training.md).

Full-hour follow-up passed (2026-10-29, sourcefde8b1f): 15/15 successful pauses,
all durations filled, update median7.7735s, 15 update_paused and no pause/resume skips.
Native exit0/faultnull/cleanup[], t16384->t31744, 15583 completed-episode steps.
All67 old episode/16 train rows preserved; 48 new stall and20 nonstall contexts
validated. Zero-enemy stall kind/distance fields are conditionally empty by design.
Task2.2 passed in this scope; no task2.3 acceptance or archive is claimed.
See [hour qualification](../../../reports/2026-10-29-focus-hour-qualification.md).
