# Archive

This directory holds code, tests, configs, docs and OpenSpec changes from the
hinted training direction (scripted setup, combat gate, geometry features, firing
shaping, combat navigation, diagnostics and roadmap stubs). The project moved to
pure self-learning on 2026-10-22; see `docs/UPDATE_DECISION.md`.

Rules:

- This is history only. Nothing here is current authority or instructions.
- Nothing here is imported, linted, type-checked or tested. Files keep their
  original contents, so imports inside them may point to modules that no longer
  exist in `src/`.
- Do not move code back without a new OpenSpec change.
- Old checkpoint lineages under `runs/` are not moved. They stay on disk and are
  not compatible with the pure profile.

Layout mirrors the original paths:

| Path | Contents |
| --- | --- |
| `src/isaac_threrisaifuture/` | Hint, diagnostic, native-episode and roadmap modules |
| `tests/` | Their tests and the wall-stagnation fixture |
| `mod/main.pre-pure.lua` | Full observer mod before the pure trim; `mod/experimental/` |
| `configs/` | v2-v5 pilot training configs |
| `docs/` | Hint and experiment docs, old tasks and plans |
| `openspec/changes/` | All open changes at the time of the switch |
| `openspec/specs/combat-experience-gate/` | Spec of the removed combat gate |
| `root/`, `scripts/` | Old file-bus pointers, death-restart launcher, wait scripts |

`openspec/changes/wall-stagnation-replay/` and
`src/isaac_threrisaifuture/wall_stagnation.py` were uncommitted work of another
agent at the time of the move. They are preserved here unchanged; the diagnosis
report stays in `reports/2026-10-22-wall-stagnation-diagnosis.md`.
