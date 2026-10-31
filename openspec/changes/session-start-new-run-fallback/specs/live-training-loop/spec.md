## ADDED Requirements

### Requirement: Supervisor session entry on file2
A pure-profile supervisor session SHALL continue the file2 game when the fresh native log
confirms a loaded file2 game state, and SHALL start a New Run on file2 only when the fresh log
verifies that file2 has no game state. With neither or both kinds of evidence it SHALL stop
before any entry key. It SHALL never replace an existing Continue.

#### Scenario: Existing game
- **WHEN** the fresh log shows file2 game state loaded
- **THEN** the session sends Continue and records `menu_entry_resolved` with mode `continue`

#### Scenario: No game after a death at the lease end
- **WHEN** the fresh log shows `No Game State detected` for file2
- **THEN** the session starts a New Run, confirms the character and records
  `menu_new_run_verified`

#### Scenario: No evidence
- **WHEN** the fresh log shows neither a loaded nor a missing file2 game state
- **THEN** the session raises a menu fault and sends no entry key
