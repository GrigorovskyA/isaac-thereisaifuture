"""OFFLINE production-Lua tests for bounded step-evidence trace records. Isaac is simulated.

These records are raw bridge-side facts; no test asserts engine consumption or readiness.
"""

import pytest
import test_lua_observer
from test_lua_actions import input_value, send
from test_lua_callback_trace import FAILING_DEBUG_LOGGER, events, field, lines, traced
from test_lua_observer import ROOT

EVIDENCE = {"hold_update", "release_update", "release_input"}


def facts(lua):
    return [x for x in lines(lua) if field(x, "event") in EVIDENCE]


def test_disabled_mode_emits_nothing_and_changes_no_inputs():
    lua = traced(trace=False)
    send(lua)
    lua.execute("callbacks.update(); NOW=NOW+250")
    assert input_value(lua) is None
    lua.execute("callbacks.update()")
    assert lines(lua) == []


def test_acceptance_records_hold_endpoint_and_deadline():
    lua = traced()
    send(lua, frames=7)
    line = lines(lua)[0]
    now = int(lua.globals().NOW)
    assert field(line, "event") == "action_accepted" and field(line, "frames") == "7"
    assert field(line, "until") == "27" and field(line, "deadline_ms") == str(now + 250)
    assert field(line, "seq") == "1" and field(line, "frame") == "20"


@pytest.mark.parametrize(
    "setup",
    [
        lambda lua: send(lua, sequence=2, frame_id=19),
        lambda lua: send(lua, kind="heartbeat", move="none", shoot="none", frames=0),
        lambda lua: send(lua, sequence=1, session_id="b" * 32),
    ],
)
def test_rejected_or_heartbeat_commands_start_nothing(setup):
    lua = traced()
    setup(lua)
    lua.execute("callbacks.update()")
    assert lines(lua) == []


def test_hold_update_once_per_frame_without_consumption_claims():
    lua = traced()
    send(lua)
    lua.execute("callbacks.update(); callbacks.update()")
    lua.execute("FRAME=21; callbacks.update(); callbacks.update()")
    seen = facts(lua)
    assert [field(x, "event") for x in seen] == ["hold_update"] * 2
    assert [field(x, "left") for x in seen] == ["15", "14"]
    assert [field(x, "upd_since") for x in seen] == ["1", "3"]
    assert all(field(x, "hold_seq") == "1" for x in seen)
    assert not any("consum" in x or "ready" in x for x in lines(lua))


def test_release_keeps_original_hold_identity_and_expiry_conditions():
    lua = traced()
    send(lua)
    send(lua, sequence=2, kind="heartbeat", move="none", shoot="none", frames=0)
    lua.execute("NOW=NOW+250")
    assert input_value(lua) is None
    release = next(x for x in lines(lua) if field(x, "event") == "release")
    assert field(release, "hold_seq") == "1" and field(release, "seq") == "2"
    assert field(release, "reason") == "expiry"
    assert (field(release, "frame_due"), field(release, "wall_due")) == ("0", "1")
    assert field(release, "left") == "15"


def test_frame_expiry_is_distinguished_from_wall_expiry():
    lua = traced()
    send(lua, frames=3)
    lua.execute("FRAME=23")
    assert input_value(lua) is None
    release = next(x for x in lines(lua) if field(x, "event") == "release")
    assert (field(release, "frame_due"), field(release, "wall_due")) == ("1", "0")


def test_explicit_release_before_endpoint_and_pending_correlation():
    lua = traced()
    send(lua)
    send(lua, sequence=2, kind="release", move="none", shoot="none", frames=0)
    release = next(x for x in lines(lua) if field(x, "event") == "release")
    assert field(release, "reason") == "explicit_release" and field(release, "left") == "15"
    assert input_value(lua, 1, 2) is None
    assert input_value(lua, 1, 2) is None
    lua.execute("callbacks.update(); callbacks.update(); FRAME=21; callbacks.update()")
    names = [field(x, "event") for x in facts(lua)]
    assert names == ["release_input", "release_update"]
    assert all(field(x, "hold_seq") == "1" for x in facts(lua))
    assert "override=nil" in facts(lua)[0] and "hold=absent" in facts(lua)[1]
    assert "neutral" not in " ".join(lines(lua))


def test_non_movement_and_foreign_input_never_confirm_release():
    lua = traced()
    send(lua)
    lua.execute("NOW=NOW+250; callbacks.update()")
    assert input_value(lua, 8) is None
    assert lua.eval("callbacks.input(mod,nil,2,1)") is None
    assert lua.eval("callbacks.input(mod,{ToPlayer=function() return nil end},2,1)") is None
    assert [x for x in facts(lua) if field(x, "event") == "release_input"] == []


