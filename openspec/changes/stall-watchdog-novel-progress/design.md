## Design

`RunProgress` (in `stall_watchdog.py`) keeps per-run sets of visited
`(stage, room_index)` keys, floors and collectible IDs and the peak of each counter.
`LiveBackend.start_episode` resets it from the first playable snapshot; `_watch`
asks `RunProgress.novel(events, stage=...)` instead of matching event kinds.
`StallWatchdog` itself is unchanged (it still takes a boolean `progress`).

The event deriver and the reward ledger are untouched: the reward ledger already
pays only first visits and counters above the peak, so watchdog and reward now
agree on what counts as progress.
