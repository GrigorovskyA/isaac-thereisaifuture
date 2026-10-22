# Development guide

## 1. Two separate learning processes

Codex develops the software: mod, transport, environment, training, and validation.
The RL model learns to play within that software. Good code does not establish
learning; high reward does not establish a correct integration. Each milestone
must deliver an observable vertical result. All project work is written in English.

Start with `docs/STATUS.md`, not PPO against a nonexistent Isaac environment.
Do not add dozens of empty modules for anticipated features.

## 2. Setup and working commands

Run PowerShell from the project root. Explicit `.venv/Scripts/python.exe` paths
avoid confusion between Store Python, system Python, and the Codex runtime.
If supplying your own interpreter, use CPython 3.12 x64.

```powershell
.\scripts\Bootstrap.ps1 -PythonExe 'C:\path\to\Python312\python.exe'
.\scripts\OpenSpec.ps1 --version
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli doctor
.\scripts\Check.ps1
.\scripts\Smoke-RL.ps1
```

Do not recreate a working environment for every task. `Check.ps1` runs offline
checks and does not install or control the game. `Smoke-RL.ps1` trains for 16 steps
in a small synthetic environment, saves a checkpoint, and reloads it. This checks
library compatibility and the MultiDiscrete/LSTM path, not Isaac performance.

A global `openspec` command is unnecessary. `OpenSpec.ps1` runs the pinned local
version and temporarily points XDG configuration to `.tooling`. It restores the
original environment variables afterward. The project profile includes verify;
global profiles are unaffected. OpenSpec artifact language is English.