def test_new_action_evicts_pending_release_without_false_confirmation():
    lua = traced()
    send(lua)
    lua.execute("NOW=NOW+250; callbacks.update()")
    send(lua, sequence=2)
    assert input_value(lua) == 1
    lua.execute("callbacks.update()")
    seen = facts(lua)
    assert [field(x, "event") for x in seen] == ["hold_update"]
    assert field(seen[0], "hold_seq") == "2"


def test_replacing_a_live_hold_keeps_no_pending_release():
    lua = traced()
    send(lua)
    send(lua, sequence=2, move="left")
    assert input_value(lua, 0) == 1
    lua.execute("callbacks.update()")
    assert [field(x, "event") for x in facts(lua)] == ["hold_update"]


@pytest.mark.parametrize(
    "event",
    [
        "callbacks.room()",
        "callbacks.level()",
        "callbacks.start(mod,false)",
        "callbacks.game_end(mod,false)",
    ],
)
def test_context_change_discards_pending_release(event):
    lua = traced()
    send(lua)
    lua.execute("NOW=NOW+250; callbacks.update()")
    lua.execute(event)
    assert input_value(lua) is None
    lua.execute("callbacks.update()")
    assert facts(lua) == []


def test_disconnect_clears_state_and_reconnect_cannot_revive_it():
    lua = traced()
    send(lua)
    lua.execute("PEER_CLOSED=true; callbacks.render()")
    total = len(lines(lua))
    lua.execute("callbacks.update(); callbacks.room()")
    assert input_value(lua) is None
    assert len(lines(lua)) == total and facts(lua) == []


def test_budget_stop_is_final_and_evidence_hooks_stay_silent_after_it():
    lua = traced()
    send(lua)
    for _ in range(600):
        input_value(lua)
    seen = lines(lua)
    assert len(seen) == 512 and all(len(x) <= 300 for x in seen)
    assert events(lua).count("stop") == 1
    lua.execute("callbacks.update(); NOW=NOW+250; callbacks.update()")
    assert input_value(lua) is None
    lua.execute("callbacks.update(); callbacks.room()")
    assert len(lines(lua)) == 512 and facts(lua) == []


def test_overlong_line_stops_the_trace_instead_of_truncating(tmp_path, monkeypatch):
    source = (ROOT / "mod/observer/main.lua").read_text(encoding="utf-8")
    patched = source.replace("TRACE_LINE_MAX = 512, 10000, 300", "TRACE_LINE_MAX = 512, 10000, 150")
    assert patched != source
    (tmp_path / "mod/observer").mkdir(parents=True)
    (tmp_path / "mod/observer/main.lua").write_text(patched, encoding="utf-8")
    monkeypatch.setattr(test_lua_observer, "ROOT", tmp_path)
    lua = traced()
    send(lua)  # the acceptance record exceeds the patched 150-byte limit
    seen = lines(lua)
    assert [field(x, "event") for x in seen] == ["stop"]
    assert field(seen[0], "reason") == "line_limit" and len(seen[0]) <= 150
    assert input_value(lua, 1, 2) == 1
    lua.execute("callbacks.update(); NOW=NOW+250")
    assert input_value(lua) is None
    assert len(lines(lua)) == 1


@pytest.mark.parametrize(
    "failing", ["action_accepted", "release", "release_update", "release_input", "hold_update"]
)
def test_logger_failure_on_evidence_hooks_changes_no_behavior(failing):
    lua = traced()
    lua.execute(
        f"ATTEMPTS=0; print=function(m) if m:find('event={failing} ',1,true) then"
        " ATTEMPTS=ATTEMPTS+1; error('log fail') end"
        " LOGS[#LOGS+1]=m end"
    )
    send(lua)
    lua.execute("callbacks.update()")
    assert input_value(lua, 1, 2) == 1
    send(lua, sequence=2, kind="release", move="none", shoot="none", frames=0)
    assert input_value(lua, 1, 2) is None
    lua.execute("callbacks.update()")
    assert lua.globals().ATTEMPTS == 1
    total = len(lines(lua))
    lua.execute("callbacks.update(); callbacks.room()")
    assert len(lines(lua)) == total and not lua.globals().CLOSED
    assert input_value(lua) is None
    lua.execute("callbacks.exit()")
    assert lua.globals().CLOSED


def test_debug_string_failure_during_evidence_stops_further_attempts():
    lua = traced()
    lua.execute(FAILING_DEBUG_LOGGER)
    send(lua)
    lua.execute("callbacks.update(); NOW=NOW+250; callbacks.update()")
    assert lua.globals().ATTEMPTS == 1 and lines(lua) == []
    assert input_value(lua) is None


