"""Bounded Steam launch and observation, with optional local menu-only Continue."""

import argparse
import csv
import hashlib
import json
import math
import os
import re
import subprocess
import time
import uuid
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TextIO

from .menu_entry import FreshGameLog, continue_file2, new_run_file2
from .observation import BridgeError, BridgeTimeout, ProtocolError
from .observer_client import ObservationClient, ObserverConfig

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MOD_DIRECTORY = Path("mods/isaac_threrisaifuture_observer")


@dataclass(frozen=True)
class LaunchOptions:
    samples: int = 3000
    connection_timeout: float = 180
    duration: float = 900
    reconnects: int = 3
    continue_file2: bool = False
    new_run_file2: bool = False

    def __post_init__(self) -> None:
        if type(self.continue_file2) is not bool or type(self.new_run_file2) is not bool:
            raise ValueError("Automatic entry flags must be boolean")
        if self.continue_file2 and self.new_run_file2:
            raise ValueError("Continue and New Run are mutually exclusive")
        if type(self.samples) is not int or not 1 <= self.samples <= 100000:
            raise ValueError("Samples must be an integer in 1..100000")
        if type(self.reconnects) is not int or not 0 <= self.reconnects <= 10:
            raise ValueError("Reconnects must be an integer in 0..10")
        for name, value, limit in (
            ("Connection timeout", self.connection_timeout, 600),
            ("Duration", self.duration, 3600),
        ):
            if not math.isfinite(value) or not 0 < value <= limit:
                raise ValueError(f"{name} must be finite, positive and at most {limit} seconds")


def library_paths(steam_root: Path) -> list[Path]:
    """Read library path entries only; never inspect Steam account/userdata files."""
    paths = [steam_root]
    vdf = steam_root / "steamapps/libraryfolders.vdf"
    if vdf.is_file():
        text = vdf.read_text(encoding="utf-8-sig")
        for match in re.finditer(r'^\s*"path"\s*"([^"\r\n]+)"', text, re.MULTILINE):
            path = Path(match[1].replace("\\\\", "\\"))
            if path not in paths:
                paths.append(path)
    return paths


def discover_game() -> Path:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
        steam_root = Path(winreg.QueryValueEx(key, "SteamPath")[0])
    found = [
        directory
        for library in library_paths(steam_root)
        if (directory := library / "steamapps/common/The Binding of Isaac Rebirth")
        .joinpath("isaac-ng.exe")
        .is_file()
    ]
    if len(found) != 1:
        raise ValueError("Expected one installed Isaac; supply --game-directory explicitly")
    return found[0]


