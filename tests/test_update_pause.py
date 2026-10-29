"""OFFLINE tests of pausing the live game around optimizer updates (fake game and keyboard)."""

import csv
import itertools
import types
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from test_live import live

from isaac_threrisaifuture import live as live_module
from isaac_threrisaifuture.episodes import Action
from isaac_threrisaifuture.live import LiveBackend
from isaac_threrisaifuture.menu_entry import MenuEntryError
from isaac_threrisaifuture.stall_watchdog import StallWatchdog
from isaac_threrisaifuture.training_metrics import TrainMetricsCallback
from isaac_threrisaifuture.update_pause import PauseResult, UpdatePause, UpdatePauseCallback


class FakeGame:
    """Status machine: a working Esc toggles paused; `lag` lets the game ignore the key."""

    def __init__(self, log: list[str], status: str = "active") -> None:
        self.log, self.status = log, status
        self.responds = True

    def release(self) -> None:
        self.log.append("release")

    def cancelled(self) -> bool:
        return False

    def game_status(self, timeout: float) -> str | None:
        return self.status

    def wait_game_status(self, wanted: str, timeout: float) -> bool:
        self.log.append(f"wait {wanted}")
        return self.status == wanted


class FakeKeyboard:
    def __init__(self, game: FakeGame, log: list[str], error: str | None = None) -> None:
        self.game, self.log, self.error = game, log, error
        self.keys: list[str] = []

    def ready(self) -> bool:
        return True

    def press(self, key: str, stop: Any) -> None:
        self.keys.append(key)
        self.log.append(f"press {key}")
        if self.game.responds:
            self.game.status = "paused" if self.game.status == "active" else "active"
        if self.error:
            raise MenuEntryError(self.error)


def make(error: str | None = None, status: str = "active", keyboard: bool = True):
    log: list[str] = []
    events: list[tuple[str, Any]] = []
    game = FakeGame(log, status)
    fake = FakeKeyboard(game, log, error)
    ticks = itertools.count(0, 2)
    pause = UpdatePause(
        fake if keyboard else None,
        lambda event, data: events.append((event, data)),
        clock=lambda: float(next(ticks)),
    )
    return pause, game, fake, log, events


def test_pause_then_resume_orders_release_escape_and_waits():
    pause, game, keyboard, log, events = make()
    pause.pause(game)
    assert log == ["release", "press Escape", "wait paused"] and game.status == "paused"
    log.clear()
    result = pause.resume(game)
    assert log == ["press Escape", "wait active"] and game.status == "active"
    assert result == PauseResult(2.0, True) and events == []


def test_game_that_ignores_the_key_times_out_without_a_second_press():
    pause, game, keyboard, log, events = make()
    game.responds = False
    pause.pause(game)
    assert events == [("update_pause_skipped", {"reason": "no paused snapshot in time"})]
    result = pause.resume(game)
    assert result == PauseResult(0.0, False) and keyboard.keys == ["Escape"]  # still active


def test_late_pause_after_a_timeout_is_still_undone_on_resume():
    pause, game, keyboard, log, events = make()
    game.responds = False
    pause.pause(game)
    game.status = "paused"  # the key took effect after the wait gave up
    game.responds = True
    result = pause.resume(game)
    assert game.status == "active" and keyboard.keys == ["Escape", "Escape"]
    assert result is not None and not result.ok


def test_already_paused_game_is_left_alone():
    pause, game, keyboard, log, events = make(status="paused")
    pause.pause(game)
    assert keyboard.keys == [] and log == []
    assert events == [("update_pause_skipped", {"reason": "already paused"})]
    assert pause.resume(game) is None and game.status == "paused"


@pytest.mark.parametrize("status", ["dead", "unavailable", None])
def test_no_pause_without_a_playable_game(status):
    pause, game, keyboard, log, events = make(status=status)  # type: ignore[arg-type]
    pause.pause(game)
    assert keyboard.keys == [] and len(events) == 1
    assert pause.resume(game) is None


def test_focus_loss_before_the_key_is_skipped_and_never_raised():
    pause, game, keyboard, log, events = make(error="Isaac is not foreground; no input sent")
    game.responds = False
    pause.pause(game)
    assert events[0][0] == "update_pause_skipped"
    assert "not foreground" in events[0][1]["reason"]
    assert pause.resume(game) == PauseResult(0.0, False)
    assert keyboard.keys == ["Escape"] and game.status == "active"


def test_focus_loss_after_the_key_down_still_resumes_a_paused_game():
    pause, game, keyboard, log, events = make(error="Isaac lost focus during menu input")
    pause.pause(game)  # the key went down before the focus check failed
    assert game.status == "paused"
    assert "paused, but" in events[0][1]["reason"]
    keyboard.error = None
    result = pause.resume(game)
    assert game.status == "active" and result is not None and not result.ok


def test_failed_resume_retries_once_then_gives_up_without_raising():
    pause, game, keyboard, log, events = make()
    pause.pause(game)
    game.responds = False
    result = pause.resume(game)
    assert keyboard.keys == ["Escape"] * 3 and result is not None and not result.ok
    assert [e for e, _ in events].count("update_resume_failed") == 2


def test_missing_keyboard_is_recorded_and_not_an_error():
    pause, game, keyboard, log, events = make(keyboard=False)
    pause.pause(game)
    assert events == [("update_pause_skipped", {"reason": "no keyboard"})]
    assert pause.resume(game) is None


