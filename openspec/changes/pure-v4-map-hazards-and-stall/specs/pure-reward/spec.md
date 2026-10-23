## ADDED Requirements

### Requirement: Reward v5 stall restart
Reward v5 SHALL charge -10 for a stall restart, equal to the death penalty, and SHALL
keep all other reward v4 terms unchanged.

#### Scenario: Stall truncation
- **WHEN** an episode is truncated by the stall watchdog
- **THEN** the stall column is -10 once and no death penalty is paid
