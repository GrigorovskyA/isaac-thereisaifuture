## Why

A pedestal item on the floor reaches the policy as one pickup-variant bit, one number (item ID
divided by 1024) and a shop flag. The active item is likewise one number. The network cannot tell
two items apart, so it cannot learn item synergies, for example which items fit a transformation
or which pedestal is worth taking. Observation schema 8 gave every enemy an identity bucket;
items have none.

The reward v11 run has not trained yet, so the lineage restarts once for both changes. Observation
schema 9 is launched together with reward v11.

## What Changes

- Observation schema 9 on wire frame schema 7; reward v11 unchanged.
- Pedestal collectibles (pickup variant 100, subtype > 0) carry ItemConfig catalog facts on the
  wire: `item_quality` (0-4), `item_type` (passive, active, familiar, unknown), `item_max_charges`
  and `item_tags` (a bit mask over 8 tags). All four go together and appear on those pickups only.
- The inventory carries `active_quality` and `active_tags` for the active item.
- The frame carries `tag_counts`: held collectibles per tag, recomputed with the held list.
- Tags are the transformation sets read by name from the game (`ItemConfig.TAG_<NAME>`): GUPPY,
  FLY, MUSHROOM, SYRINGE, BOB, SPIDER, BABY, MOM. A name missing from the game reads as no tag.
- Encoder: a pedestal slot grows from 22 to 99 floats (quality, type one-hot, max charges, tag
  bits, 64-bucket identity one-hot). The inventory block grows from 9 to 82 floats (quality, tag
  bits, 64-bucket one-hot of the active item). A new block holds the held tag counts (8, count / 3
  clipped). The bucket is `(item_id * 2654435761 mod 2^32) >> 26`.
- A blind pedestal (curse of the blind) hides its item: if `pickup:IsBlind()` exists and is true
  or the level has the curse of the blind, the observer exports subtype 0 and no facts.
- `OBSERVATION_SIZE` 9762 -> 11691. `configs/training-pure-v4.yaml` pins schema 9 with a new
  contract hash; schema 8 checkpoints are refused. Hyperparameters and reward are unchanged.

## Non-goals

- No reward change (reward v11), no action change, no hyperparameter change.
- No predicted stat changes, no "good item" ranking, no advice features: only what the game's
  ItemConfig says about an item (quality, type, charges, tags).
- The 1024-wide held collectible multi-hot is unchanged.
- No new wire capability: the facts ride in the existing entity frame.

## Acceptance

- (a) Offline gate: `scripts/check.sh` or `scripts/Check.ps1` and strict OpenSpec validation.
- (b) Native passive audit: a pedestal collectible shows a non-zero quality and bucket, the
  maximum snapshot bytes stay below the 131072 cap, and the held tag counts change after taking
  a tagged item.
- (c) Later: the lineage trains with reward v11; no acceptance claim before a native run.

## Impact

`mod/observer/main.lua`, `src/isaac_threrisaifuture/{entities,encoding,sim}.py`,
`configs/training-pure-v4.yaml`, tests, docs. The mod must be redeployed with the code: Python
refuses frames of schema 6. Unverified natively: the ItemConfig field names (`Quality`, `Type`,
`MaxCharges`), `ItemConfigItem:HasTags`, the `ItemConfig.TAG_*` names, the ItemType names and
numbers, and `EntityPickup:IsBlind()` (whether it exists and hides the item under the curse).
