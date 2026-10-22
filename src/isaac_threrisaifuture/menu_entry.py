"""Bounded local menu input and native-log evidence; no screen capture."""

import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Literal, Protocol

MAX_LOG_BYTES = 2 * 1024 * 1024
MENU_INITIALIZED = "Menu Online Awards Init"
INTRO_PLAYING = "playing cutscene 1 (Intro)."
SLOT_LOAD = re.compile(r"Loading PersistentGameData[^\r\n]*persistentgamedata([123])\.dat")
RUN_START = re.compile(r"RNG Start Seed:[^\r\n]*\[([^,\]\r\n]+),\s*([123])\]")


class MenuEntryError(ValueError):
    """Menu ownership, evidence or bounded transition failed."""


class MenuInput(Protocol):
    def ready(self) -> bool: ...
    def press(self, key: str, stop: Callable[[], bool]) -> None: ...


class FreshGameLog:
    """Read only a newly written launch log, with a strict size bound."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.baseline = path.stat().st_mtime_ns if path.exists() else None
        self.previous = ""
        self.activated = False

    def read(self) -> str:
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return ""
        if not self.activated and stat.st_mtime_ns == self.baseline:
            return ""
        if stat.st_size > MAX_LOG_BYTES:
            raise MenuEntryError("Native menu log exceeds 2 MiB")
        with self.path.open("rb") as stream:
            data = stream.read(MAX_LOG_BYTES + 1)
        if len(data) > MAX_LOG_BYTES:
            raise MenuEntryError("Native menu log exceeds 2 MiB")
        text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")
        if self.previous and not text.startswith(self.previous):
            raise MenuEntryError("Native log was replaced during menu entry")
        self.previous, self.activated = text, True
        return text


def held_key(
    send: Callable[[bool], None],
    foreground: Callable[[], bool],
    stop: Callable[[], bool],
) -> None:
    """Always release a 300ms scan-code press, including cancellation/faults."""
    if stop():
        return
    if not foreground():
        raise MenuEntryError("Isaac is not foreground; no input sent")
    try:
        send(False)
        until = time.monotonic() + 0.3
        while time.monotonic() < until:
            if stop():
                break
            if not foreground():
                raise MenuEntryError("Isaac lost focus during menu input")
            time.sleep(0.02)
    finally:
        send(True)


def enter_file2(
    journal: FreshGameLog,
    keyboard: MenuInput,
    deadline: float,
    record: Callable[[str, object], None],
    *,
    mode: Literal["continue", "new-run"] = "continue",
    replace_existing: bool = False,
) -> None:
    """Enter one declared mode using fresh selected-slot evidence."""
    if mode not in ("continue", "new-run"):
        raise MenuEntryError("Unknown automatic menu entry mode")
    if type(replace_existing) is not bool or (replace_existing and mode != "new-run"):
        raise MenuEntryError("Explicit replacement requires New Run mode and boolean intent")
    key_limit = 10 if replace_existing else 8
    cap = min(deadline, time.monotonic() + 60)
    keys = 0
    entry_issued = False

    def read() -> str:
        if time.monotonic() >= cap:
            raise MenuEntryError("Menu entry deadline expired")
        return journal.read()

    def started() -> bool:
        text = read()
        if "RNG Start Seed:" in text:
            return True  # Stop even for unrecognized mode/slot syntax.
        return False

    def press(key: str) -> None:
        nonlocal keys
        if started():
            raise MenuEntryError("Run started before the requested Continue; input stopped")
        if keys >= key_limit:
            raise MenuEntryError("Menu key budget exhausted")
        keys += 1
        record("menu_key", {"key": key, "count": keys})
        keyboard.press(key, started)

    def settle(seconds: float) -> str:
        until = min(cap, time.monotonic() + seconds)
        while time.monotonic() < until:
            text = read()
            if "RNG Start Seed:" in text:
                if not entry_issued:
                    raise MenuEntryError("Unexpected run start; menu input stopped")
                return text
            time.sleep(0.05)
        return read()

    intro_skipped = False
    while True:
        text = read()
        if "RNG Start Seed:" in text:
            raise MenuEntryError("Run already started; refusing keyboard takeover")
        if MENU_INITIALIZED in text and keyboard.ready():
            break
        if not intro_skipped and INTRO_PLAYING in text and keyboard.ready():
            press("Enter")
            intro_skipped = True
        time.sleep(0.1)
    # Initial startup scans all slots before this marker; never accept those scans.
    offset = text.index(MENU_INITIALIZED) + len(MENU_INITIALIZED)
    settle(1.5)

    def selected(text: str, begin: int) -> int | None:
        slots = {int(match[1]) for match in SLOT_LOAD.finditer(text[begin:])}
        if len(slots) > 1:
            raise MenuEntryError("Ambiguous selected-slot metadata; input stopped")
        return next(iter(slots)) if slots else None

    slot = selected(read(), offset)
    for _ in range(4 - keys):
        if slot is not None:
            break
        press("Enter")  # Intro, title, then selected save's game menu.
        slot = selected(settle(1.5), offset)
    if slot is None:
        raise MenuEntryError("Selected-slot metadata not observed within startup key budget")

    if slot != 2:
        press("Escape")
        settle(1)
        press("Right" if slot == 1 else "Left")
        settle(0.75)
        offset = len(read())
        press("Enter")
        slot = selected(settle(1.5), offset)
        if slot != 2:
            raise MenuEntryError("File2 selection was not confirmed; Continue not sent")

    text = read()[offset:]
    available = re.search(r"Loading GameState 2[^\r\n]*\n[^\r\n]*GameState Version Loaded:", text)
    missing = re.search(r"rep\+gamestate2\.dat\.[^\r\n]*No Game State detected\.", text)
    if mode == "continue" and not available:
        raise MenuEntryError("Existing file2 game state not confirmed; no New Run fallback")
    if mode == "new-run" and not replace_existing and (available or not missing):
        raise MenuEntryError("New Run refused: existing Continue or unverified file2 absence")
    if replace_existing and (not available or missing):
        raise MenuEntryError("Replacement requires verified existing file2 Continue")
    record("menu_slot_verified", {"slot": 2, "source": "fresh_selected_metadata"})
    if replace_existing:
        record("menu_replace_explicit", {"slot": 2, "existing_continue": True})
        press("Up")
        settle(0.25)
    entry_issued = True
    press("Enter")
    if mode == "new-run":
        text = settle(1.5)
        if "RNG Start Seed:" not in text:
            press("Enter")  # Confirm the remembered character; bridge must verify Isaac.
    while True:
        text = settle(0.1)
        if "RNG Start Seed:" in text:
            match = RUN_START.search(text)
            expected = "Continue" if mode == "continue" else "New"
            if match is None or match[1].strip() != expected or match[2] != "2":
                raise MenuEntryError("Unexpected run mode/slot; all menu input stopped")
            event = "menu_continue_verified" if mode == "continue" else "menu_new_run_verified"
            record(event, {"slot": 2, "mode": expected, "keys": keys})
            return


def continue_file2(
    journal: FreshGameLog,
    keyboard: MenuInput,
    deadline: float,
    record: Callable[[str, object], None],
) -> None:
    enter_file2(journal, keyboard, deadline, record, mode="continue")


def new_run_file2(
    journal: FreshGameLog,
    keyboard: MenuInput,
    deadline: float,
    record: Callable[[str, object], None],
) -> None:
    enter_file2(journal, keyboard, deadline, record, mode="new-run")
