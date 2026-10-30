# Reward v11 / observation schema 9: approximately 50k-step milestone

Date: October 30, 2026. Snapshot captured **16:20:48 UTC / 17:20:48 CET**.
Source `3264207f54608c96d6937396cd02bba1769bb5af`, pushed before launch; no training
source/config/mod changes. Untracked unrelated tools are excluded from this report.
Contract `7c01606925675e6e7535a61ca75b26770e5aadecf8110dfc96bb251448dfcd7c`.

The first saved checkpoint at or above 50000 is **7c016069-s1-t50176**.
The snapshot contains **224 completed episodes / 49963 observed steps / 49 train rows**.
Training remains active, fault null. This is an ongoing training comparison, not a
frozen-policy evaluation or a final cleanup report.

## Scope, evidence and method

[Finite authorization and limits](2026-10-30-reward-v11-schema9-native-plan.md).
Seed 1, native file2, one fresh initialization at 13:13:00 UTC. RecurrentPPO,
11691 inputs, features512, n_steps1024, batch128, epochs10, target_kl0.03,
gamma0.998, entropy coefficient0.005. Stall terminates the learner; CSV retains
truncated/stall. Cross-run novelty is 0.1/sqrt(N), blocked_cost0.
Absolute stop remains **November 1 09:00 CET (08:00 UTC)**; minimum target300k does
not extend it. Monitoring reads files without opening/activating PC windows.

Stable evidence is local under `reports/local/reward-v11-schema9-20261030`:
`milestone-50000.json`, `milestone-50000/{episodes.csv,train.csv,manifest.json}`,
`launch.json`, `native-check.json`, `audit/`, `preflight.json`, archive receipts.
The owner copied metrics/manifest within seconds of checkpoint publication. Model, normalizer and novelty-count hashes were independently verified against
the captured manifest before publication. Models
remain under runs/pure-v4 and normal retention applies; the snapshot is evidence,
not a separately pinned model. Completed episode data exclude the ongoing tail.

The common cumulative interval is **(0,50000] observed episode steps**, starting
fresh for each lineage. Episodes are assigned by cumulative endpoint and never
split. Consequently actual whole-episode step denominators differ below; rates use
those denominators. For this first milestone the latest approximately50k interval
is the same interval. No exact matching of saved-model/optimizer steps is implied.
V9 observed steps contain unsaved tails (105104 observed vs102400 saved at its end).
Baselines: v10 archive has64430 observed steps, v9schema8 has105104. Both support
this window; neither supports an extrapolated150k/300k comparison.

## Gameplay outcomes

| Metric | v11 | v10 | v9 schema8 |
|---|---:|---:|---:|
| Completed episodes | 224 | 228 | 204 |
| Whole-episode observed steps | 49963 | 49664 | 49908 |
| Exit starting room | 70.5% (158/224) | 59.6% (136/228) | 71.1% (145/204) |
| Rooms / episode | 1.795 | 1.680 | 1.848 |
| Stall episodes | 67.0% (150/224) | 66.2% (151/228) | 70.6% (144/204) |
| Deaths | 33.0% (74/224) | 33.8% (77/228) | 29.4% (60/204) |
| Steps in stall-ended episodes | 77.3% (38604/49963) | 72.8% (36171/49664) | 80.6% (40231/49908) |
| Reached stage >=2 | 0.0% (0/224) | 0.0% (0/228) | 0.0% (0/204) |
| Never-left-start proxy among stalls | 44.0% (66/150) | 60.9% (92/151) | 41.0% (59/144) |
| Collectibles: total; /episode; /1k steps | 7; 0.031; 0.140 | 4; 0.018; 0.081 | 9; 0.044; 0.180 |
| Kills /1k steps | 2.942 | 3.322 | 3.947 |
| Room clears /1k steps | 0.500 | 0.483 | 0.601 |
| Goal hops <1 among filled stall rows | 76.7% (115/150) | 76.2% (115/151) | N/A |
| Clear-room stalls /all stalls | 91.3% (137/150) | 95.4% (144/151) | 64.6% (93/144) |
| Clear + zero open unexplored doors: /all stalls; /clear stalls | 23.3% (35/150); 25.5% (35/137) | 17.2% (26/151); 18.1% (26/144) | 30.6% (44/144); 47.3% (44/93) |

Exit-start improves over v10 by **10.9 percentage points**, but is approximately
level with v9schema8. Stall share is essentially unchanged from v10. Rooms/episode
is higher than v10 and lower than v9; kills/1k is lower than both. No episode in
these windows reached stage2. Seven collectible pickups occurred in v11 versus
four in v10 and nine in v9; a small uncontrolled sample does not establish improved
item selection. The 150k goals (>80% exit-start, <50% stalls, >2.5 rooms/episode)
are not met in this early window and are not stop rules.

The starting-room stall measure is a proxy: rooms_visited=1 means the episode never
left its starting room. It does not count episodes that returned there later.
Goal-hops evidence is available for150/150 v11 and151/151 v10 stalls; v9 is N/A.
Goal hops<1 alone does not prove a clear room or an open unexplored door. The dead-end
proxy is clear room AND zero open unexplored doors; it is descriptive, not proof of
an unavoidable dead end. Missing historical fields are not imputed.

## Reward columns (episode means)

