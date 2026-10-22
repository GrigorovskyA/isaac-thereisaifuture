## Why

Roadmap item 20: the Dead God goal on file 2 needs a persistent, tamper-evident record of
which prerequisites were actually observed in game, and a deterministic way to choose the
next achievable goal. Account-wide Steam achievements must not substitute for it.

## What Changes

- Add `progression.py`: append-only hash-chained JSONL `Ledger`, `UnlockGraph` loader,
  `select_next_goal` with an explanation.
- Only `observed_in_game` evidence counts; `manual_note` and `inferred` are stored but ignored.

## Scope and non-goals

- In scope: offline ledger, graph-as-data loader, selector, synthetic-fixture tests.
- Out of scope: real unlock requirements (supplied later as researched data), slot
  eligibility (item 19), reconciling with the real file-2 state, daily/time-gated goals.
- This is an offline contract. It MUST NOT be archived until real evidence exists.

## Dependencies and risks

- Real dependency data for the verified game version is unknown and not shipped.
- A hash chain detects accidental edits and casual tampering, not a malicious rewrite of the
  whole file.
