## Why

The first 9 native `pure-v1` episodes (about 7k steps) show that reward v2 pays
most for doing nothing: stall-restarted episodes that never fought returned +2 to
+5.6, mostly from novelty (+4 to +6.5 per episode), while episodes that damaged
enemies and died returned -12.6 and -13.3. Three causes are structural, not noise:
novelty 1/sqrt(n) per visit grows like 2*sqrt(n) and pays for standing still; a
stall restart costs nothing while death costs -10; one hit taken (usually a full
heart, -4) costs twice a full enemy kill (+2). Training statistics (entropy,
value fit, action mix) are not recorded at all.

## What Changes

- Reward v3 (`configs/reward-v3.yaml`): novelty pays only the first visit of a
  (stage, room, 40-unit cell) per run (0.02, about 1.8 for a full 1x1 room); enemy damage 5.0 per full enemy HP;
  first room clear 10; first room visit 3 (was 1); health lost -1 per half-heart; stall restart -5 (a wasted
  run, outcome-only); death -10 unchanged; pickups unchanged.
- New lineage `pure-v2` (`configs/training-pure-v2.yaml`, run root `runs/pure-v2`);
  `pure-v1` stays preserved on disk and is not resumed.
- Episode summary adds use presses (bomb/active/pill-card), half-hearts lost,
  steps to first room exit and to first enemy damage.
- New `metrics/train.csv`: one row per PPO update with SB3 train statistics
  (entropy, value/policy loss, explained variance, approx KL, clip fraction,
  learning rate) and the rollout action mix per head.
- Dashboard: training-statistics charts, action mix, start-room exit rate,
  throughput; fixes the duplicated end-reason label.

## Capabilities

### New Capabilities

- `training-metrics`: per-update training statistics and action mix.

### Modified Capabilities

- `pure-reward`: reward v3 terms (delta in this change; base requirements live in
  the unarchived `pure-self-learning-v1` change).

## Non-goals

- Technique rewards, action masks, scripted setup or curriculum.
- Resuming or migrating `pure-v1`.
- Claims that the new weights improve play; that needs hours of new evidence.

## Impact

Python reward ledger, env summary, training callback, configs, dashboard, docs and
tests. No Lua, protocol or observation change. Acceptance: offline gate green; the
exploit tests show stalling and standing still no longer beat fighting in
synthetic episodes; native evidence comes from the next `pure-v2` hours.
