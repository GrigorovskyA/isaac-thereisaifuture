"""Stall watchdog: active wall time without any progress event ends the episode."""

import time
from collections.abc import Callable

# Events that prove the agent is doing something useful in the game.
PROGRESS_KINDS = frozenset(
    {"enemy_damaged", "room_entered", "room_cleared", "pickup_gained", "floor_entered"}
)
DEFAULT_STALL_SECONDS = 90.0
# One gap between two snapshots earns at most this much time. Snapshots arrive every
# 50 ms, so longer gaps mean a busy learner or a stuck transport, not game time.
MAX_GAP_SECONDS = 2.0


class StallWatchdog:
    """Counts wall time between consecutive active snapshots since the last progress.

    Paused or unavailable snapshots never add time, and neither does the gap that
    follows them. After `stall_seconds` it fires once; `reset()` re-arms it.
    """

    def __init__(
        self,
        stall_seconds: float = DEFAULT_STALL_SECONDS,
        *,
        clock: Callable[[], float] = time.monotonic,
        max_gap: float = MAX_GAP_SECONDS,
    ) -> None:
        if stall_seconds <= 0 or max_gap <= 0:
            raise ValueError("Stall limit and gap cap must be positive")
        self.stall_seconds = stall_seconds
        self.max_gap = max_gap
        self._clock = clock
        self.reset()

    @property
    def idle_seconds(self) -> float:
        return self._idle

    @property
    def fired(self) -> bool:
        return self._fired

    def reset(self) -> None:
        """Start a fresh window, for example on a new game epoch."""
        self._idle = 0.0
        self._fired = False
        self._last: float | None = None  # clock of the previous active snapshot

    def observe(self, *, active: bool, progress: bool = False) -> bool:
        """Feed one snapshot; True exactly once, when the stall limit is reached."""
        now = self._clock()
        last, self._last = self._last, (now if active else None)
        if not active:
            return False
        if progress:
            self._idle = 0.0
            return False
        if last is not None:
            self._idle += min(max(0.0, now - last), self.max_gap)
        if self._idle >= self.stall_seconds and not self._fired:
            self._fired = True
            return True
        return False
