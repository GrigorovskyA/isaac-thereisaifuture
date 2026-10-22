## Why

Roadmap item 12: define the strategic (floor) layer and its interface to low-level combat so
room selection, boss routing and floor completion can be measured and later learned. This is an
offline contract and MUST NOT be archived until real-game evidence exists.

## What Changes

- Add `floors.py`: `FloorPolicy` protocol, `FloorView`, `FloorDecision`, `FloorExecutor`,
  `RandomFloorPolicy`, `ScriptedFloorPolicy` (labelled scripted), `FloorMetrics`, `aggregate`.
- Add `tests/test_floors.py` with an explicitly synthetic floor simulator.

## Scope and non-goals

- In scope: options (clear room, take item, go boss, descend) over known rooms only, boss-routing
  precondition, option executor delegating combat to an injected callable, floor metrics.
- Out of scope: the learned floor policy, real navigation (item 11), real-game floors.
- A scripted policy does not establish learned route planning; decisions carry a source label.

## Dependencies and risks

- Uses plain room tuples; the navigation module will adapt its known map to `FloorView`.
- Risk: the synthetic floor hides real layout, secret rooms and door/lock complexity.

## Acceptance criteria

- Offline: decisions target only known rooms; boss routing requires a known boss room.
- Offline: timeout/truncation, death and infrastructure fault are distinct outcomes.
- Offline: baselines are deterministic per seed; decision budget bounds loops.
- Pending real game: autonomous exploration of a bounded floor set on unseen seeds.

## Impact

New module and tests only.
