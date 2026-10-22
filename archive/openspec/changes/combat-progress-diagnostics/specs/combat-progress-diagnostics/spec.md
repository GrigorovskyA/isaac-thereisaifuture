## ADDED Requirements

### Requirement: Bounded separate combat evidence
The combat gate SHALL optionally capture versioned policy vectors and selected
actions with matching same-frame raw snapshots in a separate oracle file, with
explicit byte bounds, record identities and missing weapon-range metadata.

#### Scenario: Combat transition capture
- **WHEN** a diagnostic-enabled gated combat action returns
- **THEN** before/after vectors match the recorded raw entity frame encoding
- **AND** oracle data never enters learner observations or info
- **AND** waiting/navigation samples are not written as learner transitions

#### Scenario: Capture capacity exhausted
- **WHEN** the next pair would exceed the combined byte cap
- **THEN** the cap is not exceeded and the run stops before another action
- **AND** existing evidence is not overwritten or silently declared complete

### Requirement: Conservative persistent progress window
An explicitly configured monitor SHALL accumulate only eligible same-visit combat
action frame deltas without registered conservative HP-floor damage or a clear.
Software resets SHALL NOT renew the window or historical HP allowance.

#### Scenario: Stuck room across software resets
- **WHEN** software episodes end in the same native visit without registered progress
- **THEN** their observed combat deltas accumulate toward one window
- **AND** expiry stops before another gameplay action with a distinct reason
- **AND** the last real transition is retained without fabricated death or clear

#### Scenario: Healing and disappearance
- **WHEN** an enemy heals, disappears, reappears or an overflow obscures continuity
- **THEN** those changes alone do not count as damage or kills
- **AND** only damage below the conservative historical HP floor resets the window

#### Scenario: New room or management time
- **WHEN** a native visit changes or the gate waits for combat
- **THEN** a new visit starts a new window and management time adds no combat deltas

### Requirement: Explicit unchanged learning contract
Live and finite-session interfaces SHALL validate and record diagnostic byte caps
and optional progress windows, default off, without changing policy/reward schemas.

#### Scenario: Disabled or invalid options
- **WHEN** options are omitted
- **THEN** existing learning behavior is unchanged
- **WHEN** a progress window is invalid or combat options lack the gate
- **THEN** validation rejects the request before game actions
