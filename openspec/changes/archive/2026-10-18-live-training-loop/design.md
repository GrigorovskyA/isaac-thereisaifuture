## Context

User decisions of 2026-10-18 (see proposal): approximate events, autonomous death
restart, training on file 2. Implemented behavior is described below; future intent
is marked as such.

## Protocol

- Capability `live_loop_v1` is advertised only when a valid `training` approval is
  loaded and the entity API is available. Requesting it requires exactly
  `entity_observation_v1`, `safe_actions_v1`, `death_restart_v1`; it excludes the
  oracle probe and native step modes. A `training` approval without `live_loop_v1`
  cannot enable `safe_actions_v1`.
- Approval file (`mods/isaac_threrisaifuture_observer/action_authorization.json`,
  at most 2048 bytes, loaded once per mod load): `profile_mode="training"`, `slot=2`,
  no `game_epoch`, `expires_at <= now + 28800`, integer `max_restarts` 1..5000, plus
  the four evidence strings. Older modes keep their epoch binding and 30-minute limit.
- Snapshot field `oracle` (live sessions only): `room_clear`, `player_dead`,
  `enemies[{entity_id, hp, max_hp}]` (at most 64, includes invisible active enemies),
  `enemy_overflow`. `null` exactly when the snapshot is unavailable.
- Command ack `status` is `accepted` or `rejected`. Rejection (live only) covers a
  different epoch/visit, a frame newer than the last sent snapshot, a frame older than
  15 updates, pause, death or player-count changes. It consumes the sequence and
  releases input. Malformed, noncanonical, wrong-session or non-increasing commands
  still close the session.
- Live sampling is 50 ms (default 200 ms).

## Lifecycle and cleanup

- Lease: the action authority deadline equals the approval expiry (per mod load).
- Restart budget: `max_restarts` attempts within the lease, at least 4 s between
  dispatches, the existing 1.5 s post-death delay and 5 s fresh-start confirmation.
- Game end keeps actions armed in a live session; the hold is released by the guard
  while the player is dead.
- The engine `restart` fires `MC_PRE_GAME_EXIT` and closes the socket (evidence in
  reports/2026-10-17-restart-after-game-over.md). In a live session with a restart in
  flight the training approval is kept; a normal exit still drops it.
- Disconnect always releases input (unchanged).

## Python side

- `LiveClient` drains the socket in a reader thread into a bounded backlog (512).
  Without it, Lua closes the session when Python blocks during a PPO update (3 s output
  deadline). Reader failures are stored and re-raised to the caller.
- `EventDeriver` produces `OracleEvent`s from consecutive oracle blocks: spawn (amount
  `max_hp`), damage (HP decrease), kill (enemy vanished; remaining HP is credited as
  damage; suspended while overflowing), room clear (false→true within a visit), player
  damage/heal (red+soul half hearts; damage attributed to enemies), player death.
- `LiveBackend`: an episode is a segment of the continuing run. Death terminates;
  room clear terminates; 1800 updates truncate without any reset. `start_episode`
  continues from the latest playable state, reconnecting after a restart within 90 s.
  `step` sends one action of `repeat` frames and waits for a snapshot at or after
  `ack.frame_id + repeat` (5 s, extended while paused up to 600 s).
- An epoch change without an observed death is an `EpisodeFault`.
  `FaultTolerantEnv` truncates the segment with `info["fault"]` within a fault budget
  (default 20); protocol errors are never retried.

## Risks and trade-offs

- The game is not paused during PPO updates; the character idles. Mitigated by small
  `n_steps`. Future: pause support or asynchronous rollouts.
- Approximate labels can misattribute damage or kills; they are labeled approximate
  in documentation and are a reward hypothesis (reward-v1 coefficients unchanged).
- Frequent restarts may be unstable; budget and interval limit the rate.
- No exploration reward yet: after a clear the agent gets no incentive to leave the
  room (future reward-v2 with first-visit room reward).

## Primary Windows review: bounded failure paths

Enemy identity history retains only the current bounded oracle membership. A
missing identity during current/previous overflow is forgotten without inferring
a kill; it must be observed again before later complete-frame disappearance can
produce a new estimate. This prevents unbounded history under membership churn.

A reader ProtocolError is checked before reset calls connect/accept, since those
operations clear connection-local failure state. It must propagate as fatal.
Random and training runs pass one absolute deadline through the backend and fault
wrapper. Reset/reconnect/pause waits use the smaller remaining deadline, and
fault retries cannot renew it. Bounded in-flight I/O and ongoing model computation
may overrun until their next return; no subsequent action is sent after expiry.
Budget interruption during a rollout closes the environment and records no new
checkpoint claim for that unfinished rollout. Tests use fake time and fake peers;
this is not runtime acceptance.
