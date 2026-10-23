"""Offline unit tests of live-loop event derivation, fault budget and approval writing."""

import json

import gymnasium as gym
import pytest
from synthetic import oracle_metrics
from test_entity_transport import entity_snapshot

from isaac_threrisaifuture.episodes import EpisodeFault
from isaac_threrisaifuture.live import (
    EventDeriver,
    FaultTolerantEnv,
    LiveSnapshot,
    TrainingApproval,
    write_training_approval,
)
from isaac_threrisaifuture.observation import ProtocolError
from isaac_threrisaifuture.observer_client import ObserverConfig

SESSION = "a" * 32


def live(
    sequence, *, enemies=(), clear=False, dead=False, overflow=0, visit=None, red=6
):  # fmt: skip
    raw = entity_snapshot(SESSION, sequence, frame_id=sequence)
    raw["frame_id"] = sequence
    raw["entity_frame"]["health"]["red_half_hearts"] = red
    raw["player"]["health"]["red_half_hearts"] = red
    if visit is not None:
        raw["room"]["visit_id"] = raw["entity_frame"]["room_visit"] = visit
    raw["oracle"] = {
        "room_clear": clear,
        "player_dead": dead,
        "enemies": [{"entity_id": i, "hp": hp, "max_hp": 10.0} for i, hp in enemies],
        "enemy_overflow": overflow,
        "room_index": 84,
        **oracle_metrics(),
    }
    return LiveSnapshot.model_validate_json(json.dumps(raw))


def kinds(events):
    return [(e.kind, e.entity_id, e.amount) for e in events]


def test_deriver_observed_damage_clear_and_player_hp_without_absence_kills():
    d = EventDeriver()
    assert kinds(d.begin(live(1, enemies=[(1, 10.0), (2, 10.0)]))) == [
        ("enemy_spawned", 1, 10.0),
        ("enemy_spawned", 2, 10.0),
    ]
    assert kinds(d.update(live(2, enemies=[(1, 7.0), (2, 10.0)], red=5))) == [
        ("enemy_damaged", 1, 3.0),
        ("player_damaged", None, 1.0),
    ]
    events = d.update(live(3, enemies=[(2, 10.0)], clear=False, red=6))
    assert kinds(events) == [
        ("player_healed", None, 1.0),
    ]
    assert kinds(d.update(live(4, clear=True))) == [
        ("room_cleared", None, None),
    ]
    assert d.update(live(5, clear=True)) == []


def test_deriver_new_visit_resets_without_kills_or_clear():
    d = EventDeriver()
    d.begin(live(1, enemies=[(1, 10.0)]))
    events = d.update(live(2, enemies=[(7, 10.0)], clear=True, visit=2))
    assert kinds(events) == [("enemy_spawned", 7, 10.0)]


def test_deriver_overflow_suppresses_kills_until_complete():
    d = EventDeriver()
    d.begin(live(1, enemies=[(1, 10.0)]))
    assert d.update(live(2, overflow=3)) == []
    assert d.update(live(3)) == []  # previous frame was incomplete
    assert d.update(live(4)) == []  # Absence across a coverage gap stays unknown.
    d.update(live(5, enemies=[(1, 10.0)]))
    assert d.update(live(6)) == []  # Complete absence still does not prove death.


def test_deriver_death_once():
    d = EventDeriver()
    d.begin(live(1))
    assert [e.kind for e in d.update(live(2, dead=True))] == ["player_died"]
    assert d.update(live(3, dead=True)) == []


def test_live_snapshot_requires_oracle_and_bounded_hp():
    raw = json.loads(live(1).model_dump_json())
    raw["oracle"]["enemies"] = [{"entity_id": 1, "hp": 11.0, "max_hp": 10.0}]
    with pytest.raises(ValueError):
        LiveSnapshot.model_validate_json(json.dumps(raw))
    raw["oracle"] = None
    with pytest.raises(ValueError):
        LiveSnapshot.model_validate_json(json.dumps(raw))


class Flaky(gym.Env):
    observation_space = gym.spaces.Discrete(2)
    action_space = gym.spaces.Discrete(2)

    def __init__(self, failures):
        self.failures = list(failures)

    def _maybe_fail(self):
        if self.failures:
            raise self.failures.pop(0)

    def reset(self, **kwargs):
        self._maybe_fail()
        return 0, {}

    def step(self, action):
        self._maybe_fail()
        return 1, 1.0, False, False, {}


def test_fault_budget_truncates_then_raises():
    records = []
    env = FaultTolerantEnv(
        Flaky([EpisodeFault("reset")]), max_faults=1, on_record=lambda k, v: records.append(k)
    )
    assert env.reset()[0] == 0
    env.env.failures = [EpisodeFault("step")]
    with pytest.raises(EpisodeFault):
        env.step(0)
    assert records == ["fault", "fault"]


def test_fault_step_is_truncation_not_death():
    env = FaultTolerantEnv(Flaky([]), max_faults=5)
    env.reset()
    env.env.failures = [EpisodeFault("lost")]
    obs, reward, terminated, truncated, info = env.step(0)
    assert (obs, reward, terminated, truncated) == (0, 0.0, False, True)
    assert info["fault"] == "lost"


