"""Pause the game while the optimizer runs (live backend only).

Isaac keeps running during an update, so damage taken while the learner is busy would be blamed
on the first action of the next rollout. At rollout end the callback releases the held input and
presses Esc through the guarded menu keyboard, then waits for a "paused" snapshot. At the next
rollout start it presses Esc again and waits for an "active" one. Pausing is best effort: every
failure is recorded and training goes on without a pause; it never faults the session.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from stable_baselines3.common.callbacks import BaseCallback

from .menu_entry import MenuInput

WAIT_SECONDS = 3.0
STATUS_SECONDS = 0.5
RESUME_ATTEMPTS = 2


class PausableGame(Protocol):
    def release(self) -> None: ...
    def cancelled(self) -> bool: ...
    def game_status(self, timeout: float) -> str | None: ...
    def wait_game_status(self, wanted: str, timeout: float) -> bool: ...


@dataclass(frozen=True)
class PauseResult:
    seconds: float  # time the game stood still around the update; 0 when it did not
    ok: bool  # paused and resumed cleanly


class UpdatePause:
    """Pause and resume one game around an update; state is kept between the two calls."""

    def __init__(
        self,
        keyboard: MenuInput | None,
        record: Callable[[str, Any], None],
        *,
        wait_seconds: float = WAIT_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.keyboard = keyboard
        self.record = record
        self.wait_seconds = wait_seconds
        self._clock = clock
        self._reset()

    def _reset(self) -> None:
        self._pressed = False  # an Esc was sent, so the game may be paused
        self._ok = False
        self._since: float | None = None

    def _skip(self, event: str, reason: str) -> None:
        self.record(event, {"reason": reason})

    def _press(self, game: PausableGame) -> str | None:
        """Send Esc; the error text when the key could not be sent cleanly."""
        if self.keyboard is None:
            return "no keyboard"
        try:
            self.keyboard.press("Escape", game.cancelled)
        except Exception as error:  # focus lost, window gone, SendInput failed
            return f"{type(error).__name__}: {error}"
        return None

    def pause(self, game: PausableGame) -> None:
        self._reset()
        try:
            status = game.game_status(STATUS_SECONDS)
            if status != "active":
                reason = "already paused" if status == "paused" else f"game {status or 'silent'}"
                return self._skip("update_pause_skipped", reason)
            game.release()
            error = self._press(game)
            self._pressed = error != "no keyboard"
            if error == "no keyboard":
                return self._skip("update_pause_skipped", error)
            if game.wait_game_status("paused", self.wait_seconds):
                self._since = self._clock()
                self._ok = error is None
                if error is not None:
                    self._skip("update_pause_skipped", f"paused, but {error}")
            else:
                self._skip("update_pause_skipped", error or "no paused snapshot in time")
        except Exception as error:  # a closed bridge is faulted by the next step, not here
            self._skip("update_pause_skipped", f"{type(error).__name__}: {error}")

    def resume(self, game: PausableGame) -> PauseResult | None:
        """Undo the pause; None when no pause was attempted for this update."""
        if not self._pressed:
            return None
        resumed = False
        try:
            for _ in range(RESUME_ATTEMPTS):
                # Trust the game, not our bookkeeping: a late or failed key may leave either state.
                status = game.game_status(STATUS_SECONDS)
                if status != "paused":
                    resumed = True
                    break
                error = self._press(game)
                if game.wait_game_status("active", self.wait_seconds):
                    resumed = True
                    break
                self._skip("update_resume_failed", error or "no active snapshot in time")
        except Exception as error:
            self._skip("update_resume_failed", f"{type(error).__name__}: {error}")
        seconds = 0.0 if self._since is None else max(self._clock() - self._since, 0.0)
        result = PauseResult(seconds, self._ok and resumed)
        self._reset()
        return result


class UpdatePauseCallback(BaseCallback):
    """Calls the pause at rollout end and the resume at the next rollout start.

    Put it before the metrics callback: the resume then finishes before the next rollout is
    timed, and `last` is ready when the metrics row of the finished update is written.
    """

    def __init__(self, pause: UpdatePause) -> None:
        super().__init__()
        self.pause = pause
        self.last: PauseResult | None = None
        self._armed = False  # a pause was attempted at the last rollout end

    def _game(self) -> PausableGame | None:
        try:
            env: Any = self.training_env.get_attr("unwrapped")[0]
            backend = env.controller.backend
        except Exception:
            return None
        return backend if hasattr(backend, "wait_game_status") else None  # sim and fakes: no-op

    def _on_step(self) -> bool:
        return True

    def _on_rollout_end(self) -> None:
        game = self._game()
        if game is not None:
            self.last, self._armed = None, True
            self.pause.pause(game)

    def _on_rollout_start(self) -> None:
        self.release()

    def release(self) -> None:
        """Resume if paused (also called when training ends or fails while paused)."""
        game = self._game()
        if game is not None:
            result = self.pause.resume(game)
            if self._armed:
                self.last = result or PauseResult(0.0, False)  # skipped: nothing was paused
            self._armed = False
