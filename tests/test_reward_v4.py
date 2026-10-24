"""Reward v4 terms, exploit bounds, new oracle events and episode semantics. All offline."""

import copy
import csv
import json
from pathlib import Path

import numpy as np
import pytest
import yaml
from synthetic import event, frame, inventory, oracle_metrics, room_facts
from test_entity_transport import entity_snapshot

from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.entities import OracleEvent
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import FIELDS, EpisodeMetricsWriter
from isaac_threrisaifuture.episodes import Scenario, StepResult
from isaac_threrisaifuture.live import LIVE_SCENARIO, EventDeriver, LiveSnapshot
from isaac_threrisaifuture.recording import JsonlRecorder, open_replay
from isaac_threrisaifuture.rewards import (
    DEFAULT_CONFIG_V7,
    REWARD_V4_COLUMNS,
    RewardLedgerV4,
    RewardV4Coefficients,
)

SESSION = "a" * 32
COEF = RewardV4Coefficients.load()


def live(seq, *, epoch=1, room=84, stage=1, coins=0, bombs=0, keys=0, items=(), red=6, dead=False):
    raw = entity_snapshot(SESSION, seq, frame_id=seq, game_epoch=epoch)
    raw["frame_id"] = seq
    raw["game_epoch"] = epoch
    raw["entity_frame"]["inventory"] = inventory(coins=coins, bombs=bombs, keys=keys).model_dump()
    raw["entity_frame"]["collectibles"] = sorted(items)
    raw["entity_frame"]["room"] = room_facts(stage=stage).model_dump()
    raw["entity_frame"]["entities"] = []
    for block in (raw["entity_frame"]["health"], raw["player"]["health"]):
        block["red_half_hearts"] = red
    raw["oracle"] = {
        "room_clear": False,
        "player_dead": dead,
        "enemies": [],
        "enemy_overflow": 0,
        "room_index": room,
        **oracle_metrics(),
    }
    return LiveSnapshot.model_validate_json(json.dumps(raw))


def derived(deriver, snap):
    return [(e.kind, e.room_index, e.stage, e.resource, e.item_id, e.amount) for e in
            deriver.update(snap)]  # fmt: skip


# --- configuration ------------------------------------------------------------------


def test_coefficients_load_the_shipped_file():
    assert COEF.room_clear_first == 10.0 and COEF.consumable_run_cap == 3.0
    assert COEF.novelty_cell_size == 40 and COEF.novelty_coefficient == 0.02
    assert COEF.enemy_hp_fraction_total == 5.0 and COEF.player_damage_half_heart == -0.5
    assert COEF.stall_restart == -5.0 and COEF.death == -10.0
    assert COEF.stagnation_per_second == -0.1 and COEF.stagnation_grace_seconds == 20.0


def test_coefficient_keys_are_strict(tmp_path: Path):
    raw = yaml.safe_load(DEFAULT_CONFIG_V7.read_text(encoding="utf-8"))
    for mutate in (
        lambda r: r["outcome"].pop("death"),
        lambda r: r["pickups"].update(extra=1.0),
        lambda r: r.update(unknown={}),
        lambda r: r.update(reward_version=1),
        lambda r: r["outcome"].update(death="high"),
        lambda r: r["novelty"].update(cell_size=0),
    ):
        bad = copy.deepcopy(raw)
        mutate(bad)
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.safe_dump(bad), encoding="utf-8")
        with pytest.raises(ValueError):
            RewardV4Coefficients.load(path)


# --- ledger terms -------------------------------------------------------------------


def ledger(start_frame=None, room=1) -> RewardLedgerV4:
    ledger = RewardLedgerV4(COEF)
    ledger.reset(1)
    ledger.begin(start_frame or frame(), room)
    return ledger


def consume(ledger, *events, updates=0):
    return ledger.consume(list(events), updates)


def pickup(resource, amount, total):
    return event("pickup_gained", resource=resource, amount=float(amount), total=total)


def collectible(item_id):
    return event("pickup_gained", resource="collectible", item_id=item_id)


