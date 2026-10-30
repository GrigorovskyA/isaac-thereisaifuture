"""Reward v10: the door potential counts the rooms still to cross through the doors seen."""

import csv
import random
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import yaml
from synthetic import event, frame, room_facts
from test_reward_v4 import LIVE_SCENARIO

from isaac_threrisaifuture.encoding import room_diagonal
from isaac_threrisaifuture.entities import BOSS_ROOM_TYPE, Entity, OracleDoor, Vec
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import EpisodeMetricsWriter
from isaac_threrisaifuture.episodes import StepResult
from isaac_threrisaifuture.rewards import (
    DEFAULT_CONFIG_V9,
    DEFAULT_CONFIG_V10,
    RewardLedgerV4,
    RewardV4Coefficients,
)
from isaac_threrisaifuture.room_graph import RoomGraph
from isaac_threrisaifuture.training import load_training_config

ROOT = Path(__file__).parents[1]
CONFIG, _ = load_training_config(ROOT / "configs" / "training-pure-v4.yaml")
GAMMA = CONFIG.hyperparameters.gamma
STALL_SECONDS = CONFIG.watchdog.stall_seconds
COEF = RewardV4Coefficients.load(DEFAULT_CONFIG_V10)
CAP = COEF.door_shaping_max_hops
K = COEF.door_shaping_coefficient
DIAGONAL = room_diagonal(1)
A, B, C, D, E = 84, 85, 86, 87, 88  # level grid indexes


def dr(slot, target, x=580.0, y=280.0, *, open=True, usable=True) -> OracleDoor:
    return OracleDoor(slot=slot, x=x, y=y, open=open, unexplored=True, target=target, usable=usable)


def at(x=100.0, y=280.0, *, clear=True, stage=1, room_type=1, entities=None, **changes):
    room = room_facts(clear=clear, stage=stage, type=room_type)
    return frame(entities, player_position=Vec(x=x, y=y), room=room, **changes)


def trapdoor(x, y) -> Entity:
    return Entity(
        kind="obstacle",
        entity_id=1,
        spawn_generation=0,
        position=Vec(x=x, y=y),
        obstacle_class="trapdoor",
    )


def make(coef=COEF, gamma=GAMMA) -> RewardLedgerV4:
    return RewardLedgerV4(coef, stall_seconds=STALL_SECONDS, gamma=gamma)


def start(value, grid, doors, **kw) -> None:
    value.reset(1)
    value.begin(kw.pop("frame", at()), 1, doors, kw.pop("enemies", False), grid)


def visit(value, grid, doors, f=None, *, enemies=False, terminal=False):
    """One consumed step in a room; returns the door shaping paid."""
    _, parts = value.consume(
        [], 0, f or at(), 1, doors, enemies_present=enemies, terminal=terminal, room_grid=grid
    )
    return parts["door_shaping"]


def cost(value, grid, doors, f=None, *, enemies=False) -> float:
    """Graph cost of the state; sees the room like a consumed step does."""
    return -value._potential(f or at(), doors, enemies, grid) / K


# --- configuration ---------------------------------------------------------------------


def test_v10_differs_from_v9_only_in_the_door_shaping_section():
    v10 = yaml.safe_load(DEFAULT_CONFIG_V10.read_text("utf-8"))
    v9 = yaml.safe_load(DEFAULT_CONFIG_V9.read_text("utf-8"))
    assert v10.pop("reward_version") == 10 and v9.pop("reward_version") == 9
    assert v10.pop("door_shaping") == {"coefficient": 2.0, "max_hops": 5}
    assert v9.pop("door_shaping") == {"coefficient": 2.0}
    assert v10 == v9
    old = RewardV4Coefficients.load(DEFAULT_CONFIG_V9)
    assert COEF == replace(old, door_shaping_max_hops=5) and old.door_shaping_max_hops == 0


