## Context

No bridge field currently reports the active save slot, the achievements flag, console/debug use,
save tampering or the mod list. These are modelled as optional evidence values.

## Decisions

- **Fail closed**: `None` means unknown and is always denied with an explicit reason code
  (`*_unknown`). Wrong or bad values give `slot_wrong`, `achievements_disabled`, `console_debug_used`,
  `save_edited_or_imported`, `mods_block_achievements`. An empty game version is `game_version_unknown`.
- **Guard**: `require_eligible` raises `EligibilityError(reasons)` and must run before any autonomous
  progression; `evaluate` is the non-raising form.
- **Audit**: `audit_record` returns a JSON-serializable dict with a schema version and only
  bridge-observed values; no filesystem paths or user names.
- **Required slot**: constant 2 per the user's target.
