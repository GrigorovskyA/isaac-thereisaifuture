# GPU and auxiliary self-prediction: 75k training report

2026-11-01, Europe/Amsterdam. The first recorded saved checkpoint at or above 75,000 steps was `0399c37d-s1-t75776`, completed at 03:52:07 CET (02:52:07 UTC). At this hourly review the run remained active and had reached `0399c37d-s1-t82944`. The 75,776 checkpoint was no longer in the five retained checkpoint directories, so its files could not be independently rehashed at this review. The completion event and bounded CSV data establish the recorded milestone; they do not substitute for a retained checkpoint readback.

## Scope and evidence

Source commit `077508f`, seed 1, native file 2, fresh model; contract `0399c37db311f00df37cea79a66385ff6cd7150dfcfa0c9e3e46415f577da79a`, CUDA learner and auxiliary self-prediction. Initial menu selected file 2 Continue. The supervisor and Isaac processes were present at review, with live episode progress. The status retains one previously reported message-deadline fault from episode 109; subsequent checkpoints and episodes demonstrate progress, but do not erase that fault. No milestone-triggered stop or change was made.

Evidence: `runs/pure-v4/supervisor/session-20261031-220351-0001/console.txt` records checkpoint completion; `runs/pure-v4/metrics/{episodes,train}.csv`; archived baseline metrics; `reports/local/gpu-auxiliary-20261031/75k-summary.json` and `milestone-summary.py`. The analysis was made after the threshold, not from a snapshot taken at the instant of 75,776; all comparisons below explicitly filter by fixed bounds. The latest retained checkpoint `0399c37d-s1-t82944` was verified at review: all four model, normalizer, novelty-count and auxiliary SHA-256 values matched its manifest. This does not verify the no-longer-retained 75,776 bytes.

## Gameplay comparison

Select completed episodes whose cumulative observed-step endpoint is in `(0,75000]`; include whole boundary episodes, never split them. Actual included steps differ from one another and from the saved-model step count. The metrics are training trajectories from changing policies, one seed, and uncontrolled layouts, not frozen-policy evaluation. Full-batch-structured ended at 22,535 observed steps and cannot be compared through 75k.

| Lineage | Episodes | Included observed steps | 3+ rooms | Rooms / episode | Stall episodes | Kills | Kills / 1k steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPU + auxiliary | 497 | 74,736 | 27/497 = 5.4% | 1.656 | 374/497 = 75.3% | 371 | 4.964 |
| v11 | 341 | 74,961 | 38/341 = 11.1% | 1.865 | 223/341 = 65.4% | 292 | 3.895 |
| v12 | 431 | 74,776 | 24/431 = 5.6% | 1.775 | 315/431 = 73.1% | 392 | 5.242 |

The 3+ room share is below the 25% goal at this boundary. This describes training, not task acceptance or causal superiority.

For the common early interval `(0,22535]` only:

| Lineage | Episodes | Included observed steps | 3+ rooms | Rooms / episode | Stall episodes | Kills / 1k steps |
|---|---:|---:|---:|---:|---:|---:|
| GPU + auxiliary | 141 | 22,328 | 6/141 = 4.3% | 1.560 | 102/141 = 72.3% | 3.673 |
| v11 | 96 | 22,510 | 12/96 = 12.5% | 1.750 | 65/96 = 67.7% | 2.799 |
| v12 | 132 | 22,480 | 3/132 = 2.3% | 1.553 | 101/132 = 76.5% | 3.959 |
| Full-batch structured | 127 | 22,535 | 8/127 = 6.3% | 1.614 | 94/127 = 74.0% | 2.840 |

Within the current 75k interval, whole-episode endpoint windows `(0,37500]` and `(37500,75000]` had respectively 247 and 250 episodes, 3+ room shares 13/247 = 5.3% and 14/250 = 5.6%, rooms/episode 1.575 and 1.736, stall shares 182/247 = 73.7% and 192/250 = 76.8%, and kills/1k steps 3.974 and 5.961. This is within-run descriptive growth, not evidence of growth after 75k. Growth after 75k is not yet measured at this milestone; assess it at 150k.

## Optimizer trends through saved step 75,776

74 train rows, split into 37 rows through 37,888 and 37 rows above 37,888 through 75,776. This is a model-step bound, separate from episode endpoints.

| Statistic | First 37 rows mean | Last 37 rows mean | Interpretation |
|---|---:|---:|---|
| aux_latent_loss | 0.03819 | 0.03435 | Early first value 0.3566 fell rapidly; later range 0.02718–0.04094, not approximately zero. |
| value_loss | 0.21212 | 0.11385 | Lower in the later half; no sustained rise established by these aggregates. |
| explained_variance | 0.29252 | 0.37470 | Higher mean, but fluctuating; overall range -0.7111 to 0.7938. |
| approx_kl | 0.01236 | 0.02535 | Increased. |
| aux_approx_kl | 0.00219 | 0.00767 | Increased; reached at least half PPO KL in 7/74 rows, never exceeded it. |
| rollout_seconds | 241.19 | 265.03 | Later mean is about 20% slower than the earlier approximate 220 s reference. |
| update_seconds | 24.45 (36 values) | 33.12 (37 values) | All 73 recorded values below 60 s; first row blank. |
| aux_seconds | 11.35 | 14.87 | Later phase is slower. |

`n_updates` increased from 10 to 740 across 74 rows. The auxiliary KL is sometimes comparable to PPO KL (7/74 rows at least half), so reducing `aux_coef` from 1.0 to 0.3–0.5 is a possible hyperparameter-only proposal for review, not a change made or proof that it will improve play. Continue monitoring the KL and latent/value trends. Rollout slowdown is a measured caveat, not an independent frame-rate measurement.

## Limits and next milestone

This is an interim descriptive training report, not native gameplay acceptance. Checkpoint rotation prevents independent readback of the first 75k milestone files. The current run remains active; preserve its lineage and report equal bounds and post-75k growth at 150k. Baselines and old runs remain untouched. Project source/config/mod were not changed for this report.
