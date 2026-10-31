# Reward v12/schema9: final training report

**Stopped by the human October 31, 2026 at17:22:56.287075 UTC /18:22:56 CET.**
Final checkpoint **1a6d8146-s1-t173056**, **173056 /300000 saved steps**
(**126944 short**), 1032 completed episodes /173786 observed steps /
169 train rows. The300k milestone was not reached; no300k report or result is
imputed. No restart, retry or extension was performed. stop.forever remains in place.

## Authorization, identity and evidence

One Start-Pure.cmd --initialize launched October31 at06:31:15.330771 UTC /07:31CET.
Source `4c5893762692b06279747c71b58685fffa97a9db`,menu commit5627159; later commits
are reports/docs only. Contract
`1a6d8146f5e89b7bdad14fe21d3afa9cc1f5c4192b8e5f24cefb6bbab0e0c8d8`,
reward_version12,observation9/11691 inputs,action2. Manifest label pure-v11 is retained
by design; exact config hash identifies v12. Seed1,file2,RecurrentPPO,features512,
n_steps1024,batch128,epochs10,targetKL.03,gamma.998,ent.005. Door4,death-11,stall-4,
stagnation-.39 after12s,stall30. Frozen inputs were rehashed and all matched the
session plan. No source/config/mod/save/Cloud changes. Lua was not redeployed.

The finite stop was first saved>=300000 or November1 12:31:15.330771 UTC,
whichever first; the human stopped earlier. The deadline was not extended.
[Plan](2026-10-31-reward-v12-schema9-native-plan.md),
[offline verification](2026-10-31-reward-v12-offline-verification.md),
[launch](2026-10-31-reward-v12-schema9-launch.md),
[native audit](2026-10-31-reward-v12-schema9-native-audit.md),
[50k report](2026-10-31-reward-v12-schema9-50k.md),
[150k report](2026-10-31-reward-v12-schema9-150k.md).

Evidence E=reports/local/reward-v12-schema9-20261031:launch/status/result.json,
user-stop.request,final-freeze.json,archive-final.json,first-rollover.json and
supervisor session plan/menu/events/status/result. Owner result records user stop,
launcherexit0, no extra startup session. Owner stderr is empty. All77 archived v11
files were independently rehashed at terminal stop and match archive-before.json;
older archives/reports are preserved.

## Outcomes and equal-bound v11 comparison

Whole completed episodes are selected by cumulative endpoint, never split. Observed
steps include unsaved rollout tails and differ from saved-model/optimizer steps.
Episode IDs reset per session; counts use CSV rows. Missing data are not imputed.
Cumulative bounds (0,173786], recent~50k (123786,173786]. Both are within v11's
254782 observed steps, so each comparison uses identical cumulative bounds. Actual
selected episode/step denominators can differ. V11's finalsavedt253952 and1180episodes
are historical baseline evidence, not a frozen paired evaluation.

| Metric | v12 cumulative | v12 recent (123786,173786] | v11 same cumulative bounds | v11 same recent bounds |
|---|---:|---:|---:|---:|
| Episodes | 1032 | 316 | 809 | 245 |
| Actual whole-episode steps | 173786 | 50149 | 173335 | 49914 |
| Exit-start | 81.1% (837/1032) | 88.6% (280/316) | 82.8% (670/809) | 91.0% (223/245) |
| Stall share | 70.5% (728/1032) | 68.0% (215/316) | 62.2% (503/809) | 58.8% (144/245) |
| Rooms / episode | 1.891 | 1.972 | 1.936 | 1.988 |
| Stage >=2 | 0.0% (0/1032) | 0.0% (0/316) | 0.0% (0/809) | 0.0% (0/245) |
| Never-left-start / stalls | 26.8% (195/728) | 16.7% (36/215) | 27.6% (139/503) | 15.3% (22/144) |
| Stall-ended steps | 81.8% (142186/173786) | 80.9% (40561/50149) | 75.8% (131460/173335) | 75.3% (37596/49914) |
| Collectibles total; /episode; /1k steps | 29; 0.028; 0.167 | 6; 0.019; 0.120 | 36; 0.044; 0.208 | 13; 0.053; 0.260 |
| Kills /1k steps | 6.404 | 7.159 | 4.540 | 5.469 |
| Clears /1k steps | 0.903 | 0.997 | 0.750 | 0.781 |
| Stall goal hops <1 / filled stalls | 72.4% (527/728) | 66.5% (143/215) | 64.9% (325/501) | 58.0% (83/143) |
| Mean col_novelty | 0.65713 (1032/1032) | 0.41267 (316/316) | 0.83816 (809/809) | 0.47119 (245/245) |

