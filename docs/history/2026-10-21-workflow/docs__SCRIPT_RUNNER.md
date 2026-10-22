# Delegated script execution

Current receipt2026-10-21:firing-training-pilot-20261021-01 is closed. Separate
live-firing-v3 latest7951bf19-s20-t24064,root runs/live-firing-v3-pilot-20261021,
config training-live-firing-v3-pilot.yaml/hash7951bf19,seed20. Original v2 t21760
remains unchanged. No standing resume/New Run authority or longer-stage escalation.
The five-minute inclusive-startup trial saved2304 new steps but showed no observed
damage/clear gain;next offline diagnosis. See
[results](../reports/2026-10-21-firing-training-pilot-results.md). Older roots and
prerequisites below retain their historical scope.

User authorization:2026-10-20. Use one fresh `gpt-6-luna` worker with reasoning
effort `high` and `fork_turns="none"`. It executes prepared scripts, including
game checks and learning; the primary writes code, chooses the experiment and
accepts results. This is execution delegation, not a separate autonomous developer.

## Existing command inventory

For the user's screenless startup request, use the shipped
`./Start-IsaacAgent.cmd` entry point, first checking `--preflight-only`.
The equivalent PowerShell wrapper needs a host that permits local scripts.
Do not use the ignored menu/screenshot helper for this path.
The current agent entry point uses bounded local menu-only keys and fresh native
Continue,file2 evidence; no screenshots or desktop tools. It requires an existing
file2 run in default Continue mode and stops on focus/state failure. Explicit
`--entry-mode new-run` requires affirmative file2 saved-game absence and validates
Isaac from an active snapshot;it does not overwrite an available Continue. The
observer closes on return before
a separate gated runtime command can attach. No learning starts from this command.
It cannot be run concurrently with a live controller on port 9528. A successful
snapshot does not verify the save slot or authorize training. See LAUNCHER.md.

All commands run from D:\isaac using the project virtual environment. The primary
supplies complete arguments and environment values in each assignment; examples
below describe interfaces and are not a ready-to-run training authorization.

| Phase | Existing entry point | Worker responsibility |
| --- | --- | --- |
| Offline checks | `./scripts/Check.ps1` or named `.venv/Scripts/python.exe -m pytest ...` | Capture output/exit code; report exact counts, including skipped tests. Do not fix failures. |
| Approval | `.venv/Scripts/python.exe -m isaac_threrisaifuture.cli approve-training` | Only when the primary supplies exact game directory, hours, restart limit and `--confirmed-save-slot 2`; verify resulting path/hash/expiry. Never accept broad CLI defaults for a bounded assignment. |
| Launch | `Start-Process 'steam://rungameid/250900'` | Check the declared instance/preflight first. Preserve existing Steam launch options. Do not use the direct-executable `live --launch` path instead. |
| Menu preparation | A primary-specified local menu helper | Use menu-only input and its focus guard to enter file2/Continue or the explicitly named New Run. Refusal stops that action; no gameplay keys or alternate bypass. |
| Native check | `.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode random ...` or an exact named diagnostic | Execute only the prepared finite check; random actions are game control, not training evidence. |
| Learning | `.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config ... --resume --seed ... --steps ... --minutes ... --max-faults ... --combat-gate --auto-navigate --gate-wait-minutes ... --navigation-budget-scale ... --max-deaths ... --confirmed-save-slot 2` | Verify the expected latest checkpoint/config/seed first. `--steps` is the final cumulative training target, not the number of new samples. Match the supplied absolute deadline and approval; record actual session path from output. |
| Shutdown | A primary-specified normal WM_CLOSE helper | Close promptly when the command returns or its absolute deadline requires stopping. Release bridge actions; verify process/listener absence and exact approval cleanup before slower analysis. |
| Evidence | Prepared read-only verification script | Check manifests, model/normalizer hashes, lineage/latest pointer, learned versus unsaved samples and disk usage. Return evidence, not a success claim based only on exit0. |

