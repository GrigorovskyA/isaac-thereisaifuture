## Context

Held collectibles are a 1024-wide multi-hot, so the policy already knows what it carries. What it
lacks is the identity of what it sees: pedestals and the active slot.

## Decisions

- Identity bucket: a Knuth multiplicative hash of the item ID, top 6 bits, 64 buckets. About 729
  items share 64 buckets (about 11 per bucket); the first linear layer learns one embedding per
  bucket. Same idea as the enemy identity, a different function (one key, no type shift).
- Catalog facts only: quality, type, max charges and tag bits come from `ItemConfig`. Tag bits are
  the game's own transformation sets (8 of them), so the agent can see which items count toward a
  transformation. No predicted effects, no ranking.
- The tag list lives in one constant per side (`ITEM_TAGS` in `entities.py`, `item_tag_names` in
  `main.lua`); a test compares them. Bit i of a mask is entry i. The Lua side reads each flag from
  the game (`ItemConfig.TAG_<NAME>`, missing = 0), so no number is hard-coded.
- Wire: item facts are optional fields, omitted off pedestals (like the enemy identity), so frame
  size grows only with pedestals. Worst case (all 24 pickup slots are pedestals, 256 held items
  with every tag): 81 KB Lua entity frame, 85 KB live snapshot, 111 KB Python extreme-number
  case, under the 131072 cap.
- Held tag counts are computed when the held list is recomputed (every 30 frames, room change or
  game start), not every frame.
- Blind pedestals: the item is hidden in game, so the observer exports subtype 0 and no facts when
  `IsBlind()` reports true or the level has the curse of the blind (`LevelCurse.CURSE_OF_BLIND`,
  bit 64), which covers the plain Repentance API without `IsBlind()`. Unreadable curses also hide
  the item. Other "?" pedestals (alt-path choices) rely on `IsBlind()` and are checked natively.
- This change supersedes the schema 8 layout numbers (9762 floats); the schema 8 delta specs
  describe the layout before this change.

## Risks

- The first layer grows by about 1900 inputs (9762 -> 11691); one update takes slightly longer.
- Two items can share a bucket; the type, quality and tag bits still tell most of them apart.