def test_max_hops_is_required_for_v10_and_forbidden_before(tmp_path):
    raw = yaml.safe_load(DEFAULT_CONFIG_V10.read_text("utf-8"))
    v9 = yaml.safe_load(DEFAULT_CONFIG_V9.read_text("utf-8"))
    cases = {
        "missing": lambda r: r["door_shaping"].pop("max_hops"),
        "zero": lambda r: r["door_shaping"].update(max_hops=0),
        "text": lambda r: r["door_shaping"].update(max_hops="5"),
        "float": lambda r: r["door_shaping"].update(max_hops=2.5),
        "bool": lambda r: r["door_shaping"].update(max_hops=True),
        "extra": lambda r: r["door_shaping"].update(more=1),
    }
    for name, mutate in cases.items():
        bad = yaml.safe_load(yaml.safe_dump(raw))
        mutate(bad)
        path = tmp_path / f"{name}.yaml"
        path.write_text(yaml.safe_dump(bad), "utf-8")
        with pytest.raises(ValueError):
            RewardV4Coefficients.load(path)
    path = tmp_path / "v9_with_hops.yaml"
    v9["door_shaping"]["max_hops"] = 5
    path.write_text(yaml.safe_dump(v9), "utf-8")
    with pytest.raises(ValueError):
        RewardV4Coefficients.load(path)


def test_the_largest_potential_is_the_coefficient_times_one_plus_the_cap():
    value = make()
    start(value, A, [])
    assert value._phi == -K * (1 + CAP) == -12.0  # no door to a goal: the constant


# --- graph potential -------------------------------------------------------------------


def test_dead_end_room_costs_the_door_share_plus_one_hop_back_to_the_frontier():
    value = make()
    start(value, A, [dr(0, B), dr(1, C)])  # A has doors to B and to C
    here = at(100, 280, room_type=1)
    # B is a dead end: its only door leads back to A, whose other door leads to unvisited C.
    back = [dr(0, A, 20.0, 280.0)]
    assert cost(value, B, back, here) == pytest.approx(80 / DIAGONAL + 1)


def test_walking_toward_the_exit_door_of_a_dead_end_pays():
    value = make()
    start(value, A, [dr(0, B), dr(1, C)])
    back = [dr(0, A, 20.0, 280.0)]
    visit(value, B, back, at(300, 280))
    paid = [visit(value, B, back, at(x, 280)) for x in (240, 180, 120, 60)]
    assert all(p > 0 for p in paid)
    away = [visit(value, B, back, at(x, 280)) for x in (120, 240, 360)]
    assert all(p < 0 for p in away)


def test_a_two_hop_chain_adds_one_per_room_to_cross():
    value = make()
    start(value, A, [dr(0, B)])
    visit(value, B, [dr(0, A), dr(1, C)])
    visit(value, C, [dr(0, B), dr(1, D)])  # D is unvisited: C is one door from a goal
    fighting = at(clear=False)  # a constant in-room term of 1
    assert cost(value, C, [dr(0, B), dr(1, D)], fighting) == 1 + 0
    assert cost(value, B, [dr(0, A), dr(1, C)], fighting) == 1 + 1
    assert cost(value, A, [dr(0, B)], fighting) == 1 + 2


def test_the_best_door_wins_between_a_frontier_door_and_a_longer_way():
    value = make()
    start(value, A, [dr(0, B), dr(1, C)])
    visit(value, B, [dr(0, A), dr(1, D)])
    doors = [dr(0, B), dr(1, C)]  # C is unvisited itself: zero hops
    assert cost(value, A, doors, at(clear=False)) == 1 + 0


def test_locked_and_secret_closed_doors_are_ignored():
    value = make()
    sealed = [dr(0, B, usable=False), dr(1, C, usable=False)]
    start(value, A, sealed)
    assert cost(value, A, sealed) == 1 + CAP  # no usable door: the constant, no gradient
    mixed = [dr(0, B, usable=False), dr(1, C, x=300.0)]
    # Only the usable door counts, whatever the nearer unusable one is.
    near = at(580, 280)
    assert cost(value, A, mixed, near) == pytest.approx(280 / DIAGONAL + 0)
    graph = RoomGraph()
    graph.observe((1, 0), A, sealed, boss_room=False)
    assert graph.hops() == {}  # an unusable door is no edge to a goal