def test_each_term_has_its_own_column_and_columns_sum_to_the_reward():
    ledger_ = ledger()
    events = [
        event("enemy_spawned", entity_id=1, spawn_generation=0, amount=10.0),
        event("enemy_damaged", entity_id=1, spawn_generation=0, amount=5.0),
        event("room_cleared", room_index=1),
        event("room_entered", room_index=2),
        event("floor_entered", stage=2),
        event("player_damaged", amount=2.0, damage_source="enemy"),
        collectible(5),
        pickup("coin", 1, 1),
        event("player_healed", amount=1.0),
    ]
    total, parts = ledger_.consume(events, 30)  # one second
    assert set(parts) == set(REWARD_V4_COLUMNS)
    assert parts["enemy_damage"] == pytest.approx(COEF.enemy_hp_fraction_total / 2)
    assert parts["room_clear"] == COEF.room_clear_first
    assert parts["room_visit"] == COEF.room_first_visit
    assert parts["floor_entered"] == COEF.floor_first_entered
    assert parts["damage_taken"] == 2 * COEF.player_damage_half_heart
    assert parts["time"] == pytest.approx(COEF.time_second)
    assert parts["collectible_new"] == COEF.collectible_new
    assert parts["pickup_coin"] == COEF.coin
    assert parts["heal"] == COEF.heal_half_heart
    assert parts["death"] == 0.0 and parts["novelty"] == 0.0
    assert total == pytest.approx(sum(parts.values()))
    _, parts = ledger_.consume([event("player_died")], 0)
    assert parts["death"] == COEF.death


def test_enemy_damage_is_monotonic_per_enemy():
    ledger_ = ledger()
    spawn = event("enemy_spawned", entity_id=1, spawn_generation=0, amount=10.0)
    hit = event("enemy_damaged", entity_id=1, spawn_generation=0, amount=6.0)
    consume(ledger_, spawn)
    paid = sum(consume(ledger_, hit)[1]["enemy_damage"] for _ in range(3))
    assert paid == pytest.approx(COEF.enemy_hp_fraction_total)


def test_no_time_cost_after_death():
    ledger_ = ledger()
    consume(ledger_, event("player_died"))
    assert consume(ledger_, updates=300)[1]["time"] == 0.0


# --- exploit bounds -----------------------------------------------------------------


def test_repeated_room_entry_and_reclear_pay_once():
    ledger_ = ledger(room=1)
    assert consume(ledger_, event("room_entered", room_index=1))[1]["room_visit"] == 0.0  # start
    first = consume(ledger_, event("room_entered", room_index=2))[1]["room_visit"]
    clear = consume(ledger_, event("room_cleared", room_index=2))[1]["room_clear"]
    assert (first, clear) == (COEF.room_first_visit, COEF.room_clear_first)
    for _ in range(3):
        total, _ = consume(
            ledger_,
            event("room_entered", room_index=1),
            event("room_entered", room_index=2),
            event("room_cleared", room_index=2),
        )
        assert total == 0.0


def test_room_clear_without_index_uses_the_current_room():
    ledger_ = ledger(room=1)
    consume(ledger_, event("room_entered", room_index=2))
    assert consume(ledger_, event("room_cleared"))[1]["room_clear"] == COEF.room_clear_first
    assert consume(ledger_, event("room_cleared"))[1]["room_clear"] == 0.0


def test_start_floor_is_free_and_each_new_floor_pays_once():
    ledger_ = ledger(frame(room=room_facts(stage=3)))
    assert consume(ledger_, event("floor_entered", stage=3))[1]["floor_entered"] == 0.0
    assert consume(ledger_, event("floor_entered", stage=4))[1]["floor_entered"] > 0
    assert consume(ledger_, event("floor_entered", stage=4))[1]["floor_entered"] == 0.0


def test_a_reused_room_index_on_a_new_floor_pays_again():
    ledger_ = ledger(room=84)
    assert consume(ledger_, event("room_cleared", room_index=84))[1]["room_clear"] > 0
    next_floor = frame(room=room_facts(stage=2))
    _, parts = ledger_.consume(
        [event("floor_entered", stage=2), event("room_entered", room_index=84)],
        0,
        next_floor,
        84,
    )
    assert parts["room_visit"] == COEF.room_first_visit
    _, parts = ledger_.consume([event("room_cleared", room_index=84)], 0, next_floor, 84)
    assert parts["room_clear"] == COEF.room_clear_first
    assert ledger_.run_stats()["rooms_visited"] == 2


