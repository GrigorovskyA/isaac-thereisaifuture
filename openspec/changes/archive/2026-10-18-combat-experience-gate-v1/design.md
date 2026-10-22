## Context

Live runs wrap `IsaacCombatEnv` (EpisodeController over `LiveBackend`) in
`FaultTolerantEnv`; training wraps that in SB3 `Monitor` -> `DummyVecEnv` ->
`VecNormalize` and calls `model.learn(n_steps)` per checkpoint chunk. Episodes end on
`room_cleared` (terminated), `player_died` (terminated) or 1800 game updates
(truncated). The live scenario allows room changes and never forces resets.

## Decisions

### Wrapper placement

`CombatGateEnv` wraps the `FaultTolerantEnv` returned by `make_live_env`:

    VecNormalize(DummyVecEnv([Monitor(CombatGateEnv(FaultTolerantEnv(IsaacCombatEnv)))]))

The gate sees exactly the steps SB3 counts, including fault truncations. It reaches
the `LiveBackend` via `env.unwrapped.controller.backend` for management reads only.

### Handoff inside reset (SB3 trap)

`DummyVecEnv` auto-resets after every terminal/truncated step, and `learn(n_steps)`
collects a full rollout before updating. The gate performs the whole operator
wait inside `reset()`:

- the terminal step (with its reward and `done`) is returned normally, so SB3 stores
  the terminal reward and sets `episode_start` for the recurrent state;
- the blocking reset returns only an eligible combat observation, so no wait frame is
  ever an observation, sample, decision or normalizer update;
- one rollout spans several short encounters; updates and checkpoints still happen
  every `n_steps` combat decisions; `Monitor` sees ordinary episodes.

`training.py` needs no change.

### Eligibility (management only)

`classify(snapshot, previous)` returns one of:

| state | condition |
|---|---|
| unavailable | no snapshot, `status=unavailable`, or missing frame/oracle |
| paused | `status=paused` |
| dead | `oracle.player_dead` |
| transition | session, epoch or room visit differs from the previous snapshot |
| ambiguous | `oracle.enemy_overflow > 0` (coverage incomplete) |
| cleared | `oracle.room_clear` |
| empty | no listed enemy with `hp > 0` |
| combat | otherwise: live active player, known uncleared room, alive enemies |

Only `combat` is eligible. The order makes unknown/incomplete data ineligible; nothing
is ever inferred as a kill, clear or combat. The classification is logged but never
reaches the encoder, policy, recurrent state, normalizer or reward ledger.

### State machine

    stopped <- (deadline | wait cap | protocol error | close)
    [reset] -> waiting_for_operator --valid ack + combat--> ready_pending
    ready_pending --inner reset returns same-room combat--> combat_active
    ready_pending --race (room/state changed)--> waiting_for_operator (new request)
    combat_active --terminal/truncated/fault/room change--> (next reset) waiting

- Entering `waiting_for_operator` releases input (idempotent `release` command) and
  issues a new request; no action command is sent while waiting.
- While waiting, only `LiveBackend.poll` runs: it drains the bounded inbox, keeps the
  latest snapshot and reconnects after a restart. It never sends commands.
- In `combat_active` eligibility is maintained (feedback 1). The gate installs a veto
  hook `LiveBackend.action_gate`; `LiveBackend.step` evaluates it on the current state
  and on every drained queued snapshot *after* absorbing it (events are kept, a queued
  death still terminates) and *before* sending the action. A veto withholds the action,
  sends `release`, waits for one frame newer than the step start and sets
  `LiveBackend.blocked`. After every step the gate classifies the final state as well.
  Any non-combat result (`empty`, `cleared` without the event, `ambiguous`, `paused`,
  `unavailable`, `room_changed`) truncates the segment with `info["gate_exit"]` (and
  `info["action_withheld"]` when vetoed) and releases. No clear or death is fabricated.
  Trade-off: if the clear flag lags enemy deaths past the step boundary, the segment
  ends as `empty` and the clear bonus is not credited (kill rewards are). The vetoed
  step is still one SB3 sample; its recorded action was not executed and it is counted
  as `withheld_actions`.
- Any episode end (clear, death, timeout, fault, gate exit) leads to a handoff. A
  fight that is still active after a timeout also needs fresh readiness.

### Operator handshake

Files live in the fixed per-session directory `<session>/combat_gate/`:

- `request.json` (runner-owned): `request_id` (128-bit random nonce), `handoff`,
  `state`, `issued_at`, latest observed `session_id`/`game_epoch`/`room_visit`/
  `eligibility`. It is rewritten only when the observation provenance or state changes.
- `ready.json` (operator-owned): `request_id`, `session_id`, `game_epoch`,
  `room_visit`, `acked_at`. `combat-ready --session-dir` copies the provenance from
  `request.json` and writes it atomically. It writes no other path.

The runner reads at most 4096 bytes and always deletes the ack. It rejects an ack that is:

- invalid;
- for a consumed request (`replayed`) or another request (`stale_request`);
- from before the request (`predates_wait`) or more than 5 s in the future;
- for another session, epoch or room;
- sent while the latest state is not `combat` (`not_eligible`).

An accepted request id is consumed. A new handoff deletes any leftover ack before it
writes the new request. A new enemy never resumes control without an ack.

### Budgets and cleanup

- The run deadline (`--minutes`) covers waits, pauses, resets and reconnects;
  `LiveBudgetExpired` stops the run.
- During each handoff the gate narrows `run_deadline` on the backend and on every
  wrapper holding one (`FaultTolerantEnv`) to `min(original, handoff cap)` and restores
  the original value afterwards. Waits, `poll` reconnects, the resume `env.reset()` and
  its `start_episode` reconnect loop therefore all stop at the smaller deadline. The
  gate rechecks both deadlines after the reset returns and never activates combat after
  expiry. A narrowed expiry is reported as `CombatGateExpired` (cap) or
  `LiveBudgetExpired` (run deadline); protocol errors stay protocol errors.
- Freshness: a poll with no snapshot while disconnected, or no snapshot for
  `stale_seconds` (default 1 s; the observer samples every 50 ms), clears the retained
  state (`observation_gaps`) and marks the request `unavailable`. Readiness is then
  rejected as `no_observation` until fresh state arrives.
- The per-handoff operator-wait cap (`--gate-wait-minutes`, default 10, must not
  exceed `--minutes`) raises `CombatGateExpired`, a `LiveBudgetExpired` subclass:
  it stops the run, is never a fault retry, death or success, and is never renewed.
- Protocol errors propagate. On stop, the request becomes `stopped`, so the
  `combat-ready` command refuses it, and close releases input and closes the client.
- Training reports `unsaved_steps`: gated decisions minus timesteps gained by
  checkpoints in this run. Untrained samples are never reported as an update.

### Logging

`live.jsonl` gets `combat_gate` rows:

- `wait_started`, `observed` (provenance/state changes), `ready_rejected`,
  `ready_accepted`, `resume_race`, `combat_resumed` (wait seconds/snapshots),
  `combat_ended` (outcome, steps, return, gate exit), `stopped`;
- a `summary` with handoffs, accepts, rejects by reason, wait seconds/snapshots,
  room changes observed during waits (operator assistance), combat decisions and reward.

Oracle events stay in `oracle.jsonl`.

## Trade-offs

- An ack is required even when combat continues after a timeout. That costs the operator
  time but rules out any implicit resume.
- Readiness via a file instead of stdin keeps the runner non-interactive and testable
  and needs no desktop input or wire extension.
- Seeds do not create matched real scenarios; synthetic tests prove mechanics only.