def test_a_target_unreadable_on_the_grid_is_ignored():
    value = make()
    unknown = [dr(0, -1)]
    start(value, A, unknown)
    assert cost(value, A, unknown) == 1 + CAP


def test_hops_are_capped_at_max_hops():
    chain = list(range(80, 92))
    value = make()
    start(value, chain[0], [dr(0, chain[1])])
    for here, nxt in zip(chain[1:], chain[2:], strict=False):
        visit(value, here, [dr(0, here - 1), dr(1, nxt)])
    fighting = at(clear=False)
    assert cost(value, chain[0], [dr(0, chain[1])], fighting) == 1 + CAP  # 10 rooms, capped
    short = make(replace(COEF, door_shaping_max_hops=2))
    start(short, chain[0], [dr(0, chain[1])])
    for here, nxt in zip(chain[1:], chain[2:], strict=False):
        visit(short, here, [dr(0, here - 1), dr(1, nxt)])
    assert cost(short, chain[0], [dr(0, chain[1])], fighting) == 1 + 2


def test_no_frontier_and_no_boss_is_a_constant_without_a_gradient():
    value = make()
    start(value, A, [dr(0, B)])
    visit(value, B, [dr(0, A)])  # both rooms seen, nothing left to find
    door = [dr(0, B)]
    values = {cost(value, A, door, at(x, 280)) for x in (40, 200, 580)}
    assert values == {1 + CAP}
    stay = visit(value, A, door, at(100, 280))
    assert stay == pytest.approx((GAMMA - 1) * -K * (1 + CAP))  # only the discount term


def test_the_boss_room_is_a_goal_once_it_has_been_seen():
    value = make()
    start(value, A, [dr(0, B)])
    boss = at(room_type=BOSS_ROOM_TYPE, clear=False)
    visit(value, B, [dr(0, A)], boss)  # B is the boss room; remembered
    fighting = at(clear=False)
    assert cost(value, B, [dr(0, A)], boss) == 1.0
    assert cost(value, A, [dr(0, B)], fighting) == 1 + 0  # the boss room is one door away


def test_a_cleared_boss_room_pays_the_trapdoor_distance_share():
    value = make()
    start(value, A, [dr(0, B)])
    clear_boss = at(room_type=BOSS_ROOM_TYPE, entities=[trapdoor(300, 400)])
    assert cost(value, B, [dr(0, A)], clear_boss) == pytest.approx(500 / DIAGONAL)
    far = at(room_type=BOSS_ROOM_TYPE, entities=[trapdoor(9000, 0)])
    assert cost(value, B, [dr(0, A)], far) == 1.0  # clipped like the door share
    assert cost(value, B, [dr(0, A)], at(room_type=BOSS_ROOM_TYPE)) == 0.0  # no trapdoor yet


def test_an_unclear_boss_room_or_one_with_enemies_costs_one():
    value = make()
    start(value, A, [dr(0, B)])
    alive = at(room_type=BOSS_ROOM_TYPE, clear=False, entities=[trapdoor(10, 0)])
    assert cost(value, B, [dr(0, A)], alive) == 1.0
    cleared = at(room_type=BOSS_ROOM_TYPE, entities=[trapdoor(10, 0)])
    assert cost(value, B, [dr(0, A)], cleared, enemies=True) == 1.0


def test_a_fighting_room_has_no_distance_pull():
    value = make()
    doors = [dr(0, B)]
    start(value, A, doors)
    values = {cost(value, A, doors, at(x, 280, clear=False)) for x in (40, 300, 580)}
    assert values == {1.0}
    assert {cost(value, A, doors, at(x, 280), enemies=True) for x in (40, 580)} == {1.0}
    shut = [dr(0, B, open=False)]
    assert {cost(value, A, shut, at(x, 280)) for x in (40, 580)} == {1.0}  # closed door
    assert cost(value, A, doors, at(580, 280)) == pytest.approx(0.0)  # clear room, at the door


