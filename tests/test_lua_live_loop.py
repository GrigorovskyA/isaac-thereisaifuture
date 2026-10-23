"""OFFLINE production Lua live loop: training approval, oracle block, refusals, restarts."""

import json
import time

import pytest
from test_lua_entities import STUBS as ENTITY_STUBS
from test_lua_entities import fill_worst_case
from test_lua_observer import build_lua, tick

from isaac_threrisaifuture.actions import Command
from isaac_threrisaifuture.live import LiveCommandAck, LiveSnapshot
from isaac_threrisaifuture.observation import CAPABILITIES, HelloAck, decode
from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES

LIVE_STUBS = """
ROOM_CLEAR = false
function make_enemy(id, x, y, hp, max_hp, visible)
 local e = make_entity(id, x, y, 10, visible)
 e.HitPoints, e.MaxHitPoints = hp, max_hp
 return e
end
local entity_game = Game
Game = function()
 local game = entity_game()
 local base_room = game.GetRoom
 game.GetRoom = function(self)
  local room = base_room(self)
  room.IsClear = function() return ROOM_CLEAR end
  return room
 end
 return game
end
"""

TRAINING = dict(profile_mode="training", game_epoch=None, max_restarts=3)


def build_live(*, source_changes=None, **changes):
    approval = dict(TRAINING, expires_at=int(time.time()) + 3600)
    approval.update(changes)
    lua = build_lua(
        approved=True,
        approval_changes=approval,
        source_changes=source_changes,
    )
    lua.execute(ENTITY_STUBS)
    lua.execute(LIVE_STUBS)
    lua.execute("callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=8192")
    return lua


def hello(lua, capabilities, session="a" * 32):
    tick(lua)
    request = {
        "type": "hello",
        "protocol_version": 1,
        "schema_version": 1,
        "session_id": session,
        "required_capabilities": list(CAPABILITIES) + list(capabilities),
    }
    lua.globals().INCOMING = json.dumps(request, separators=(",", ":")) + "\n"
    tick(lua, 15)


def records(lua, kind):
    return [
        line for line in lua.globals().OUTGOING.split("\n")[:-1] if json.loads(line)["type"] == kind
    ]


def live_snapshots(lua):
    return [decode(line.encode(), LiveSnapshot) for line in records(lua, "snapshot")]


def acks(lua):
    return [decode(line.encode(), LiveCommandAck) for line in records(lua, "command_ack")]


@pytest.fixture
def live():
    lua = build_live()
    lua.execute("ROOM_ENTITIES={ make_enemy(1,140,200,10,20), make_enemy(2,0,0,5,5,false) }")
    hello(lua, LIVE_LOOP_CAPABILITIES)
    assert not lua.globals().CLOSED
    return lua


def send(lua, *, sequence, kind="action", **changes):
    snap = live_snapshots(lua)[-1]
    values = dict(
        session_id=snap.session_id,
        sequence=sequence,
        game_epoch=snap.game_epoch,
        room_visit=snap.room.visit_id,
        frame_id=snap.frame_id,
        kind=kind,
        move="right" if kind == "action" else "none",
        shoot="up" if kind == "action" else "none",
        frames=5 if kind == "action" else 0,
    )
    values.update(changes)
    lua.globals().INCOMING = Command(**values).wire_bytes().decode()
    tick(lua, delta=1)
    return acks(lua)[-1]


def held(lua):
    return lua.eval("callbacks.input(mod,TEST_PLAYER,2,1)")


def test_training_approval_advertises_and_negotiates_live_loop(live):
    ack = decode(records(live, "hello_ack")[0].encode(), HelloAck)
    assert "live_loop_v1" in ack.capabilities
    assert ack.mod_version == "0.5.0-dev"
    tick(live, 10)
    snaps = live_snapshots(live)
    assert len(snaps) >= 2 and snaps[-1].oracle is not None


@pytest.mark.parametrize(
    "capabilities",
    [
        ["live_loop_v1"],
        ["entity_observation_v1", "safe_actions_v1", "live_loop_v1"],
        ["entity_observation_v1", "death_restart_v1", "live_loop_v1"],
        list(LIVE_LOOP_CAPABILITIES) + ["oracle_probe_v1"],
        ["safe_actions_v1"],
        ["entity_observation_v1", "safe_actions_v1", "death_restart_v1"],
    ],
)
def test_incomplete_mixed_or_unlooped_training_requests_close(capabilities):
    lua = build_live()
    hello(lua, capabilities)
    assert lua.globals().CLOSED
    assert not records(lua, "hello_ack")


