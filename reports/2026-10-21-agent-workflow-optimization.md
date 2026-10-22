# Evidence: focused-agent-context

- Date: 2026-10-21, Europe/Amsterdam.
- Base revision: 0e94999; primary implementation and self-review, no worker spawned.
- Scope: current instructions, evidence routing, historical snapshots, worker
  template, workflow specifications and a read-only PowerShell context helper.
- No game actions, training/model/reward/observation/dependency/global-config changes.

## Size changes

Bytes at inspection; this is document size, not billed token savings.

| File | Before | After |
| --- | ---: | ---: |
| AGENTS.md | 26532 | 6038 |
| docs/STATUS.md | 116406 | 3883 |
| ROADMAP.md | 62467 | 11173 |
| README.md | 14675 | 4144 |
| docs/AGENT_WORKFLOW.md | 11440 | 2168 |
| docs/SCRIPT_RUNNER.md | 8750 | 4347 |
| docs/DEVELOPMENT_GUIDE.md | 11454 | 11656 |
| openspec/config.yaml | 2960 | 2283 |
| subagent.md | 10414 | 469 |
| subagent_report.md | 32439 | 413 |

Startup now reads short current STATUS and relevant Git state rather than all
README/ROADMAP/guides. Workers follow exact assignments rather than rediscovery.
Historical snapshots are explicitly inactive; ten original SHA256 values match.
Full archived relative links preserve original-location semantics; the index explains it.

## Verification

| Check | Command/evidence | Exit | Result |
| --- | --- | --- | --- |
| Context behavior | pwsh -NoProfile -File reports/local/agent-workflow-optimization-20261021/smoke.ps1 | 0 | 5 checks passed: JSON, text, alternate cwd, 12 KB refusal, 35->30 Git cap |
| OpenSpec strict | scripts/OpenSpec.ps1 validate --all --strict | 0 | 53 items passed, zero failed |
| Snapshot preservation | local SHA256 comparison against baseline.json | 0 | 10/10 exact originals |
| Links and diff | local changed-document link scan; git diff --check | 0 | 45 local links passed; diff check passed |
| Full Python/RL suite | not_run | n/a | No Python/game/learning/dependency change; helper checked directly |
| Native acceptance | not_run | n/a | No new runtime authority or actions |

Local logs, fixture and baseline hashes are in
reports/local/agent-workflow-optimization-20261021 and remain outside Git.

## Verification report: focused-agent-context

Self-review used openspec-verify-change against all four change artifacts.
Completeness: five tasks; three workflow requirements, seven scenarios mapped to
AGENTS, STATUS, SCRIPT_RUNNER and Get-ProjectContext.ps1. Documentary ownership/
routing/model-fallback/recovery scenarios were self-reviewed; command bounds and
working-directory behavior have executable checks. These are not native RL tests.
Correctness: helper reads only STATUS and Git rev/status; no model/approval/raw-log,
network or runtime calls. Oversized status fails before output. Git caps are explicit.
Coherence: original engineering/evidence rules retained; development-workflow delta
synced to main requirements. No generated skills changed. New change is unarchived.
No known blocking self-review finding. Actual token/cost reduction is not measured.

## Pending game work is separate

The user-authorized geometry warm-start pilot was dispatched in another chat;
that primary and worker stopped at usage limits before final primary acceptance.
The short STATUS records pending artifact/lineage/cleanup/gameplay verification,
not a new launch instruction. Geometry tasks remain 2/4; no completion is inferred.

## Next action

Recover the already-dispatched pilot's evidence read-only before planning learning.
Use docs/WORKING_WITH_CODEX.md for chat handoffs; start a new chat after a milestone,
not per command. No archive or fresh experiment follows automatically.
