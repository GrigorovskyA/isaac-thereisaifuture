"""OFFLINE end-to-end live loop: production main.lua in lupa over a real loopback socket.

The simulated game (stubs) is not Isaac evidence; this checks the Lua <-> Python
contract: negotiation, actions, approximate events, death restart and reconnect.
"""

import socket
import threading
import time
from collections import deque
from pathlib import Path

import numpy as np
import pytest
from test_lua_live_loop import build_live

from isaac_threrisaifuture.env import IsaacCombatEnv
from isaac_threrisaifuture.live import (
    LIVE_SCENARIO,
    FaultTolerantEnv,
    LiveBackend,
    LiveClient,
    LiveRunOptions,
    run_live,
)
from isaac_threrisaifuture.observer_client import ObserverConfig
from isaac_threrisaifuture.rewards import RewardLedgerV3, RewardV3Coefficients

SOCKET_SHIM = """
local tcp = {
 settimeout=function(self,t) return 1 end,
 connect=function(self,h,p) return PY.connect() end,
 getpeername=function(self) return PY.peer() end,
 receive=function(self,n) return PY.receive(n) end,
 send=function(self,data,first,last) return PY.send(data,first,last) end,
 close=function(self) PY.close() end
}
package.preload["socket.core"] = function() return { tcp=function() return tcp end } end
"""


class Shim:
    """Nonblocking LuaSocket subset backed by a real TCP socket (game thread only)."""

    def __init__(self, port: int) -> None:
        self.port = port
        self.sock: socket.socket | None = None

    def connect(self):
        self.close()
        self.sock = socket.socket()
        self.sock.setblocking(False)
        code = self.sock.connect_ex(("127.0.0.1", self.port))
        return 1 if code == 0 else (None, "timeout")

    def peer(self):
        try:
            return self.sock.getpeername() if self.sock else None
        except OSError:
            return None

    def receive(self, n):
        try:
            data = self.sock.recv(n)
        except BlockingIOError:
            return None, "timeout", ""
        except OSError:
            return None, "closed", ""
        if not data:
            return None, "closed", ""
        return None, "timeout", data.decode()

    def send(self, data, first, last):
        try:
            sent = self.sock.send(data[first - 1 : last].encode())
        except BlockingIOError:
            return None, "timeout", first - 1
        except OSError:
            return None, "closed", first - 1
        return first - 1 + sent if first - 1 + sent == last else (None, "timeout", first - 1 + sent)

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None


class Game(threading.Thread):
    """Drives render (60/s) and update (30/s) at 2x speed; the only Lua thread."""

    def __init__(self, lua) -> None:
        super().__init__(daemon=True)
        self.lua = lua
        self.tasks: deque = deque()
        self.stop = threading.Event()
        self.error: BaseException | None = None
        self.every = ""

    def run(self) -> None:
        tick = 0
        try:
            while not self.stop.is_set():
                while self.tasks:
                    self.lua.execute(self.tasks.popleft())
                tick += 1
                self.lua.execute("NOW=NOW+17;" + self.every)
                if tick % 2 == 0:
                    self.lua.execute("FRAME=FRAME+1; callbacks.update()")
                self.lua.execute("callbacks.render()")
                time.sleep(0.008)
        except BaseException as exc:
            self.error = exc


@pytest.fixture
def world():
    client = LiveClient(ObserverConfig(port=0, accept_timeout=10.0))
    with client:
        lua = build_live(max_restarts=2)
        shim = Shim(client.address[1])
        lua.globals().PY = shim
        lua.execute(SOCKET_SHIM)
        lua.execute(
            "AUTO_START=true; SEND_LIMIT=1e9;"
            " ROOM_ENTITIES={ make_enemy(1,160,200,10,10), make_enemy(2,40,200,6,6) }"
        )
        game = Game(lua)
        game.start()
        try:
            yield client, game
        finally:
            game.stop.set()
            game.join(timeout=5)
            shim.close()
    assert game.error is None


COEF = RewardV3Coefficients.load()


