## MODIFIED Requirements

### Requirement: Explicit bounded observation launch
The launcher SHALL discover the local Steam installation or accept an explicit
game directory and enforce connection, sample and total duration limits without
monitor capture. Manual observation SHALL NOT send keyboard/mouse input; the
user-authorized local-menu-entry mode SHALL govern optional menu-only keys.
Launch SHALL use the fixed
Steam application URI and preserve existing Steam options.

#### Scenario: Launch an approved closed game
- **WHEN** installation and deployed observer match preflight checks
- **THEN** the listener is bound before requesting steam://rungameid/250900 and readiness is reported only after a validated snapshot

#### Scenario: Installation or deployment is unsuitable
- **WHEN** the game or project Python is missing, deployed hashes differ, or a game is running
- **THEN** the launcher fails before game launch and changes no game files

#### Scenario: Steam dispatch fails
- **WHEN** the registered URI launch raises an operating-system error
- **THEN** the launcher reports failure and closes the listener without direct-executable fallback

## ADDED Requirements

### Requirement: Agent terminal readiness entry point
The agent entry point SHALL finish without a terminal pause after one validated
snapshot or a bounded failure, propagate the launcher's exit code, and support
preflight without launch. It MUST NOT capture screens,start training or infer slot
selection from bridge readiness alone. Optional menu input SHALL follow the
user-authorized local-menu-entry contract; manual mode SHALL send no desktop input.

#### Scenario: First snapshot arrives
- **WHEN** the bridge handshake and first snapshot validate within the deadline
- **THEN** output includes bridge_ready with session/frame identity and slot evidence verified only by the optional native Continue check,otherwise explicitly unverified

#### Scenario: User has not entered a run
- **WHEN** no validated snapshot arrives within the configured deadline
- **THEN** the script exits with failure, releases its sockets, and leaves the game open for manual entry or normal exit