damage_dealt_fraction /1k actual steps: 8.139, 9.084, 6.144, 7.319 (same column order).

half_hearts_lost /1k actual steps: 17.596, 20.060, 15.386, 17.450 (same column order).

At identical cumulative bounds, v12 has more stalls (70.5% vs62.2%), fewer
rooms/episode (1.891 vs1.936), higher kills/1k (6.404 vs4.540) and clears/1k
(.903 vs.750). Exit-start is81.1% vs82.8%; stage2zero in both. Recent v12
stalls68.0% vs58.8% and rooms1.972 vs1.988 retain the progression limitation.
Stall/room/progression requirements remain unmet; they were not automatic stop
rules. Shorter stall limits change episode frequency, so actual denominators matter.
Kills/clears and exit/stall/room progression must be assessed separately; reward
sums and optimizer updates do not establish gameplay superiority. One seed,
changing policies and uncontrolled layouts limit inference. Never-left-start is
rooms_visited=1 among stalls, excluding later returns; goal hops<1 is descriptive.
No extrapolation beyond available baseline steps or frozen-policy claim is made.

## Reward episode means (available/selected)

| Metric | v12 cumulative | v12 recent | v11 common cumulative | v11 common recent |
|---|---:|---:|---:|---:|
| col_enemy_damage | 6.85324 (1032/1032) | 7.20827 (316/316) | 6.58169 (809/809) | 7.45595 (245/245) |
| col_room_clear | 1.52132 (1032/1032) | 1.58228 (316/316) | 1.60692 (809/809) | 1.59184 (245/245) |
| col_room_visit | 4.45252 (1032/1032) | 4.85759 (316/316) | 4.67862 (809/809) | 4.93878 (245/245) |
| col_floor_entered | 0.00000 (1032/1032) | 0.00000 (316/316) | 0.00000 (809/809) | 0.00000 (245/245) |
| col_damage_taken | -1.48159 (1032/1032) | -1.59177 (316/316) | -1.64833 (809/809) | -1.77755 (245/245) |
| col_death | -3.24031 (1032/1032) | -3.51582 (316/316) | -3.78245 (809/809) | -4.12245 (245/245) |
| col_time | -0.17153 (1032/1032) | -0.16168 (316/316) | -0.21877 (809/809) | -0.20889 (245/245) |
| col_pickup_coin | 0.02035 (1032/1032) | 0.02089 (316/316) | 0.02522 (809/809) | 0.01837 (245/245) |
| col_pickup_bomb | 0.00339 (1032/1032) | 0.00000 (316/316) | 0.00680 (809/809) | 0.01837 (245/245) |
| col_pickup_key | 0.00630 (1032/1032) | 0.00475 (316/316) | 0.00556 (809/809) | 0.00612 (245/245) |
| col_collectible_new | 0.14050 (1032/1032) | 0.09494 (316/316) | 0.22250 (809/809) | 0.26531 (245/245) |
| col_heal | 0.01114 (1032/1032) | 0.00791 (316/316) | 0.01669 (809/809) | 0.02245 (245/245) |
| col_novelty | 0.65713 (1032/1032) | 0.41267 (316/316) | 0.83816 (809/809) | 0.47119 (245/245) |
| col_stall | -2.82171 (1032/1032) | -2.72152 (316/316) | -3.10878 (809/809) | -2.93878 (245/245) |
| col_stagnation | -5.21675 (1032/1032) | -4.91137 (316/316) | -4.87470 (809/809) | -4.54770 (245/245) |
| col_door_shaping | 1.44669 (1032/1032) | 1.46838 (316/316) | 0.88295 (809/809) | 0.86925 (245/245) |

## Optimizer statistics

Model timesteps are separate from observed episode windows.

