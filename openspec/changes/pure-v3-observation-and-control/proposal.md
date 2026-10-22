## Why

After 23k `pure-v2` steps (45 updates) the policy is still 96% of maximum entropy:
bomb 0.245, movement 0.185-0.221 per direction. Three causes are in the setup, not
in the time budget alone:

- The agent cannot see its own attacks (tears, lasers, knives) or placed bombs, so
  it cannot learn to aim or to step away from its own bomb; it also cannot see its
  stats, tear flags or weapon type, so item effects such as spectral tears or
  Brimstone are invisible except through the item ID multi-hot.
- A decision every 3 game updates (0.1 s) makes random movement jitter in place,
  so doors are reached rarely and the bomb-to-explosion delay spans ~15 decisions.
- The use head starts uniform, so 75% of decisions press bomb/item/card and the
  single starting bomb is placed almost immediately.

## What Changes

- Observation schema 4: player stats (damage, tears per second, range, shot
  speed, move speed, luck), 16 tear-flag bits, weapon-type multi-hot, and new
  entity kinds `own_attack` (own tears, lasers, knives) and `bomb` (all bombs, with
  age). Facts from the game API only; no external item knowledge.
- Message limit 16 KiB -> 32 KiB on both sides for the larger frames.
- Decisions hold 6 game updates (0.2 s).
- The use head starts at P(none)=0.85, 0.05 for each press (initial logits only;
  learning may move them anywhere).
- Reward v4: new collectible 2.0 per item ID per run (was 1.0); everything else
  as reward v3.
- New lineage `pure-v3` (`configs/training-pure-v3.yaml`, `runs/pure-v3`).
  `pure-v2` is preserved, not resumed. The synthetic knowledge fixture
  `data/knowledge/` moves to `archive/`.

## Capabilities

### Modified Capabilities

- `pure-observation`, `pure-actions`, `pure-reward` (deltas here; base
  requirements live in the unarchived `pure-self-learning-v1`).

## Non-goals

- Scraped or curated item knowledge (dead-god.ru, wikis) or item quality from
  ItemConfig. Revisit only with evidence that game facts are insufficient.
- Familiars, technique rewards, masks or scripted control.

## Impact

Lua observer, wire models, encoder, env/action repeat, model initialisation,
reward config, lineage config, dashboard defaults, docs and tests. Requires
redeploying `mod/observer` and a short native check. Unverified natively: stat
and tear-flag API values, weapon-type detection, own-attack spawner attribution,
bomb age, snapshot size under heavy attack counts.
