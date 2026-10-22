# Combat-experience gate (opt-in)

2026-10-20 extension: `--auto-navigate` selects separate bounded scripted management
inside the reset wait. Its implementation is offline-verified; installed-game
acceptance remains pending. Without that flag the operator workflow below remains
unchanged. See [navigation limits and usage](COMBAT_NAVIGATION.md).

OpenSpec archive: `openspec/changes/archive/2026-10-18-combat-experience-gate-v1`.
Status: accepted after offline checks and a bounded real random-policy test with
combat, timeout handoff, fresh readiness, final enemy defeat, empty/cleared-room
handoff and deadline cleanup. See [runtime evidence](../reports/2026-10-18-combat-gate-runtime.md).
Real gated PPO updates/checkpoints and improved play remain unverified; the actual
game test did not train a model.

## Why

In the 4096-step run ([report](../reports/2026-10-18-training-4096.md)) only two of seven
completed segments had enemies. After a natural restart, five minute-long segments were
empty, and the frozen t4096 policy chose down/down on 256/256 decisions. The gate makes the
learner act only during observed combat. A human operator moves between fights. There are
no exploration rewards, forced resets, spawned enemies or scripted navigation.

## Operator workflow (two commands)

1. Start a gated live run in one terminal, after the normal preflight and approval from
   [LIVE_LOOP](LIVE_LOOP.md):

   ```powershell
   Start-Live.cmd --mode train --config configs/training-live-v1.yaml --minutes 60 --combat-gate --gate-wait-minutes 10
   ```

   It prints `Local logs: runs\live\sessions\<stamp>`. When it needs you, it prints
   `Combat gate: input released (handoff N, ...)`.
2. While the gate waits, play by hand: walk into an uncleared room with enemies. When the
   fight is visible, confirm readiness in a second terminal:

   ```powershell
   .venv\Scripts\python.exe -m isaac_threrisaifuture.cli combat-ready --session-dir runs\live\sessions\<stamp>
   ```

   Take your hands off the controls. The learner resumes within one poll (0.25 s) if
   the request, session, game epoch and room still match and the room is still combat.
   Otherwise the ack is rejected with a logged reason; run the command again.

After every clear, death, 60 s timeout, fault or room change, input is released and step 2
repeats. A fight that is still running after a timeout also needs a new confirmation.
Random mode accepts `--combat-gate` too.

## Eligibility (management metadata only)

Each snapshot is classified from the existing live observation and oracle block, checked
in this order:

| state | meaning |
|---|---|
| `unavailable` | no snapshot, unavailable status, missing frame/oracle |
| `paused` | game paused |
| `dead` | player dead |
| `transition` | session, epoch or room visit changed since the previous snapshot |
| `ambiguous` | oracle enemy overflow (more than 64 enemies, coverage incomplete) |
| `cleared` | room clear flag set |
| `empty` | no listed enemy with hp > 0 |
| `combat` | everything else: the only eligible state |

Limits:

- Enemies are what Lua lists with `IsActiveEnemy(false)`, so some invulnerable or
  non-clearing entities count as enemies. Such rooms end by the 60 s timeout.
- Eligibility never enters the observation, policy, LSTM state, normalizer or reward. It is
  not a reward label.
- Eligibility is rechecked during combat on fresh state: before every action (including
  snapshots queued since the last step) and after every step. Any non-combat state
  (empty, cleared without the clear event, ambiguous, paused, unavailable, room change)
  withholds the next action, releases input and ends the segment as truncated with
  `info["gate_exit"]` (and `info["action_withheld"]` if the action was not sent). Damage
  and kills already observed are still credited; a queued death stays a terminal death.
- If the room clear flag lags enemy deaths past a step boundary, the segment ends as
  `empty` and the clear bonus is not credited. No clear or death is fabricated.

## Handshake files

Both files live in the fixed directory `<session>/combat_gate/`:

- `request.json` is written by the runner. It holds a 128-bit `request_id`, the
  `handoff` number, `state` (`waiting_for_operator`, `ready_pending`, `combat_active`,
  `stopped`), `issued_at`, and the latest observed `session_id`/`game_epoch`/
  `room_visit`/`eligibility`.
- `ready.json` is written only by `combat-ready`. It copies the request's id and provenance
  and adds `acked_at`.

The runner reads at most 4096 bytes and deletes every ack after one look. It rejects:

