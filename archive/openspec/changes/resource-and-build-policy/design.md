## Design

- Dedupe by identity `(session, room_visit, entity_id, spawn_generation)`; items are
  additionally deduped by `item_id` per episode, so drop-then-repick pays nothing.
- Hearts pay only effective healing (capped by max hearts); coins/bombs/keys by effective gain.
- `use` and `spend` never pay; empty uses are counted in stats.
- Total shaping per episode is capped (`episode_cap`); events from another session raise.
- `BuildChooser` is a Protocol; `RandomChooser` is a labelled scripted baseline.
- `evaluate_build` takes an evaluation callable so builds run on fixed scenarios, never in a
  live episode. Weights are hypotheses, not optimal constants.
