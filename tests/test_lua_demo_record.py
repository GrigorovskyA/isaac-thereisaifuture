"""OFFLINE production Lua demo recording: read-only handshake, oracle and human input masks."""

import json

import pytest
from test_lua_entities import STUBS as ENTITY_STUBS
from test_lua_entities import fill_worst_case
from test_lua_live_loop import LIVE_STUBS, build_live, hello, live_snapshots, records
from test_lua_observer import build_lua, tick

from isaac_threrisaifuture.live_wire import (
    DEMO_RECORD_CAPABILITY,
    HUMAN_INPUT_BITS,
    MAX_HUMAN_INPUT_MASKS,
    DemoSnapshot,
)
from isaac_threrisaifuture.observation import HelloAck, decode
from isaac_threrisaifuture.observer_client import LIVE_LOOP_CAPABILITIES

DEMO = ["entity_observation_v1", DEMO_RECORD_CAPABILITY]

# Simulated Input API (not engine evidence): PRESSED/TRIGGERED map a ButtonAction to true;
# INPUT_CONTROLLERS records the controller index of every query.
INPUT_STUBS = """
PRESSED, TRIGGERED, INPUT_CONTROLLERS, INPUT_FAIL = {}, {}, {}, false
Input = {
 IsActionPressed=function(button, controller)
  if INPUT_FAIL then error("simulated input fault") end
  INPUT_CONTROLLERS[#INPUT_CONTROLLERS+1] = controller
  return PRESSED[button] == true
 end,
 IsActionTriggered=function(button, controller)
  INPUT_CONTROLLERS[#INPUT_CONTROLLERS+1] = controller
  return TRIGGERED[button] == true
 end,
}
Isaac.GetPlayer(0).ControllerIndex = 2
"""

BIT = {name: 1 << i for i, name in enumerate(HUMAN_INPUT_BITS)}


def build_demo():
    lua = build_lua()
    lua.execute(ENTITY_STUBS)
    lua.execute(LIVE_STUBS)
    lua.execute(INPUT_STUBS)
    lua.execute("callbacks.start(); TEST_PLAYER=Isaac.GetPlayer(0); SEND_LIMIT=8192")
    return lua


def demo_snapshots(lua):
    return [decode(line.encode(), DemoSnapshot) for line in records(lua, "snapshot")]


def settle(lua):
    """Tick until the output buffer is empty, so the next snapshot carries every new mask."""
    tick(lua, 10)
    return len(records(lua, "snapshot"))


def masks_after(lua, start):
    tick(lua, 10)
    later = demo_snapshots(lua)[start:]
    assert later
    return [m for s in later for m in s.human_input.masks], sum(
        s.human_input.dropped for s in later
    )


@pytest.fixture
def demo():
    lua = build_demo()
    lua.execute("ROOM_ENTITIES={ make_enemy(1,140,200,10,20), make_enemy(2,0,0,5,5,false) }")
    hello(lua, DEMO)
    assert not lua.globals().CLOSED
    return lua


def test_demo_record_is_advertised_without_approval_and_negotiated(demo):
    ack = decode(records(demo, "hello_ack")[0].encode(), HelloAck)
    assert DEMO_RECORD_CAPABILITY in ack.capabilities
    assert "safe_actions_v1" not in ack.capabilities
    tick(demo, 20)
    snaps = demo_snapshots(demo)
    # The live sample interval (50 ms), not the default 200 ms.
    assert len(snaps) >= 6
    last = snaps[-1]
    assert last.status == "active" and last.entity_frame is not None
    assert last.oracle is not None and len(last.oracle.enemies) == 2
    assert last.oracle.run_seed is None
    assert last.human_input.masks == [] and last.human_input.dropped == 0


@pytest.mark.parametrize(
    "capabilities",
    [
        [DEMO_RECORD_CAPABILITY],
        [DEMO_RECORD_CAPABILITY, "safe_actions_v1"],
        [DEMO_RECORD_CAPABILITY, "death_restart_v1"],
        DEMO + ["safe_actions_v1"],
        DEMO + ["death_restart_v1"],
        DEMO + ["entity_action_v1"],
        DEMO + ["oracle_player_died_v1"],
        list(LIVE_LOOP_CAPABILITIES) + [DEMO_RECORD_CAPABILITY],
        list(LIVE_LOOP_CAPABILITIES) + [DEMO_RECORD_CAPABILITY, "seeded_restart_v1"],
        DEMO + ["seeded_restart_v1"],
    ],
)
def test_demo_record_with_any_other_mode_is_refused(capabilities):
    lua = build_live()  # training approval: actions, restarts and the live loop are advertised
    lua.execute(INPUT_STUBS)
    hello(lua, capabilities)
    assert lua.globals().CLOSED
    assert not records(lua, "hello_ack")


def test_demo_record_with_training_approval_stays_read_only():
    lua = build_live()
    lua.execute(INPUT_STUBS)
    hello(lua, DEMO)
    assert not lua.globals().CLOSED
    tick(lua, 10)
    assert demo_snapshots(lua)[-1].oracle is not None
    lua.execute("IS_DEAD=true; callbacks.game_end(mod,true)")
    tick(lua, 400)
    assert not lua.eval("#COMMANDS")  # no restart is ever dispatched