def test_damage_then_heal_is_capped_by_earlier_loss():
    ledger_ = ledger()
    consume(ledger_, event("player_damaged", amount=2.0, damage_source="enemy"))
    paid = consume(ledger_, event("player_healed", amount=4.0))[1]["heal"]
    assert paid == 2 * COEF.heal_half_heart
    assert consume(ledger_, event("player_healed", amount=2.0))[1]["heal"] == 0.0
    consume(ledger_, event("player_damaged", amount=1.0, damage_source="enemy"))
    assert consume(ledger_, event("player_healed", amount=1.0))[1]["heal"] > 0


def test_new_collectible_pays_two_in_reward_v4():
    ledger_ = ledger(frame(collectibles=[7]))
    assert COEF.collectible_new == 2.0
    assert consume(ledger_, collectible(9))[1]["collectible_new"] == 2.0


def test_drop_and_repickup_of_a_collectible_pays_once():
    ledger_ = ledger(frame(collectibles=[7]))
    assert consume(ledger_, collectible(7))[1]["collectible_new"] == 0.0  # held at the start
    assert consume(ledger_, collectible(9))[1]["collectible_new"] == COEF.collectible_new
    assert consume(ledger_, collectible(9))[1]["collectible_new"] == 0.0


def test_drop_and_repickup_of_a_consumable_pays_once():
    ledger_ = ledger()
    assert consume(ledger_, pickup("bomb", 2, 2))[1]["pickup_bomb"] == 2 * COEF.bomb
    # Spent down to 0, then 2 bombs again: nothing above the run's peak.
    assert consume(ledger_, pickup("bomb", 2, 2))[1]["pickup_bomb"] == 0.0
    # A gain that passes the peak pays only the units above it.
    assert consume(ledger_, pickup("bomb", 2, 3))[1]["pickup_bomb"] == COEF.bomb


def test_starting_consumables_are_not_rewarded():
    ledger_ = ledger(frame(inventory=inventory(coins=5)))
    assert consume(ledger_, pickup("coin", 1, 5))[1]["pickup_coin"] == 0.0
    assert consume(ledger_, pickup("coin", 1, 6))[1]["pickup_coin"] == COEF.coin


def test_consumable_cap_is_shared_and_bounds_farming():
    ledger_ = ledger()
    paid = 0.0
    for total in range(1, 200):
        parts = consume(ledger_, pickup("coin", 1, total))[1]
        paid += parts["pickup_coin"]
    assert paid == pytest.approx(COEF.consumable_run_cap)
    # The cap is shared: bombs and keys find it already used up.
    assert consume(ledger_, pickup("bomb", 1, 1))[1]["pickup_bomb"] == 0.0
    assert consume(ledger_, pickup("key", 1, 1))[1]["pickup_key"] == 0.0


def test_new_run_resets_sets_caps_and_heal_pool():
    first = frame(frame_id=1)
    ledger_ = ledger(first, room=1)
    consume(ledger_, event("room_entered", room_index=2), collectible(9))
    consume(ledger_, event("room_cleared", room_index=2), event("floor_entered", stage=2))
    consume(ledger_, event("player_damaged", amount=2.0, damage_source="enemy"))
    for total in range(1, 100):
        consume(ledger_, pickup("coin", 1, total))
    # Same epoch (for example a fault retry): nothing resets.
    ledger_.reset(2)
    ledger_.begin(frame(frame_id=50), 2)
    assert consume(ledger_, event("room_cleared", room_index=2))[0] == 0.0
    assert consume(ledger_, event("player_healed", amount=2.0))[1]["heal"] > 0
    assert consume(ledger_, collectible(9))[0] == 0.0
    # A new epoch is a new run: everything pays again.
    ledger_.reset(3)
    ledger_.begin(frame(game_epoch=2), 1)
    assert consume(ledger_, event("room_entered", room_index=2))[1]["room_visit"] > 0
    assert consume(ledger_, event("room_cleared", room_index=2))[1]["room_clear"] > 0
    assert consume(ledger_, event("floor_entered", stage=2))[1]["floor_entered"] > 0
    assert consume(ledger_, collectible(9))[1]["collectible_new"] > 0
    assert consume(ledger_, pickup("coin", 1, 1))[1]["pickup_coin"] > 0
    assert consume(ledger_, event("player_healed", amount=2.0))[1]["heal"] == 0.0  # no loss yet


