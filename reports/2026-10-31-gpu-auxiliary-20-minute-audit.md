# GPU and auxiliary training: 20-minute audit

2026-10-31, Europe/Amsterdam. Result: partial; final checkpoint readback command failed with a PowerShell parser error. Training was not stopped by this audit.

## Preparation and launch

- Source commit `077508f` pushed to origin/main. `tools/offline-replay-viewer` was left uncommitted.
- CUDA Torch 2.14.1+cu130; Check.ps1 passed with isolated Lua and temporary directory: 1672 passed, 0 skipped, 2 warnings; OpenSpec 35/35. The default temporary directory produced WinError 5 during pytest cleanup; a separate run with the requested basetemp passed 1282 tests with 12 Lua-module skips, before the full Lua-enabled pass. Smoke-RL passed including cuda_to_cpu_checkpoint.
- Config hash `0399c37db311f00df37cea79a66385ff6cd7150dfcfa0c9e3e46415f577da79a` confirmed before launch and in runtime log.
- Previous run moved to `runs/pure-v4-full-batch-structured`; 37 files matched SHA-256 before and after. Evidence: `reports/local/gpu-auxiliary-20261031/archive-before.json` and `archive-after.json`.
- Observer deployed while Isaac closed; source/deployed SHA-256 `c0e46838b2ea2e3d186911a86d48f1cc056353a967a92cc4846eb4a3de3a1fe7`. Prior observer backed up under `reports/local/gpu-auxiliary-20261031/observer-before-main.lua`.
- Supervisor session `session-20261031-220351-0001` started at 22:03:51 CET, fresh model `--initialize`. `menu.jsonl` recorded `menu_entry_resolved`, slot 2, Continue, plus verification. NVIDIA listed actual worker PID 21264 among GPU processes; config requires CUDA and torch reported CUDA available. This is runtime device evidence, not a gameplay-quality claim.

## Observed training rows

| Steps | rollout s | update s | aux s | n_updates | approx_kl | aux_approx_kl | aux_latent_loss | value_loss | explained_variance |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1024 | 230.156 | not recorded | 12.342 | 10 | 0.013155 | 0.004990 | 0.356557 | 1.820596 | -0.01549 |
| 2048 | 221.562 | 26.141 | 10.631 | 20 | 0.010203 | 0.0000286 | 0.066412 | 0.365392 | 0.51573 |
| 3072 | 229.234 | 20.969 | 10.346 | 30 | 0.006024 | 0.000114 | 0.039919 | 0.230657 | -0.41347 |
| 4096 | 235.954 | 22.000 | 10.205 | 40 | 0.007877 | 0.0000889 | 0.031808 | 0.281170 | 0.10768 |

Three recorded update durations were under 60 seconds; first row is blank. `n_updates` grew by 10 each rollout. Rollouts were 221.6-236.0 seconds versus the approximate prior 220 seconds; no independent frame-rate measurement was taken. The auxiliary KL was below PPO KL in each row, so the proposed coefficient change is not supported on these observations. Latent loss declined and value loss rose slightly in the last row; this is not evidence of collapse to zero, but warrants monitoring. Explained variance fluctuated.

## Checkpoints and status

At t1024 the manifest hashes matched actual bytes for `model.zip` (`ff6e90d72e4efb6d230a741a8cb431b4ae9626e1ad0b6d0526818fd03c8cfbc5`), `vecnormalize.pkl` (`028282a95ba4c7b60df733cddd6f5140cd1c969270384c3ab6f6dfcc196ef3c7`), `novelty_counts.npz` (`3c18c8178ed479a6aefc4b5b482d8e96f48f3d167710a16da7b93baed01e09d3`) and `auxiliary.pt` (`5ece799902d076d0eee6e61a5cfdcc9fc6c667d3a567779e4a7f7d18ed5672b2`).

`Train-Status.cmd` before launch reported not running; during training reported RUNNING. At 22:23:24 CET the last successful status read showed training, no fault, 4096 saved steps and 30 episodes. Train-Stop was not invoked or tested, per instruction. Training was still running in that last successful read.

At approximately 20 minutes, a command intended to recheck hashes of checkpoint `0399c37d-s1-t4096` failed before execution with `ParserError: An empty pipe element is not allowed` due to a malformed PowerShell pipeline. No t4096 hash result is claimed. Subsequent actions were stopped as instructed; no 75k/150k comparison was performed.

## Follow-up readback

At 22:26:09 CET, latest checkpoint `0399c37d-s1-t5120` was read successfully; all four SHA-256 values matched their manifest: model `98b46d20406500442d22907b135424efb4eb7f954285bcc45d24d559a2a20850`; normalizer `d96d8700554307217121d43f08dc4e8411beebb55c7bfb810a3e394c776f970a`; novelty counts `3d86bdf628675defee3f2fffb3460d19b22b678b015efebbefc224dde1edd673`; auxiliary `77860fdc490cbd806e9e1ded23a802abf9c1cee0a2570f2149413784522360ed`. Supervisor showed training, fault null. The previously failed t4096 command did not establish t4096 hashes; the newer checkpoint was checked instead.
