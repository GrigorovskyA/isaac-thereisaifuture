## Context

AGENTS.md allows reference knowledge but requires provenance and licenses, and forbids
hidden data in policy inputs.

## Decisions

- **Schema**: pydantic strict, frozen, `extra=forbid` (so unexpected fields such as seed contents
  are rejected). `schema_version` must equal 1.
- **Provenance**: at least one source with name, license, retrieved date, permitted use and a
  url or commit; every record cites a declared source.
- **Honesty fields**: `confidence` (default `unknown`), `verified_in_game` (default false), and
  `unknown_fields`. Verified without a known confidence is rejected.
- **Loader**: file absent returns an empty `KnowledgeBase`; oversize (1 MiB) or invalid files
  raise `KnowledgeError`. Loaded once, no per-step re-reads.
- **Encoder**: input is the player's own item ids; output is `len(tag_vocabulary) + 1` floats:
  saturating tag counts and the fraction of unknown ids. Unknown ids are handled explicitly.