def test_standing_still_pays_novelty_once():
    ledger_ = ledger()
    here = frame()
    values = [ledger_.consume([], 0, here, 1)[1]["novelty"] for _ in range(400)]
    assert values[0] == COEF.novelty_coefficient
    assert sum(values) == COEF.novelty_coefficient  # nothing after the first visit


def test_novelty_keys_are_room_and_cell_and_a_new_cell_is_fresh():
    ledger_ = ledger()
    at = lambda x, room: ledger_.consume([], 0, frame(player_position={"x": x, "y": 0}), room)[1]  # noqa: E731
    base = COEF.novelty_coefficient
    cell = COEF.novelty_cell_size
    assert at(1.0, 1)["novelty"] == base
    assert at(cell - 1, 1)["novelty"] == 0.0  # same cell, already visited
    assert at(cell + 1, 1)["novelty"] == base  # next cell
    assert at(1.0, 2)["novelty"] == base  # same cell, other room
    assert at(1.0, 1)["novelty"] == 0.0  # back in room 1: still paid once per run


def test_novelty_is_paid_again_only_in_a_new_run():
    ledger_ = ledger()
    here = frame()
    assert ledger_.consume([], 0, here, 1)[1]["novelty"] == COEF.novelty_coefficient
    ledger_.reset(2)
    ledger_.begin(here, 1)  # same session and epoch: still the same run
    assert ledger_.consume([], 0, here, 1)[1]["novelty"] == 0.0
    ledger_.reset(3)
    ledger_.begin(frame(game_epoch=2), 1)
    assert ledger_.consume([], 0, here, 1)[1]["novelty"] == COEF.novelty_coefficient


def test_stall_penalty_is_the_configured_term_and_death_never_pays_it():
    ledger_ = ledger()
    assert ledger_.stall_restart() == COEF.stall_restart
    consume(ledger_, event("player_died"))
    assert ledger_.stall_restart() == 0.0


def test_no_item_use_term_exists():
    assert not any("use" in name or "item" in name for name in REWARD_V4_COLUMNS)


# --- event derivation ---------------------------------------------------------------


def test_room_floor_and_pickup_events_from_successive_frames():
    d = EventDeriver()
    assert derived(d, live(1, items=[3])) == []  # baseline: no events, even with items held
    assert derived(d, live(2, room=90, coins=2, items=[3, 8])) == [
        ("room_entered", 90, None, None, None, None),
        ("pickup_gained", None, None, "coin", None, 2.0),
        ("pickup_gained", None, None, "collectible", 8, None),
    ]
    assert derived(d, live(3, room=90, coins=2, items=[3, 8])) == []
    assert derived(d, live(4, room=12, stage=2, bombs=1, keys=3, items=[3, 8])) == [
        ("floor_entered", None, 2, None, None, None),
        ("room_entered", 12, None, None, None, None),
        ("pickup_gained", None, None, "bomb", None, 1.0),
        ("pickup_gained", None, None, "key", None, 3.0),
    ]


def test_pickup_event_carries_the_new_counter():
    d = EventDeriver()
    d.begin(live(1, coins=4))
    (gain,) = d.update(live(2, coins=7))
    assert (gain.amount, gain.total) == (3.0, 7)


def test_counter_decreases_and_item_removal_emit_nothing_then_regain_does():
    d = EventDeriver()
    d.begin(live(1, coins=5, bombs=2, keys=1, items=[3, 8]))
    assert derived(d, live(2, coins=1, bombs=0, keys=0, items=[3])) == []
    regained = derived(d, live(3, coins=2, items=[3, 8]))
    assert [r[3] for r in regained] == ["coin", "collectible"]


def test_epoch_change_resets_the_baseline_silently():
    d = EventDeriver()
    d.begin(live(1, room=5, stage=3, coins=9, items=[3, 8]))
    assert derived(d, live(1, epoch=2, room=1, stage=1, coins=0, items=[])) == []
    assert derived(d, live(2, epoch=2, room=1, stage=1, coins=1, items=[])) == [
        ("pickup_gained", None, None, "coin", None, 1.0)
    ]


def test_begin_within_an_epoch_keeps_the_level_baseline():
    d = EventDeriver()
    d.begin(live(1, room=5))
    assert [e.kind for e in d.begin(live(2, room=6))] == ["room_entered"]