def test_bridge_error_while_pausing_is_recorded_not_raised():
    pause, game, keyboard, log, events = make()

    def broken(timeout: float) -> str:
        raise ConnectionError("peer closed")

    game.game_status = broken  # type: ignore[method-assign]
    pause.pause(game)
    assert events[0][1]["reason"] == "ConnectionError: peer closed"


class Model:
    def __init__(self, backend: Any) -> None:
        env = types.SimpleNamespace(controller=types.SimpleNamespace(backend=backend))
        self.num_timesteps = 4
        self.rollout_buffer = types.SimpleNamespace(actions=np.zeros((4, 1, 3)))
        self.logger = types.SimpleNamespace(name_to_value={})
        self.get_env = lambda: types.SimpleNamespace(get_attr=lambda name: [env])


def test_callbacks_pause_at_rollout_end_resume_at_start_and_fill_the_columns(tmp_path: Path):
    pause, game, keyboard, log, events = make()
    game.__dict__["wait_game_status"] = game.wait_game_status  # plain duck type for the callback
    pause_callback = UpdatePauseCallback(pause)
    metrics = TrainMetricsCallback(tmp_path / "train.csv", pause=pause_callback)
    for callback in (pause_callback, metrics):
        callback.model = Model(game)  # type: ignore[assignment]
    for _ in range(2):  # the first start has nothing to resume
        for callback in (pause_callback, metrics):
            callback._on_rollout_start()
        assert game.status == "active"
        for callback in (pause_callback, metrics):
            callback._on_rollout_end()
        assert game.status == "paused"  # the optimizer would run now
    for callback in (pause_callback, metrics):
        callback._on_rollout_start()
    metrics._on_training_end()
    rows = list(csv.DictReader((tmp_path / "train.csv").open(encoding="utf-8")))
    assert [(r["pause_seconds"], r["pause_ok"]) for r in rows] == [("2.0", "1"), ("2.0", "1")]


def test_a_skipped_pause_writes_ok_zero_and_a_sim_backend_leaves_the_columns_empty(tmp_path):
    pause, game, keyboard, log, events = make(status="paused")
    callback = UpdatePauseCallback(pause)
    metrics = TrainMetricsCallback(tmp_path / "a.csv", pause=callback)
    for item in (callback, metrics):
        item.model = Model(game)  # type: ignore[assignment]
    callback._on_rollout_end()
    metrics._on_rollout_end()
    callback._on_rollout_start()
    metrics._on_rollout_start()
    metrics._on_training_end()
    (row,) = csv.DictReader((tmp_path / "a.csv").open(encoding="utf-8"))
    assert (row["pause_seconds"], row["pause_ok"]) == ("0.0", "0")

    sim = Model(object())  # a backend that cannot pause
    pause2, game2, keyboard2, *_ = make()
    callback2 = UpdatePauseCallback(pause2)
    metrics2 = TrainMetricsCallback(tmp_path / "b.csv", pause=callback2)
    for item in (callback2, metrics2):
        item.model = sim  # type: ignore[assignment]
    for item in (callback2, metrics2):
        item._on_rollout_end()
    for item in (callback2, metrics2):
        item._on_rollout_start()
    metrics2._on_training_end()
    (row,) = csv.DictReader((tmp_path / "b.csv").open(encoding="utf-8"))
    assert row["pause_seconds"] == row["pause_ok"] == "" and keyboard2.keys == []


def test_release_resumes_a_game_left_paused_by_a_failed_update():
    pause, game, keyboard, log, events = make()
    game.__dict__["wait_game_status"] = game.wait_game_status
    callback = UpdatePauseCallback(pause)
    callback.model = Model(game)  # type: ignore[assignment]
    callback._on_rollout_end()
    assert game.status == "paused"
    callback.release()
    assert game.status == "active"


def snap(frame: int, status: str):
    return live(frame).model_copy(update={"status": status})


def test_backend_replays_pause_snapshots_without_counting_paused_time():
    commands: list[int] = []
    inbox = [snap(2, "active")]
    queue = [snap(3, "paused"), snap(3, "paused"), snap(3, "active"), snap(5, "active")]

    def command(kind, reference, **kwargs):
        commands.append(reference.frame_id)
        return types.SimpleNamespace(status="accepted", frame_id=reference.frame_id)

    def drain():
        items, inbox[:] = list(inbox), []
        return items

    def take(timeout):
        if not queue:
            raise live_module.BridgeTimeout("empty")
        return queue.pop(0)

    client = types.SimpleNamespace(drain=drain, command=command, take=take)
    ticks = itertools.count(0, 50)  # every watchdog observation is 50 s after the last
    watchdog = StallWatchdog(40.0, clock=lambda: float(next(ticks)))
    backend = LiveBackend(client, watchdog=watchdog)  # type: ignore[arg-type]
    backend._current = live(1)
    assert backend.game_status(0.1) == "active"
    assert backend.wait_game_status("paused", 1.0)
    assert not backend.wait_game_status("dead", 0.0)
    queue[:] = [snap(3, "active"), snap(5, "active")]
    assert backend.wait_game_status("active", 1.0)
    assert backend.game_status(0.1) == "active"
    queue[:] = [snap(7, "active")]
    backend.step(Action(), 1)
    assert commands == [3]  # the first command after the pause uses a snapshot read after resume
    # Only the one gap inside the step counts (capped at 2 s); paused and replayed ones add none.
    assert watchdog.idle_seconds == 2.0