def test_each_update_records_one_mask_of_player_zero(demo):
    start = settle(demo)
    demo.execute("""
      PRESSED[ButtonAction.ACTION_LEFT], PRESSED[ButtonAction.ACTION_SHOOTUP] = true, true
      callbacks.update()
      PRESSED = { [ButtonAction.ACTION_DOWN]=true, [ButtonAction.ACTION_SHOOTRIGHT]=true,
        [ButtonAction.ACTION_BOMB]=true, [ButtonAction.ACTION_ITEM]=true,
        [ButtonAction.ACTION_PILLCARD]=true }
      TRIGGERED = { [ButtonAction.ACTION_BOMB]=true, [ButtonAction.ACTION_PILLCARD]=true }
      callbacks.update()
      PRESSED, TRIGGERED = {}, { [ButtonAction.ACTION_ITEM]=true }
      callbacks.update()
    """)
    masks, dropped = masks_after(demo, start)
    assert masks == [
        BIT["move_left"] | BIT["shoot_up"],
        BIT["move_down"]
        | BIT["shoot_right"]
        | BIT["bomb"]
        | BIT["active"]
        | BIT["pillcard"]
        | BIT["bomb_triggered"]
        | BIT["pillcard_triggered"],
        BIT["active_triggered"],
    ]
    assert dropped == 0
    assert set(demo.globals().INPUT_CONTROLLERS.values()) == {2}
    assert len(demo.globals().INPUT_CONTROLLERS) == 3 * len(HUMAN_INPUT_BITS)


def test_buffer_keeps_the_newest_sixteen_and_counts_dropped(demo):
    start = settle(demo)
    # Update i holds the movement and shoot-left buttons of i's low five bits: its mask is i.
    demo.execute("""
      local order = { ButtonAction.ACTION_LEFT, ButtonAction.ACTION_RIGHT, ButtonAction.ACTION_UP,
        ButtonAction.ACTION_DOWN, ButtonAction.ACTION_SHOOTLEFT }
      for i=0,19 do
        PRESSED = {}
        for b, button in ipairs(order) do PRESSED[button] = (i >> (b - 1)) & 1 == 1 end
        callbacks.update()
      end
    """)
    masks, dropped = masks_after(demo, start)
    assert len(masks) == MAX_HUMAN_INPUT_MASKS
    assert masks == list(range(4, 20)) and dropped == 4
    # The buffer is cleared once sent.
    tick(demo, 10)
    last = demo_snapshots(demo)[-1].human_input
    assert last.masks == [] and last.dropped == 0


def test_a_new_game_clears_buffered_masks(demo):
    start = settle(demo)
    demo.execute("PRESSED[ButtonAction.ACTION_RIGHT] = true; callbacks.update()")
    demo.execute("callbacks.start(mod, false)")
    masks, dropped = masks_after(demo, start)
    assert masks == [] and dropped == 0


def test_no_masks_outside_a_run(demo):
    settle(demo)
    demo.execute("callbacks.game_end(mod, false)")
    demo.execute("callbacks.exit()")  # a game exit closes the session
    assert demo.globals().CLOSED
    demo.execute("PRESSED[ButtonAction.ACTION_RIGHT] = true; callbacks.update()")
    assert len(demo.globals().INPUT_CONTROLLERS) == 0


def test_input_fault_closes_the_session(demo):
    demo.execute("INPUT_FAIL = true; callbacks.update()")
    assert demo.globals().CLOSED
    assert any("Demo input fault" in line for line in demo.globals().LOGS.values())


def test_real_input_passes_through_the_input_hook(demo):
    for hook in range(3):
        for button in (0, 4, 8, 9, 10):
            assert demo.eval(f"callbacks.input(mod,TEST_PLAYER,{hook},{button})") is None


def test_entity_mode_without_demo_reads_no_input_and_sends_no_human_input():
    lua = build_demo()
    hello(lua, ["entity_observation_v1"])
    lua.execute("PRESSED[ButtonAction.ACTION_RIGHT] = true; callbacks.update()")
    tick(lua, 20)
    lines = records(lua, "snapshot")
    assert lines and all(
        "human_input" not in json.loads(line) and "oracle" not in json.loads(line) for line in lines
    )
    assert len(lua.globals().INPUT_CONTROLLERS) == 0


def test_live_loop_snapshots_are_unchanged():
    lua = build_live()
    lua.execute(INPUT_STUBS)
    hello(lua, LIVE_LOOP_CAPABILITIES)
    lua.execute("callbacks.update()")
    tick(lua, 10)
    assert live_snapshots(lua)[-1].oracle is not None
    assert all("human_input" not in json.loads(line) for line in records(lua, "snapshot"))
    assert len(lua.globals().INPUT_CONTROLLERS) == 0


def test_worst_case_demo_snapshot_fits_the_wire_limit():
    lua = build_demo()
    fill_worst_case(lua)
    lua.execute("""
      for i=1,70 do
        ROOM_ENTITIES[#ROOM_ENTITIES+1]=make_enemy(1000+i,-700.123+i,-600.456,123456.789,999999.999)
      end
    """)
    hello(lua, DEMO)
    tick(lua, 40)
    lua.execute("""
      for _, button in pairs(ButtonAction) do PRESSED[button], TRIGGERED[button] = true, true end
      for i=1,40 do callbacks.update() end
    """)
    tick(lua, 40)
    snaps = demo_snapshots(lua)
    widest = max(snaps, key=lambda s: len(s.human_input.masks))
    assert widest.human_input.masks == [(1 << len(HUMAN_INPUT_BITS)) - 1] * 16
    assert widest.human_input.dropped == 24
    assert widest.oracle is not None and len(widest.oracle.enemies) == 64
    assert len(widest.entity_frame.entities) == 256
    sizes = [len(line.encode()) for line in records(lua, "snapshot")]
    print("worst-case demo snapshot bytes:", max(sizes))
    assert max(sizes) < 131072 - 16384 and not lua.globals().CLOSED
