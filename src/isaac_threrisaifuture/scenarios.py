"""Fixed, bounded combat scenario pool with disjoint train/validation/test splits.

The synthetic fields (enemy count and HP) are toy values, not game data. Changing any scenario
or split assignment requires a new SCENARIO_SET_VERSION so that reports stay comparable.
"""

from .episodes import Scenario, Split

SCENARIO_SET_VERSION = "synthetic-combat-v1"
SPLITS: tuple[Split, ...] = ("train", "validation", "test")
_TIME_LIMIT = 900  # game updates (30 s)

SCENARIOS: tuple[Scenario, ...] = (
    Scenario("train-d1-a", "train", 1, _TIME_LIMIT, enemy_count=1, enemy_hp=7.0),
    Scenario("train-d2-a", "train", 2, _TIME_LIMIT, enemy_count=2, enemy_hp=10.5),
    Scenario("train-d3-a", "train", 3, _TIME_LIMIT, enemy_count=4, enemy_hp=14.0),
    Scenario("val-d1-a", "validation", 1, _TIME_LIMIT, enemy_count=1, enemy_hp=10.5),
    Scenario("val-d2-a", "validation", 2, _TIME_LIMIT, enemy_count=3, enemy_hp=7.0),
    Scenario("val-d3-a", "validation", 3, _TIME_LIMIT, enemy_count=5, enemy_hp=10.5),
    Scenario("test-d1-a", "test", 1, _TIME_LIMIT, enemy_count=2, enemy_hp=7.0),
    Scenario("test-d2-a", "test", 2, _TIME_LIMIT, enemy_count=3, enemy_hp=14.0),
    Scenario("test-d3-a", "test", 3, _TIME_LIMIT, enemy_count=6, enemy_hp=10.5),
)


def scenarios_for(split: Split) -> tuple[Scenario, ...]:
    if split not in SPLITS:
        raise ValueError(f"Unknown split {split!r}")
    return tuple(s for s in SCENARIOS if s.split == split)
