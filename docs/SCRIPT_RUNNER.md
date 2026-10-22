# Delegated script execution

Standing user authorization: 2026-10-20. Primary prepares and accepts; one fresh
`gpt-6-luna` / `high` worker executes with `fork_turns="none"`. If unavailable,
primary executes directly and reports the limitation. No substitute model.
Use direct tool commands for simple deterministic work. A worker is useful for
substantial isolated execution/log analysis or a bounded runtime assignment.

## Read and write scope

The exact assignment replaces broad startup discovery for a worker. Read AGENTS
and this contract, then only specified helpers/inputs. For runtime also read
RUNTIME_AUTHORITY and the named plan. Do not read the full roadmap or old reports.
Workers execute supplied commands; no fixes, source/test/config edits, dependency
installation, deployment, Git, nested agents, file bus or scheduled supervision.
Allowed writes are only declared artifacts/logs, runtime checkpoints/normalizers
and exact approval creation/removal included in the prepared commands.

## Required assignment

Use [the compact template](templates/SCRIPT_ASSIGNMENT.md). Include:

1. Unique task ID, working directory, exact model/effort, allowed paths and goal.
2. Exact ordered commands/environment, helper/source/config hashes and preflight.
3. Named parent checkpoint, normalizer/schema/config/seed; fail on mismatch.
4. One global absolute deadline, steps/disk/death/restart/fault limits and any
   explicitly enumerated retries. No independent lease/budget renewal.
5. Stop/release/normal shutdown and hash-owned approval cleanup commands.
6. Required result format, log paths and verification commands.

The worker may not invent experiments, expand caps, initialize missing state,
retry outside the plan or infer New Run permission from menu capability.
A missing helper or refused action stops the task; no alternate bypass.
One worker at a time. Primary freezes tested inputs and does not control its game.

## Existing entry points (interfaces, not execution authority)

| Phase | Command/interface | Requirement |
| --- | --- | --- |
| Offline checks | `scripts/Check.ps1` or explicit project Python module | Save full logs; exact exit and pass/fail/skip counts |
| Preflight/Continue | `Start-IsaacAgent.cmd --preflight-only`, then exact assigned entry | Steam; foreground/ownership guards; fresh Continue/file2 and active Isaac evidence |
| Approval | `python -m isaac_threrisaifuture.cli approve-training` | Exact supplied values, file2, expiry/hash ownership; no broad defaults |
| Native diagnostic | Exact supplied finite helper or `live --mode random` | Structured bridge only; random input is not learning |
| Training | Exact supplied helper/`live --mode train` with config, resume, seed and caps | `--steps` is cumulative target; verify lineage and fixed absolute deadline |
| Shutdown | Exact supplied normal owned WM_CLOSE/release helper | Release first; verify observer/game/listener and approval cleanup |
| Verification | Prepared read-only analysis | Check model/normalizer/manifests, saved/unsaved work and all faults |

See LAUNCHER and TRAINING_SESSION for details only when that entry point is assigned.
Legacy Start-Isaac observation mode is separate. Never use direct-executable launch
to bypass the assigned Steam path. No concurrent controller on port 9528.
New Run requires explicit experiment authority and the shipped launcher's fresh
file2/no-Continue checks; default is Continue. No screenshots or gameplay keys.
Ignored helpers in reports/local are not shipped interfaces; inspect/hash the exact
named helper. Successful startup does not authorize learning or prove eligibility.

## Return and primary acceptance

Save full command output locally. Return only task ID, tested revision/hash identity,
commands/exit codes, pass/fail/skip counts, concise failures, artifacts and blockers.
Runtime additionally reports checkpoint before/after, saved/unsaved counts, outcomes,
budget use and release/game/listener/approval cleanup evidence. Do not paste raw traces.
Primary reads the actual artifacts and verifies unchanged tested inputs. Worker
assertions alone are not evidence. Keep task active until execution ends; do not
relaunch after failure without a newly valid assignment. Current lineage/pilot state
lives only in STATUS and its evidence links, not duplicate latest receipts here.
