# Reward v11 and observation schema 9: finite native plan

Authorized by the human October 30, 2026. This plan supersedes the stopped v10
training plan. It authorizes one fresh model launch, not a retry after a fault.

## Frozen inputs and offline verification

- Changes: `door-entry-fix-reward-v11`, `item-identity-observation-v9`.
- Contract: `7c01606925675e6e7535a61ca75b26770e5aadecf8110dfc96bb251448dfcd7c`.
- Observation 9: 11691 floats; action 2; reward `pure-v11`; entity frame 7.
- RecurrentPPO: seed 1, features 512, n_steps 1024, batch 128, n_epochs 10,
  target_kl 0.03, gamma 0.998, ent_coef 0.005, learning_rate 0.0003.
- Stall ends learning as terminated; episode metrics retain truncated/stall.
  Novelty is 0.1/sqrt(N), persisted across runs in checkpoint/novelty_counts.npz.
  blocked_cost is zero. No reward or configuration edits during this run.
- Check.ps1 passed: 1543 tests including isolated Lua, no skips; lint, format,
  typing and dependencies passed; strict OpenSpec 28/28. One existing synthetic
  AllNaN warning. This is offline verification, not native acceptance.
- Local evidence: `reports/local/reward-v11-schema9-20261030` (E).
  launch.json records the committed source revision and exact launch/check times.

## Preservation, deployment and launch

Verify hashes before and after moving runs/pure-v4 to runs/pure-v4-reward-v10.
Preserve v10 checkpoint `3043a54c-s1-t63488`, 290 completed episodes and 64430
observed episode steps; checkpoint steps are 63488. Preserve the earlier failed
v10 startup archive and all previous evidence. Preserve v9 schema8 at
runs/pure-v4-reward-v9-schema8 (105104 observed steps, checkpoint 102400).

Close the dashboard. With the game closed, back up and deploy only the project's
observer main.lua and metadata.xml; compare deployed hashes and run preflight.
Do not change saves, Steam Cloud or launch options. Use Start-Pure.cmd --initialize
once with the ordinary guarded Continue path. A refused Continue stops the task;
there is no fallback New Run or manual retry under this plan.

The prepared hidden finite owner schedules stop.forever at **2026-11-01 08:00 UTC
(09:00 CET)** before training proceeds. Minimum target: 300000 saved model steps.
The target does not extend the deadline. Only a later human decision can extend it.
Compatible automatic lease rollover may resume the same lineage under this deadline.

During training, monitoring reads files only: never open or activate a PC window,
console, browser or Codex panel. Do not restart the dashboard. Native guarded keys
handle game focus. The prepared passive audit preserves decoder results, model
inputs, reward state and returned transitions; it writes bounded local evidence
for the first 22 minutes per worker (64 MiB cap per stream).

## Native check at 18 minutes

The owner writes E/native-check.json. Independently inspect its denominators and
raw evidence before notifying once in Russian. Measure:

- Visible collectible pedestals: item_quality 0..4, item_type passive/active/familiar,
  item_tags 0..255 and item_max_charges 0..24. Other pickups omit these fields.
- Active item quality/tags when an active item is held; tag_counts has eight numbers.
  Every sampled frame must decode and be smaller than 131072 bytes.
- Latest checkpoint has hash-matching novelty_counts.npz; repeated starting-room
  novelty payments decline as visit counts rise. Report per-run payment sums with
  the incomplete final episode excluded, and decayed-payment counts.
- Train statistics are populated. Report update_seconds median/range (expected
  about 25..35 s), approx_kl distribution and values above approximately 0.03.
  Timing and KL expectations are descriptive, not automatic stop thresholds.
- Where encountered, learner stall flags are terminated=true/truncated=false.

Stop on invalid frames, visible pedestals always lacking plausible fields, invalid
item placement/inventory/tag counts, missing required evidence or training faults.
Unencountered pedestal/active/Blind variants remain unverified, not fabricated.
Pause failures alone never stop training. No pause threshold or configuration fix.
More than ten minutes without fresh steps/checkpoints/episodes warrants bounded
log inspection and a possible-stall notification, not an invented retry.

## Reports and comparison method

At the first saved checkpoint at or above 50000, 150000 and 300000, the owner copies
metrics and the manifest into E/milestone-TARGET and records the actual checkpoint.
Produce English milestone reports and update STATUS/TRAINING_SESSION links.
Report v11 cumulatively from zero and in the latest approximately 50k observed
episode-step interval. Boundary episodes stay whole, assigned by cumulative end;
show actual whole-episode step denominators. Observed steps may contain unsaved
tails and do not equal optimizer/model steps.

Compare v10 and v9 schema8 only on the same cumulative observed-step bounds, up to
the minimum available for each pair: v10 64430; v9 105104. No extrapolation and no
claimed matched baseline at 150k or 300k. Report missing historical context as N/A.
Metrics: exit-start share (rooms_visited>1), stall share, rooms/episode, stage>=2,
stall episodes that never left the starting room (rooms_visited=1 proxy), mean
col_novelty, collectible pickups per episode/1k steps; entropy, approx_kl and
clip_fraction with train-row/model-step denominators. Goals at 150k: exit-start
above 80%, stalls below 50%, rooms/episode above 2.5. These are measured outcomes,
not stop rules or frozen-policy acceptance. Include other reward-column means
where practical. No OpenSpec task is accepted from optimizer statistics alone.

## Stop and handoff

Human stop: create both E/user-stop.request and runs/pure-v4/supervisor/stop.forever.
On fault, deadline or check failure keep stopped, preserve evidence and do not retry.
Inspect every session's exit, fault, status_writes_skipped and cleanup_errors;
launcher exit zero cannot erase faults or unverified release. Verify actual absence
of game, worker, owner, Start-Pure, listener 9528 and deployed action_authorization.json
or temporary approval. Retain stop.forever and freeze final hashes.

Finish the English final training report with actual end date/reason, source,
launch/check/cleanup evidence and comparison limits. Relevant report/docs only:
whitespace/link/strict OpenSpec checks, review staged files, commit/push existing
origin main. Never stage runs, local evidence, models, raw logs, tools or unrelated
work. Do not archive incomplete OpenSpec changes. Notify the final outcome once in
Russian and delete the monitor when no authorized work remains.
