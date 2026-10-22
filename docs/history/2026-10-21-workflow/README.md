# isaac-threrisaifuture

A self-learning RL agent for **The Binding of Isaac: Repentance+ (Steam, Windows)**.
The goal is to watch an initially inexperienced agent learn to survive, clear
rooms and floors, manage resources, and develop a strategy for complete runs.
The final user goal is **Dead God on save file 2**, earned through gameplay.
The intended interface is one script that opens terminal logs, launches the game
and connects the structured Lua/Python bridge without screen capture. Local menu-only
keyboard input is allowed; gameplay stays on the structured bridge. See
[launcher](docs/LAUNCHER.md) and [progression goal and limits](docs/PROGRESSION_GOAL.md).

The exact project name is `isaac-threrisaifuture`. The Python package is
`isaac_threrisaifuture`; the diagnostic command is `isaac-future`.

Finite training orchestration now has a [versioned runner](docs/TRAINING_SESSION.md)
with offline deadline/status/cleanup checks. Native five-minute qualification is
pending; the stopped overnight experiment remains suspended.

Repository: [GrigorovskyA/isaac-thereisaifuture](https://github.com/GrigorovskyA/isaac-thereisaifuture).
The repository slug differs from the project name specified above.

## Local Windows checkout

The active local project is `D:\isaac` (moved on 2026-10-17). Run project commands
from that directory. The earlier Documents checkout path is a compatibility
junction to this directory; preserve it because existing shortcuts and Node
package junctions still use that alias. A separate pre-move rollback copy was
retained locally. See [migration evidence](reports/2026-10-17-project-relocation.md).

## Current status

Latest accepted result (2026-10-18): observer 0.5.0-dev is installed. Real-game
random integration completed with operator-assisted room navigation, native
movement/shooting and a natural death followed by automatic restart/reconnect.
A short 256-step RecurrentPPO run saved a model and normalizer; offline reload
passed. The live-training-loop change is archived. This proves a working pipeline,
not improved play or autonomous navigation. See
[checkpoint evidence](reports/2026-10-18-live-training-checkpoint.md) and STATUS.
The detailed observations below describe earlier milestones.

This repository provides the development foundation and a minimal read-only
Lua/Python observation bridge with offline tests. A user-authorized read-only
probe captured real handshakes and a 3000-snapshot, approximately ten-minute read
with one recovered timeout. Script launch and controlled reconnection worked;
the user confirmed no visible hangs and retained manual control. **Read-only
acceptance passed for the recorded profile.** Bounded movement/shooting passed **50/50 real controlled sequences** under
the explicit ordinary-profile test exception, including failure cleanup; see
[runtime evidence](reports/2026-10-17-safe-actions-runtime.md). The action gate
is disabled by default. Later environment/training modules are offline contracts;
an Isaac-connected Gymnasium backend and trained Isaac model remain unverified.
Offline checks alone do not establish real-game acceptance for later milestones.
Item 04 is now accepted: observer 0.4.0 exported 250 real entity frames, including
all four native kinds over eight room visits; recorded fixture replay passed.
See [entity protocol](docs/ENTITY_OBSERVATION_PROTOCOL.md) and
[evidence](reports/2026-10-17-entity-observation-v1.md). Latest checks: 1224 tests,
no skips; strict OpenSpec 25/25. Native episode/Gymnasium integration is next. Installed/source observer is
0.4.5-dev (later-frame HP diagnostics verified narrowly in manual combat)
with diagnostics inactive by default. One live callback-order pulse passed;
Closed-game 0.4.5-dev deployment has matching hashes and passed launcher preflight;
see [deployment evidence](reports/2026-10-18-later-frame-hp-deployment.md).
A bounded 0.4.5-dev run captured 593 snapshots, 197 later records and 16 explicit
removed facts; 87 diagnostic windows showed changed later HP. This is raw timing
evidence, not applied-damage or step acceptance. See
[later-frame runtime evidence](reports/2026-10-18-later-frame-hp-runtime.md).
A pragmatic [live training loop](docs/LIVE_LOOP.md) (source 0.5.0-dev, offline-verified only) runs random or RecurrentPPO play on file 2 with autonomous death restarts via `Start-Live.cmd`.
Exact native step completion and outcome events remain unfinished. See [callback probe procedure](docs/CALLBACK_TRACE_PROBE.md) and the offline [step evidence hooks](docs/NATIVE_STEP_EVIDENCE.md) (source 0.4.6-dev, not installed).
The passive [oracle probe](docs/ORACLE_PROBE.md) passed live attach/read/stop;
its outcome-ordering scenarios remain unverified. A separate entity recording
covered 21 room visits; diagnostics were restored OFF after manual exit. See
[partial runtime evidence](reports/2026-10-18-oracle-probe-runtime.md).
Diagnostics now use `observe --oracle-probe --samples 600` on the same installed
mod, without replacing files per test. The new negotiated activation passed
offline checks and live explicit activation on 0.4.4-dev. The first post-update
sample can still precede changed HP; it is not an applied-damage barrier. The
latest recording ended early after logged game over/run exit. See
[runtime evidence](reports/2026-10-18-post-update-hp-runtime.md) and
[procedure](docs/ORACLE_PROBE.md).
The accepted follow-up implements an explicitly opted-in, bounded restart after
game over. [Death-restart guide](docs/DEATH_RESTART.md): initial launch and file-2
selection stay manual. One real natural-death restart passed on J460 as character
type 0, with manual control retained after observer shutdown.

See the [setup report](docs/SETUP_REPORT.md) for the verified installation results.

The [compatibility audit](docs/COMPATIBILITY_AUDIT.md) is complete (2026-10-17).
Steam Repentance+ v1.9.7.17.J460 / build 22878971 is installed. The recommendation
is a minimal original observation adapter using bundled LuaSocket; item 02 is
archived with real-game evidence. Training-profile isolation remains open. See
[observation protocol and commands](docs/OBSERVATION_PROTOCOL.md) and STATUS.

Development currently uses one Windows agent working sequentially through
OpenSpec. The user stopped the external executor; its handoff heartbeat is
paused. See [agent workflow](docs/AGENT_WORKFLOW.md).

**The entire project uses English:** documentation, specifications, code, comments,
configuration descriptions, reports, CLI output, and future interface text.

## Target capabilities

- Receive structured game state through a Lua mod and local Python bridge.
- Move and shoot independently, dodge threats, and use supported abilities.
- Explore the known map, choose doors, and progress through floors and bosses.
- Make decisions about bombs, keys, coins, shops, and deals.
- Use reference knowledge about items and interactions while learning their value
  for the current build and situation.
- Find secret rooms using player-visible evidence rather than hidden map data.
- Save checkpoints and metrics; watch a selected model in spectator mode.
- Compare new and old models on separate evaluation scenarios.

The first learning task is combat in a limited room set. Full runs are a final
milestone, not the acceptance criterion for the first prototype. This is an
experimental RL project; completion dates and win rates are not guaranteed.

## Stack and initial decisions

| Area | Decision |
|---|---|
| Platform | Native Windows; one Steam Repentance+ instance initially |
| Development | One Windows agent, OpenSpec, Git, PowerShell |
| Python | Python 3.12 in a separate `.venv` |
| RL | PyTorch, Gymnasium, Stable-Baselines3, sb3-contrib/RecurrentPPO |
| Game communication | Lua and local transport; bridge selected after compatibility audit |
| Observations | Structured features; pixel learning is outside the first MVP |
| Metrics | JSONL and TensorBoard; SQLite if needed later |
| Checks | Ruff, mypy, pytest, and separate real-game checks |

PyTorch is initially installed with its CPU backend, suitable for the small initial
model. CUDA selection follows measurements. An RTX 4070 was detected, but this
installation does not enable GPU training. Do not install CUDA Toolkit or update
drivers without an identified need.

## Quick start in PowerShell

For a bounded **observation session**, double-click `Start-Isaac.cmd` at the
repository root after normally exiting any already-running game. It uses project
Python directly, opens terminal logs, checks the installed observer hashes, binds
the listener, then launches Isaac with temporary `--luadebug`. No PowerShell
execution-policy change, monitor capture or automatic mod deployment is required.
Select **file 2 manually**: automatic selection is not implemented or verified.
This does not start training or verify achievement eligibility. See the
[launcher guide](docs/LAUNCHER.md) for budgets, logs, preflight and limitations.

Run the following commands **from this repository's root**:

```powershell
Set-Location '<project-path>\isaac-threrisaifuture'
.\scripts\Check.ps1
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli doctor
.\scripts\OpenSpec.ps1 list
```

Virtualenv activation is unnecessary. If Windows blocks `.ps1` execution, use the
PowerShell execution method permitted on your system; do not change system-wide
execution policy just for this project. The explicit Python command above requires
no activation.

### Installing on another computer

Prerequisites are Git, Node.js **20.19+**, and official CPython **3.12 x64**.
A standard Node installation includes npm; the current Codex environment provides pnpm.

```powershell
.\scripts\Bootstrap.ps1
.\scripts\OpenSpec.ps1 init --tools codex --profile custom --language English --no-animation
.\scripts\Check.ps1
```

`Bootstrap.ps1` creates `.venv`, installs CPU PyTorch and pinned Python dependencies,
and installs local OpenSpec. It does not install Steam, the game, REPENTOGON, or Lua
mods. See the development guide for deliberate dependency updates.

OpenSpec is installed **locally**, not as a system command. Use
`.\scripts\OpenSpec.ps1 ...`; the wrapper also selects the project profile including
`verify`. There is no need for a second global installation or changes to other projects.

## Working with Codex

Open this directory as the Codex project, or run `codex` from its root. Project
instructions are in [AGENTS.md](AGENTS.md); OpenSpec skills are in `.agents/skills/`.
Refresh or restart the session if needed for skill discovery.

Current active change: `bridge-safe-actions`; see [protocol](docs/SAFE_ACTIONS.md)
and [latest authorization/deployment evidence](reports/2026-10-17-ordinary-profile-action-authorization.md).
Adapter 0.3.1 is installed with verified hashes/preflight. The user approved
bounded ordinary-profile movement/shooting tests; current manual slot/room
confirmation and actual live evidence remain pending. A private expiring approval
and 120-second action lease keep each test finite. Launch/selection stay manual.

Suggested next task:

```text
Read AGENTS.md, README.md, ROADMAP.md, docs/DEVELOPMENT_GUIDE.md, and docs/STATUS.md.
Keep the entire project in English.
Work as one agent without an orchestrator or subagents.
Review the archived bridge-handshake-and-observation evidence; do not reimplement it.
Verify the observer-only mod profile, research non-visual save-file-2 selection,
and resolve approved training isolation and instance/slot evidence before live player control.
Continue the active bridge-safe-actions change; do not repeat completed observer/restart work.
Keep game changes gated on the authorization for the specific profile and action.
Use small changes with measurable acceptance criteria.
Report offline results separately from real-game checks.
Update STATUS.md and the evidence report; never claim game support from mock tests.
```

Enter these skills **in Codex chat**, not in PowerShell:

```text
$openspec-propose
$openspec-apply-change
$openspec-verify-change
$openspec-archive-change
```

Run structural validation from PowerShell:

```powershell
.\scripts\OpenSpec.ps1 validate --all --strict
```

Validation checks specification artifacts. Software correctness and model quality
require their own tests and experiments.

## Repository map

```text
AGENTS.md                  Single-agent working instructions
README.md                  Entry point, installation, and commands
ROADMAP.md                 Milestones, dependencies, and acceptance criteria
docs/DEVELOPMENT_GUIDE.md   Practical engineering workflow
docs/ARCHITECTURE.md        Component boundaries and proposed game protocol
docs/RL_DESIGN.md           Observations, learning, rewards, and evaluation
docs/GAME_SETUP.md          Compatibility audit and game connection
docs/STATUS.md              Current handoff and next action
docs/SETUP_REPORT.md        Verified initial installation results
docs/SOURCES.md             Primary sources and research candidates
openspec/specs/            Baseline requirements
openspec/changes/          Active proposals and archives
.agents/skills/            Generated OpenSpec skills
.tooling/openspec/         Isolated OpenSpec profile
configs/                  Versioned experiment templates
scripts/                  Installation, OpenSpec, checks, and RL stack smoke
src/isaac_threrisaifuture/  Diagnostics, observation models and typed consumer
mod/                      Read-only Lua observer artifacts
tests/                    Offline tests and future game tests
reports/                  Short reports and evidence template
```

## Data and saves

User game saves are not training data. Before controlled game testing, establish
an isolated training profile and a verified restoration procedure. Discover actual
paths on this computer rather than guessing from online examples. Changes to saves,
Steam Cloud, or mod installation require specific authorization before the action.

Do not commit `.venv`, `node_modules`, raw game dumps, checkpoints, or large logs.
Every experiment records its configuration, seed, Git revision, and environment
versions. Check licenses and compatibility before using third-party code or data.

Start with [agent instructions](AGENTS.md), the [roadmap](ROADMAP.md), the
[development guide](docs/DEVELOPMENT_GUIDE.md), and [current status](docs/STATUS.md).
