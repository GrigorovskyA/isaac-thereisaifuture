# Reward v12/schema9:50k-step training milestone

October31,2026. First saved checkpoint>=50000: **1a6d8146-s1-t50176**.
Owner snapshot captured **09:40:39.788507UTC /10:40:39CET**:50176 saved model steps,
**296 completed episodes /50127 observed episode steps /48 train rows**.
Training remains active, fault=null; game34956,worker26124 andfinite owner30588
were present with fresh checkpoint/episode advancement at the09:48UTC check.

## Scope and evidence

Source `4c5893762692b06279747c71b58685fffa97a9db` remains frozen; later05c8fa5/be501bc
are report/docs commits. Untracked tools are excluded. Exact contract
`1a6d8146f5e89b7bdad14fe21d3afa9cc1f5c4192b8e5f24cefb6bbab0e0c8d8`;
reward_version12,obs9/11691 inputs,action2. Manifest reward_contract remains pure-v11
by design: use exact config hash to distinguish lineages.
Seed1,native file2,RecurrentPPO,features512,n_steps1024,batch128,epochs10,targetKL.03,
gamma.998,ent.005. Door4,death-11,stall-4,stagnation-.39 after12s,stall30.
One initialization October31 at06:31:15UTC; no source/config/mod/save/Cloud edits.

[Finite plan](2026-10-31-reward-v12-schema9-native-plan.md),
[launch receipt](2026-10-31-reward-v12-schema9-launch.md),
[native audit](2026-10-31-reward-v12-schema9-native-audit.md),
[offline verification](2026-10-31-reward-v12-offline-verification.md).
Stop at firstsaved>=300000 or November1 12:31:15.330771UTC /13:31CET,whicheverfirst;
any infrastructure fault/required audit failure stops. No manualretry/extension.

Evidence E=reports/local/reward-v12-schema9-20261031:milestone-50000.json and
milestone-50000/{episodes.csv,train.csv,manifest.json}. Owner receipt includes
verified model/normalizer/counts SHA256; a separate read before publication matched
all three against the captured manifest. Normal retention applies; the metrics
snapshot does not separately pin model files. Baseline archive
runs/pure-v4-reward-v11-schema9 has1180episodes/254782observedsteps/248trainrows,
finalsavedt253952; all77file hashes matched before/after moving at launch.

## Method and gameplay

Cumulative v12 snapshot bounds are (0,50127]. Its latest approximately50k window is
the same initial window. Baseline comparison uses **identical cumulative bounds
(0,50000]** for both lineages. Whole episodes are assigned by cumulative endpoint,
never split; actual whole-episode denominators below differ and rates use them.
Observedsteps include unsaved episode/rollout tails and are not exact saved-model
or optimizer steps. No missing fields are imputed. Both baselines started fromzero.

| Metric | v12 cumulative/latest~50k (0,50127] | v12 common (0,50000] | v11 common (0,50000] |
|---|---:|---:|---:|
| Episodes | 296 | 295 | 224 |
| Actual whole-episode steps | 50127 | 49978 | 49963 |
| Exit-start | 64.2% (190/296) | 64.4% (190/295) | 70.5% (158/224) |
| Stall share | 74.0% (219/296) | 73.9% (218/295) | 67.0% (150/224) |
| Rooms / episode | 1.689 | 1.692 | 1.795 |
| Stage >=2 | 0.0% (0/296) | 0.0% (0/295) | 0.0% (0/224) |
| Never-left-start / stalls | 48.4% (106/219) | 48.2% (105/218) | 44.0% (66/150) |
| Stall-ended steps | 82.7% (41471/50127) | 82.7% (41322/49978) | 77.3% (38604/49963) |
| Collectibles total; /episode; /1k steps | 7; 0.024; 0.140 | 7; 0.024; 0.140 | 7; 0.031; 0.140 |
| Kills /1k steps | 4.090 | 4.102 | 2.942 |
| Clears /1k steps | 0.519 | 0.520 | 0.500 |
| Stall goal hops <1 / filled stalls | 82.2% (180/219) | 82.1% (179/218) | 76.7% (115/150) |
| Mean col_novelty | 0.99340 (296/296) | 0.99535 (295/295) | 1.37896 (224/224) |
| Damage dealt fraction /1k steps | 5.513 | 5.529 | 4.215 |
| Half-hearts lost /1k steps | 15.062 | 15.067 | 13.330 |

At equal bounds v12 has lower exit-start share (**64.4% vs70.5%**), higher stall
share (**73.9% vs67.0%**) and fewer rooms/episode (**1.692 vs1.795**). Kills/1k
are higher (**4.102 vs2.942**), clears/1k are close (**0.520 vs0.500**).
Each collected7 items, about0.140/1k steps; no episode reachedstage2. Shorter stall
limits produce more episodes per observedstep: report actual denominators rather
than comparing episode counts alone. This early window does not show broad gameplay
improvement, and no causal or frozen-policy superiority is claimed.

