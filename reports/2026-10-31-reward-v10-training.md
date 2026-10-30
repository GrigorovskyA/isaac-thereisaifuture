# Reward v10 training: user-requested stop

Actual date: October 30, 2026. Authorized initialized launch 2026-10-30T08:22:44.587539+00:00; user stop completed 2026-10-30T12:26:04.036725+00:00 (13:26:04 CET). The planned October 31 09:00 CET deadline was superseded by the human stop request.

Final checkpoint: **3043a54c-s1-t63488**, 63488 saved model steps. **290 completed episodes**, 64430 completed-episode steps. Unfinished rollout work after that checkpoint was not saved as a new checkpoint. No further training or reward-v11 initialization was launched.

## Identity and offline checks

- Source `af432a374064dab6a3ce21a89b0927ad2792a353`, pushed with the requested reward-v10 commit. Python3.12.14, native Windows; file2/Isaac, seed1, train split, uncontrolled native room trajectories.
- Contract `3043a54c9d56e402f4a2bb6bd96906e79ee6ae3d7cc272a834d13ac13e31f621`; observation8/9762, action2/pure-v10, features512/n_steps1024/batch256/gamma0.998/entropy0.005/stall40. Config/mod unchanged during training.
- Windows Check.ps1: **1466 passed, no skips**, including isolated Lua5.3. Lint, format, mypy and pip check passed; strict OpenSpec26/26. One existing synthetic All-NaN warning. No unchanged full-suite rerun for this report.
- Lua SHA256 `1bf9402f50d99b96d6e148ed2f0a3c59cad564398eb827bbaee061865b3513cd`; metadata `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.
- V9 schema8 is preserved at `runs/pure-v4-reward-v9-schema8`, final t102400;443 episodes/100 train rows. Post-move model/normalizer/metrics hashes were verified and remained unchanged at final inspection. There was no pre-move hash receipt; the new code intentionally refuses old v9 manifests.
- Bounds: original absolute deadline October 31 08:00 UTC, native lease28740s, disk20,480,000,000 bytes; death/stall restarts allowed. Pause failures alone were not a stop condition. Foreground was left to the guarded native game keyboard; monitoring read files only.

## Startup attempts and final session

| Session | State | Learner exit | Fault | Cleanup | Skipped status writes |
| --- | --- | ---: | --- | --- | ---: |
| session-20261030-091653-0001 | fault | 1 | MenuEntryError: Existing file2 game state not confirmed; no New Run fallback | ['worker: RuntimeError: Owned worker required termination; cooperative release unverified'] | 0 |
| session-20261030-091730-0002 | fault | 1 | None | ['worker: RuntimeError: Owned worker required termination; cooperative release unverified'] | 0 |
| session-20261030-092245-0001 | user_cancelled | 0 | None | [] | 0 |

The first Continue-only launch failed before learning: existing file2 game state was not confirmed; no New Run fallback was taken. The built-in supervisor opened a second startup before the fault guard stopped it. Both startup workers needed termination; cooperative release in those attempts was unverified. Neither produced a checkpoint or episode. Failed root: `runs/pure-v4-reward-v10-startup-failed-20261030`.

The human then explicitly requested a new game. A bounded native New Run selected file2, verified New mode/slot2 and Isaac character0 in three bridge snapshots, and closed normally to preserve Continue. The later authorized initialized launch is the one that trained; its final session exited0, fault=null, cleanup_errors=[], status_writes_skipped=0.

Post-stop inspection confirmed no game, training worker, finite owner, Start-Pure or port9528 listener; deployed action_authorization.json and its temporary file are absent. stop.forever and user-stop.request remain. Frozen source/config/deployed hashes match the session plans. A separately started read-only dashboard remains; it is not a training process. The successful final cleanup does not retroactively clear the earlier startup errors.

## Native graph-label verification

The owner's 15-minute check at 2026-10-30T08:37:44.680062+00:00 passed: 858 samples; nonnegative door targets 2502/2502; matches to visible snapshot map entries 2357/2502; ordinary-room nonnegative room_grid 747/747; nonzero shaping 17/17 completed episodes; stall_goal_hops 11/11 stalls. Max snapshot 17439 bytes.

Independent followup at 08:39 UTC:953 samples,2749 valid targets,2604 map matches,842/842 normal room indexes valid. There were 45 locked-door samples and 0 usable=true violations. Nonzero shaping19/19 episodes and stall_goal_hops13/13 stalls; all4 measured pauses succeeded. This verification was notified once.

Targets absent from the visible minimap are not proved invalid; oracle doors can name undisplayed rooms. Not all secret-door variants were independently encountered. The passive audit sampled once/second for the first 20 min per worker, capped 32 MiB, preserving decoder outputs and policy inputs. Deployed transport cap131072 bytes; the OpenSpec task still names49152. This sample does not establish a universal size bound or complete native acceptance.

## Comparison method

These are descriptive training trajectories, not paired/frozen evaluations. Assign each complete episode to the window containing its cumulative episode-step endpoint, starting from fresh zero. Do not split boundary episodes. Rates divide by all steps in the selected complete episodes, so actual denominators differ slightly between runs. Compare identical cumulative bounds only up to the smaller observed total; v9 ends at105104 observed steps, checkpoint102400. V10 observed and saved model steps also differ because unfinished tails are not all checkpointed. These are not exact matched optimizer/checkpoint-step exposures. Missing historical stall context is excluded, not imputed; means carry available denominators.

| Cumulative bounds | Reward | Episodes | Episode steps | Exit start | Rooms/episode | Kills/1k | Clears/1k | Stage>=2 | Stalls | Deaths | Stalled-step share | Door shaping mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0-30000 | v10 | 134 | 29864 | 77/134 (57.5%) | 1.6791 (n=134) | 3.415 | 0.569 | 0/134 (0.0%) | 91/134 (67.9%) | 43/134 (32.1%) | 22059/29864 (73.9%) | 0.9511 (n=134) |
| 0-30000 | v9 schema8 | 119 | 29940 | 77/119 (64.7%) | 1.7983 (n=119) | 3.407 | 0.668 | 0/119 (0.0%) | 88/119 (73.9%) | 31/119 (26.1%) | 24995/29940 (83.5%) | 0.6166 (n=119) |
| 30000-60000 | v10 | 137 | 29968 | 89/137 (65.0%) | 1.7153 (n=137) | 3.103 | 0.300 | 0/137 (0.0%) | 88/137 (64.2%) | 49/137 (35.8%) | 21246/29968 (70.9%) | 0.9402 (n=137) |
| 30000-60000 | v9 schema8 | 133 | 29951 | 105/133 (78.9%) | 1.8797 (n=133) | 4.407 | 0.467 | 0/133 (0.0%) | 87/133 (65.4%) | 46/133 (34.6%) | 23064/29951 (77.0%) | 0.5468 (n=133) |
| 60000-64430 | v10 | 19 | 4598 | 13/19 (68.4%) | 1.8947 (n=19) | 2.827 | 0.435 | 0/19 (0.0%) | 12/19 (63.2%) | 7/19 (36.8%) | 3271/4598 (71.1%) | 1.1123 (n=19) |
| 60000-64430 | v9 schema8 | 16 | 4473 | 11/16 (68.8%) | 1.8125 (n=16) | 1.118 | 0.224 | 0/16 (0.0%) | 12/16 (75.0%) | 4/16 (25.0%) | 3749/4473 (83.8%) | 0.5629 (n=16) |

## Cleared stalls and dead-end proxy

Exit-start means rooms_visited>1. Dead-end proxy means stall_room_clear=1 AND stall_open_unexplored_doors=0; it does not prove that every possible route is inaccessible.

| Bounds | Reward | Known context / all stalls | Cleared / known stalls | Dead ends / door-known stalls | Dead ends / door-known clear stalls |
| --- | --- | ---: | ---: | ---: | ---: |
| 0-30000 | v10 | 91/91 (100.0%) | 86/91 (94.5%) | 14/91 (15.4%) | 14/86 (16.3%) |
| 0-30000 | v9 schema8 | 44/88 (50.0%) | 43/44 (97.7%) | 19/44 (43.2%) | 19/43 (44.2%) |
| 30000-60000 | v10 | 88/88 (100.0%) | 81/88 (92.0%) | 18/88 (20.5%) | 18/81 (22.2%) |
| 30000-60000 | v9 schema8 | 87/87 (100.0%) | 78/87 (89.7%) | 36/87 (41.4%) | 36/78 (46.2%) |
| 60000-64430 | v10 | 12/12 (100.0%) | 12/12 (100.0%) | 4/12 (33.3%) | 4/12 (33.3%) |
| 60000-64430 | v9 schema8 | 12/12 (100.0%) | 11/12 (91.7%) | 5/12 (41.7%) | 5/11 (45.5%) |

## stall_goal_hops distribution

Filled 191/191 stalled episodes; blank 0. V9 has no such column: N/A, not zero. This metric includes the in-room distance share plus target hops, rather than an integer graph distance.

| Hops term | Episodes / filled |
| --- | ---: |
| 0 <= x < 1 | 140/191 (73.3%) |
| 1 <= x < 2 | 50/191 (26.2%) |
| 2 <= x < 3 | 1/191 (0.5%) |
| 3 <= x < 4 | 0/191 (0.0%) |
| 4 <= x < 5 | 0/191 (0.0%) |
| 5 <= x <= 6 | 0/191 (0.0%) |

Min 0.05; median 0.40; mean 0.6103; max 2.99.

## Reward component means per completed episode

| Component | 0-30000 | 30000-60000 | 60000-64430 |
| --- | ---: | ---: | ---: |
| col_enemy_damage | 4.9553 (n=134) | 5.1018 (n=137) | 4.3443 (n=19) |
| col_room_clear | 1.2687 (n=134) | 0.6569 (n=137) | 1.0526 (n=19) |
| col_room_visit | 3.3955 (n=134) | 3.5766 (n=137) | 4.4737 (n=19) |
| col_floor_entered | 0.0000 (n=134) | 0.0000 (n=137) | 0.0000 (n=19) |
| col_damage_taken | -1.4142 (n=134) | -1.5073 (n=137) | -1.5789 (n=19) |
| col_death | -3.2090 (n=134) | -3.5766 (n=137) | -3.6842 (n=19) |
| col_time | -0.2305 (n=134) | -0.2264 (n=137) | -0.2514 (n=19) |
| col_pickup_coin | 0.0134 (n=134) | 0.0044 (n=137) | 0.0000 (n=19) |
| col_pickup_bomb | 0.0075 (n=134) | 0.0000 (n=137) | 0.1053 (n=19) |
| col_pickup_key | 0.0037 (n=134) | 0.0109 (n=137) | 0.0000 (n=19) |
| col_collectible_new | 0.1119 (n=134) | 0.0365 (n=137) | 0.2632 (n=19) |
| col_heal | 0.0149 (n=134) | 0.0000 (n=137) | 0.0000 (n=19) |
| col_novelty | 4.3119 (n=134) | 3.7562 (n=137) | 3.8842 (n=19) |
| col_stall | -3.3955 (n=134) | -3.2117 (n=137) | -3.1579 (n=19) |
| col_stagnation | -5.6123 (n=134) | -5.4808 (n=137) | -5.2399 (n=19) |
| col_door_shaping | 0.9511 (n=134) | 0.9402 (n=137) | 1.1123 (n=19) |

## Optimizer and pause recording

Train rows 62; measured pause success 61/62 (98.4%). Pause was not disabled. One update_pause_skipped and one update_resume_failed event named loss of game focus during menu input; training continued under the authorized best-effort pause policy. This was not a terminal training fault.

| Statistic | Filled / rows | First | Last | Mean |
| --- | ---: | ---: | ---: | ---: |
| entropy_loss | 62/62 | -3.805284321308136 | -3.280506744980812 | -3.6691 (n=62) |
| explained_variance | 62/62 | 0.013358891010284424 | 0.7025629281997681 | 0.4928 (n=62) |

## Limits and evidence

Native graph-door tasks 2.2/2.3 remain open. No 100k comparison was reached, no frozen evaluation was run, and no gameplay-improvement or optimal-policy claim follows from this report. Future reward-v11 work was mentioned by the human but is not launched or implemented here. Save/Cloud and launch options were not edited. Self-review only.

Local receipts: reports/local/reward-v10-newgame-20261030/{launch,result,oracle-check,new-game-preparation,archive-receipt,final-inspection}.json, oracle/*.jsonl, per-session plans/results/events and metrics; first startup evidence remains in reports/local/reward-v10-20261030. Raw logs, models, approvals, local helpers and unrelated tools/ are excluded from Git.

Final documentation whitespace and local-link checks passed; strict OpenSpec validation passed 26/26. [Native plan](2026-10-30-reward-v10-native-plan.md).
