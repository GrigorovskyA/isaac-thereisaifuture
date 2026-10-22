# Evidence: firing-cadence-diagnostics runtime comparison

- Date/time: 2026-10-19 14:30:17–14:31:12 CEST (12:30:17–12:31:12 UTC).
- Git revision: `53966bef91830c6efa3af865948ea772503bd685`; user-owned working-tree files remained out of scope.
- Change and acceptance: one separately authorized, stationary safe-room comparison; maximum 30 seconds and 16 commands, one nonrenewable 120-second approval, no movement, restart, training, stat change, save edit, or Steam Cloud change.
- Game/mod/bridge: Repentance+ `1.9.7.17.J460`; Isaac Future Observer `0.5.0-dev`; native safe-actions protocol v1.
- Python: CPython `3.12.14`; project package `0.1.0`.
- Installed diagnostic `main.lua` SHA-256: `904a8fa83d4980052d3b843892dca74699e24a68b5f1afd3c223f0c8872ae08b`.
- Restored default-off source `main.lua` SHA-256: `6172e87114a6da0a80697efdbf083b2d93d6a18b09b43c47fdfcf0173767938f`; `metadata.xml` SHA-256: `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.
- Scenario: the user confirmed save file 2, an empty room, centered player, and released keys. Read-only entity preflight observed an active type-0 character at `(320, 380)`, epoch 2 / room visit 0, with zero enemies, projectiles, or relevant overflow.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Read-only safe-room preflight | `ObservationClient(entity_observations=True)` | 0 | passed | Active, centered within probe bounds, empty enemy/projectile sets, no relevant overflow |
| Bounded two-phase probe | `python -m isaac_threrisaifuture.firing_cadence_probe --approval <private-path> --confirmed-save-slot 2 --output <ignored-private-path>` | 0 | passed | 16 command acknowledgements in 5.64 s: 7 three-frame shots, neutral, 7 six-frame shots, explicit release; all remained in one session/epoch/room |
| Private game trace correlation | Current probe session filtered from the local game log, then `firing_trace.analyze_trace` | 0 | passed | 114 records; zero rejected records or ID gaps; `stop reason=close`; 15 accepted actions, 60 sampled input callbacks, 9 native tear callbacks, 15 release records |
| Three-frame phase | Seven stationary three-frame right-shoot commands | 0 | passed | 21 sampled frames returned `1.0`; 4 native tears at relative frames 0, 12, 24, 36; tear callback `FireDelay=10` and `MaxFireDelay=10` |
| Six-frame phase | Seven stationary six-frame right-shoot commands | 0 | passed | 39 sampled frames returned `1.0`; 5 native tears at relative frames 0, 12, 24, 36, 48; tear callback `FireDelay=10` and `MaxFireDelay=10` |
| Release and operator cleanup | Explicit release, Python disconnect, user-confirmed manual control and normal game exit | 0 | passed | 14 paired release-to-next-action intervals (17–200 ms, median 101 ms); final release excluded as a boundary, no unpaired releases; approval removed, process absent, default-off mod restored |
| Final Windows quality gate after archival | `scripts/Check.ps1` | 0 | passed | 1,644 tests, zero skips/xfails; Ruff, format, mypy, pip consistency; strict OpenSpec 30/30 |
| Firing-cadence OpenSpec task | `scripts/OpenSpec.ps1 validate firing-cadence-diagnostics --strict`; `validate --all --strict` | 0 | passed | Change-specific validation passed; 31 active items passed before archive and 30 passed after archive |
| OpenSpec archive | `scripts/OpenSpec.ps1 archive firing-cadence-diagnostics --yes` | 0 | passed | Archived as `openspec/changes/archive/2026-10-19-firing-cadence-diagnostics`; native-player-actions spec updated with five lines |

## Real game

The player remained stationary. Python requested no movement. The test sent 14 right-shoot actions (seven at three frames and seven at six frames), one neutral action between phases, and an explicit release. The private game log was streamed through a filter matching only the probe session, game epoch, and room; neither the raw log nor raw trace was copied into the repository. The diagnostic ended with `stop reason=close`, not a count or deadline stop.

The user confirmed that manual movement and shooting worked after the probe, then closed the game normally. The temporary approval was removed. With no Isaac process running, the installed observer files were restored from the reviewed default-off source and verified by SHA-256; `firing_diagnostics = false`. No save, Steam Cloud, settings, or persistent launch options were changed.

## Interpretation and limitations

The observed native tear callbacks occurred every 12 game frames in both phases. The game reported `FireDelay=10` and `MaxFireDelay=10` on those tear callbacks. The sample therefore shows that both command lengths produced tear callbacks under this run; it does not show that six-frame holds fire faster, establish a maximum rate, prove engine input consumption, or establish a causal effect. The phase durations differed, and callback records are bounded diagnostic evidence. No character or weapon stats were modified.

Only one run was authorized. A repeat, stat adjustment, training run, or broader comparison needs a separate finite decision. The private trace and local backup remain ignored under `reports/local/` and are excluded from Git.
