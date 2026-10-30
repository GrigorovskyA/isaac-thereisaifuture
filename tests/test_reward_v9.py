"""Reward v9: denser exploration terms, the boss clear bonus and potential-based door shaping."""

from pathlib import Path

import numpy as np
import pytest
import yaml
from synthetic import event, frame, room_facts
from test_reward_v4 import ARCHIVED_V8, LIVE_SCENARIO, pickup

from isaac_threrisaifuture.encoding import room_diagonal
from isaac_threrisaifuture.entities import BOSS_ROOM_TYPE, OracleDoor, Vec
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import FIELDS
from isaac_threrisaifuture.episodes import StepResult
from isaac_threrisaifuture.rewards import (
    DEFAULT_CONFIG_V9,
    REWARD_V4_COLUMNS,
    RewardLedgerV4,
    RewardV4Coefficients,
)
from isaac_threrisaifuture.training import load_training_config

ROOT = Path(__file__).parents[1]
TRAINING = ROOT / "configs" / "training-pure-v4.yaml"
CONFIG, _ = load_training_config(TRAINING)
GAMMA = CONFIG.hyperparameters.gamma
STALL_SECONDS = CONFIG.watchdog.stall_seconds
COEF = RewardV4Coefficients.load(DEFAULT_CONFIG_V9)
DIAGONAL = room_diagonal(1)


def ledger(gamma=GAMMA, *, start=None, doors=None, room=1, **begin) -> RewardLedgerV4:
    value = RewardLedgerV4(COEF, stall_seconds=STALL_SECONDS, gamma=gamma)
    value.reset(1)
    value.begin(start or frame(), room, doors, **begin)
    return value


def door(slot=0, x=580.0, y=280.0, *, open=True, unexplored=True) -> OracleDoor:
    return OracleDoor(slot=slot, x=x, y=y, open=open, unexplored=unexplored, target=85, usable=True)


def at(x, y, *, clear=True, **changes):
    return frame(player_position=Vec(x=x, y=y), room=room_facts(clear=clear), **changes)


def walk(value, positions, doors, *, clear=True, enemies=False, terminal_last=False):
    """Door shaping paid for each position in turn."""
    paid = []
    for index, (x, y) in enumerate(positions):
        last = terminal_last and index == len(positions) - 1
        _, parts = value.consume(
            [], 0, at(x, y, clear=clear), 1, doors, enemies_present=enemies, terminal=last
        )
        paid.append(parts["door_shaping"])
    return paid


# --- configuration ---------------------------------------------------------------------


def test_v9_coefficients_are_the_shipped_file():
    assert COEF.room_first_visit == 5.0 and COEF.floor_first_entered == 30.0
    assert COEF.boss_room_clear_first == 20.0 and COEF.room_clear_first == 10.0
    assert (COEF.coin, COEF.bomb, COEF.key) == (0.3, 0.5, 0.5)
    assert COEF.consumable_run_cap == 10.0 and COEF.collectible_new == 5.0
    assert COEF.heal_half_heart == 0.5
    assert COEF.novelty_coefficient == 0.1 and COEF.novelty_cell_size == 40
    assert COEF.door_shaping_coefficient == 2.0
    assert RewardV4Coefficients.load() == COEF  # the default file


def test_v9_differs_from_v8_only_in_the_documented_terms():
    v9 = yaml.safe_load(DEFAULT_CONFIG_V9.read_text("utf-8"))
    v8 = yaml.safe_load(ARCHIVED_V8.read_text("utf-8"))
    assert v9.pop("reward_version") == 9 and v8.pop("reward_version") == 8
    assert v9.pop("door_shaping") == {"coefficient": 2.0}
    assert v9["outcome"].pop("boss_room_clear_first") == 20.0
    for section, changed in (
        ("outcome", {"room_first_visit": (5.0, 3.0), "floor_first_entered": (30.0, 10.0)}),
        ("pickups", dict(coin=(0.3, 0.05), bomb=(0.5, 0.1), key=(0.5, 0.1),
                         consumable_run_cap=(10.0, 3.0), collectible_new=(5.0, 2.0))),
        ("novelty", {"coefficient": (0.1, 0.02)}),
    ):  # fmt: skip
        for key, (new, old) in changed.items():
            assert v9[section].pop(key) == new and v8[section].pop(key) == old
    assert v9 == v8  # stagnation, death, damage, stall restart and the rest are unchanged


