## MODIFIED Requirements

### Requirement: Explicit bounded observation launch
The launcher SHALL start the listener before requesting Steam application250900
through its existing URI handler,provide terminal output and local logs,and
enforce connection,sample and total duration limits. Manual observation MUST NOT
send desktop input. Optional automatic entry SHALL use only the bounded verified
menu mode specified by local-menu-entry. No mode SHALL capture screens or start
training as part of observation readiness.

#### Scenario: Launch an approved closed game
- **WHEN** installation and observer preflight checks pass
- **THEN** the listener binds before the Steam request and readiness requires a validated snapshot,plus native Continue2 evidence in automatic mode

#### Scenario: Installation or deployment is unsuitable
- **WHEN** game/project Python is missing,deployed hashes differ or a game is running
- **THEN** the command fails without game launch or game-file modification
