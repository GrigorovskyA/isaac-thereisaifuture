# isaac-threrisaifuture

A local self-learning RL player for Steam The Binding of Isaac: Repentance+ on
native Windows. The target is Dead God earned through gameplay on save file 2.
Codex builds the software; Python/RecurrentPPO learns through a structured Lua
bridge. No screen capture, imported completed saves or unlock commands substitute
for gameplay. All project artifacts are English.

## Current state

The native bridge, bounded actions, live RL/checkpoint pipeline and guarded
Continue/file2 launcher have recorded evidence. Geometry/freshness corrections
and a separate 723-input warm start are implemented. Native pilot acceptance is
pending; learned improvement and full autonomous runs are not established.
Read [current STATUS](docs/STATUS.md) for the exact active change, lineage and
next action. This README does not duplicate experiment receipts or grant training.

## Local commands

The working checkout is `D:\isaac`; Python 3.12 uses `.venv` without activation.
The earlier Documents path is a compatibility junction; preserve it.

```powershell
Set-Location D:\isaac
.\scripts\Get-ProjectContext.ps1             # read-only compact handoff
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli doctor
.\scripts\Check.ps1                         # full offline code gate
.\scripts\Smoke-RL.ps1                      # synthetic stack, not Isaac proof
.\scripts\OpenSpec.ps1 list
```

For an agreed game check, `Start-IsaacAgent.cmd --preflight-only` checks the shipped
entry point. Its default Continue mode uses Steam and guarded menu-only input;
gameplay stays on the bridge. It does not start learning. Explicit New Run is a
separate experiment decision, never a Continue fallback. See [launcher](docs/LAUNCHER.md)
and [runtime authority](docs/RUNTIME_AUTHORITY.md) before controlling the game.
No per-launch question is needed within an already authorized experiment.

## Setup on another computer

Prerequisites: Git, Node.js 20.19+, official CPython 3.12 x64, and the user's
separately installed Steam game. Bootstrap installs pinned local dependencies;
it does not install Steam, the game or mods.

```powershell
.\scripts\Bootstrap.ps1
.\scripts\Check.ps1
```

OpenSpec is project-local. Use `scripts/OpenSpec.ps1`, not a global install.
Do not reinitialize the working project or change execution policy/global PATH.
CPU PyTorch is the current baseline; CUDA changes need a measured reason.

## Working with Codex

See [when to continue or start a chat](docs/WORKING_WITH_CODEX.md).

[AGENTS.md](AGENTS.md) contains current durable instructions. Start with the short
STATUS and relevant Git state; load only the guide/spec/code needed for the task.
The primary implements and accepts changes. One optional Luna/high script worker
executes exact finite commands; no old Windows/Mac file bus or heartbeat is active.
See [workflow](docs/AGENT_WORKFLOW.md) and [worker contract](docs/SCRIPT_RUNNER.md).

Use OpenSpec chat skills for behavior changes: `$openspec-propose`,
`$openspec-apply-change`, `$openspec-verify-change`, `$openspec-archive-change`.
Enter skill names in chat, not PowerShell. Do not edit generated skill files.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/STATUS.md`, `ROADMAP.md` | Current handoff; remaining milestones/acceptance |
| `docs/DEVELOPMENT_GUIDE.md` | Engineering details, read by section |
| `docs/ARCHITECTURE.md`, `docs/RL_DESIGN.md` | Design context; verify dated claims against STATUS |
| `openspec/specs`, `openspec/changes` | Requirements and change artifacts |
| `src/isaac_threrisaifuture`, `mod` | Python RL/bridge code and first-party Lua adapter |
| `configs`, `tests`, `scripts` | Versioned configurations, checks and entry points |
| `reports`, `reports/local` | Published evidence; ignored raw/local execution artifacts |
| `docs/history` | Archived documentation, not current instructions |

Saves, models, credentials, approvals and raw logs stay out of Git. Save/Cloud and
third-party mod changes require specific authorization. Experiments record schema,
configuration, seed, revision, lineage and finite budgets. Reward is separate from
native gameplay success. See [roadmap](ROADMAP.md) for the remaining target.
