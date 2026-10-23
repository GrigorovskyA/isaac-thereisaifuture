"""Kill credit (reward v6): a kill pays the remaining HP credit once, at most max HP."""

import pytest
from test_live import live

from isaac_threrisaifuture.live import EventDeriver, make_live_env
from isaac_threrisaifuture.stall_watchdog import RunProgress


def with_killed(snap, *ids):
    oracle = snap.oracle.model_copy(update={"killed": list(ids)})
    return snap.model_copy(update={"oracle": oracle})


def paid(events):
    return [(e.entity_id, e.amount) for e in events if e.kind == "enemy_damaged"]


def deriver(*enemies):
    d = EventDeriver()
    d.begin(live(1, enemies=list(enemies)))
    return d


def test_one_shot_kill_pays_max_hp_once():
    d = deriver((1, 10.0), (2, 10.0))
    events = d.update(with_killed(live(2, enemies=[(2, 10.0)]), 1))
    assert paid(events) == [(1, 10.0)]
    assert paid(d.update(with_killed(live(3, enemies=[(2, 10.0)]), 1))) == []


def test_partly_damaged_enemy_pays_the_remainder():
    d = deriver((1, 10.0))
    first = d.update(live(2, enemies=[(1, 4.0)]))
    last = d.update(with_killed(live(3), 1))
    assert sum(amount for _, amount in paid(first) + paid(last)) == 10.0
    assert paid(last) == [(1, 4.0)]


def test_never_listed_id_pays_nothing():
    d = deriver((1, 10.0))
    assert paid(d.update(with_killed(live(2, enemies=[(1, 10.0)]), 99))) == []


def test_still_listed_id_pays_nothing():
    d = deriver((1, 10.0))
    assert paid(d.update(with_killed(live(2, enemies=[(1, 10.0)]), 1))) == []


def test_a_new_game_epoch_clears_the_credit():
    d = deriver((1, 10.0))
    fresh = live(2)
    fresh = fresh.model_copy(
        update={"entity_frame": fresh.entity_frame.model_copy(update={"game_epoch": 2})}
    )
    assert paid(d.update(with_killed(fresh, 1))) == []


def test_the_kill_event_is_stall_progress():
    d = deriver((1, 10.0))
    events = d.update(with_killed(live(2), 1))
    progress = RunProgress()
    assert progress.novel(events, stage=1) is True


def test_live_env_pays_reward_v6_and_refuses_other_versions():
    client = object()
    for version in (4, 5, 7):
        with pytest.raises(ValueError, match="Unsupported reward version"):
            make_live_env(client, reward_version=version)  # type: ignore[arg-type]
    assert make_live_env(client, reward_version=6)  # type: ignore[arg-type]
