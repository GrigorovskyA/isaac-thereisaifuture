## ADDED Requirements

### Requirement: External session deadline and cancellation
The live learner SHALL accept an optional fixed monotonic deadline and stop
signal. It MUST apply the earlier of its existing budget and that deadline to
startup identity checks, combat, handoffs and training, and release input on stop.
It SHALL report decisions and checkpoint activity without changing policy inputs.

#### Scenario: Startup used the remaining budget
- **WHEN** the external deadline expires before training begins
- **THEN** no training action is issued and the log records wall-time exhaustion

#### Scenario: Cooperative cancellation
- **WHEN** the session stop signal is set during a combat step or handoff
- **THEN** the learner exits through environment cleanup and records cancellation without a fabricated death or checkpoint
