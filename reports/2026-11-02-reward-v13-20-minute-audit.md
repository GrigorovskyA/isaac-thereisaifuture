# Reward v13: 20-minute native audit

2026-11-02, Europe/Amsterdam. Result: **partial / requested calm-stall timing check did not pass as stated**. At 08:54:46 CET the session was training with no recorded supervisor fault, 1213.9 seconds elapsed and checkpoint `54be12af-s1-t4096`. The audit observation was stopped on the timing discrepancy; training itself was not stopped by the auditor. No gameplay acceptance is claimed.

## Checks and lineage

Source `3b75a3c`, pushed; contract `54be12af1dcec7f0ade2dc109cbcb2f90b71d6e58cb7d51d17b3b704fa4859cc`, reward v13, seed 1. The new model was initialized at 08:34:32 CET; menu.jsonl recorded file 2 Continue and verified it. The configured CUDA device is available, and worker PID 22320 appeared among NVIDIA GPU processes. `Check.ps1` passed 1700 tests with isolated Lua, no skips, two warnings; Smoke-RL passed; strict OpenSpec was 36/36. Previous run moved to `runs/pure-v4-e3b`; all 92 file SHA-256 hashes matched before/after, including checkpoint `db85924f-s1-t273408`. Source and deployed observer main.lua matched SHA-256 `c0e46838b2ea2e3d186911a86d48f1cc056353a967a92cc4846eb4a3de3a1fe7` and were not redeployed.

## Stall timing

The 08:54:46 read captured 60 completed episode rows, 55 stall episodes, all tagged `stall_room_clear=1`, `stall_enemies=0`; no stall with enemies was observed. All 55 calm-tagged rows had `stall_seconds_in_room` populated: 47 were within 15–20 seconds, 6 were below 15 (12.0–14.9) and 2 were above 20 (29.5 and 32.3). All eight outliers: episode 16=13.5, 21=32.3, 26=29.5, 27=13.5, 41=13.4, 42=14.9, 56=13.6, 59=12.0 seconds. Thus the requested criterion that calm-room rows show approximately 15–20 seconds is not established for all observed cases, and the enemy-present approximately 30-second case is untested.

Important measurement distinction: `stall_seconds_in_room` is game-update time since room change or episode start, whereas `StallWatchdog` counts active wall time since the last progress, excludes inactive gaps and resets on progress. These values are not identical clocks or necessarily the same interval. The outliers do not by themselves prove the watchdog fired at the wrong wall time; the present evidence does not explain each discrepancy. No code or configuration was changed in response.

## Training statistics

| Saved steps | Rollout s | Previous update s | approx_kl | entropy_loss | use_none |
|---:|---:|---:|---:|---:|---:|
| 1024 | 249.485 | blank | 0.011490 | -3.338038 | 0.8447 |
| 2048 | 250.953 | 26.515 | 0.009238 | -3.317325 | 0.8076 |
| 3072 | 256.562 | 26.516 | 0.007404 | -3.301915 | 0.8066 |
| 4096 | 255.250 | 22.172 | 0.009286 | -3.289863 | 0.8291 |

Three recorded prior-update durations were below 60 seconds; the first was blank. `use_none` was at least 0.6 in all four rows. These are early training statistics, not an evaluation of long-term performance.

The listed `entropy_loss` uses v13's 0.2 weight for the use head. Its magnitude must not
be compared to 4.6 nats or the unweighted E3B entropy as a measure of policy improvement.
The 75k and 150k reports should instead compare `move_*`, `shoot_*` and `use_none` shares.

## Checkpoint readback

At 08:54:46 CET, manifest `54be12af-s1-t4096` had `hyperparameters.use_entropy_scale=0.2` and the five files matched their manifest SHA-256:

| File | SHA-256 |
|---|---|
| model.zip | `b5a52cdf448f6b0e28b3ff3eb159e7c13ae3a2e62fa24c5ce515a0ad300c25f2` |
| vecnormalize.pkl | `2ebddc4d063beb292f0d65d6d5b96cef80e698cf8e280e7bb3e4160e948b660e` |
| novelty_counts.npz | `9589856c3bb5b70febbab8b39c72c5e23b844f57c84dfe2fac8363dec51f0ab6` |
| auxiliary.pt | `76826f1cb31f88d9582dac3fdadf172e602e03eb92934a288f27d3c8838ebc16` |
| e3b.pt | `54a858aa8cad650e36760327387b2c1adbc42053ce43e8ef7d54f911c10e2704` |

Source evidence: `runs/pure-v4/supervisor/session-20261102-083432-0001/{plan,menu,events,console,status}`, `runs/pure-v4/metrics/{episodes,train}.csv`, and `reports/local/reward-v13-20261102/archive-{before,after}.json`. Milestone reports and continued monitoring were not started after this audit discrepancy; the running supervisor was left untouched.
