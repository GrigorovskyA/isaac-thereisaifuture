# Item knowledge data

Optional reference data loaded by `isaac_threrisaifuture.knowledge.load_knowledge`. A missing
file yields an empty knowledge base; nothing else depends on it.

- `synthetic_items.json` is a **synthetic fixture** with fake IDs. It contains no real Isaac data.
- Real datasets need per-source provenance (name, url or commit, license, retrieved date,
  permitted use) and per-record `confidence` / `verified_in_game`. Items are not trusted as
  verified until IDs are confirmed in the installed game.
- Reference data must never contain hidden contents of the current seed.
- Files are limited to 1 MiB, are loaded once at startup, and are never re-read per policy step.
