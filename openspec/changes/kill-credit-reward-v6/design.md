## Lua

- `metrics.killed`: array of identities, capped at 16 (drop the oldest), reset with the
  other metrics on game start.
- In `MC_POST_NPC_DEATH`, for an unfriendly enemy, compute the same key as the capture
  loop (`"e:" .. GetPtrHash(npc) .. ":" .. npc.InitSeed`). If `entities.ids[key]` exists
  (the enemy was listed in the oracle this room visit), append that id. Everything stays
  inside the existing `pcall`.
- The oracle sends `killed` (JSON array; empty array when none).

## Python

- `LiveOracle.killed: list[EntityId]`, max length 16, metrics/reward label only.
- `EventDeriver`: after processing the current enemies of the same room visit, for every
  id in `oracle.killed` that is not in the current list and has a stored HP floor above
  zero, emit `enemy_damaged(entity_id, amount=floor)` and store floor 0. The ring is
  re-sent every snapshot; a zero floor makes repeats pay nothing. An identity whose max
  HP changed already has floor 0 and pays nothing.
- A new game epoch clears the floors as today, so ids from another run cannot pay.
- Reward version 6 uses the same ledger as v4/v5 (`REWARD_V4_VERSIONS` gains 6);
  `PURE_REWARD_VERSION = 6`, `LIVE_REWARD_CONTRACT = "pure-v6"`,
  `RewardContract` replaces `pure-v5` with `pure-v6`, `make_live_env` accepts 1 or 6.

## Exploit check

Total credit per identity stays at most max HP: the floor only falls, the kill credit
pays the floor and zeroes it. Re-sent ids, a re-listed identity and a new room visit
pay nothing more. The damage-then-heal case keeps its floor rule.