@pytest.mark.parametrize(
    "changes",
    [
        dict(profile_mode="isolated", game_epoch=1, max_restarts=None),
        dict(game_epoch=1),
        dict(max_restarts=-1),
        dict(max_restarts=5001),
        dict(max_restarts=1.5),
        dict(expires_at=int(time.time()) + 28800 + 600),
        dict(expires_at=int(time.time()) - 1),
    ],
)
def test_invalid_or_non_training_approval_never_advertises_live_loop(changes):
    lua = build_live(**changes)
    hello(lua, [])
    ack = decode(records(lua, "hello_ack")[0].encode(), HelloAck)
    assert "live_loop_v1" not in ack.capabilities


def test_legacy_approval_rejects_max_restarts_field():
    lua = build_live(profile_mode="isolated", game_epoch=1)
    hello(lua, [])
    ack = decode(records(lua, "hello_ack")[0].encode(), HelloAck)
    assert "safe_actions_v1" not in ack.capabilities


def test_oracle_block_separates_labels_from_policy_frame(live):
    tick(live, 5)
    snap = live_snapshots(live)[-1]
    assert snap.oracle is not None and snap.entity_frame is not None
    assert sorted((e.hp, e.max_hp) for e in snap.oracle.enemies) == [(5, 5), (10, 20)]
    assert not snap.oracle.room_clear and not snap.oracle.player_dead
    visible = [e for e in snap.entity_frame.entities if e.kind == "enemy"]
    assert len(visible) == 1 and visible[0].hp is None and visible[0].max_hp is None
    oracle_ids = {e.entity_id for e in snap.oracle.enemies}
    assert visible[0].entity_id in oracle_ids
    live.execute("ROOM_CLEAR=true; ROOM_ENTITIES={}")
    tick(live, 5)
    snap = live_snapshots(live)[-1]
    assert snap.oracle is not None and snap.oracle.room_clear and snap.oracle.enemies == []


def test_oracle_bounds_hp_and_counts_overflow():
    lua = build_live()
    lua.execute(
        "ROOM_ENTITIES={ make_enemy(1,140,200,30,20), make_enemy(2,140,200,0/0,5),"
        " make_enemy(3,140,200,1,0) }"
        " for i=4,70 do ROOM_ENTITIES[#ROOM_ENTITIES+1]=make_enemy(i,150,200,1,1) end"
    )
    hello(lua, LIVE_LOOP_CAPABILITIES)
    tick(lua, 5)
    oracle = live_snapshots(lua)[-1].oracle
    assert oracle is not None
    # 1 clamped + 67 valid enemies; NaN hp and max_hp<=0 are skipped.
    assert len(oracle.enemies) == 64 and oracle.enemy_overflow == 68 - 64
    assert max(e.hp for e in oracle.enemies) == 20  # hp above max_hp is clamped
    assert all(e.hp == e.hp for e in oracle.enemies)  # NaN and max_hp<=0 are skipped


def test_accepted_action_holds_input_and_older_frame_reference_is_allowed(live):
    tick(live, 3)
    snap = live_snapshots(live)[-2]
    ack = send(live, sequence=1, frame_id=snap.frame_id)
    assert ack.status == "accepted"
    assert held(live) == 1.0


@pytest.mark.parametrize("state", ["IS_DEAD=true", "PAUSED=true", "PLAYER_COUNT=2"])
def test_state_races_are_rejected_without_closing(live, state):
    send(live, sequence=1)
    assert held(live) == 1.0
    live.execute(state)
    ack = send(live, sequence=2)
    assert ack.status == "rejected" and not live.globals().CLOSED
    assert not held(live)
    live.execute("IS_DEAD=false; PAUSED=false; PLAYER_COUNT=1")
    tick(live, 3)
    assert send(live, sequence=3).status == "accepted"


@pytest.mark.parametrize(
    "changes", [dict(room_visit=99), dict(game_epoch=99), dict(frame_id=10**6)]
)
def test_stale_identity_is_rejected_without_closing(live, changes):
    ack = send(live, sequence=1, **changes)
    assert ack.status == "rejected" and not live.globals().CLOSED


