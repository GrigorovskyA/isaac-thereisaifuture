## Why

After 477k steps the reward v7 policy is still at random-play level
(`reports/2026-10-26-pure-v7-t477184-eval-and-timing.md`). Two session-long numbers explain the
slow learning:

- With the 90 s stall watchdog, 69% of training episodes end in a stall, and 82% of all
  environment steps are spent in stalled episodes, mostly standing in the empty start room.
- `steps_to_first_exit` over 897 episodes: p50 53 steps, p75 139, p90 252 (about 4.4 steps
  per second). A 40 s limit (about 180 steps) still covers p75.

Samples from stalled episodes carry little signal, and the stall penalty arrives about 400 steps
after its cause (gamma 0.998). A shorter stall limit cuts the wasted samples per hour two to
three times and moves the penalty closer to the cause.

## What Changes

- `configs/training-pure-v4.yaml`: `watchdog.stall_seconds: 40` (was 90) and
  `contract.reward_version: 8`. Hyperparameters stay unchanged.
- Reward v8 (`configs/reward-v8.yaml`) = reward v7 with `stagnation.per_second: -0.25` (was
  -0.1) and `stagnation.grace_seconds: 12` (was 20). The cap stays
  `-0.25 * (40 - 12) = -7.0`, so a full stall still costs at most -12 and a death from full
  health (-13) never pays better than a full stall.
- Reward v7 config moves to `archive/configs/reward-v7.yaml`. The ledger still loads it, as it
  loads the archived v4-v6 files.
- Contract: reward contract `pure-v8`; pure-v7 checkpoints are refused. The stagnation ledger
  uses the stall limit of the training config (40 s), not the 90 s default.
- The ledger rejects a stagnation grace period that is not shorter than its stall limit.
- Lineage `pure-v4` starts again with `--initialize`; the reward v7 run is kept as
  `runs/pure-v4-reward-v7` (done on Windows).

## Non-goals

- No change to the observation, actions, policy or hyperparameters.
- No Lua change and no observer redeploy.
- No reward for using items, aiming, moving or any other technique.

## Acceptance

Same per-1000-step criterion as reward v7 (revised 2.3). A frozen evaluation of the latest
checkpoint (`Start-Eval.cmd`, two 3600 s sessions) is compared with `random-prior` by
`scripts/compare_eval.py --baseline random-prior`:

- the 95% bootstrap interval of `kills_1k` minus `random-prior` is above zero; and
- the point difference of `clears_1k` is positive.

The 40 s limit also applies to frozen evaluation and changes how episodes end, so the
`random-prior` baseline is evaluated again under this config (two 3600 s sessions); the
reward v7 baseline roots are not compared with v8 checkpoints.

Training-side check: over the first 8 h session, the share of steps spent in stalled
episodes is below 50% (82% under reward v7).

## Impact

- `src/isaac_threrisaifuture/{rewards,live,checkpoints,training}.py`, configs, tests, docs.
