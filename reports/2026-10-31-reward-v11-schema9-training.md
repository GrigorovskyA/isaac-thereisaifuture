# Reward v11 / observation schema 9: final training report

Actual end: **October 31, 2026, 05:11:30 UTC / 06:11:30 CET**, before the authorized
November1 08:00 UTC / 09:00 CET deadline. Reason: **training startup fault during
automatic lease rollover**. Training remains stopped; no manual retry, fallback
New Run, source/config/mod/save/Cloud change or deadline extension was performed.

Final checkpoint **7c016069-s1-t253952** reached **253952/300000 saved steps
(84.65%; 46048 short)**. There are **1180 completed episodes / 254782 observed
steps / 248 train rows**. The300k milestone was not reached and has no report.
The launcher exited0, but two startup sessions faulted with learner exit1 and
cleanup errors; this is not a clean successful completion.

## Authority, configuration and evidence

[Finite launch/audit plan](2026-10-30-reward-v11-schema9-native-plan.md),
[50k report](2026-10-30-reward-v11-schema9-50k.md),
[150k report](2026-10-30-reward-v11-schema9-150k.md).
Source `3264207f54608c96d6937396cd02bba1769bb5af`; later5a9d940/d438e05 commits
changed reports/docs only. Source/config/mod diff against3264207 is empty.
Contract `7c01606925675e6e7535a61ca75b26770e5aadecf8110dfc96bb251448dfcd7c`:
observation9/11691 inputs, action2, reward pure-v11. Seed1, native save file2,
RecurrentPPO, features512, n_steps1024, batch128, epochs10, target_kl0.03,
gamma0.998, ent_coef0.005. Cross-run novelty counts persist; stall transitions
terminate the learner while CSV summaries retain truncated/stall.

The one authorized `Start-Pure.cmd --initialize` launch occurred October30 at
13:13:00.340078 UTC; total elapsed time to owner completion was15h58m30s. The finite owner scheduled the fixed deadline before training;
fault monitoring wrote stop.forever earlier. Minimum300k never overrode the deadline.
No new experiment, manual retry or initialization was authorized by this failure.

Local evidence root: `reports/local/reward-v11-schema9-20261030` (E).
Authority: launch.json, result.json/status.json, fault-stop.json, training.log,
owner.stderr, native-check.json and every supervisor session's plan/events/result.
Terminal metrics/manifest copies are in E/final; hashes are in E/final-integrity.json.
No models, raw logs or local receipts are committed.

## All session outcomes

| Session suffix | End UTC | Final checkpoint | State / learner exit | Fault | Cleanup errors | Skipped status writes |
|---|---|---|---|---|---|---|
| 0001 | 10-30 21:11:48 | 7c016069-s1-t128000 | completed / 0 | null | [] | 0 |
| 0002 | 10-31 05:10:35 | 7c016069-s1-t253952 | completed / 0 | null | [] | 0 |
| 0003 | 10-31 05:11:14 | 7c016069-s1-t253952 | fault / 1 | MenuEntryError: Existing file2 game state not confirmed; no New Run fallback | worker: RuntimeError: Owned worker required termination; cooperative release unverified | 0 |
| 0004 | 10-31 05:11:30 | 7c016069-s1-t253952 | fault / 1 | null | worker: RuntimeError: Owned worker required termination; cooperative release unverified | 0 |

Sessions1/2 each exhausted their normal finite wall-time lease and exited0 with
fault=null/cleanup=[]; the same lineage resumed automatically. Session3 could not
confirm an existing file2 game state: `MenuEntryError: Existing file2 game state
not confirmed; no New Run fallback`. Its bounded console/menu logs show the
ordinary guarded Continue attempt and observer waiting, not successful gameplay.
The exact cause of the missing confirmation is unverified; no save reset or
fallback was attempted.

An automatic session4 began before the owner stop was observed. It made no new
checkpoint or completed episode, then ended with reason `User cancellation
requested`. That label came from the stop-file path; there was no new human stop
request. The owner recorded `training fault`, the supervisor stopped on stop file,
and its consecutive_faults count is2. Sessions3/4 required owned-worker termination:
**cooperative input release remains unverified**. Launcher exit0 does not erase
these faults or cleanup errors. No manual retry followed.