def test_window_overrun_is_rejected(live):
    snap = live_snapshots(live)[-1]
    live.execute("FRAME=FRAME+16")
    assert send(live, sequence=1, frame_id=snap.frame_id).status == "rejected"


def test_replayed_sequence_still_closes_the_session(live):
    send(live, sequence=2)
    live.globals().INCOMING = (
        Command(
            session_id="a" * 32,
            sequence=2,
            game_epoch=live_snapshots(live)[-1].game_epoch,
            room_visit=live_snapshots(live)[-1].room.visit_id,
            frame_id=live_snapshots(live)[-1].frame_id,
            kind="heartbeat",
            move="none",
            shoot="none",
            frames=0,
        )
        .wire_bytes()
        .decode()
    )
    tick(live, delta=1)
    assert live.globals().CLOSED


def test_missed_heartbeat_releases_input_but_keeps_session(live):
    send(live, sequence=1, frames=15)
    assert held(live) == 1.0
    live.execute("NOW=NOW+600")
    tick(live, delta=1)
    assert not held(live)
    assert not live.globals().CLOSED
    tick(live, 5)
    assert send(live, sequence=2).status == "accepted"


def reconnect(lua, session):
    lua.execute('PEER_CLOSED=false; OUTGOING=""')
    tick(lua, delta=1001)
    hello(lua, LIVE_LOOP_CAPABILITIES, session=session)


def die(lua):
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, 100, delta=20)


def test_autonomous_restart_keeps_training_approval_and_reconnects():
    lua = build_live()
    lua.execute("AUTO_START=true")
    hello(lua, LIVE_LOOP_CAPABILITIES)
    die(lua)
    assert list(lua.globals().COMMANDS.values()) == ["restart"]
    assert lua.globals().CLOSED  # engine restart fires PRE_GAME_EXIT
    reconnect(lua, "b" * 32)
    ack = decode(records(lua, "hello_ack")[0].encode(), HelloAck)
    assert "live_loop_v1" in ack.capabilities


def test_restart_budget_and_interval_follow_training_approval():
    lua = build_live(max_restarts=2)
    lua.execute("AUTO_START=true")
    sessions = iter("bcdef")
    hello(lua, LIVE_LOOP_CAPABILITIES)
    for _ in range(4):
        die(lua)
        reconnect(lua, next(sessions) * 32)
    assert list(lua.globals().COMMANDS.values()) == ["restart", "restart"]


def test_restart_dispatches_respect_minimum_interval():
    lua = build_live(max_restarts=5)
    lua.execute("AUTO_START=true")
    hello(lua, LIVE_LOOP_CAPABILITIES)
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, 80, delta=20)  # 1.6 s: first dispatch after the 1.5 s delay
    assert len(lua.globals().COMMANDS) == 1
    reconnect(lua, "b" * 32)
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, 80, delta=20)
    assert len(lua.globals().COMMANDS) == 1  # within the 4 s live interval
    tick(lua, 100, delta=20)
    assert len(lua.globals().COMMANDS) == 2


def test_normal_exit_drops_training_approval():
    lua = build_live()
    hello(lua, LIVE_LOOP_CAPABILITIES)
    lua.execute("callbacks.exit(mod,false); callbacks.start(mod,false)")
    lua.globals().OUTGOING = ""
    tick(lua, 60)
    hello(lua, [], session="b" * 32)
    ack = decode(records(lua, "hello_ack")[0].encode(), HelloAck)
    assert "safe_actions_v1" not in ack.capabilities


def test_oracle_carries_room_index_and_the_policy_frame_does_not(live):
    live.execute("ROOM_INDEX=97")
    tick(live, 5)
    snap = live_snapshots(live)[-1]
    assert snap.oracle is not None and snap.oracle.room_index == 97
    assert "room_index" not in snap.entity_frame.model_dump_json()
    live.execute("ROOM_INDEX=-4")  # special rooms use negative indexes
    tick(live, 5)
    assert live_snapshots(live)[-1].oracle.room_index == -4


def test_live_use_press_triggers_once_and_releases(live):
    ack = send(live, sequence=1, use="bomb")
    assert ack.status == "accepted"
    assert live.eval("callbacks.input(mod,TEST_PLAYER,0,10)") is True
    assert live.eval("callbacks.input(mod,TEST_PLAYER,1,10)") is True
    assert live.eval("callbacks.input(mod,TEST_PLAYER,1,10)") is False
    assert live.eval("callbacks.input(mod,TEST_PLAYER,0,10)") is True
    send(live, sequence=2, kind="release")
    assert live.eval("callbacks.input(mod,TEST_PLAYER,0,10)") is None


