# isaac-threrisaifuture

A local self-learning RL player for Steam The Binding of Isaac: Repentance+ on
native Windows. The target is Dead God earned through gameplay on save file 2.
Codex builds the software; Python/RecurrentPPO learns through a structured Lua
bridge. No screen capture, imported completed saves or unlock commands substitute
for gameplay. All project artifacts are English.

## Current state

Since 2026-10-22 the project is **pure self-learning** ([decision](docs/UPDATE_DECISION.md)):
one RecurrentPPO model (`pure-v2`) learns from scratch and continuously, from raw
game facts (observation schema 3) and outcome rewards only (reward v3), with a
use-item action head, a stall watchdog and unlimited New Run after death. There is
no scripted setup or advice feature. The hinted work is history in `archive/`.
The refactor is verified offline; native acceptance is pending. Read
[STATUS](docs/STATUS.md) for the exact state and next action.

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

Pure training on Windows (see [runtime authority](docs/RUNTIME_AUTHORITY.md)); deploy
`mod/observer` to the game while Isaac is closed first:

```powershell
# First session ever (fresh pure-v2 model):
.\Start-Pure.cmd "<Isaac install dir>" "<path to log.txt>" --initialize
# Every later start (resumes latest, runs sessions back to back):
.\Start-Pure.cmd "<Isaac install dir>" "<path to log.txt>"
```

Live training dashboard (read-only, http://127.0.0.1:8765): `.\Start-Dashboard.cmd`

Stop with `runs\pure-v2\supervisor\stop.forever` or Ctrl+C. Progress per episode is
in `runs\pure-v2\metrics\episodes.csv` (training statistics in `train.csv`); hyperparameters in
`configs/training-pure-v2.yaml` may be tuned between sessions without a new lineage.

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
The primary implements and accepts changes; no old Windows/Mac file bus or
heartbeat is active.
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
| `archive/` | Hinted-direction code, tests, docs and changes; history only |
| `docs/history` | Archived documentation, not current instructions |

Saves, models, credentials, approvals and raw logs stay out of Git. Save/Cloud and
third-party mod changes require specific authorization. Experiments record schema,
configuration, seed, revision, lineage and finite budgets. Reward is separate from
native gameplay success. See [roadmap](ROADMAP.md) for the remaining target.
