## Context

The v10 cost of a state is the minimum over usable doors of `in_room(e) + H(target)`, with
`in_room(e) = d / D` when the room is calm (clear, no enemies) and the door is open, else the
constant 1. A live boss room costs 1. Walking through an open door into a new room that still has
enemies changes `in_room` from near 0 to 1, so the step pays `gamma * Phi(s') - Phi(s)` of about
`-coefficient`. At 61k steps this looks like the cause of the stalls next to open doors.

## Change

One parameter, `blocked_cost` (`door_shaping_blocked_cost`, default 1.0 in code):

- in-room term of a door in a room that is not calm, or of a closed door: `blocked_cost`;
- cost of a boss room that is not clear or has enemies: `blocked_cost`.

v11 sets it to 0. Since the same `Phi` is used for `s` and `s'`, the shaping stays
`gamma * Phi(s') - Phi(s)` with `Phi = 0` after a terminal step: it still telescopes to
`-Phi(s0)` and does not change the optimal policy (Ng et al. 1999).

## Effects

- Entering a frontier room (a new room with unvisited neighbours): `Phi` stays near 0, no cost.
- Entering a dead end: `H` is at least 1, so `Phi` drops by `coefficient * H`; this is the
  information the potential should give.
- Clearing a room: `Phi` falls by at most `coefficient * d / D` (<= 2), small against
  `room_clear_first` 10.
- The no-goal fallback `1 + max_hops` is unchanged, so a floor with nothing left still reads as
  the worst state.

## Stall is terminal for learning

SB3 sets `TimeLimit.truncated` from the returned `truncated` flag and RecurrentPPO adds
`gamma * V(terminal obs)` to the reward. A stall is followed by a New Run, so the episode really
ends, and the stall clock is an observation, so V of the last state is not a value of continued
play. `IsaacCombatEnv.step` returns `terminated = terminated or stall` and `truncated = truncated
and not stall`; the transition, `info`, the summary and `episodes.csv` are unchanged. The reward
`terminal` flag follows the same rule, so `Phi(s')` = 0 is paid only on a true end. Consumers of
the flags (`FaultTolerantEnv`, evaluation, live evaluation, `random` run) only test
`terminated or truncated`; outcome counts come from `info["outcome"]` and the summary.

## Novelty across runs

`NoveltyCounts` maps `(stage, room, cell_x, cell_y)` to the number of runs that first visited
the key. The ledger keeps its per-run set; on a first visit in a run it increments the count and
pays `coefficient / sqrt(N)` (0.1, 0.0707, 0.0577 ...). Counts survive runs, sessions and
resumes, so cycling runs cannot reset them. The table is saved as `novelty_counts.npz` (int64
rows, no pickle) in each checkpoint directory, with its sha256 in the manifest; resume loads it,
a fresh model starts empty. Size: at most 13 stages * 169 grid rooms * 364 cells = 799,708 keys
(about 16 MB); `MAX_KEYS` 1,000,000 is a hard cap and a full table pays nothing for new keys.
Frozen evaluation uses a frozen table: it reads (N = count + 1, empty at start) and never stores.
Room indexes repeat across seeds, so a key is a position in the grid, not a specific room.

## Hyperparameters

`target_kl` is an optional `Hyperparameters` field (None when absent) passed to
RecurrentPPO and recorded per checkpoint like the others; the contract hash covers only
`contract`.

## Loader and compatibility

`blocked_cost` is required for v11 (a number, not a bool, >= 0) and forbidden for v9 and v10, so
the v10 config, its tests and its results stay byte-for-byte as they were. The reward contract
becomes `pure-v11`; `pure-v10` checkpoints are refused like `pure-v9` ones. `cross_run` is required for v11 and
forbidden for v4-v10, whose configs and results do not change.