def game_running() -> bool:
    """Conservatively refuse any already-running Isaac process, regardless of library."""
    result = subprocess.run(
        ["tasklist.exe", "/FI", "IMAGENAME eq isaac-ng.exe", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
        errors="replace",
        check=True,
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return any(
        row and row[0].casefold() == "isaac-ng.exe"
        for row in csv.reader(result.stdout.splitlines())
    )


def preflight(directory: Path, project: Path = PROJECT_ROOT) -> Path:
    directory = directory.resolve(strict=True)
    if not (directory / "isaac-ng.exe").is_file():
        raise ValueError("Selected game directory does not contain isaac-ng.exe")
    if game_running():
        raise ValueError("Isaac is already running; exit normally to preserve the run first")
    for name in ("main.lua", "metadata.xml"):
        source = project / "mod/observer" / name
        deployed = directory / MOD_DIRECTORY / name
        if not deployed.is_file():
            raise ValueError(f"Observer artifact missing: {name}; review deployment instructions")
        if (
            hashlib.sha256(source.read_bytes()).digest()
            != hashlib.sha256(deployed.read_bytes()).digest()
        ):
            raise ValueError(f"Observer artifact differs: {name}; no automatic overwrite")
    return directory


class EventLog(AbstractContextManager["EventLog"]):
    def __init__(self, path: Path) -> None:
        self.stream: TextIO = path.open("x", encoding="utf-8")

    def record(self, event: str, data: object = None, *, visible: bool = True) -> None:
        line = json.dumps({"time": time.time(), "event": event, "data": data}, allow_nan=False)
        self.stream.write(line + "\n")
        self.stream.flush()
        if visible:
            print(line, flush=True)

    def __exit__(self, *args: object) -> None:
        self.stream.close()


def request_steam_launch() -> None:
    """Use the user's existing Steam configuration without desktop input."""
    os.startfile("steam://rungameid/250900")


def observe_game(
    directory: Path,
    options: LaunchOptions,
    project: Path = PROJECT_ROOT,
    *,
    game_log: Path | None = None,
) -> Path:
    """Preflight, bind, request launch, then observe within explicit budgets."""
    directory = preflight(directory, project)
    run = project / "runs" / (time.strftime("observe-%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    print(f"Local logs: {run}", flush=True)
    deadline = time.monotonic() + options.duration
    with EventLog(run / "observer.jsonl") as log:
        try:
            log.record("configuration", asdict(options))
            config = ObserverConfig(accept_timeout=options.connection_timeout)
            with ObservationClient(config) as client:
                log.record("listening", client.address)
                if game_running():
                    raise ValueError("Another game instance appeared; launch cancelled")
                if time.monotonic() >= deadline:
                    raise BridgeTimeout("Observation session deadline expired before launch")
                journal = (
                    FreshGameLog(
                        game_log
                        or Path.home() / "Documents/My Games/Binding of Isaac Repentance+/log.txt"
                    )
                    if options.continue_file2 or options.new_run_file2
                    else None
                )
                launched_at = time.time()
                request_steam_launch()
                log.record("launch_requested", {"via": "steam", "ready": False})
                log.record(
                    "waiting_for_run",
                    {
                        "requested_save": 2,
                        "automatic_continue": options.continue_file2,
                        "automatic_new_run": options.new_run_file2,
                    },
                )
                if journal is not None:
                    from .windows_menu import WindowsMenu

                    entry = new_run_file2 if options.new_run_file2 else continue_file2
                    entry(journal, WindowsMenu(directory, launched_at), deadline, log.record)
                observe_sessions(client, options, deadline, log)
        except KeyboardInterrupt:
            log.record("stopped", "User interrupted; observer closed, game left running")
            raise
        except (BridgeError, OSError, ValueError, subprocess.SubprocessError) as exc:
            log.record("fault", str(exc))
            raise
    return run


def observe_sessions(
    client: ObservationClient, options: LaunchOptions, deadline: float, log: EventLog
) -> None:
    samples = 0
    retries = options.reconnects
    while samples < options.samples:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeTimeout("Observation session deadline expired")
        client.config = ObserverConfig(
            accept_timeout=min(options.connection_timeout, remaining / 2),
            handshake_timeout=min(3, remaining / 2),
        )
        try:
            log.record("handshake", client.accept().model_dump(mode="json"))
            while samples < options.samples:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise BridgeTimeout("Observation session deadline expired")
                client.config = ObserverConfig(message_timeout=min(3, remaining))
                snapshot = client.receive()
                if options.new_run_file2:
                    if snapshot.status != "active" or snapshot.player is None:
                        log.record(
                            "waiting_for_active_isaac", {"status": snapshot.status}, visible=False
                        )
                        continue
                    if snapshot.player.character_type != 0:
                        raise ValueError("New Run character is not Isaac; readiness refused")
                if samples == 0:
                    log.record(
                        "bridge_ready",
                        {
                            "session": snapshot.session_id,
                            "frame": snapshot.frame_id,
                            "requested_save": 2,
                            "save_slot_verified": options.continue_file2 or options.new_run_file2,
                            "character_verified": 0 if options.new_run_file2 else None,
                            "slot_evidence": "native_new_log"
                            if options.new_run_file2
                            else "native_continue_log"
                            if options.continue_file2
                            else None,
                        },
                    )
                log.record("snapshot", snapshot.model_dump(mode="json"), visible=False)
                samples += 1
                if samples % 5 == 1:
                    log.record(
                        "progress",
                        {
                            "samples": samples,
                            "frame": snapshot.frame_id,
                            "session": snapshot.session_id,
                        },
                    )
        except ProtocolError:
            raise  # Malformed/incompatible data must not be concealed by retrying.
        except BridgeError as exc:
            if retries == 0:
                raise
            retries -= 1
            log.record(
                "reconnecting", {"reason": str(exc), "retries_left": retries, "outcome": "unknown"}
            )
    log.record("completed", {"samples": samples})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-directory", type=Path)
    parser.add_argument("--samples", type=int, default=3000)
    parser.add_argument("--connection-timeout", type=float, default=180)
    parser.add_argument("--duration", type=float, default=900)
    parser.add_argument("--reconnects", type=int, default=3)
    parser.add_argument("--preflight-only", action="store_true")
    entry_options = parser.add_mutually_exclusive_group()
    entry_options.add_argument(
        "--continue-file2", action="store_true", help="Local menu keys; no screenshots"
    )
    entry_options.add_argument("--entry-mode", choices=["manual", "continue", "new-run"])
    parser.add_argument("--game-log", type=Path, help="Native Repentance+ log for menu evidence")
    args = parser.parse_args()
    try:
        if os.name != "nt":
            raise ValueError("Game launch requires native Windows")
        options = LaunchOptions(
            args.samples,
            args.connection_timeout,
            args.duration,
            args.reconnects,
            args.continue_file2 or args.entry_mode == "continue",
            args.entry_mode == "new-run",
        )
        directory = args.game_directory or discover_game()
        print("Read-only observation; no gameplay control or training.", flush=True)
        if options.new_run_file2:
            print(
                "Explicit file2 New Run; existing Continue is protected; Isaac required.",
                flush=True,
            )
        elif options.continue_file2:
            print(
                "Local menu-only Continue on file2; do not use the game menus during startup.",
                flush=True,
            )
        else:
            print("Select file2 / Continue manually; slot identity is unverified.", flush=True)
        print(
            "Steam launch uses existing options; --luadebug must already be configured.", flush=True
        )
        print("Ctrl+C closes observation; the game remains running for normal exit.", flush=True)
        print(
            f"Session limits: {options.samples} snapshots, {options.duration:g} seconds total, "
            f"{options.reconnects} reconnects.",
            flush=True,
        )
        if args.preflight_only:
            preflight(directory)
            print("Preflight passed; no processes launched or game files changed.")
        else:
            observe_game(directory, options, game_log=args.game_log)
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except (BridgeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Launcher error: {exc}", flush=True)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
