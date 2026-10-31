## Why

Rewards v9 to v12 and the learner changes after them all train on whatever run the game happens
to deal. Most runs end in the first rooms, and runs that teach the agent much (a large learning
signal) are seen once and lost. Prioritized Level Replay (Jiang, Grefenstette and Rocktaeschel,
ICML 2021, arXiv 2010.03548) replays the levels with the largest recent learning signal and gave
large gains in sample efficiency and generalization on Procgen. In Isaac a level is a run seed.
An automatic curriculum driven by the agent's own learning signal is allowed by the pure doctrine
(`docs/UPDATE_DECISION.md`): it chooses which seed to play, never what to do; no observation,
reward term or action changes.

## What Changes

- `level_replay.py`: `SeedBank`, a bank of run seeds ("XXXX XXXX", the game's alphabet) with
  scores. Each New Run is a replay with probability `plr_replay_probability` (0.5), sampled by
  P = (1 - rho) P_score + rho P_staleness with rank prioritization (temperature
  `plr_temperature` 0.1) and staleness mix `plr_staleness` (0.1); otherwise the run is unseeded
  and its seed joins the bank (`plr_bank_size` 500, eviction of the lowest score, oldest first).
- `learner.PureRecurrentPPO`: records each step's run id from the step info and, before the
  rollout normalization, adds the step's |GAE advantage| to its run; a seed's score is the mean
  over the trained steps of its latest run, accumulated across rollouts.
- Lua observer (`mod/observer/main.lua`): new opt-in capability `seeded_restart_v1` (live loop
  only). The oracle block gains `run_seed` (`Game():GetSeeds():GetStartSeedString()`, validated,
  null when unreadable). Commands gain an optional validated `seed`: `restart` with a seed issues
  `Isaac.ExecuteCommand("seed XXXX XXXX")` instead of `restart`, and the new kind `next_seed`
  arms the seed of the mod's own death restart for the current game epoch. Both go through the
  existing guarded dispatch (pacing, budget, lease, 5 s confirmation). Malformed seeds close the
  session; nothing else reaches the console.
- `LiveBackend`: under level replay it notes each run's seed, arms the planned seed at the start
  of a run (bounded retries) and sends it with the stall restart.
- Contract field `level_replay: none | plr_v1` (hashed; `none`, absent or explicit, is left out of
  the hash, so the next-lineage hash `0399c37d...` stays). Hyperparameters `plr_*` (not hashed;
  recorded per checkpoint only under `plr_v1`).
- Checkpoints save the bank as `level_replay.json`, hashed in the manifest; resume under `plr_v1`
  refuses a checkpoint without it. Frozen evaluation never uses level replay.
- `episodes.csv` gains `run_seed` and `seed_replayed` (empty when off) with a one-time header
  upgrade.

## Non-goals

- No change of reward, observation (the seed is never encoded), actions or normalizer; the
  shipped contract stays `none` and the current lineage is not touched.
- No replay inside a run (no save states), no curriculum over floors or characters, no
  hand-picked seeds and no special seeds.
- No PLR in frozen evaluation and no seeded evaluation protocol.
- No value-loss score variant and no robust PLR (that is a later change if needed).

## Acceptance

- Offline gate (`scripts/check.sh` with the two known macOS-only failures / `Check.ps1`),
  `scripts/smoke_rl.py` and strict OpenSpec validation pass; the shipped contract hash is
  unchanged.
- Tests show: rank prioritization, staleness and eviction; score attribution across rollouts;
  the bank's save/load round trip and resume refusal; Lua issues exactly `seed XXXX XXXX` for a
  seeded stall restart and an armed death restart, rejects malformed seeds, keeps the plain
  restart unchanged and reports the seed; `episodes.csv` columns.
- Native: the `seed` console command from Lua starts the requested seed with the same
  exit/start order as `restart` (see tasks).
- Learning: a later lineage with `level_replay: plr_v1` (otherwise the same contract) compared
  with the `none` lineage at equal steps (rooms per episode, share of episodes with 3+ rooms,
  floor 2 rate, explained variance) on fresh unseeded runs in frozen evaluation.

## Impact

- `src/isaac_threrisaifuture/{level_replay,learner,training,checkpoints,live,live_wire,actions,
  observer_client,env,episode_metrics}.py`, `mod/observer/main.lua`, `configs/training-pure-v4.yaml`
  (comment and `plr_*` defaults only), tests, docs.
- Turning it on needs a new lineage and the redeployed observer mod. Replayed runs are seeded
  runs, which disable achievements; the user accepts the file-2/achievement risk
  (`docs/RUNTIME_AUTHORITY.md`).