def test_the_door_share_is_clipped_to_one():
    value = make()
    far = [dr(0, B, 9000.0, 9000.0)]
    start(value, A, far)
    assert cost(value, A, far) == 1.0


def test_floor_change_and_new_episode_clear_the_graph():
    value = make()
    start(value, A, [dr(0, B)])
    visit(value, B, [dr(0, A)])
    assert value._graph.visited == {A, B}
    visit(value, C, [dr(0, D)], at(stage=2))  # a new floor starts a new graph
    assert value._graph.visited == {C} and set(value._graph.edges) == {C}
    value.reset(2)
    value.begin(at(), 1, [dr(0, E)], False, A)  # a new episode starts one too
    assert value._graph.visited == {A} and value._graph.edges == {A: {E: True}}
    visit(value, B, [dr(0, A)])
    other_type = frame(room=room_facts(stage=1, stage_type=2))  # alternate floor path
    visit(value, C, [dr(0, D)], other_type)
    assert value._graph.visited == {C}


def test_an_off_grid_room_without_doors_data_or_a_dead_player_has_no_potential():
    value = make()
    start(value, A, [dr(0, B)])
    assert value._potential(at(), [dr(0, B)], False, -1) == 0.0
    assert value._potential(at(), [dr(0, B)], False, None) == 0.0
    assert value._potential(at(), None, False, A) == 0.0
    assert value._potential(at(), [dr(0, B)], False, A) < 0.0
    value.consume([event("player_died")], 0, at(), 1, [dr(0, B)], room_grid=A)
    assert value._potential(at(), [dr(0, B)], False, A) == 0.0


def test_a_visited_target_is_no_goal_and_an_unvisited_one_is():
    graph = RoomGraph()
    graph.observe((1, 0), A, [dr(0, B), dr(1, C)], boss_room=False)
    assert graph.hops() == {B: 0, C: 0, A: 1}
    graph.observe((1, 0), B, [dr(0, A)], boss_room=False)
    assert graph.hops() == {C: 0, A: 1, B: 2}


def test_v9_config_keeps_the_v9_potential_ignoring_the_graph():
    old = RewardLedgerV4(
        RewardV4Coefficients.load(DEFAULT_CONFIG_V9), stall_seconds=STALL_SECONDS, gamma=GAMMA
    )
    old.reset(1)
    old.begin(at(100, 280), 1, [dr(0, B, 580.0, 280.0)], False, A)
    unexplored = OracleDoor(slot=1, x=60, y=280, open=True, unexplored=False, target=C, usable=True)
    assert old._phi == pytest.approx(-2.0 * 480 / DIAGONAL)
    assert old._potential(at(100, 280), [unexplored], False, A) == 0.0  # v9: explored door
    assert old._potential(at(100, 280), [dr(0, B)], True, A) == 0.0  # v9: enemies present


# --- telescoping and exploits ----------------------------------------------------------

TOPOLOGY = {
    80: [(81, True), (82, True)],
    81: [(80, True), (83, True)],
    82: [(80, True), (84, False)],  # the way to 84 is locked
    83: [(81, True), (84, True)],
    84: [(83, True)],
}


def trajectory(rng, steps):
    """A random walk over TOPOLOGY with random clear and enemy flags."""
    room = 80
    for _ in range(steps):
        if rng.random() < 0.3:
            room = rng.choice([target for target, usable in TOPOLOGY[room] if usable] or [room])
        doors = [
            dr(slot, target, 60.0 + 100.0 * slot, 280.0, open=rng.random() < 0.8, usable=usable)
            for slot, (target, usable) in enumerate(TOPOLOGY[room])
        ]
        position = at(rng.uniform(60, 580), rng.uniform(140, 420), clear=rng.random() < 0.7)
        yield room, doors, position, rng.random() < 0.3


