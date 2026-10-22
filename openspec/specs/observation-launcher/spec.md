# observation-launcher Specification

## Purpose
Define a bounded Windows terminal entry point that launches the approved game
and read-only observer, exposes session logs, reconnects conservatively and
preserves user control without screen capture or desktop input injection.

## Requirements

### Requirement: Explicit bounded observation launch
The launcher SHALL start the read-only listener before requesting game launch,
provide terminal output and local logs, and enforce connection, sample and total
duration limits without monitor capture or synthetic keyboard/mouse input.

#### Scenario: Launch an approved closed game
- **WHEN** the installation and deployed observer match preflight checks
- **THEN** the in-process listener is bound before isaac-ng.exe is started with
  temporary --luadebug and actual readiness is reported only by the handshake

#### Scenario: Installation or deployment is unsuitable
- **WHEN** the game or project Python is missing, deployed hashes differ, or a game is running
- **THEN** the launcher fails before launching either observer or game and changes no game files

### Requirement: Owned process and log lifecycle
The launcher SHALL persist observer output only in ignored local run storage and
close its owned observer resources on completion, failure, deadline or interruption.
It MUST NOT terminate the game or modify saves, mods, Cloud or persistent options.

#### Scenario: Port conflict or listener startup failure
- **WHEN** the observer cannot bind or exits before listener readiness
- **THEN** game launch is not requested and the script exits with an error

#### Scenario: End an observation session
- **WHEN** the sample budget, deadline, user interruption or observer fault ends the session
- **THEN** observer resources are released and the game is left for normal user exit

### Requirement: Bounded reconnection across user-managed runs
Transport failures SHALL allow a bounded configurable number of fresh handshakes
within the original session duration and sample budget. The launcher MUST NOT
infer character death from disconnection, automatically restart a run, or retry
malformed/incompatible protocol data. Default reconnect budget SHALL be three,
configurable from zero to ten.

#### Scenario: User ends a run and continues another
- **WHEN** Lua closes its peer and the reconnect budget is available
- **THEN** the terminal reports reconnection with unknown gameplay outcome,
  waits for a new session and continues counting validated samples

#### Scenario: Retry budget exhausted or protocol invalid
- **WHEN** reconnect attempts are exhausted or the peer violates the protocol
- **THEN** observation fails explicitly and closes sockets without terminating the game

### Requirement: Honest save-file selection status
The launcher MUST display file 2 as the requested target and state that automatic
selection and slot identity verification are unavailable in this increment.

#### Scenario: User starts the observation launcher
- **WHEN** preflight succeeds
- **THEN** the terminal asks the user to select file 2 manually and does not claim
  isolation, achievement eligibility, autonomous gameplay or Dead God completion
