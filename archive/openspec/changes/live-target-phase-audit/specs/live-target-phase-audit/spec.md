## Purpose

Collect bounded local facts about potentially vulnerable phases and actual exported
membership without changing the live policy,oracle wire,gate,reward or game state.

## ADDED Requirements

### Requirement: Explicit local phase audit
Only literal true configuration and an active live connection SHALL enable target
phase diagnostics. Disabled diagnostics MUST perform no extra entity API reads.
Facts SHALL remain in the local game log and MUST NOT enter wire messages,policy
observations,normalization,model state or reward events. Diagnostics MUST be read-only.

#### Scenario: Default mode
- **WHEN** diagnostics are false or a truthy nonboolean value
- **THEN** no audit API read or audit line occurs and previous capture output is preserved

#### Scenario: Vulnerable entity excluded from export
- **WHEN** a candidate is vulnerable but fails normal export filters
- **THEN** log its raw flags,type/variant,HP and position plus actual policy/oracle inclusion without inserting it into either list

### Requirement: Finite and failure-isolated audit
One nonrenewable window per mod load SHALL last at most120s,emit at most512 lines
of at most800 characters,retain at most128 labels and inspect at most64 entities
per sample,no faster than10Hz. Changes and disappearance MAY be logged; absence
MUST NOT be called death. Budget exhaustion or an API/log failure MUST stop only
diagnostics without changing normal capture,actions,release or authority.

#### Scenario: Resource exhaustion
- **WHEN** time,line,label or scan limits are reached
- **THEN** diagnostics stop without renewing on reconnect or changing the game

#### Scenario: Missing or failing API
- **WHEN** an audit-only API fails
- **THEN** diagnostics stop and normal capture proceeds unchanged

### Requirement: Provenance and membership correlation
Each audit line SHALL name session,epoch,visit,frame and a bounded local lifetime
label. Candidate records MUST distinguish observed engine facts from exact
post-cap exported membership. Position MUST NOT trigger an unbounded change log.
Raw pointers/seeds MUST NOT be exposed. An unobserved native phase stays pending.
#### Scenario: Same identity changes phase
- **WHEN** one sampled lifetime changes flags or HP
- **THEN** retain its local label and compare its actual exported membership with the raw facts

### Requirement: Target phase candidate selection
NPCs and entities marked enemy or vulnerable SHALL always be diagnostic candidates.
Other effects SHALL require literal true target_phase_passive_effects configuration,
default false;this diagnostic selection MUST NOT change policy/oracle exports.
An available NPC champion-color index SHALL be logged locally and MUST NOT enter
wire/model input;an unavailable champion API MUST NOT prevent other phase records.

#### Scenario: Passive visual effects churn
- **WHEN** many non-NPC,non-enemy,non-vulnerable effects appear in default diagnostic mode
- **THEN** they consume no lifetime labels and subsequent NPC phase changes remain observable within the original finite budget

#### Scenario: Champion modifier observed
- **WHEN** an NPC provides a champion-color index
- **THEN** record it as raw local evidence rather than inferring it from HP or color,and preserve diagnostic operation when the optional method is missing
