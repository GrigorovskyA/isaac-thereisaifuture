## Why

Roadmap item 13: item reference knowledge must be allowed but never silently trusted. A
versioned, provenance-checked, optional dataset and a feature encoder let later policies use
item tags without a scripted strategy and without hidden seed data.

## What Changes

- Add `knowledge.py`: strict schema, `load_knowledge`, `KnowledgeBase` (lookup by id and tag),
  tag-count feature encoder.
- Add `data/knowledge/` with a clearly synthetic fixture (fake IDs) and a README.

## Scope and non-goals

- In scope: offline contract, rejection paths, optional loading.
- Out of scope: real item data, in-game ID verification, action extensions for active
  items, bombs, cards and pills, policy integration.
- This is an offline contract. The change MUST NOT be archived until real item IDs are
  confirmed in game and the real dataset has audited provenance.

## Dependencies and risks

- Risk: a real dataset may carry wrong numbers; `confidence` and `verified_in_game` make that explicit.
- Blocked: in-game ID confirmation and 30-50 real items.