def test_reentrant_logger_cannot_recurse_or_change_behavior():
    lua = traced()
    lua.execute(
        "REENTER=0; print=function(m) if m:find('Future Trace',1,true) then REENTER=REENTER+1;"
        " callbacks.update() end LOGS[#LOGS+1]=m end"
    )
    send(lua)
    lua.execute("callbacks.update()")
    assert input_value(lua, 1, 2) == 1
    lua.execute("NOW=NOW+250")
    assert input_value(lua, 1, 2) is None
    assert lua.globals().REENTER < 50
    lua.execute("callbacks.room()")
    assert input_value(lua) is None


def test_frame_read_reentry_cannot_emit_old_hold_in_new_room():
    lua = traced()
    send(lua)
    lua.execute(
        "READS=0; BASE_GAME=Game; Game=function() local g=BASE_GAME();"
        " g.GetFrameCount=function() READS=READS+1;"
        " if READS==4 then callbacks.room() end; return FRAME end; return g end;"
        " callbacks.update()"
    )
    assert not any(field(x, "event") == "hold_update" for x in facts(lua))
    total = len(lines(lua))
    lua.execute("callbacks.update()")
    assert len(lines(lua)) == total
    assert input_value(lua) is None and not lua.globals().CLOSED


def test_pointer_read_reentry_cannot_confirm_release_in_new_room():
    lua = traced()
    send(lua)
    send(lua, sequence=2, kind="release", move="none", shoot="none", frames=0)
    lua.execute(
        "BASE_HASH=GetPtrHash; TRIGGER=true; GetPtrHash=function(e)"
        " if TRIGGER then TRIGGER=false; callbacks.room() end; return BASE_HASH(e) end"
    )
    assert input_value(lua) is None
    assert not any(field(x, "event") == "release_input" for x in facts(lua))


def test_reentrant_logger_ends_window_instead_of_silently_continuing():
    lua = traced()
    lua.execute(
        "print=function(m) if m:find('event=action_accepted',1,true) then"
        " callbacks.update() end; LOGS[#LOGS+1]=m end"
    )
    send(lua)
    total = len(lines(lua))
    lua.execute("callbacks.update()")
    assert len(lines(lua)) == total
    assert input_value(lua, 1, 2) == 1


def test_reentry_starting_trace_cannot_close_peer_via_cleared_hold():
    lua = traced()
    lua.execute(
        "BASE_TIME=Isaac.GetTime; TRIGGER=false;"
        "print=function(m) if m:find('Action accepted',1,true) then TRIGGER=true end;"
        " LOGS[#LOGS+1]=m end; Isaac.GetTime=function()"
        " if TRIGGER then TRIGGER=false; callbacks.room() end; return BASE_TIME() end"
    )
    send(lua)
    assert not lua.globals().CLOSED
    assert input_value(lua) is None


def test_regressing_frame_never_counts_an_already_observed_hold_frame_again():
    lua = traced()
    send(lua)
    lua.execute("callbacks.update(); FRAME=21; callbacks.update(); FRAME=20; callbacks.update()")
    seen = [x for x in facts(lua) if field(x, "event") == "hold_update"]
    assert [field(x, "frame") for x in seen] == ["20", "21"]


def test_pending_release_supersession_is_explicit_and_correlated():
    lua = traced()
    send(lua)
    send(lua, sequence=2, kind="release", move="none", shoot="none", frames=0)
    send(lua, sequence=3)
    superseded = [x for x in lines(lua) if field(x, "event") == "release_superseded"]
    assert len(superseded) == 1
    assert field(superseded[0], "hold_seq") == "1" and field(superseded[0], "by_seq") == "3"


def test_pending_release_does_not_retain_an_input_entity_wrapper():
    lua = traced()
    send(lua)
    send(lua, sequence=2, kind="release", move="none", shoot="none", frames=0)
    lua.execute(
        "local e={ToPlayer=function() return Isaac.GetPlayer(0) end};"
        " WEAK=setmetatable({e},{__mode='v'}); callbacks.input(mod,e,2,1);"
        " e=nil; collectgarbage('collect')"
    )
    assert lua.globals().WEAK[1] is None
    assert any(field(x, "event") == "release_input" for x in facts(lua))


def test_unknown_input_hook_is_not_release_confirmation():
    lua = traced()
    send(lua)
    send(lua, sequence=2, kind="release", move="none", shoot="none", frames=0)
    assert input_value(lua, 1, 999) is None
    assert not any(field(x, "event") == "release_input" for x in facts(lua))