def test_protocol_faults_are_never_retried():
    fault = EpisodeFault("bad")
    fault.__cause__ = ProtocolError("malformed")
    env = FaultTolerantEnv(Flaky([fault]), max_faults=10)
    with pytest.raises(EpisodeFault):
        env.reset()


def test_training_approval_written_atomically(tmp_path):
    mod = tmp_path / "mods" / "isaac_threrisaifuture_observer"
    mod.mkdir(parents=True)
    path = write_training_approval(tmp_path, hours=2, max_restarts=300, now=1000)
    approval = TrainingApproval.model_validate_json(path.read_text())
    assert approval.expires_at == 1000 + 7200 and approval.slot == 2
    assert approval.max_restarts == 300 and "game_epoch" not in path.read_text()
    assert not list(mod.glob("*.tmp"))


@pytest.mark.parametrize("hours,restarts", [(0, 10), (9, 10), (1, -1), (1, 5001)])
def test_training_approval_bounds(tmp_path, hours, restarts):
    (tmp_path / "mods" / "isaac_threrisaifuture_observer").mkdir(parents=True)
    with pytest.raises(ValueError):
        write_training_approval(tmp_path, hours=hours, max_restarts=restarts)


def test_training_approval_zero_restarts_means_unlimited(tmp_path):
    (tmp_path / "mods" / "isaac_threrisaifuture_observer").mkdir(parents=True)
    path = write_training_approval(tmp_path, hours=1, max_restarts=0, now=1000)
    assert TrainingApproval.model_validate_json(path.read_text()).max_restarts == 0


def test_training_approval_requires_deployed_mod(tmp_path):
    with pytest.raises(ValueError):
        write_training_approval(tmp_path, hours=1, max_restarts=10)


@pytest.mark.parametrize("option", ["safe_actions", "restart_after_death", "entity_observations"])
def test_live_loop_config_is_exclusive(option):
    with pytest.raises(ValueError):
        ObserverConfig(live_loop=True, **{option: True})


def test_overflow_history_stays_bounded_without_inventing_kills():
    deriver = EventDeriver()
    for index in range(10):
        snap = live(index + 1, enemies=[(index * 64 + j, 10.0) for j in range(64)], overflow=1)
        events = deriver.begin(snap) if index == 0 else deriver.update(snap)
        assert len(deriver._enemies) <= 64
        assert not any(event.kind == "enemy_killed" for event in events)


def test_fatal_reader_protocol_error_is_not_reconnected(monkeypatch):
    from isaac_threrisaifuture.live import LIVE_SCENARIO, LiveBackend, LiveClient

    client = LiveClient(ObserverConfig())
    client._failure = ProtocolError("malformed record")
    calls = []
    monkeypatch.setattr(client, "connect", lambda: calls.append("reconnect"))
    with pytest.raises(ProtocolError, match="malformed record"):
        LiveBackend(client).start_episode(LIVE_SCENARIO, None)
    assert calls == []


def test_random_budget_caps_initial_reset_and_does_not_retry_after_expiry(monkeypatch, tmp_path):
    from isaac_threrisaifuture.live import LiveClient, LiveRunOptions, _random_run
    from isaac_threrisaifuture.observation import BridgeTimeout

    clock = [0.0]
    client = LiveClient(ObserverConfig())
    client._peer = object()  # No networking: reset uses only the substituted take.
    waits = []

    def take(timeout):
        waits.append(timeout)
        clock[0] += timeout
        raise BridgeTimeout("no playable state")

    monkeypatch.setattr(client, "take", take)
    monkeypatch.setattr(client, "close_peer", lambda: None)
    monkeypatch.setattr(client, "close", lambda: None)
    monkeypatch.setattr("isaac_threrisaifuture.live.time.monotonic", lambda: clock[0])
    records = []
    _random_run(
        client,
        LiveRunOptions(mode="random", out_dir=tmp_path, minutes=0.01),
        lambda *row: records.append(row),
        lambda event: None,
        None,
    )
    assert waits == [pytest.approx(0.6)]
    assert clock[0] == pytest.approx(0.6)
    assert records[-1] == ("budget", "wall time reached")


def test_budget_expiry_does_not_consume_fault_retries(monkeypatch):
    from isaac_threrisaifuture.live import LiveBudgetExpired

    env = FaultTolerantEnv(Flaky([]), max_faults=20, run_deadline=10.0)
    monkeypatch.setattr("isaac_threrisaifuture.live.time.monotonic", lambda: 10.0)
    with pytest.raises(LiveBudgetExpired):
        env.reset()
    assert env.faults == 0


def test_interrupted_training_rollout_does_not_claim_a_checkpoint(monkeypatch, tmp_path):
    reason = "Live wall-time budget exhausted"
    from isaac_threrisaifuture.live import LiveBudgetExpired, LiveRunOptions, _train_run

    def expire(*args, **kwargs):
        raise LiveBudgetExpired(reason)

    monkeypatch.setattr("isaac_threrisaifuture.training.train", expire)
    records = []
    _train_run(
        None,
        LiveRunOptions(mode="train", out_dir=tmp_path),
        lambda *row: records.append(row),
        lambda event: None,
    )
    assert [row[0] for row in records] == ["training", "budget"]
    assert "no new checkpoint" in records[-1][1]
    assert records[-1][1].startswith(reason)
    assert not list(tmp_path.rglob("latest.txt"))