def make_env(client):
    backend = LiveBackend(client, restart_timeout=20.0)
    ledger = RewardLedgerV3(COEF)
    events = []
    env = IsaacCombatEnv(backend, [LIVE_SCENARIO], accountant=ledger, oracle_sink=events.append)
    return FaultTolerantEnv(env, max_faults=0), events


def test_live_loop_rewards_death_restart_and_next_episode(world):
    client, game = world
    env, events = make_env(client)
    obs, info = env.reset(seed=1)
    assert obs.shape == env.observation_space.shape
    first_session = client._session
    action = np.array([2, 1, 0])
    total = 0.0
    _, reward, terminated, truncated, info = env.step(action)
    assert not terminated and not truncated
    game.tasks.append("ROOM_ENTITIES[1].HitPoints=4")
    for _ in range(5):
        _, reward, *_ = env.step(action)
        total += reward
    assert total > 0  # damage reward from an approximate frame delta
    game.tasks.append("ROOM_ENTITIES={}; ROOM_CLEAR=true")
    clear_reward = 0.0
    for _ in range(10):
        _, reward, terminated, truncated, info = env.step(action)
        clear_reward += info["reward_components"]["room_clear"]
        assert not terminated and not truncated  # a room clear never ends the run
    assert clear_reward == COEF.room_clear_first
    assert {e.kind for e in events} >= {"enemy_spawned", "enemy_damaged", "room_cleared"}
    assert not any(e.kind == "enemy_killed" for e in events)

    game.tasks.append("ROOM_CLEAR=false; IS_DEAD=true; callbacks.game_end(mod,true)")
    for _ in range(20):
        _, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break
    assert terminated and info["outcome"] == "death" and reward < 0
    summary = info["episode_summary"]
    assert summary["outcome"] == "terminated" and summary["end_reason"] == "death"
    assert summary["rooms_cleared"] == 1 and summary["columns"]["death"] == COEF.death
    assert summary["damage_dealt_fraction"] > 0

    env.reset()  # waits for the autonomous restart, then reconnects
    assert client._session != first_session
    _, _, terminated, truncated, info = env.step(action)
    assert not terminated and "fault" not in info
    env.close()


def free_port():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture
def lua_game():
    port = free_port()
    lua = build_live(max_restarts=5)
    shim = Shim(port)
    lua.globals().PY = shim
    lua.execute(SOCKET_SHIM)
    lua.execute("AUTO_START=true; SEND_LIMIT=1e9; ROOM_ENTITIES={ make_enemy(1,160,200,10,10) }")
    game = Game(lua)
    game.start()
    yield port, game
    game.stop.set()
    game.join(timeout=5)
    shim.close()
    assert game.error is None


def read_jsonl(path):
    import json

    return [json.loads(line) for line in path.read_text().splitlines()]


def test_run_live_random_mode_logs_episodes_and_separate_oracle(lua_game, tmp_path):
    port, game = lua_game
    game.every = "local e=ROOM_ENTITIES[1]; e.HitPoints=math.max(1,e.HitPoints-0.01)"
    logs = run_live(LiveRunOptions(mode="random", out_dir=tmp_path, steps=40, seed=3, port=port))
    live_log = read_jsonl(logs / "live.jsonl")
    assert [r["event"] for r in live_log][:3] == ["configuration", "listening", "connected"]
    assert all(r["event"] != "fault" for r in live_log)
    oracle = read_jsonl(logs / "oracle.jsonl")
    assert any(e["kind"] == "enemy_damaged" for e in oracle)
    assert "enemy_damaged" not in (logs / "live.jsonl").read_text()


def test_run_live_train_mode_checkpoints(lua_game, tmp_path):
    port, _ = lua_game
    config = tmp_path / "tiny.yaml"
    text = (Path(__file__).parents[1] / "configs/training-live-v1.yaml").read_text()
    config.write_text(
        text.replace("n_steps: 256", "n_steps: 16")
        .replace("batch_size: 64", "batch_size: 8")
        .replace("lstm_hidden_size: 128", "lstm_hidden_size: 16")
    )
    run_live(
        LiveRunOptions(
            mode="train", out_dir=tmp_path, steps=16, seed=5, config_path=config, port=port
        )
    )
    assert (tmp_path / "seed-5" / "checkpoints" / "latest.txt").is_file()
