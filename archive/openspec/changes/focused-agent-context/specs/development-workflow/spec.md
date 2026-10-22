# Spec Delta

## MODIFIED Requirements

### Requirement: Single-agent development
Development SHALL use one primary Codex agent responsible for implementation and
acceptance. The primary MAY use one prepared script worker at a time under current
user authorization. Workers MUST NOT edit source/tests/configuration, install
dependencies, write Git, spawn agents or expand their assignments.

#### Scenario: Start or resume work
- **WHEN** the primary starts or resumes a task
- **THEN** it reads short current STATUS and relevant Git state, loading additional
  roadmap/change/specification/source context only for the task

#### Scenario: Execute a prepared worker task
- **WHEN** substantial execution is delegated
- **THEN** one fresh Luna/high worker receives exact commands, identities, paths and
  finite caps without chat history, and primary verifies actual artifacts

#### Scenario: Requested worker model is unavailable
- **WHEN** the authorized model or effort cannot be used
- **THEN** primary reports the limitation and executes directly without substitution

## ADDED Requirements

### Requirement: Focused current context
Current instructions/status SHALL separate durable rules and current state from
history. Historical documents MUST NOT grant execution authority. Routine output
SHALL be bounded summaries with full logs retained locally.

#### Scenario: Answer a status question
- **WHEN** the user asks about project progress
- **THEN** the agent uses current STATUS and relevant evidence without mandatory
  reading of all guides, roadmap, historical reports or raw traces

#### Scenario: Recover an unfinished experiment
- **WHEN** an earlier runtime task ended without final acceptance
- **THEN** handoff identifies pending artifact verification without authorizing
  another launch, resume, New Run or longer duration

### Requirement: Read-only project context command
The project SHALL provide text/JSON context containing current STATUS and local
Git identity/state without reading models, approvals or raw logs or invoking
runtime, network or dependencies. STATUS above 12 KB MUST be refused. Git entries
MUST be capped at 30 with actual count and truncation flag.

#### Scenario: Invoke outside the checkout
- **WHEN** the helper is called from another working directory
- **THEN** it resolves the intended checkout from its own script location

#### Scenario: Context exceeds output bounds
- **WHEN** STATUS exceeds 12 KB or Git has more than 30 changed entries
- **THEN** oversized STATUS is refused and oversized Git output shows at most 30
  entries with actual count and truncation flag