## Final gameplay outcomes

Cumulative observed bounds are (0,254782]; the recent approximately50k bounds are
(204782,254782]. Whole episodes are assigned by cumulative endpoint without splitting;
rates use actual selected whole-episode steps below. Observed steps include unsaved
rollout tails, including those at lease boundaries; they are not exact saved-model
or optimizer steps. Episode IDs reset per session, so denominators count CSV rows.

| Metric | v11 cumulative (0,254782] | v11 recent (204782,254782] |
|---|---:|---:|
| Episodes | 1180 | 211 |
| Actual whole-episode steps | 254782 | 50144 |
| Exit-start | 84.6% (998/1180) | 88.6% (187/211) |
| Stall share | 64.0% (755/1180) | 72.5% (153/211) |
| Rooms / episode | 1.964 | 2.033 |
| Stage >=2 | 0.0% (0/1180) | 0.0% (0/211) |
| Never-left-start / stalls | 24.1% (182/755) | 15.7% (24/153) |
| Stall-ended steps | 78.3% (199473/254782) | 87.7% (43988/50144) |
| Collectibles total; /episode; /1k steps | 64; 0.054; 0.251 | 13; 0.062; 0.259 |
| Kills /1k steps | 4.843 | 4.986 |
| Clears /1k steps | 0.793 | 0.858 |
| Stall goal hops <1 / filled stalls | 63.5% (478/753) | 64.7% (99/153) |
| Mean col_novelty | 0.69503 (1180/1180) | 0.38302 (211/211) |

The150k exit-start goal was met (81.9%), but the combined150k requirement was not:
stalls61.9%, rooms1.931. Those measured requirements were not stop rules.
No frozen-policy or full native gameplay acceptance follows from training metrics.
The never-left-start proxy is rooms_visited=1 among stalls, excluding later returns.
Goal hops<1 alone does not prove a clear room with an open unexplored door.

Recent stall share rose to72.5%, compared with55.0% in the150k report's recent
window. Exit-start remains high, but room visitation is about2 per episode and no
stage2 occurred. Leaving the start more reliably has not resolved stagnation or
established progression. The64 collectible pickups do not establish item-selection
quality in this uncontrolled sample.

## Baselines and equal observed bounds

V10 supports64430 observed steps (290 episodes/62 train rows, saved t63488), v9
schema8 supports105104 (443/100, saved t102400). Neither supports the final
cumulative or recent50k bounds: both are **N/A** there. No extrapolation is made.
These pairwise tables use identical cumulative bounds with whole episodes.

### Common observed bound (0,64430]

| Metric | v11 | v10 |
|---|---:|---:|
| Episodes | 288 | 290 |
| Actual whole-episode steps | 64424 | 64430 |
| Exit-start | 74.0% (213/288) | 61.7% (179/290) |
| Stall share | 66.7% (192/288) | 65.9% (191/290) |
| Rooms / episode | 1.868 | 1.710 |
| Stage >=2 | 0.0% (0/288) | 0.0% (0/290) |
| Never-left-start / stalls | 39.1% (75/192) | 58.1% (111/191) |
| Stall-ended steps | 78.2% (50365/64424) | 72.3% (46576/64430) |
| Collectibles total; /episode; /1k steps | 9; 0.031; 0.140 | 5; 0.017; 0.078 |
| Kills /1k steps | 3.881 | 3.228 |
| Clears /1k steps | 0.667 | 0.435 |
| Stall goal hops <1 / filled stalls | 70.8% (136/192) | 73.3% (140/191) |
| Mean col_novelty | 1.31252 (288/288) | 4.02138 (290/290) |

### Common observed bound (0,105104]

