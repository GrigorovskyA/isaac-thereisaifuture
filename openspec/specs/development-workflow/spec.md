# development-workflow Specification

## Purpose

Define sequential single-agent development with verifiable results. Process
requirements do not imply that game integration has been completed.

## Requirements

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

### Requirement: English project language
All project artifacts MUST use English, including documentation, agent instructions,
specifications, code, comments, configuration descriptions, CLI output, reports,
examples, and future interface text.

#### Scenario: Create or update a project artifact
- **WHEN** a contributor or agent creates or modifies project content
- **THEN** the content is written in English and OpenSpec generation remains
  configured for English, regardless of the language used in the conversation

### Requirement: Evidence before archival
The agent MUST archive a change only after its acceptance checks are complete and
evidence distinguishes offline, real-game, and RL evaluation results.

#### Scenario: Game integration has only mock tests
- **WHEN** offline tests pass but a required game run is blocked
- **THEN** the integration criterion remains incomplete and the change is not
  archived as completed game integration

### Requirement: Durable handoff
The agent SHALL record current state, check results, blockers, and the next action
in docs/STATUS.md before ending a work session.

#### Scenario: Session ends after a partial change
- **WHEN** implementation is incomplete
- **THEN** STATUS identifies the active change, completed work, and concrete continuation

### Requirement: Isolated development dependencies
The project SHALL use local Node dependencies and a separate Python environment,
record verified versions, and avoid requiring global OpenSpec profile changes.

#### Scenario: Run project OpenSpec
- **WHEN** the user invokes scripts/OpenSpec.ps1
- **THEN** it uses the local version and project profile including verify and
  restores the original environment variables afterward

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
