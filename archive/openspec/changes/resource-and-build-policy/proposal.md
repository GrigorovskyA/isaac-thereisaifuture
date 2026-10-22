## Why

Roadmap item 14: item, shop and consumable choices need bounded, exploit-free shaping and
an offline way to evaluate builds, so a learned build policy can be compared with random
choice without rewarding farming loops.

## What Changes

- Add `resources.py`: `ResourceState`, `ResourceEvent`, `ResourceLedger`, `Offer`,
  `BuildChooser` protocol, `RandomChooser` baseline, `evaluate_build`.
- Add tests for each exploit.

## Scope and non-goals

- Offline contract only. No real-game events, no item data, no learned chooser, no
  item-tier baseline (needs verified item data from item 13).
- This change MUST NOT be archived until real-game evidence exists.

## Dependencies and risks

- Real pickup/drop/spend/use events and entity identity must be verified in the bridge.
- Risk: item identity per drop may differ in the real game; item-level dedupe is per episode.