| Metric | v11 | v9 |
|---|---:|---:|
| Episodes | 475 | 443 |
| Actual whole-episode steps | 104959 | 105104 |
| Exit-start | 77.3% (367/475) | 71.8% (318/443) |
| Stall share | 65.7% (312/475) | 70.9% (314/443) |
| Rooms / episode | 1.897 | 1.831 |
| Stage >=2 | 0.0% (0/475) | 0.0% (0/443) |
| Never-left-start / stalls | 34.6% (108/312) | 39.8% (125/314) |
| Stall-ended steps | 77.4% (81256/104959) | 80.3% (84369/105104) |
| Collectibles total; /episode; /1k steps | 21; 0.044; 0.200 | 17; 0.038; 0.162 |
| Kills /1k steps | 3.859 | 3.368 |
| Clears /1k steps | 0.715 | 0.599 |
| Stall goal hops <1 / filled stalls | 67.3% (210/312) | N/A |
| Mean col_novelty | 1.07828 (475/475) | 4.09391 (443/443) |

At the supported v10 bound, exit-start/rooms improve but stall share is essentially
unchanged. At the supported v9 bound, exit-start improves and stall share falls.
These are one-seed, changing-policy, uncontrolled-layout training comparisons,
not causal isolation or held-out frozen evaluation. Historic missing fields remain
N/A; the v9 final fault/forced cleanup and earlier failed v10 startup remain
preserved in their original reports.

## Reward column means

| Metric | v11 cumulative (1180 episodes) | v11 recent |
|---|---:|---:|
| col_enemy_damage | 6.85649 (1180/1180) | 7.29974 (211/211) |
| col_room_clear | 1.71186 (1180/1180) | 2.03791 (211/211) |
| col_room_visit | 4.82203 (1180/1180) | 5.16588 (211/211) |
| col_floor_entered | 0.00000 (1180/1180) | 0.00000 (211/211) |
| col_damage_taken | -1.66525 (1180/1180) | -1.59953 (211/211) |
| col_death | -3.60169 (1180/1180) | -2.74882 (211/211) |
| col_time | -0.22023 (1180/1180) | -0.24179 (211/211) |
| col_pickup_coin | 0.02085 (1180/1180) | 0.00711 (211/211) |
| col_pickup_bomb | 0.00508 (1180/1180) | 0.00000 (211/211) |
| col_pickup_key | 0.00636 (1180/1180) | 0.00711 (211/211) |
| col_collectible_new | 0.27119 (1180/1180) | 0.30806 (211/211) |
| col_heal | 0.02161 (1180/1180) | 0.02370 (211/211) |
| col_novelty | 0.69503 (1180/1180) | 0.38302 (211/211) |
| col_stall | -3.19915 (1180/1180) | -3.62559 (211/211) |
| col_stagnation | -4.95630 (1180/1180) | -5.33741 (211/211) |
| col_door_shaping | 0.89594 (1180/1180) | 0.94195 (211/211) |

Reward magnitudes differ across contracts and are not gameplay scores.

## Optimizer statistics

Recorded model-step intervals are separate from observed episode windows.

| Metric | v11 cumulative | v11 recent model interval (203952,253952] |
|---|---:|---:|
| Train rows; model-step range | 248; 1024..253952 | 49; 204800..253952 |
| entropy_loss (negative entropy) | -3.62227 (248/248) | -3.58016 (49/49) |
| approx_kl | 0.03038 (248/248) | 0.03074 (49/49) |
| clip_fraction | 0.14898 (248/248) | 0.16208 (49/49) |
| KL max; values >0.03 | 0.12731; 90/248 | 0.07781; 20/49 |
| Update seconds median; range; rows | 5.781; 1.984..29.157; 246/248 | 7.312; 2.812..23.375; 49/49 |
| pause_ok true / measured | 244/248 | 49/49 |

Target KL is an update early-stop setting, not a strict logged-value bound.
Timing/KL and pause outcomes were descriptive, not automatic stop rules. No pause
percentage guard or tuning was introduced. Initial/prior-update timing blanks are
excluded with explicit row denominators. Equal-model-bound baseline optimizer
tables at63488/102400 are retained in the150k report; no final-step baseline exists.

## Verification, preservation and cleanup