def test_worst_case_live_snapshot_with_oracle_fits_the_wire_limit():
    lua = build_live()
    fill_worst_case(lua)
    lua.execute("""
      for i=1,70 do
        ROOM_ENTITIES[#ROOM_ENTITIES+1]=make_enemy(1000+i,-700.123+i,-600.456,123456.789,999999.999)
      end
    """)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    tick(lua, 40)
    snap = live_snapshots(lua)[-1]
    assert snap.oracle is not None and len(snap.oracle.enemies) == 64
    assert len(snap.entity_frame.collectibles) == 256
    assert len(snap.entity_frame.entities) == 84  # every kind at its cap, incl. 16 own, 4 bombs
    sizes = [len(line.encode()) for line in records(lua, "snapshot")]
    print("worst-case live snapshot bytes:", max(sizes))
    assert max(sizes) < 49152 and not lua.globals().CLOSED


METRIC_STUBS = """
EntityFlag = { FLAG_FRIENDLY = 1 << 13 }
DamageFlag = { DAMAGE_EXPLOSION = 1 << 2, DAMAGE_SPIKES = 1 << 7, DAMAGE_FIRE = 1 << 12,
 DAMAGE_ACID = 1 << 22, DAMAGE_CURSED_DOOR = 1 << 28 }
EntityType.ENTITY_BOMB, EntityType.ENTITY_PROJECTILE = 4, 9
function make_npc(enemy, friendly)
 return { IsEnemy=function() return enemy end,
  HasEntityFlags=function(self, flag) return friendly and flag == EntityFlag.FLAG_FRIENDLY end }
end
function hit(flags, source, victim)
 return callbacks.damage(mod, victim or TEST_PLAYER, 1, flags, source, 0)
end
"""

HIT_CASES = [
    ("DamageFlag.DAMAGE_EXPLOSION", "{Type=4, Entity={SpawnerType=1}}", "own_bomb"),
    ("DamageFlag.DAMAGE_EXPLOSION", "{Type=4, Entity={SpawnerType=10}}", "explosion"),
    ("DamageFlag.DAMAGE_EXPLOSION", "{Type=4, Entity={Spawner=TEST_PLAYER}}", "own_bomb"),
    ("DamageFlag.DAMAGE_EXPLOSION", "{Type=0}", "explosion"),
    ("DamageFlag.DAMAGE_SPIKES", "{Type=0}", "spikes"),
    ("DamageFlag.DAMAGE_CURSED_DOOR", "{Type=0}", "spikes"),
    ("DamageFlag.DAMAGE_FIRE", "{Type=0}", "fire"),
    ("DamageFlag.DAMAGE_ACID", "{Type=0}", "creep"),
    ("0", "{Type=9}", "projectile"),
    ("0", "{Type=26}", "enemy"),
    ("0", "{Type=1000}", "other"),
    ("0", "nil", "other"),
]


def oracle_metrics(lua):
    tick(lua, 20)
    oracle = live_snapshots(lua)[-1].oracle
    return oracle.kills, oracle.player_hits.model_dump()


@pytest.fixture
def metrics():
    lua = build_live()
    lua.execute(METRIC_STUBS)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    assert not lua.globals().CLOSED
    return lua


@pytest.mark.parametrize(("flags", "source", "klass"), HIT_CASES)
def test_player_hits_are_classified_and_never_alter_damage(metrics, flags, source, klass):
    assert metrics.eval(f"hit({flags}, {source})") is None
    kills, hits = oracle_metrics(metrics)
    assert hits[klass] == 1 and sum(hits.values()) == 1 and kills == 0


def test_other_entities_do_not_count_as_player_hits(metrics):
    metrics.execute("hit(0, {Type=26}, {})")
    assert sum(oracle_metrics(metrics)[1].values()) == 0


def test_kills_count_only_unfriendly_enemies(metrics):
    metrics.execute("""
      callbacks.npc_death(mod, make_npc(true, false))
      callbacks.npc_death(mod, make_npc(true, false))
      callbacks.npc_death(mod, make_npc(true, true))
      callbacks.npc_death(mod, make_npc(false, false))
    """)
    assert oracle_metrics(metrics)[0] == 2


