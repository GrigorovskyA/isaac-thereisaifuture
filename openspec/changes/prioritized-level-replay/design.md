## Context

Lineage `pure-v4` (next contract `0399c37d...`: reward v12, schema 9, structured features,
rollout advantages, cuda, auxiliary self-prediction) trains on one real-time game. Death
restarts are issued by the Lua mod itself (`MC_POST_GAME_END` -> 1.5 s delay -> guarded
`Isaac.ExecuteCommand("restart")` -> 5 s fresh game-start confirmation); stall restarts are a
`restart` command from Python through the same dispatch. The game's start seed is a string like
"T1MM AY48" (`Seeds:GetStartSeedString()`); the console command `seed T1MM AY48` "starts a new run
with the inputted seed" (Debug Console wiki). Seed strings use A-Z and 0-9 without I, O, U and 5
(wiki "Seeds"); entering a seed disables achievements for that run.

## Decision 1: a level is a run seed; the bank is learner state

`level_replay.SeedBank` holds up to `plr_bank_size` seeds with a score, the run counter when the
seed last started (staleness) and when it was added. On each New Run with a scored seed in the
bank, a replay happens with probability `plr_replay_probability`; the seed is drawn from
P = (1 - rho) P_S + rho P_C, P_S proportional to (1 / rank) ^ (1 / beta) over the scores (rank 1
= highest, stable ties), P_C proportional to the runs since the seed was last started (uniform if
all are 0), beta = `plr_temperature`, rho = `plr_staleness`, as in the paper. Unscored seeds are
never replayed. A fresh run is unseeded (`restart`); its seed joins the bank, and a full bank
evicts the lowest score, then the oldest; unscored seeds go last. The random draw uses a NumPy
generator seeded by (lineage seed, run counter), so a resumed lineage decides the same way without
a saved generator state.

The bank (seeds, scores, run counter) is saved per checkpoint as `level_replay.json` (format 1,
JSON, validated on load) with its sha256 in the manifest (`level_replay_file`,
`level_replay_sha256`), like `novelty_counts.npz`. Under `plr_v1` resume refuses a checkpoint
without it; other contracts refuse a bank. A smaller `plr_bank_size` after a resume evicts down.

## Decision 2: score = mean |GAE advantage| of the run's trained steps

The env puts the backend's current run id into each step's info (`level_replay_run`; never into
the observation). `PureRecurrentPPO._update_info_buffer` records it per collected step. In
`train`, before `normalize_rollout_advantages`, the raw advantages of the buffer (one env) are
grouped by run id; each run accumulates sum and count across rollouts, and the seed's score is
the running mean over all of its trained steps (the latest run of a seed replaces the score of
earlier ones). Runs that are neither in the rollout nor current are closed. A rollout whose ids do
not line up is not scored (`train/plr_scored_steps` 0). Positive value loss is not used: with
GAE lambda 0.98 the mean |advantage| is the paper's best-performing L1 value-loss score.

## Decision 3: wire protocol, minimal and opt-in

- Capability `seeded_restart_v1`, advertised with `live_loop_v1` and allowed only with it. The
  Python client requires it only when the contract is `plr_v1` (`ObserverConfig.seeded_restart`),
  so a redeployed mod changes nothing for the current Python and an old mod still serves `none`.
- Oracle field `run_seed` (only after the capability): the validated start seed string, read once
  per game epoch, or null. The oracle block is labels/metadata; the encoder never reads it, and a
  test proves the encoding is identical with and without it.
- Command field `seed` (only after the capability, only on `restart` and `next_seed`), appended
  after `frames` in the canonical order; omitted when absent, so other commands keep their bytes.
  The Lua canonical comparison strips whitespace, so the seed's space is stripped on both sides,
  and the decoded value must match `^[alphabet]{4} [alphabet]{4}$` exactly. Anything else (wrong
  case, I/O/U/5, missing space, extra characters, quotes, a seed on another kind, a seed without
  the capability) is a protocol error that closes the session; it is never dispatched.

## Decision 4: seeded restarts through the existing guarded dispatch

- Stall: `LiveBackend.request_restart` sends `restart` with the planned seed (or none). Lua keeps
  every existing guard (training mode, lease, attempt budget, pacing, refusal while dead, paused,
  pending or awaiting) and stores the seed in `restart.pending`.
- Death: the mod decides when to restart, so Python decides the seed in advance. At the start of
  each run the bank plans the next New Run; with a replay planned, the backend sends `next_seed`
  (refused once a restart is pending or awaiting; retried on later steps up to 20 times per run).
  Lua stores it for the current game epoch only; `MC_POST_GAME_END` copies it into the pending
  death restart; a game start or disconnect clears it.
- `lifecycle()` re-validates the seed and dispatches `Isaac.ExecuteCommand("seed " .. seed)`
  instead of `"restart"`; attempts, pacing, the 5 s confirmation and the fault-disable path are
  unchanged and shared.
- If arming fails or the death comes first, that New Run is fresh; the bank records what actually
  happened from the reported seed (`seed_replayed` = the seed was in the bank when the run
  started), never what was planned. A run whose seed cannot be read is not banked.

The design covers deaths, so no stall-only fallback is needed. It depends on native facts that
offline stubs cannot prove (tasks 2.3-2.5): that `seed X` from Lua behaves like `restart`
(exit, then a fresh `continued == false` start within 5 s) and that a plain `restart` after a
seeded run draws a fresh seed. If `restart` repeated the seed, every "fresh" run would show up
as `seed_replayed` 1 and the bank would not grow; the native check must decide before a long run.

## Failure handling and compatibility

- `level_replay: none` (default, shipped): no capability is requested, no seed is sent, no step
  info key or bank exists, the PLR hyperparameters are not recorded and `run_seed` /
  `seed_replayed` stay empty. The contract hash ignores `level_replay: none`.
- `plr_v1` without a client that negotiated the capability is refused before training
  (`make_live_env`); a mod without it fails the handshake.
- Evaluation never negotiates the capability and never builds a bank.
- Seeded runs disable achievements; file-2/achievement risk is accepted by the user
  (`docs/RUNTIME_AUTHORITY.md`). Special seeds are never produced: only seeds the game reported
  for unseeded runs are replayed.
- Turning `plr_v1` on needs a redeployed observer mod (`mod/observer/main.lua`) and a new lineage.
