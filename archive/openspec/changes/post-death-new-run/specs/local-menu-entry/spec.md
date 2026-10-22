## ADDED Requirements

### Requirement: Explicit post-death New Run
Automatic file2 New Run SHALL require explicit mode selection and fresh affirmative
evidence that the selected file2 has no saved Continue. It MUST refuse an available
or unverified Continue rather than overwrite it. The existing local input guards
and eight-key,60s menu,2MiB log bounds SHALL also apply to New Run.

#### Scenario: File2 has no Continue
- **WHEN** explicit new-run mode and fresh selected-slot missing-game evidence are present
- **THEN** the controller confirms New Run and the default character,stops keys on run start and requires native [New,2] plus an active Isaac snapshot for readiness

#### Scenario: Existing run or unknown absence
- **WHEN** file2 has a loaded game state or absence cannot be affirmatively established
- **THEN** no New Run confirmation is sent and the command fails without fallback

### Requirement: New Run character readiness
New-run readiness SHALL require player.character_type0 from an active validated
bridge snapshot after verified native New,file2 entry. Other characters MUST fail
before readiness or gameplay control. Temporary unavailable snapshots MAY be
awaited within the original duration budget. New Run MUST NOT initialize or reset
a training model,normalizer,checkpoint or approval.

#### Scenario: Load boundary then Isaac
- **WHEN** unavailable load snapshots precede an active Isaac snapshot within budget
- **THEN** only the active Isaac snapshot satisfies the agent readiness sample

#### Scenario: Another character starts
- **WHEN** an active snapshot identifies a character other than0
- **THEN** report failure and close observation resources without further keys or gameplay actions