def test_v8_stays_loadable_without_the_v9_terms():
    old = RewardV4Coefficients.load(ARCHIVED_V8)
    assert old.door_shaping_coefficient == 0.0 and old.boss_room_clear_first == 0.0


def test_the_v9_sections_are_required_and_strict(tmp_path):
    raw = yaml.safe_load(DEFAULT_CONFIG_V9.read_text("utf-8"))
    mutations = {
        "no_door_shaping": lambda r: r.pop("door_shaping"),
        "no_boss": lambda r: r["outcome"].pop("boss_room_clear_first"),
        "extra_key": lambda r: r["door_shaping"].update(extra=1.0),
        "text": lambda r: r["door_shaping"].update(coefficient="2"),
        "negative": lambda r: r["door_shaping"].update(coefficient=-1.0),
    }
    for name, mutate in mutations.items():
        bad = yaml.safe_load(yaml.safe_dump(raw))
        mutate(bad)
        path = tmp_path / f"{name}.yaml"
        path.write_text(yaml.safe_dump(bad), "utf-8")
        with pytest.raises(ValueError):
            RewardV4Coefficients.load(path)
    v8 = yaml.safe_load(ARCHIVED_V8.read_text("utf-8"))
    path = tmp_path / "v8_with_shaping.yaml"
    path.write_text(yaml.safe_dump({**v8, "door_shaping": {"coefficient": 2.0}}), "utf-8")
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(path)


def test_the_training_config_pins_the_current_contract_and_the_entropy_coefficient():
    assert CONFIG.contract.reward_version == 10 and CONFIG.contract.observation_schema_version == 8
    assert CONFIG.hyperparameters.ent_coef == 0.005 and STALL_SECONDS == 40.0


def test_a_full_stall_still_never_pays_more_than_death_from_full_health():
    full_stall = COEF.stall_restart + COEF.stagnation_per_second * (
        STALL_SECONDS - COEF.stagnation_grace_seconds
    )
    assert full_stall == -12.0
    assert full_stall >= COEF.death + 6 * COEF.player_damage_half_heart


def test_door_shaping_needs_gamma():
    with pytest.raises(ValueError, match="gamma"):
        RewardLedgerV4(COEF)
    with pytest.raises(ValueError, match="gamma"):
        RewardLedgerV4(COEF, gamma=1.5)
    assert RewardLedgerV4(RewardV4Coefficients.load(ARCHIVED_V8))  # v8 never shapes


def test_the_door_shaping_column_exists_and_reaches_the_episode_file():
    assert "door_shaping" in REWARD_V4_COLUMNS and "col_door_shaping" in FIELDS


# --- boss clear ------------------------------------------------------------------------


def test_the_first_clear_of_a_boss_room_pays_the_bonus_once():
    boss = frame(room=room_facts(type=BOSS_ROOM_TYPE))
    value = ledger(start=boss, room=7)
    _, parts = value.consume([event("room_cleared", room_index=7)], 0, boss, 7)
    assert parts["room_clear"] == COEF.room_clear_first + COEF.boss_room_clear_first == 30.0
    _, again = value.consume([event("room_cleared", room_index=7, frame_id=2)], 0, boss, 7)
    assert again["room_clear"] == 0.0  # per run, like room_clear_first


def test_other_room_types_get_no_boss_bonus_and_a_second_boss_room_pays_again():
    value = ledger(room=1)
    treasure = frame(room=room_facts(type=4))
    _, parts = value.consume([event("room_cleared", room_index=1)], 0, treasure, 1)
    assert parts["room_clear"] == COEF.room_clear_first
    second_boss = frame(room=room_facts(type=BOSS_ROOM_TYPE, stage=2))
    _, parts = value.consume([event("room_cleared", room_index=1)], 0, second_boss, 1)
    assert parts["room_clear"] == 30.0  # another floor's boss room is another room


# --- door shaping ----------------------------------------------------------------------


def test_potential_is_minus_the_scaled_distance_to_the_nearest_open_unexplored_door():
    doors = [door(0, 580, 280), door(1, 60, 280), door(2, 320, 140, open=False)]
    value = ledger(doors=doors, start=at(100, 280))
    # Phi(start) = -2 * 40 / D; standing still pays (gamma - 1) * Phi.
    _, parts = value.consume([], 0, at(100, 280), 1, doors)
    assert parts["door_shaping"] == pytest.approx((GAMMA - 1) * -2.0 * 40.0 / DIAGONAL)