| Column | v11 (224 episodes) | v10 (228) | v9 schema8 (204) |
|---|---:|---:|---:|
| col_enemy_damage | 4.70083 | 5.05543 | 6.32316 |
| col_room_clear | 1.11607 | 1.05263 | 1.47059 |
| col_room_visit | 3.97321 | 3.39912 | 4.24020 |
| col_floor_entered | 0.00000 | 0.00000 | 0.00000 |
| col_damage_taken | -1.48661 | -1.44298 | -1.38971 |
| col_death | -3.30357 | -3.37719 | -2.94118 |
| col_time | -0.22788 | -0.22524 | -0.25384 |
| col_pickup_coin | 0.01741 | 0.00921 | 0.00882 |
| col_pickup_bomb | 0.00000 | 0.00439 | 0.04902 |
| col_pickup_key | 0.00446 | 0.00877 | 0.00735 |
| col_collectible_new | 0.15625 | 0.08772 | 0.22059 |
| col_heal | 0.00670 | 0.00877 | 0.01471 |
| col_novelty | 1.37896 | 4.12105 | 4.56225 |
| col_stall | -3.34821 | -3.31140 | -3.52941 |
| col_stagnation | -5.33304 | -5.49452 | -5.54306 |
| col_door_shaping | 0.84821 | 0.91934 | 0.58871 |

Mean col_novelty is lower under cross-run decay, as designed. Reward means are
not interchangeable gameplay scores between reward contracts.

## Optimizer and pause measurements

Train comparison uses recorded model timesteps **1024..49152** (48 rows per run),
separate from the observed episode interval. Historical missing statistics stay
missing. Values below are means over available rows unless specified.

| Measurement | v11 | v10 | v9 schema8 |
|---|---:|---:|---:|
| entropy_loss (negative entropy) | -3.67591 (48/48 rows) | -3.72250 (48/48 rows) | -3.76233 (32/48 rows) |
| approx_kl | 0.02425 (48/48 rows) | 0.00692 (48/48 rows) | 0.00832 (32/48 rows) |
| clip_fraction | 0.15594 (48/48 rows) | 0.04009 (48/48 rows) | 0.05443 (32/48 rows) |
| Maximum approx_kl | 0.05575 | 0.01605 | 0.02263 |
| pause_ok measured rows | 93.8% (45/48) | 100.0% (48/48) | 97.0% (32/33) |
| Median update_seconds | 8.406 s (47/48 rows) | 7.687 s (47/48 rows) | 7.610 s (44/48 rows) |

At the actual t50176 snapshot there are49 train rows: entropy_loss mean-3.67145,
approx_kl mean0.02409/max0.05575, clip_fraction mean0.15655;10/49 approx_kl values
exceed0.03. The configured target_kl is an early-stop setting, not a strict bound on
reported values. Update times are below the rough25..35s expectation; pause_seconds
includes checkpoint/idle overhead and update_seconds is associated with the prior
update, with the first row blank. These are observations, not reasons to stop or
tune the run. Pause failures alone do not stop training. Optimizer statistics and
rewards do not establish improved native gameplay.

## Native audit and integrity

| Check | Status | Evidence / limit |
|---|---|---|
| Full offline Check.ps1 | passed | 1543 tests including Lua, no skips; lint/format/mypy/dependencies; existing synthetic AllNaN warning |
| Strict OpenSpec | passed | 28/28 before launch; report-only validation repeated at publication |
| V10 preservation | passed | All32 files hashed before and after move; final3043a54c-s1-t63488,290 episodes |
| Deployment / contract | passed | preflight.json; source/deployed bytes matched; exact contract above |
| 18-minute owner audit | passed for encountered cases | 1039 snapshots;3/3 pedestal samples;232 other pickups clean; max19784 bytes; all tag vectors length8 |
| Independent follow-up | passed for encountered cases | 1222 snapshots;3/3 samples of ONE item509 (familiar, quality1, tags0, charges0);396 other pickups omit item fields; max19877 bytes |
| Novelty persistence | passed in sampled checkpoint | t5120 counts hash matched;356 keys, max count17;601 decayed starting-room payments |
| Stall learner flags | passed in sampled transitions | 14/14 stalls terminated=true/truncated=false; CSV remains truncated/stall |
| Active / nonzero transformation tags / Blind | not_run natively | Not encountered in bounded audit; no fallback/API acceptance claim |
| Frozen evaluation | not_run | Ongoing training, not held-out evaluation |
| Final cleanup | not_run | Training active under fixed deadline |

Owner audit first3 starting-room novelty sums were3.200,3.949,3.475; last3 completed
sums0.460,2.131,0.524. Different paths/exposure mean these are descriptive; lower
repeat-cell payments and persisted counts support the decay mechanism. No full
item API/Blind acceptance follows from one familiar with zero tags.
Deployed Lua SHA256: b647b712a4dc92d7fee21ce9031d0e2ef24c058f61292d56ba2e41b9969d8c50.
Metadata SHA256: 00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997.

## Limits and continuation

One seed and changing policies, uncontrolled native layouts, no confidence claim,
no frozen comparison. Runtime audit coverage does not close all OpenSpec native
requirements; tasks remain open. Continue unchanged toward150k/300k under the same
absolute deadline and fault/disk limits. Stop on faults; no manual retry. Self-review
and document/link/whitespace/strict-spec checks are not independent review.
