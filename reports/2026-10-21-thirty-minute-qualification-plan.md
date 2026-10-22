# Finite thirty-minute native qualification plan

User requested a roughly thirty-minute training run on 2026-10-21. This is a new
bounded request; it does not resume the cancelled overnight experiment.

Base revision: 416e4b2ac9972341932b3a92e41c3474f9a7364a. Config conservative-v2 overnight hash
7d53f55f92aae137da716f2916e4cc18db2c2594ef76bb58d2104bdb1e7ce4ee; same observation/action/reward, CPU RecurrentPPO, seed20.
Continue file2 from immutable 7d53f55f-s20-t7424; no model initialization, migration,
New Run, save/Cloud/launch-option edits, deployment or scripted gameplay.

Global action deadline Unix 1792570830.5518756; cleanup deadline 1792570875.5518756.
At most30minutes including startup and between-stage review. Stage1 is300seconds
from invocation, max2 death restarts; only after primary checks complete duration,
positive compatible checkpoint update, event/status truth and owned cleanup may
stage2 use the remaining fixed time and at most8 additional restarts. Total10.
No automatic retries, no infrastructure fault tolerance. Step ceiling1billion is
nonbinding, total run/output disk emergency cap2GiB. Time-dominant ordinary-room
navigation retains local guards and stops exhausted/unreachable routes. No reset
fallback. Early navigation stop does not qualify the longer stage.

Exact stage1 command:
`.venv/Scripts/python.exe reports/local/native-30min-qualification-20261021/run_stage1.py`.
Private assignment records exact paths/options, source/mod/config/parent hashes,
driver SHA, deadlines and expected revision. One fresh gpt-6-luna/high worker,
no source/config/Git/deployment edits or nested agents. Bridge-only gameplay;
Steam/menu-only guarded Continue2. Primary does not control the game concurrently.

Cleanup uses the tested supervisor: cooperative release, owned worker timeout,
normal owned-game close, exact approval-hash cleanup, sleep release and immutable
source/parent verification. No force-killing Isaac. Primary independently reads
session identity, events, manifests/latest, process/listener/approval and errors.
Raw damage/clear and manual-stop acceptance remain separate if not observed;
weight updates prove continuation only, not better play. If no new fight is found
or any gate fails, stop and retain all evidence rather than renewing the lease.

## Explicit replacement amendment

First Continue pilot ended early after58.766s,zero combat/updates,observed ordinary
component exhausted. Primary verified61 frozen hashes and clean shutdown. User
then explicitly approved one New Run on file2 replacing that game run,while
retaining t7424. This is a new scoped authorization,not reuse of the cancelled one.

Implement/test explicit replacement before menu input. Stage2 is a new300s native
qualification,max2 restarts; stage3 can use remaining original fixed deadline with
max6 restarts only after positive completed update/full300s/clean owned shutdown
and primary verification. No further replacement. Global deadline unchanged;
preparation consumes remaining time. Exact stage2 command:
`.venv/Scripts/python.exe reports/local/native-30min-qualification-20261021/run_stage2.py`.
Private assignment/driver freeze exact revised source/config/parent and record the
one human authorization. Runtime override preserves Steam/focus/slot/log/bridge
guards and writes honest explicit-new-run entry metadata. New mode must be
natively [New,2] and bridge-active Isaac; any refusal stops with no alternate input.