def test_room_cleared_event_carries_the_room_index():
    d = EventDeriver()
    d.begin(live(1))
    raw = json.loads(live(2).model_dump_json())
    raw["oracle"]["room_clear"] = True
    (clear,) = d.update(LiveSnapshot.model_validate_json(json.dumps(raw)))
    assert (clear.kind, clear.room_index) == ("room_cleared", 84)


def test_event_wire_model_stays_strict():
    ok = dict(provenance="game_api", session_id=SESSION, game_epoch=1, room_visit=1, frame_id=1)
    bad = [
        dict(kind="room_entered"),
        dict(kind="floor_entered"),
        dict(kind="floor_entered", stage=2, room_index=3),
        dict(kind="pickup_gained"),
        dict(kind="pickup_gained", resource="coin", amount=1.0),
        dict(kind="pickup_gained", resource="coin", amount=3.0, total=2),
        dict(kind="pickup_gained", resource="collectible"),
        dict(kind="pickup_gained", resource="collectible", item_id=4, amount=1.0),
        dict(kind="player_died", resource="coin"),
        dict(kind="player_died", room_index=1),
        dict(kind="room_entered", room_index=1, extra=1),
    ]
    for fields in bad:
        with pytest.raises(ValueError):
            OracleEvent(**ok, **fields)  # type: ignore[arg-type]
    assert OracleEvent(**ok, kind="room_entered", room_index=-2).room_index == -2


def test_oracle_room_index_never_enters_the_policy_vector():
    assert "room_index" not in type(frame()).model_fields
    a, b = live(1, room=3), live(1, room=200)
    assert a.entity_frame is not None and b.entity_frame is not None
    assert a.entity_frame == b.entity_frame
    assert np.array_equal(encode(a.entity_frame).vector, encode(b.entity_frame).vector)


# --- episodes -----------------------------------------------------------------------


class Script:
    """Replays prepared results; every step is one game update."""

    supports_seed = False

    def __init__(self, steps):
        self.steps = list(steps)
        self.first = True

    def start_episode(self, scenario, seed):
        return StepResult(frame(frame_id=1, player_position={"x": 5.0, "y": 5.0}), (), room_index=1)

    def step(self, action, repeat):
        frame_id, events, room = self.steps.pop(0)
        return StepResult(
            frame(frame_id=frame_id),
            tuple(event(kind, frame_id, **fields) for kind, fields in events),
            room_index=room,
        )

    def release(self):
        pass

    def close(self):
        pass


def run_env(steps, scenario=LIVE_SCENARIO, truncate_at=None):
    env = IsaacCombatEnv(Script(steps), [scenario], accountant=RewardLedgerV4(COEF))
    env.reset()
    results = []
    for index in range(len(steps)):
        if truncate_at == index:
            env.request_truncation("stall")
        results.append(env.step(np.array([0, 0, 0])))
        if results[-1][2] or results[-1][3]:
            break
    return env, results


def test_live_scenario_has_no_time_cap_and_does_not_end_on_clear():
    assert LIVE_SCENARIO.max_game_updates is None and not LIVE_SCENARIO.end_on_clear
    assert LIVE_SCENARIO.allow_room_change


def test_episode_continues_across_room_clear_and_room_change():
    steps = [
        (2, [("room_cleared", dict(room_index=1))], 1),
        (3, [("room_entered", dict(room_index=2))], 2),
        (4, [("floor_entered", dict(stage=2))], 2),
    ]
    steps += [(5 + i, [], 2) for i in range(5000)]
    env, results = run_env(steps)
    assert all(not term and not trunc for _, _, term, trunc, _ in results)
    assert len(results) == len(steps)  # 5000+ steps, far beyond the old 60 s cap
    assert results[0][4]["reward_components"]["room_clear"] == COEF.room_clear_first
    assert "episode_summary" not in results[0][4]


