## Why

Roadmap item 07 needs a reward ledger that cannot be farmed, so that later baselines and PPO runs are comparable. Reward coefficients in `configs/reward-v1.yaml` are hypotheses and are loaded, not hard-coded.

## What Changes

- Add `rewards.py`: `CombatCoefficients.load` and `RewardLedger`, which implements the `RewardAccountant` protocol.
- Credit enemy damage once per entity identity (entity id plus spawn generation), capped by initial HP, so healed HP is never paid twice.
- Add `scenarios.py` (fixed disjoint train/validation/test splits, versioned), `baselines.py` (random and labelled scripted policies) and `evaluation.py` (equal-budget evaluation, Wilson CI, separate fault reporting, JSON report).
- Pay kill, first room clear, and death at most once; ignore duplicate events.

## Non-goals

- Learned policies; baselines are non-learning references only.
- Real-game validation; the ledger is verified only against synthetic events.

## Impact

- New module `rewards.py`, new tests `tests/test_rewards.py`. Offline contract only; the change must not be archived until real events are observed.
