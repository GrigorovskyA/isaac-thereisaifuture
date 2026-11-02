# Demo pretraining: launch and 20-minute native audit

2026-11-02, Europe/Amsterdam. First demo-pretrained run: contract `c8a7486b9806f2cd76e3aab5324163659dfb4b3ae41a619ed61a362be8936121`, source code `92d378d`, seed 1, file 2 Continue, reward v13. The user supplied 20,099 decision steps in 18 sequences. Prior reward-v13 run was preserved at `runs/pure-v4-reward-v13`: all 47 file hashes matched before/after; inventories in `reports/local/demo-lineage-20261102`. The deployed observer matched source. The actual worker PID 8340 appeared among NVIDIA GPU processes.

## Pretraining

`runs/pure-v4/seed-1/pretraining.json` reports 19,073 training and 1,026 holdout steps, split into 16 and 2 sequences respectively. It ran 2,250 optimization steps in 150.4 seconds, selecting best step 750 using holdout loss. Holdout NLL fell from 3.3949 to 1.9812.

| Head | Holdout before | Holdout after | Majority baseline |
|---|---:|---:|---:|
| Move | 25.6% | 50.4% | 26.3% |
| Shoot | 21.0% | 78.2% | 44.5% |
| Use | 99.51% | 99.51% | 99.51% |

Move and shoot accuracy exceeded the majority baselines in this held-out sample. Use accuracy equals the baseline and does not show that rare item actions were learned. Only two sequences were held out; this is not independent gameplay validation. Previous recording analysis found a possible mismatch between bomb-held starts and trigger labels and one message timeout; the user later reported three bombs in a separate approach, matching three labels. Input coverage remains a limitation.

## Native training interval

The step-0 checkpoint completed at 19:19:21.445 CET. The fixed 20-minute window ends at 19:39:21.445 CET. By completed episode `wall_time` within that interval, there were 44 episodes / 4,541 observed episode steps, averaging **1.659 rooms/episode** (18 one-room, 23 two-room, 3 three-room), 16 deaths, 28 stalls and 73 recorded kills. The requested >1.7 rooms threshold was not met in this short sample. These are online, changing-policy training episodes, not frozen evaluation or statistical proof of improvement.

For context, the archived reward-v13 episode CSV at the same cumulative observed-step bound `(0,4541]` has 61 whole episodes / 4,482 actual selected steps, averaging 1.164 rooms/episode, with 56 stalls and 5 deaths. Different trajectories, initial game state, episode lengths and the small early sample limit this comparison; 1.7 was a later v13 reference, not an independently measured matched 20-minute result.

The first four train rows show `approx_kl` 0.0878, 0.0656, 0.0985, 0.0758 and `aux_approx_kl` 0.3084, 0.1380, 0.1209, 0.1059. This is a notable change signal after pretraining, not a direct measure of gameplay or a diagnosis of cause. `n_updates` grew 1, 3, 5, 7; recorded update times 18.328, 19.282, 18.984 s (first blank). No hyperparameters were changed. Weighted entropy must not be compared to 4.6 nats or the unweighted E3B metric.

At 19:40 CET, session `session-20261102-191622-0001` remained training, fault null, latest `c8a7486b-s1-t4096`; model, normalizer, novelty counts, auxiliary and E3B checkpoint files all matched manifest SHA-256. The recorded smoke is an interim check; native gameplay acceptance and durable improvement remain unproven. Training was left running at the user's request.