@pytest.mark.parametrize("seed", range(8))
def test_discounted_shaping_telescopes_to_minus_the_first_potential(seed):
    rng = random.Random(seed)
    value = make()
    first, doors, position, _ = next(trajectory(random.Random(seed), 1))
    start(value, first, doors, frame=position)
    phi0 = value._phi
    steps = list(trajectory(rng, 60))
    total = 0.0
    for t, (room, doors, position, enemies) in enumerate(steps):
        last = t == len(steps) - 1
        total += GAMMA**t * visit(value, room, doors, position, enemies=enemies, terminal=last)
    assert total == pytest.approx(-phi0, abs=1e-9)  # Phi_T = 0: nothing is left over


def test_reentering_rooms_forever_never_farms_the_shaping():
    value = make()
    start(value, 80, [dr(0, 81), dr(1, 82)])
    steps = 600
    total = 0.0
    for t in range(steps):
        room = 80 + (t % 2)  # step through the same two rooms again and again
        doors = [dr(0, 81 - (t % 2) * 1), dr(1, 82)] if room == 80 else [dr(0, 80), dr(1, 83)]
        total += visit(value, room, doors, at(60 + (t * 37) % 500, 280))
    bound = K * (1 + CAP) * (1 + (1 - GAMMA) * steps)
    assert abs(total) <= bound  # the same bound as for any closed walk: discount dust only


def test_a_terminal_step_ends_in_zero_potential():
    value = make()
    start(value, A, [dr(0, B)])
    phi = value._phi
    paid = visit(value, A, [dr(0, B)], terminal=True)
    assert paid == pytest.approx(-phi) and value._phi == 0.0


# --- environment and metrics -----------------------------------------------------------


class Rooms:
    """Backend with prepared frames; every step is in grid room B with one door to unvisited C."""

    supports_seed = False

    def __init__(self, clear=False):
        self.clear = clear
        self.count = 0

    def start_episode(self, scenario, seed):
        return self._result()

    def step(self, action, repeat):
        return self._result()

    def _result(self):
        self.count += 1
        return StepResult(
            at(300, 280, clear=self.clear, frame_id=self.count),
            (),
            room_index=1,
            doors=(dr(0, C),),
            enemies_present=not self.clear,
            room_grid=B,
        )

    def release(self):
        pass

    def close(self):
        pass


def test_the_env_passes_the_grid_room_and_a_stall_row_carries_the_goal_term(tmp_path):
    ledger = make()
    env = IsaacCombatEnv(Rooms(), [LIVE_SCENARIO], accountant=ledger)
    env.reset()
    env.request_truncation("stall")
    *_, info = env.step(np.array([0, 0, 0]))
    summary = info["episode_summary"]
    assert summary["truncation_reason"] == "stall" and summary["stall_goal_hops"] == 1.0
    path = tmp_path / "episodes.csv"
    EpisodeMetricsWriter(path).write(summary)
    row = next(csv.DictReader(path.open(encoding="utf-8")))
    assert row["stall_goal_hops"] == "1.0"
    clear = IsaacCombatEnv(Rooms(clear=True), [LIVE_SCENARIO], accountant=make())
    clear.reset()
    clear.request_truncation("stall")
    *_, info = clear.step(np.array([0, 0, 0]))
    assert info["episode_summary"]["stall_goal_hops"] == pytest.approx(round(280 / DIAGONAL, 2))


def test_a_death_row_has_no_goal_term(tmp_path):
    class Dying(Rooms):
        def _result(self):
            result = super()._result()
            died = (event("player_died", result.frame.frame_id),) if self.count > 1 else ()
            return StepResult(
                result.frame,
                died,
                room_index=1,
                doors=result.doors,
                enemies_present=True,
                room_grid=B,
            )

    env = IsaacCombatEnv(Dying(), [LIVE_SCENARIO], accountant=make())
    env.reset()
    *_, info = env.step(np.array([0, 0, 0]))
    summary = info["episode_summary"]
    assert summary["end_reason"] == "death"
    path = tmp_path / "episodes.csv"
    EpisodeMetricsWriter(path).write(summary)
    row = next(csv.DictReader(path.open(encoding="utf-8")))
    assert row["stall_goal_hops"] == ""