| Metric | v12 all/common | v12 recent model~50k | v11 common recorded model bound |
|---|---:|---:|---:|
| Rows; model-step bounds | 169;1024..173056 | 49;123904..173056 | 169;1024..173056 |
| entropy_loss | -3.88767 (169/169) | -3.97827 (49/49) | -3.64233 (169/169) |
| approx_kl | 0.02993 (169/169) | 0.03115 (49/49) | 0.02980 (169/169) |
| clip_fraction | 0.14039 (169/169) | 0.11693 (49/49) | 0.14633 (169/169) |
| KL max; rows>.03 | 0.09769;61/169 | 0.09769;19/49 | 0.12731;54/169 |
| Update seconds median; range; coverage | 3.891;1.406..20.719;167/169 | 3.734;2.391..13.250;48/49 | 5.187;1.984..27.922;167/169 |
| pause_ok true/filled | 168/169 | 49/49 | 165/169 |

entropy_loss is negative entropy; timing excludes blank prior-update values.
TargetKL is an update early-stop setting, not a strict logged-value bound. Timing,
KL and pause outcomes remain descriptive; no halt guard or tuning was added.

## Native audit and rollover limits

The18-minute check passed27episodes/4trainrows:22/22 stalls had backend idle
30.000..30.188 active game seconds, col_stall=-4,fullcol_stagnation=-7.02,
learnerterminated=true/truncated=false. Novelty counts t4096 SHA matched manifest,
256keys/max21;689/783 positive start payments decayed.1035 frames,max12501bytes,
1035 numeric8 tag vectors,no audit errors. Initial file2 no-game New Run entry
was verified. These samples do not establish every unencountered item condition
or native gameplay acceptance.

First8hrollover14:30:02UTC completed normally. Last completed episode742 was stall
14:29:53UTC; previous741 died14:28:50UTC. Session2 chose and verified Continue,
resume=true,parentlatestt126976,same contract; new episodes andt128000 checkpoint
proved advancement. The death immediately before lease + positive NoGameState ->
resumed New Run case was **UNENCOUNTERED**, remains unverified and open. No forced
death or game manipulation. Initial New Run does not prove that resumed path.

## Session exits and terminal cleanup

| Session | State | Learner exit | Fault | Cleanup errors | Status writes skipped |
|---|---|---:|---|---|---:|
| 073115-0001 | completed / lease budget | 0 | null | [] | 0 |
| 153002-0002 | user_cancelled | 0 | null | [] | 0 |

The final unfinished rollout produced no extra checkpoint aftert173056. Launcher
exit0 agrees with both clean session results; no fault or cleanup error is hidden.
Read-only terminal inspection confirmed no Isaac game, training worker/wrappers,
finite owner/wrapper or Start-Pure launcher; listener9528 absent. Deployed
action_authorization.json and action_authorization.tmp absent. stop.forever retained.
No forced termination was needed; cooperative cleanup reports no error.

## Frozen artifacts and publication checks

- model.zip: `f1de153d2b7f5728001ae711eccab5b017b8500784623ed12b0098764ef60c0d`
- vecnormalize.pkl: `ee7d9eeb5e76f22d5930b01ad788fa1908e1017f84b3ad84fbf3e8bdac200694`
- novelty_counts.npz: `3d61432b47611c28eb3053775a9b03d5c885c176691ce04636bfc885f7ad3d30`
- configs\training-pure-v4.yaml: `65d3bf40563cb657367a09ac0a8e690b8fc06df4602973097bec263ab8b4e63a`
- configs\reward-v12.yaml: `e4becfd631d92406470cfdf3307acfad76501466ddff4b0501a403bf68b925d9`
- manifest.json: `d483641313a5a0b9758c8d54efdc639553c194cece6593696cc0822e47acfbf6`
- deployed main.lua: `b647b712a4dc92d7fee21ce9031d0e2ef24c058f61292d56ba2e41b9969d8c50`
- deployed metadata.xml: `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`

Offline Check1569includingLua/no skips passed before launch, with one existing
synthetic AllNaN warning. Final report/docs-only whitespace/local-link checks and
strictOpenSpec30/30 validate publication; unchanged code does not require another
fullRL gate. Pending native gameplay and conditional resumed-NewRun tasks remain
open; no OpenSpec change is archived. This is self-review, not independent review.
The monitor is deleted after publication; any further training needs a human decision.