def test_death_terminates_with_a_summary():
    steps = [
        (2, [("room_entered", dict(room_index=2))], 2),
        (3, [("pickup_gained", dict(resource="coin", amount=1.0, total=1))], 2),
        (4, [("player_died", {})], 2),
    ]
    env, results = run_env(steps)
    _, reward, terminated, truncated, info = results[-1]
    assert terminated and not truncated and info["outcome"] == "death"
    assert reward == pytest.approx(
        COEF.death + COEF.time_second * 1 / 30 + info["reward_components"]["novelty"]
    )
    s = info["episode_summary"]
    assert s["outcome"] == "terminated" and s["end_reason"] == "death"
    assert s["truncation_reason"] is None and s["timesteps"] == 3
    assert s["rooms_visited"] == 2 and s["rooms_cleared"] == 0 and s["max_stage"] == 1
    assert s["pickups"] == {"coin": 1.0, "bomb": 0.0, "key": 0.0, "collectible": 0.0}
    assert s["damage_dealt_fraction"] == 0.0
    assert s["return"] == pytest.approx(sum(s["columns"].values()))
    assert s["columns"]["room_visit"] == COEF.room_first_visit
    assert s["columns"]["death"] == COEF.death
    assert env.controller.running is False


def test_truncation_has_a_reason_in_step_info_and_summary():
    steps = [(2, [], 1), (3, [], 1), (4, [], 1)]
    env, results = run_env(steps, truncate_at=1)
    _, _, terminated, truncated, info = results[-1]
    assert len(results) == 2 and truncated and not terminated
    assert info["outcome"] == "truncated" and info["truncation_reason"] == "stall"
    s = info["episode_summary"]
    assert s["outcome"] == "truncated" and s["truncation_reason"] == "stall"
    assert results[0][4]["truncation_reason"] is None


def test_stall_truncation_pays_the_penalty_once_on_the_final_step():
    steps = [(2, [], 1), (3, [], 1), (4, [], 1)]
    _, results = run_env(steps, truncate_at=1)
    assert results[0][4]["reward_components"].get("stall", 0.0) == 0.0
    _, reward, _, truncated, info = results[-1]
    assert truncated and info["reward_components"]["stall"] == COEF.stall_restart
    summary = info["episode_summary"]
    assert summary["columns"]["stall"] == COEF.stall_restart  # exactly once
    assert summary["return"] == pytest.approx(sum(summary["columns"].values()))
    assert reward == pytest.approx(sum(info["reward_components"].values()))


def test_other_truncations_and_death_do_not_pay_the_stall_penalty():
    capped = Scenario("capped", "train", 1, 2, 0, 1.0, True, False)
    _, results = run_env([(2, [], 1), (3, [], 1), (4, [], 1)], scenario=capped)
    assert results[-1][3] and results[-1][4]["episode_summary"]["columns"]["stall"] == 0.0
    _, results = run_env([(2, [("player_died", {})], 1), (3, [], 1)], truncate_at=0)
    info = results[-1][4]
    assert info["episode_summary"]["columns"].get("stall", 0.0) == 0.0


def test_scenario_cap_still_truncates_when_set():
    capped = Scenario("capped", "train", 1, 2, 0, 1.0, True, False)
    _, results = run_env([(2, [], 1), (3, [], 1), (4, [], 1)], scenario=capped)
    assert results[-1][3] and results[-1][4]["truncation_reason"] == "unknown"


def test_summary_counts_damage_fraction_and_clears():
    steps = [
        (2, [("enemy_spawned", dict(entity_id=1, spawn_generation=0, amount=10.0))], 1),
        (3, [("enemy_damaged", dict(entity_id=1, spawn_generation=0, amount=4.0))], 1),
        (4, [("room_cleared", dict(room_index=1))], 1),
        (5, [("player_died", {})], 1),
    ]
    _, results = run_env(steps)
    s = results[-1][4]["episode_summary"]
    assert s["damage_dealt_fraction"] == pytest.approx(0.4)
    assert s["rooms_cleared"] == 1


def test_summary_adds_use_counts_hearts_lost_and_first_exit_and_damage():
    steps = [
        (2, [], 1),
        (3, [("enemy_spawned", dict(entity_id=1, spawn_generation=0, amount=10.0))], 1),
        (4, [("enemy_damaged", dict(entity_id=1, spawn_generation=0, amount=4.0))], 1),
        (5, [("player_damaged", dict(amount=2.0, damage_source="enemy"))], 2),
        (6, [("player_damaged", dict(amount=1.0, damage_source="enemy"))], 2),
        (7, [("player_died", {})], 2),
    ]
    uses = [0, 1, 1, 2, 3, 0]
    env = IsaacCombatEnv(Script(steps), [LIVE_SCENARIO], accountant=RewardLedgerV4(COEF))
    env.reset()
    info = {}
    for use in uses:
        info = env.step(np.array([0, 0, use]))[4]
    s = info["episode_summary"]
    assert (s["use_bomb"], s["use_active"], s["use_pillcard"]) == (2, 1, 1)
    assert s["half_hearts_lost"] == 3.0
    assert s["steps_to_first_damage"] == 3 and s["steps_to_first_exit"] == 4