| Check | Status | Evidence / limit |
|---|---|---|
| Full Windows offline gate | passed before launch | 1543 tests including isolated Lua, no skips; existing synthetic AllNaN warning |
| Strict OpenSpec | passed | 28/28 before launch and repeated for final docs |
| Initial owner18-minute audit | passed for encountered cases | 1039 snapshots,3/3 plausible pedestal samples,232 other pickups clean,all tag counts length8,max19784 bytes |
| Independent follow-up | passed for encountered cases | 1222 samples,3/3 samples of ONE familiar item509 quality1/tags0/charges0,396 other pickups clean,max19877 bytes |
| Novelty persistence / stall flags | passed in sampled evidence | t5120 counts hash valid,356 keys/max17;601 decayed starting-room payments;14/14 learner stall flags terminal |
| Active/nonzero transformation tags/Blind | not_run in bounded initial audit | Positive native scenarios unverified; no full item API acceptance |
| Final checkpoint integrity | passed | Model/normalizer/counts match manifest; frozen hash receipt E/final-integrity.json |
| V10 archive | passed | All32 files rehashed against before/after receipts at terminal audit; hashes unchanged |
| Processes at terminal audit | passed for actual absence | No Isaac, training worker, finite owner or Start-Pure process |
| Listener9528 / deployed approval | passed for actual absence | No listener, action_authorization.json or action_authorization.tmp; recursive mod-directory check |
| stop.forever | passed | Present and retained |
| Cooperative input release | unverified | Sessions3/4 required worker termination; actual absence does not establish prior release |
| Frozen policy evaluation | not_run | No superiority or Dead God/progression acceptance claimed |

Terminal read-only process/listener/approval checks occurred October31 at about
05:27-05:29 UTC, with readback in E/final-cleanup.json. The owner and wrapper had exited; no remaining session could advance.
owner.stderr is empty; no owner-error.json exists. All four session results were
reviewed, including cleanup errors and zero skipped-status counts. No live game
window was opened or activated by monitoring.

V10 final model SHA256:
`61488c8a722b3857216e74df50971d1843769bb6ad2031e602e26d367f8ef652`;
normalizer `ef2c0c0761b67552c7490305e06c4004b7f4764dcead4d5597d1f6f284a9b4c4`.
All older lineages, failed v10 startup archive and reports remain preserved.

Final SHA256 freeze (source revision above; paths in E/final-integrity.json):

- model.zip: `610fca8489024ae2f9d2f83cb17cc426ba35ea4ccac4bd32b02dfad5ac24dd30`
- vecnormalize.pkl: `3f61ef651f5a96014af9f305c64411ffd0370810e2f4e9053bcade80a1a8ba5e`
- novelty_counts.npz: `e984fed0d67de6444c5f39ca7cc8a960f3cfe4d25f450d10133d65f828a0783e`
- manifest.json: `f8d1fe5770faab9640549838904c8faf5d5d85079ee8f33fda1678bfc1e69fce`
- training-pure-v4.yaml: `1a451ac1458b68541272df4b1fa8f5ba727d685e2af1fa43dde9cbe60593e411`
- reward-v11.yaml: `429210016d1aff0d05a4a396bedd92cb74baa23930b071b2fd99e818e037eebd`
- main.lua: `b647b712a4dc92d7fee21ce9031d0e2ef24c058f61292d56ba2e41b9969d8c50`
- metadata.xml: `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`

## Limits and handoff

The authorized finite attempt is finished early on a startup fault. Keep stopped
with stop.forever; no retry, repair, new initialization or extension. Native tasks
remain open and no OpenSpec change is archived. Saved253952 steps are46048 short
of300000; no300k success is claimed. The historical native positive-case gaps and
cooperative-release uncertainty remain explicit.

Only reports/docs are published. Whitespace/local Markdown links and strict
OpenSpec validation are the final checks; unchanged training code does not require
another live/full RL test. This is self-review, not independent review. The recurring
monitor is deleted after this final handoff; further training needs a human decision.

Final publication checks passed: git diff --check, local Markdown links, unchanged
config contract, and `scripts/OpenSpec.ps1 validate --all --strict` (exit0,28/28).
