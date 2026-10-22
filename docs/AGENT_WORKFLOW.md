# Agent workflow

Current consolidated mode, 2026-10-21. AGENTS.md supplies project-wide rules.

| Role | Owns |
| --- | --- |
| Primary Windows agent | Scope, implementation, commands, budgets, acceptance, docs and Git |
| Optional Luna/high worker | Finite prepared execution; compact evidence; no fixes or Git |
| Python RL/session code | Game-step loop, optimization, checkpoints and implemented finite guards |

Codex does not choose every game action. Do not keep an LLM polling unchanged
logs when a bounded script can wait and return a terminal result.
Use a worker for substantial isolated execution/analysis, not simple commands.
One worker at a time; no nested workers, concurrent game control or shared writes.

## Task cycle

1. Read short STATUS and relevant Git state; load task-specific source/specs only.
2. Make a coherent change; use OpenSpec for software behavior changes.
3. Use focused checks while editing, then a full gate on the final code revision.
4. For delegation use SCRIPT_RUNNER and its template. Freeze tested inputs;
   do not duplicate the worker's discovery or launch a second controller.
5. Verify actual artifacts and revision identities; primary implements fixes.
6. Update STATUS in place, record evidence, review staged changes, commit/push.
   Keep software correctness, native acceptance and learning quality distinct.

Raw logs stay local. Summaries contain counts, failures, hashes and paths.
STATUS links evidence; ROADMAP holds dependencies/acceptance; AGENTS holds durable
rules. Start a fresh chat at a meaningful handoff when history becomes noisy,
retaining unresolved constraints rather than rediscovering completed work.

## Inactive coordination

The former Windows/Mac file bus, remote code executor and heartbeat are inactive.
Do not use subagent.md, subagent_report.md or agent-status.json to dispatch, poll,
resume or accept current work. Old task IDs/timestamps are history.
Only a fresh bounded assignment under current authorization is executable.
No scheduled supervision or cross-chat messaging is granted by this workflow.
History: [snapshot index](history/2026-10-21-workflow/INDEX.md), on demand only.
