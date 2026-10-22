# Script execution authorization (user request, 2026-10-20)

The current script-runner delegation section in AGENTS.md takes precedence over
older workflow text below: the primary may use one bounded `gpt-6-luna` / `high`
subagent for offline tests, real-game checks and bounded training through prepared
commands. The primary defines experiments/budgets, implements code and verifies
logs, checkpoints and cleanup. The worker may perform Steam launch, file2 menu
selection, structured-bridge execution and normal shutdown within its assignment.
See [command inventory and handoff](SCRIPT_RUNNER.md). This does not reactivate
the file bus or grant code changes, Git writes, nested delegation or scheduled
supervision. Older primary-only runtime ownership below is superseded in this scope.

# Earlier development workflow: file bus (user request, 2026-10-19)

This section supersedes every earlier mode below. Two low-cost coordinator agents
talk through files in the shared SMB checkout; the expensive work runs in a fresh
Mac subagent per task. Nobody polls with an LLM: each coordinator blocks in a
shell wait script and only spends a model turn when the partner file changed.

| Role | Where | Model | Owns |
| --- | --- | --- | --- |
| Windows coordinator | Codex on Windows | cheap (e.g. luna high) | subagent.md, Check.ps1, game launch/training, Git, STATUS/ROADMAP, acceptance |
| Mac coordinator | Copilot CLI on macOS | cheap (e.g. luna high) | agent-status.json, subagent_report.md, spawning the worker |
| Worker | Mac subagent, fresh per task | claude-sonnet-5.5 | code, tests, log analysis, evidence report |

Loop:

1. Windows writes one task (or feedback) to `subagent.md`: task ID, goal, allowed
   writes, acceptance checks, logs to analyse.
2. Mac waits with `scripts/wait-change.sh subagent.md 3600`, reads the task,
   publishes `working`, runs one worker subagent with the full task text, checks
   the worker's evidence briefly (scope, tests run, no silent failures), prepends
   a summary to `subagent_report.md` and publishes `ready_for_review`,
   `needs_input` or `blocked`.
3. Windows waits with
   `./scripts/Wait-Change.ps1 -Path agent-status.json -States 'ready_for_review|needs_input|blocked'`,
   then runs `./scripts/Check.ps1` and, when the task needs it, launches Isaac via
   Steam, enters file 2 / Continue and runs the bounded game check or training
   session (see the AGENTS.md autonomy authorization). It records results, commits
   accepted work and writes the next task or feedback to `subagent.md`.
4. A wait timeout (exit 2) just repeats the wait. After three timeouts in a row the
   coordinator records `blocked` (Mac) or a note in STATUS (Windows) and stops.

Rules: acceptance is decided by Check.ps1, real-game evidence and logs, not by a
coordinator's opinion. One task at a time; the Mac never commits, pushes or
launches the game; the Windows side never edits the worker's files while the
status is `working`. Restart a coordinator session about once a day; state lives in
files, not in chat history. Status format: see the historical section below.

## Coordinator prompts

Mac (paste into Copilot CLI, cheap model selected with /model):

> You are the Mac coordinator for isaac-threrisaifuture (docs/AGENT_WORKFLOW.md,
> file bus). Loop: run `scripts/wait-change.sh subagent.md 3600` as an async shell
> and end your turn until it completes. On change, read subagent.md; if it holds
> a new task or feedback, publish agent-status.json `working`, then launch ONE
> general-purpose subagent with model claude-sonnet-5.5 and the full task text,
> AGENTS.md rules and the required report path. Review its result briefly
> (allowed writes respected, tests and exit codes reported), prepend the summary
> to subagent_report.md and publish the final state atomically. Do not write code
> yourself, commit, push or launch the game. Then wait again.

Windows (paste into Codex, cheap model):

> You are the Windows coordinator for isaac-threrisaifuture (docs/AGENT_WORKFLOW.md,
> file bus, AGENTS.md autonomy authorization). Pick the next roadmap step, write
> one bounded task to subagent.md, then run
> `./scripts/Wait-Change.ps1 -Path agent-status.json -States 'ready_for_review|needs_input|blocked'`.
> On ready_for_review run ./scripts/Check.ps1 and any required game check or
> bounded training session yourself (Steam launch, file 2 / Continue by menu keys).
> Accept and commit on evidence, or write feedback. Answer needs_input questions
> within the authorization or escalate to the user. Keep messages short.

# Earlier workflow notes (historical)

Current superseding mode (2026-10-19): at the user's request the primary Windows
agent took over the delivered async-regression diff and implemented windows-gate-
ipc. All executor write authority is closed; no new delegation or monitor is
active. Windows quality gate now passes 1451 tests, zero skips/xfails, strict
OpenSpec 30/30. Primary owns review, Git and any separately authorized runtime
preparation. Older assignments and blocked-state notes below are historical.