Typical Python checks:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests scripts/smoke_rl.py
.\.venv\Scripts\python.exe -m ruff format src tests scripts/smoke_rl.py
.\.venv\Scripts\python.exe -m mypy
.\.venv\Scripts\python.exe -m pytest -m 'not game'
```

## 3. Choosing the next task

Read STATUS, the roadmap, active changes, and Git diff. Choose the smallest task
that resolves the next uncertainty. Receiving player position is more useful
initially than building a universal RL framework.

Before implementation, define:

- The observable behavior and its trigger.
- Required external game versions and capabilities.
- The offline test establishing internal correctness.
- The real-game scenario establishing integration.
- How to stop the test, release input, and clean up its artifacts.
- Explicit non-goals for this change.

Do not combine a new protocol, reward design, CUDA migration, and item strategy in
one change. If validation depends on a missing component, implement that dependency
first or explicitly scope the task to an offline contract.

## 4. OpenSpec workflow

Use skills in Codex chat and the CLI in PowerShell. Read installed skills in
`.agents/skills`. Clarify genuinely missing requirements; do not request repeated
approval for each step of an already authorized task.

```text
$openspec-propose audit-game-compatibility
```

After drafting proposal, specifications, design, and tasks:

```powershell
.\scripts\OpenSpec.ps1 list
.\scripts\OpenSpec.ps1 status --change audit-game-compatibility
.\scripts\OpenSpec.ps1 validate audit-game-compatibility --strict
```

Then in chat:

```text
$openspec-apply-change audit-game-compatibility
$openspec-verify-change audit-game-compatibility
```

A capability name describes behavior, such as `game-bridge`; a change ID describes
an increment, such as `bridge-safe-actions`. Delta specifications add or modify
requirements with observable scenarios. Do not keep the architecture only in a
task checklist: current specifications must remain the source of truth after archival.

After implementation, run Check, targeted tests, required real-game checks, and a
diff review. Only then use `$openspec-archive-change`. Fix verification gaps rather
than marking unfinished tasks complete to archive them.

Baseline specifications describe required future behavior, not implemented game
support. The compatibility audit is complete; see COMPATIBILITY_AUDIT and STATUS.
The bridge-handshake-and-observation change is archived with read-only runtime
acceptance under a specifically authorized ordinary-profile exception. See its
evidence and OBSERVATION_PROTOCOL. That does not authorize actions, resets or
training, or establish automatic file-2 selection and training isolation.

## 5. Smallest path to a game MVP

**Read-only audit first.** Follow GAME_SETUP to identify versions and training-profile
isolation. Repentance and Repentance+ are not assumed interchangeable. Record bridge
commits and licenses. Present the user with concrete installations/settings actually
needed for the chosen approach.

**Then handshake.** Minimal Lua code sends version and frame information. Python
connects, reads a snapshot, and exits. Confirm that the snapshot follows the real
game rather than returning a constant placeholder.

**Then control.** Add one movement command, independent shooting, neutral actions,
and a watchdog. Reject stale or mismatched session IDs before application. Test
connection loss: the character must not keep moving after Python dies.

**Then episode lifecycle.** Add automatic reset on an approved profile, ending
events, counters, and time limits. Network failure must be reported as an
infrastructure fault rather than an artificial character death.

**Then Gymnasium.** Convert verified bridge state into observations/rewards and
policy actions into commands. Complete a step at its agreed game frame; a fixed
`sleep(0.1)` is not a synchronization contract. Run the checker and repeated episodes.

## 6. Python and Lua responsibilities

Lua owns game truth: API reads, events, approved action application, watchdog, and
local identities. Python owns validation, episode management, observation encoding,
reward accounting, learning, and metrics. Select callbacks and transport after the
audit; do not assume LuaSocket or speed-control APIs exist.

Use loopback transport with versioned, bounded messages, framing, timeouts,
heartbeat, and explicit errors. Do not serialize entire engine objects or accept
arbitrary executable Lua/shell commands over the protocol. Isolate the game adapter
from the RL algorithm so a bridge replacement does not require rewriting PPO.

ARCHITECTURE lists future modules as organizational guidance, not a requirement
to create every directory immediately.

## 7. Observations, actions, and rewards

Every feature specifies units, range, dtype, normalization, and provenance. Entity
tables have capacities and masks, with stable documented ordering. Never silently
drop the nearest dangerous projectile because an array is full.

Keep the initial action space small with independent movement and shooting.
Later bomb/active-item actions need edge-trigger semantics, cooldowns, and validity
rules. Define invalid-action behavior in a specification and keep train/inference
semantics identical.

Compute rewards from deduplicated events, not repeated UI states. Log components
separately. Initial configuration coefficients are engineering hypotheses from the
project discussion; later features remain disabled during combat MVP development.
Do not activate synergy rewards without a verifiable utility definition. See RL_DESIGN.

## 8. Training experiments

Before a run, create a manifest: run ID, Git revision/dirty status, config hash,
library and game/mod versions, scenario split, seeds, reward/observation/action
versions, device, budget, and parent checkpoint. Fix the checkpoint-selection rule.

Test one hypothesis per experiment, such as whether LSTM helps partial observability.
Use comparable scenarios and budgets. Start with an interface smoke, then bounded
training, then evaluation. Investigate transition/reward correctness before making
the model ten times larger.

Report clear rate, damage per room, progress, deaths, episode length, stuck rate,
steps/sec, fault rate, and reward components. Later add win rate, secret-room
success per bomb, and resource efficiency. Keep training reward beside gameplay
outcomes rather than hiding both inside a single quality score.

Checkpoints include the model, observation schema, normalizer, configuration, and
lineage. Exact resume may also need optimizer/RNG and engine state. If the engine
cannot be restored, begin a new episode and record the discontinuity. Reset LSTM
state at episode boundaries. Evaluation must not update normalization statistics.

## 9. Git and dependencies

Use small commits for accepted changes. Review the diff for saves, secrets, huge
dumps, and models. Do not add third-party code without license review. A remote
repository or publication is a separate user task.

Pyproject constraints define compatible versions. requirements-lock records the
verified Windows/Python 3.12 environment except CPU torch, which is pinned in
Bootstrap and installed first from the official CPU index. This snapshot is not
a cross-platform lock and does not contain cryptographic hashes.

After a deliberate update, resolve dependencies and run pip consistency, Check,
and Smoke-RL. Rebuild the lock from freeze without the editable project or torch,
and record reasons/versions in SETUP_REPORT. A fresh-environment check is useful
when installation changes, not after every text edit. Keep absolute local paths
out of dependency locks.

Update OpenSpec explicitly: package.json and pnpm-lock, wrapper `update`, generated
skill diff review, and strict validation. Do not upgrade on every startup. Keep
English artifact generation configured after updates. For CUDA, use a separate
environment and compatible wheel/lock; verify actual torch GPU execution. Merely
running `nvidia-smi` does not establish GPU training.

## 10. Failures and recovery

On a hang, stop actions and preserve recent frame/episode IDs, process state, and
the error. Distinguish game, transport, Python, and policy failures. Do not turn a
timeout into a valid transition. After three attempts at the same root cause,
write a diagnostic note and stop that approach.

If pip/ensurepip fails, check the actual interpreter and `.venv`/TEMP permissions.
When execution permissions block an action, use the supported escalation mechanism
if available. Do not repeat identical commands indefinitely or delete user Python
profiles to repair this project.

## 11. Completing a work session

Update STATUS with the active change, completed work, exact checks/results,
blockers, and next action. Use the evidence template. A separate review pass by
the implementing agent is a self-review, not an independent reviewer. Mark roadmap
items complete only when their acceptance criteria hold. A restarted session must
be able to continue from these files without the user retelling the entire history.

## Orchestrator and executor workflow

The user explicitly selected a primary Windows orchestrator and remote executor.
Follow AGENT_WORKFLOW.md: tasks in subagent.md, compact executor state in
agent-status.json and details in named reports. Poll once per minute; avoid
rereading unchanged reports. The primary reviews and runs Windows checks before
committing. Game, isolation, lease and reset limits remain unchanged.
