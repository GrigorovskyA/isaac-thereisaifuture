"""Native Windows menu-only scan codes with verified process/window ownership."""

import ctypes
import time
from collections.abc import Callable
from ctypes import wintypes
from pathlib import Path
from typing import Any

from .menu_entry import MenuEntryError, held_key


class _Mouse(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("data", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("extra", ctypes.c_size_t),
    ]


class _Key(ctypes.Structure):
    _fields_ = [
        ("vk", wintypes.WORD),
        ("scan", wintypes.WORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("extra", ctypes.c_size_t),
    ]


class _Union(ctypes.Union):
    _fields_ = [("key", _Key), ("mouse", _Mouse)]


class _Input(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("value", _Union)]


class WindowsMenu:
    def __init__(self, directory: Path, launched_at: float) -> None:
        self.expected = (directory / "isaac-ng.exe").resolve()
        self.launched_at = launched_at
        self.window: tuple[int, int] | None = None
        self.user: Any = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel: Any = ctypes.WinDLL("kernel32", use_last_error=True)
        self.callback_type: Any = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        definitions: tuple[tuple[Any, list[Any], Any], ...] = (
            (self.user.EnumWindows, [self.callback_type, wintypes.LPARAM], wintypes.BOOL),
            (self.user.IsWindowVisible, [wintypes.HWND], wintypes.BOOL),
            (
                self.user.GetWindowThreadProcessId,
                [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)],
                wintypes.DWORD,
            ),
            (self.user.GetForegroundWindow, [], wintypes.HWND),
            (self.user.SetForegroundWindow, [wintypes.HWND], wintypes.BOOL),
            (self.user.ShowWindow, [wintypes.HWND, ctypes.c_int], wintypes.BOOL),
            (
                self.user.SendInput,
                [wintypes.UINT, ctypes.POINTER(_Input), ctypes.c_int],
                wintypes.UINT,
            ),
            (
                self.kernel.OpenProcess,
                [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD],
                wintypes.HANDLE,
            ),
            (self.kernel.CloseHandle, [wintypes.HANDLE], wintypes.BOOL),
            (
                self.kernel.QueryFullProcessImageNameW,
                [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)],
                wintypes.BOOL,
            ),
            (
                self.kernel.GetProcessTimes,
                [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4,
                wintypes.BOOL,
            ),
        )
        for function, args, result in definitions:
            function.argtypes, function.restype = args, result

    def _identity(self, pid: int) -> tuple[Path, float] | None:
        handle = self.kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            buffer = ctypes.create_unicode_buffer(32768)
            size = wintypes.DWORD(len(buffer))
            if not self.kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
                return None
            times = [wintypes.FILETIME() for _ in range(4)]
            if not self.kernel.GetProcessTimes(handle, *(ctypes.byref(item) for item in times)):
                return None
            created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
            return Path(buffer.value).resolve(), created / 10_000_000 - 11644473600
        finally:
            self.kernel.CloseHandle(handle)

    def ready(self) -> bool:
        found: list[tuple[int, int]] = []
        invalid: list[str] = []

        def visit(hwnd: int, _: int) -> bool:
            if self.user.IsWindowVisible(hwnd):
                pid = wintypes.DWORD()
                self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                identity = self._identity(pid.value)
                if identity is not None and identity[0].name.casefold() == "isaac-ng.exe":
                    if identity[0] != self.expected or identity[1] < self.launched_at:
                        invalid.append("Unexpected executable or older game process")
                    found.append((hwnd, pid.value))
            return True

        if not self.user.EnumWindows(self.callback_type(visit), 0):
            raise MenuEntryError("Window enumeration failed")
        if invalid or len(found) > 1:
            raise MenuEntryError("Expected one newly launched Isaac window at the approved path")
        if not found:
            if self.window is not None:
                raise MenuEntryError("Owned Isaac window disappeared")
            return False
        if self.window is not None and self.window != found[0]:
            raise MenuEntryError("Owned Isaac window/PID changed")
        self.window = found[0]
        return True

    def press(self, key: str, stop: Callable[[], bool]) -> None:
        codes = {
            "Enter": (0x1C, False),
            "Escape": (0x01, False),
            "Left": (0x4B, True),
            "Right": (0x4D, True),
            "Up": (0x48, True),
        }
        if key not in codes:
            raise MenuEntryError("Only declared menu keys are allowed")
        if stop():
            return
        if not self.ready() or self.window is None:
            raise MenuEntryError("Owned Isaac window is not ready")
        hwnd, pid = self.window
        self.user.ShowWindow(hwnd, 9)
        self.user.SetForegroundWindow(hwnd)
        time.sleep(0.2)

        def foreground() -> bool:
            actual = wintypes.DWORD()
            self.user.GetWindowThreadProcessId(hwnd, ctypes.byref(actual))
            return bool(self.user.GetForegroundWindow() == hwnd and actual.value == pid)

        def send(release: bool) -> None:
            scan, extended = codes[key]
            flags = 8 | (1 if extended else 0) | (2 if release else 0)
            event = _Input(type=1, value=_Union(key=_Key(scan=scan, flags=flags)))
            if self.user.SendInput(1, ctypes.byref(event), ctypes.sizeof(_Input)) != 1:
                raise MenuEntryError(
                    "Menu key release failed" if release else "Menu key-down failed"
                )

        held_key(send, foreground, stop)
