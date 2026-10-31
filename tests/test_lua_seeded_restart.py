"""OFFLINE production Lua: seeded restarts for level replay (capability `seeded_restart_v1`).

The game API is simulated (`GetSeeds():GetStartSeedString()`); whether the real `seed` console
command behaves like `restart` is a native check (openspec change prioritized-level-replay).
"""

import json
import time

import pytest
from test_async_restart_training import REAL_ORDER, SOCKET_SHIM, Game, Shim, defer
from test_lua_live_loop import acks, build_live, hello, live_snapshots, records, send
from test_lua_observer import tick
from test_lua_restart_command import DEFAULT_ROOM, dispatches, logged

from isaac_threrisaifuture.level_replay import SeedBank
from isaac_threrisaifuture.live import LiveClient, make_live_env
from isaac_threrisaifuture.observation import HelloAck, decode
from isaac_threrisaifuture.observer_client import (
    LIVE_LOOP_CAPABILITIES,
    SEEDED_RESTART_CAPABILITY,
    ObserverConfig,
)

SEEDED = (*LIVE_LOOP_CAPABILITIES, SEEDED_RESTART_CAPABILITY)
# Simulated start seeds (not engine evidence): `seed X` starts X, a plain restart the next fresh
# seed of FRESH_SEEDS.
SEED_STUBS = """
START_SEED, FRESH_SEEDS, FRESH_INDEX = "AAAA BBBB", { "CCCC DDDD", "EEEE FFFF" }, 0
SEED_READS = 0
local seed_game = Game
Game = function()
 local game = seed_game()
 game.GetSeeds = function()
  return { GetStartSeedString = function()
   SEED_READS = SEED_READS + 1
   if SEED_FAIL then error("simulated seed fault") end
   return START_SEED
  end }
 end
 return game
end
local seed_execute = Isaac.ExecuteCommand
Isaac.ExecuteCommand = function(command)
 if command:sub(1, 5) == "seed " then START_SEED = command:sub(6)
 else FRESH_INDEX = FRESH_INDEX + 1; START_SEED = FRESH_SEEDS[FRESH_INDEX] or START_SEED end
 return seed_execute(command)
end
"""


def started(capabilities=SEEDED, *, auto_start=True, room=DEFAULT_ROOM):
    lua = build_live(max_restarts=5)
    lua.execute(SEED_STUBS)
    lua.execute(f"AUTO_START={'true' if auto_start else 'false'}; {room}")
    hello(lua, capabilities)
    tick(lua, 5)
    return lua


def reconnect(lua, session, capabilities=SEEDED):
    lua.execute('PEER_CLOSED=false; OUTGOING=""; INCOMING=""')
    calls = lua.eval("CONNECT_CALLS")
    for _ in range(400):
        if lua.eval("CONNECT_CALLS") > calls:
            break
        tick(lua, delta=17)
    hello(lua, capabilities, session=session)
    tick(lua, 5)


def die(lua):
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, 100, delta=20)


def test_seeded_restart_is_advertised_and_reports_the_run_seed():
    lua = started()
    ack = decode(records(lua, "hello_ack")[0].encode(), HelloAck)
    assert SEEDED_RESTART_CAPABILITY in ack.capabilities
    snap = live_snapshots(lua)[-1]
    assert snap.oracle is not None and snap.oracle.run_seed == "AAAA BBBB"
    reads = lua.eval("SEED_READS")
    tick(lua, 10)
    assert lua.eval("SEED_READS") == reads  # read once per game epoch
    # The policy frame never carries the seed; it lives in the oracle block only.
    raw = json.loads(records(lua, "snapshot")[-1])
    assert "run_seed" not in json.dumps(raw["entity_frame"]) and "seed" not in raw["entity_frame"]


def test_without_the_capability_snapshots_and_restarts_are_unchanged():
    lua = started(LIVE_LOOP_CAPABILITIES)
    raw = json.loads(records(lua, "snapshot")[-1])
    assert "run_seed" not in raw["oracle"]
    assert send(lua, sequence=1, kind="restart").status == "accepted"
    tick(lua, 30)
    assert dispatches(lua) == ["restart"]


def test_seeded_restarts_require_the_live_loop():
    lua = build_live()
    lua.execute(SEED_STUBS)
    hello(lua, [SEEDED_RESTART_CAPABILITY])
    assert lua.globals().CLOSED and not records(lua, "hello_ack")


@pytest.mark.parametrize("seed", ["AAAA BBBB", None])
def test_an_unreadable_or_invalid_seed_is_null(seed):
    lua = build_live()
    lua.execute(SEED_STUBS)
    lua.execute("SEED_FAIL=true" if seed else 'START_SEED="iiii 5555"')
    lua.execute(DEFAULT_ROOM)
    hello(lua, SEEDED)
    tick(lua, 5)
    assert not lua.globals().CLOSED
    raw = json.loads(records(lua, "snapshot")[-1])
    assert raw["oracle"]["run_seed"] is None


def test_a_seeded_stall_restart_issues_exactly_the_seed_command():
    lua = started()
    assert send(lua, sequence=1, kind="restart", seed="T1MM AY48").status == "accepted"
    tick(lua, 30)
    assert dispatches(lua) == ["seed T1MM AY48"]
    assert logged(lua, "source=command seed=T1MM AY48")
    reconnect(lua, "b" * 32)
    snap = live_snapshots(lua)[-1]
    assert snap.game_epoch == 2 and snap.oracle is not None and snap.oracle.run_seed == "T1MM AY48"


def test_a_plain_restart_is_unchanged_with_the_capability():
    lua = started()
    assert send(lua, sequence=1, kind="restart").status == "accepted"
    tick(lua, 30)
    assert dispatches(lua) == ["restart"]
    reconnect(lua, "b" * 32)
    assert live_snapshots(lua)[-1].oracle.run_seed == "CCCC DDDD"


