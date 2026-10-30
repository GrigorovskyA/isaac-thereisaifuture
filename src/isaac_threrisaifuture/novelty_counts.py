"""Cross-run novelty counts for reward v11 (reward state only, never an observation).

For each novelty key (stage, room, cell) the table stores in how many runs it was first visited.
The ledger pays coefficient / sqrt(N) with N that count, so the start room stops paying ~3 per run.

Size bound: a floor has at most 169 grid rooms and a room at most 26 x 14 cells, and stages go to
13, so the table cannot pass 13 * 169 * 364 = 799,708 keys (about 16 MB as npz, 5 ints each).
`MAX_KEYS` is a hard cap above that; a full table refuses new keys (they pay nothing).
"""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray

Key = tuple[int, int, int, int]
MAX_KEYS = 1_000_000
COUNTS_FILE = "novelty_counts.npz"
_FORMAT = 1


class NoveltyCountsError(Exception):
    """Missing or corrupt counts file."""


class NoveltyCounts:
    """Runs-per-key table. A frozen table (evaluation) never stores a count."""

    def __init__(self, *, frozen: bool = False) -> None:
        self.frozen = frozen
        self._counts: dict[Key, int] = {}

    def __len__(self) -> int:
        return len(self._counts)

    def get(self, key: Key) -> int:
        return self._counts.get(key, 0)

    def visit(self, key: Key) -> int:
        """Count a first visit of `key` in a run; return N, or 0 when the table is full."""
        before = self._counts.get(key, 0)
        if self.frozen:
            return before + 1  # peek: the count a real run would have paid
        if before == 0 and len(self._counts) >= MAX_KEYS:
            return 0
        self._counts[key] = before + 1
        return before + 1

    def save(self, path: Path) -> None:
        rows: NDArray[np.int64] = np.zeros((len(self._counts), 5), dtype=np.int64)
        for index, (key, count) in enumerate(sorted(self._counts.items())):
            rows[index] = (*key, count)
        with path.open("wb") as stream:
            np.savez(stream, format=np.int64(_FORMAT), rows=rows)

    def load(self, path: Path) -> None:
        """Replace the table with the file's content; never reads pickles."""
        try:
            with np.load(path, allow_pickle=False) as data:
                rows = data["rows"]
                version = int(data["format"])
        except (OSError, ValueError, KeyError) as error:
            raise NoveltyCountsError(f"Cannot read novelty counts {path}: {error}") from error
        if version != _FORMAT or rows.ndim != 2 or rows.shape[1] != 5:
            raise NoveltyCountsError(f"Unsupported novelty counts file {path}")
        if len(rows) > MAX_KEYS or (len(rows) and int(rows[:, 4].min()) < 1):
            raise NoveltyCountsError(f"Invalid novelty counts file {path}")
        self._counts = {(int(a), int(b), int(c), int(d)): int(n) for a, b, c, d, n in rows.tolist()}
