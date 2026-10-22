## ADDED Requirements

### Requirement: Unscored curriculum setup
An explicitly enabled curriculum setup SHALL keep its scripted actions and waits
outside learner samples, normalization, recurrent state and reward credit. It
MUST release input and obtain fresh combat and firing eligibility before handing
control to the learner. Setup metadata MUST NOT become policy input.

#### Scenario: Reach an exposed start
- **WHEN** setup reaches a settled position with a visible clear aligned in-range target
- **THEN** setup releases input and records its separate provenance
- **AND** the first learner observation and reward baseline come from fresh post-setup state
- **AND** setup contributes zero learner samples or normalization updates

#### Scenario: State changes during control transfer
- **WHEN** the room, target, weapon or combat eligibility changes before the first learner command
- **THEN** learning does not begin from the stale setup result
- **AND** the runner releases input and reports the failed handoff

#### Scenario: Visible enemies become ready after initial combat metadata
- **WHEN** all other entry checks pass and oracle combat is available but no enemy is yet visible
- **THEN** setup MAY wait without commands for at most 5 seconds and 100 snapshots, including the first, inside its original setup and shared deadlines
- **AND** it checks every observation for health loss and context, grid, weapon, door or oracle-membership changes
- **AND** once enemies are visible the same fixed target MUST pass before any movement; a wrong target, exhausted cap or changed state stops without retry

### Requirement: Setup and learning have explicit shared limits
Setup and learning SHALL share one fixed outer deadline with separate declared
phase caps. All progress, step, trace, disk and restart limits MUST be listed.
Setup failure MUST NOT trigger New Run, death reset, a changed target or a renewed
budget. Default modes MUST remain unchanged when this curriculum is disabled.

#### Scenario: Setup cannot converge
- **WHEN** the positioning cap or no-progress limit is exhausted
- **THEN** the run stops without learner actions or a fresh budget
- **AND** the report distinguishes setup failure from policy performance

#### Scenario: Death before automatic reset
- **WHEN** a death is observed in a zero-restart pilot
- **THEN** control stops before any reset or restart command
- **AND** the observed endpoint and any unfinished rollout are recorded honestly
