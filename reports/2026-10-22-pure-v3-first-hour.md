# Evidence: pure-v3 first hour and the stall watchdog fix

- Date: 2026-10-22, Europe/Amsterdam. Host: macOS, offline read of
  `runs/pure-v3/metrics/{episodes,train}.csv` and
  `runs/pure-v3/supervisor/session-20261022-195102-0001/events.jsonl` during the
  running two-hour session. No game control and no SMB writes during the session.
- Lineage `pure-v3` (schema 4, reward v4, action repeat 6, seed 1), contract hash
  `03b9c5e3...`. Data up to checkpoint `03b9c5e3-s1-t22528` (44 updates).

## Episodes (second session, 34 episodes; plus 6 qualification episodes)

| Third | Mean return | Left start room | Rooms cleared | Death share | Bomb requests per step |
| --- | ---: | ---: | ---: | ---: | ---: |
| pure-v2, first 10 | -4.76 | 50% | 0.00 | 30% | 0.238 |
| pure-v3, 1 | 2.08 | 77% | 0.23 | 23% | 0.047 |
| pure-v3, 2 | -3.69 | 69% | 0.08 | 54% | 0.064 |
| pure-v3, 3 | -3.78 | 75% | 0.08 | 42% | 0.070 |

- Reward alignment: return vs rooms cleared r=0.86, vs damage dealt r=0.60; left
  start room -0.55 vs stayed -5.08; any clear +18.5 (4 episodes).
- The use-head prior worked: bomb requests 0.05-0.07 per step instead of 0.24, but
  the bomb share in `train.csv` rose from 0.046 to 0.080 over 40 updates.
- Explained variance 0.17-0.59 (pure-v2 ended at -3.28). Entropy about 3.8 of 4.6;
  the lower start comes from the prior, not from learning.
- One collectible in 40 episodes; no second floor. About 4.3 steps per second.

## Findings

1. Episode 33 ran 4242 steps (about 16 min) with 2 rooms visited and no enemy damage.
   Every `room_entered` event reset the stall watchdog, including re-entering a known
   room, so walking through one door back and forth kept a stalled run alive (value
   loss fell to 0.0016). `pickup_gained` had the same hole (bomb placed, bomb picked
   up). Fixed by `openspec/changes/stall-watchdog-novel-progress`.
2. Many deaths are very fast: all 15 deaths lose 6 half-hearts, several within 5-69
   steps (episode 18: 5 steps, 211 game updates, 8 enemies spawned; episode 31:
   44 steps with no enemies). A fresh Basement run should not die that fast. Not yet
   explained; candidates are an episode starting before the New Run took effect, or
   self-damage (bombs, fire places, spikes). Needs a native look at the transition.
3. `enemies_killed` is 0 in every episode, including cleared rooms. The counter does
   not work; reward is unaffected (it pays damage and clears).
4. Obstacles carry no type: the Lua side sends the 12 nearest grid obstacles (rocks,
   pits, spikes, poop, TNT, walls) with position only, so the agent cannot tell a
   bombable rock from a pit or see that a pickup is enclosed.

## Watchdog fix verification (macOS)

- New tests: revisits, counter peaks, collectibles, floors, damage, clears, and a live
  test where walking between two known rooms still stalls after 90 s; it fails on the
  old behaviour and passes now.
- Gate: ruff and format clean, mypy 31 files clean, pytest 1120 passed / 1 skipped /
  2 known macOS-only failures, strict OpenSpec 14/14, RL smoke passed.
- not_run: Windows `Check.ps1`, native effect (tasks 2.2 and 2.3 of the change).

Limits: one seed, about 40 episodes, observational. No claim of improved play.
