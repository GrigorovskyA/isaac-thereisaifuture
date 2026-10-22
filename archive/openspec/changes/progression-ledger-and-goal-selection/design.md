## Context

AGENTS.md forbids edited saves or unlock commands as achievement evidence and requires
provenance. Nothing records per-file progress yet.

## Decisions

- **Ledger**: JSONL, one event per line with `seq`, `goal_id`, `source`, `session_id`,
  `run_id`, `timestamp`, `prev_hash`, `hash` (SHA-256 over canonical JSON). Load verifies
  sequence, chain, hash and source; the first failure sets `Ledger.error`.
- **Counting**: `completed_goals()` raises `LedgerError` when verification failed; appends are
  refused too. Only `observed_in_game` counts.
- **Graph**: JSON `{schema_version, target, goals: {id: {requires: [...]}}}` loaded from a
  parameter path. Missing dependencies and cycles raise `GraphError`. Test data is synthetic.
- **Selector**: considers only goals the target transitively needs, picks the first
  alphabetically among those whose requirements are all observed, and returns a reason and the
  sorted remaining list.
