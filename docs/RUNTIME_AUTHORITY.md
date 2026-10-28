# Runtime authority and experiment boundaries

Consolidated 2026-10-21 from existing user authorizations. This document preserves
authority; it does not start, resume or extend an experiment. Read with STATUS
and the exact run plan before game control.

## Standing permissions

- Primary may launch/close/relaunch Isaac for agreed checks or training without
  another per-launch question. Launch through Steam (steam://rungameid/250900),
  preserving existing --luadebug options; verify effective Lua access.
- Guarded menu-only input may select file 2, Continue, pause and normal exit.
  Gameplay stays on the structured bridge; no screen capture substitution.
- User accepts file-2/achievement risk. Save-slot/achievement eligibility checks
  no longer block training; record anomalies. Still verify intended instance,
  profile and fresh file-2 menu evidence. An unrelated ordinary run is not a test.
- One Luna/high script worker may execute exact finite prepared launch/menu/check/
  training/shutdown commands under the same guards. No source/config/dependency,
  deployment, Git, nested-agent or scheduled-supervision authority is granted.

## Pure profile standing authority (user decision 2026-10-22)

Applies only to the pure self-learning profile (`configs/training-pure-v4.yaml`,
lineage `pure-v4`, `docs/UPDATE_DECISION.md`):

- Continuous training of the one `pure-v4` lineage is authorized. The forever
  supervisor (`session_runner --forever`) may run bounded sessions back to back,
  each within the Lua lease (8 h), always resuming `latest`. Lineages `pure-v1` (reward v2),
  `pure-v2` (schema 3, reward v3, action repeat 3) and `pure-v3` (schema 4, reward v4) are preserved on disk and are not
  resumed (their contracts differ). The reward v6 run of `pure-v4` is kept as
  `runs/pure-v4-reward-v6`, the reward v7 run as `runs/pure-v4-reward-v7` and the reward v8 run
  as `runs/pure-v4-reward-v8`. The reward-v9 schema-6 qualification is preserved as
  `runs/pure-v4-reward-v9-schema6` and is not resumed; `pure-v4` restarts with reward v9,
  observation schema 7 and a 40 s stall limit (`--initialize`).
- New Run after death and after a stall-watchdog restart is authorized without a
  count limit (approval `max_restarts` 0). Restart pacing still applies.
- Sessions stop on the stop file, Ctrl+C, the disk cap or the consecutive
  infrastructure-fault cap (default 5). Faults are never retried silently past it.
- Tunable hyperparameters may change between sessions; contract changes need a new
  lineage and an explicit plan.
- The first native session after this refactor is the bounded acceptance session
  in `openspec/changes/pure-self-learning-v1` task 4.3; continuous training starts
  only after it passes.

## Experiment authority

Each experiment outside the pure profile needs user-authorized scope and a
recorded plan: steps, fixed inclusive wall time, disk, death/restart/fault limits,
expected source/config/model/normalizer identities, stop conditions and cleanup.
Retries share one absolute deadline. Never renew an expired lease silently.
Outside the pure profile, default approvals allow at most 10 death restarts per
session. Larger/nonbinding count limits apply only when explicitly authorized for
that experiment.

Cancelled four-hour/hour attempts and closed v2/v3 pilots grant no resume.
Do not repeat a pilot or escalate 5 minutes -> 15-30 minutes -> one hour -> four
hours without applicable new experiment authorization. Menu capability is not
permission to replace an exhausted Continue. New Run must be explicit for that
experiment, never a hidden fallback. Preparation alone is not native acceptance.

Resume only named compatible state; missing/corrupt/incompatible artifacts stop.
Never remove --resume, redirect output or initialize a fresh model to bypass failure.
A new observation/reward lineage requires an explicit migration/initialization plan.
Preserve original v2 7d53f55f-s20-t21760, v3 7951bf19-s20-t24064, t7680/t7424,
and original/migrated t6912. Children do not replace preserved parents.
Current lineage and pending acceptance belong in STATUS, not duplicate receipts here.

## Preflight and cleanup

Verify source/deployed/config hashes, lineage and intended instance/profile before
actions. Stop on focus refusal, invalid identity, resource/time exhaustion and
declared infrastructure faults; never bypass a refused action.
Bind native actions to session/episode/frame. Release before optimization and on
stop/fault/disconnect/control transfer. Record gaps and recurrent resets honestly.

Release first, close observer, close only the owned game normally, verify process/
listener state and remove only the exact unchanged owned approval. Never delete
a foreign/changed approval. Read back saved/unsaved work and checkpoint lineage.
No edits to frozen tested inputs or primary game control while a worker runs.
A script exit or absent process alone does not establish complete cleanup.

## Separately authorized actions

Save edits/imports, unlock commands, Steam Cloud changes, Steam launch-option edits
and third-party mod installation/activation require specific authorization.
Do not bypass gates, Windows protection, sandboxing or firewall rules.
No new file bus, heartbeat or scheduled agent supervision is granted. The pure
profile process supervisor above is the only standing training loop.

## Scientific limits

Frozen native probes establish only measured scenarios/contracts; synthetic RL
smoke checks library behavior. Updated weights, reward or a completed timer do
not prove better play. Report damage dealt/taken, clears/deaths, stagnation,
missing coverage and faults separately. Frozen refresh checks do not broadly
qualify real optimizer latency or all weapons. Corner interpolation remains limited.
Partial logs cannot prove zero damage; training metrics cannot prove Dead God.
