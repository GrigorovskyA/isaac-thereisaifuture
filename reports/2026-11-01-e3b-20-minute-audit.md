# E3B count intrinsic: 20-minute native audit

2026-11-01, Europe/Amsterdam. Session `session-20261101-101159-0001` started 10:11:59 CET; readback at 10:32:10 CET showed training, 1210 seconds elapsed, no recorded fault, and latest `db85924f-s1-t4096`. This is an early operational audit, not gameplay acceptance.

## Launch and lineage

Source `dc21b2e` (pushed); contract `db85924fdb4f26190d287bf67336aabaa77aca941602016fcebfc5054a64cf21`; seed 1, fresh model initialization, file 2 Continue, E3B count intrinsic and auxiliary enabled. `menu.jsonl` contains `menu_entry_resolved`, `menu_slot_verified` and `menu_continue_verified`. Runtime training event reported the same contract. CUDA Torch `2.14.1+cu130` reported CUDA available; the actual worker PID 12948 appeared among NVIDIA GPU processes, and the config requires `device: cuda`.

`Check.ps1` passed with isolated Lua and temp: 1672 tests, no skips, two warnings; strict OpenSpec 35/35. Smoke-RL passed, including CUDA-to-CPU checkpoint and an E3B IDM loss. The previous GPU-auxiliary run was moved to `runs/pure-v4-gpu-auxiliary`; all 58 file SHA-256 values matched before/after, including checkpoint `0399c37d-s1-t141312`. Before/after inventories are in `reports/local/e3b-lineage-20261101/`. Source and deployed observer main.lua both matched `c0e46838b2ea2e3d186911a86d48f1cc056353a967a92cc4846eb4a3de3a1fe7`; no redeployment occurred.

## Training statistics

| Saved steps | Rollout s | Prior update s | aux s | e3b s | n_updates | approx_kl | aux_approx_kl | e3b_idm_loss | e3b_bonus_mean |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1024 | 238.328 | blank | 11.556 | 4.651 | 10 | 0.011071 | 0.003416 | 4.0523 | 0.018930 |
| 2048 | 247.375 | 27.937 | 9.306 | 4.371 | 20 | 0.008114 | 0.0000489 | 3.7723 | 0.000637 |
| 3072 | 240.860 | 24.578 | 8.239 | 4.316 | 30 | 0.013223 | 0.0000282 | 3.6950 | 0.001298 |
| 4096 | 236.312 | 23.969 | 8.007 | 4.251 | 40 | 0.007811 | 0.0001009 | 3.5624 | 0.001453 |

The first `update_seconds` is blank by design; the following three record the prior update and are all below 60 seconds. `n_updates` increased by ten each rollout; IDM loss fell over these four measurements. E3B bonus means are per-step training values and are distinct from episode totals.

Four rollout durations averaged 240.72 s (range 236.31–247.38 s), approximately 2% above the upper end of the requested rough 220–236 s reference; the second rollout exceeded it by 11.38 s (4.8%). This small early sample does not establish that E3B caused the difference or demonstrate the no-slowdown goal; continue monitoring. No independent FPS measurement was made.

At 10:31:51 CET, 29 completed episode rows had mean `col_e3b` 0.8034 and mean `col_room_visit` 2.2414. The requested threshold `mean col_e3b > ~5` was not reached, so no reduction of `e3b_beta` is proposed on this sample. Counts and sums are training data, not a controlled evaluation.

## Checkpoint readback

At 10:32:10 CET, all five files of `db85924f-s1-t4096` matched their manifest SHA-256:

| File | SHA-256 |
|---|---|
| model.zip | `e17e3f051ea0832f36ca7be7964f3b5d4173bf677e1d7271ba50d8e24a403b7d` |
| vecnormalize.pkl | `c684cbfccf3d1ac496ca316ae58c6f75a48e5ce7cd49e1546359d0ccd54e7406` |
| novelty_counts.npz | `6e4389d9652df36a77d260e8885f52a3f1d6119b87ea1e7d763f9781721f6238` |
| auxiliary.pt | `dbc00805da6171e4049327cd3e4547b4206646cd22045192acba017f5f740b6b` |
| e3b.pt | `82d74819b1132d4f1605629e0bc5a51d23c873075e49667a7de47c8c4d97b761` |

`Train-Status.cmd` returned not running before launch and RUNNING during the audit. `Train-Stop.cmd` was not invoked. The first checkpoint at t1024 was independently verified as well. Training continues; 75k and 150k milestone comparisons remain pending. Native OpenSpec acceptance is not inferred from this audit.
