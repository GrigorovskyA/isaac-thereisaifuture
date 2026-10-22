## ADDED Requirements

### Requirement: Bounded local file2 Continue
The agent launcher SHALL use local menu-only keys without screenshots or agent
desktop tools to enter file2 Continue. It MUST bind the bridge before Steam launch,
refuse an existing game,and enforce eight keys,60 seconds menu time and a 2MiB
native-log bound within the original session deadline. It MUST NOT silently start
a new run,reset a model,change saves/options or start training.

#### Scenario: Fresh file2 Continue
- **WHEN** fresh menu initialization and subsequent selected-slot metadata loads are observed
- **THEN** the controller selects file2 if necessary,issues Continue once and requires fresh [Continue,2] plus a validated bridge snapshot before success

#### Scenario: Initial scans or stale log
- **WHEN** a previous run marker or initial scans of all slots are present
- **THEN** they do not authorize Continue or successful readiness

#### Scenario: Unknown state or exhausted budget
- **WHEN** the expected log evidence is absent,oversized,ambiguous or past the key/time budget
- **THEN** input stops,resources close and no additional blind confirmation is sent

### Requirement: Verified menu input ownership
Every key-down SHALL require a single expected visible game window,matching
executable path,new process creation time and foreground identity. A foreground
refusal MUST stop input without bypass. Held input MUST be released on every path;
any run-start marker MUST stop further keyboard input even if its slot is wrong.

#### Scenario: Focus or identity fails
- **WHEN** focus cannot be obtained or the window/process identity changes
- **THEN** no key-down is sent and the launcher reports failure

#### Scenario: Gameplay begins during a press
- **WHEN** the fresh log reports any run start
- **THEN** the held key is released and no subsequent menu key is sent