def test_summary_leaves_exit_and_damage_empty_when_they_never_happen(tmp_path: Path):
    _, results = run_env([(2, [], 1), (3, [("player_died", {})], 1)])
    s = results[-1][4]["episode_summary"]
    assert s["steps_to_first_exit"] is None and s["steps_to_first_damage"] is None
    writer = EpisodeMetricsWriter(tmp_path / "e.csv")
    writer.write(s)
    row = next(csv.DictReader((tmp_path / "e.csv").open(encoding="utf-8")))
    assert row["steps_to_first_exit"] == "" and row["use_bomb"] == "0" and "col_stall" in row
    assert FIELDS[-1] == "wall_time"


# --- exploit bounds -------------------------------------------------------------------


def idle_until_stall_return():
    """Wander every cell (13 x 7) of a full room for 90 s of an empty fight, then stall out."""
    ledger_ = ledger()
    total = 0.0
    cell = COEF.novelty_cell_size
    steps = 90 * 30 // 3
    for step in range(steps):
        x, y = (step % 13) * cell + 1, (step // 13 % 7) * cell + 1
        total += ledger_.consume([], 3, frame(player_position={"x": x, "y": y}), 1)[0]
    return total + ledger_.stall_restart()


def test_idle_until_stall_returns_less_than_one_kill_one_heart_and_a_first_clear():
    ledger_ = ledger()
    total, _ = ledger_.consume(
        [
            event("enemy_spawned", entity_id=1, spawn_generation=0, amount=10.0),
            event("enemy_damaged", entity_id=1, spawn_generation=0, amount=10.0),
            event("player_damaged", amount=2.0, damage_source="enemy"),
            event("room_cleared", room_index=1),
        ],
        30 * 30,
        frame(),
        1,
    )
    idle = idle_until_stall_return()
    assert idle < 0 < total
    assert idle < total - COEF.room_clear_first  # even without the clear bonus


def test_novelty_of_an_idle_episode_is_bounded_by_the_cells_reached():
    ledger_ = ledger()
    cell = COEF.novelty_cell_size
    paid = sum(
        ledger_.consume([], 0, frame(player_position={"x": (i % 3) * cell + 1, "y": 1.0}), 1)[1][
            "novelty"
        ]
        for i in range(1000)
    )
    assert paid == pytest.approx(3 * COEF.novelty_coefficient)


# --- metrics file -------------------------------------------------------------------


def test_episode_metrics_writer_appends_rows_with_one_header(tmp_path: Path):
    steps = [(2, [("player_died", {})], 1)]
    _, results = run_env(steps)
    summary = results[-1][4]["episode_summary"]
    path = tmp_path / "metrics" / "episodes.csv"
    for _ in range(2):
        writer = EpisodeMetricsWriter(path)
        writer.write(summary)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len(rows) == 2 and tuple(rows[0]) == FIELDS
    assert float(rows[0]["return"]) == pytest.approx(summary["return"])
    assert rows[0]["outcome"] == "terminated" and rows[0]["truncation_reason"] == ""
    assert float(rows[0]["col_death"]) == COEF.death
    assert rows[0]["pickups_coin"] == "0.0"


def test_episode_metrics_writer_refuses_a_foreign_header(tmp_path: Path):
    path = tmp_path / "episodes.csv"
    path.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError):
        EpisodeMetricsWriter(path)


def test_new_event_kinds_record_and_replay(tmp_path: Path):
    events = [
        event("room_entered", room_index=3),
        event("floor_entered", frame_id=2, stage=2),
        event("pickup_gained", frame_id=3, resource="key", amount=1.0, total=1),
        event("pickup_gained", frame_id=4, resource="collectible", item_id=12),
    ]
    path = tmp_path / "oracle.jsonl"
    with JsonlRecorder(path, "oracle_events", "synthetic") as recorder:
        for item in events:
            recorder.record(item)
    _, replay = open_replay(path, "oracle_events")
    assert list(replay) == events