def test_walking_toward_a_door_pays_and_walking_away_costs():
    doors = [door()]
    value = ledger(doors=doors, start=at(100, 280))
    toward = walk(value, [(200, 280), (300, 280), (400, 280)], doors)
    assert all(paid > 0 for paid in toward)
    assert sum(toward) == pytest.approx(2.0 * 300 / DIAGONAL, rel=0.01)
    away = walk(value, [(300, 280), (200, 280), (100, 280)], doors)
    assert all(paid < 0 for paid in away)


def test_a_closed_loop_nets_nothing_but_the_discount_term():
    doors = [door()]
    loop = [(200, 280), (300, 280), (400, 280), (300, 280), (200, 280), (100, 280)]
    exact = ledger(1.0, doors=doors, start=at(100, 280))  # no discount: potentials telescope
    assert sum(walk(exact, loop, doors)) == pytest.approx(0.0, abs=1e-9)
    value = ledger(doors=doors, start=at(100, 280))
    net = sum(walk(value, loop, doors))
    # With gamma < 1 the net is (gamma - 1) times the potentials visited: small, never a farm.
    assert 0.0 <= net <= (1 - GAMMA) * COEF.door_shaping_coefficient * len(loop)
    repeated = ledger(doors=doors, start=at(100, 280))
    steps = 50 * len(loop)  # walking back and forth for 300 steps
    assert (
        sum(walk(repeated, loop * 50, doors)) <= (1 - GAMMA) * COEF.door_shaping_coefficient * steps
    )


def test_standing_still_pays_only_the_discount_term():
    doors = [door()]
    value = ledger(doors=doors, start=at(100, 280))
    paid = walk(value, [(100, 280)] * 180, doors)  # a 40 s stall at 4.5 steps per second
    phi = -2.0 * min(480 / DIAGONAL, 1.0)
    assert all(p == pytest.approx((GAMMA - 1) * phi) for p in paid)
    assert 0 < sum(paid) < 1.0


def test_a_room_with_enemies_or_not_clear_pays_nothing():
    doors = [door()]
    for clear, enemies in ((True, True), (False, False), (False, True)):
        value = ledger(doors=doors, start=at(100, 280, clear=clear), enemies_present=enemies)
        paid = walk(
            value, [(100, 280), (300, 280), (500, 280)], doors, clear=clear, enemies=enemies
        )
        assert paid == [0.0, 0.0, 0.0]


def test_doors_that_are_closed_explored_or_unknown_pay_nothing():
    for doors in ([door(open=False)], [door(unexplored=False)], [], None):
        value = ledger(doors=doors, start=at(100, 280))
        assert walk(value, [(300, 280), (500, 280)], doors) == [0.0, 0.0]


def test_a_visited_room_pays_no_shaping_toward_its_visited_targets():
    # Re-entering room A: its door to B is explored, so only the unexplored door C counts.
    doors = [door(0, 580, 280, unexplored=False), door(1, 60, 280)]
    value = ledger(doors=doors, start=at(300, 280))
    toward_visited = walk(value, [(400, 280), (500, 280), (570, 280)], doors)
    assert all(paid < 0 for paid in toward_visited)  # moving away from the unexplored door
    only_visited = [door(0, 580, 280, unexplored=False)]
    value = ledger(doors=only_visited, start=at(300, 280))
    assert walk(value, [(400, 280), (500, 280), (570, 280)], only_visited) == [0.0, 0.0, 0.0]


def test_the_first_step_pays_no_bonus_because_begin_sets_the_starting_potential():
    doors = [door()]
    value = ledger(doors=doors, start=at(100, 280))
    first = walk(value, [(100, 280)], doors)[0]
    assert abs(first) < 0.01  # not gamma * Phi, about 2 * 480 / D = 1.5


def test_a_terminal_step_ends_in_zero_potential():
    doors = [door()]
    value = ledger(doors=doors, start=at(100, 280))
    walk(value, [(200, 280)], doors)
    phi = -2.0 * 380 / DIAGONAL
    last = walk(value, [(200, 280)], doors, terminal_last=True)[0]
    assert last == pytest.approx(-phi)  # gamma * 0 - Phi(s)
    assert value._phi == 0.0


