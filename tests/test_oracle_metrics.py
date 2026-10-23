"""Kills and player hits by source reach episode rows as metrics, never as policy input."""

import csv

import numpy as np
from synthetic import oracle_metrics
from test_reward_v4 import SESSION, live

from isaac_threrisaifuture.encoding import encode
from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.episode_metrics import FIELDS, EpisodeMetricsWriter
from isaac_threrisaifuture.episodes import HIT_FIELDS
from isaac_threrisaifuture.live import LIVE_SCENARIO, LiveBackend, LiveCommandAck
from isaac_threrisaifuture.live_wire import PlayerHits
from isaac_threrisaifuture.rewards import RewardLedgerV4, RewardV4Coefficients


def counted(seq, kills=0, *, dead=False, epoch=1, **hits):
    snap = live(seq, epoch=epoch, dead=dead)
    metrics = oracle_metrics(**hits)
    metrics["kills"] = kills
    oracle = snap.oracle.model_copy(
        update={"kills": kills, "player_hits": PlayerHits.model_validate(metrics["player_hits"])}
    )
    return snap.model_copy(update={"oracle": oracle})


class ScriptedClient:
    """First snapshot from the backlog, then one scripted snapshot per take()."""

    connected = True
    failure = None

    def __init__(self, snapshots):
        self.snapshots = list(snapshots)
        self.sent = 0
        self.served = False

    def drain(self):
        if self.served:
            return []
        self.served = True
        return [self.snapshots.pop(0)]

    def take(self, timeout):
        return self.snapshots.pop(0)

    def command(self, kind, reference, **_):
        self.sent += 1
        return LiveCommandAck(
            type="command_ack", protocol_version=1, session_id=SESSION, sequence=self.sent,
            game_epoch=reference.game_epoch, room_visit=reference.room.visit_id,
            frame_id=reference.frame_id, kind=kind, status="accepted",
        )  # fmt: skip


def make_env(snapshots):
    backend = LiveBackend(ScriptedClient(snapshots))  # type: ignore[arg-type]
    return IsaacCombatEnv(
        backend,
        [LIVE_SCENARIO],
        action_repeat=1,
        accountant=RewardLedgerV4(RewardV4Coefficients.load()),
    )


def test_episode_row_counts_kills_and_hits_since_the_episode_start(tmp_path):
    snapshots = [
        counted(1, kills=4, enemy=2, own_bomb=1),  # counters before the episode do not count
        counted(2, kills=5, enemy=3),
        counted(3, kills=7, enemy=3, own_bomb=2, spikes=1),
        counted(4, kills=7, enemy=3, own_bomb=2, spikes=1, dead=True),
    ]
    env = make_env(snapshots)
    env.reset()
    for _ in range(3):
        *_, info = env.step(np.array([0, 0, 0]))
    summary = info["episode_summary"]
    assert summary["enemies_killed"] == 3 and summary["hits_enemy"] == 1
    assert summary["hits_own_bomb"] == 1 and summary["hits_spikes"] == 1
    assert summary["hits_projectile"] == summary["hits_fire"] == 0
    path = tmp_path / "episodes.csv"
    EpisodeMetricsWriter(path).write(summary)
    row = next(csv.DictReader(path.open(encoding="utf-8")))
    assert row["enemies_killed"] == "3" and row["hits_own_bomb"] == "1" and row["hits_creep"] == "0"
    assert {"enemies_killed", *HIT_FIELDS} <= set(FIELDS)
    assert info["episode"]["enemies_killed"] == 3


def test_deltas_never_go_negative_when_the_epoch_counters_reset():
    backend = LiveBackend(ScriptedClient([counted(1, kills=9, enemy=5)]))  # type: ignore[arg-type]
    backend.start_episode(LIVE_SCENARIO, None)
    assert backend.episode_oracle_stats()["kills"] == 0
    backend._current = counted(2, kills=2, enemy=1)  # counters restarted below the start values
    stats = backend.episode_oracle_stats()
    assert stats["kills"] == 2 and stats["hits_enemy"] == 1
    assert all(value >= 0 for value in stats.values())


def test_backend_without_oracle_metrics_gives_zero_hits():
    from isaac_threrisaifuture.sim import SyntheticRoomBackend

    env = IsaacCombatEnv(
        SyntheticRoomBackend(), [LIVE_SCENARIO.__class__("toy", "train", 1, 4, 1, 1.0)]
    )
    env.reset(seed=1)
    for _ in range(4):
        *_, info = env.step(np.array([0, 0, 0]))
        if "episode_summary" in info:
            break
    summary = info["episode_summary"]
    assert all(summary[name] == 0 for name in HIT_FIELDS)


def test_counters_never_enter_the_observation():
    quiet = counted(1, kills=0)
    busy = counted(1, kills=40, enemy=9, own_bomb=7, spikes=3, fire=2, creep=1)
    assert quiet.entity_frame == busy.entity_frame
    assert np.array_equal(encode(quiet.entity_frame).vector, encode(busy.entity_frame).vector)
