# Demo lineage v2 start evidence

Date: 2026-11-04, Europe/Amsterdam. Source: `f6c5c0f`. Self-review; this is not evidence of improved gameplay.

## Preparation and checks

- Training was not running and `runs/pure-v4` was absent before initialization.
- `scripts/Check.ps1` passed: 1,792 collected and passed, 0 failed, 0 skipped; two warnings. Lint, format, mypy and dependency checks passed. The process used `PYTEST_ADDOPTS=--basetemp=reports/local/pytest-20261104`, test-only `reports/local/reward-v12-schema9-20261031/lua-runtime` on `PYTHONPATH`, and the installed game's `resources/scripts/json.lua` via `ISAAC_JSON_LUA`. Strict OpenSpec validation passed 37/37. The ignored temporary directory was retained as requested.
- Both `demo_dataset runs/demos` and the same command with `--characters all` reported 36,154 steps, 19 sequences, characters `{"0": 36154}`, and zero dropped steps.
- `runs/pure-v4-demo-bc-v1/seed-1/checkpoints` contained `c8a7486b-s1-t440320`; `latest.txt` pointed to it. This checks the specified checkpoint, not a complete archive inventory.
- With Isaac closed, source and installed observer `main.lua` SHA-256 both matched `449f9e765a643a9c9c24724a2649a2407db560890093851677d831f0db711bac`. The mod was not redeployed.

## Initialization and pretraining

`Train-Start.cmd --initialize` started supervisor session `session-20261104-123331-0001`. Menu evidence verified slot 2 Continue, and the observer verified character 0. The runtime configuration event recorded contract `c8a7486b9806f2cd76e3aab5324163659dfb4b3ae41a619ed61a362be8936121`.

`runs/pure-v4/seed-1/pretraining.json` reports 31,934 training demo steps in 17 sequences, and 4,220 holdout steps in two sequences. It stopped at 2,750 optimizer steps after 370.562 seconds and selected best step 1,250. Final train NLL was 0.314885; selected holdout-after NLL was 1.806281. These values are from different points in the early-stopped run.

| Head | Holdout before accuracy | Holdout after accuracy | Majority accuracy |
| --- | ---: | ---: | ---: |
| Move | 22.84% | 59.48% | 25.36% |
| Shoot | 20.62% | 78.10% | 29.36% |
| Use | 99.74% | 99.74% | 99.74% |

The holdout contains only two sequences; use accuracy matches the majority baseline.

## Audit after 20 minutes of RL

The initial `c8a7486b-s1-t0` checkpoint completed at 12:41:49 CET. At 13:02:07 CET, approximately 20 minutes 18 seconds later, `Train-Status.cmd` reported training running, supervisor PIDs 39264 and 54704, stop file absent, latest checkpoint `c8a7486b-s1-t3072`, 50 episodes, session state `training`, and no displayed fault. `latest.txt` agreed with the checkpoint ID. Supervisor `status.json` had `fault: null` and `reason: null`. A search of `console.txt` for fault, error, traceback, exception and timeout found only configuration keys `connection_timeout` and `max_faults`, not a fault message. This is a point-in-time audit; training continued.

No frozen evaluation or gameplay improvement is established by this startup audit.