def test_death_pays_nothing_further_and_a_dead_player_has_no_potential():
    doors = [door()]
    value = ledger(doors=doors, start=at(100, 280))
    _, parts = value.consume([event("player_died")], 0, at(100, 280), 1, doors, terminal=True)
    assert parts["death"] == COEF.death
    assert parts["door_shaping"] == pytest.approx(2.0 * 480 / DIAGONAL)
    assert value._potential(at(100, 280), doors, False) == 0.0


def test_a_room_change_uses_the_old_potential_and_the_new_rooms():
    old = [door(0, 580, 280)]
    value = ledger(doors=old, start=at(560, 280))  # beside the door of the first room
    new = [door(1, 60, 280)]  # the next room, entered from the west
    _, parts = value.consume(
        [event("room_entered", room_index=2)], 0, at(100, 280, game_epoch=1), 2, new
    )
    phi_old, phi_new = -2.0 * 20 / DIAGONAL, -2.0 * 40 / DIAGONAL
    assert parts["door_shaping"] == pytest.approx(GAMMA * phi_new - phi_old)
    assert parts["room_visit"] == COEF.room_first_visit


def test_the_total_over_a_room_crossing_is_bounded_by_the_coefficient():
    doors = [door()]
    value = ledger(doors=doors, start=at(100, 280))
    path = [(100 + 20 * i, 280) for i in range(1, 24)]
    paid = walk(value, path, doors)
    # Leaving into a room with enemies drops the potential to zero.
    _, leave = value.consume([event("room_entered", room_index=2)], 0, at(100, 280), 2, [], True)
    assert 0 < sum(paid) + leave["door_shaping"] <= COEF.door_shaping_coefficient


def test_the_distance_scale_is_clipped_to_one():
    doors = [door(0, 9000, 9000)]
    value = ledger(doors=doors, start=at(100, 280))
    assert value._potential(at(100, 280), doors, False) == -COEF.door_shaping_coefficient


def test_the_v8_ledger_pays_no_shaping():
    value = RewardLedgerV4(RewardV4Coefficients.load(ARCHIVED_V8))
    value.begin(at(100, 280), 1, [door()])
    _, parts = value.consume([], 0, at(300, 280), 1, [door()])
    assert parts["door_shaping"] == 0.0


# --- environment -----------------------------------------------------------------------


class Rooms:
    """Backend with prepared frames, doors and enemy flags; one game update per step."""

    supports_seed = False

    def __init__(self, steps):
        self.steps = list(steps)

    def start_episode(self, scenario, seed):
        return self._result(*self.steps.pop(0))

    def step(self, action, repeat):
        return self._result(*self.steps.pop(0))

    @staticmethod
    def _result(frame_id, x, doors, enemies=False, events=()):
        return StepResult(
            at(x, 280, frame_id=frame_id),
            tuple(event(kind, frame_id, **fields) for kind, fields in events),
            room_index=1,
            doors=doors,
            enemies_present=enemies,
        )

    def release(self):
        pass

    def close(self):
        pass


def test_the_env_passes_doors_enemies_and_the_terminal_flag_to_the_ledger():
    doors = (door(),)
    steps = [
        (1, 100, doors),
        (2, 200, doors),
        (3, 300, doors, True),  # enemies appear: the potential drops to zero
        (4, 300, doors, True, [("player_died", {})]),
    ]
    env = IsaacCombatEnv(
        Rooms(steps), [LIVE_SCENARIO], accountant=RewardLedgerV4(COEF, gamma=GAMMA)
    )
    env.reset()
    results = [env.step(np.array([0, 0, 0])) for _ in range(3)]
    paid = [r[4]["reward_components"]["door_shaping"] for r in results]
    assert paid[0] > 0
    assert paid[1] == pytest.approx(2.0 * 380 / DIAGONAL)  # enemies appeared: Phi -> 0
    assert paid[2] == 0.0
    assert results[2][2] is True  # the death ends the episode
    assert env._columns["door_shaping"] == pytest.approx(sum(paid))


def test_pickups_pay_the_v9_rates_inside_the_cap():
    value = ledger()
    _, parts = value.consume([pickup("coin", 10, 10)], 0)
    assert parts["pickup_coin"] == pytest.approx(3.0)
    _, parts = value.consume([pickup("bomb", 20, 20)], 0)
    assert parts["pickup_bomb"] == pytest.approx(7.0)  # capped at 10 for the run
