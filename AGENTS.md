# Agent instructions: isaac-threrisaifuture

## Purpose and authority

Build a local RL player for Steam The Binding of Isaac: Repentance+ on native
Windows. Goal: Dead God through gameplay on save file 2.
Codex develops software; Python/RecurrentPPO learns to play.
Direction since 2026-10-22: pure self-learning (`docs/UPDATE_DECISION.md`). One
`pure-v1` RecurrentPPO lineage learns from raw facts and outcome rewards only. No
scripted setup, advice features or technique rewards. `archive/` is history only.
Project artifacts must be English; conversation may follow the user.
Preserve `isaac-threrisaifuture` and package `isaac_threrisaifuture`.

Current rules, consolidated 2026-10-21, updated 2026-10-22. Superseded receipts are history, not
authority. User instructions prevail. Never revive old tasks/approvals/budgets.

## Load context by task

At startup/resume read short STATUS and Git state (`scripts/Get-ProjectContext.ps1`
combines them). Workers instead follow their exact assignment and SCRIPT_RUNNER.
Inspect relevant diffs; preserve unrelated work. Do not reread instructions already
supplied in full. Load further context by task:

| Task | Additional context |
| --- | --- |
| Status/question | Relevant STATUS evidence link; bounded sections |
| Implementation | Active change proposal/design/tasks/delta specs, relevant main spec and source/tests |
| Next milestone | Relevant ROADMAP section and current blockers |
| Engineering detail | Relevant DEVELOPMENT_GUIDE, architecture or RL section |
| Game/training | RUNTIME_AUTHORITY, exact run plan and relevant runtime guide |
| Worker execution | Exact assignment and SCRIPT_RUNNER; no general rediscovery |
| Historical decision | Named report; archived history only for a specific discrepancy |

Use `rg` and bounded reads; aggregate traces with scripts. Keep full logs in
`reports/local/`; return counts, failures, identities and paths. Narrow truncated
queries. Read skills on demand; never edit generated skills. Prefer local scripts
to a new MCP service.

## Development and delegation

Primary owns implementation, experiments, self-review and acceptance. Run simple
commands directly; delegate substantial isolated execution/log work when useful.
One script worker at a time: `gpt-6-luna`, effort `high`, `fork_turns="none"`.
Standing 2026-10-20 permission covers prepared offline/bounded runtime execution,
not new experiments. No nested agents.
Workers have no code/config/dependency/Git/deployment writes or invented retries/
budgets. See `docs/SCRIPT_RUNNER.md` for allowed artifact writes and exact handoff.
If model/effort is unavailable, report it and execute directly; do not substitute.
No file bus/heartbeat/scheduled agent supervision. Old subagent/status files are
history. The pure profile process supervisor is the only standing training loop.
Do not edit frozen tested inputs or control a worker's game during execution.
Verify actual logs, exit codes, revision/hashes and cleanup before acceptance.

## Runtime boundaries

Before game actions read `docs/RUNTIME_AUTHORITY.md` and the exact plan. Use Steam
and guarded menu keys; gameplay uses the bridge. File 2 is authorized; achievement
eligibility is a separate evidence issue.
Pure profile: continuous `pure-v1` training with unlimited New Run after death or
stall is standing authority (see RUNTIME_AUTHORITY); fault and disk caps still stop.
Other experiments need steps, fixed time/disk/fault/restart caps, lineage and
cleanup. Missing/incompatible state stops; new lineage needs a plan. No old-pilot
resume. Preserve old lineages under `runs/`; STATUS identifies current lineage.
Save/Cloud/launch-option edits, unlocks and third-party mods require specific authority.

## Engineering and evidence

- Use Python 3.12, project `.venv`, typed interfaces and validated transport.
- Bound data size/frequency/waits; never indefinitely block a game callback.
- Bind actions to session/episode/frame; reject stale/replayed actions; release
  input on expiry, disconnect, fault and stop.
- Separate acquisition, encoding and reward. Keep oracle/hidden data out of policy,
  normalizer, recurrent state and inference records reused as model inputs.
- Distinguish termination, truncation, unknown outcomes and infrastructure faults.
- Version observation/action/reward/config contracts; save normalization and lineage.
- Test reward exploits: repeated entry, healed damage and item cycling included.
- Separate train/validation/test; report seeds, attempts, failures and denominators.
  Reward, optimizer updates and synthetic smoke do not prove better native play.
- Prefer installed source/primary docs; audit external licenses/APIs. No empty
  architecture or unnecessary dependency updates.
- Do not change global PATH, profiles, security settings or dependencies unnecessarily.

## OpenSpec and verification

Behavior/protocol/reward/evaluation changes need a small OpenSpec change.
Docs-only corrections/reorganization need no software change. Define measurable
acceptance, validate, implement and verify against specs/evidence. Use the verify
skill; archive only accepted scope. Blocked native tasks stay unfinished.

Commands from `D:\isaac`:

```powershell
.\scripts\Check.ps1                         # lint/format/mypy/offline tests/pip/strict specs
.\scripts\Smoke-RL.ps1                      # synthetic CPU stack only
.\scripts\OpenSpec.ps1 validate <id> --strict
```

Use focused checks, then the full gate on final code. Rerun after relevant changes/
failures, not unchanged success. Dependency changes need locks/pip/RL smoke.
Docs-only work uses diff/link/config checks, no game/full RL suite. Never weaken tests.
Use `reports/EVIDENCE_TEMPLATE.md`; distinguish passed/failed/not_run/blocked.
Self-review is not independent review. After three unsuccessful attempts at one
cause, stop that approach and record the blocker.

## Finish and handoff

Update STATUS in place (about 100 lines); link reports, never prepend history.
Keep AGENTS around 6 KB; put procedures in linked docs. ROADMAP holds acceptance.
Commit/push meaningful verified milestones to existing origin (user authorized
2026-10-20), unless the user says the work is handed off uncommitted. Review staged changes; never force-push, create remotes or include
saves, models, approvals, credentials, raw logs or unrelated changes. Publication
is not native acceptance or training authority.
Use short milestone handoffs. Report outcome/checks/limits/next action. History:
`docs/history/2026-10-21-workflow/INDEX.md`, on demand only.