The versioned finite session module now has offline contracts; native qualification
is pending. See [TRAINING_SESSION.md](TRAINING_SESSION.md). It does not reactivate
the stopped overnight experiment. Historical menu,
shutdown and evidence helpers used in previous runs are ignored local files under
reports/local; their paths and hashes must be supplied and inspected for each
assignment. This document does not claim those helpers are a shipped launcher.
If a required helper or command is missing, stop and report it; do not improvise.

## Required handoff

The primary supplies one compact assignment containing:

1. Task ID, D:\isaac working directory, AGENTS.md scope, exact model/effort and
   allowed output/log/approval paths.
2. Exact sequential commands, environment values, required helper/source/config
   hashes, active game/profile/save2 expectations and preflight results to verify.
3. Parent checkpoint ID, model/normalizer hashes, expected seed/schema/config,
   resume target and whether a fresh native game run is part of setup. A gameplay
   restart never authorizes a fresh learning model.
4. One global budget: new decision cap and cumulative target, absolute deadline
   covering preparation/restarts, disk cap, death/restart/fault limits, gate and
   navigation caps. Any planned retries share this budget; no silent renewal.
5. Ordered stop/cleanup commands and exact approval-hash ownership rules. Do not
   delete a changed foreign approval or close an unrelated game instance.
6. Expected return format: commands/exit codes, log/session paths, source hashes,
   before/after checkpoint identity, learned/unsaved counts, all outcomes/faults,
   budget accounting, shutdown/listener/approval checks and unresolved blockers.

The primary keeps the task active until the worker returns and reviews the actual
artifacts against the unchanged tested files. A worker can follow session progress
inside this finite execution; it cannot schedule future sessions or invent recovery.

## Current training prerequisite

Superseding receipt2026-10-21:latest is7d53f55f-s20-t21760 in
runs/live-conservative-v2-overnight-20261021,seed20,unchanged
configs/training-live-conservative-v2-overnight.yaml (hash7d53f55f). User stopped
training for corner analysis. No automatic resume or New Run;all hour assignments
are closed. Preserve t7680/t7424 and original/migrated t6912. See
reports/2026-10-21-one-hour-stopped-analysis.md. Older roots below are history.

The user's longer experiment used an explicit budget-only artifact migration;
see reports/2026-10-20-extended-conservative-plan.md and matching results.
Current continuation is runs/live-conservative-v2-extended-20261020,seed20,
config configs/training-live-conservative-v2-extended.yaml (hash08e0d262),latest
08e0d262-s20-t6912,reward live-conservative-v2. Resume exactly this compatible
latest under a newly recorded budget;never repeat the migration/initialization.
Target ceiling12288,config wall cap12min. Old conservative1536 and legacy8960
roots remain immutable history. Earlier baseline details below retain that scope.

The explicit independent conservative-v2 baseline has now been executed under
reports/2026-10-20-conservative-baseline-plan.md;see its matching results report.
New lineage is runs/live-conservative-v2-development-20261020,seed20,config
configs/training-live-conservative-v2.yaml,latest92969b7f-s20-t1536. Future runs
must resume that exact compatible latest state under a new finite plan;do not
repeat its initial no-resume command. Its configuration ceiling is4096 steps.
Legacy t8960 is retained separately;the compatibility restrictions below still
apply to that history. Do not mix model/normalizer state between these roots.

The conservative correction in openspec/changes/live-reward-continuity has passed
offline checks; native acceptance is recorded separately in
reports/2026-10-20-live-reward-continuity.md. The live-conservative-v2 reward contract
rejects legacy combat-v1 resume before environment creation. t8960 remains readable
for frozen analysis. Preserve it as development history; an explicit migration or
separate new-lineage plan is required before further learning. Do not remove
--resume or switch output directories to bypass a mismatch.
