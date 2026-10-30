"""Reward v11: a blocked door or live boss room costs `blocked_cost` = 0, so room entry is free."""

import random
from dataclasses import replace

import pytest
import yaml
from test_reward_v10 import (
    CAP,
    GAMMA,
    A,
    B,
    C,
    K,
    at,
    cost,
    dr,
    make,
    start,
    trajectory,
    trapdoor,
    visit,
)

from isaac_threrisaifuture.entities import BOSS_ROOM_TYPE
from isaac_threrisaifuture.rewards import (
    DEFAULT_CONFIG_V10,
    DEFAULT_CONFIG_V11,
    RewardV4Coefficients,
)

V10 = RewardV4Coefficients.load(DEFAULT_CONFIG_V10)
V11 = RewardV4Coefficients.load(DEFAULT_CONFIG_V11)


def enter_from_door(coef, doors_inside):
    """Walk from the door of cleared room A into unvisited room B; returns (paid, phi_before)."""
    value = make(coef)
    start(value, A, [dr(0, B, 100.0, 280.0), dr(1, C)], frame=at(100.0, 280.0))
    phi_before = value._phi
    paid = visit(value, B, doors_inside, at(300.0, 280.0, clear=False), enemies=True)
    return paid, phi_before


def test_v11_differs_from_v10_only_in_the_version_and_blocked_cost():
    v11 = yaml.safe_load(DEFAULT_CONFIG_V11.read_text("utf-8"))
    v10 = yaml.safe_load(DEFAULT_CONFIG_V10.read_text("utf-8"))
    assert v11.pop("reward_version") == 11 and v10.pop("reward_version") == 10
    assert v11["novelty"].pop("cross_run") is True  # the only novelty change
    assert v11.pop("door_shaping") == {"coefficient": 2.0, "max_hops": 5, "blocked_cost": 0.0}
    assert v10.pop("door_shaping") == {"coefficient": 2.0, "max_hops": 5}
    assert v11 == v10
    assert V10.door_shaping_blocked_cost == 1.0 and V11 == replace(
        V10, door_shaping_blocked_cost=0, novelty_cross_run=True
    )


def test_a_fighting_room_costs_one_under_v10_and_zero_under_v11():
    doors = [dr(0, B)]
    fighting = at(300, 280, clear=False)
    for coef, expected in ((V10, 1.0), (V11, 0.0)):
        value = make(coef)
        start(value, A, doors)
        assert cost(value, A, doors, fighting) == expected
        assert cost(value, A, doors, at(300, 280), enemies=True) == expected
        assert cost(value, A, [dr(0, B, open=False)], at(300, 280)) == expected
    # A calm room with an open door keeps the distance share under both.
    value = make(V11)
    start(value, A, doors)
    assert cost(value, A, doors, at(100, 280)) > 0.0


def test_entering_a_frontier_room_pays_nothing_under_v11_and_about_minus_two_under_v10():
    frontier = [dr(0, A, 20.0, 280.0), dr(1, C)]  # B has a door to unvisited C
    paid11, phi11 = enter_from_door(V11, frontier)
    paid10, phi10 = enter_from_door(V10, frontier)
    assert phi11 == 0.0 and phi10 == 0.0  # standing at the open door of the cleared room
    assert paid11 == pytest.approx(0.0, abs=1e-9)
    assert paid10 == pytest.approx(-K * GAMMA)  # the v10 entry penalty


def test_entering_a_dead_end_still_drops_the_potential_by_coefficient_times_hops():
    dead_end = [dr(0, A, 20.0, 280.0)]  # back to A, which still has the unvisited C
    paid, phi_before = enter_from_door(V11, dead_end)
    hops = 1  # B -> A, then A's door to C
    assert paid == pytest.approx(GAMMA * -K * hops - phi_before)
    assert paid < 0.0


def test_an_uncleared_boss_room_costs_zero_under_v11_and_one_under_v10():
    alive = at(room_type=BOSS_ROOM_TYPE, clear=False, entities=[trapdoor(10, 0)])
    for coef, expected in ((V10, 1.0), (V11, 0.0)):
        value = make(coef)
        start(value, A, [dr(0, B)])
        assert cost(value, B, [dr(0, A)], alive) == expected
        assert cost(value, B, [dr(0, A)], at(room_type=BOSS_ROOM_TYPE), enemies=True) == expected
    # The cleared boss room still pays the trapdoor distance share.
    value = make(V11)
    start(value, A, [dr(0, B)])
    clear_boss = at(room_type=BOSS_ROOM_TYPE, entities=[trapdoor(300, 400)])
    assert cost(value, B, [dr(0, A)], clear_boss) > 0.0


def test_no_goal_door_keeps_the_constant_one_plus_the_cap():
    value = make(V11)
    start(value, A, [])
    assert value._phi == -K * (1 + CAP)


@pytest.mark.parametrize("seed", range(8))
def test_discounted_shaping_telescopes_to_minus_the_first_potential_under_v11(seed):
    rng = random.Random(seed)
    value = make(V11)
    first, doors, position, _ = next(trajectory(random.Random(seed), 1))
    start(value, first, doors, frame=position)
    phi0 = value._phi
    steps = list(trajectory(rng, 60))
    total = 0.0
    for t, (room, doors, position, enemies) in enumerate(steps):
        last = t == len(steps) - 1
        total += GAMMA**t * visit(value, room, doors, position, enemies=enemies, terminal=last)
    assert total == pytest.approx(-phi0, abs=1e-9)


def test_the_loader_validates_blocked_cost(tmp_path):
    raw = yaml.safe_load(DEFAULT_CONFIG_V11.read_text("utf-8"))
    cases = {
        "missing": lambda r: r["door_shaping"].pop("blocked_cost"),
        "negative": lambda r: r["door_shaping"].update(blocked_cost=-0.5),
        "bool": lambda r: r["door_shaping"].update(blocked_cost=False),
        "text": lambda r: r["door_shaping"].update(blocked_cost="0"),
    }
    for name, mutate in cases.items():
        bad = yaml.safe_load(yaml.safe_dump(raw))
        mutate(bad)
        path = tmp_path / f"{name}.yaml"
        path.write_text(yaml.safe_dump(bad), "utf-8")
        with pytest.raises(ValueError):
            RewardV4Coefficients.load(path)
    ok = yaml.safe_load(yaml.safe_dump(raw))
    ok["door_shaping"]["blocked_cost"] = 0.5
    path = tmp_path / "half.yaml"
    path.write_text(yaml.safe_dump(ok), "utf-8")
    assert RewardV4Coefficients.load(path).door_shaping_blocked_cost == 0.5


def test_the_loader_rejects_blocked_cost_in_v10(tmp_path):
    raw = yaml.safe_load(DEFAULT_CONFIG_V10.read_text("utf-8"))
    raw["door_shaping"]["blocked_cost"] = 0.0
    path = tmp_path / "v10_blocked.yaml"
    path.write_text(yaml.safe_dump(raw), "utf-8")
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(path)
    with pytest.raises(ValueError):
        replace(V11, door_shaping_blocked_cost=-1.0)