def test_the_armed_seed_routes_the_death_restart_through_the_same_guarded_path():
    lua = started()
    assert send(lua, sequence=1, kind="next_seed", seed="T1MM AY48").status == "accepted"
    assert logged(lua, "Next run seed armed epoch=1 seed=T1MM AY48")
    die(lua)
    assert dispatches(lua) == ["seed T1MM AY48"]
    assert logged(lua, "source=death seed=T1MM AY48") and logged(lua, "Death restart confirmed")
    # The armed seed belongs to one epoch: the next death restart is plain again.
    reconnect(lua, "b" * 32)
    lua.execute("callbacks.render()")
    tick(lua, 250, delta=20)  # the 4 s restart pacing
    die(lua)
    assert dispatches(lua) == ["seed T1MM AY48", "restart"]


def test_a_disconnect_drops_the_armed_seed():
    lua = started()
    assert send(lua, sequence=1, kind="next_seed", seed="T1MM AY48").status == "accepted"
    lua.execute("PEER_CLOSED=true")
    tick(lua, 5)
    reconnect(lua, "b" * 32)
    die(lua)
    assert dispatches(lua) == ["restart"]


@pytest.mark.parametrize(
    "seed",
    ["t1mm ay48", "T1MMAY48", "IIII AAAA", "5AAA AAAA", "T1MM AY48 ", "T1MM; AY48", "",
     'T1MM AY48"; restart "'],
)  # fmt: skip
def test_malformed_seeds_close_the_session_and_are_never_dispatched(seed):
    for kind in ("restart", "next_seed"):
        lua = started()
        snap = live_snapshots(lua)[-1]
        command = {
            "type": "command", "protocol_version": 1, "session_id": snap.session_id,
            "sequence": 1, "game_epoch": snap.game_epoch, "room_visit": snap.room.visit_id,
            "frame_id": snap.frame_id, "kind": kind, "move": "none", "shoot": "none",
            "use": "none", "frames": 0, "seed": seed,
        }  # fmt: skip
        lua.globals().INCOMING = json.dumps(command, separators=(",", ":")) + "\n"
        tick(lua, 30)
        assert lua.globals().CLOSED and dispatches(lua) == [] and not acks(lua)


def test_seeds_need_the_capability_and_only_ride_restart_or_next_seed():
    lua = started(LIVE_LOOP_CAPABILITIES)
    with pytest.raises(Exception):  # noqa: B017 - the session closes before an ack exists
        send(lua, sequence=1, kind="next_seed", seed="T1MM AY48")
    assert lua.globals().CLOSED and dispatches(lua) == []
    lua = started()
    snap = live_snapshots(lua)[-1]
    raw = (
        '{"type":"command","protocol_version":1,"session_id":"' + snap.session_id
        + '","sequence":1,"game_epoch":1,"room_visit":' + str(snap.room.visit_id)
        + ',"frame_id":' + str(snap.frame_id)
        + ',"kind":"heartbeat","move":"none","shoot":"none","use":"none","frames":0,'
        + '"seed":"T1MM AY48"}\n'
    )  # fmt: skip
    lua.globals().INCOMING = raw
    tick(lua, 5)
    assert lua.globals().CLOSED and dispatches(lua) == []


def test_next_seed_is_refused_once_a_restart_is_scheduled():
    lua = started(auto_start=False)
    assert send(lua, sequence=1, kind="restart").status == "accepted"
    assert send(lua, sequence=2, kind="next_seed", seed="T1MM AY48").status == "rejected"
    assert not lua.globals().CLOSED


def test_plr_through_the_loopback_seeds_the_death_restart():
    """Python plans a replay, arms it, the player dies and the mod starts that seed."""
    seeds = SeedBank(replay_probability=1.0, capacity=10, seed=1)
    seeds.begin_run("GGGG HHHH", 99)  # an earlier, scored run of the seed to replay
    seeds.score_rollout([seeds.current_run], [2.0])
    client = LiveClient(ObserverConfig(port=0, accept_timeout=10.0, live_loop=True,
                                       seeded_restart=True))  # fmt: skip
    with client:
        lua = build_live(max_restarts=1)
        lua.execute(SEED_STUBS)
        shim = Shim(client.address[1])
        lua.globals().PY = shim
        lua.execute(SOCKET_SHIM)
        lua.execute("SEND_LIMIT=1e9; ROOM_ENTITIES={ make_enemy(1,160,200,10,10) }")
        defer(lua, REAL_ORDER)
        game = Game(lua)
        game.every = "run_due()"
        game.start()
        try:
            env = make_live_env(client, max_faults=0, run_deadline=time.monotonic() + 60,
                                level_replay=seeds)  # fmt: skip
            client.connect()
            env.reset()
            assert seeds.facts() == {"run_seed": "AAAA BBBB", "seed_replayed": 0}
            assert seeds.planned_seed == "GGGG HHHH"
            env.step([0, 0, 0])  # the first step arms the planned seed
            game.tasks.append("IS_DEAD=true; callbacks.game_end(mod,true)")
            info: dict = {}
            for _ in range(200):
                _, _, terminated, truncated, info = env.step([0, 0, 0])
                if terminated or truncated:
                    break
            assert info.get("outcome") == "death"
            assert info["episode_summary"]["run_seed"] == "AAAA BBBB"
            env.reset()
            assert seeds.facts() == {"run_seed": "GGGG HHHH", "seed_replayed": 1}
            env.close()
        finally:
            game.stop.set()
            game.join(timeout=5)
            shim.close()
        assert game.error is None
        assert list(lua.globals().COMMANDS.values()) == ["seed GGGG HHHH"]