Current superseding task: async-restart-training-regression-20261019-01,
explicitly requested by the user as one sequential multi-stage offline assignment.
Follow subagent.md exclusively for allowed writes and stages. Earlier tasks are
closed; their status is historical. Primary owns Windows review, acceptance,
STATUS/ROADMAP, commits and any future runtime decision. Synthetic learner tests
are permitted in disposable test fixtures; no actual Isaac training, production
fix, deployment, approval, monitor resumption or nested delegation is authorized.

Current superseding task: restart-authority-diagnostics-20261018-01, explicitly
requested by the user after the diagnostic plan. One manually launched executor
has delivered the accepted offline implementation after feedback 1; executor
write authority is closed. Runtime acceptance remains unfinished. Older assignments below
are closed historical records. The primary owns review, STATUS, ROADMAP, Windows
acceptance, commits/pushes and runtime work. No monitor resumption, additional
delegation, game access or authorization change is implied. Match the new task
ID in fresh status and report; the prior ready_for_review status is stale.

Current assignment: combat-experience-gate-20261018-01. User-requested offline
executor scope is defined in subagent.md; all prior assignments are closed.
Primary review and Windows checks precede acceptance. No runtime authority,
automatic monitoring or successor task is implied.

Current superseding assignment: frozen-live-runner-20261018-01. The user requested
the next manually launched offline executor task. Follow only subagent.md's
allowed writes; frozen-policy-evaluation is accepted and closed. Primary review
and Windows checks precede acceptance. No runtime authority or heartbeat restart.

Current 2026-10-18 exception: the user requested one manually launched executor
assignment, frozen-policy-evaluation-20261018-01. Only the explicit offline writes
in subagent.md are authorized. The primary owns runtime work, review, STATUS,
roadmap, commits and pushes. No live evaluation, training, heartbeat or additional
delegation is granted. Earlier assignments below are closed historical records.

2026-10-18 exception: the user requested the bounded external executor assignment
lua-step-evidence-20261018-01 and will launch it manually. The previous
later-frame-hp-20261018-01 and native-step-lifecycle-20261018-01 tasks are accepted
and closed. subagent.md defines the new task's
only current authority and allowed writes. The executor returns a named evidence
report and task-matched agent-status.json; the primary reviews actual diffs and
runs Windows checks before accepting, committing or pushing. No heartbeat restart,
automatic monitoring, successor assignment or runtime authority is granted.
The earlier cancellation below remains applicable to every other assignment.

On 2026-10-17 the user stopped the remote executor and asked the primary Windows
agent to continue alone. The isaac-remote-handoff heartbeat is PAUSED (verified).
Do not dispatch tasks, spawn agents or reactivate that automation without a new
user request. subagent.md cancels prior assignments; agent-status.json is retained
as historical ignored runtime state, not current progress or execution authority.

The primary owns implementation, self-review, Windows checks, evidence, OpenSpec,
commits and pushes. Preserve unrelated edits and private-file exclusions. Current
runtime permissions, manual game launch/save selection, action expiry and reset
limits are unchanged. Do not infer training isolation from file 2 or ordinary-
profile bounded-action permission.

The historical file-handoff procedure below explains earlier reports only; it is
inactive and grants no continuing executor authority.

# Historical file-based agent workflow

The user explicitly appointed the primary Windows agent as orchestrator and the
remote agent as executor on 2026-10-17. This coordinates development only; it
never removes game authorization, isolation, input-expiry or reset limits.

- Orchestrator owns subagent.md: one current task with a unique task ID, frozen
  inputs, allowed writes, acceptance checks and review feedback. No two tasks
  write the same files concurrently. No nested agents.
- Executor owns agent-status.json: schema_version 1, task_id, state, updated_at,
  short summary, result_path and optional question. Use non-dot-prefixed temp
  filenames over SMB; never mark shared outputs Hidden/ReadOnly. States: assigned, working,
  ready_for_review, needs_input, blocked. Use English and atomic replacement.
- Detailed results live at the task's named report path, with actual commands,
  exit codes and not_run checks. Do not copy source or raw logs into status.
- Read the small status and task-file header/mtime every minute. Read the full
  task only on changed task ID, modified feedback or a pending question; inspect
  reports/diffs only for a question or ready_for_review.
  Unchanged status needs no reply or user notification. Status timestamps are
  liveness hints, not proof of completion; verify file/task identity and code.
- Commit an accepted batch before issuing a successor that edits its files.
  Do not silently change a frozen task mid-execution; version review corrections.
- Orchestrator runs Windows tests and OpenSpec strict validation, records review,
  marks tasks complete only after evidence, commits and pushes accepted changes.
  New task IDs supersede old status; stale results never complete a new task.
- Existing standing ordinary-profile observation/bounded action permissions remain.
  Manual game launch/slot selection, verified training isolation for repeated
  episodes, private-data exclusions and all action/reset budgets remain required.
  Executor never controls/deploys the game, edits saves/Cloud, starts training,
  installs dependencies, commits, pushes or archives without a separate task.

The app heartbeat checks the status once per minute in the same thread. It stays
quiet during routine progress and reports meaningful results or required human
input. It is not a game supervisor and does not launch a second game or agent.
