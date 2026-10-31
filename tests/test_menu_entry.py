"""Behavioral menu evidence/ownership tests; no real window or input."""

import ctypes
from pathlib import Path
from unittest.mock import Mock

import pytest

from isaac_threrisaifuture import menu_entry as menu
from isaac_threrisaifuture.windows_menu import WindowsMenu


class Clock:
    def __init__(self):
        self.value = 0.0

    def monotonic(self):
        return self.value

    def sleep(self, seconds):
        self.value += seconds


@pytest.fixture
def clock(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(menu, "time", clock)
    return clock


def slot_record(slot, available=True):
    text = f"Loading PersistentGameData from Steam Cloud: rep+persistentgamedata{slot}.dat.\n"
    if available:
        text += f"Loading GameState {slot} from SteamCloud!\nGameState Version Loaded: 169\n"
    else:
        text += (
            f"SteamCloud could not find or open rep+gamestate{slot}.dat. No Game State detected.\n"
        )
    return text


class Journal:
    def __init__(self):
        self.text = slot_record(1) + slot_record(2) + slot_record(3)
        self.text += menu.MENU_INITIALIZED + "\n"

    def read(self):
        return self.text


class Keyboard:
    def __init__(self, journal, slot=1, available=True, result="Continue, 2"):
        self.journal, self.slot, self.available = journal, slot, available
        self.result = result
        self.keys = []
        self.stage = 0

    def ready(self):
        return True

    def press(self, key, stop):
        assert not stop()
        self.keys.append(key)
        if key == "Escape":
            self.stage = 2
        elif key in ("Left", "Right"):
            self.slot += 1 if key == "Right" else -1
        elif self.stage < 2:
            self.stage += 1
        elif self.stage == 2:
            self.journal.text += slot_record(self.slot, self.available)
            self.stage = 3
        else:
            self.journal.text += f"RNG Start Seed: TEST SEED [ {self.result}]\n".replace("[ ", "[")


class NewKeyboard(Keyboard):
    def press(self, key, stop):
        if self.stage == 3 and key == "Enter":
            assert not stop()
            self.keys.append(key)
            self.stage = 4  # New Run opens character selection first.
        else:
            super().press(key, stop)


@pytest.mark.parametrize("initial", [1, 2, 3])
def test_continue_uses_fresh_selected_slot_and_stops_keys(clock, initial):
    journal = Journal()
    keyboard = Keyboard(journal, slot=initial)
    events = []
    menu.continue_file2(journal, keyboard, 60, lambda name, data: events.append((name, data)))
    assert keyboard.keys == (
        ["Enter"] * 4
        if initial == 2
        else ["Enter"] * 3 + ["Escape", "Right" if initial == 1 else "Left", "Enter", "Enter"]
    )
    assert events[-1][0] == "menu_continue_verified"
    assert events[-1][1]["slot"] == 2


def test_initial_scans_never_authorize_continue(clock):
    journal = Journal()
    keyboard = Mock(ready=lambda: True)
    with pytest.raises(menu.MenuEntryError, match="metadata not observed"):
        menu.continue_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.press.call_count == 4


def test_intro_skip_precedes_menu_initialization(clock):
    journal = Journal()
    journal.text = menu.INTRO_PLAYING + "\n"
    keyboard = Keyboard(journal, slot=2)
    original = keyboard.press

    def skip_intro(key, stop):
        if menu.MENU_INITIALIZED not in journal.text:
            journal.text += slot_record(1) + slot_record(2) + slot_record(3)
            journal.text += menu.MENU_INITIALIZED + "\n"
        original(key, stop)

    keyboard.press = skip_intro
    events = []
    menu.continue_file2(journal, keyboard, 60, lambda name, _: events.append(name))
    assert keyboard.keys == ["Enter"] * 4
    assert events[-1] == "menu_continue_verified"


@pytest.mark.parametrize("result", ["Continue, 1", "New Run, 2", "Unknown"])
def test_unexpected_run_stops_all_further_keys(clock, result):
    journal = Journal()
    keyboard = Keyboard(journal, slot=2, result=result)
    with pytest.raises(menu.MenuEntryError, match="Unexpected run"):
        menu.continue_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.keys == ["Enter"] * 4


def test_unexpected_start_during_intro_stops_before_another_press(clock):
    journal = Journal()
    keyboard = Mock(ready=lambda: True)
    keyboard.press.side_effect = lambda *_: setattr(
        journal, "text", journal.text + "RNG Start Seed: TEST [Continue, 1]\n"
    )
    with pytest.raises(menu.MenuEntryError, match="Unexpected run"):
        menu.continue_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.press.call_count == 1


def test_no_existing_continue_has_no_new_run_fallback(clock):
    journal = Journal()
    keyboard = Keyboard(journal, slot=2, available=False)
    with pytest.raises(menu.MenuEntryError, match="no New Run fallback"):
        menu.continue_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.keys == ["Enter"] * 3


@pytest.mark.parametrize("initial", [1, 2])
def test_continue_or_new_continues_an_existing_run(clock, initial):
    journal = Journal()
    keyboard = Keyboard(journal, slot=initial)
    events = []
    menu.continue_or_new_run_file2(journal, keyboard, 60, lambda n, d: events.append((n, d)))
    assert ("menu_entry_resolved", {"slot": 2, "mode": "continue"}) in events
    assert events[-1][0] == "menu_continue_verified"


@pytest.mark.parametrize("initial", [1, 2, 3])
def test_continue_or_new_starts_a_new_run_only_on_verified_absence(clock, initial):
    journal = Journal()
    keyboard = NewKeyboard(journal, slot=initial, available=False, result="New, 2")
    events = []
    menu.continue_or_new_run_file2(journal, keyboard, 60, lambda n, d: events.append((n, d)))
    assert ("menu_entry_resolved", {"slot": 2, "mode": "new-run"}) in events
    assert events[-1][0] == "menu_new_run_verified"
    assert len(keyboard.keys) == (5 if initial == 2 else 8)


def test_continue_or_new_stops_without_game_state_evidence(clock):
    journal = Journal()
    keyboard = Keyboard(journal, slot=2)
    original = keyboard.press

    def silent(key, stop):
        before = journal.text
        original(key, stop)
        if keyboard.stage == 3:
            journal.text = before + slot_record(2).split("Loading GameState")[0]

    keyboard.press = silent
    with pytest.raises(menu.MenuEntryError, match="neither confirmed nor verified absent"):
        menu.continue_or_new_run_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.keys == ["Enter"] * 3


def test_continue_or_new_stops_on_contradictory_game_state_evidence(clock):
    journal = Journal()
    keyboard = Keyboard(journal, slot=2)
    original = keyboard.press

    def contradictory(key, stop):
        original(key, stop)
        if keyboard.stage == 3:
            journal.text += slot_record(2, available=False)

    keyboard.press = contradictory
    with pytest.raises(menu.MenuEntryError, match="Contradictory"):
        menu.continue_or_new_run_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.keys == ["Enter"] * 3


def test_failed_target_selection_does_not_confirm_continue(clock):
    journal = Journal()
    keyboard = Keyboard(journal)
    original = keyboard.press

    def broken(key, stop):
        if key == "Right":
            keyboard.keys.append(key)  # A game can ignore a successfully sent key.
        else:
            original(key, stop)

    keyboard.press = broken
    with pytest.raises(menu.MenuEntryError, match="selection was not confirmed"):
        menu.continue_file2(journal, keyboard, 60, lambda *_: None)
    assert len(keyboard.keys) == 6


def test_menu_wait_is_bounded(clock):
    with pytest.raises(menu.MenuEntryError, match="deadline"):
        menu.continue_file2(Mock(read=lambda: ""), Mock(), 1, lambda *_: None)
    assert clock.value < 1.2


def test_stale_log_is_not_evidence_and_new_log_is_bounded(tmp_path):
    path = tmp_path / "log.txt"
    path.write_text("RNG Start Seed: OLD [Continue, 2]\n")
    journal = menu.FreshGameLog(path)
    assert journal.read() == ""
    path.write_text(menu.MENU_INITIALIZED + "\n")
    import os

    os.utime(path, ns=(journal.baseline + 1_000_000, journal.baseline + 1_000_000))
    assert journal.read() == menu.MENU_INITIALIZED + "\n"
    path.write_bytes(b"x" * (menu.MAX_LOG_BYTES + 1))
    with pytest.raises(menu.MenuEntryError, match="2 MiB"):
        journal.read()


def test_log_rotation_during_input_stops(tmp_path):
    path = tmp_path / "log.txt"
    journal = menu.FreshGameLog(path)
    path.write_text("Fresh startup\n")
    assert journal.read()
    path.write_text("Replacement\n")
    with pytest.raises(menu.MenuEntryError, match="replaced"):
        journal.read()


def test_hold_releases_on_down_failure(clock):
    calls = []

    def send(up):
        calls.append(up)
        if not up:
            raise OSError("down failed")

    with pytest.raises(OSError, match="down failed"):
        menu.held_key(send, lambda: True, lambda: False)
    assert calls == [False, True]


def test_focus_refusal_sends_nothing(clock):
    send = Mock()
    with pytest.raises(menu.MenuEntryError, match="no input"):
        menu.held_key(send, lambda: False, lambda: False)
    send.assert_not_called()


def test_lost_focus_releases_key(clock):
    send = Mock()
    focus = Mock(side_effect=[True, False])
    with pytest.raises(menu.MenuEntryError, match="lost focus"):
        menu.held_key(send, focus, lambda: False)
    assert send.call_args_list == [((False,),), ((True,),)]


def test_run_marker_during_hold_releases_immediately(clock):
    send = Mock()
    menu.held_key(send, lambda: True, Mock(side_effect=[False, True]))
    assert send.call_args_list == [((False,),), ((True,),)]
    assert clock.value == 0


def test_windows_foreground_refusal_sends_no_menu_key(monkeypatch, clock):
    adapter = WindowsMenu.__new__(WindowsMenu)
    adapter.window = (123, 456)
    adapter.user = Mock()
    adapter.user.GetForegroundWindow.return_value = 789
    adapter.user.GetWindowThreadProcessId.side_effect = lambda _, ptr: setattr(
        ptr._obj, "value", 456
    )
    monkeypatch.setattr(adapter, "ready", lambda: True)
    from isaac_threrisaifuture import windows_menu

    monkeypatch.setattr(windows_menu, "time", clock)
    adapter._identity = Mock(return_value=(Path("C:/apps/agent.exe"), 1.0))
    with pytest.raises(menu.MenuEntryError, match=r"foreground: agent\.exe\); no input"):
        adapter.press("Enter", lambda: False)
    # Only Alt taps (focus unlock) were sent between the attempts; never the menu key.
    scans = [call.args[1]._obj.value.key.scan for call in adapter.user.SendInput.call_args_list]
    assert scans == [windows_menu.ALT_SCAN] * 2 * (windows_menu.FOCUS_ATTEMPTS - 1)
    assert adapter.user.SetForegroundWindow.call_count == windows_menu.FOCUS_ATTEMPTS


def test_windows_focus_is_taken_after_an_alt_tap(monkeypatch, clock):
    adapter = WindowsMenu.__new__(WindowsMenu)
    adapter.window = (123, 456)
    adapter.user = Mock()
    focused = {"hwnd": 789}
    adapter.user.GetForegroundWindow.side_effect = lambda: focused["hwnd"]
    adapter.user.GetWindowThreadProcessId.side_effect = lambda _, ptr: setattr(
        ptr._obj, "value", 456
    )
    sent: list[tuple[int, int]] = []

    def send_input(_count, ptr, _size):
        key = ptr._obj.value.key
        sent.append((key.scan, key.flags))
        return 1

    adapter.user.SendInput.side_effect = send_input
    # The second SetForegroundWindow (after the Alt tap) succeeds.
    adapter.user.SetForegroundWindow.side_effect = lambda hwnd: focused.update(
        hwnd=hwnd if sent else 789
    )
    monkeypatch.setattr(adapter, "ready", lambda: True)
    from isaac_threrisaifuture import windows_menu

    monkeypatch.setattr(windows_menu, "time", clock)
    monkeypatch.setattr(menu, "time", clock)
    adapter.press("Escape", lambda: False)
    assert sent[:2] == [(windows_menu.ALT_SCAN, 8), (windows_menu.ALT_SCAN, 10)]
    assert sent[2:] == [(0x01, 8), (0x01, 10)]  # then the Esc press and release


@pytest.mark.parametrize("fault", ["old", "path", "multiple", "changed"])
def test_window_identity_refuses_unowned_process(tmp_path, fault):
    adapter = WindowsMenu.__new__(WindowsMenu)
    adapter.expected = (tmp_path / "isaac-ng.exe").resolve()
    adapter.launched_at = 100.0
    adapter.window = (99, 77) if fault == "changed" else None
    adapter.user = Mock()
    adapter.callback_type = lambda callback: callback
    adapter.user.IsWindowVisible.return_value = True
    adapter.user.GetWindowThreadProcessId.side_effect = lambda _, ptr: setattr(
        ptr._obj, "value", 10
    )
    adapter._identity = Mock(
        return_value=(
            tmp_path / "other/isaac-ng.exe" if fault == "path" else adapter.expected,
            99.0 if fault == "old" else 101.0,
        )
    )

    def enumerate_windows(callback, _):
        callback(123, 0)
        if fault == "multiple":
            callback(456, 0)
        return True

    adapter.user.EnumWindows.side_effect = enumerate_windows
    with pytest.raises(menu.MenuEntryError):
        adapter.ready()
    adapter.user.SendInput.assert_not_called()


def test_windows_input_struct_matches_native_64bit_layout():
    from isaac_threrisaifuture.windows_menu import _Input

    assert ctypes.sizeof(_Input) == 40


@pytest.mark.parametrize("initial", [1, 2, 3])
def test_explicit_new_run_after_absence_uses_bounded_character_confirmation(clock, initial):
    journal = Journal()
    keyboard = NewKeyboard(journal, slot=initial, available=False, result="New, 2")
    events = []
    menu.new_run_file2(journal, keyboard, 60, lambda name, data: events.append((name, data)))
    assert len(keyboard.keys) == (5 if initial == 2 else 8)
    assert events[-1][0] == "menu_new_run_verified"
    assert events[-1][1]["mode"] == "New"


def test_new_run_protects_existing_continue(clock):
    journal = Journal()
    keyboard = NewKeyboard(journal, slot=2, available=True)
    with pytest.raises(menu.MenuEntryError, match="New Run refused"):
        menu.new_run_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.keys == ["Enter"] * 3


class ReplacementKeyboard(NewKeyboard):
    def press(self, key, stop):
        if key == "Up" and self.stage == 3:
            assert not stop()
            self.keys.append(key)
            return
        super().press(key, stop)


@pytest.mark.parametrize("initial", [1, 2, 3])
def test_authorized_replacement_verifies_slot_new_mode_and_bounded_keys(clock, initial):
    journal = Journal()
    keyboard = ReplacementKeyboard(journal, slot=initial, result="New, 2")
    events = []
    menu.enter_file2(
        journal,
        keyboard,
        60,
        lambda n, d: events.append((n, d)),
        mode="new-run",
        replace_existing=True,
    )
    assert keyboard.keys.count("Up") == 1
    assert len(keyboard.keys) <= 10
    assert any(n == "menu_replace_explicit" for n, _ in events)
    assert events[-1][0] == "menu_new_run_verified"


@pytest.mark.parametrize("result", ["Continue, 2", "New, 1", "Unknown"])
def test_replacement_wrong_native_start_stops_all_keys(clock, result):
    journal = Journal()
    keyboard = ReplacementKeyboard(journal, slot=2, result=result)
    with pytest.raises(menu.MenuEntryError, match="Unexpected run"):
        menu.enter_file2(
            journal, keyboard, 60, lambda *_: None, mode="new-run", replace_existing=True
        )
    assert len(keyboard.keys) == 6


def test_replacement_requires_known_existing_file2(clock):
    journal = Journal()
    keyboard = ReplacementKeyboard(journal, slot=2, available=False)
    with pytest.raises(menu.MenuEntryError, match="verified existing"):
        menu.enter_file2(
            journal, keyboard, 60, lambda *_: None, mode="new-run", replace_existing=True
        )
    assert "Up" not in keyboard.keys


@pytest.mark.parametrize("intent", [True, "yes", 1])
def test_continue_cannot_accept_replacement_intent(clock, intent):
    keyboard = Mock()
    with pytest.raises(menu.MenuEntryError, match="Explicit replacement"):
        menu.enter_file2(Journal(), keyboard, 60, lambda *_: None, replace_existing=intent)
    keyboard.press.assert_not_called()


def test_new_run_requires_positive_absence_not_missing_version_alone(clock):
    journal = Journal()
    keyboard = NewKeyboard(journal, slot=2, available=False)
    original = keyboard.press

    def unknown_state(key, stop):
        original(key, stop)
        journal.text = (
            "\n".join(
                line for line in journal.text.splitlines() if "No Game State detected" not in line
            )
            + "\n"
        )

    keyboard.press = unknown_state
    with pytest.raises(menu.MenuEntryError, match="New Run refused"):
        menu.new_run_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.keys == ["Enter"] * 3


@pytest.mark.parametrize("result", ["New, 1", "Continue, 2", "Unknown"])
def test_new_run_rejects_wrong_start_and_stops_keys(clock, result):
    journal = Journal()
    keyboard = NewKeyboard(journal, slot=2, available=False, result=result)
    with pytest.raises(menu.MenuEntryError, match="Unexpected run"):
        menu.new_run_file2(journal, keyboard, 60, lambda *_: None)
    assert keyboard.keys == ["Enter"] * 5
