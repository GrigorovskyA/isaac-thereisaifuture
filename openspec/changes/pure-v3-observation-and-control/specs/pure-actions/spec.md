## ADDED Requirements

### Requirement: Slower decisions and use prior
Each decision SHALL hold 6 game updates. A newly created model SHALL start with
P(use=none)=0.85 and 0.05 for each press; learning MAY change these freely.

#### Scenario: Fresh model
- **WHEN** a pure-v3 model is created
- **THEN** its use-head probabilities on any observation are 0.85/0.05/0.05/0.05 within 1e-3