| reason | cause |
|---|---|
| `invalid` | unparsable or oversized ack |
| `replayed` | an already accepted request |
| `stale_request` | a different request id |
| `predates_wait` | acked before the request |
| `future_timestamp` | dated more than 5 s ahead |
| `cross_session`, `cross_epoch`, `cross_room` | provenance does not match the latest snapshot |
| `no_observation` | no snapshot seen yet |
| `not_eligible` | the latest state is not `combat` |

Other rules:

- Each new handoff deletes any leftover ack before it issues its request.
- Enemies appearing on their own never resume control.
- `combat-ready` refuses a `stopped` request or one without an observed state, and
  writes no other file.

## Budgets and stopping

- `--minutes` is one absolute deadline. It covers operator waits, pauses, resets and
  reconnects; it is never renewed.
- `--gate-wait-minutes` (default 10, at most `--minutes`) caps each handoff. When it
  expires the run stops (`CombatGateExpired`). That is not a fault retry, death or success.
- On any stop the gate releases input, marks `request.json` `stopped`, logs a summary and
  closes the client. Nothing relaunches the game, resets a run or resumes training.
- Protocol errors stop the run. Disconnects during a wait reconnect within the deadline.
- Every wait, reconnect and the resume reset are bounded by the smaller of `--minutes`
  and the current handoff cap; combat never starts after either expires.
- Readiness counts only against fresh state. After a disconnect or about 1 s without
  snapshots, a `combat-ready` is rejected (`no_observation`); run it again once the game
  streams again.
- Existing approval expiry and native restart limits still apply.

## Training interaction

The wait runs inside `reset()`:

- the terminal step and its reward reach SB3 normally;
- `DummyVecEnv` auto-reset blocks until combat resumes;
- the rollout's `episode_starts` resets the LSTM at every encounter boundary;
- wait frames never become observations, samples or normalizer updates;
- `Monitor` sees ordinary episodes, so one `n_steps` rollout spans several short fights
  and then updates and checkpoints as usual (checkpoint format and lineage unchanged).

If the deadline or wait cap interrupts a rollout, its partial samples are lost. The
log records `budget` ("unfinished rollout has no new checkpoint") and a `rollout_accounting`
row with `combat_decisions`, `checkpointed_timesteps` and `unsaved_steps`.

## Log rows (`live.jsonl`, kind `combat_gate`)

| event | meaning |
|---|---|
| `wait_started` | input released, new request (`reason`: run_start, episode_end, resume_race, ready_revoked) |
| `observed` | eligibility/provenance changed during the wait (room changes count as operator assistance) |
| `ready_rejected` | ack rejected, with `reason` |
| `ready_accepted` | ack accepted |
| `ready_revoked` | room/epoch changed before resume |
| `resume_race` | the reset snapshot was no longer same-room combat |
| `combat_resumed` | with `wait_seconds` |
| `combat_ended` | `outcome`, `gate_exit`, `fault`, `steps`, `episode_return` |
| `stopped` | the stop reason |
| `summary` | handoffs, accepts, rejects by reason, wait seconds and snapshots, wait room changes, resume races, observation gaps, withheld actions, combat decisions and reward, outcomes |

Oracle events remain in `oracle.jsonl`.

## Windows file-sharing recovery

Request/ack publication stays atomic, using unique sibling temporary files.
Reads are limited to 4097 bytes, with oversized messages rejected. Windows
sharing/access conflicts (native errors 5/32 or CRT EACCES) are retried for at
most 250 ms/26 attempts per operation, with at most 10 ms between attempts.
Gate I/O also obeys the original, narrowed handoff/global deadline. Other errors
propagate immediately; a permanent lock stops the operation and never grants
readiness or renews authority. No partial target replacement is used.

Stop releases input and records in-memory stopped state first. Publication and
ack removal remain best effort; after budget expiry they get only one immediate
attempt, without waiting/retry. A blocked stopped-file update can therefore leave
the prior disk record, but the stopped process cannot accept readiness; a future
handoff uses a new nonce. Secondary cleanup errors appear in the stopped row and
summary path. If the recorder itself fails, cleanup errors remain in memory and
are attached to the original reset exception; environment/client close still runs.

## Pending real-game evidence (primary-owned)

- Windows `Check.ps1`.
- A bounded gated run on file 2. Record handoffs, accepted/rejected acks, wait exposure,
  that no input was sent while waiting, release on clear/death/timeout, and correct
  restart provenance.
- Seeds do not create matched real scenarios. Synthetic tests prove mechanics, not play
  quality.
