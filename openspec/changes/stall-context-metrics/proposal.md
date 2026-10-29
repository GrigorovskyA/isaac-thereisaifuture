## Why

In the last long run (reward v9, 450 late episodes: 284 stalls, 166 deaths) 58% of stalls ended
in a room that was not cleared (no new damage for 40 s while enemies remained), 24% in a cleared
room the agent did not leave, 18% in the start room. We need to know why before changing the
reward: unreachable, invulnerable or flying enemies, an unkillable "enemy" that keeps the room
uncleared, the agent avoiding enemies, or dead ends with no open door into an unexplored room.

## What Changes

- `episodes.csv` gains `last_room_clear` (every row) and `stall_*` columns, filled only for stall
  truncations from the last snapshot (entity frame, live oracle): room clear, type and shape;
  observed and oracle enemy counts; invulnerable, flying and boss enemy counts; distinct enemy
  `type.variant` kinds; nearest enemy distance; open doors and open unexplored doors; half
  hearts; seconds in the room (game updates since the room change or episode start / 30).
- `LiveBackend.oracle_enemy_count()` (metrics only). `EpisodeMetricsWriter` rewrites an older
  header once, like the `train.csv` upgrade; old rows get empty cells.
- Docs: `docs/TRAINING_SESSION.md`.

## Non-goals

- No change to the contract (hash `b26db425...` stays), observation, reward, actions or Lua.
- No policy input, no reward term and no change to the stall limit.
- No change to the dashboard or `compare_eval.py`; they ignore the new columns.

## Acceptance

- Offline gate and strict OpenSpec validation pass; tests cover a stall in an uncleared room with
  an invulnerable flying enemy, a death row with empty `stall_*`, the header upgrade and the
  unchanged contract hash.
- Native: in the next session every stall row has the `stall_*` columns filled.

## Impact

- `src/isaac_threrisaifuture/{env,episode_metrics,live}.py`, `tests/test_stall_context.py`,
  `docs/TRAINING_SESSION.md`.