KILL_STUBS = """
function killable(id, friendly)
 local e = make_enemy(id, 140, 200, 10, 10)
 e.IsEnemy = function() return true end
 e.HasEntityFlags = function(self, flag) return friendly and flag == EntityFlag.FLAG_FRIENDLY end
 return e
end
"""


def killed_ids(lua):
    tick(lua, 20)
    oracle = live_snapshots(lua)[-1].oracle
    return oracle.killed, {e.entity_id for e in oracle.enemies}


def test_killed_lists_only_listed_unfriendly_enemies(metrics):
    metrics.execute(KILL_STUBS)
    metrics.execute("""
      ROOM_ENTITIES = { killable(1), killable(2), killable(3, true) }
    """)
    tick(metrics, 20)
    _, listed = killed_ids(metrics)
    assert len(listed) == 3
    metrics.execute("""
      callbacks.npc_death(mod, ROOM_ENTITIES[1])
      callbacks.npc_death(mod, ROOM_ENTITIES[3])
      callbacks.npc_death(mod, killable(9))   -- never listed
    """)
    killed, listed = killed_ids(metrics)
    assert len(killed) == 1 and killed[0] in listed
    assert oracle_metrics(metrics)[0] == 2  # the friendly one is not counted


def test_killed_keeps_the_last_sixteen_oldest_first(metrics):
    metrics.execute(KILL_STUBS)
    metrics.execute("ROOM_ENTITIES = {} for i=1,10 do ROOM_ENTITIES[i] = killable(i) end")
    tick(metrics, 20)
    first = live_snapshots(metrics)[-1].oracle
    ids = [e.entity_id for e in sorted(first.enemies, key=lambda e: e.entity_id)]
    metrics.execute("""
      for round=1,2 do for i=1,10 do callbacks.npc_death(mod, ROOM_ENTITIES[i]) end end
    """)
    killed, _ = killed_ids(metrics)
    assert len(killed) == 16 and killed == (ids + ids)[-16:]


def test_killed_is_empty_after_a_new_game(metrics):
    metrics.execute(KILL_STUBS)
    metrics.execute("ROOM_ENTITIES = { killable(1) }")
    tick(metrics, 20)
    metrics.execute("callbacks.npc_death(mod, ROOM_ENTITIES[1])")
    assert len(killed_ids(metrics)[0]) == 1
    metrics.execute("callbacks.start(mod, false)")
    assert killed_ids(metrics)[0] == []


def test_metrics_reset_on_game_start_and_stay_out_of_the_policy_frame(metrics):
    metrics.execute("callbacks.npc_death(mod, make_npc(true, false)); hit(0, {Type=9})")
    kills, hits = oracle_metrics(metrics)
    assert kills == 1 and hits["projectile"] == 1
    assert "kills" not in live_snapshots(metrics)[-1].entity_frame.model_dump_json()
    metrics.execute("callbacks.start(mod, false)")
    kills, hits = oracle_metrics(metrics)
    assert kills == 0 and sum(hits.values()) == 0


def test_failing_metric_callbacks_never_close_the_observer(metrics):
    metrics.execute("""
      callbacks.npc_death(mod, {})                       -- no IsEnemy: raises inside
      callbacks.npc_death(mod, nil)
      callbacks.damage(mod, nil, 1, 0, {}, 0)
      callbacks.damage(mod, TEST_PLAYER, 1, 1.5, {Type=9}, 0)  -- float flags: bitwise error
      Isaac.GetPlayer = function() error("simulated fault") end
      callbacks.damage(mod, TEST_PLAYER, 1, 0, {Type=9}, 0)
    """)
    assert not metrics.globals().CLOSED


def test_worst_case_oracle_metrics_fit_the_wire_limit():
    lua = build_live()
    fill_worst_case(lua)
    lua.execute(METRIC_STUBS)
    lua.execute("""
      for i=1,70 do
        ROOM_ENTITIES[#ROOM_ENTITIES+1]=make_enemy(1000+i,-700.123+i,-600.456,123456.789,999999.999)
      end
    """)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    tick(lua, 40)
    snap = live_snapshots(lua)[-1]
    assert snap.oracle is not None and len(snap.entity_frame.map) == 64
    sizes = [len(line.encode()) for line in records(lua, "snapshot")]
    print("worst-case live snapshot bytes (with map, hits):", max(sizes))
    assert max(sizes) < 49152 and not lua.globals().CLOSED