Never-left-start means rooms_visited=1 among stalls; it is a proxy excluding later
returns. Goal hops<1 is descriptive, not proof of a clear room/open unexploreddoor.
The150k requirements (stallshare<50%,rooms>2.5 and progression) are not met in this
early window and are not stop rules. One seed,changing policies and uncontrolled
native layouts limit inference. Reward totals differ between contracts.

## Reward columns:episode means (available/selected)

| Metric | v12 common (295 episodes) | v11 common (224) |
|---|---:|---:|
| col_enemy_damage | 4.68363 (295/295) | 4.70083 (224/224) |
| col_room_clear | 0.88136 (295/295) | 1.11607 (224/224) |
| col_room_visit | 3.45763 (295/295) | 3.97321 (224/224) |
| col_floor_entered | 0.00000 (295/295) | 0.00000 (224/224) |
| col_damage_taken | -1.27627 (295/295) | -1.48661 (224/224) |
| col_death | -2.87119 (295/295) | -3.30357 (224/224) |
| col_time | -0.17272 (295/295) | -0.22788 (224/224) |
| col_pickup_coin | 0.00407 (295/295) | 0.01741 (224/224) |
| col_pickup_bomb | 0.01186 (295/295) | 0.00000 (224/224) |
| col_pickup_key | 0.00508 (295/295) | 0.00446 (224/224) |
| col_collectible_new | 0.11864 (295/295) | 0.15625 (224/224) |
| col_heal | 0.00847 (295/295) | 0.00670 (224/224) |
| col_novelty | 0.99535 (295/295) | 1.37896 (224/224) |
| col_stall | -2.95593 (295/295) | -3.34821 (224/224) |
| col_stagnation | -5.54725 (295/295) | -5.33304 (224/224) |
| col_door_shaping | 1.37723 (295/295) | 0.84821 (224/224) |

## Optimizer statistics

Common recorded model timesteps1024..49152,48rows per lineage, separately from
the observedepisode bounds. The v12 snapshot has no train row for50176; it is not
imputed from the later live CSV. Available values are compared below.

| Metric | v12 | v11 |
|---|---:|---:|
| Train rows; recorded model steps | 48; 1024..49152 | 48; 1024..49152 |
| entropy_loss (negative entropy) | -3.78854 (48/48) | -3.67591 (48/48) |
| approx_kl | 0.02790 (48/48) | 0.02425 (48/48) |
| clip_fraction | 0.16681 (48/48) | 0.15594 (48/48) |
| KL max; >0.03 rows | 0.09677; 13/48 | 0.05575; 10/48 |
| Update seconds median;range;coverage | 6.250; 2.141..20.719; 47/48 | 8.406; 2.437..17.891; 47/48 |
| pause_ok true/measured | 47/48 | 45/48 |

Target KL is an update early-stop setting, not a strict logged-value bound. Timing,
KL and pause outcomes are descriptive; no pause percentage guard or tuning is
introduced. update_seconds records the prior update,first timing blank excluded.
Optimizer changes do not prove improved native play.

## Native checks and remaining limits

| Check | Status | Evidence / limit |
|---|---|---|
| Full offline gate | passed before launch | Check1569includingLua/no skips;lint/format/mypy/pip;one existing syntheticAllNaNwarning |
| Strict OpenSpec | passed | 30/30; report-only validation repeated |
| Initial18-minute native audit | passed for encountered cases | 22/22 stalls30.000..30.188s,col_stall-4,col_stagnation-7.02,learnerterminal flags correct |
| Snapshot/counts audit | passed in sample | 1035frames,max12501bytes;counts t4096SHAvalid,256keys/max21;689/783 startpayments decayed |
| Initial menu entry | passed | menu_entry_resolved slot2/new-run thenmenu_new_run_verified,8keys |
| Milestone hashes | passed | Model/normalizer/counts matchmanifest and ownerreceipt |
| First8hrollover after death | not_run | Expected around14:30UTC /15:30CET; initial entry is not resumed-entry proof |
| Frozen evaluation / progression acceptance | not_run | Ongoing training,no stage2 in this window |
| Final cleanup | not_run | Training active under finite target/deadline |

Snapshot SHA256:

- model.zip: `8bd8c9ad7a88b46a9edac785db8df21bdf8f06dc91596daa6367c81aeaa3f461`
- vecnormalize.pkl: `54c52e098ed67f7095063a8e29b39d5ab9e9e8d046237e56363f7050a3e867e2`
- novelty_counts.npz: `b637c3ec2df08fa47649abbb290691fd0ebc2c58fb5ecd35c328090a1e71f283`

All pending native OpenSpec tasks remain open; no change is archived. Continue
unchanged to150k/300k, with first8hrollover independently inspected and conditional
death/no-game scenario reported as unencountered if it does not occur. Future v11
comparisons stop at254782 available observedsteps; no300k extrapolation.
This report is self-review,not independent review. Whitespace/local Markdown links
and strictOpenSpec are publication checks; no fullRL rerun for report-only edits.
